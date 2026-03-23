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