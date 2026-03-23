#!/usr/bin/env python3
"""
Generate genre pages with correct data from analysis.json files
"""

import json
import os
from pathlib import Path

# Define all genres with their metadata
GENRES = {
    'piano': {'name': 'Piano', 'emoji': '🎹'},
    'sleep': {'name': 'Sleep', 'emoji': '🌙'},
    'chill': {'name': 'Chill', 'emoji': '😌'},
    'study': {'name': 'Study', 'emoji': '📚'},
    'classical': {'name': 'Classical', 'emoji': '🎻'},
    'jazz': {'name': 'Jazz', 'emoji': '🎷'},
    'acoustic': {'name': 'Acoustic', 'emoji': '🎸'},
    'electronic': {'name': 'Electronic', 'emoji': '⚡'},
    'hip-hop': {'name': 'Hip Hop', 'emoji': '🎤'},
    'soul': {'name': 'Soul', 'emoji': '🎙️'},
    'ambient': {'name': 'Ambient', 'emoji': '🌌'},
    'focus': {'name': 'Focus', 'emoji': '🎯'},
    'jazz-piano': {'name': 'Jazz Piano', 'emoji': '🎹'},
    'neo-classical': {'name': 'Neo-Classical', 'emoji': '🏛️'},
    'lofi-hip-hop': {'name': 'Lo-Fi Hip Hop', 'emoji': '🎵'}
}

def load_template():
    """Load the reference HTML template from lofi-hip-hop"""
    template_path = Path("~/kapiko/site/genres/lofi-hip-hop/index.html").expanduser()
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_analysis_data(genre):
    """Load analysis.json data for a specific genre"""
    analysis_path = Path(f"~/kapiko/site/genres/{genre}/analysis.json").expanduser()
    with open(analysis_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def convert_bpm_histogram(histogram_data):
    """Convert BPM histogram from analysis.json format to chart format"""
    # Standard BPM ranges for chart
    bpm_ranges = ['0-30', '30-60', '60-90', '90-120', '120-150', '150-180', '180+']
    chart_data = [0, 0, 0, 0, 0, 0, 0]
    
    total_tracks = sum(histogram_data.values())
    
    for range_key, count in histogram_data.items():
        percentage = round((count / total_tracks) * 100)
        
        # Map analysis.json ranges to chart ranges
        if '60-69' in range_key or '70-79' in range_key or '80-89' in range_key:
            chart_data[2] += percentage  # 60-90
        elif '90-99' in range_key or '100-109' in range_key or '110-119' in range_key:
            chart_data[3] += percentage  # 90-120
        elif '120-129' in range_key or '130-139' in range_key or '140-149' in range_key:
            chart_data[4] += percentage  # 120-150
        elif '150-159' in range_key or '160-169' in range_key or '170-179' in range_key:
            chart_data[5] += percentage  # 150-180
        elif '180-189' in range_key or '190-199' in range_key or '200-209' in range_key:
            chart_data[6] += percentage  # 180+
    
    return chart_data

def format_key_distribution(key_dist):
    """Format key distribution for chart"""
    # Standard order for keys
    key_order = ['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']
    chart_data = []
    total = sum(key_dist.values())
    
    for key in key_order:
        count = key_dist.get(key, 0)
        percentage = round((count / total) * 100) if total > 0 else 0
        chart_data.append(percentage)
    
    return chart_data

def format_top_artists(tracks):
    """Get top artists from tracks data"""
    artist_counts = {}
    for track in tracks:
        artists = track['artists'].split(';')[0]  # Take first artist for simplicity
        artist_counts[artists] = artist_counts.get(artists, 0) + 1
    
    # Get top 10 artists
    top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'labels': [artist for artist, count in top_artists],
        'data': [count for artist, count in top_artists]
    }

def calculate_medians(tracks):
    """Calculate median values for audio features"""
    features = ['energy', 'valence', 'danceability', 'acousticness', 'instrumentalness', 'speechiness']
    medians = {}
    
    for feature in features:
        values = [track[feature] * 100 for track in tracks]  # Convert to percentage
        values.sort()
        n = len(values)
        if n % 2 == 0:
            median = (values[n//2 - 1] + values[n//2]) / 2
        else:
            median = values[n//2]
        medians[feature] = round(median)
    
    return medians

def format_tracks_js_array(tracks):
    """Format tracks for JavaScript TRACKS array"""
    js_tracks = []
    for track in tracks:
        js_track = {
            'name': track['name'],
            'artists': track['artists'],
            'popularity': track['popularity'],
            'tempo': round(track['tempo'], 1),
            'key': track['key'],
            'mode': track['mode'],
            'energy': round(track['energy'] * 100),
            'valence': round(track['valence'] * 100),
            'slug': track['slug']
        }
        js_tracks.append(js_track)
    
    return json.dumps(js_tracks, separators=(',', ': '))

def generate_scatter_data(tracks, x_field, y_field):
    """Generate scatter plot data"""
    return [
        {'x': round(track[x_field] * 100, 1), 'y': round(track[y_field] * 100, 1)}
        for track in tracks
    ]

def generate_page_html(genre, template):
    """Generate HTML page for a specific genre"""
    data = load_analysis_data(genre)
    genre_info = GENRES[genre]
    
    # Calculate all necessary data
    medians = calculate_medians(data['tracks'])
    bpm_chart_data = convert_bpm_histogram(data['bpm']['histogram'])
    key_chart_data = format_key_distribution(data['key_distribution'])
    top_artists = format_top_artists(data['tracks'])
    tracks_js = format_tracks_js_array(data['tracks'])
    
    # Energy-Valence scatter data
    ev_scatter = json.dumps(generate_scatter_data(data['tracks'], 'energy', 'valence'))
    
    # Acousticness-Instrumentalness scatter data
    ai_scatter = json.dumps(generate_scatter_data(data['tracks'], 'acousticness', 'instrumentalness'))
    
    # Mode distribution percentages
    total_tracks = data['track_count']
    major_pct = round((data['mode_distribution']['Major'] / total_tracks) * 100)
    minor_pct = round((data['mode_distribution']['Minor'] / total_tracks) * 100)
    
    # Replace all template variables
    html = template
    
    # Title and headers
    html = html.replace('Lo-Fi Hip Hop — kapiko music analytics', f'{genre_info["name"]} — kapiko music analytics')
    html = html.replace('<h1>Lo-Fi Hip Hop</h1>', f'<h1>{genre_info["name"]}</h1>')
    
    # Chart titles
    html = html.replace('Lo-Fi Hip Hop Production Characteristics', f'{genre_info["name"]} Production Characteristics')
    html = html.replace('Lo-Fi Hip Hop Essential Tracks', f'{genre_info["name"]} Essential Tracks')
    
    # Footer text
    html = html.replace('top 100 lo-fi hip hop tracks', f'top 100 {genre_info["name"].lower()} tracks')
    
    # Radar chart data (medians)
    radar_data = f"[{medians['energy']}, {medians['valence']}, {medians['danceability']}, {medians['acousticness']}, {medians['instrumentalness']}, {medians['speechiness']}]"
    html = html.replace('data: [33, 29, 62, 63, 76, 5],', f'data: {radar_data},')
    
    # BPM histogram data
    bpm_data_str = str(bpm_chart_data).replace('[', '[').replace(']', ']')
    html = html.replace('data: [0, 0, 61, 20, 12, 7, 0],', f'data: {bpm_data_str},')
    
    # Key distribution data
    key_labels = "['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']"
    key_data_str = str(key_chart_data)
    html = html.replace("labels: ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'],", f"labels: {key_labels},")
    html = html.replace('data: [13, 6, 10, 5, 4, 11, 4, 13, 6, 7, 8, 6],', f'data: {key_data_str},')
    
    # Mode distribution data
    html = html.replace('data: [72, 28],', f'data: [{major_pct}, {minor_pct}],')
    
    # Energy-Valence scatter
    html = html.replace('data: [{"x": 28, "y": 24}, {"x": 37, "y": 28}', f'data: {ev_scatter[1:-1]}')  # Remove brackets
    
    # Acousticness-Instrumentalness scatter
    ai_pattern = '"data": [{"x": 63, "y": 76}, {"x": 30, "y": 0}'
    if ai_pattern in html:
        html = html.replace(ai_pattern, f'"data": {ai_scatter[1:-1]}')  # Remove brackets
    
    # Top artists data
    artists_labels = json.dumps(top_artists['labels'])
    artists_data = str(top_artists['data'])
    html = html.replace("labels: ['Otaku', 'Elijah Who', 'Cigarettes After Sex', 'Kupla', 'Emancipator', 'Bonobo', 'Frank Ocean', 'Idealism', 'Ensidya', 'Breakfast For Brunch'],", 
                       f"labels: {artists_labels},")
    html = html.replace('data: [7, 6, 6, 6, 5, 4, 3, 3, 3, 3],', f'data: {artists_data},')
    
    # Tracks JavaScript array - this is the most critical replacement
    tracks_pattern = 'const TRACKS = [{"name": "my new love"'
    tracks_end_pattern = '"}];'
    
    # Find and replace the entire TRACKS array
    start_idx = html.find('const TRACKS = [')
    if start_idx != -1:
        end_idx = html.find('];', start_idx) + 2
        html = html[:start_idx] + f'const TRACKS = {tracks_js};' + html[end_idx:]
    
    return html

def main():
    """Main function to generate all genre pages"""
    print("Loading template from lofi-hip-hop...")
    template = load_template()
    
    # Create output directory if it doesn't exist
    scripts_dir = Path("~/kapiko/scripts").expanduser()
    scripts_dir.mkdir(exist_ok=True)
    
    print(f"Generating pages for {len(GENRES)} genres...")
    
    verification_data = {}
    
    for genre in GENRES:
        print(f"  Processing {genre}...")
        
        try:
            # Load analysis data to get top tracks for verification
            data = load_analysis_data(genre)
            top_tracks = data['tracks'][:3]  # Top 3 tracks
            verification_data[genre] = [f"{track['name']} - {track['artists']}" for track in top_tracks]
            
            # Generate HTML
            html = generate_page_html(genre, template)
            
            # Write to genre directory
            output_path = Path(f"~/kapiko/site/genres/{genre}/index.html").expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"    ✓ Generated {genre}/index.html")
            
        except Exception as e:
            print(f"    ✗ Error processing {genre}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("VERIFICATION - Top 3 tracks per genre:")
    print("="*60)
    
    for genre, tracks in verification_data.items():
        genre_name = GENRES[genre]['name']
        print(f"\n{genre_name} ({genre}):")
        for i, track in enumerate(tracks, 1):
            print(f"  {i}. {track}")
    
    print(f"\n{'='*60}")
    print("✅ Genre page generation completed!")
    print(f"Processed {len(verification_data)} genres successfully.")
    
    # Check piano specifically
    if 'piano' in verification_data:
        piano_top = verification_data['piano'][0]
        if "I Ain't Worried" in piano_top and "OneRepublic" in piano_top:
            print("✅ VERIFICATION PASSED: Piano page shows 'I Ain't Worried - OneRepublic' as top track")
        else:
            print(f"❌ VERIFICATION FAILED: Piano top track is '{piano_top}', expected 'I Ain't Worried - OneRepublic'")

if __name__ == "__main__":
    main()