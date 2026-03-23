#!/usr/bin/env python3
"""Generate kapiko song pages from genre analysis.json files.

Usage:
  python3 generate_song_pages.py          # all songs
  python3 generate_song_pages.py 0 200    # slice [0:200]
"""

import json, os, sys, re, html as H
from pathlib import Path

SITE = Path.home() / 'kapiko' / 'site'
GENRES = ['piano', 'sleep', 'chill', 'study', 'classical', 'jazz', 'acoustic', 'electronic', 'hip-hop', 'soul', 'pop', 'r-n-b', 'country', 'rock', 'edm', 'indie', 'folk', 'reggaeton', 'synth-pop', 'trip-hop', 'blues', 'metal', 'funk', 'disco', 'reggae', 'punk', 'house', 'techno', 'trance', 'deep-house', 'dubstep', 'k-pop', 'latin', 'afrobeat', 'j-pop', 'alt-rock', 'grunge', 'hard-rock', 'singer-songwriter', 'indie-pop', 'dance', 'heavy-metal', 'gospel', 'emo', 'ska', 'drum-and-bass', 'progressive-house', 'idm', 'electro', 'punk-rock', 'hardcore', 'psych-rock', 'rock-n-roll', 'indian', 'anime', 'dancehall', 'mandopop', 'bluegrass', 'new-age', 'guitar', 'alternative', 'goth', 'industrial', 'metalcore', 'death-metal', 'dub', 'garage', 'minimal-techno', 'detroit-techno', 'chicago-house', 'hardstyle', 'world-music', 'opera', 'tango', 'salsa', 'j-rock', 'cantopop', 'rockabilly', 'honky-tonk', 'power-pop', 'black-metal', 'brazil', 'breakbeat', 'british', 'children', 'club', 'comedy', 'disney', 'forro', 'french', 'german', 'grindcore', 'groove', 'happy', 'iranian', 'j-dance', 'j-idol', 'kids', 'latino', 'malay', 'mpb', 'pagode', 'party', 'pop-film', 'romance', 'sad', 'samba', 'sertanejo', 'show-tunes', 'songwriter', 'spanish', 'swedish', 'turkish']

def esc(t): return H.escape(str(t))

def primary_artist(artist_str):
    """Return first/primary artist only — drop featured/collaborators."""
    for sep in [',', ' feat.', ' feat ', ' ft.', ' ft ', ' Feat.', ' Feat ', ' x ', ' X ', ' & ', ' with ', ' With ']:
        if sep in artist_str:
            return artist_str.split(sep)[0].strip()
    return artist_str.strip()

def make_title_tag(song_name, artist_str):
    """Build a <title> that fits ~60 chars: Song by Artist — AI Prompt & Analysis | kapiko"""
    artist = primary_artist(artist_str)
    suffix_long = " — AI Prompt & Analysis | kapiko"  # 32 chars
    suffix_short = " — AI Prompt | kapiko"             # 21 chars
    base = f"{song_name} by {artist}"
    if len(base + suffix_long) <= 62:
        return base + suffix_long
    if len(base + suffix_short) <= 62:
        return base + suffix_short
    # Last resort: truncate artist
    return f"{song_name} by {artist[:20]}… — AI Prompt | kapiko"

def fmt_dur(ms):
    s = ms / 1000
    return f"{int(s//60)}:{int(s%60):02d}"

def loud_pct(db):
    return max(0, min(100, (60+db)/60*100))

def get_camelot_key(key, mode):
    """Convert key/mode to Camelot notation."""
    major_keys = {'C': '8B', 'G': '9B', 'D': '10B', 'A': '11B', 'E': '12B', 
                  'B': '1B', 'F#': '2B', 'Db': '3B', 'Ab': '4B', 'Eb': '5B', 
                  'Bb': '6B', 'F': '7B'}
    minor_keys = {'A': '8A', 'E': '9A', 'B': '10A', 'F#': '11A', 'C#': '12A',
                  'G#': '1A', 'D#': '2A', 'Bb': '3A', 'F': '4A', 'C': '5A',
                  'G': '6A', 'D': '7A'}
    
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
        'piano': ['piano','soft keys'],
        'sleep': ['ambient pads','soft drone'],
        'chill': ['electric piano','soft synth'],
        'study': ['lo-fi piano','ambient pads'],
        'classical': ['strings','orchestra'],
        'jazz': ['saxophone','jazz piano','upright bass'],
        'acoustic': ['acoustic guitar','fingerpicking'],
        'electronic': ['synthesizer','drum machine'],
        'hip-hop': ['808 bass','hi-hats','snare'],
        'soul': ['organ','electric piano','bass guitar'],
        'pop': ['synth','programmed drums','electric guitar'],
        'r-n-b': ['808 bass','smooth synth pads','electric piano'],
        'country': ['acoustic guitar','pedal steel','fiddle'],
        'rock': ['electric guitar','drum kit','bass guitar'],
        'edm': ['synth leads','sidechained bass','four-on-the-floor kick'],
        'indie': ['jangly guitar','analog synths','drum machine'],
        'folk': ['acoustic guitar','banjo','mandolin'],
        'reggaeton': ['dembow beat','808 bass','synth stabs'],
        'synth-pop': ['analog synth','drum machine','arpeggiator'],
        'trip-hop': ['breakbeats','jazz samples','deep bass'],
        'blues': ['electric guitar','harmonica','bass guitar'],
        'metal': ['distorted guitar','double bass drum','bass guitar'],
        'funk': ['slap bass','clavinet','wah-wah guitar'],
        'disco': ['string section','rhythm guitar','bass guitar'],
        'reggae': ['skank guitar','deep bass','organ'],
        'punk': ['power chords','fast drums','distorted bass'],
        'house': ['four-on-the-floor kick','hi-hats','synth chords'],
        'techno': ['drum machine','analog synth','acid line'],
        'trance': ['supersaw synth','pluck leads','ethereal pads'],
        'deep-house': ['warm bass','jazz chords','soft pads'],
        'dubstep': ['wobble bass','sub-bass','synth risers'],
        'k-pop': ['synth','programmed drums','vocal harmonies'],
        'latin': ['congas','timbales','acoustic guitar'],
        'afrobeat': ['talking drum','horn section','rhythm guitar'],
        'j-pop': ['synth','electric guitar','piano'],
        'alt-rock': ['distorted guitar','bass','reverb effects'],
        'grunge': ['heavy distortion guitar','pounding drums','bass'],
        'hard-rock': ['overdriven guitar','power chords','heavy drums'],
        'singer-songwriter': ['acoustic guitar','piano','soft vocals'],
        'indie-pop': ['jangly guitar','synth pads','drum machine'],
        'dance': ['synth','programmed drums','bass drops'],
        'heavy-metal': ['heavily distorted guitar','double bass drum','bass guitar'],
        'gospel': ['choir vocals','organ','piano'],
        'emo': ['distorted guitar','bass','reverbed arpeggios'],
        'ska': ['upstroke guitar','trumpet','trombone'],
        'drum-and-bass': ['breakbeats','sub-bass','synth stabs'],
        'progressive-house': ['long synth pads','arpeggiated leads','rolling bassline'],
        'idm': ['granular synth','complex drum patterns','spectral processing'],
        'electro': ['TR-808 drums','analog synth','vocoder'],
        'punk-rock': ['power chords','fast drums','gang vocals'],
        'hardcore': ['heavy riffs','blast beats','shout vocals'],
        'psych-rock': ['fuzz guitar','wah pedal','mellotron'],
        'rock-n-roll': ['electric guitar','upright bass','saxophone'],
        'indian': ['sitar','tabla','harmonium'],
        'anime': ['orchestra','electric guitar','choir'],
        'dancehall': ['digital riddim','synth bass','vocal chatting'],
        'mandopop': ['piano','strings','acoustic guitar'],
        'bluegrass': ['banjo','fiddle','mandolin'],
        'new-age': ['crystal bowls','soft synth pads','flute'],
        'guitar': ['acoustic guitar','electric guitar','classical guitar'],
        'alternative': ['guitar','synths','experimental textures'],
        'goth': ['chorus guitar','synth pads','deep vocals'],
        'industrial': ['distorted synth','metal percussion','processed vocals'],
        'metalcore': ['drop-tuned guitar','blast beats','dual vocals'],
        'death-metal': ['tremolo picking','blast beat drums','guttural vocals'],
        'dub': ['delay effects','sub-bass','melodica'],
        'garage': ['shuffled hi-hats','sub-bass','vocal chops'],
        'minimal-techno': ['click percussion','micro-loops','subtle bass'],
        'detroit-techno': ['analog synth','909 drums','deep bass'],
        'chicago-house': ['TR-909 kick','acid line','gospel vocals'],
        'hardstyle': ['distorted kick','reverse bass','supersaw leads'],
        'world-music': ['diverse traditional instruments','percussion','vocals'],
        'opera': ['orchestra','operatic voice','strings'],
        'tango': ['bandoneon','violin','piano'],
        'salsa': ['congas','timbales','trumpet'],
        'j-rock': ['electric guitar','bass','powerful vocals'],
        'cantopop': ['piano','strings','acoustic guitar'],
        'rockabilly': ['slap bass','twangy guitar','snare drum'],
        'honky-tonk': ['steel guitar','fiddle','honky-tonk piano'],
        'power-pop': ['chiming guitar','vocal harmonies','handclaps'],
        'black-metal': ['tremolo guitar','blast beats','shrieked vocals'],
        'brazil': ['acoustic guitar','percussion','cavaquinho'],
        'breakbeat': ['chopped breaks','heavy bass','synth stabs'],
        'british': ['guitar','bass','drums'],
        'children': ['piano','ukulele','xylophone'],
        'club': ['heavy bass','synth drops','vocal hooks'],
        'comedy': ['various','piano','sound effects'],
        'disney': ['orchestra','piano','choir'],
        'forro': ['accordion','zabumba drum','triangle'],
        'french': ['accordion','guitar','synths'],
        'german': ['synths','guitar','electronic production'],
        'grindcore': ['blast beats','distorted guitar','guttural vocals'],
        'groove': ['heavy riffs','tight drums','bass groove'],
        'happy': ['synths','bright drums','cheerful melodies'],
        'iranian': ['tar','santur','kamancheh'],
        'j-dance': ['synth','electronic drums','bass drops'],
        'j-idol': ['synth','programmed drums','vocal harmonies'],
        'kids': ['ukulele','piano','friendly vocals'],
        'latino': ['congas','trumpet','accordion'],
        'malay': ['rebab','kompang','guitar'],
        'mpb': ['acoustic guitar','piano','percussion'],
        'pagode': ['cavaquinho','pandeiro','banjo'],
        'party': ['heavy bass','synths','brass'],
        'pop-film': ['orchestra','synth','piano'],
        'romance': ['strings','piano','acoustic guitar'],
        'sad': ['piano','strings','soft guitar'],
        'samba': ['surdo','tamborim','cavaquinho'],
        'sertanejo': ['viola caipira','acoustic guitar','accordion'],
        'show-tunes': ['orchestra','piano','brass'],
        'songwriter': ['acoustic guitar','piano','harmonica'],
        'spanish': ['Spanish guitar','cajon','castanets'],
        'swedish': ['synths','guitar','polished production'],
        'turkish': ['baglama','ney','darbuka'],
    }.get(genre, ['various instruments'])
    return ', '.join(base)

def infer_style(genre, energy, acousticness):
    if acousticness > 0.7: return 'organic, warm, natural'
    if energy > 0.7: return 'driving, energetic, produced'
    if energy < 0.3: return 'minimal, ambient, sparse'
    return 'polished, balanced, studio-quality'

def get_track_genres(track_slug, all_genres_data):
    """Find all genres this track appears in."""
    genres = []
    for genre, data in all_genres_data.items():
        if any(t.get('slug') == track_slug for t in data.get('tracks', [])):
            genres.append(genre)
    return genres

def find_similar_songs(track_slug, track_artist, track_key, track_mode, primary_genre, all_genres_data):
    """Find similar songs by artist, genre, and key. Deduplicates across sections."""
    similar_artist = []
    similar_genre = []
    similar_key = []
    seen_slugs = {track_slug}  # track our own slug + anything already added
    
    key_mode = f"{track_key} {track_mode}"
    
    for genre, data in all_genres_data.items():
        for track in data.get('tracks', []):
            slug = track.get('slug', '')
            if not slug or slug in seen_slugs:
                continue
            
            entry = {
                'name': track.get('name'),
                'artist': track.get('artists', '').split(';')[0].strip(),
                'tempo': track.get('tempo', 120),
                'key': f"{track.get('key', 'C')} {track.get('mode', 'Major')}",
                'slug': slug,
                'genre': genre
            }
            
            # More from same artist (match on first artist)
            first_artist = track.get('artists', '').split(';')[0].strip()
            track_first_artist = track_artist.split(';')[0].strip()
            if first_artist == track_first_artist and len(similar_artist) < 6:
                similar_artist.append(entry)
                seen_slugs.add(slug)
            
            # Same genre (but different artist, not already used)
            elif (genre == primary_genre and slug not in seen_slugs and 
                  len(similar_genre) < 6):
                similar_genre.append(entry)
                seen_slugs.add(slug)
            
            # Same key (any genre, not already used)
            elif (f"{track.get('key', 'C')} {track.get('mode', 'Major')}" == key_mode and
                  slug not in seen_slugs and len(similar_key) < 6):
                similar_key.append(entry)
                seen_slugs.add(slug)
    
    return similar_artist[:6], similar_genre[:6], similar_key[:6]

GENRE_DISPLAY = {
    'piano':'Piano','sleep':'Sleep','chill':'Chill','study':'Study',
    'classical':'Classical','jazz':'Jazz','acoustic':'Acoustic',
    'electronic':'Electronic','hip-hop':'Hip-Hop','soul':'Soul',
    'ambient':'Ambient','lofi-hip-hop':'Lo-Fi Hip Hop',
    'neo-classical':'Neo-Classical','focus':'Focus','jazz-piano':'Jazz Piano'
}

def make_page(t, genre, all_genres_data=None):
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
    
    # Get track genres and similar songs
    track_genres = get_track_genres(slug, all_genres_data) if all_genres_data else [genre]
    similar_artist, similar_genre, similar_key = find_similar_songs(
        slug, artist, key, mode, genre, all_genres_data) if all_genres_data else ([], [], [])
    
    gen_prompt = f"Create a {gdisp.lower()} track at {tempo:.0f} BPM in {key_mode}. {instruments}. Mood: {mood}. Style: {style}. Target energy {e*100:.0f}%, valence {v*100:.0f}%."
    suno_prompt = f"{gdisp.lower()}, {mood}, {instruments}, {style}, {tempo:.0f} BPM"
    udio_prompt = f"A {gdisp.lower()} track that feels {mood} with {instruments} — {style} in the style of {artist.split(';')[0]}"
    agent_json = json.dumps({
        "track_reference": {"title": name, "artist": artist},
        "generation_params": {"bpm": round(tempo), "key": key_mode, "duration": dur_str, "energy": round(e,3), "valence": round(v,3), "acousticness": round(a,3), "instrumentalness": round(ins,3)},
        "style": {"genre": genre, "mood": mood, "instruments": instruments.split(', '), "production": style},
        "prompt": gen_prompt
    }, indent=2)
    
    # Build genre pills
    genre_pills = ''.join(f'<a href="/genres/{g}/" class="pill genre">{GENRE_DISPLAY.get(g, g.replace("-", " ").title())}</a>' 
                         for g in sorted(track_genres)[:5])
    
    # Build similar songs sections
    def format_song_card(song, link_type="song"):
        href = f"/songs/{song['slug']}/" if song.get('slug') else '#'
        return f'''
        <a href="{href}" class="similar-card">
          <div class="similar-title">{esc(song['name'])}</div>
          <div class="similar-artist">{esc(song['artist'])}</div>
          <div class="similar-meta">{song['tempo']:.0f} BPM • {esc(song['key'])}</div>
        </a>'''
    
    similar_artist_html = ''
    if similar_artist:
        similar_artist_html = f'''
        <div class="section-label"><h2>More from {esc(artist.split(';')[0])}</h2></div>
        <div class="similar-grid">
          {"".join(format_song_card(s) for s in similar_artist)}
        </div>'''
    
    similar_genre_html = ''
    if similar_genre:
        similar_genre_html = f'''
        <div class="section-label"><h2>Similar in {esc(gdisp)}</h2></div>
        <div class="similar-grid">
          {"".join(format_song_card(s) for s in similar_genre)}
        </div>'''
    
    similar_key_html = ''
    if similar_key:
        similar_key_html = f'''
        <div class="section-label"><h2>Songs in {esc(key_mode)}</h2></div>
        <div class="similar-grid">
          {"".join(format_song_card(s) for s in similar_key)}
        </div>'''
    
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
    "sameAs": [
      "https://open.spotify.com/search/{esc(name.replace(' ', '%20'))}%20{esc(primary_artist(artist).replace(' ', '%20'))}",
      "https://www.youtube.com/results?search_query={esc(name.replace(' ', '+'))}+{esc(primary_artist(artist).replace(' ', '+'))}"
    ],
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
    "name": "How to Recreate \"{esc(name)}\" by {esc(primary_artist(artist))} with AI",
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
    
    /* Header */
    header{{background:#0d0e20;border-bottom:1px solid var(--border);padding:2rem 0}}
    .breadcrumb{{color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem}}
    .breadcrumb a{{color:var(--teal);text-decoration:none}}.breadcrumb a:hover{{text-decoration:underline}}
    .hero-content{{display:grid;grid-template-columns:160px 1fr;gap:1.5rem;align-items:start}}
    .album-art{{width:160px;height:160px;border-radius:12px;background:var(--bg-card);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;color:var(--text-muted);font-size:0.8rem}}
    .hero-info h1{{font-size:2rem;font-weight:700;margin-bottom:0.3rem}}
    .hero-artist{{font-size:1.1rem;color:var(--purple);font-weight:500;margin-bottom:1rem}}
    .metadata-row{{display:flex;flex-direction:column;gap:0.3rem;font-size:0.9rem;margin-bottom:1rem}}
    .metadata-item{{color:var(--text-muted)}}
    .spotify-btn{{display:inline-flex;align-items:center;gap:0.5rem;background:#1DB954;color:#fff;text-decoration:none;padding:0.6rem 1.2rem;border-radius:6px;font-weight:600;font-size:0.85rem;margin-bottom:1rem}}
    .spotify-btn:hover{{background:#1ed760}}
    .listen-links{{display:flex;gap:0.6rem;margin-top:0.5rem;align-items:center}}
    .listen-links a{{display:flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:50%;background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);transition:color 0.2s,border-color 0.2s;text-decoration:none}}
    .listen-links a:hover{{color:var(--teal);border-color:var(--teal)}}
    .listen-links a svg{{width:16px;height:16px;fill:currentColor}}
    .genre-tags{{display:flex;flex-wrap:wrap;gap:0.4rem}}
    .pill{{background:rgba(91,155,213,0.1);color:var(--blue);border:1px solid rgba(91,155,213,0.2);border-radius:20px;padding:0.3rem 0.8rem;font-size:0.8rem;text-decoration:none}}
    .pill.genre:hover{{background:rgba(91,155,213,0.2)}}
    
    /* YouTube */
    .yt-section{{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.5rem;margin:2rem 0}}
    .yt-embed{{position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px}}
    .yt-embed iframe{{position:absolute;top:0;left:0;width:100%;height:100%}}
    
    /* Stat cards */
    .stats-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1rem;margin:2rem 0}}
    .stat-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1rem;text-align:center}}
    .stat-val{{font-size:1.5rem;font-weight:700;color:var(--teal)}}
    .stat-label{{font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.05em;margin-top:0.2rem}}
    .stat-key{{font-size:0.75rem;color:var(--text-muted);margin-top:0.2rem}}
    
    /* Sections */
    .section-label{{margin:2.5rem 0 1rem}}
    .section-label h2{{font-size:0.8rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--teal);font-weight:600}}
    
    /* Charts */
    .chart-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem}}
    .chart-wrap{{height:280px;position:relative}}
    .audio-features-grid{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;align-items:start}}
    
    /* Feature bars */
    .feature-bars{{display:flex;flex-direction:column;gap:0.8rem}}
    .feature-item{{display:grid;grid-template-columns:130px 50px 1fr;align-items:center;gap:0.5rem}}
    .feature-label{{font-size:0.85rem;color:var(--text-muted)}}
    .feature-val{{font-size:0.85rem;font-weight:600;text-align:right}}
    .feature-track{{height:6px;background:rgba(255,255,255,0.05);border-radius:3px;overflow:hidden}}
    .feature-fill{{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--teal),var(--purple))}}
    
    /* Similar songs */
    .similar-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem}}
    a.similar-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1rem;text-decoration:none;color:inherit;display:block;transition:border-color 0.2s,transform 0.2s}}
    a.similar-card:hover{{border-color:rgba(78,205,196,0.3);transform:translateY(-2px)}}
    .similar-title{{font-weight:600;margin-bottom:0.2rem}}
    .similar-artist{{color:var(--text-muted);font-size:0.9rem;margin-bottom:0.3rem}}
    .similar-meta{{color:var(--text-muted);font-size:0.8rem}}
    
    /* Prompt lab */
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
    
    /* Footer */
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

<!-- Header -->
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
          <a href="https://open.spotify.com/search/{esc(name.replace(' ', '%20'))}%20{esc(primary_artist(artist).replace(' ', '%20'))}" target="_blank" rel="noopener" title="Find on Spotify">
            <svg viewBox="0 0 24 24"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>
          </a>
          <a href="https://www.youtube.com/results?search_query={esc(name.replace(' ', '+'))}+{esc(primary_artist(artist).replace(' ', '+'))}" target="_blank" rel="noopener" title="Find on YouTube">
            <svg viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
          </a>
        </div>
        <div class="genre-tags">
          {genre_pills}
        </div>
      </div>
    </div>
  </div>
</header>

<div class="container">

  <!-- YouTube Listen Section -->
  <div class="section-label"><h2>Listen</h2></div>
  <div class="yt-section">
    <p style="color:var(--text-muted);text-align:center;font-style:italic;">YouTube embed would appear here if available</p>
  </div>

  <!-- Overview Stats -->
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

  <!-- Audio Features -->
  <div class="section-label"><h2>Audio Features</h2></div>
  <div class="chart-card">
    <div class="audio-features-grid">
      <div class="chart-wrap" style="height:250px">
        <canvas id="radarChart"></canvas>
      </div>
      <div class="feature-bars">
        <div class="feature-item">
          <div class="feature-label">Energy</div>
          <div class="feature-val">{e*100:.1f}%</div>
          <div class="feature-track"><div class="feature-fill" style="width:{e*100:.0f}%"></div></div>
        </div>
        <div class="feature-item">
          <div class="feature-label">Danceability</div>
          <div class="feature-val">{d*100:.1f}%</div>
          <div class="feature-track"><div class="feature-fill" style="width:{d*100:.0f}%"></div></div>
        </div>
        <div class="feature-item">
          <div class="feature-label">Valence</div>
          <div class="feature-val">{v*100:.1f}%</div>
          <div class="feature-track"><div class="feature-fill" style="width:{max(v*100,2):.0f}%"></div></div>
        </div>
        <div class="feature-item">
          <div class="feature-label">Acousticness</div>
          <div class="feature-val">{a*100:.1f}%</div>
          <div class="feature-track"><div class="feature-fill" style="width:{a*100:.0f}%"></div></div>
        </div>
        <div class="feature-item">
          <div class="feature-label">Instrumentalness</div>
          <div class="feature-val">{ins*100:.1f}%</div>
          <div class="feature-track"><div class="feature-fill" style="width:{max(ins*100,2):.0f}%"></div></div>
        </div>
        <div class="feature-item">
          <div class="feature-label">Speechiness</div>
          <div class="feature-val">{sp*100:.1f}%</div>
          <div class="feature-track"><div class="feature-fill" style="width:{max(sp*100,2):.0f}%"></div></div>
        </div>
        <div class="feature-item">
          <div class="feature-label">Liveness</div>
          <div class="feature-val">{liv*100:.1f}%</div>
          <div class="feature-track"><div class="feature-fill" style="width:{max(liv*100,2):.0f}%"></div></div>
        </div>
        <div class="feature-item">
          <div class="feature-label">Loudness</div>
          <div class="feature-val">{loud:.1f} dB</div>
          <div class="feature-track"><div class="feature-fill" style="width:{loud_pct(loud):.0f}%"></div></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Prompt Lab -->
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

  <!-- Similar Songs -->
  {similar_artist_html}
  {similar_genre_html}  
  {similar_key_html}

</div>

<!-- Footer -->
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

def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 999999
    
    # Load all genre data for similar songs feature
    all_genres_data = {}
    for g in GENRES:
        apath = SITE / 'genres' / g / 'analysis.json'
        if apath.exists():
            try:
                data = json.load(open(apath))
                all_genres_data[g] = data
            except:
                continue
    
    # Collect all unique songs across all genres
    all_songs = {}  # slug -> (track_data, genre)
    for g in GENRES:
        apath = SITE / 'genres' / g / 'analysis.json'
        if not apath.exists():
            continue
        data = json.load(open(apath))
        for t in data['tracks']:
            slug = t.get('slug', '')
            if slug and slug not in all_songs:
                all_songs[slug] = (t, g)
    
    slugs = sorted(all_songs.keys())
    subset = slugs[start:end]
    
    print(f"Total unique songs: {len(slugs)}")
    print(f"Processing slice [{start}:{end}] = {len(subset)} songs")
    
    created = 0
    skipped = 0
    errors = 0
    
    for slug in subset:
        song_dir = SITE / 'songs' / slug
        if song_dir.exists() and (song_dir / 'index.html').exists():
            skipped += 1
            continue
        
        t, g = all_songs[slug]
        try:
            html = make_page(t, g, all_genres_data)
            song_dir.mkdir(parents=True, exist_ok=True)
            (song_dir / 'index.html').write_text(html, encoding='utf-8')
            created += 1
            if created % 50 == 0:
                print(f"  ...{created} created so far")
        except Exception as ex:
            errors += 1
            print(f"  ERROR {slug}: {ex}")
    
    print(f"\nDone! Created: {created}, Skipped (existing): {skipped}, Errors: {errors}")

if __name__ == '__main__':
    main()