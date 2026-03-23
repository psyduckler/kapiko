#!/usr/bin/env python3
"""
Generate genre pages for kapiko.ai based on analysis.json data.
Reads the soul page as template and adapts it for each genre.
"""

import json
import sys
import os
from pathlib import Path

# Genre metadata
GENRE_METADATA = {
    'pop': {
        'emoji': '🎵', 
        'color': '#e87d7d', 
        'desc': "Mainstream popular music with catchy melodies, polished production, and broad commercial appeal.",
        'style_tags': "pop, mainstream, radio-friendly, catchy, polished",
        'instruments': "synth, programmed drums, electric guitar, vocal layers, bass",
        'mood': "catchy, uplifting, energetic, anthemic"
    },
    'r-n-b': {
        'emoji': '🎤', 
        'color': '#9b7fd4', 
        'desc': "Rhythm and blues with smooth vocals, groove-heavy production, and modern 808-driven beats.",
        'style_tags': "R&B, modern R&B, neo-R&B, smooth, groovy",
        'instruments': "808 bass, smooth synth pads, electric piano, vocal runs, hi-hats",
        'mood': "smooth, sensual, moody, intimate"
    },
    'country': {
        'emoji': '🤠', 
        'color': '#d4a574', 
        'desc': "American roots music featuring storytelling vocals, acoustic and electric guitar.",
        'style_tags': "country, americana, country-pop, outlaw, twang",
        'instruments': "acoustic guitar, pedal steel, fiddle, banjo, dobro",
        'mood': "nostalgic, heartfelt, warm, storytelling"
    },
    'rock': {
        'emoji': '🎸', 
        'color': '#e85d5d', 
        'desc': "Guitar-driven music with strong rhythms and powerful vocals.",
        'style_tags': "rock, alternative rock, hard rock, classic rock, arena rock",
        'instruments': "electric guitar, distortion, drum kit, bass guitar, power chords",
        'mood': "powerful, driving, raw, rebellious"
    },
    'edm': {
        'emoji': '⚡', 
        'color': '#4ecdc4', 
        'desc': "Electronic dance music designed for festivals and big rooms. High energy, dramatic builds.",
        'style_tags': "EDM, dance, festival, house, progressive",
        'instruments': "synth leads, sidechained bass, risers, drops, four-on-the-floor kick",
        'mood': "euphoric, high-energy, anthemic, pulsing"
    },
    'indie': {
        'emoji': '🎭', 
        'color': '#5b9bd5', 
        'desc': "Independent music with creative freedom and unconventional production.",
        'style_tags': "indie, indie rock, indie pop, alternative, lo-fi",
        'instruments': "jangly guitar, analog synths, drum machine, bass, reverbed vocals",
        'mood': "wistful, introspective, dreamy, bittersweet"
    },
    'folk': {
        'emoji': '🌾', 
        'color': '#8fbc8f', 
        'desc': "Traditional and contemporary acoustic music rooted in storytelling and organic instrumentation.",
        'style_tags': "folk, acoustic, singer-songwriter, traditional, roots",
        'instruments': "acoustic guitar, banjo, mandolin, harmonica, upright bass",
        'mood': "earthy, warm, storytelling, intimate"
    },
    'reggaeton': {
        'emoji': '🔥', 
        'color': '#ff6b6b', 
        'desc': "Latin urban music built on the iconic dembow rhythm. Fastest-growing genre globally.",
        'style_tags': "reggaeton, latin urban, dembow, perreo, trap latino",
        'instruments': "dembow beat, 808 bass, synth stabs, vocal chops, clap patterns",
        'mood': "infectious, rhythmic, bold, party"
    },
    'synth-pop': {
        'emoji': '🎹', 
        'color': '#c77dba', 
        'desc': "80s-born pop music built on synthesizers and drum machines.",
        'style_tags': "synth-pop, new wave, electropop, 80s, synthwave",
        'instruments': "analog synth, drum machine, arpeggiator, vocoder, gated reverb",
        'mood': "nostalgic, bright, danceable, futuristic"
    },
    'trip-hop': {
        'emoji': '🌙', 
        'color': '#6a5acd', 
        'desc': "Downtempo electronic music with jazz samples, moody atmospheres, and cinematic production.",
        'style_tags': "trip-hop, downtempo, Bristol sound, dark electronic, cinematic",
        'instruments': "breakbeats, jazz samples, vinyl crackle, deep bass, Rhodes piano",
        'mood': "moody, atmospheric, nocturnal, hypnotic"
    },
    'blues': {
        'emoji': '🎺',
        'color': '#4a7ab5',
        'desc': "Expressive music built on twelve-bar progressions, call-and-response vocals, and raw emotional delivery.",
        'style_tags': "blues, delta blues, Chicago blues, blues rock, electric blues",
        'instruments': "electric guitar, harmonica, bass guitar, organ, slide guitar",
        'mood': "soulful, gritty, expressive, melancholic"
    },
    'metal': {
        'emoji': '🤘',
        'color': '#8b0000',
        'desc': "Heavy, powerful rock with distorted guitars, aggressive instrumentation, and intense energy.",
        'style_tags': "metal, heavy metal, thrash, power metal, progressive metal",
        'instruments': "distorted electric guitar, double bass drum, bass guitar, power chords, shredding",
        'mood': "aggressive, powerful, intense, dark"
    },
    'funk': {
        'emoji': '🎸',
        'color': '#ff8c00',
        'desc': "Groove-heavy music emphasizing rhythm section, syncopated basslines, and infectious danceability.",
        'style_tags': "funk, P-funk, soul-funk, funk rock, electro-funk",
        'instruments': "slap bass, clavinet, wah-wah guitar, horn section, tight drums",
        'mood': "groovy, energetic, playful, infectious"
    },
    'disco': {
        'emoji': '🕺',
        'color': '#daa520',
        'desc': "Funk-influenced dance music with orchestral arrangements, steady four-on-the-floor beats, and euphoric energy.",
        'style_tags': "disco, nu-disco, Eurodisco, disco house, boogie",
        'instruments': "string section, rhythm guitar, hi-hat, bass guitar, brass hits",
        'mood': "euphoric, glamorous, danceable, celebratory"
    },
    'reggae': {
        'emoji': '🏝️',
        'color': '#228b22',
        'desc': "Jamaican music with off-beat rhythms, deep bass, and social consciousness. The sound of island groove.",
        'style_tags': "reggae, roots reggae, dancehall, dub, lovers rock",
        'instruments': "skank guitar, deep bass, organ bubbles, rim shot, melodica",
        'mood': "laid-back, conscious, warm, rhythmic"
    },
    'punk': {
        'emoji': '⚡',
        'color': '#ff1493',
        'desc': "Raw, rebellious rock with short songs, fast tempos, and anti-establishment energy.",
        'style_tags': "punk, punk rock, pop-punk, hardcore punk, post-punk",
        'instruments': "power chords, fast drums, distorted bass, shout vocals, snare",
        'mood': "rebellious, energetic, raw, defiant"
    },
    'house': {
        'emoji': '🏠',
        'color': '#9370db',
        'desc': "Four-on-the-floor electronic dance music with soulful and disco influences. The backbone of club culture.",
        'style_tags': "house, deep house, tech house, progressive house, vocal house",
        'instruments': "four-on-the-floor kick, hi-hats, synth chords, bass groove, vocal samples",
        'mood': "uplifting, groovy, euphoric, hypnotic"
    },
    'techno': {
        'emoji': '🤖',
        'color': '#2f4f4f',
        'desc': "Repetitive electronic music with mechanical rhythms, futuristic sounds, and industrial aesthetics.",
        'style_tags': "techno, Detroit techno, minimal techno, industrial techno, acid techno",
        'instruments': "drum machine, analog synth, 303 acid line, industrial percussion, reverb tails",
        'mood': "hypnotic, dark, driving, mechanical"
    },
    'trance': {
        'emoji': '🌀',
        'color': '#00ced1',
        'desc': "Hypnotic electronic music with ethereal melodies, uplifting builds, and transcendent energy.",
        'style_tags': "trance, uplifting trance, progressive trance, vocal trance, psytrance",
        'instruments': "supersaw synth, pluck leads, kick drum, ethereal pads, arpeggiated sequences",
        'mood': "euphoric, transcendent, emotional, driving"
    },
    'deep-house': {
        'emoji': '🌊',
        'color': '#5f9ea0',
        'desc': "Soulful house music with warm basslines, jazzy elements, and atmospheric depth.",
        'style_tags': "deep house, soulful house, organic house, afro house, melodic house",
        'instruments': "warm bass, jazz chords, soft pads, shuffled hi-hats, vocal chops",
        'mood': "soulful, warm, atmospheric, groovy"
    },
    'dubstep': {
        'emoji': '🔊',
        'color': '#4b0082',
        'desc': "Electronic music with wobble bass, syncopated rhythms, and dramatic drops.",
        'style_tags': "dubstep, brostep, melodic dubstep, riddim, future bass",
        'instruments': "wobble bass, LFO modulation, snare hits, sub-bass, synth risers",
        'mood': "intense, dramatic, heavy, cinematic"
    },
    'k-pop': {
        'emoji': '🇰🇷',
        'color': '#ff69b4',
        'desc': "Korean pop music with polished production, choreographed performances, and genre-blending creativity.",
        'style_tags': "K-pop, Korean pop, idol pop, K-R&B, K-hip-hop",
        'instruments': "synth, programmed drums, bass drops, vocal harmonies, electronic beats",
        'mood': "energetic, catchy, polished, dynamic"
    },
    'latin': {
        'emoji': '🌶️',
        'color': '#ff4500',
        'desc': "Music from Latin America featuring diverse rhythms, passionate vocals, and cultural traditions.",
        'style_tags': "latin, latin pop, salsa, cumbia, bachata",
        'instruments': "congas, timbales, acoustic guitar, brass section, bongos",
        'mood': "passionate, rhythmic, warm, celebratory"
    },
    'afrobeat': {
        'emoji': '🌍',
        'color': '#daa520',
        'desc': "Polyrhythmic West African grooves blending jazz, funk, and traditional percussion. The sound of a continent.",
        'style_tags': "Afrobeat, Afrobeats, Afro-fusion, highlife, Afro-pop",
        'instruments': "talking drum, shekere, horn section, rhythm guitar, polyrhythmic percussion",
        'mood': "joyful, rhythmic, communal, vibrant"
    },
    'j-pop': {
        'emoji': '🎌',
        'color': '#ff6347',
        'desc': "Japanese pop music with distinctive melodies, dynamic production, and anime-adjacent energy.",
        'style_tags': "J-pop, Japanese pop, anime OST, city pop, visual kei",
        'instruments': "synth, electric guitar, programmed drums, piano, vocal harmonies",
        'mood': "bright, energetic, melodic, emotional"
    },
    'alt-rock': {
        'emoji': '⚡',
        'color': '#cd853f',
        'desc': "Alternative rock with unconventional song structures, indie sensibilities, and genre-bending creativity.",
        'style_tags': "alt-rock, alternative, post-punk revival, indie rock, shoegaze",
        'instruments': "distorted guitar, bass, drums, reverb effects, synths",
        'mood': "angsty, introspective, dynamic, raw"
    },
    'grunge': {
        'emoji': '🧽',
        'color': '#696969',
        'desc': "Raw rock from the Pacific Northwest with distorted guitars, angst-driven lyrics, and deliberate lo-fi production.",
        'style_tags': "grunge, Seattle sound, post-grunge, sludge, noise rock",
        'instruments': "heavy distortion guitar, drop-D tuning, pounding drums, bass, flanged vocals",
        'mood': "angsty, heavy, raw, melancholic"
    },
    'hard-rock': {
        'emoji': '🎸',
        'color': '#b22222',
        'desc': "Heavy guitar-driven rock with powerful drums, strong melodies, and arena-filling energy.",
        'style_tags': "hard rock, classic rock, arena rock, blues rock, stadium rock",
        'instruments': "overdriven guitar, power chords, bass guitar, heavy drums, wailing vocals",
        'mood': "powerful, energetic, rebellious, anthemic"
    },
    'singer-songwriter': {
        'emoji': '✍️',
        'color': '#bc8f8f',
        'desc': "Intimate acoustic music with personal lyrics, solo performances, and raw emotional honesty.",
        'style_tags': "singer-songwriter, acoustic, folk-pop, confessional, storytelling",
        'instruments': "acoustic guitar, piano, soft vocals, light percussion, harmonica",
        'mood': "intimate, honest, vulnerable, reflective"
    },
    'indie-pop': {
        'emoji': '🎈',
        'color': '#da70d6',
        'desc': "Independent pop music with melodic hooks, artistic integrity, and lo-fi charm.",
        'style_tags': "indie pop, dream pop, bedroom pop, twee, jangle pop",
        'instruments': "jangly guitar, synth pads, drum machine, bass, breathy vocals",
        'mood': "dreamy, bittersweet, whimsical, nostalgic"
    }
}

def load_analysis_data(genre_slug):
    """Load analysis.json for the given genre."""
    analysis_path = Path(f"~/kapiko/site/genres/{genre_slug}/analysis.json").expanduser()
    if not analysis_path.exists():
        raise FileNotFoundError(f"Analysis file not found: {analysis_path}")
    
    with open(analysis_path, 'r') as f:
        return json.load(f)

def load_soul_template():
    """Load the soul page template."""
    template_path = Path("~/kapiko/site/genres/soul/index.html").expanduser()
    with open(template_path, 'r') as f:
        return f.read()

def format_key_name(key_code):
    """Convert key code to readable format."""
    key_mapping = {
        0: 'C', 1: 'C#/Db', 2: 'D', 3: 'D#/Eb', 4: 'E', 5: 'F',
        6: 'F#/Gb', 7: 'G', 8: 'G#/Ab', 9: 'A', 10: 'A#/Bb', 11: 'B'
    }
    return key_mapping.get(key_code, f'Key {key_code}')

def create_prompt_lab_content(genre_slug, data, metadata):
    """Generate the prompt lab sections for the genre."""
    
    # Get top keys from key_distribution
    key_items = list(data['key_distribution'].items())
    key_items.sort(key=lambda x: x[1], reverse=True)
    top_keys = [k for k, v in key_items[:3]]
    
    # Feature Translator
    feature_translator = f"""BPM {int(data['bpm']['q1'])}-{int(data['bpm']['q3'])}: {metadata['mood'].split(',')[0]} pace
Energy {int(data['energy']['mean']*100-10)}-{int(data['energy']['mean']*100+10)}%: {metadata['mood'].split(',')[0]}, {metadata['mood'].split(',')[1] if ',' in metadata['mood'] else 'dynamic'}
Valence {int(data['valence']['mean']*100-10)}-{int(data['valence']['mean']*100+10)}%: {metadata['mood']}
Danceability {int(data['danceability']['mean']*100-5)}-{int(data['danceability']['mean']*100+5)}%: {metadata['style_tags'].split(',')[0]} groove
Acousticness {int(data['acousticness']['mean']*100-10)}-{int(data['acousticness']['mean']*100+10)}%: {metadata['instruments'].split(',')[0]} textures
Instrumentalness {int(data['instrumentalness']['mean']*100-10)}-{int(data['instrumentalness']['mean']*100+10)}%: Focus on {metadata['instruments'].split(',')[0]}
Speechiness {int(data['speechiness']['mean']*100)}-{int(data['speechiness']['mean']*100+10)}%: Clean {metadata['style_tags'].split(',')[0]} passages
Tempo: {metadata['mood'].split(',')[0]} to moderate
Key preference: {top_keys[0]}, {top_keys[1] if len(top_keys) > 1 else 'C'}, warm keys"""

    # Prompt Template
    genre_display = genre_slug.replace('-', ' ').title()
    main_instrument = metadata['instruments'].split(',')[0]
    prompt_template = f"""Create a {metadata['style_tags'].split(',')[0]} track with:

• {metadata['instruments'].split(',')[0]} foundation ({int(data['bpm']['median'])} BPM)
• {metadata['style_tags'].split(',')[1] if ',' in metadata['style_tags'] else 'modern'}-inspired {metadata['instruments'].split(',')[1] if ',' in metadata['instruments'] else 'elements'}
• {metadata['mood'].split(',')[0]} {metadata['instruments'].split(',')[0]} patterns
• {metadata['instruments'].split(',')[2] if len(metadata['instruments'].split(',')) > 2 else 'melodic'} {metadata['instruments'].split(',')[3] if len(metadata['instruments'].split(',')) > 3 else 'layers'}
• {metadata['mood'].split(',')[1] if ',' in metadata['mood'] else 'atmospheric'} production style
• {metadata['style_tags'].split(',')[2] if len(metadata['style_tags'].split(',')) > 2 else 'signature'} sound design
• Moderate energy ({int(data['energy']['mean']*100)}%), {metadata['mood'].split(',')[0]} mood ({int(data['valence']['mean']*100)}%)
• {metadata['style_tags'].split(',')[0]} arrangement ({int(data['instrumentalness']['mean']*100)}%), {metadata['instruments'].split(',')[0]} elements ({int(data['acousticness']['mean']*100)}%)

Artists to reference: {', '.join([artist['name'] for artist in data['top_artists'][:6]])}

Duration: 3-4 minutes, perfect for {metadata['mood'].split(',')[-1]} listening"""

    # Genre Recipe JSON
    # Calculate mode percentages from mode_distribution
    total_tracks = data['mode_distribution']['Major'] + data['mode_distribution']['Minor']
    major_pct = (data['mode_distribution']['Major'] / total_tracks) * 100
    minor_pct = (data['mode_distribution']['Minor'] / total_tracks) * 100
    
    # Extract artist names
    artist_names = [artist['name'] for artist in data['top_artists'][:8]]
    
    genre_recipe = f"""{{
  "genre": "{genre_slug.replace('-', ' ')}",
  "audio_features": {{
    "bpm": {{"min": {int(data['bpm']['min'])}, "max": {int(data['bpm']['max'])}, "median": {int(data['bpm']['median'])}}},
    "energy": {{"avg": {data['energy']['mean']:.3f}, "range": "{metadata['mood'].split(',')[0]}"}},
    "valence": {{"avg": {data['valence']['mean']:.3f}, "range": "{metadata['mood']}"}},
    "danceability": {{"avg": {data['danceability']['mean']:.3f}, "range": "{metadata['style_tags'].split(',')[0]} groove"}},
    "acousticness": {{"avg": {data['acousticness']['mean']:.3f}, "range": "{metadata['instruments'].split(',')[0]}/organic"}},
    "instrumentalness": {{"avg": {data['instrumentalness']['mean']:.3f}, "range": "focus on {metadata['instruments'].split(',')[0]}"}},
    "key_preference": {json.dumps(top_keys)},
    "mode_preference": {{"major": {major_pct:.1f}, "minor": {minor_pct:.1f}}}
  }},
  "production_style": {{
    "instruments": {json.dumps(metadata['instruments'].split(', '))},
    "style_tags": {json.dumps(metadata['style_tags'].split(', '))},
    "mood_descriptors": {json.dumps(metadata['mood'].split(', '))},
    "tempo_category": "{metadata['mood'].split(',')[0]}_to_moderate"
  }},
  "reference_artists": {json.dumps(artist_names)},
  "track_characteristics": {{
    "typical_length": "3-4 minutes",
    "listening_context": "{metadata['mood'].split(',')[-1]} listening",
    "production_focus": "{metadata['instruments'].split(',')[0]} foundation"
  }}
}}"""

    return feature_translator, prompt_template, genre_recipe

def generate_genre_page(genre_slug):
    """Generate a complete genre page HTML."""
    if genre_slug not in GENRE_METADATA:
        raise ValueError(f"Unknown genre: {genre_slug}")
    
    # Load data
    data = load_analysis_data(genre_slug)
    metadata = GENRE_METADATA[genre_slug]
    template = load_soul_template()
    
    # Generate prompt lab content
    feature_translator, prompt_template, genre_recipe = create_prompt_lab_content(genre_slug, data, metadata)
    
    # Replace template content
    html = template
    
    # Basic replacements
    html = html.replace("Soul — kapiko", f"{genre_slug.replace('-', ' ').title()} — kapiko")
    html = html.replace("<title>Soul — kapiko", f"<title>{genre_slug.replace('-', ' ').title()} — kapiko")
    html = html.replace('🎷', metadata['emoji'])
    html = html.replace('#4ecdc4', metadata['color'])  # Replace the teal accent color
    
    # Header section - correct patterns from soul page
    html = html.replace(
        '<h1>Soul</h1>',
        f'<h1>{metadata["emoji"]} {genre_slug.replace("-", " ").title()}</h1>'
    )
    html = html.replace(
        'Dusty beats and mellow grooves',
        metadata['desc'].split('.')[0]  # First sentence only for subtitle
    )
    
    # Replace data in script section
    # Find and replace the soul data with our genre data
    html = html.replace('"soul"', f'"{genre_slug}"')
    html = html.replace('const genreData = null; // Will be loaded via JS', f'const genreData = {json.dumps(data, indent=2)};')
    
    # Replace prompt lab content
    # Feature Translator
    old_translator = """BPM 70-95: Laid-back groove, unhurried pace
Energy 15-45%: Mellow, contemplative, low-key
Valence 10-45%: Introspective, melancholic, bittersweet
Danceability 55-75%: Subtle head-nod rhythm, not for clubs
Acousticness 50-90%: Warm analog textures, organic feel
Instrumentalness 60-95%: Minimal vocals, focus on melody
Speechiness 0-10%: Clean instrumental passages
Tempo: Slow to moderate, never rushed
Key preference: G#/Ab, C#/Db, flat keys for warmth"""
    html = html.replace(old_translator, feature_translator)
    
    # Prompt Template - find the existing one and replace
    old_template_start = html.find('Create a lo-fi hip hop beat with:')
    if old_template_start != -1:
        old_template_end = html.find('Duration: 2-3 minutes, perfect for studying/relaxing', old_template_start)
        if old_template_end != -1:
            old_template_end = html.find('</pre>', old_template_end)
            if old_template_end != -1:
                old_template = html[old_template_start:old_template_end]
                html = html.replace(old_template, prompt_template)
    
    # Genre Recipe JSON - find and replace the JSON block
    old_json_start = html.find('{\n  "genre": "lo-fi hip hop",')
    if old_json_start != -1:
        old_json_end = html.find('}\n}', old_json_start) + 2
        if old_json_end > old_json_start:
            old_json = html[old_json_start:old_json_end]
            html = html.replace(old_json, genre_recipe)
    
    return html

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 generate_genre_page_v2.py <genre-slug>")
        sys.exit(1)
    
    genre_slug = sys.argv[1]
    
    try:
        # Generate the HTML
        html_content = generate_genre_page(genre_slug)
        
        # Create output directory
        output_dir = Path(f"~/kapiko/site/genres/{genre_slug}").expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        output_path = output_dir / "index.html"
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"Generated {output_path} ({len(html_content)} chars)")
        
    except Exception as e:
        print(f"Error generating page for {genre_slug}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()