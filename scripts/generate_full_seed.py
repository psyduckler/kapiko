#!/usr/bin/env python3
"""
Generate complete D1 seed SQL file for kapiko music API.
Processes all 118 genres and their tracks from analysis.json files.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def escape_sql_string(value: str) -> str:
    """Escape single quotes for SQL string literals."""
    if value is None:
        return 'NULL'
    # Escape single quotes by doubling them
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def convert_key_to_int(key_input) -> Optional[int]:
    """Convert key string (C, C#, D, etc.) or int to integer (0-11)."""
    if key_input is None:
        return None
    
    # If it's already an integer, just return it
    if isinstance(key_input, int):
        return key_input if 0 <= key_input <= 11 else None
    
    # If it's a string, convert it
    if isinstance(key_input, str):
        if not key_input or key_input.lower() in ['null', 'none', '']:
            return None
            
        key_map = {
            'C': 0, 'C#': 1, 'DB': 1, 'D': 2, 'D#': 3, 'EB': 3,
            'E': 4, 'F': 5, 'F#': 6, 'GB': 6, 'G': 7, 'G#': 8,
            'AB': 8, 'A': 9, 'A#': 10, 'BB': 10, 'B': 11
        }
        
        key_upper = key_input.upper()
        return key_map.get(key_upper)
    
    return None


def convert_mode_to_int(mode_input) -> Optional[int]:
    """Convert mode string (Major/Minor) or int to integer (1/0)."""
    if mode_input is None:
        return None
    
    # If it's already an integer, return it
    if isinstance(mode_input, int):
        return mode_input if mode_input in [0, 1] else None
    
    # If it's a string, convert it
    if isinstance(mode_input, str):
        if not mode_input or mode_input.lower() in ['null', 'none', '']:
            return None
        
        mode_lower = mode_input.lower()
        if mode_lower == 'major':
            return 1
        elif mode_lower == 'minor':
            return 0
    
    return None


def slug_to_display_name(slug: str) -> str:
    """Convert genre slug to display name."""
    # Special cases
    special_cases = {
        'r-n-b': 'R&B',
        'k-pop': 'K-Pop',
        'j-pop': 'J-Pop',
        'uk-garage': 'UK Garage',
        'drum-and-bass': 'Drum and Bass',
        'hip-hop': 'Hip Hop',
        'alt-rock': 'Alternative Rock',
        'hard-rock': 'Hard Rock',
        'soft-rock': 'Soft Rock',
        'punk-rock': 'Punk Rock',
        'indie-pop': 'Indie Pop',
        'synth-pop': 'Synth Pop',
        'electro-pop': 'Electro Pop',
        'power-pop': 'Power Pop',
        'dance-pop': 'Dance Pop',
        'new-wave': 'New Wave',
        'post-rock': 'Post Rock',
        'black-metal': 'Black Metal',
        'death-metal': 'Death Metal',
        'heavy-metal': 'Heavy Metal',
        'speed-metal': 'Speed Metal',
        'folk-rock': 'Folk Rock',
        'acid-jazz': 'Acid Jazz',
        'smooth-jazz': 'Smooth Jazz',
        'jazz-piano': 'Jazz Piano',
        'lofi-hip-hop': 'Lo-Fi Hip Hop',
        'neo-classical': 'Neo Classical',
        'new-age': 'New Age',
        'trip-hop': 'Trip Hop'
    }
    
    if slug in special_cases:
        return special_cases[slug]
    
    # Default: capitalize each word, replace hyphens with spaces
    return slug.replace('-', ' ').title()


def generate_genre_description(genre_data: Dict) -> str:
    """Generate a brief description based on audio characteristics."""
    name = slug_to_display_name(genre_data['genre'])
    
    # Extract averages with fallbacks
    energy = genre_data.get('energy', {}).get('mean', 0.5)
    valence = genre_data.get('valence', {}).get('mean', 0.5)
    tempo = genre_data.get('bpm', {}).get('mean', 120)
    acousticness = genre_data.get('acousticness', {}).get('mean', 0.5)
    danceability = genre_data.get('danceability', {}).get('mean', 0.5)
    instrumentalness = genre_data.get('instrumentalness', {}).get('mean', 0.5)
    
    # Generate description based on characteristics
    descriptors = []
    
    # Energy level
    if energy > 0.7:
        descriptors.append("high-energy")
    elif energy < 0.3:
        descriptors.append("relaxing")
    else:
        descriptors.append("moderate-energy")
    
    # Tempo
    if tempo > 140:
        descriptors.append("fast-paced")
    elif tempo < 80:
        descriptors.append("slow-tempo")
    
    # Mood
    if valence > 0.7:
        descriptors.append("uplifting")
    elif valence < 0.3:
        descriptors.append("melancholic")
    
    # Sound characteristics
    if acousticness > 0.6:
        descriptors.append("acoustic")
    elif acousticness < 0.2:
        descriptors.append("electronic")
    
    if danceability > 0.7:
        descriptors.append("danceable")
    
    if instrumentalness > 0.6:
        descriptors.append("instrumental")
    
    # Combine descriptors
    if descriptors:
        desc = f"{name} music featuring {', '.join(descriptors[:3])} sounds"
    else:
        desc = f"{name} music with diverse sonic characteristics"
    
    return desc[:200]  # Limit length


def load_genre_data(genres_dir: Path) -> List[Dict]:
    """Load all genre data from analysis.json files."""
    genres = []
    
    for genre_path in sorted(genres_dir.iterdir()):
        if genre_path.is_dir():
            analysis_file = genre_path / 'analysis.json'
            if analysis_file.exists():
                try:
                    with open(analysis_file, 'r') as f:
                        data = json.load(f)
                        data['slug'] = genre_path.name
                        genres.append(data)
                except Exception as e:
                    print(f"Error loading {analysis_file}: {e}")
    
    return genres


def load_top100_tracks(file_path: Path) -> List[Dict]:
    """Load tracks from a top-100 JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []


def get_special_genre_tracks(genre_slug: str) -> List[Dict]:
    """Load tracks for special genres that need top-100 files."""
    file_mapping = {
        'ambient': Path('/Users/bjh/kapiko/data/ambient-top100.json'),
        'focus': Path('/Users/bjh/.openclaw/workspace/kapiko-genres/focus/focus-top100.json'),
        'jazz-piano': Path('/Users/bjh/.openclaw/workspace/kapiko-genres/jazz-piano/jazz-piano-top100.json'),
        'lofi-hip-hop': Path('/Users/bjh/.openclaw/workspace/kapiko-genres/lofi-hip-hop/lofi-top100.json'),
        'neo-classical': Path('/Users/bjh/.openclaw/workspace/kapiko-genres/neo-classical/neo-classical-top100.json')
    }
    
    file_path = file_mapping.get(genre_slug)
    if file_path and file_path.exists():
        return load_top100_tracks(file_path)
    return []


def generate_seed_sql():
    """Generate the complete seed SQL file."""
    genres_dir = Path('/Users/bjh/kapiko/site/genres')
    output_path = Path('/Users/bjh/kapiko/api/src/db/seed_full.sql')
    
    print("Loading genre data...")
    all_genres = load_genre_data(genres_dir)
    print(f"Found {len(all_genres)} genres")
    
    # Special genres that need top-100 files
    special_genres = {'ambient', 'focus', 'jazz-piano', 'lofi-hip-hop', 'neo-classical'}
    
    # Start building SQL
    sql_lines = [
        "-- D1 Seed Data for Kapiko Music API",
        "-- Generated from all 118 genres and their tracks",
        "",
        "-- Clean slate",
        "DELETE FROM tracks;",
        "DELETE FROM genres;",
        "",
        "-- Genre data",
    ]
    
    genre_count = 0
    track_count = 0
    
    # Process each genre
    for genre_data in all_genres:
        genre_slug = genre_data['slug']
        genre_name = slug_to_display_name(genre_slug)
        description = generate_genre_description(genre_data)
        
        # Get averages
        track_count_val = genre_data.get('track_count', 0)
        avg_tempo = genre_data.get('bpm', {}).get('mean')
        avg_energy = genre_data.get('energy', {}).get('mean')
        avg_valence = genre_data.get('valence', {}).get('mean')
        avg_loudness = genre_data.get('loudness', {}).get('mean')
        avg_acousticness = genre_data.get('acousticness', {}).get('mean')
        avg_danceability = genre_data.get('danceability', {}).get('mean')
        avg_instrumentalness = genre_data.get('instrumentalness', {}).get('mean')
        avg_speechiness = genre_data.get('speechiness', {}).get('mean')
        
        # Format values
        def fmt_val(val):
            return f"{val:.4f}" if val is not None else "NULL"
        
        genre_sql = f"""INSERT OR REPLACE INTO genres (
  id, name, description, track_count, avg_tempo, avg_energy, avg_valence,
  avg_loudness, avg_acousticness, avg_danceability, avg_instrumentalness, avg_speechiness
) VALUES (
  {escape_sql_string(genre_slug)}, {escape_sql_string(genre_name)}, {escape_sql_string(description)},
  {track_count_val}, {fmt_val(avg_tempo)}, {fmt_val(avg_energy)}, {fmt_val(avg_valence)},
  {fmt_val(avg_loudness)}, {fmt_val(avg_acousticness)}, {fmt_val(avg_danceability)},
  {fmt_val(avg_instrumentalness)}, {fmt_val(avg_speechiness)}
);"""
        
        sql_lines.append(genre_sql)
        genre_count += 1
        
        # Process tracks for this genre
        tracks = []
        
        if genre_slug in special_genres:
            # Use top-100 file
            tracks = get_special_genre_tracks(genre_slug)
            print(f"Loaded {len(tracks)} tracks for {genre_slug} from top-100 file")
        else:
            # Use analysis.json tracks
            tracks = genre_data.get('tracks', [])
            print(f"Loaded {len(tracks)} tracks for {genre_slug} from analysis.json")
        
        # Process each track
        for track in tracks:
            track_id = track.get('track_id') or track.get('slug')
            if not track_id:
                # Generate ID from name if no slug available
                track_id = re.sub(r'[^a-zA-Z0-9]', '-', track.get('name', '')).lower()
                track_id = re.sub(r'-+', '-', track_id).strip('-')
            
            name = track.get('name', '')
            artists = track.get('artists', '')
            album = track.get('album', '')
            popularity = track.get('popularity', 0)
            duration_ms = track.get('duration_ms', 0)
            tempo = track.get('tempo')
            energy = track.get('energy')
            valence = track.get('valence')
            loudness = track.get('loudness')
            acousticness = track.get('acousticness')
            danceability = track.get('danceability')
            instrumentalness = track.get('instrumentalness')
            speechiness = track.get('speechiness')
            liveness = track.get('liveness')
            
            # Handle key/mode conversion
            key = convert_key_to_int(track.get('key'))
            mode = convert_mode_to_int(track.get('mode'))
            time_signature = track.get('time_signature', 4)
            
            def fmt_val_or_null(val):
                return f"{val:.4f}" if val is not None else "NULL"
            
            def fmt_int_or_null(val):
                return str(int(val)) if val is not None else "NULL"
            
            track_sql = f"""INSERT OR IGNORE INTO tracks (
  id, name, artists, album, genre_id, popularity, duration_ms, tempo, energy, valence,
  loudness, acousticness, danceability, instrumentalness, speechiness, liveness,
  key, mode, time_signature, source
) VALUES (
  {escape_sql_string(track_id)}, {escape_sql_string(name)}, {escape_sql_string(artists)},
  {escape_sql_string(album)}, {escape_sql_string(genre_slug)}, {popularity}, {duration_ms},
  {fmt_val_or_null(tempo)}, {fmt_val_or_null(energy)}, {fmt_val_or_null(valence)},
  {fmt_val_or_null(loudness)}, {fmt_val_or_null(acousticness)}, {fmt_val_or_null(danceability)},
  {fmt_val_or_null(instrumentalness)}, {fmt_val_or_null(speechiness)}, {fmt_val_or_null(liveness)},
  {fmt_int_or_null(key)}, {fmt_int_or_null(mode)}, {fmt_int_or_null(time_signature)}, 'spotify'
);"""
            
            sql_lines.append(track_sql)
            track_count += 1
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write SQL file
    print(f"\nWriting SQL to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"\n✅ Generated seed file:")
    print(f"   📁 {output_path}")
    print(f"   🎵 {genre_count} genres")
    print(f"   🎵 {track_count} tracks")
    print(f"   📏 {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    return output_path


def validate_sql_file(file_path: Path):
    """Basic validation of the generated SQL file."""
    print("\n🔍 Validating SQL file...")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Basic syntax checks
        genre_inserts = content.count('INSERT OR REPLACE INTO genres')
        track_inserts = content.count('INSERT OR IGNORE INTO tracks')
        
        print(f"   ✅ Found {genre_inserts} genre INSERT statements")
        print(f"   ✅ Found {track_inserts} track INSERT statements")
        
        # Check for basic SQL issues
        if "INSERT OR REPLACE INTO genres" not in content:
            print("   ❌ No genre INSERT statements found")
            return False
            
        if "INSERT OR IGNORE INTO tracks" not in content:
            print("   ❌ No track INSERT statements found") 
            return False
        
        if "DELETE FROM tracks;" not in content:
            print("   ❌ Missing DELETE FROM tracks;")
            return False
            
        if "DELETE FROM genres;" not in content:
            print("   ❌ Missing DELETE FROM genres;")
            return False
        
        # Check for unescaped quotes (basic check)
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if "INSERT" in line and "VALUES" in line:
                # Count single quotes - should be even
                single_quotes = line.count("'")
                if single_quotes % 2 != 0:
                    print(f"   ⚠️  Possible unescaped quote on line {i}")
        
        print("   ✅ Basic SQL validation passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
        return False


if __name__ == "__main__":
    print("🎵 Generating D1 seed SQL file for kapiko music API")
    print("=" * 60)
    
    output_file = generate_seed_sql()
    validate_sql_file(output_file)
    
    print("\n🎉 Complete! The seed file is ready to use.")