#!/usr/bin/env python3
"""Generate kapiko song pages from genre analysis.json files.

Template matches the reference: /songs/experience-ludovico-einaudi/

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
    for sep in [',', ' feat.', ' feat ', ' ft.', ' ft ', ' Feat.', ' Feat ', ' x ', ' X ', ' & ', ' with ', ' With ']:
        if sep in artist_str:
            return artist_str.split(sep)[0].strip()
    return artist_str.strip()

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
    return minor_keys.get(key, f'{key}A')

def infer_mood(energy, valence):
    if energy < 0.3 and valence < 0.3: return 'melancholic / introspective'
    if energy < 0.3 and valence >= 0.3: return 'peaceful / serene'
    if energy < 0.5 and valence < 0.4: return 'contemplative / moody'
    if energy < 0.5 and valence >= 0.4: return 'relaxed / warm'
    if energy < 0.7 and valence < 0.4: return 'intense / brooding'
    if energy < 0.7 and valence >= 0.4: return 'upbeat / groovy'
    if valence >= 0.5: return 'energetic / joyful'
    return 'powerful / dark'

def infer_atmosphere(energy, valence, acousticness):
    if acousticness > 0.7 and energy < 0.4: return 'intimate'
    if energy > 0.7: return 'explosive'
    if valence < 0.3: return 'expansive'
    if energy < 0.4: return 'ethereal'
    return 'vibrant'

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
    return base  # Return as list now

def infer_production_style(genre, energy, acousticness):
    if acousticness > 0.7: return 'organic acoustic recording'
    if energy > 0.7 and acousticness < 0.3: return 'heavily produced digital'
    if energy < 0.3: return 'minimal ambient processing'
    return 'polished studio production'

def infer_production_effects(energy, acousticness, instrumentalness):
    effects = []
    if acousticness > 0.5: effects.append('natural room reverb')
    else: effects.append('reverb tail')
    if energy < 0.4: effects.append('delay')
    if instrumentalness > 0.5: effects.append('spatial panning')
    return effects

def infer_texture(energy, acousticness):
    if energy < 0.3: return 'sparse'
    if energy < 0.5: return 'layered'
    if energy < 0.7: return 'dense'
    return 'wall-of-sound'

def infer_dynamics(energy, valence):
    if energy < 0.3: return 'static'
    if energy < 0.5: return 'gentle swells'
    if energy < 0.7: return 'dynamic'
    return 'explosive'

def infer_stereo(energy, acousticness):
    if energy < 0.3: return 'wide'
    if acousticness > 0.6: return 'intimate'
    return 'moderate'

def infer_energy_label(e):
    if e < 0.2: return 'very low'
    if e < 0.4: return 'subdued'
    if e < 0.6: return 'moderate'
    if e < 0.8: return 'high'
    return 'explosive'

def infer_energy_tags(e):
    if e < 0.3: return ['subdued','restrained','understated','soft']
    if e < 0.5: return ['moderate','balanced','controlled','steady']
    if e < 0.7: return ['energetic','driving','powerful','dynamic']
    return ['explosive','intense','relentless','fierce']

def infer_mood_tags(valence):
    if valence < 0.2: return ['melancholic','somber','introspective','heavy']
    if valence < 0.4: return ['contemplative','moody','bittersweet','pensive']
    if valence < 0.6: return ['warm','hopeful','nostalgic','gentle']
    if valence < 0.8: return ['uplifting','bright','cheerful','positive']
    return ['euphoric','ecstatic','triumphant','jubilant']

def infer_vocals(instrumentalness, speechiness):
    if instrumentalness > 0.5: return 'None'
    if speechiness > 0.3: return 'Prominent Vocals'
    return 'Vocal Lead'

def infer_harmony(acousticness, energy):
    if acousticness > 0.7: return 'Simple Chords'
    if energy > 0.7: return 'Power Chords'
    return 'Rich Harmony'

def infer_rhythm(energy, danceability):
    if energy < 0.3: return 'Subtle Pulse'
    if danceability > 0.7: return 'Strong Groove'
    if energy > 0.7: return 'Driving Beat'
    return 'Steady Rhythm'

def infer_notable(name, artist, genre, mood, instruments_list, production_style):
    inst_str = ' and '.join(instruments_list[:2]) if len(instruments_list) >= 2 else instruments_list[0]
    return f"A distinctive {genre.replace('-', ' ')} track featuring {inst_str}, creating a {mood.split('/')[0].strip().lower()} soundscape."

def infer_similar_artists(artist, genre):
    # Simple similar artist inference based on genre
    genre_artists = {
        'piano': ['Ludovico Einaudi', 'Yiruma'],
        'classical': ['Chopin', 'Debussy'],
        'jazz': ['Miles Davis', 'John Coltrane'],
        'rock': ['Foo Fighters', 'Arctic Monkeys'],
        'pop': ['Taylor Swift', 'Ed Sheeran'],
        'hip-hop': ['Kendrick Lamar', 'J. Cole'],
        'electronic': ['Aphex Twin', 'Boards of Canada'],
        'r-n-b': ['SZA', 'Frank Ocean'],
        'country': ['Luke Combs', 'Morgan Wallen'],
        'metal': ['Metallica', 'Iron Maiden'],
        'indie': ['Radiohead', 'Tame Impala'],
        'folk': ['Fleet Foxes', 'Bon Iver'],
    }
    artists = genre_artists.get(genre, [primary_artist(artist)])
    # Filter out the track's own artist
    pa = primary_artist(artist)
    return [a for a in artists if a != pa][:2] or [pa]


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
    'progressive-house':'Progressive House','idm':'IDM','electro':'Electro',
    'punk-rock':'Punk Rock','hardcore':'Hardcore','psych-rock':'Psych Rock',
    'rock-n-roll':'Rock & Roll','indian':'Indian','anime':'Anime',
    'dancehall':'Dancehall','mandopop':'Mandopop','bluegrass':'Bluegrass',
    'new-age':'New Age','guitar':'Guitar','alternative':'Alternative',
    'goth':'Goth','industrial':'Industrial','metalcore':'Metalcore',
    'death-metal':'Death Metal','dub':'Dub','garage':'Garage',
    'minimal-techno':'Minimal Techno','detroit-techno':'Detroit Techno',
    'chicago-house':'Chicago House','hardstyle':'Hardstyle',
    'world-music':'World Music','opera':'Opera','tango':'Tango',
    'salsa':'Salsa','j-rock':'J-Rock','cantopop':'Cantopop',
}

def get_track_genres(track_slug, all_genres_data):
    genres = []
    for genre, data in all_genres_data.items():
        if any(t.get('slug') == track_slug for t in data.get('tracks', [])):
            genres.append(genre)
    return genres

# ── HTML Template (matches reference: experience-ludovico-einaudi) ────────

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
    
    # Optional fields from enriched data
    album_img = t.get('album_image', '')
    spotify_url = t.get('spotify_url', '')
    youtube_url = t.get('youtube_url', '')
    youtube_id = t.get('youtube_id', '')
    
    dur_str = fmt_dur(dur_ms)
    key_mode = f"{key} {mode}"
    key_short = f"{key} {'Maj' if mode == 'Major' else 'Min'}"
    camelot_key = get_camelot_key(key, mode)
    gdisp = GENRE_DISPLAY.get(genre, genre.replace('-',' ').title())
    
    # Infer all analysis fields
    mood = infer_mood(e, v)
    atmosphere = infer_atmosphere(e, v, a)
    instruments_list = infer_instruments(genre, a, ins, e)
    instruments_str = ', '.join(instruments_list)
    production_style = infer_production_style(genre, e, a)
    production_effects = infer_production_effects(e, a, ins)
    texture = infer_texture(e, a)
    dynamics = infer_dynamics(e, v)
    stereo = infer_stereo(e, a)
    energy_tags = infer_energy_tags(e)
    mood_tags = infer_mood_tags(v)
    vocals = infer_vocals(ins, sp)
    harmony = infer_harmony(a, e)
    rhythm = infer_rhythm(e, d)
    notable = infer_notable(name, artist, gdisp.lower(), mood, instruments_list, production_style)
    similar_artists = infer_similar_artists(artist, genre)
    
    track_genres = get_track_genres(slug, all_genres_data) if all_genres_data else [genre]
    genre_tags_list = sorted(set(track_genres))[:5]
    if genre not in genre_tags_list:
        genre_tags_list = [genre] + genre_tags_list[:4]
    
    pa = primary_artist(artist)
    
    # Build prompts
    gen_prompt = f"Create a {dur_str} {gdisp.lower()} track at {tempo:.0f} BPM in {key_mode}. {'Instrumental' if ins > 0.5 else 'With vocals'} — {instruments_str}. {mood.capitalize()} and {atmosphere}. {production_style.capitalize()}, with {production_effects[0]}. {texture.capitalize()} texture, {dynamics} dynamics, {stereo} stereo field. {'Subdued' if e < 0.4 else 'Moderate' if e < 0.6 else 'High'} energy ({e*100:.0f}%), {'melancholic' if v < 0.3 else 'warm' if v < 0.6 else 'bright'} mood ({v*100:.0f}%). Think {' meets '.join(similar_artists[:2])}."
    suno_prompt = f"{gdisp.lower()}, {mood.replace(' / ', ', ')}, {atmosphere}, {instruments_str}, {'subdued' if e < 0.4 else 'energetic'}, {production_style}, {production_effects[0]}"
    udio_prompt = f"A {gdisp.lower()} track that feels {mood} and {atmosphere} with {instruments_str} — {production_style} in the style of {' and '.join(similar_artists[:2])}"
    agent_json = json.dumps({
        "track_reference": {"title": name, "artist": artist},
        "generation_params": {"bpm": round(tempo), "key": key_mode, "duration": dur_str, "energy": round(e,3), "valence": round(v,3), "acousticness": round(a,3), "instrumentalness": round(ins,3)},
        "style": {"genres": [GENRE_DISPLAY.get(g, g.replace('-',' ').title()) for g in genre_tags_list], "mood": mood, "atmosphere": atmosphere, "instruments": instruments_list, "primary_instrument": instruments_list[0], "vocals": vocals},
        "production": {"style": production_style, "effects": production_effects, "texture": texture, "dynamics": dynamics, "stereo": stereo},
        "reference_artists": similar_artists,
        "prompt": gen_prompt
    }, indent=2)
    
    # Spotify/YouTube fallback URLs
    if not spotify_url:
        spotify_url = f"https://open.spotify.com/search/{H.escape(name.replace(' ', '%20'))}%20{H.escape(pa.replace(' ', '%20'))}"
    if not youtube_url:
        youtube_url = f"https://www.youtube.com/results?search_query={H.escape(name.replace(' ', '+'))}+{H.escape(pa.replace(' ', '+'))}"
    
    # Album art HTML
    album_art_html = f'<img src="{esc(album_img)}" alt="{esc(album)} — {esc(pa)} album cover" loading="lazy">' if album_img else f'<div style="display:flex;align-items:center;justify-content:center;width:100%;height:100%;color:var(--text-muted);font-size:2.5rem;font-family:var(--serif);">{esc(name[0])}</div>'
    
    # OG image meta
    og_image_meta = f'''  <meta property="og:image" content="{esc(album_img)}">
  <meta property="og:image:width" content="640">
  <meta property="og:image:height" content="640">
  <meta property="og:image:alt" content="{esc(album)} album cover — {esc(pa)}">
  <meta name="twitter:image" content="{esc(album_img)}">''' if album_img else ''
    
    og_audio = f'\n  <meta property="og:audio" content="{esc(spotify_url)}">\n  <meta property="og:audio:type" content="audio/vnd.spotify.track">' if spotify_url.startswith('https://open.spotify.com/track/') else ''
    
    # YouTube embed
    yt_section = ''
    if youtube_id:
        yt_section = f'''
  <div class="section-heading">
    <h2>Listen</h2>
    <div class="line"></div>
  </div>
  <div class="yt-card">
    <div class="yt-embed">
      <iframe src="https://www.youtube.com/embed/{esc(youtube_id)}" allow="autoplay; encrypted-media" allowfullscreen loading="lazy" title="{esc(name)} — {esc(pa)}"></iframe>
    </div>
  </div>'''
    
    # Instruments FAQ answer
    inst_faq = f"The primary instruments are {instruments_str}, with {production_style} and {production_effects[0]} production."
    
    # Genre tags for AI Analysis section
    genre_tag_chips = ''.join(f'<span class="tag blue">{esc(GENRE_DISPLAY.get(g, g.replace("-"," ").title()))}</span>' for g in genre_tags_list)
    
    # Similar artist chips
    similar_chips = ''.join(f'<span class="tag neutral">{esc(a)}</span>' for a in similar_artists)
    
    # Instrument chips
    inst_chips = ''.join(f'<span class="tag">{esc(i)}</span>' for i in instruments_list)
    
    # Production effect chips
    effect_chips = ''.join(f'<span class="tag purple">{esc(fx)}</span>' for fx in production_effects)
    
    # Energy tag chips
    energy_tag_chips = ''.join(f'<span class="tag">{esc(t)}</span>' for t in energy_tags)
    
    # Mood tag chips
    mood_tag_chips = ''.join(f'<span class="tag purple">{esc(t)}</span>' for t in mood_tags)
    
    # Key tags
    key_type = 'major' if mode == 'Major' else 'minor'
    key_tags = f'<span class="tag blue">{key_type}</span><span class="tag blue">{harmony.lower().replace(" ", "-")}</span>'
    
    # Production value display
    prod_val = production_style
    
    # Nav genre link
    nav_genre_link = f'<li><a href="/genres/{esc(genre)}/">{esc(gdisp)}</a></li>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(make_title_tag(name, artist))}</title>
  <meta name="description" content="Recreate {esc(name)} by {esc(pa)} using AI music generators like Suno and Udio. Copy our data-driven prompts — includes full audio analysis: {tempo:.0f} BPM, {esc(key_mode)}, mood, instrumentation &amp; production breakdown.">
  <meta property="og:title" content="Recreate &quot;{esc(name)}&quot; by {esc(pa)} with AI — kapiko">
  <meta property="og:description" content="Data-driven AI music prompts for Suno, Udio &amp; more. Full audio analysis of {esc(name)} — BPM, key, mood, instrumentation.">
  <meta property="og:type" content="music.song">
  <meta property="og:url" content="https://kapiko.ai/songs/{esc(slug)}/">
  <meta property="og:site_name" content="kapiko">
{og_image_meta}{og_audio}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Recreate &quot;{esc(name)}&quot; by {esc(pa)} with AI — kapiko">
  <meta name="twitter:description" content="Data-driven AI music prompts for Suno, Udio &amp; more. Full audio analysis of {esc(name)} — BPM, key, mood, instrumentation.">
  <meta name="twitter:site" content="@kapiko_ai">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://kapiko.ai/songs/{esc(slug)}/">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Pacifico&family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "MusicRecording",
    "name": "{esc(name)}",
    "duration": "PT{int(dur_ms/60000)}M{int((dur_ms%60000)/1000)}S",
    "byArtist": [{{ "@type": "MusicGroup", "name": "{esc(pa)}" }}],
    {"\"inAlbum\": { \"@type\": \"MusicAlbum\", \"name\": \"" + esc(album) + "\"" + (', \"image\": \"' + esc(album_img) + '\"' if album_img else '') + " }," if album else ""}
    {"\"image\": \"" + esc(album_img) + "\"," if album_img else ""}
    "genre": [{', '.join('"' + esc(GENRE_DISPLAY.get(g, g.replace('-',' ').title())) + '"' for g in genre_tags_list)}],
    "url": "https://kapiko.ai/songs/{esc(slug)}/",
    "sameAs": ["{esc(spotify_url)}", "{esc(youtube_url)}"],
    "publisher": {{ "@type": "Organization", "name": "kapiko", "url": "https://kapiko.ai" }}
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "kapiko", "item": "https://kapiko.ai/" }},
      {{ "@type": "ListItem", "position": 2, "name": "{esc(gdisp)}", "item": "https://kapiko.ai/genres/{esc(genre)}/" }},
      {{ "@type": "ListItem", "position": 3, "name": "{esc(name)} — {esc(pa)}" }}
    ]
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {{ "@type": "Question", "name": "What BPM is {esc(name)} by {esc(pa)}?", "acceptedAnswer": {{ "@type": "Answer", "text": "{esc(name)} by {esc(pa)} is {tempo:.0f} BPM." }} }},
      {{ "@type": "Question", "name": "What key is {esc(name)} by {esc(pa)} in?", "acceptedAnswer": {{ "@type": "Answer", "text": "{esc(name)} is in {esc(key_mode)}." }} }},
      {{ "@type": "Question", "name": "What instruments are in {esc(name)} by {esc(pa)}?", "acceptedAnswer": {{ "@type": "Answer", "text": "{esc(inst_faq)}" }} }},
      {"\"@type\": \"Question\", \"name\": \"What album is " + esc(name) + " by " + esc(pa) + " from?\", \"acceptedAnswer\": { \"@type\": \"Answer\", \"text\": \"" + esc(name) + " is from the album " + esc(album) + ".\" }" if album else ""}
      {{ "@type": "Question", "name": "How do I recreate {esc(name)} by {esc(pa)} with AI?", "acceptedAnswer": {{ "@type": "Answer", "text": "Use the prompt: {esc(gen_prompt)} Paste into Suno, Udio, MiniMax Music, ElevenLabs, or any AI music generator." }} }}
    ]
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "HowTo",
    "name": "How to Recreate \\"{esc(name)}\\" by {esc(pa)} with AI",
    "description": "Use data-driven prompts to recreate the sound of {esc(name)} using Suno, Udio, or any AI music generator.",
    "step": [
      {{ "@type": "HowToStep", "name": "Choose your AI music tool", "text": "Select Suno, Udio, or another AI music generation service." }},
      {{ "@type": "HowToStep", "name": "Copy the prompt", "text": "Copy the ready-to-use prompt: {esc(gen_prompt)}" }},
      {{ "@type": "HowToStep", "name": "Generate and refine", "text": "Paste the prompt into your chosen tool, generate the track, and iterate on the results." }}
    ]
  }}
  </script>

  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #08090f; --bg-raised: #0e1019; --bg-card: #12131f; --bg-card-hover: #161726;
      --border: rgba(255,255,255,0.06); --border-accent: rgba(78,205,196,0.18);
      --text: #e2e5f0; --text-secondary: #a0a5c0; --text-muted: #5a5f80;
      --accent: #4ecdc4; --accent-dim: rgba(78,205,196,0.12); --accent-mid: rgba(78,205,196,0.22);
      --purple: #a78bfa; --purple-dim: rgba(167,139,250,0.12);
      --blue: #60a5fa; --amber: #fbbf24;
      --serif: 'DM Serif Display', Georgia, serif;
      --sans: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      --mono: 'JetBrains Mono', 'SF Mono', monospace;
    }}
    html {{ scroll-behavior: smooth; }}
    body {{ font-family: var(--sans); background: var(--bg); color: var(--text); line-height: 1.6; -webkit-font-smoothing: antialiased; }}
    .container {{ max-width: 880px; margin: 0 auto; padding: 0 1.5rem; }}

    /* Nav */
    .topnav {{ background: var(--bg); border-bottom: 1px solid var(--border); padding: 0.8rem 0; position: sticky; top: 0; z-index: 100; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }}
    .topnav-inner {{ display: flex; justify-content: space-between; align-items: center; }}
    .topnav-logo {{ font-family: 'Pacifico', cursive; font-size: 1.15rem; color: var(--text); text-decoration: none; }}
    .topnav-links {{ display: flex; gap: 1.5rem; list-style: none; }}
    .topnav-links a {{ color: var(--text-muted); text-decoration: none; font-size: 0.82rem; font-weight: 500; letter-spacing: 0.02em; transition: color 0.2s; }}
    .topnav-links a:hover {{ color: var(--accent); }}

    /* Hero */
    .hero {{ padding: 2.5rem 0 1.5rem; border-bottom: 1px solid var(--border); position: relative; }}
    .hero::before {{ content: ''; position: absolute; inset: 0; background: radial-gradient(ellipse 60% 50% at 50% 0%, rgba(78,205,196,0.04), transparent); pointer-events: none; }}
    .breadcrumb {{ font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1.2rem; display: flex; gap: 0.4rem; align-items: center; }}
    .breadcrumb a {{ color: var(--accent); text-decoration: none; font-weight: 500; }}
    .breadcrumb a:hover {{ text-decoration: underline; }}
    .breadcrumb .sep {{ opacity: 0.4; }}
    .hero-content {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 2rem; }}
    .hero-text {{ flex: 1; }}
    .album-art {{ flex-shrink: 0; width: 180px; height: 180px; border-radius: 10px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.5); background: var(--bg-card); }}
    .album-art img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    @media (max-width: 600px) {{ .album-art {{ width: 120px; height: 120px; }} }}
    h1 {{ font-family: var(--serif); font-size: 2.6rem; font-weight: 400; letter-spacing: -0.03em; line-height: 1.15; margin-bottom: 0.4rem; }}
    .artist-name {{ font-size: 1.05rem; color: var(--purple); font-weight: 500; margin-bottom: 0.25rem; }}
    .album-name {{ font-size: 0.85rem; color: var(--text-muted); font-style: italic; }}
    .listen-links {{ display: flex; gap: 0.6rem; margin-top: 0.5rem; align-items: center; }}
    .listen-links a {{ display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 50%; background: var(--bg-card); border: 1px solid var(--border); color: var(--text-muted); transition: color 0.2s, border-color 0.2s; text-decoration: none; }}
    .listen-links a:hover {{ color: var(--accent); border-color: var(--accent); }}
    .listen-links a svg {{ width: 16px; height: 16px; fill: currentColor; }}
    .stats-strip {{ display: flex; gap: 0.5rem; margin-top: 1.2rem; flex-wrap: wrap; }}
    .stat-chip {{ display: flex; align-items: center; gap: 0.4rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 0.45rem 0.8rem; }}
    .stat-chip-val {{ font-size: 0.9rem; font-weight: 700; color: var(--accent); font-family: var(--mono); }}
    .stat-chip-label {{ font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }}

    /* CTA Banner */
    .cta-banner {{ margin: 2rem 0; background: linear-gradient(135deg, rgba(78,205,196,0.06) 0%, rgba(167,139,250,0.06) 100%); border: 1px solid var(--border-accent); border-radius: 16px; padding: 2rem; position: relative; overflow: hidden; }}
    .cta-banner::before {{ content: ''; position: absolute; top: -40%; right: -10%; width: 300px; height: 300px; background: radial-gradient(circle, rgba(78,205,196,0.08), transparent 70%); pointer-events: none; }}
    .cta-banner h2 {{ font-family: var(--serif); font-size: 1.6rem; font-weight: 400; margin-bottom: 0.5rem; position: relative; }}
    .cta-banner p {{ color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 1.2rem; max-width: 580px; position: relative; }}
    .cta-jump {{ display: inline-flex; align-items: center; gap: 0.5rem; background: var(--accent); color: var(--bg); font-weight: 600; font-size: 0.9rem; padding: 0.7rem 1.5rem; border-radius: 10px; text-decoration: none; transition: all 0.2s; position: relative; }}
    .cta-jump:hover {{ background: #5de0d7; transform: translateY(-1px); box-shadow: 0 4px 20px rgba(78,205,196,0.25); }}
    .cta-jump .arrow {{ transition: transform 0.2s; }}
    .cta-jump:hover .arrow {{ transform: translateX(3px); }}

    /* Section headings */
    .section-heading {{ margin: 2.5rem 0 1.2rem; display: flex; align-items: center; gap: 0.8rem; }}
    .section-heading h2 {{ font-family: var(--serif); font-size: 1.35rem; font-weight: 400; letter-spacing: -0.01em; }}
    .section-heading .line {{ flex: 1; height: 1px; background: var(--border); }}

    /* Prompt Lab */
    .prompt-lab {{ display: flex; flex-direction: column; gap: 1.2rem; }}
    .prompt-grid {{ display: flex; flex-direction: column; gap: 1rem; }}
    .prompt-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 1.4rem 1.5rem; position: relative; }}
    .prompt-card-highlight {{ border-color: var(--border-accent); }}
    .prompt-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; }}
    .prompt-label {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--accent); font-weight: 700; }}
    .prompt-hint {{ font-size: 0.84rem; color: var(--text-muted); margin-bottom: 0.7rem; line-height: 1.5; }}
    .prompt-hint strong {{ color: var(--text-secondary); }}
    .copy-btn {{ display: inline-flex; align-items: center; gap: 0.4rem; background: var(--accent); color: var(--bg); border: none; border-radius: 8px; padding: 0.5rem 1.1rem; font-size: 0.8rem; font-weight: 600; cursor: pointer; transition: all 0.2s; font-family: var(--sans); }}
    .copy-btn:hover {{ background: #5de0d7; }}
    .copy-btn.copied {{ background: var(--purple); }}
    .prompt-text {{ font-family: var(--mono); font-size: 0.82rem; line-height: 1.65; color: var(--accent); background: rgba(0,0,0,0.4); border-radius: 10px; padding: 1.2rem; border: 1px solid var(--border); white-space: pre-wrap; word-break: break-word; }}
    .prompt-code {{ font-family: var(--mono); font-size: 0.8rem; line-height: 1.65; color: var(--accent); background: rgba(0,0,0,0.4); border-radius: 10px; padding: 1.2rem; overflow-x: auto; white-space: pre; border: 1px solid var(--border); }}

    /* Parameter cards */
    .params-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 0.8rem; margin-top: 0.5rem; }}
    .param-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.1rem 1.2rem; transition: border-color 0.2s; }}
    .param-card:hover {{ border-color: var(--border-accent); }}
    .param-label {{ font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 0.25rem; }}
    .param-value {{ font-family: var(--mono); font-size: 1.15rem; font-weight: 700; color: var(--accent); margin-bottom: 0.35rem; }}
    .param-desc {{ font-size: 0.82rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 0.5rem; }}
    .param-tags {{ display: flex; flex-wrap: wrap; gap: 0.3rem; }}
    .tag {{ background: var(--accent-dim); color: var(--accent); border: 1px solid rgba(78,205,196,0.12); border-radius: 6px; padding: 0.2rem 0.55rem; font-size: 0.72rem; font-weight: 500; }}
    .tag.purple {{ background: var(--purple-dim); color: var(--purple); border-color: rgba(167,139,250,0.12); }}
    .tag.blue {{ background: rgba(96,165,250,0.1); color: var(--blue); border-color: rgba(96,165,250,0.12); }}
    .tag.neutral {{ background: rgba(255,255,255,0.04); color: var(--text-secondary); border-color: rgba(255,255,255,0.08); }}

    /* YouTube */
    .yt-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }}
    .yt-embed {{ position: relative; padding-bottom: 56.25%; height: 0; }}
    .yt-embed iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }}

    /* Audio Features */
    .features-layout {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: start; }}
    .chart-wrap {{ height: 260px; position: relative; }}
    .feature-bars {{ display: flex; flex-direction: column; gap: 0.7rem; }}
    .feature-item {{ display: grid; grid-template-columns: 120px 52px 1fr; align-items: center; gap: 0.6rem; }}
    .feature-name {{ font-size: 0.82rem; color: var(--text-muted); }}
    .feature-val {{ font-family: var(--mono); font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); text-align: right; }}
    .feature-track {{ height: 5px; background: rgba(255,255,255,0.04); border-radius: 3px; overflow: hidden; }}
    .feature-fill {{ height: 100%; border-radius: 3px; background: linear-gradient(90deg, var(--accent), var(--purple)); }}

    /* Analysis grid */
    .analysis-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }}
    .detail-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 1.3rem 1.4rem; transition: border-color 0.2s; }}
    .detail-card:hover {{ border-color: var(--border-accent); }}
    .detail-card h3 {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--purple); font-weight: 700; margin-bottom: 0.7rem; }}
    .detail-note {{ font-size: 0.84rem; color: var(--text-muted); margin-top: 0.5rem; }}
    .detail-note strong {{ color: var(--text-secondary); }}
    .mood-tags {{ display: flex; gap: 0.6rem; flex-wrap: wrap; }}
    .mood-primary {{ background: var(--purple-dim); color: var(--purple); padding: 0.35rem 0.9rem; border-radius: 8px; font-weight: 600; font-size: 0.9rem; }}
    .mood-atmo {{ background: var(--accent-dim); color: var(--accent); padding: 0.35rem 0.9rem; border-radius: 8px; font-size: 0.85rem; }}
    .prod-style {{ font-family: var(--serif); font-style: italic; color: var(--text); font-size: 1rem; margin-bottom: 0.6rem; }}
    .prod-meta {{ display: flex; gap: 1.2rem; flex-wrap: wrap; margin-top: 0.6rem; font-size: 0.82rem; color: var(--text-muted); }}
    .prod-meta strong {{ color: var(--text-secondary); }}
    .notable-text {{ font-family: var(--serif); font-size: 1.05rem; font-style: italic; line-height: 1.75; color: var(--text-secondary); }}

    /* Character grid */
    .char-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0.8rem; }}
    .char-item {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; text-align: center; }}
    .char-label {{ font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }}
    .char-value {{ font-family: var(--serif); font-size: 1.1rem; color: var(--text); margin-top: 0.25rem; }}

    /* Footer */
    footer {{ margin-top: 3rem; padding: 1.8rem 0; border-top: 1px solid var(--border); }}
    .footer-inner {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; }}
    .footer-links {{ display: flex; gap: 1.5rem; }}
    footer a {{ color: var(--text-muted); text-decoration: none; font-size: 0.82rem; transition: color 0.2s; }}
    footer a:hover {{ color: var(--accent); }}
    .footer-credit {{ font-size: 0.78rem; color: var(--text-muted); }}

    @media (max-width: 680px) {{
      h1 {{ font-size: 1.8rem; }}
      .hero-content {{ flex-direction: column; gap: 1rem; }}
      .features-layout {{ grid-template-columns: 1fr; }}
      .feature-item {{ grid-template-columns: 100px 45px 1fr; }}
      .stats-strip {{ gap: 0.4rem; }}
      .cta-banner {{ padding: 1.5rem; }}
      .cta-banner h2 {{ font-size: 1.3rem; }}
      .topnav-links {{ gap: 1rem; }}
    }}
  </style>
</head>
<body>

<!-- Nav -->
<nav class="topnav">
  <div class="container topnav-inner">
    <a href="/" class="topnav-logo">kapiko</a>
    <ul class="topnav-links">
      {nav_genre_link}
      <li><a href="/data/">Data</a></li>
      <li><a href="/api/openapi.json">API</a></li>
    </ul>
  </div>
</nav>

<!-- Hero -->
<header class="hero">
  <div class="container">
    <div class="breadcrumb">
      <a href="/" style="font-family:'Pacifico',cursive">kapiko</a> <span class="sep">›</span>
      <a href="/genres/{esc(genre)}/">{esc(gdisp)}</a> <span class="sep">›</span>
      <span>Song Analysis</span>
    </div>
    <div class="hero-content">
      <div class="hero-text">
        <h1>{esc(name)}</h1>
        <div class="artist-name">{esc(artist)}</div>
        {"<div class=\"album-name\">" + esc(album) + "</div>" if album else ""}
        <div class="listen-links">
          <a href="{esc(spotify_url)}" target="_blank" rel="noopener" title="Listen on Spotify">
            <svg viewBox="0 0 24 24"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>
          </a>
          <a href="{esc(youtube_url)}" target="_blank" rel="noopener" title="Watch on YouTube">
            <svg viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
          </a>
        </div>
        <div class="stats-strip">
          <div class="stat-chip"><span class="stat-chip-val">{tempo:.0f}</span><span class="stat-chip-label">BPM</span></div>
          <div class="stat-chip"><span class="stat-chip-val">{esc(key_short)}</span><span class="stat-chip-label">Key</span></div>
          <div class="stat-chip"><span class="stat-chip-val">{e*100:.1f}%</span><span class="stat-chip-label">Energy</span></div>
          <div class="stat-chip"><span class="stat-chip-val">{dur_str}</span><span class="stat-chip-label">Duration</span></div>
          <div class="stat-chip"><span class="stat-chip-val">{pop}</span><span class="stat-chip-label">Popularity</span></div>
        </div>
      </div>
      <div class="album-art">
        {album_art_html}
      </div>
    </div>
  </div>
</header>

<div class="container">

  <!-- CTA Banner -->
  <div class="cta-banner">
    <h2>Recreate this track with AI</h2>
    <p>Copy data-driven prompts for Suno, Udio, MiniMax Music, and more — tuned to match the exact BPM, key, mood, and production style.</p>
    <a href="#prompt-lab" class="cta-jump">Get the prompts <span class="arrow">→</span></a>
  </div>

  <!-- Prompt Lab -->
  <div class="section-heading" id="prompt-lab">
    <h2>Prompts to recreate &ldquo;{esc(name)}&rdquo; by {esc(pa)}</h2>
    <div class="line"></div>
  </div>
  <div class="prompt-lab">
    <div class="prompt-grid">

    <!-- General prompt -->
    <div class="prompt-card prompt-card-highlight">
      <div class="prompt-header">
        <span class="prompt-label">General — Ready-to-use prompt</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptGeneral">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          Copy Prompt
        </button>
      </div>
      <div class="prompt-hint">Paste into <strong>Suno</strong>, <strong>Udio</strong>, <strong>MiniMax Music</strong>, <strong>ElevenLabs</strong>, <strong>Mureka</strong>, <strong>Beatoven.ai</strong>, <strong>Stable Audio</strong>, <strong>AIVA</strong>, <strong>Soundraw</strong>, or any AI music generator.</div>
      <div class="prompt-text" id="promptGeneral">{esc(gen_prompt)}</div>
    </div>

    <!-- Suno prompt -->
    <div class="prompt-card prompt-card-highlight">
      <div class="prompt-header">
        <span class="prompt-label">Suno — Style tags</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptSuno">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          Copy Tags
        </button>
      </div>
      <div class="prompt-hint">Paste into the <strong>Style of Music</strong> field in Suno. Set BPM to <strong>{tempo:.0f}</strong>.</div>
      <div class="prompt-text" id="promptSuno">{esc(suno_prompt)}</div>
    </div>

    <!-- Udio prompt -->
    <div class="prompt-card prompt-card-highlight">
      <div class="prompt-header">
        <span class="prompt-label">Udio — Prompt</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptUdio">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          Copy Prompt
        </button>
      </div>
      <div class="prompt-hint">Paste as the main prompt. Use <strong>manual mode</strong> to set BPM ({tempo:.0f}) and key ({esc(key_mode)}).</div>
      <div class="prompt-text" id="promptUdio">{esc(udio_prompt)}</div>
    </div>

    <!-- Agent JSON -->
    <div class="prompt-card prompt-card-highlight">
      <div class="prompt-header">
        <span class="prompt-label">Agent JSON — Structured data</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptAgent">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          Copy JSON
        </button>
      </div>
      <div class="prompt-hint">Machine-readable format for AI agents, APIs, and programmatic music generation.</div>
      <pre class="prompt-code" id="promptAgent">{esc(agent_json)}</pre>
    </div>

    </div><!-- /prompt-grid -->

    <!-- Parameter breakdown -->
    <div class="params-grid">
      <div class="param-card">
        <div class="param-label">Tempo</div>
        <div class="param-value">{tempo:.0f} BPM</div>
        <div class="param-desc">{"Slow" if tempo < 80 else "Mid-tempo" if tempo < 120 else "Upbeat" if tempo < 150 else "Fast"} pace. Natural rhythm for the genre.</div>
        <div class="param-tags">{energy_tag_chips}</div>
      </div>
      <div class="param-card">
        <div class="param-label">Energy</div>
        <div class="param-value">{e*100:.1f}%</div>
        <div class="param-desc">{infer_energy_label(e).capitalize()} energy level. Sets the dynamic intensity.</div>
        <div class="param-tags">{energy_tag_chips}</div>
      </div>
      <div class="param-card">
        <div class="param-label">Mood</div>
        <div class="param-value">{v*100:.1f}% Valence</div>
        <div class="param-desc">{mood.capitalize()} mood with {atmosphere} atmosphere.</div>
        <div class="param-tags">{mood_tag_chips}</div>
      </div>
      <div class="param-card">
        <div class="param-label">Instrumentation</div>
        <div class="param-value">{len(instruments_list)} Instruments</div>
        <div class="param-desc">Primary: {esc(instruments_list[0])}. Full arrangement with {esc(instruments_str)}.</div>
        <div class="param-tags">{inst_chips}</div>
      </div>
      <div class="param-card">
        <div class="param-label">Key &amp; Tonality</div>
        <div class="param-value">{esc(key_mode)}</div>
        <div class="param-desc">{mode} key. Harmonic foundation with {harmony.lower()}.</div>
        <div class="param-tags">{key_tags}</div>
      </div>
      <div class="param-card">
        <div class="param-label">Production</div>
        <div class="param-value">{esc(production_style)}</div>
        <div class="param-desc">{esc(production_effects[0].capitalize())}. {texture.capitalize()} texture, {dynamics} dynamics.</div>
        <div class="param-tags">{effect_chips}<span class="tag">{esc(texture)}</span><span class="tag">{esc(stereo)}-stereo</span></div>
      </div>
    </div>
  </div>
{yt_section}

  <!-- Audio Features -->
  <div class="section-heading">
    <h2>Audio Features</h2>
    <div class="line"></div>
  </div>
  <div class="detail-card" style="padding:1.5rem">
    <div class="features-layout">
      <div class="chart-wrap">
        <canvas id="radarChart"></canvas>
      </div>
      <div class="feature-bars">
        <div class="feature-item"><div class="feature-name">Energy</div><div class="feature-val">{e*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{e*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-name">Danceability</div><div class="feature-val">{d*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{d*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-name">Valence</div><div class="feature-val">{v*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(v*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-name">Acousticness</div><div class="feature-val">{a*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{a*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-name">Instrumentalness</div><div class="feature-val">{ins*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(ins*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-name">Speechiness</div><div class="feature-val">{sp*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(sp*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-name">Liveness</div><div class="feature-val">{liv*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(liv*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-name">Loudness</div><div class="feature-val">{loud:.1f} dB</div><div class="feature-track"><div class="feature-fill" style="width:{loud_pct(loud):.0f}%"></div></div></div>
      </div>
    </div>
  </div>

  <!-- AI Audio Analysis -->
  <div class="section-heading">
    <h2>AI Audio Analysis</h2>
    <div class="line"></div>
  </div>
  <div class="analysis-grid">
    <div class="detail-card">
      <h3>Instrumentation</h3>
      <div class="param-tags">{inst_chips}</div>
      <div class="detail-note">Primary: <strong>{esc(instruments_list[0])}</strong></div>
    </div>
    <div class="detail-card">
      <h3>Mood &amp; Atmosphere</h3>
      <div class="mood-tags">
        <span class="mood-primary">{esc(mood)}</span>
        <span class="mood-atmo">{esc(atmosphere)}</span>
      </div>
    </div>
    <div class="detail-card">
      <h3>Production &amp; Sound Design</h3>
      <p class="prod-style">{esc(production_style)}</p>
      <div class="param-tags">{effect_chips}</div>
      <div class="prod-meta">
        <span>Texture: <strong>{esc(texture)}</strong></span>
        <span>Dynamics: <strong>{esc(dynamics)}</strong></span>
        <span>Stereo: <strong>{esc(stereo)}</strong></span>
      </div>
    </div>
    <div class="detail-card">
      <h3>Genre Tags</h3>
      <div class="param-tags">{genre_tag_chips}</div>
    </div>
    <div class="detail-card">
      <h3>Similar Artists</h3>
      <div class="param-tags">{similar_chips}</div>
    </div>
    <div class="detail-card">
      <h3>What Makes This Track Unique</h3>
      <p class="notable-text">{esc(notable)}</p>
    </div>
  </div>

  <!-- Musical Character -->
  <div class="section-heading">
    <h2>Musical Character</h2>
    <div class="line"></div>
  </div>
  <div class="char-grid">
    <div class="char-item"><div class="char-label">Vocals</div><div class="char-value">{esc(vocals)}</div></div>
    <div class="char-item"><div class="char-label">Harmony</div><div class="char-value">{esc(harmony)}</div></div>
    <div class="char-item"><div class="char-label">Rhythm</div><div class="char-value">{esc(rhythm)}</div></div>
    <div class="char-item"><div class="char-label">Estimated Key</div><div class="char-value">{esc(key_mode)}</div></div>
  </div>
</div>

<!-- Footer -->
<footer>
  <div class="container footer-inner">
    <div class="footer-links">
      <a href="/genres/{esc(genre)}/">← {esc(gdisp)} Genre</a>
      <a href="/" style="font-family:'Pacifico',cursive">kapiko.ai</a>
      <a href="/api/openapi.json">API</a>
    </div>
    <div class="footer-credit">Data from Spotify audio features + Gemini AI audio analysis.</div>
  </div>
</footer>

<script>
const ctx = document.getElementById('radarChart');
if (ctx) {{
  new Chart(ctx, {{
    type: 'radar',
    data: {{
      labels: ['Energy','Danceability','Valence','Acousticness','Instrumentalness','Speechiness'],
      datasets: [{{
        data: [{e},{d},{v},{a},{ins},{sp}],
        backgroundColor: 'rgba(78,205,196,0.12)',
        borderColor: '#4ecdc4',
        borderWidth: 2,
        pointBackgroundColor: '#4ecdc4',
        pointRadius: 3,
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        r: {{
          beginAtZero: true,
          max: 1,
          ticks: {{ display: false }},
          grid: {{ color: 'rgba(255,255,255,0.05)' }},
          pointLabels: {{ color: '#6b7099', font: {{ family: "'DM Sans'", size: 11 }} }},
          angleLines: {{ color: 'rgba(255,255,255,0.05)' }},
        }}
      }}
    }}
  }});
}}
function copyPrompt(btn) {{
  const id = btn.getAttribute('data-target');
  const el = document.getElementById(id);
  const text = el.textContent || el.innerText;
  navigator.clipboard.writeText(text.trim()).then(() => {{
    const orig = btn.innerHTML;
    btn.classList.add('copied');
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Copied!';
    setTimeout(() => {{ btn.innerHTML = orig; btn.classList.remove('copied'); }}, 2000);
  }});
}}
</script>
</body>
</html>'''


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 999999
    
    all_genres_data = {}
    for g in GENRES:
        apath = SITE / 'genres' / g / 'analysis.json'
        if apath.exists():
            try:
                data = json.load(open(apath))
                all_genres_data[g] = data
            except:
                continue
    
    all_songs = {}
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
