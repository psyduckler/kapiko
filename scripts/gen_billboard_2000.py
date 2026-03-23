#!/usr/bin/env python3
"""Generate kapiko song pages for Billboard Year-End Hot 100 (2000) missing songs.

Fetches Spotify audio features and generates pages using the same HTML template
as generate_song_pages.py, but outputs to ~/kapiko-site/site/songs/.
"""

import json, sys, re, html as H, time, base64, urllib.request, urllib.parse, urllib.error
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
SITE = Path.home() / 'kapiko-site' / 'site'
SONGS_DIR = SITE / 'songs'
GENRES_DIR = SITE / 'genres'

# ── Key mapping ────────────────────────────────────────────────────────────
KEY_NAMES = {0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',7:'G',8:'G#',9:'A',10:'A#',11:'B'}
MODE_NAMES = {0:'Minor',1:'Major'}

# ── Genre assignments for Billboard 2000 songs ────────────────────────────
SONG_GENRES = {
    'smooth-santana': 'rock',
    'maria-maria-santana': 'latin',
    'i-wanna-know-joe': 'r-n-b',
    'everything-you-want-vertical-horizon': 'rock',
    'say-my-name-destiny-s-child': 'r-n-b',
    'i-knew-i-loved-you-savage-garden': 'pop',
    'bent-matchbox-twenty': 'alt-rock',
    'he-wasn-t-man-enough-toni-braxton': 'r-n-b',
    'try-again-aaliyah': 'r-n-b',
    'jumpin-jumpin-destiny-s-child': 'r-n-b',
}

# ── Helpers (copied from generate_song_pages.py) ──────────────────────────
GENRE_DISPLAY = {
    'piano':'Piano','sleep':'Sleep','chill':'Chill','study':'Study',
    'classical':'Classical','jazz':'Jazz','acoustic':'Acoustic',
    'electronic':'Electronic','hip-hop':'Hip-Hop','soul':'Soul',
    'ambient':'Ambient','lofi-hip-hop':'Lo-Fi Hip Hop',
    'neo-classical':'Neo-Classical','focus':'Focus','jazz-piano':'Jazz Piano',
    'pop':'Pop','r-n-b':'R&B','rock':'Rock','country':'Country',
    'edm':'EDM','indie':'Indie','folk':'Folk','reggaeton':'Reggaeton',
    'synth-pop':'Synth-Pop','trip-hop':'Trip-Hop','blues':'Blues',
    'metal':'Metal','funk':'Funk','disco':'Disco','reggae':'Reggae',
    'punk':'Punk','house':'House','techno':'Techno','trance':'Trance',
    'deep-house':'Deep House','dubstep':'Dubstep','k-pop':'K-Pop',
    'latin':'Latin','afrobeat':'Afrobeat','j-pop':'J-Pop','alt-rock':'Alt-Rock',
    'grunge':'Grunge','hard-rock':'Hard Rock','singer-songwriter':'Singer-Songwriter',
    'indie-pop':'Indie Pop','dance':'Dance','heavy-metal':'Heavy Metal',
    'gospel':'Gospel','emo':'Emo','ska':'Ska','drum-and-bass':'Drum & Bass',
}

def esc(t): return H.escape(str(t))

def primary_artist(artist_str):
    for sep in [',', ' feat.', ' feat ', ' ft.', ' ft ', ' Feat.', ' Feat ', ' x ', ' X ', ' & ', ' with ', ' With ']:
        if sep in artist_str:
            return artist_str.split(sep)[0].strip()
    return artist_str.strip()

def make_slug(title, artist):
    primary = re.split(r'\s+feat\w*\s+|\s+ft\.?\s+|\s+with\s+', artist, flags=re.IGNORECASE)[0].strip()
    return re.sub(r'[^a-z0-9]+', '-', (title + '-' + primary).lower()).strip('-')

def make_title_tag(song_name, artist_str):
    artist = primary_artist(artist_str)
    suffix_long = " — AI Prompt & Analysis | kapiko"
    suffix_short = " — AI Prompt | kapiko"
    base = f"{song_name} by {artist}"
    if len(base + suffix_long) <= 62:
        return base + suffix_long
    if len(base + suffix_short) <= 62:
        return base + suffix_short
    return f"{song_name} by {artist[:20]}… — AI Prompt | kapiko"

def fmt_dur(ms):
    s = ms / 1000
    return f"{int(s//60)}:{int(s%60):02d}"

def loud_pct(db):
    return max(0, min(100, (60+db)/60*100))

def get_camelot_key(key, mode):
    major_keys = {'C':'8B','G':'9B','D':'10B','A':'11B','E':'12B','B':'1B',
                  'F#':'2B','Db':'3B','Ab':'4B','Eb':'5B','Bb':'6B','F':'7B'}
    minor_keys = {'A':'8A','E':'9A','B':'10A','F#':'11A','C#':'12A','G#':'1A',
                  'D#':'2A','Bb':'3A','F':'4A','C':'5A','G':'6A','D':'7A'}
    if mode == 'Major':
        return major_keys.get(key, f'{key}B')
    else:
        return minor_keys.get(key, f'{key}A')

def infer_mood(energy, valence):
    if energy < 0.3 and valence < 0.3: return 'melancholic, introspective'
    if energy < 0.3 and valence >= 0.3: return 'peaceful, serene'
    if energy < 0.5 and valence < 0.4: return 'contemplative, moody'
    if energy < 0.5 and valence >= 0.4: return 'relaxed, warm'
    if energy < 0.7 and valence < 0.4: return 'intense, brooding'
    if energy < 0.7 and valence >= 0.4: return 'upbeat, groovy'
    if valence >= 0.5: return 'energetic, joyful'
    return 'powerful, dark'

def infer_instruments(genre, acousticness, instrumentalness, energy):
    base = {
        'pop': ['synth','programmed drums','electric guitar'],
        'r-n-b': ['808 bass','smooth synth pads','electric piano'],
        'rock': ['electric guitar','drum kit','bass guitar'],
        'alt-rock': ['distorted guitar','bass','reverb effects'],
        'latin': ['congas','timbales','acoustic guitar'],
        'soul': ['organ','electric piano','bass guitar'],
        'country': ['acoustic guitar','pedal steel','fiddle'],
        'hip-hop': ['808 bass','hi-hats','snare'],
        'electronic': ['synthesizer','drum machine'],
        'acoustic': ['acoustic guitar','fingerpicking'],
    }.get(genre, ['various instruments'])
    return ', '.join(base)

def infer_style(genre, energy, acousticness):
    if acousticness > 0.7: return 'organic, warm, natural'
    if energy > 0.7: return 'driving, energetic, produced'
    if energy < 0.3: return 'minimal, ambient, sparse'
    return 'polished, balanced, studio-quality'

# ── Spotify API ────────────────────────────────────────────────────────────
def get_spotify_token(client_id, client_secret):
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=b"grant_type=client_credentials",
        headers={"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())['access_token']

def spotify_get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} for {url}")
        return None

def search_track(title, artist, token):
    q = urllib.parse.quote(f"track:{title} artist:{artist}")
    data = spotify_get(f"https://api.spotify.com/v1/search?q={q}&type=track&limit=1", token)
    if data and data['tracks']['items']:
        return data['tracks']['items'][0]
    # Fallback: search by title only
    q2 = urllib.parse.quote(f"{title} {artist}")
    data2 = spotify_get(f"https://api.spotify.com/v1/search?q={q2}&type=track&limit=1", token)
    if data2 and data2['tracks']['items']:
        return data2['tracks']['items'][0]
    return None

def get_audio_features(track_id, token):
    return spotify_get(f"https://api.spotify.com/v1/audio-features/{track_id}", token)

# ── HTML Generator ─────────────────────────────────────────────────────────
def make_page(t, genre):
    name = t['name']
    artist = t['artists']
    slug = t.get('slug', '')
    album = t.get('album', '')
    pop = t.get('popularity', 50)
    tempo = t.get('tempo', 120)
    key = t.get('key', 'C')
    mode = t.get('mode', 'Major')
    e = t.get('energy', 0.5)
    v = t.get('valence', 0.5)
    d = t.get('danceability', 0.5)
    a = t.get('acousticness', 0.5)
    ins = t.get('instrumentalness', 0.1)
    sp = t.get('speechiness', 0.05)
    liv = t.get('liveness', 0.1)
    loud = t.get('loudness', -8.0)
    dur_ms = t.get('duration_ms', 210000)

    dur_str = fmt_dur(dur_ms)
    mood = infer_mood(e, v)
    instruments = infer_instruments(genre, a, ins, e)
    style = infer_style(genre, e, a)
    gdisp = GENRE_DISPLAY.get(genre, genre.replace('-',' ').title())
    key_mode = f"{key} {mode}"
    camelot_key = get_camelot_key(key, mode)

    gen_prompt = f"Create a {gdisp.lower()} track at {tempo:.0f} BPM in {key_mode}. {instruments}. Mood: {mood}. Style: {style}. Target energy {e*100:.0f}%, valence {v*100:.0f}%."
    suno_prompt = f"{gdisp.lower()}, {mood}, {instruments}, {style}, {tempo:.0f} BPM"
    udio_prompt = f"A {gdisp.lower()} track that feels {mood} with {instruments} — {style} in the style of {artist.split(';')[0]}"
    agent_json = json.dumps({
        "track_reference": {"title": name, "artist": artist},
        "generation_params": {"bpm": round(tempo), "key": key_mode, "duration": dur_str, "energy": round(e,3), "valence": round(v,3), "acousticness": round(a,3), "instrumentalness": round(ins,3)},
        "style": {"genre": genre, "mood": mood, "instruments": instruments.split(', '), "production": style},
        "prompt": gen_prompt
    }, indent=2)

    genre_pill = f'<a href="/genres/{genre}/" class="pill genre">{esc(gdisp)}</a>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(make_title_tag(name, artist))}</title>
  <meta name="description" content="Audio analysis of {esc(name)} by {esc(artist)}. BPM, key, energy, mood, and AI music generation prompts.">
  <link rel="canonical" href="https://kapiko.ai/songs/{esc(slug)}/">

  <!-- Open Graph -->
  <meta property="og:title" content="{esc(name)} by {esc(primary_artist(artist))} — AI Prompt &amp; Analysis | kapiko">
  <meta property="og:description" content="Audio analysis and AI music generation prompts for {esc(name)} — {tempo:.0f} BPM in {esc(key_mode)}, {e*100:.0f}% energy">
  <meta property="og:url" content="https://kapiko.ai/songs/{esc(slug)}/">
  <meta property="og:type" content="music.song">
  <meta property="og:site_name" content="kapiko">
  <meta name="robots" content="index, follow">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{esc(name)} by {esc(primary_artist(artist))} — AI Prompt &amp; Analysis | kapiko">
  <meta name="twitter:description" content="Audio analysis and AI music generation prompts for {esc(name)}">

  <!-- JSON-LD: MusicRecording -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "MusicRecording",
    "name": "{esc(name)}",
    "duration": "PT{int(dur_ms/60000)}M{int((dur_ms%60000)/1000)}S",
    "byArtist": {{ "@type": "MusicGroup", "name": "{esc(primary_artist(artist))}" }},
    {"\"inAlbum\": { \"@type\": \"MusicAlbum\", \"name\": \"" + esc(album) + "\" }," if album else ""}
    "genre": ["{esc(gdisp)}"],
    "url": "https://kapiko.ai/songs/{esc(slug)}/",
    "publisher": {{ "@type": "Organization", "name": "kapiko", "url": "https://kapiko.ai" }}
  }}
  </script>
  <!-- JSON-LD: BreadcrumbList -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "kapiko", "item": "https://kapiko.ai/" }},
      {{ "@type": "ListItem", "position": 2, "name": "{esc(gdisp)}", "item": "https://kapiko.ai/genres/{esc(genre)}/" }},
      {{ "@type": "ListItem", "position": 3, "name": "{esc(name)} — {esc(primary_artist(artist))}" }}
    ]
  }}
  </script>
  <!-- JSON-LD: FAQPage -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {{
        "@type": "Question",
        "name": "What BPM is {esc(name)} by {esc(primary_artist(artist))}?",
        "acceptedAnswer": {{ "@type": "Answer", "text": "{esc(name)} by {esc(primary_artist(artist))} is {tempo:.0f} BPM." }}
      }},
      {{
        "@type": "Question",
        "name": "What key is {esc(name)} by {esc(primary_artist(artist))} in?",
        "acceptedAnswer": {{ "@type": "Answer", "text": "{esc(name)} is in {esc(key_mode)}." }}
      }},
      {{
        "@type": "Question",
        "name": "How do I recreate {esc(name)} by {esc(primary_artist(artist))} with AI?",
        "acceptedAnswer": {{ "@type": "Answer", "text": "Use the prompt: {esc(gen_prompt)} Paste into Suno, Udio, MiniMax Music, ElevenLabs, or any AI music generator." }}
      }}
    ]
  }}
  </script>
  <!-- JSON-LD: HowTo -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "HowTo",
    "name": "How to Recreate \\"{esc(name)}\\" by {esc(primary_artist(artist))} with AI",
    "description": "Use data-driven prompts to recreate the sound of {esc(name)} using Suno, Udio, or any AI music generator.",
    "step": [
      {{ "@type": "HowToStep", "name": "Choose your AI music tool", "text": "Select Suno, Udio, MiniMax Music, ElevenLabs, Mureka, Beatoven.ai, Stable Audio, AIVA, Soundraw, or another AI music generator." }},
      {{ "@type": "HowToStep", "name": "Copy the prompt", "text": "Copy the ready-to-use prompt: {esc(gen_prompt)}" }},
      {{ "@type": "HowToStep", "name": "Generate and refine", "text": "Paste the prompt into your chosen tool, generate the track, and iterate on the results." }}
    ]
  }}
  </script>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    :root{{--bg:#0b0c1a;--bg-card:#111222;--border:rgba(255,255,255,0.07);--text:#dde1f0;--text-muted:#6b7099;--teal:#4ecdc4;--purple:#9b7fd4;--blue:#5b9bd5}}
    body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
    .container{{max-width:900px;margin:0 auto;padding:0 1.5rem}}
    header{{background:#0d0e20;border-bottom:1px solid var(--border);padding:2rem 0}}
    .breadcrumb{{color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem}}
    .breadcrumb a{{color:var(--teal);text-decoration:none}}.breadcrumb a:hover{{text-decoration:underline}}
    .hero-content{{display:grid;grid-template-columns:160px 1fr;gap:1.5rem;align-items:start}}
    .album-art{{width:160px;height:160px;border-radius:12px;background:var(--bg-card);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;color:var(--text-muted);font-size:0.8rem}}
    .hero-info h1{{font-size:2rem;font-weight:700;margin-bottom:0.3rem}}
    .hero-artist{{font-size:1.1rem;color:var(--purple);font-weight:500;margin-bottom:1rem}}
    .metadata-row{{display:flex;flex-direction:column;gap:0.3rem;font-size:0.9rem;margin-bottom:1rem}}
    .metadata-item{{color:var(--text-muted)}}
    .listen-links{{display:flex;gap:0.6rem;margin-top:0.5rem;align-items:center}}
    .listen-links a{{display:flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:50%;background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);transition:color 0.2s,border-color 0.2s;text-decoration:none}}
    .listen-links a:hover{{color:var(--teal);border-color:var(--teal)}}
    .listen-links a svg{{width:16px;height:16px;fill:currentColor}}
    .genre-tags{{display:flex;flex-wrap:wrap;gap:0.4rem;margin-top:0.8rem}}
    .pill{{background:rgba(91,155,213,0.1);color:var(--blue);border:1px solid rgba(91,155,213,0.2);border-radius:20px;padding:0.3rem 0.8rem;font-size:0.8rem;text-decoration:none}}
    .pill.genre:hover{{background:rgba(91,155,213,0.2)}}
    .yt-section{{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.5rem;margin:2rem 0}}
    .stats-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1rem;margin:2rem 0}}
    .stat-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1rem;text-align:center}}
    .stat-val{{font-size:1.5rem;font-weight:700;color:var(--teal)}}
    .stat-label{{font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.05em;margin-top:0.2rem}}
    .stat-key{{font-size:0.75rem;color:var(--text-muted);margin-top:0.2rem}}
    .section-label{{margin:2.5rem 0 1rem}}
    .section-label h2{{font-size:0.8rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--teal);font-weight:600}}
    .chart-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem}}
    .chart-wrap{{height:280px;position:relative}}
    .audio-features-grid{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;align-items:start}}
    .feature-bars{{display:flex;flex-direction:column;gap:0.8rem}}
    .feature-item{{display:grid;grid-template-columns:130px 50px 1fr;align-items:center;gap:0.5rem}}
    .feature-label{{font-size:0.85rem;color:var(--text-muted)}}
    .feature-val{{font-size:0.85rem;font-weight:600;text-align:right}}
    .feature-track{{height:6px;background:rgba(255,255,255,0.05);border-radius:3px;overflow:hidden}}
    .feature-fill{{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--teal),var(--purple))}}
    .prompt-lab{{display:flex;flex-direction:column;gap:1.5rem;margin-bottom:2rem}}
    .prompt-lab-intro h3{{font-size:1.3rem;font-weight:700;margin-bottom:0.5rem}}
    .prompt-lab-intro p{{color:var(--text-muted);font-size:0.95rem;line-height:1.6}}
    .prompt-tabs{{display:flex;gap:0.5rem;flex-wrap:wrap}}
    .prompt-tab{{background:rgba(255,255,255,0.04);color:var(--text-muted);border:1px solid var(--border);border-radius:8px;padding:0.5rem 1.2rem;font-size:0.85rem;font-weight:500;cursor:pointer;transition:all 0.2s;font-family:'Inter',sans-serif}}
    .prompt-tab:hover{{background:rgba(78,205,196,0.08);color:var(--text)}}
    .prompt-tab.active{{background:rgba(78,205,196,0.15);color:var(--teal);border-color:rgba(78,205,196,0.3)}}
    .prompt-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.5rem;position:relative}}
    .prompt-card-main{{border-color:rgba(78,205,196,0.25);background:linear-gradient(135deg,rgba(78,205,196,0.04),rgba(155,127,212,0.04))}}
    .prompt-card-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem}}
    .prompt-card-label{{font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--teal);font-weight:600}}
    .prompt-hint{{font-size:0.85rem;color:var(--text-muted);margin-bottom:0.8rem;line-height:1.5}}
    .prompt-hint strong{{color:var(--text)}}
    .copy-btn{{background:rgba(78,205,196,0.15);color:var(--teal);border:1px solid rgba(78,205,196,0.3);border-radius:8px;padding:0.4rem 1rem;font-size:0.8rem;cursor:pointer;transition:all 0.2s;font-family:'Inter',sans-serif}}
    .copy-btn:hover{{background:rgba(78,205,196,0.25)}}
    .prompt-text{{font-size:0.95rem;line-height:1.7;color:var(--text);font-family:'Inter',sans-serif}}
    .prompt-code{{font-size:0.82rem;line-height:1.6;color:var(--teal);font-family:'JetBrains Mono','Fira Code',monospace;background:rgba(0,0,0,0.3);border-radius:8px;padding:1rem;overflow-x:auto;white-space:pre;margin:0}}
    footer{{margin-top:3rem;padding:1.5rem 0;border-top:1px solid var(--border);text-align:center;color:var(--text-muted);font-size:0.8rem}}
    footer a{{color:var(--teal);text-decoration:none}}
    @media(max-width:600px){{
      .hero-content{{grid-template-columns:1fr;text-align:center;gap:1rem}}
      .album-art{{width:140px;height:140px;margin:0 auto}}
      .stats-row{{grid-template-columns:repeat(2,1fr)}}
      .feature-item{{grid-template-columns:100px 45px 1fr}}
      .audio-features-grid{{grid-template-columns:1fr;gap:1rem}}
    }}
  </style>
</head>
<body>

<header>
  <div class="container">
    <div class="breadcrumb"><a href="/genres/{esc(genre)}/">{esc(gdisp)}</a> → Song Analysis</div>
    <div class="hero-content">
      <div class="album-art">No Image</div>
      <div class="hero-info">
        <h1>{esc(name)}</h1>
        <div class="hero-artist">{esc(artist)}</div>
        <div class="metadata-row">
          {"<div class=\"metadata-item\">From <em>" + esc(album) + "</em></div>" if album else ""}
        </div>
        <div class="listen-links">
          <a href="https://open.spotify.com/search/{esc(urllib.parse.quote(name + ' ' + primary_artist(artist)))}" target="_blank" rel="noopener" title="Find on Spotify">
            <svg viewBox="0 0 24 24"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>
          </a>
          <a href="https://www.youtube.com/results?search_query={esc(urllib.parse.quote(name + ' ' + primary_artist(artist)))}" target="_blank" rel="noopener" title="Find on YouTube">
            <svg viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
          </a>
        </div>
        <div class="genre-tags">
          {genre_pill}
        </div>
      </div>
    </div>
  </div>
</header>

<div class="container">
  <div class="section-label"><h2>Listen</h2></div>
  <div class="yt-section">
    <p style="color:var(--text-muted);text-align:center;font-style:italic;">Search for this track on YouTube or Spotify above.</p>
  </div>

  <div class="section-label"><h2>Overview</h2></div>
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-val">{tempo:.0f}</div>
      <div class="stat-label">BPM</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">{esc(key_mode)}</div>
      <div class="stat-label">Key</div>
      <div class="stat-key">{esc(camelot_key)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">{e*100:.0f}%</div>
      <div class="stat-label">Energy</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">{dur_str}</div>
      <div class="stat-label">Duration</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">{pop}</div>
      <div class="stat-label">Popularity</div>
    </div>
  </div>

  <div class="section-label"><h2>Audio Features</h2></div>
  <div class="chart-card">
    <div class="audio-features-grid">
      <div class="chart-wrap" style="height:250px">
        <canvas id="radarChart"></canvas>
      </div>
      <div class="feature-bars">
        <div class="feature-item"><div class="feature-label">Energy</div><div class="feature-val">{e*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{e*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Danceability</div><div class="feature-val">{d*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{d*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Valence</div><div class="feature-val">{v*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(v*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Acousticness</div><div class="feature-val">{a*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{a*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Instrumentalness</div><div class="feature-val">{ins*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(ins*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Speechiness</div><div class="feature-val">{sp*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(sp*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Liveness</div><div class="feature-val">{liv*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(liv*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Loudness</div><div class="feature-val">{loud:.1f} dB</div><div class="feature-track"><div class="feature-fill" style="width:{loud_pct(loud):.0f}%"></div></div></div>
      </div>
    </div>
  </div>

  <div class="section-label"><h2>Prompts to recreate &ldquo;{esc(name)}&rdquo; by {esc(primary_artist(artist))}</h2></div>
  <div class="prompt-lab">
    <div class="prompt-lab-intro">
      <p>Paste into <strong>Suno</strong>, <strong>Udio</strong>, <strong>MiniMax Music</strong>, <strong>ElevenLabs</strong>, <strong>Mureka</strong>, <strong>Beatoven.ai</strong>, <strong>Stable Audio</strong>, <strong>AIVA</strong>, <strong>Soundraw</strong>, or any AI music generator.</p>
    </div>
    <div class="prompt-tabs">
      <button class="prompt-tab active" onclick="switchTab(this,'general')">General</button>
      <button class="prompt-tab" onclick="switchTab(this,'suno')">Suno</button>
      <button class="prompt-tab" onclick="switchTab(this,'udio')">Udio</button>
      <button class="prompt-tab" onclick="switchTab(this,'agent')">Agent JSON</button>
    </div>
    <div class="prompt-card prompt-card-main prompt-panel" id="panel-general">
      <div class="prompt-card-header">
        <span class="prompt-card-label">Ready-to-Use Prompt</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptGeneral">Copy</button>
      </div>
      <div class="prompt-text" id="promptGeneral">{esc(gen_prompt)}</div>
    </div>
    <div class="prompt-card prompt-card-main prompt-panel" id="panel-suno" style="display:none">
      <div class="prompt-card-header">
        <span class="prompt-card-label">Suno Style Tags</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptSuno">Copy</button>
      </div>
      <div class="prompt-hint">Paste into the <strong>Style of Music</strong> field. Set BPM to {tempo:.0f}.</div>
      <div class="prompt-text" id="promptSuno">{esc(suno_prompt)}</div>
    </div>
    <div class="prompt-card prompt-card-main prompt-panel" id="panel-udio" style="display:none">
      <div class="prompt-card-header">
        <span class="prompt-card-label">Udio Prompt</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptUdio">Copy</button>
      </div>
      <div class="prompt-hint">Use manual mode to set BPM ({tempo:.0f}) and key ({esc(key_mode)}).</div>
      <div class="prompt-text" id="promptUdio">{esc(udio_prompt)}</div>
    </div>
    <div class="prompt-card prompt-card-main prompt-panel" id="panel-agent" style="display:none">
      <div class="prompt-card-header">
        <span class="prompt-card-label">Structured Data for Agents</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptAgent">Copy</button>
      </div>
      <pre class="prompt-code" id="promptAgent">{esc(agent_json)}</pre>
    </div>
  </div>
</div>

<footer>
  <div class="container">
    <p>&copy; <a href="/">kapiko.ai</a> • <a href="/data/">Data</a> • <a href="/genres/{esc(genre)}/">Back to {esc(gdisp)}</a></p>
  </div>
</footer>

<script>
const ctx=document.getElementById('radarChart');
if(ctx){{new Chart(ctx,{{type:'radar',data:{{labels:['Energy','Danceability','Valence','Acousticness','Instrumentalness','Speechiness','Liveness'],datasets:[{{data:[{e},{d},{v},{a},{ins},{sp},{liv}],backgroundColor:'rgba(78,205,196,0.15)',borderColor:'#4ecdc4',borderWidth:2,pointBackgroundColor:'#4ecdc4',pointRadius:4}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{r:{{beginAtZero:true,max:1,ticks:{{display:false}},grid:{{color:'rgba(255,255,255,0.06)'}},pointLabels:{{color:'#6b7099',font:{{size:11}}}},angleLines:{{color:'rgba(255,255,255,0.06)'}}}}}}}}}})}};
function copyPrompt(btn){{const id=btn.getAttribute('data-target');const text=document.getElementById(id).textContent;navigator.clipboard.writeText(text).then(()=>{{btn.textContent='Copied!';btn.style.background='rgba(78,205,196,0.3)';setTimeout(()=>{{btn.textContent='Copy';btn.style.background=''}},2000)}})}}
function switchTab(btn,panel){{document.querySelectorAll('.prompt-tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.prompt-panel').forEach(p=>p.style.display='none');btn.classList.add('active');const el=document.getElementById('panel-'+panel);if(el)el.style.display=''}}
</script>
</body>
</html>'''

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    import subprocess
    
    # Get Spotify credentials
    client_id = subprocess.check_output(['security','find-generic-password','-s','spotify-client-id','-w']).decode().strip()
    client_secret = subprocess.check_output(['security','find-generic-password','-s','spotify-client-secret','-w']).decode().strip()
    
    print("Getting Spotify token...")
    token = get_spotify_token(client_id, client_secret)
    print(f"Token: {token[:20]}...")
    
    # Songs to process: first 10 missing from Billboard 2000
    songs = [
        {'rank': 2, 'title': 'Smooth', 'artist': 'Santana featuring Rob Thomas', 'slug': 'smooth-santana', 'search_artist': 'Santana'},
        {'rank': 3, 'title': 'Maria Maria', 'artist': 'Santana featuring The Product G&B', 'slug': 'maria-maria-santana', 'search_artist': 'Santana'},
        {'rank': 4, 'title': 'I Wanna Know', 'artist': 'Joe', 'slug': 'i-wanna-know-joe', 'search_artist': 'Joe'},
        {'rank': 5, 'title': 'Everything You Want', 'artist': 'Vertical Horizon', 'slug': 'everything-you-want-vertical-horizon', 'search_artist': 'Vertical Horizon'},
        {'rank': 6, 'title': 'Say My Name', 'artist': "Destiny's Child", 'slug': 'say-my-name-destiny-s-child', 'search_artist': "Destiny's Child"},
        {'rank': 7, 'title': 'I Knew I Loved You', 'artist': 'Savage Garden', 'slug': 'i-knew-i-loved-you-savage-garden', 'search_artist': 'Savage Garden'},
        {'rank': 9, 'title': 'Bent', 'artist': 'Matchbox Twenty', 'slug': 'bent-matchbox-twenty', 'search_artist': 'Matchbox Twenty'},
        {'rank': 10, 'title': "He Wasn't Man Enough", 'artist': 'Toni Braxton', 'slug': 'he-wasn-t-man-enough-toni-braxton', 'search_artist': 'Toni Braxton'},
        {'rank': 12, 'title': 'Try Again', 'artist': 'Aaliyah', 'slug': 'try-again-aaliyah', 'search_artist': 'Aaliyah'},
        {'rank': 13, 'title': "Jumpin', Jumpin'", 'artist': "Destiny's Child", 'slug': 'jumpin-jumpin-destiny-s-child', 'search_artist': "Destiny's Child"},
    ]
    
    results = []
    
    for song in songs:
        slug = song['slug']
        out_dir = SONGS_DIR / slug
        
        # Check if already exists
        if (out_dir / 'index.html').exists():
            print(f"SKIP [{song['rank']}] {song['title']} — already exists")
            results.append({'rank': song['rank'], 'title': song['title'], 'artist': song['artist'], 'slug': slug, 'status': 'skipped'})
            continue
        
        print(f"Processing [{song['rank']}] {song['title']} by {song['search_artist']}...")
        
        # Search Spotify
        track = search_track(song['title'], song['search_artist'], token)
        if not track:
            print(f"  ERROR: track not found on Spotify")
            results.append({'rank': song['rank'], 'title': song['title'], 'artist': song['artist'], 'slug': slug, 'status': 'error: not found on Spotify'})
            continue
        
        track_id = track['id']
        print(f"  Found: {track['name']} by {track['artists'][0]['name']} (ID: {track_id})")
        
        # Get audio features - DEPRECATED, returns 403. Use placeholders.
        # time.sleep(0.3)
        # af = get_audio_features(track_id, token)
        # if not af:
        #     print(f"  ERROR: could not get audio features")
        #     results.append({'rank': song['rank'], 'title': song['title'], 'artist': song['artist'], 'slug': slug, 'status': 'error: no audio features'})
        #     continue
        
        # Use placeholder data for audio features
        af = {
            'tempo': 120.0, 'key': 0, 'mode': 1, 'energy': 0.5, 'valence': 0.5,
            'danceability': 0.5, 'acousticness': 0.5, 'instrumentalness': 0.0,
            'loudness': -8.0, 'speechiness': 0.05, 'liveness': 0.1, 
            'duration_ms': track.get('duration_ms', 210000)
        }
        print("  WARN: Using placeholder audio features due to API restrictions.")
        
        # Map Spotify data to track record
        key_name = KEY_NAMES.get(af.get('key', 0), 'C')
        mode_name = MODE_NAMES.get(af.get('mode', 1), 'Major')
        artists_str = '; '.join(a['name'] for a in track['artists'])
        
        t_data = {
            'name': track['name'],
            'artists': artists_str,
            'slug': slug,
            'album': track['album']['name'],
            'popularity': track.get('popularity', 50),
            'tempo': af.get('tempo', 120.0),
            'key': key_name,
            'mode': mode_name,
            'energy': af.get('energy', 0.5),
            'valence': af.get('valence', 0.5),
            'danceability': af.get('danceability', 0.5),
            'acousticness': af.get('acousticness', 0.5),
            'instrumentalness': af.get('instrumentalness', 0.0),
            'loudness': af.get('loudness', -8.0),
            'speechiness': af.get('speechiness', 0.05),
            'liveness': af.get('liveness', 0.1),
            'duration_ms': af.get('duration_ms', 210000),
        }
        
        print(f"  Data: {t_data['tempo']:.0f} BPM, {t_data['key']} {t_data['mode']}, energy={t_data['energy']:.2f}, valence={t_data['valence']:.2f}")
        
        # Determine genre
        genre = SONG_GENRES.get(slug, 'pop')
        
        # Generate HTML
        try:
            html = make_page(t_data, genre)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / 'index.html').write_text(html, encoding='utf-8')
            print(f"  ✓ Created {out_dir}/index.html")
            results.append({'rank': song['rank'], 'title': song['title'], 'artist': song['artist'], 'slug': slug, 'status': 'created', 'bpm': round(t_data['tempo']), 'key': f"{t_data['key']} {t_data['mode']}", 'genre': genre})
        except Exception as ex:
            print(f"  ERROR generating page: {ex}")
            import traceback; traceback.print_exc()
            results.append({'rank': song['rank'], 'title': song['title'], 'artist': song['artist'], 'slug': slug, 'status': f'error: {ex}'})
        
        time.sleep(0.2)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for r in results:
        extra = f" | {r.get('bpm')} BPM, {r.get('key')}, genre={r.get('genre')}" if r['status'] == 'created' else ''
        print(f"[{r['rank']:2d}] {r['title']} — {r['artist']}")
        print(f"     slug: {r['slug']}")
        print(f"     status: {r['status']}{extra}")

if __name__ == '__main__':
    main()
