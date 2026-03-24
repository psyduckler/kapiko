#!/usr/bin/env python3
"""
Phase 2: Apply content + UX improvements to all 118 kapiko genre pages.

Changes:
1. Genre Profile Prose section (data-driven, ~300-400 words)
2. Key Finding callout boxes per section
3. Visible FAQ accordion section
4. Section reorder: Prompt Lab before Audio DNA
5. Download Data button in hero
6. Update ToC with new sections
7. Genre Comparison mini-section
"""

import os
import re
import json
import glob
from pathlib import Path

SITE_DIR = Path("/Users/psy/kapiko-site/site/genres")

# ── Related genres mapping (from apply_seo_fixes.py) ─────────────────────────
RELATED_MAP = {
    "acoustic": ["folk", "indie", "singer-songwriter", "country", "alternative"],
    "afrobeat": ["afro-soul", "highlife", "funk", "world-music", "latin"],
    "alt-rock": ["alternative", "indie", "grunge", "rock", "punk-rock"],
    "alternative": ["alt-rock", "indie", "rock", "grunge", "post-rock"],
    "ambient": ["neo-classical", "new-age", "chill", "electronic", "sleep"],
    "anime": ["j-pop", "j-rock", "video-game-music", "classical", "electronic"],
    "black-metal": ["death-metal", "heavy-metal", "doom-metal", "thrash-metal", "metal"],
    "bluegrass": ["country", "folk", "acoustic", "americana", "roots"],
    "blues": ["jazz", "soul", "r-n-b", "rock", "country"],
    "brazil": ["bossa-nova", "samba", "latin", "afrobeat", "world-music"],
    "breakbeat": ["drum-and-bass", "electronic", "techno", "house", "edm"],
    "british": ["alternative", "indie", "rock", "pop", "art-rock"],
    "cantopop": ["j-pop", "k-pop", "mandopop", "pop", "anime"],
    "chicago-house": ["house", "deep-house", "techno", "electronic", "club"],
    "children": ["pop", "folk", "acoustic", "classical", "comedy"],
    "chill": ["ambient", "lo-fi", "sleep", "focus", "acoustic"],
    "classical": ["neo-classical", "ambient", "opera", "piano", "cinematic"],
    "club": ["house", "techno", "edm", "electronic", "dance"],
    "comedy": ["pop", "folk", "indie", "acoustic", "children"],
    "country": ["folk", "bluegrass", "americana", "acoustic", "pop"],
    "dance": ["edm", "house", "pop", "electronic", "club"],
    "death-metal": ["black-metal", "heavy-metal", "thrash-metal", "metal", "doom-metal"],
    "deep-house": ["house", "chicago-house", "techno", "electronic", "club"],
    "disco": ["funk", "r-n-b", "soul", "dance", "pop"],
    "doom-metal": ["black-metal", "death-metal", "heavy-metal", "metal", "sludge"],
    "drum-and-bass": ["breakbeat", "electronic", "techno", "jungle", "edm"],
    "dubstep": ["edm", "electronic", "drum-and-bass", "trap", "bass"],
    "edm": ["electronic", "house", "techno", "dance", "trance"],
    "electro": ["electronic", "synth-pop", "electro-house", "techno", "dance"],
    "electronic": ["edm", "ambient", "techno", "house", "synth-pop"],
    "emo": ["punk-rock", "pop-punk", "alternative", "indie", "rock"],
    "folk": ["acoustic", "country", "singer-songwriter", "bluegrass", "americana"],
    "funk": ["r-n-b", "soul", "disco", "hip-hop", "jazz"],
    "garage-rock": ["punk-rock", "rock", "alternative", "indie", "blues"],
    "gospel": ["soul", "r-n-b", "blues", "christian", "pop"],
    "grunge": ["alt-rock", "alternative", "rock", "indie", "punk-rock"],
    "hard-rock": ["heavy-metal", "rock", "alt-rock", "metal", "punk-rock"],
    "heavy-metal": ["hard-rock", "metal", "death-metal", "black-metal", "thrash-metal"],
    "hip-hop": ["r-n-b", "trap", "rap", "soul", "electronic"],
    "house": ["deep-house", "chicago-house", "techno", "edm", "electronic"],
    "indie": ["alternative", "folk", "indie-pop", "rock", "acoustic"],
    "indie-pop": ["indie", "pop", "alternative", "synth-pop", "dream-pop"],
    "industrial": ["metal", "electronic", "noise", "techno", "ebm"],
    "j-pop": ["k-pop", "anime", "cantopop", "pop", "j-rock"],
    "j-rock": ["j-pop", "anime", "alt-rock", "rock", "visual-kei"],
    "jazz": ["blues", "soul", "bossa-nova", "r-n-b", "brazil"],
    "jazz-piano": ["jazz", "classical", "blues", "neo-classical", "piano"],
    "k-pop": ["j-pop", "pop", "cantopop", "dance", "electronic"],
    "latin": ["reggaeton", "salsa", "brazil", "afrobeat", "pop"],
    "lo-fi": ["chill", "ambient", "hip-hop", "sleep", "focus"],
    "metal": ["heavy-metal", "hard-rock", "black-metal", "death-metal", "thrash-metal"],
    "neo-classical": ["classical", "ambient", "piano", "cinematic", "jazz-piano"],
    "new-age": ["ambient", "neo-classical", "chill", "sleep", "focus"],
    "opera": ["classical", "musical-theatre", "neo-classical", "piano", "jazz"],
    "piano": ["classical", "jazz-piano", "neo-classical", "ambient", "acoustic"],
    "pop": ["indie-pop", "synth-pop", "dance", "r-n-b", "electronic"],
    "post-rock": ["alternative", "ambient", "shoegaze", "indie", "progressive-rock"],
    "progressive-rock": ["post-rock", "art-rock", "rock", "metal", "alternative"],
    "psychedelic": ["progressive-rock", "art-rock", "shoegaze", "alternative", "rock"],
    "punk-rock": ["alt-rock", "emo", "pop-punk", "hardcore", "garage-rock"],
    "r-n-b": ["soul", "hip-hop", "funk", "pop", "gospel"],
    "reggae": ["dancehall", "reggaeton", "latin", "ska", "dub"],
    "reggaeton": ["latin", "reggae", "hip-hop", "dance", "trap"],
    "rock": ["alt-rock", "alternative", "hard-rock", "indie", "classic-rock"],
    "salsa": ["latin", "brazil", "cumbia", "afrobeat", "world-music"],
    "shoegaze": ["dream-pop", "alternative", "indie", "psychedelic", "post-rock"],
    "singer-songwriter": ["folk", "acoustic", "indie", "country", "alternative"],
    "ska": ["reggae", "punk-rock", "rocksteady", "dance", "pop"],
    "sleep": ["ambient", "chill", "new-age", "lo-fi", "neo-classical"],
    "soul": ["r-n-b", "funk", "gospel", "blues", "jazz"],
    "synth-pop": ["electronic", "pop", "new-wave", "indie-pop", "electro"],
    "techno": ["house", "electronic", "edm", "drum-and-bass", "techno"],
    "thrash-metal": ["heavy-metal", "metal", "death-metal", "hard-rock", "black-metal"],
    "trance": ["edm", "electronic", "house", "techno", "dance"],
    "trap": ["hip-hop", "r-n-b", "edm", "electronic", "rap"],
    "world-music": ["afrobeat", "latin", "brazil", "folk", "reggae"],
}


def load_analysis(slug: str) -> dict:
    """Load analysis.json for a given slug. Returns empty dict if not found."""
    path = SITE_DIR / slug / "analysis.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def get_bpm_stdev(bpm_data: dict) -> float:
    """Get BPM stdev from either stdev key or q1/q3."""
    if 'stdev' in bpm_data:
        return float(bpm_data['stdev'])
    # Estimate from q1/q3 (IQR ≈ 1.35σ)
    if 'q1' in bpm_data and 'q3' in bpm_data:
        return round((bpm_data['q3'] - bpm_data['q1']) / 1.35, 1)
    return 0.0


def get_bpm_range(bpm_data: dict) -> tuple:
    """Get BPM low/high (25th–75th pct)."""
    if 'q1' in bpm_data and 'q3' in bpm_data:
        return round(bpm_data['q1'], 1), round(bpm_data['q3'], 1)
    if 'raw' in bpm_data:
        raw = sorted(bpm_data['raw'])
        n = len(raw)
        return round(raw[n//4], 1), round(raw[3*n//4], 1)
    median = bpm_data.get('median', 120)
    stdev = get_bpm_stdev(bpm_data)
    return round(max(0, median - stdev), 1), round(median + stdev, 1)


def get_duration_min(data: dict) -> float:
    """Get duration in minutes. Returns 0 if not available."""
    dur = data.get('duration', {})
    if not dur:
        return 0.0
    # New format: median in ms
    if 'median' in dur and dur['median'] > 1000:
        return round(dur['median'] / 60000, 1)
    # Old format: median_min in minutes
    if 'median_min' in dur:
        return round(dur['median_min'], 1)
    # q3/q1 format
    if 'median' in dur:
        val = dur['median']
        if val < 20:  # minutes
            return round(val, 1)
        return round(val / 60000, 1)
    return 0.0


def extract_stats(data: dict) -> dict:
    """Extract all stats for a genre page."""
    stats = {}

    # BPM
    bpm = data.get('bpm', {})
    stats['bpm_median'] = round(bpm.get('median', 120), 1)
    stats['bpm_stdev'] = get_bpm_stdev(bpm)
    stats['bpm_low'], stats['bpm_high'] = get_bpm_range(bpm)

    # Key
    key_dist = data.get('key_distribution', {})
    if key_dist:
        top_key = max(key_dist, key=key_dist.get)
        stats['top_key'] = top_key
        stats['top_key_count'] = key_dist[top_key]
    else:
        stats['top_key'] = 'C'
        stats['top_key_count'] = 0

    # Mode
    mode_dist = data.get('mode_distribution', {})
    major_count = mode_dist.get('Major', 0)
    minor_count = mode_dist.get('Minor', 0)
    total = major_count + minor_count if (major_count + minor_count) > 0 else 100
    stats['major_pct'] = round(100 * major_count / total)
    stats['minor_pct'] = round(100 * minor_count / total)
    stats['dominant_mode'] = 'major' if major_count >= minor_count else 'minor'
    stats['dominant_pct'] = max(stats['major_pct'], stats['minor_pct'])

    # Audio features (all 0-1 scale)
    for feat in ['energy', 'valence', 'acousticness', 'instrumentalness', 'danceability', 'speechiness']:
        d = data.get(feat, {})
        val = d.get('median', d.get('mean', 0.5))
        stats[feat] = round(val * 100, 1)

    # Loudness
    loud = data.get('loudness', {})
    stats['loudness'] = round(loud.get('median', loud.get('mean', -8.0)), 1)

    # Top artists
    artists = data.get('top_artists', [])[:5]
    stats['artists'] = artists

    # Duration
    stats['duration_min'] = get_duration_min(data)

    # Tracks (sorted by popularity)
    tracks = data.get('tracks', [])
    if tracks:
        sorted_tracks = sorted(tracks, key=lambda t: -t.get('popularity', 0))
        top_track = sorted_tracks[0]
        stats['top_track_name'] = top_track.get('name', '')
        stats['top_track_artist'] = top_track.get('artists', '')
        stats['top_track_pop'] = top_track.get('popularity', 0)
    else:
        stats['top_track_name'] = ''
        stats['top_track_artist'] = ''
        stats['top_track_pop'] = 0

    # Key distribution for comparison
    stats['key_dist'] = key_dist

    return stats


def generate_genre_profile(genre_name: str, stats: dict) -> tuple:
    """Generate 4 paragraphs of natural prose from stats."""
    energy = stats['energy']
    valence = stats['valence']
    acoustic = stats['acousticness']
    instrumental = stats['instrumentalness']
    dance = stats['danceability']
    speech = stats['speechiness']
    loudness = stats['loudness']
    bpm_median = stats['bpm_median']
    bpm_stdev = stats['bpm_stdev']
    top_key = stats['top_key']
    top_key_count = stats['top_key_count']
    dominant_mode = stats['dominant_mode']
    dominant_pct = stats['dominant_pct']
    artists = stats['artists']
    duration_min = stats['duration_min']

    gn = genre_name
    gl = genre_name.lower()

    # Energy descriptor
    if energy < 20:
        energy_desc = "exceptionally low energy, creating a hushed, almost meditative atmosphere"
    elif energy < 35:
        energy_desc = "low energy levels that favor restraint and subtlety over intensity"
    elif energy < 50:
        energy_desc = "moderate energy, balancing movement with space"
    elif energy < 70:
        energy_desc = "solid energy that keeps listeners engaged without overwhelming"
    else:
        energy_desc = "high energy that drives the music forward with force and momentum"

    # Valence descriptor
    if valence < 20:
        valence_desc = "deeply melancholic and emotionally heavy"
    elif valence < 35:
        valence_desc = "leaning toward introspection and wistfulness"
    elif valence < 50:
        valence_desc = "emotionally balanced, neither overtly happy nor sad"
    elif valence < 65:
        valence_desc = "generally upbeat and positive in tone"
    else:
        valence_desc = "bright, happy, and emotionally uplifting"

    # BPM descriptor
    if bpm_median < 80:
        bpm_desc = "slow, deliberate tempo"
    elif bpm_median < 110:
        bpm_desc = "relaxed, mid-tempo pace"
    elif bpm_median < 130:
        bpm_desc = "moderate tempo that sits comfortably in walking-pace territory"
    elif bpm_median < 150:
        bpm_desc = "uptempo drive"
    else:
        bpm_desc = "fast, high-energy tempo"

    # Acousticness descriptor
    if acoustic > 70:
        acoustic_desc = f"heavily acoustic character ({acoustic}% median acousticness), favoring organic instruments and natural textures"
    elif acoustic > 40:
        acoustic_desc = f"a blend of acoustic and electronic elements ({acoustic}% acousticness)"
    else:
        acoustic_desc = f"predominantly electronic production ({acoustic}% acousticness), built on synthesized sounds and digital textures"

    # Danceability descriptor
    if dance < 40:
        dance_desc = "suggesting minimal rhythmic drive"
    elif dance < 60:
        dance_desc = "providing enough groove to move to"
    else:
        dance_desc = "making it highly danceable"

    # Speechiness descriptor
    if speech < 5:
        speech_desc = "virtually absent"
    elif speech < 15:
        speech_desc = "minimal"
    else:
        speech_desc = "notable"

    p1 = (f"{gn} music is characterized by {energy_desc}, with a median energy of {energy}%. "
          f"The genre carries {acoustic_desc}. Instrumentalness sits at {instrumental}%, "
          f"while danceability registers at {dance}% — {dance_desc}. The emotional tone is "
          f"{valence_desc}, with valence at {valence}%. Speechiness is {speech_desc} at {speech}%.")

    # Tonal character
    if dominant_mode == 'major' and dominant_pct > 60:
        tonal_char = "creating an overall sense of brightness and openness"
    elif dominant_mode == 'minor' and dominant_pct > 60:
        tonal_char = "lending a darker, more complex tonal character"
    else:
        tonal_char = "showing a fairly even split between light and dark tonalities"

    stdev_str = f"±{round(bpm_stdev, 1)}" if bpm_stdev > 0 else ""
    bpm_suffix = f" ({stdev_str})" if stdev_str else ""

    p2 = (f"The typical {gl} track moves at a {bpm_desc} of {bpm_median} BPM{bpm_suffix}. "
          f"Tonally, {top_key} is the most common key"
          + (f" ({top_key_count} of 100 tracks)" if top_key_count else "") +
          f", and {dominant_pct}% of tracks are in a {dominant_mode} key — {tonal_char}.")

    # Artists paragraph
    artist_names = [a['name'] for a in artists]
    if len(artist_names) >= 3:
        p3_artists = ', '.join(artist_names[:3])
        p3_extra = f" alongside {', '.join(artist_names[3:])}" if len(artist_names) > 3 else ""
    elif len(artist_names) > 0:
        p3_artists = ', '.join(artist_names)
        p3_extra = ""
    else:
        p3_artists = "various artists"
        p3_extra = ""

    if duration_min > 0:
        dur_str = f"The typical track runs about {duration_min} minutes, "
        if duration_min < 4.0:
            dur_str += "optimized for streaming attention spans."
        elif duration_min > 5.5:
            dur_str += "giving enough room for ideas to develop fully."
        else:
            dur_str += "hitting a sweet spot for both streaming and deeper listening."
    else:
        dur_str = ""

    p3 = f"The genre's sonic identity is shaped by artists like {p3_artists}{p3_extra}. {dur_str}".strip()

    # Production/loudness
    if loudness < -15:
        loud_desc = "extremely quiet and dynamic, with lots of headroom"
    elif loudness < -10:
        loud_desc = "relatively quiet compared to mainstream genres, preserving dynamic range"
    elif loudness < -7:
        loud_desc = "moderately loud, balancing dynamics with presence"
    elif loudness < -5:
        loud_desc = "loud and compressed, optimized for impact over nuance"
    else:
        loud_desc = "heavily compressed and maximally loud, typical of genres competing for streaming attention"

    p4 = (f"Production-wise, {gl} sits at a median loudness of {loudness} dB — {loud_desc}. "
          f"Whether you're producing in the genre or analyzing it for AI music generation, "
          f"these numbers provide a precise target for capturing the authentic {gl} sound.")

    return p1, p2, p3, p4


def build_genre_profile_html(genre_name: str, stats: dict) -> str:
    """Build the Genre Profile section HTML."""
    p1, p2, p3, p4 = generate_genre_profile(genre_name, stats)
    return (
        '\n  <div class="section-label" id="genre-profile"><h2>Genre Profile</h2></div>\n'
        '  <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:28px 32px;margin-bottom:32px;max-width:800px">\n'
        f'    <p style="font-size:15px;color:#dde1f0;line-height:1.8;margin-bottom:16px">{p1}</p>\n'
        f'    <p style="font-size:15px;color:#dde1f0;line-height:1.8;margin-bottom:16px">{p2}</p>\n'
        f'    <p style="font-size:15px;color:#dde1f0;line-height:1.8;margin-bottom:16px">{p3}</p>\n'
        f'    <p style="font-size:15px;color:#dde1f0;line-height:1.8">{p4}</p>\n'
        '  </div>\n'
    )


def build_callout(text: str) -> str:
    """Build a key finding callout box."""
    return (
        '  <div style="background:rgba(78,205,196,0.06);border-left:3px solid #4ecdc4;border-radius:0 10px 10px 0;padding:14px 20px;margin-bottom:20px;max-width:800px">\n'
        f'    <p style="font-size:14px;color:#dde1f0;line-height:1.6;margin:0"><strong style="color:#4ecdc4">Key finding:</strong> {text}</p>\n'
        '  </div>\n'
    )


def build_faq_html(genre_name: str, stats: dict) -> str:
    """Build the visible FAQ accordion section."""
    gn = genre_name
    gl = genre_name.lower()
    bpm_median = stats['bpm_median']
    bpm_stdev = stats['bpm_stdev']
    bpm_low = stats['bpm_low']
    bpm_high = stats['bpm_high']
    top_key = stats['top_key']
    major_pct = stats['major_pct']
    minor_pct = stats['minor_pct']
    energy = stats['energy']
    valence = stats['valence']
    acoustic = stats['acousticness']
    instrumental = stats['instrumentalness']
    dominant_mode = stats['dominant_mode']

    # Valence description
    if valence < 20:
        valence_adj = "deeply melancholic and emotionally heavy"
        key_mood = "reinforces this introspective, somber quality" if major_pct < 50 else "provides occasional moments of brightness amid the heaviness"
    elif valence < 35:
        valence_adj = "more introspective and wistful than happy"
        key_mood = "adds weight to the emotional tone" if major_pct < 50 else "keeps the sound from feeling too dark"
    elif valence < 50:
        valence_adj = "emotionally balanced, sitting between sad and happy"
        key_mood = "tilts the overall feel toward the darker side" if major_pct < 50 else "provides a sense of balance and emotional complexity"
    elif valence < 65:
        valence_adj = "generally positive and upbeat in tone"
        key_mood = "reinforces the upbeat character" if major_pct > 50 else "adds unexpected emotional depth"
    else:
        valence_adj = "bright, uplifting, and emotionally positive"
        key_mood = "strongly reinforces that happy, energetic character" if major_pct > 60 else "gives it a surprisingly complex emotional palette"

    # Instruments description
    if acoustic > 70 and instrumental > 50:
        instruments_desc = f"acoustic instruments like piano, guitar, strings, and woodwinds — with minimal vocals and electronic elements"
        leans_desc = f"leans strongly toward organic, acoustic production with high instrumentalness ({instrumental}%), making it almost entirely instrument-driven"
    elif acoustic > 70:
        instruments_desc = f"organic acoustic instruments alongside vocals, with very little electronic processing"
        leans_desc = f"leans toward acoustic and organic textures ({acoustic}% acousticness), blending natural instruments with vocal performances"
    elif acoustic > 40:
        instruments_desc = f"a mix of acoustic and electronic elements — live instruments blended with digital production"
        leans_desc = f"sits in a hybrid space ({acoustic}% acousticness, {instrumental}% instrumentalness), combining organic and electronic sounds"
    elif instrumental > 60:
        instruments_desc = f"synthesizers, drum machines, and digital sound design — predominantly instrumental with few or no vocals"
        leans_desc = f"leans heavily electronic ({acoustic}% acousticness) with a focus on instrumental textures ({instrumental}% instrumentalness)"
    else:
        instruments_desc = f"electronic production with synthesizers, programmed beats, and digital effects alongside vocal performances"
        leans_desc = f"is primarily electronic ({acoustic}% acousticness) with a strong vocal or lyrical focus ({instrumental}% instrumentalness)"

    stdev_str = f" with a standard deviation of {bpm_stdev}" if bpm_stdev > 0 else ""

    html = (
        '\n  <div class="section-label" id="faq"><h2>Frequently Asked Questions</h2></div>\n'
        '  <div style="display:flex;flex-direction:column;gap:12px;margin-bottom:32px;max-width:800px">\n'
        # Q1: BPM
        '    <details style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:0;overflow:hidden">\n'
        f'      <summary style="padding:16px 20px;font-size:15px;font-weight:600;color:#dde1f0;cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between">What BPM is {gn} music?<span style="color:#4ecdc4;font-size:18px;transition:transform 0.2s">+</span></summary>\n'
        f'      <div style="padding:0 20px 16px;font-size:14px;color:#6b7099;line-height:1.7">Based on analysis of the top 100 {gl} tracks on Spotify, the median BPM is {bpm_median}{stdev_str}. The typical range falls between {bpm_low} and {bpm_high} BPM.</div>\n'
        '    </details>\n'
        # Q2: Key
        '    <details style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:0;overflow:hidden">\n'
        f'      <summary style="padding:16px 20px;font-size:15px;font-weight:600;color:#dde1f0;cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between">What key is {gn} music usually in?<span style="color:#4ecdc4;font-size:18px;transition:transform 0.2s">+</span></summary>\n'
        f'      <div style="padding:0 20px 16px;font-size:14px;color:#6b7099;line-height:1.7">The most common key in {gl} music is {top_key}, and {major_pct}% of tracks are in a major key.</div>\n'
        '    </details>\n'
        # Q3: AI
        '    <details style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:0;overflow:hidden">\n'
        f'      <summary style="padding:16px 20px;font-size:15px;font-weight:600;color:#dde1f0;cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between">How do I make {gn} music with AI?<span style="color:#4ecdc4;font-size:18px;transition:transform 0.2s">+</span></summary>\n'
        f'      <div style="padding:0 20px 16px;font-size:14px;color:#6b7099;line-height:1.7">Use AI music generators like Suno or Udio with genre-specific prompts. Key parameters for {gl}: BPM around {bpm_median}, energy level around {energy}%, and valence around {valence}%. Visit the <a href="#prompt-lab" style="color:#4ecdc4;text-decoration:none">Prompt Lab section</a> on this page for a ready-to-copy prompt template.</div>\n'
        '    </details>\n'
        # Q4: Instruments
        '    <details style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:0;overflow:hidden">\n'
        f'      <summary style="padding:16px 20px;font-size:15px;font-weight:600;color:#dde1f0;cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between">What instruments are used in {gn} music?<span style="color:#4ecdc4;font-size:18px;transition:transform 0.2s">+</span></summary>\n'
        f'      <div style="padding:0 20px 16px;font-size:14px;color:#6b7099;line-height:1.7">{gn} music typically features {instruments_desc}. With an acousticness of {acoustic}% and instrumentalness of {instrumental}%, the genre {leans_desc}.</div>\n'
        '    </details>\n'
        # Q5: Happy or sad
        '    <details style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:0;overflow:hidden">\n'
        f'      <summary style="padding:16px 20px;font-size:15px;font-weight:600;color:#dde1f0;cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between">Is {gn} music happy or sad?<span style="color:#4ecdc4;font-size:18px;transition:transform 0.2s">+</span></summary>\n'
        f'      <div style="padding:0 20px 16px;font-size:14px;color:#6b7099;line-height:1.7">With a median valence of {valence}%, {gl} music is {valence_adj}. {major_pct}% of tracks use major keys, which {key_mood}.</div>\n'
        '    </details>\n'
        '  </div>\n'
    )
    return html


def build_compare_html(slug: str, genre_name: str, stats: dict) -> str:
    """Build the Genre Comparison mini-section."""
    related_slugs = RELATED_MAP.get(slug, [])[:3]
    cards = []

    for rel_slug in related_slugs:
        rel_data = load_analysis(rel_slug)
        if not rel_data:
            continue
        rel_stats = extract_stats(rel_data)
        rel_name = rel_slug.replace('-', ' ').title()
        rel_name = rel_name.replace('R N B', 'R&B').replace('J Pop', 'J-Pop').replace('K Pop', 'K-Pop').replace('Edm', 'EDM')

        # Build comparison sentence
        energy_diff = round(stats['energy'] - rel_stats['energy'], 1)
        valence_diff = round(stats['valence'] - rel_stats['valence'], 1)
        bpm_diff = round(stats['bpm_median'] - rel_stats['bpm_median'], 1)

        parts = []
        if abs(energy_diff) >= 5:
            direction = "more energetic" if energy_diff > 0 else "more subdued"
            parts.append(f"{direction} ({abs(energy_diff)}% energy difference)")
        if abs(valence_diff) >= 5:
            direction = "happier" if valence_diff > 0 else "darker"
            parts.append(f"{direction} in mood ({abs(valence_diff)}% valence gap)")
        if abs(bpm_diff) >= 5:
            direction = "faster" if bpm_diff > 0 else "slower"
            parts.append(f"{abs(bpm_diff)} BPM {direction}")

        if parts:
            comparison = f"{genre_name} is {', '.join(parts[:2])} than {rel_name}."
        else:
            comparison = f"{genre_name} and {rel_name} share a very similar sonic profile across energy, valence, and tempo."

        cards.append(
            f'    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:20px">\n'
            f'      <div style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#6b7099;margin-bottom:8px">{genre_name} vs {rel_name}</div>\n'
            f'      <div style="font-size:14px;color:#dde1f0;line-height:1.6">{comparison}</div>\n'
            '    </div>\n'
        )

    if not cards:
        return ''

    return (
        f'\n  <div class="section-label" id="compare"><h2>How {genre_name} Compares</h2></div>\n'
        '  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:32px">\n'
        + ''.join(cards) +
        '  </div>\n'
    )


def update_faq_schema(content: str, genre_name: str, stats: dict) -> str:
    """Add instruments + happy/sad questions to the existing FAQPage JSON-LD."""
    gn = genre_name
    gl = genre_name.lower()
    acoustic = stats['acousticness']
    instrumental = stats['instrumentalness']
    valence = stats['valence']
    major_pct = stats['major_pct']
    dominant_mode = stats['dominant_mode']
    bpm_median = stats['bpm_median']
    energy = stats['energy']

    # Instruments answer
    if acoustic > 70 and instrumental > 50:
        inst_answer = f"{gn} music typically features acoustic instruments — piano, guitar, strings — with minimal vocals. With {acoustic}% acousticness and {instrumental}% instrumentalness, it's a predominantly organic, instrumental genre."
    elif acoustic > 70:
        inst_answer = f"{gn} music favors organic acoustic instruments ({acoustic}% acousticness) alongside vocal performances. Instrumentalness at {instrumental}% indicates a vocal-forward sound with natural instrument backing."
    elif acoustic > 40:
        inst_answer = f"{gn} music blends acoustic and electronic instruments ({acoustic}% acousticness). The {instrumental}% instrumentalness suggests a mix of vocal and purely instrumental tracks."
    elif instrumental > 60:
        inst_answer = f"{gn} music is predominantly electronic and instrumental — synthesizers, drum machines, and digital sound design dominate at {acoustic}% acousticness, with {instrumental}% instrumentalness meaning few or no vocals."
    else:
        inst_answer = f"{gn} music uses primarily electronic production ({acoustic}% acousticness) with significant vocal content ({instrumental}% instrumentalness shows moderate instrumental focus). Expect synthesizers and programmed beats alongside vocals."

    # Happy/sad answer
    if valence < 20:
        mood_answer = f"With a median valence of {valence}%, {gl} music is deeply melancholic and emotionally heavy. {major_pct}% of tracks use major keys, but the low valence score overrides the typical brightness of major keys."
    elif valence < 35:
        mood_answer = f"With a median valence of {valence}%, {gl} music leans toward introspection and wistfulness — more sad than happy. {major_pct}% of tracks use major keys, providing occasional uplift within an overall contemplative character."
    elif valence < 50:
        mood_answer = f"With a median valence of {valence}%, {gl} music is emotionally balanced — neither overtly happy nor sad. {major_pct}% of tracks in major keys keeps the sound from feeling too dark."
    elif valence < 65:
        mood_answer = f"With a median valence of {valence}%, {gl} music is generally positive and upbeat. {major_pct}% of tracks use major keys, reinforcing the uplifting emotional character."
    else:
        mood_answer = f"With a median valence of {valence}%, {gl} music is bright and emotionally uplifting. Combined with {major_pct}% major key usage, this is one of the happier-sounding genres."

    # Find the FAQPage JSON-LD and add the new questions
    faq_pattern = re.compile(
        r'(<script type="application/ld\+json">\s*\{[^}]*"@type":\s*"FAQPage".*?"mainEntity":\s*\[)(.*?)(\]\s*\}\s*</script>)',
        re.DOTALL
    )

    def add_faq_questions(m):
        prefix = m.group(1)
        existing = m.group(2)
        suffix = m.group(3)

        # Don't add if already has instruments question
        if 'instruments' in existing.lower() and 'happy or sad' in existing.lower():
            return m.group(0)

        new_q4 = f''',
    {{
      "@type": "Question",
      "name": "What instruments are used in {gn} music?",
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": "{inst_answer.replace('"', "'")}"
      }}
    }},
    {{
      "@type": "Question",
      "name": "Is {gn} music happy or sad?",
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": "{mood_answer.replace('"', "'")}"
      }}
    }}'''

        return prefix + existing + new_q4 + suffix

    return faq_pattern.sub(add_faq_questions, content)


def update_toc(content: str) -> str:
    """Replace ToC links with new section order."""
    new_toc_links = (
        '\n      <a href="#genre-profile" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Genre Profile</a>\n'
        '      <a href="#prompt-lab" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Prompt Lab</a>\n'
        '      <a href="#audio-dna" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Audio DNA</a>\n'
        '      <a href="#rhythm-tonality" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Rhythm &amp; Tonality</a>\n'
        '      <a href="#ai-analysis" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">AI Audio Analysis</a>\n'
        '      <a href="#emotional" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Emotional Fingerprint</a>\n'
        '      <a href="#top-artists" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Top Artists</a>\n'
        '      <a href="#hit-factors" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">What Makes a Hit</a>\n'
        '      <a href="#correlations" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Feature Correlations</a>\n'
        '      <a href="#production" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Production Profile</a>\n'
        '      <a href="#top-tracks" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Top Tracks</a>\n'
        '      <a href="#faq" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">FAQ</a>\n'
        '    '
    )

    # Find the ToC flex container and replace its contents
    toc_pattern = re.compile(
        r'(<div style="display:flex;flex-wrap:wrap;gap:8px 20px">)(.*?)(</div>\s*</nav>)',
        re.DOTALL
    )
    result = toc_pattern.sub(lambda m: m.group(1) + new_toc_links + m.group(3), content, count=1)
    return result


def add_section_ids(content: str) -> str:
    """Add IDs to section-label divs that are missing them (for 117 non-ambient pages)."""
    # Map from h2 text to id
    SECTION_ID_MAP = {
        'Audio DNA': 'audio-dna',
        '✨ Prompt Lab': 'prompt-lab',
        'Prompt Lab': 'prompt-lab',
        'Rhythm &amp; Tonality': 'rhythm-tonality',
        'Rhythm & Tonality': 'rhythm-tonality',
        'AI Audio Analysis': 'ai-analysis',
        'Emotional Fingerprint': 'emotional',
        'Top Artists': 'top-artists',
        'What Makes a Hit': 'hit-factors',
        'Feature Correlations': 'correlations',
        'Production Profile': 'production',
        'Top Tracks': 'top-tracks',
    }

    def add_id(m):
        div_tag = m.group(1)
        h2_content = m.group(2)

        # Already has an id
        if 'id=' in div_tag:
            return m.group(0)

        section_id = SECTION_ID_MAP.get(h2_content.strip())
        if section_id:
            return f'<div class="section-label" id="{section_id}"><h2>{h2_content}</h2></div>'
        return m.group(0)

    # Match section-label divs with h2
    pattern = re.compile(
        r'(<div class="section-label"(?:\s+[^>]*)?>)\s*<h2>(.*?)</h2>\s*</div>',
        re.DOTALL
    )
    return pattern.sub(add_id, content)


def add_download_button(content: str) -> str:
    """Add Download Data button next to Jump to Prompt Lab."""
    download_btn = (
        '\n    <a href="analysis.json" download style="display:inline-flex;align-items:center;gap:6px;'
        'margin-top:16px;margin-left:10px;padding:10px 20px;background:rgba(155,127,212,0.1);'
        'border:1px solid rgba(155,127,212,0.25);border-radius:8px;color:#9b7fd4;text-decoration:none;'
        'font-size:13px;font-weight:600;letter-spacing:0.03em;transition:background 0.2s" '
        "onmouseover=\"this.style.background='rgba(155,127,212,0.2)'\" "
        "onmouseout=\"this.style.background='rgba(155,127,212,0.1)'\">Download Data (JSON) ↓</a>"
    )

    # Find the Jump to Prompt Lab link and add download button after it
    pattern = re.compile(
        r'(<a href="#prompt-lab"[^>]+>Jump to Prompt Lab[^<]*</a>)',
        re.DOTALL
    )

    def add_btn(m):
        # Don't add if download button already exists
        return m.group(1) + download_btn

    # Check if already added
    if 'Download Data (JSON)' in content:
        return content

    return pattern.sub(add_btn, content, count=1)


def add_section_ids_to_header_section(content: str) -> str:
    """Also handle multi-line section-label patterns for older page format."""
    # Handle multi-line format: <div class="section-label">\n    <h2>Text</h2>\n  </div>
    SECTION_ID_MAP = {
        'Audio DNA': 'audio-dna',
        '✨ Prompt Lab': 'prompt-lab',
        'Prompt Lab': 'prompt-lab',
        'Rhythm &amp; Tonality': 'rhythm-tonality',
        'Rhythm & Tonality': 'rhythm-tonality',
        'AI Audio Analysis': 'ai-analysis',
        'Emotional Fingerprint': 'emotional',
        'Top Artists': 'top-artists',
        'What Makes a Hit': 'hit-factors',
        'Feature Correlations': 'correlations',
        'Production Profile': 'production',
        'Top Tracks': 'top-tracks',
    }

    def replace_multi(m):
        h2_text = m.group(1).strip()
        section_id = SECTION_ID_MAP.get(h2_text)
        if section_id:
            return f'  <div class="section-label" id="{section_id}"><h2>{h2_text}</h2></div>'
        return m.group(0)

    pattern = re.compile(
        r'  <div class="section-label">\s*\n\s*<h2>(.*?)</h2>\s*\n\s*</div>',
        re.DOTALL
    )
    return pattern.sub(replace_multi, content)


def reorder_audio_dna_and_prompt_lab(content: str) -> str:
    """
    Reorder sections: move Prompt Lab BEFORE Audio DNA.
    Current order: ... ToC ... Audio DNA section ... Prompt Lab section ... Rhythm ...
    New order:     ... ToC ... Genre Profile ... Prompt Lab ... Audio DNA ... Rhythm ...
    """
    # Find Audio DNA section: from the section-label id="audio-dna" to (but not including) Prompt Lab section-label
    audio_dna_pattern = re.compile(
        r'(  <!-- (?:Section: )?Audio DNA -->\s*\n)?'
        r'  (<div class="section-label" id="audio-dna">.*?</div>)\s*\n'
        r'(.*?)'  # audio dna content
        r'(?=\s*  <!-- (?:Section: )?Prompt Lab -->|\s*  <div class="section-label" id="prompt-lab">)',
        re.DOTALL
    )

    prompt_lab_pattern = re.compile(
        r'(  <!-- (?:Section: )?Prompt Lab -->\s*\n)?'
        r'  (<div class="section-label" id="prompt-lab">.*?</div>)\s*\n'
        r'(.*?)'  # prompt lab content
        r'(?=\s*  <!-- (?:Section: )?Rhythm|\s*  <div class="section-label" id="rhythm-tonality">)',
        re.DOTALL
    )

    audio_dna_m = audio_dna_pattern.search(content)
    prompt_lab_m = prompt_lab_pattern.search(content)

    if not audio_dna_m or not prompt_lab_m:
        return content  # Can't find sections, skip

    # Extract the full blocks
    audio_dna_block = audio_dna_m.group(0)
    prompt_lab_block = prompt_lab_m.group(0)

    # Make sure prompt lab comes after audio dna
    if audio_dna_m.start() > prompt_lab_m.start():
        # Already in wrong order or already swapped
        return content

    # Replace: put prompt lab first, then audio dna
    # The combined region = audio_dna + prompt_lab
    combined_start = audio_dna_m.start()
    combined_end = prompt_lab_m.end()

    # Build clean versions
    audio_label = '  <div class="section-label" id="audio-dna"><h2>Audio DNA</h2></div>\n'
    prompt_label = '  <div class="section-label" id="prompt-lab"><h2>Prompt Lab</h2></div>\n'

    # Get the content bodies (after the section-label, before the next section-label)
    audio_content_body = audio_dna_m.group(3)
    prompt_content_body = prompt_lab_m.group(3)

    new_section = (
        '  <!-- Section: Prompt Lab -->\n'
        + prompt_label
        + '\n'
        + prompt_content_body
        + '\n  <!-- Section: Audio DNA -->\n'
        + audio_label
        + '\n'
        + audio_content_body
    )

    return content[:combined_start] + new_section + content[combined_end:]


def add_callouts_to_sections(content: str, genre_name: str, stats: dict) -> str:
    """Add key finding callout boxes to relevant sections."""
    gl = genre_name.lower()
    gl_clean = re.sub(r'[^\w\s&-]', '', gl).strip()  # remove emoji etc

    # ── Audio DNA callout ────────────────────────────────────────────────────
    features = {
        'Energy': stats['energy'],
        'Acousticness': stats['acousticness'],
        'Instrumentalness': stats['instrumentalness'],
        'Danceability': stats['danceability'],
        'Valence': stats['valence'],
        'Speechiness': stats['speechiness'],
    }
    highest_feat = max(features, key=features.get)
    lowest_feat = min(features, key=features.get)
    h_val = features[highest_feat]
    l_val = features[lowest_feat]

    if h_val > 70 and l_val < 10:
        interpretation = f"a genre defined as much by what it lacks as what it contains"
    elif h_val > 70:
        interpretation = f"showing a strong emphasis on {highest_feat.lower()}"
    elif l_val < 5:
        interpretation = f"with almost no {lowest_feat.lower()} to speak of"
    else:
        interpretation = f"revealing a balanced sonic profile"

    audio_dna_callout = build_callout(
        f"Six audio features define {gl_clean}'s fingerprint: {highest_feat} leads at {h_val}%, "
        f"while {lowest_feat} sits at just {l_val}% — {interpretation}."
    )

    # ── Rhythm & Tonality callout ─────────────────────────────────────────────
    bpm_stdev_str = f" (σ {stats['bpm_stdev']})" if stats['bpm_stdev'] > 0 else ""
    rhythm_callout = build_callout(
        f"{stats['dominant_pct']}% of {gl_clean} tracks are in a {stats['dominant_mode']} key, "
        f"with {stats['top_key']} the most common. "
        f"Typical BPM: {stats['bpm_median']}{bpm_stdev_str}."
    )

    # ── Top Artists callout ───────────────────────────────────────────────────
    artists = stats['artists']
    if len(artists) >= 3:
        a1, a2, a3 = artists[0], artists[1], artists[2]
        artists_callout = build_callout(
            f"{a1['name']} dominates with {a1['count']} tracks in the top 100, "
            f"followed by {a2['name']} ({a2['count']}) and {a3['name']} ({a3['count']})."
        )
    elif len(artists) >= 2:
        a1, a2 = artists[0], artists[1]
        artists_callout = build_callout(
            f"{a1['name']} leads with {a1['count']} tracks, followed by {a2['name']} ({a2['count']})."
        )
    elif len(artists) == 1:
        artists_callout = build_callout(
            f"{artists[0]['name']} dominates with {artists[0]['count']} tracks in the top 100."
        )
    else:
        artists_callout = ''

    # ── Top Tracks callout ─────────────────────────────────────────────────────
    top_track = stats['top_track_name']
    top_artist = stats['top_track_artist']
    top_pop = stats['top_track_pop']
    if top_track:
        # Clean artist name (take first if semicolon-separated)
        top_artist_clean = top_artist.split(';')[0] if top_artist else ''
        tracks_callout = build_callout(
            f"The most popular {gl_clean} track is &ldquo;{top_track}&rdquo;"
            + (f" by {top_artist_clean}" if top_artist_clean else "") +
            (f" with a popularity score of {top_pop}." if top_pop else ".")
        )
    else:
        tracks_callout = ''

    # Insert callouts after each section-label
    def insert_after_section(content, section_id, callout):
        """Insert callout HTML immediately after the section-label div for section_id."""
        pattern = re.compile(
            r'(<div class="section-label" id="' + re.escape(section_id) + r'">.*?</div>\s*\n)',
            re.DOTALL
        )
        return pattern.sub(lambda m: m.group(1) + callout, content, count=1)

    # Don't add callout if already present (idempotency)
    if 'Key finding:' not in content:
        content = insert_after_section(content, 'audio-dna', audio_dna_callout)
        content = insert_after_section(content, 'rhythm-tonality', rhythm_callout)
        if artists_callout:
            content = insert_after_section(content, 'top-artists', artists_callout)
        if tracks_callout:
            content = insert_after_section(content, 'top-tracks', tracks_callout)

    return content


def add_genre_profile_and_compare(content: str, slug: str, genre_name: str, stats: dict) -> str:
    """Add Genre Profile section after ToC and Compare section before FAQ/Related."""

    # ── Genre Profile: insert after ToC (which ends with </nav>) before Audio DNA ──
    profile_html = build_genre_profile_html(genre_name, stats)

    # Check if already added
    if 'id="genre-profile"' not in content:
        # Find the ToC nav closing tag, insert after it
        toc_end_pattern = re.compile(
            r'(</nav>\s*\n\s*<!-- (?:Section: )?Audio DNA -->)',
            re.DOTALL
        )
        if toc_end_pattern.search(content):
            content = toc_end_pattern.sub(
                lambda m: '</nav>\n' + profile_html + '\n  <!-- Section: Audio DNA -->',
                content, count=1
            )
        else:
            # Try to find </nav> before section-label id="audio-dna"
            toc_end_pattern2 = re.compile(
                r'(</nav>\s*\n\s*<!-- Section: Prompt Lab -->)',
                re.DOTALL
            )
            if toc_end_pattern2.search(content):
                content = toc_end_pattern2.sub(
                    lambda m: '</nav>\n' + profile_html + '\n  <!-- Section: Prompt Lab -->',
                    content, count=1
                )
            else:
                # Fallback: find toc nav specifically
                toc_pattern = re.compile(
                    r'(  </div>\s*\n  </nav>\s*\n)',
                    re.DOTALL
                )
                # Only replace the FIRST match (the ToC nav)
                content = toc_pattern.sub(
                    lambda m: m.group(1) + profile_html,
                    content, count=1
                )

    # ── Compare Section: insert before Related Genres or FAQ ──────────────────
    compare_html = build_compare_html(slug, genre_name, stats)

    if compare_html and 'id="compare"' not in content:
        # Insert before the Related Genres section or top-tracks trailing + related
        before_related = re.compile(
            r'(\s*<div class="section-label" id="related">)',
            re.DOTALL
        )
        if before_related.search(content):
            content = before_related.sub(
                lambda m: '\n' + compare_html + m.group(1),
                content, count=1
            )

    return content


def add_faq_section(content: str, genre_name: str, stats: dict) -> str:
    """Add visible FAQ section before Related Genres."""
    if 'id="faq"' in content:
        return content

    faq_html = build_faq_html(genre_name, stats)

    # Insert before Related Genres
    before_related = re.compile(
        r'(\s*<div class="section-label" id="related">)',
        re.DOTALL
    )
    if before_related.search(content):
        content = before_related.sub(
            lambda m: '\n' + faq_html + m.group(1),
            content, count=1
        )

    return content


def extract_genre_name(content: str, slug: str) -> str:
    """Extract the genre display name from the h1 tag."""
    m = re.search(r'<h1>(.*?)</h1>', content, re.DOTALL)
    if m:
        name = m.group(1).strip()
        # Strip emoji and extra whitespace
        name = re.sub(r'[\U00010000-\U0010ffff]', '', name)  # Remove emoji
        name = re.sub(r'[^\w\s&/\-\'()]', '', name)
        name = name.strip()
        if name:
            return name
    # Fallback to slug
    return slug.replace('-', ' ').title()


def process_genre(slug: str, dry_run: bool = False) -> bool:
    """Process a single genre page. Returns True if modified."""
    html_path = SITE_DIR / slug / "index.html"
    analysis_path = SITE_DIR / slug / "analysis.json"

    if not html_path.exists():
        print(f"  ⚠️  {slug}: index.html not found, skipping")
        return False

    if not analysis_path.exists():
        print(f"  ⚠️  {slug}: analysis.json not found, skipping")
        return False

    with open(html_path, 'r', encoding='utf-8') as f:
        original = f.read()

    data = {}
    with open(analysis_path) as f:
        data = json.load(f)

    stats = extract_stats(data)
    genre_name = extract_genre_name(original, slug)
    content = original

    # 1. Add section IDs (multi-line format)
    content = add_section_ids_to_header_section(content)
    # Also handle inline format
    content = add_section_ids(content)

    # 2. Add Download button
    content = add_download_button(content)

    # 3. Update ToC
    content = update_toc(content)

    # 4. Reorder sections (Prompt Lab before Audio DNA)
    content = reorder_audio_dna_and_prompt_lab(content)

    # 5. Add Genre Profile prose section
    content = add_genre_profile_and_compare(content, slug, genre_name, stats)

    # 6. Add callout boxes
    content = add_callouts_to_sections(content, genre_name, stats)

    # 7. Add FAQ section
    content = add_faq_section(content, genre_name, stats)

    # 8. Update FAQ schema
    content = update_faq_schema(content, genre_name, stats)

    if content == original:
        print(f"  ⚪ {slug}: no changes")
        return False

    if dry_run:
        print(f"  🔵 {slug}: would update (dry run)")
        return True

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✅ {slug}: updated")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Apply Phase 2 fixes to all genre pages')
    parser.add_argument('--dry-run', action='store_true', help='Do not write files')
    parser.add_argument('--genre', type=str, help='Process only this genre slug')
    args = parser.parse_args()

    if args.genre:
        slugs = [args.genre]
    else:
        slugs = sorted([d.name for d in SITE_DIR.iterdir() if d.is_dir()])

    print(f"Processing {len(slugs)} genre pages...")
    updated = 0
    errors = 0

    for slug in slugs:
        try:
            if process_genre(slug, dry_run=args.dry_run):
                updated += 1
        except Exception as e:
            print(f"  ❌ {slug}: ERROR — {e}")
            import traceback
            traceback.print_exc()
            errors += 1

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Done: {updated} updated, {errors} errors out of {len(slugs)} genres")


if __name__ == '__main__':
    main()
