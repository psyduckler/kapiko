#!/usr/bin/env python3

import json
import os
import sys
import re
from pathlib import Path

# Genre metadata
GENRE_METADATA = {
    'piano': {
        'emoji': '🎹',
        'description': 'Classical and modern piano compositions',
        'prompt_style': 'delicate, expressive, dynamic range',
        'mood_keywords': ['contemplative', 'melodic', 'expressive', 'flowing'],
        'typical_instruments': ['piano', 'solo piano', 'grand piano'],
        'reference_artists': ['Ludovico Einaudi', 'Max Richter', 'Ólafur Arnalds']
    },
    'sleep': {
        'emoji': '🌙',
        'description': 'Gentle sounds for rest and relaxation',
        'prompt_style': 'ambient, minimal, soothing',
        'mood_keywords': ['peaceful', 'calming', 'dreamy', 'serene'],
        'typical_instruments': ['soft pads', 'gentle piano', 'ambient textures'],
        'reference_artists': ['Brian Eno', 'Tim Hecker', 'Stars of the Lid']
    },
    'chill': {
        'emoji': '😌',
        'description': 'Laid-back vibes for any time',
        'prompt_style': 'relaxed, smooth, unhurried',
        'mood_keywords': ['laid-back', 'smooth', 'mellow', 'easy-going'],
        'typical_instruments': ['electric piano', 'soft guitar', 'subtle beats'],
        'reference_artists': ['Bonobo', 'Thievery Corporation', 'Zero 7']
    },
    'study': {
        'emoji': '📚',
        'description': 'Focus music for productivity',
        'prompt_style': 'minimal, repetitive, non-distracting',
        'mood_keywords': ['focused', 'steady', 'repetitive', 'minimal'],
        'typical_instruments': ['ambient pads', 'subtle piano', 'light percussion'],
        'reference_artists': ['Kiasmos', 'Nils Frahm', 'A Winged Victory for the Sullen']
    },
    'classical': {
        'emoji': '🎻',
        'description': 'Timeless orchestral and chamber works',
        'prompt_style': 'orchestral, traditional, dynamic',
        'mood_keywords': ['majestic', 'timeless', 'dramatic', 'sophisticated'],
        'typical_instruments': ['strings', 'woodwinds', 'brass', 'orchestral'],
        'reference_artists': ['Bach', 'Mozart', 'Beethoven']
    },
    'jazz': {
        'emoji': '🎷',
        'description': 'Smooth jazz and improvisational music',
        'prompt_style': 'improvisational, swing, sophisticated',
        'mood_keywords': ['sophisticated', 'improvisational', 'smooth', 'soulful'],
        'typical_instruments': ['saxophone', 'piano', 'upright bass', 'drums'],
        'reference_artists': ['Miles Davis', 'Bill Evans', 'Coltrane']
    },
    'acoustic': {
        'emoji': '🎸',
        'description': 'Organic guitar and folk sounds',
        'prompt_style': 'organic, natural, fingerpicked',
        'mood_keywords': ['organic', 'natural', 'intimate', 'warm'],
        'typical_instruments': ['acoustic guitar', 'fingerpicking', 'folk instruments'],
        'reference_artists': ['Nick Drake', 'Iron & Wine', 'Bon Iver']
    },
    'electronic': {
        'emoji': '⚡',
        'description': 'Digital beats and synthetic textures',
        'prompt_style': 'synthetic, rhythmic, digital',
        'mood_keywords': ['digital', 'synthetic', 'rhythmic', 'modern'],
        'typical_instruments': ['synthesizers', 'drum machines', 'digital effects'],
        'reference_artists': ['Aphex Twin', 'Boards of Canada', 'Autechre']
    },
    'hip-hop': {
        'emoji': '🎤',
        'description': 'Urban beats and rhythmic flows',
        'prompt_style': 'rhythmic, boom-bap, sample-based',
        'mood_keywords': ['rhythmic', 'urban', 'groovy', 'sample-based'],
        'typical_instruments': ['drum samples', 'bass', 'vocal samples', 'turntables'],
        'reference_artists': ['J Dilla', 'Madlib', 'DJ Premier']
    },
    'soul': {
        'emoji': '🎙️',
        'description': 'Emotional vocals and R&B grooves',
        'prompt_style': 'soulful, emotional, groove-based',
        'mood_keywords': ['soulful', 'emotional', 'groovy', 'heartfelt'],
        'typical_instruments': ['vocals', 'organ', 'bass guitar', 'brass section'],
        'reference_artists': ['Stevie Wonder', 'Marvin Gaye', 'Aretha Franklin']
    }
}

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def safe_division(num, denom, default=0):
    """Safe division with default"""
    try:
        return num / denom if denom != 0 else default
    except:
        return default

def generate_audio_features_from_data(track_name, artist, all_scatter_data, all_tracks):
    """Extract audio features for a track from various scatter plot data"""
    features = {}
    
    # Find in energy_valence_scatter
    for item in all_scatter_data.get('energy_valence_scatter', []):
        if item['name'] == track_name and item['artists'] == artist:
            features['energy'] = item['energy']
            features['valence'] = item['valence']
            break
    
    # Find in acoustic_instrumental_scatter  
    for item in all_scatter_data.get('acoustic_instrumental_scatter', []):
        if item['name'] == track_name and item['artists'] == artist:
            features['acousticness'] = item['acousticness']
            features['instrumentalness'] = item['instrumentalness']
            break
    
    # Find additional features (we'll estimate these from the genre averages)
    genre_data = all_scatter_data
    features.setdefault('energy', genre_data.get('energy', {}).get('mean', 0.5))
    features.setdefault('valence', genre_data.get('valence', {}).get('mean', 0.5))
    features.setdefault('acousticness', genre_data.get('acousticness', {}).get('mean', 0.5))
    features.setdefault('instrumentalness', genre_data.get('instrumentalness', {}).get('mean', 0.5))
    features.setdefault('danceability', genre_data.get('danceability', {}).get('mean', 0.5))
    features.setdefault('speechiness', genre_data.get('speechiness', {}).get('mean', 0.05))
    features.setdefault('liveness', 0.1)  # Default low liveness
    features.setdefault('loudness', -10.0)  # Default loudness
    
    return features

def infer_mood_from_features(energy, valence, acousticness, instrumentalness, genre_slug):
    """Infer mood and style from audio features"""
    moods = []
    instruments = []
    atmosphere = []
    
    # Base on valence
    if valence < 0.2:
        moods.extend(['melancholic', 'somber', 'introspective'])
    elif valence < 0.4:
        moods.extend(['contemplative', 'mellow', 'bittersweet'])
    elif valence < 0.6:
        moods.extend(['neutral', 'balanced', 'steady'])
    elif valence < 0.8:
        moods.extend(['uplifting', 'bright', 'positive'])
    else:
        moods.extend(['joyful', 'euphoric', 'celebratory'])
    
    # Base on energy
    if energy < 0.2:
        atmosphere.extend(['minimal', 'ambient', 'static'])
        moods.append('peaceful')
    elif energy < 0.4:
        atmosphere.extend(['gentle', 'subdued', 'restrained'])
        moods.append('calming')
    elif energy < 0.6:
        atmosphere.extend(['moderate', 'balanced', 'flowing'])
        moods.append('smooth')
    elif energy < 0.8:
        atmosphere.extend(['dynamic', 'lively', 'engaging'])
        moods.append('energetic')
    else:
        atmosphere.extend(['intense', 'powerful', 'driving'])
        moods.append('explosive')
    
    # Base on acousticness
    if acousticness > 0.7:
        instruments.extend(['acoustic guitar', 'piano', 'strings', 'natural textures'])
        atmosphere.append('organic')
    elif acousticness > 0.4:
        instruments.extend(['mixed acoustic/electric', 'layered textures'])
        atmosphere.append('hybrid')
    else:
        instruments.extend(['synthesizers', 'electronic elements', 'digital processing'])
        atmosphere.append('synthetic')
    
    # Base on instrumentalness
    if instrumentalness > 0.8:
        instruments.append('purely instrumental')
    elif instrumentalness > 0.5:
        instruments.append('minimal vocals')
        moods.append('meditative')
    else:
        instruments.append('vocal-driven')
    
    # Genre-specific adjustments
    genre_meta = GENRE_METADATA.get(genre_slug, {})
    if genre_meta:
        instruments.extend(genre_meta.get('typical_instruments', []))
        moods.extend(genre_meta.get('mood_keywords', []))
    
    return {
        'mood': moods[:3],  # Top 3
        'atmosphere': atmosphere[:2],  # Top 2  
        'instruments': instruments[:4]  # Top 4
    }

def generate_prompt_content(track_name, artist, tempo, key, mode, duration_min, audio_features, genre_slug):
    """Generate prompt lab content for a track"""
    
    # Infer characteristics from audio features
    characteristics = infer_mood_from_features(
        audio_features['energy'],
        audio_features['valence'], 
        audio_features['acousticness'],
        audio_features['instrumentalness'],
        genre_slug
    )
    
    # Get genre metadata
    genre_meta = GENRE_METADATA.get(genre_slug, {})
    reference_artists = genre_meta.get('reference_artists', ['Similar Artist'])
    
    # Primary mood and atmosphere
    primary_mood = characteristics['mood'][0] if characteristics['mood'] else 'expressive'
    primary_atmosphere = characteristics['atmosphere'][0] if characteristics['atmosphere'] else 'flowing'
    
    # Instruments
    primary_instrument = characteristics['instruments'][0] if characteristics['instruments'] else 'piano'
    
    # Duration formatting
    minutes = int(duration_min)
    seconds = int((duration_min % 1) * 60)
    duration_str = f"{minutes}:{seconds:02d}"
    
    # Energy level description
    energy_pct = round(audio_features['energy'] * 100)
    if energy_pct < 25:
        energy_desc = 'minimal'
    elif energy_pct < 50:
        energy_desc = 'subdued'
    elif energy_pct < 75:
        energy_desc = 'moderate'
    else:
        energy_desc = 'high'
    
    # Valence level description  
    valence_pct = round(audio_features['valence'] * 100)
    if valence_pct < 25:
        valence_desc = 'melancholic'
    elif valence_pct < 50:
        valence_desc = 'contemplative' 
    elif valence_pct < 75:
        valence_desc = 'balanced'
    else:
        valence_desc = 'uplifting'
    
    # Style description
    style_desc = genre_meta.get('prompt_style', 'expressive, dynamic')
    
    # Generate prompts
    general_prompt = f"Create a {duration_str} {genre_slug.replace('-', ' ')} track at {tempo} BPM in {key} {mode}. Instrumental — {primary_instrument}. {primary_mood} / {valence_desc} and {primary_atmosphere}. {style_desc.title()}. {energy_desc.title()} energy ({energy_pct}%), {valence_desc} mood ({valence_pct}%). Think {reference_artists[0]} meets {reference_artists[1] if len(reference_artists) > 1 else 'ambient textures'}."
    
    suno_prompt = f"{genre_slug.replace('-', ' ')}, {primary_mood} / {valence_desc}, {primary_atmosphere}, {primary_instrument}, {energy_desc}, {style_desc}"
    
    udio_prompt = f"A {genre_slug.replace('-', ' ')} track that feels {primary_mood} / {valence_desc} and {primary_atmosphere} with {primary_instrument} — {style_desc} in the style of {reference_artists[0]} and {reference_artists[1] if len(reference_artists) > 1 else 'ambient music'}"
    
    # JSON data
    agent_json = {
        "track_reference": {
            "title": track_name,
            "artist": artist
        },
        "generation_params": {
            "bpm": int(tempo),
            "key": f"{key} {mode}",
            "duration": duration_str,
            "energy": round(audio_features['energy'], 3),
            "valence": round(audio_features['valence'], 3),
            "acousticness": round(audio_features['acousticness'], 3),
            "instrumentalness": round(audio_features['instrumentalness'], 3)
        },
        "style": {
            "genres": [genre_slug.replace('-', ' ')] + genre_meta.get('mood_keywords', [])[:2],
            "mood": primary_mood + " / " + valence_desc,
            "atmosphere": primary_atmosphere,
            "instruments": characteristics['instruments'][:3],
            "primary_instrument": primary_instrument,
            "vocals": "None" if audio_features['instrumentalness'] > 0.8 else "Minimal"
        },
        "production": {
            "style": style_desc,
            "effects": [],
            "texture": "layered",
            "dynamics": "static" if energy_pct < 40 else "dynamic",
            "stereo": "moderate"
        },
        "reference_artists": reference_artists[:2],
        "prompt": general_prompt
    }
    
    return general_prompt, suno_prompt, udio_prompt, agent_json

def load_analysis_data(genre_slug):
    """Load analysis.json for a genre"""
    analysis_path = Path(f"~/kapiko/site/genres/{genre_slug}/analysis.json").expanduser()
    if not analysis_path.exists():
        raise FileNotFoundError(f"No analysis.json found for genre: {genre_slug}")
    
    with open(analysis_path, 'r') as f:
        return json.load(f)

def generate_genre_page(genre_slug):
    """Generate a genre index.html page"""
    
    # Map some genre slugs to the actual directory names
    genre_mapping = {
        'piano': 'piano',
        'sleep': 'sleep', 
        'chill': 'chill',
        'study': 'study',
        'classical': 'classical',
        'jazz': 'jazz',
        'acoustic': 'acoustic', 
        'electronic': 'electronic',
        'hip-hop': 'hip-hop',
        'soul': 'soul'
    }
    
    # Check if this maps to an existing directory
    actual_genre_slug = genre_mapping.get(genre_slug, genre_slug)
    genre_dir = Path(f"~/kapiko/site/genres/{actual_genre_slug}").expanduser()
    
    if not genre_dir.exists():
        print(f"Genre directory not found: {genre_dir}")
        return False
    
    # Load the template from lofi-hip-hop
    template_path = Path("~/kapiko/site/genres/lofi-hip-hop/index.html").expanduser()
    if not template_path.exists():
        print(f"Template not found: {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Load analysis data
    try:
        data = load_analysis_data(actual_genre_slug)
    except FileNotFoundError:
        print(f"Analysis data not found for: {actual_genre_slug}")
        return False
    
    # Get genre metadata
    genre_meta = GENRE_METADATA.get(genre_slug, {})
    genre_name = genre_slug.replace('-', ' ').title()
    genre_emoji = genre_meta.get('emoji', '🎵')
    genre_description = genre_meta.get('description', 'Musical genre analysis')
    
    # Replace title and metadata  
    new_content = template_content.replace("Lo-Fi Hip Hop", f"{genre_emoji} {genre_name}")
    new_content = new_content.replace("Lo-fi hip hop", genre_name.lower())
    new_content = new_content.replace("lo-fi hip hop", genre_name.lower()) 
    new_content = new_content.replace("Dusty beats and mellow grooves", genre_description)
    
    # Replace genre-specific stats if available
    if 'bpm' in data and 'median' in data['bpm']:
        median_bpm = int(data['bpm']['median'])
        new_content = re.sub(r'<div class="stat-value teal">\d+</div>', f'<div class="stat-value teal">{median_bpm}</div>', new_content, count=1)
    
    if 'energy' in data and 'mean' in data['energy']:
        avg_energy = int(data['energy']['mean'] * 100)
        new_content = re.sub(r'<div class="stat-value purple">\d+%</div>', f'<div class="stat-value purple">{avg_energy}%</div>', new_content, count=1)
    
    if 'valence' in data and 'mean' in data['valence']:
        avg_valence = int(data['valence']['mean'] * 100) 
        new_content = re.sub(r'<div class="stat-value blue">\d+%</div>', f'<div class="stat-value blue">{avg_valence}%</div>', new_content, count=1)
    
    # Replace top key
    if 'key_distribution' in data:
        top_key = max(data['key_distribution'], key=data['key_distribution'].get)
        new_content = re.sub(r'<div class="stat-value teal">[^<]+</div>', f'<div class="stat-value teal">{top_key}</div>', new_content)
    
    # Replace major/minor split
    if 'mode_distribution' in data:
        major_pct = data['mode_distribution'].get('Major', 50)
        minor_pct = data['mode_distribution'].get('Minor', 50)
        new_content = new_content.replace('55/45', f'{major_pct}/{minor_pct}')
    
    # Update JavaScript data with actual analysis data
    # This is a bit complex, so we'll keep the original data structure
    # and just update the page content for now
    
    # Write the output
    output_path = genre_dir / "index.html"
    with open(output_path, 'w') as f:
        f.write(new_content)
    
    print(f"Generated genre page: {output_path}")
    return True

def generate_song_page(track_data, genre_slug, all_data):
    """Generate a song page"""
    
    # Extract track info
    track_name = track_data['name'] 
    artist = track_data['artists']
    popularity = track_data.get('popularity', 50)
    tempo = track_data.get('tempo', 120)
    key = track_data.get('key', 'C')
    mode = track_data.get('mode', 'Major')
    
    # Create slug
    song_slug = slugify(f"{track_name} {artist}")
    
    # Skip if already exists
    song_dir = Path(f"~/kapiko/site/songs/{song_slug}").expanduser()
    if song_dir.exists():
        return False, song_slug
    
    # Estimate duration (from genre average or default)
    duration_min = all_data.get('duration', {}).get('mean', 3.5)  # Default 3.5 min
    
    # Get audio features
    audio_features = generate_audio_features_from_data(track_name, artist, all_data, all_data.get('tracks', []))
    
    # Generate prompts
    general_prompt, suno_prompt, udio_prompt, agent_json = generate_prompt_content(
        track_name, artist, tempo, key, mode, duration_min, audio_features, genre_slug
    )
    
    # Load the song template
    template_path = Path("~/kapiko/site/songs/experience-ludovico-einaudi/index.html").expanduser()
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Create song directory
    song_dir.mkdir(parents=True, exist_ok=True)
    
    # Replace template content
    new_content = template_content
    
    # Update title and metadata
    new_content = new_content.replace("Experience — Analysis + Prompt Template - kapiko", f"{track_name} — Analysis + Prompt Template - kapiko")
    new_content = new_content.replace("Experience by Ludovico Einaudi", f"{track_name} by {artist}")
    
    # Update breadcrumb
    genre_display = genre_slug.replace('-', ' ').title()
    new_content = new_content.replace('<div class="breadcrumb"><a href="/genres/ambient/">Ambient</a> → Song Analysis</div>',
                                    f'<div class="breadcrumb"><a href="/genres/{genre_slug}/">{genre_display}</a> → Song Analysis</div>')
    
    # Update header info
    new_content = new_content.replace('<div class="song-title">Experience</div>', f'<div class="song-title">{track_name}</div>')
    new_content = new_content.replace('<div class="song-artist">Ludovico Einaudi, Daniel Hope, I Virtuosi Italiani</div>', f'<div class="song-artist">{artist}</div>')
    new_content = new_content.replace('<div class=\'song-album\'>In A Time Lapse</div>', '<div class="song-album">Spotify Dataset</div>')
    
    # Update stat cards
    new_content = new_content.replace('<div class="stat-val">92</div><div class="stat-label">BPM</div>', f'<div class="stat-val">{int(tempo)}</div><div class="stat-label">BPM</div>')
    new_content = new_content.replace('<div class="stat-val">D Major</div><div class="stat-label">Key</div>', f'<div class="stat-val">{key} {mode}</div><div class="stat-label">Key</div>')
    new_content = new_content.replace('<div class="stat-val">44.9%</div><div class="stat-label">Energy</div>', f'<div class="stat-val">{round(audio_features["energy"]*100, 1)}%</div><div class="stat-label">Energy</div>')
    
    # Format duration
    minutes = int(duration_min)
    seconds = int((duration_min % 1) * 60)
    duration_str = f"{minutes}:{seconds:02d}"
    new_content = new_content.replace('<div class="stat-val">5:15</div><div class="stat-label">Duration</div>', f'<div class="stat-val">{duration_str}</div><div class="stat-label">Duration</div>')
    new_content = new_content.replace('<div class="stat-val">79</div><div class="stat-label">Popularity</div>', f'<div class="stat-val">{popularity}</div><div class="stat-label">Popularity</div>')
    
    # Update prompt lab content
    new_content = new_content.replace('Create a 5:15 neo-classical track at 92 BPM in D Major. Instrumental — harp, string pads. Meditative / melancholic and expansive. Clean digital synthesis, with reverb tail. Layered texture, static dynamics, moderate stereo field. Subdued energy (45%), melancholic mood (4%). Think Ludovico Einaudi meets Olafur Arnalds.', 
                                    general_prompt)
    
    new_content = new_content.replace('neo-classical, ambient, meditative / melancholic, expansive, harp, string pads, subdued, clean digital synthesis, reverb tail',
                                    suno_prompt)
    
    new_content = new_content.replace('A neo-classical track that feels meditative / melancholic and expansive with harp, string pads — clean digital synthesis using reverb tail in the style of Ludovico Einaudi and Olafur Arnalds',
                                    udio_prompt)
    
    # Update agent JSON (this is complex - let's replace the whole block)
    json_str = json.dumps(agent_json, indent=2)
    # Find the JSON block and replace it
    json_start = new_content.find('{\n  "track_reference"')
    json_end = new_content.find('}</pre>', json_start) + 7  # Include </pre>
    if json_start > -1 and json_end > json_start:
        before = new_content[:json_start]
        after = new_content[json_end:]
        new_content = before + json_str + '</pre>' + after
    
    # Update feature values - this requires careful replacement
    features_to_update = [
        ('Energy', audio_features['energy']),
        ('Danceability', audio_features['danceability']),  
        ('Valence', audio_features['valence']),
        ('Acousticness', audio_features['acousticness']),
        ('Instrumentalness', audio_features['instrumentalness']),
        ('Speechiness', audio_features['speechiness']),
        ('Liveness', audio_features['liveness']),
    ]
    
    for feature_name, value in features_to_update:
        pct_value = round(value * 100, 1)
        # Update the feature bars
        pattern = f'<div class="feature-label">{feature_name}</div><div class="feature-val">[^<]+</div><div class="feature-track"><div class="feature-fill" style="width:[^"]+"></div></div>'
        replacement = f'<div class="feature-label">{feature_name}</div><div class="feature-val">{pct_value}%</div><div class="feature-track"><div class="feature-fill" style="width:{pct_value}%"></div></div>'
        new_content = re.sub(pattern, replacement, new_content)
    
    # Update radar chart data
    radar_data = f"[{audio_features['energy']:.3f}, {audio_features['danceability']:.3f}, {audio_features['valence']:.3f}, {audio_features['acousticness']:.3f}, {audio_features['instrumentalness']:.3f}, {audio_features['speechiness']:.3f}]"
    new_content = re.sub(r'data: \[[^]]+\]', f'data: {radar_data}', new_content)
    
    # Remove YouTube embed (we don't have videos for generated tracks)
    # Find and remove the YouTube section
    youtube_start = new_content.find('<div class="detail-section yt-section">')
    if youtube_start > -1:
        youtube_end = new_content.find('</div>', youtube_start)
        if youtube_end > -1:
            youtube_end = new_content.find('</div>', youtube_end + 1) + 6  # Include the closing div
            new_content = new_content[:youtube_start] + new_content[youtube_end:]
    
    # Update footer link
    new_content = new_content.replace('<a href="/genres/ambient/">← Back to Ambient Genre</a>',
                                    f'<a href="/genres/{genre_slug}/">← Back to {genre_display} Genre</a>')
    
    # Write the output
    output_path = song_dir / "index.html"
    with open(output_path, 'w') as f:
        f.write(new_content)
    
    return True, song_slug

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_pages.py <command> [args]")
        print("Commands:")
        print("  genres                    - Generate all 10 genre pages")
        print("  songs                     - Generate all song pages") 
        print("  songs <start> <count>     - Generate a slice of song pages")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "genres":
        # Generate all 10 genre pages
        genres = ['piano', 'sleep', 'chill', 'study', 'classical', 'jazz', 'acoustic', 'electronic', 'hip-hop', 'soul']
        generated = 0
        
        for genre in genres:
            try:
                if generate_genre_page(genre):
                    generated += 1
                    print(f"✓ Generated {genre} genre page")
                else:
                    print(f"✗ Failed to generate {genre} genre page")
            except Exception as e:
                print(f"✗ Error generating {genre}: {e}")
        
        print(f"\nGenerated {generated}/{len(genres)} genre pages")
        
    elif command == "songs":
        start_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        max_count = int(sys.argv[3]) if len(sys.argv) > 3 else None
        
        # Get all genre directories to find tracks
        genre_dirs = [d for d in Path("~/kapiko/site/genres").expanduser().iterdir() if d.is_dir()]
        
        total_generated = 0
        total_skipped = 0
        processed = 0
        
        for genre_dir in genre_dirs:
            genre_slug = genre_dir.name
            analysis_path = genre_dir / "analysis.json"
            
            if not analysis_path.exists():
                continue
                
            # Load tracks
            with open(analysis_path, 'r') as f:
                data = json.load(f)
            
            tracks = data.get('tracks', [])
            
            for track in tracks:
                if processed < start_idx:
                    processed += 1
                    continue
                    
                if max_count and (total_generated + total_skipped) >= max_count:
                    break
                
                try:
                    created, slug = generate_song_page(track, genre_slug, data)
                    if created:
                        total_generated += 1
                        print(f"✓ Generated: {slug}")
                    else:
                        total_skipped += 1
                        if total_generated < 10:  # Only show first few skips
                            print(f"- Skipped (exists): {slug}")
                        
                    processed += 1
                    
                except Exception as e:
                    print(f"✗ Error generating song {track['name']}: {e}")
                    processed += 1
                
                if max_count and (total_generated + total_skipped) >= max_count:
                    break
            
            if max_count and (total_generated + total_skipped) >= max_count:
                break
        
        print(f"\nProcessed {processed} tracks:")
        print(f"  Generated: {total_generated} new song pages")  
        print(f"  Skipped: {total_skipped} existing pages")
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()