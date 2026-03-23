#!/usr/bin/env python3
"""
Fix all kapiko song pages (1307 pages) with the following changes:
1. Fix the intro copy - standardize prompt lab intro
2. Fix broken YouTube embed HTML - add missing closing tags
3. Add JSON-LD structured data for SEO
"""

import os
import re
import json
from pathlib import Path

def extract_song_info(html_content):
    """Extract song title, artist, and slug from HTML content using regex."""
    
    # Extract title from <title> tag
    title_match = re.search(r'<title>([^<]+)</title>', html_content)
    if title_match:
        # Format: "Song Name — Analysis + Prompt Template - kapiko"
        title_text = title_match.group(1)
        song_title = title_text.split(' — ')[0] if ' — ' in title_text else title_text
    else:
        song_title = "Unknown"
    
    # Extract artist from .song-artist element
    artist_match = re.search(r'<div class="song-artist">([^<]+)</div>', html_content)
    if artist_match:
        artist_name = artist_match.group(1).strip()
    else:
        # Fallback: try to extract from breadcrumb or title
        artist_name = "Unknown Artist"
    
    return song_title, artist_name

def create_json_ld(song_title, artist_name, slug):
    """Create JSON-LD structured data for SEO."""
    json_ld = {
        "@context": "https://schema.org",
        "@type": "MusicRecording",
        "name": song_title,
        "byArtist": {"@type": "MusicGroup", "name": artist_name},
        "url": f"https://kapiko.ai/songs/{slug}/",
        "publisher": {"@type": "Organization", "name": "kapiko", "url": "https://kapiko.ai"}
    }
    return json.dumps(json_ld, indent=2)

def fix_song_page(file_path):
    """Fix a single song page HTML file."""
    print(f"Processing: {file_path}")
    
    # Get slug from directory name
    slug = Path(file_path).parent.name
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # 1. Fix the intro copy
    # Find and replace the prompt lab intro
    old_intro_pattern = r'<h3>🧪 Recreate This Track</h3>\s*<p>Use these prompt ingredients.*?</p>'
    new_intro = '''<h3>🧪 Looking to recreate this song?</h3>
      <p>Use our data-driven prompts with <strong>Suno</strong>, <strong>Udio</strong>, or any AI music generation service. Grab the structured JSON for programmatic access.</p>'''
    
    if re.search(old_intro_pattern, content, re.DOTALL):
        content = re.sub(old_intro_pattern, new_intro, content, flags=re.DOTALL)
        changes_made.append("Updated prompt lab intro")
    
    # 2. Fix broken YouTube embed HTML
    # Pattern to match broken YouTube embeds
    broken_youtube_pattern = r'(<div class="detail-section yt-section">\s*<h3>Listen</h3>\s*<div class="yt-embed">\s*<iframe src="https://www\.youtube\.com/embed/[^"]*"[^>]*></iframe>)\s*(<!-- .*? Prompt Lab)'
    
    def fix_youtube_embed(match):
        iframe_section = match.group(1)
        comment_section = match.group(2)
        # Add the missing closing divs
        return iframe_section + '\n          </div>\n        </div>\n\n  ' + comment_section
    
    if re.search(broken_youtube_pattern, content, re.DOTALL):
        content = re.sub(broken_youtube_pattern, fix_youtube_embed, content, flags=re.DOTALL)
        changes_made.append("Fixed YouTube embed HTML")
    
    # 3. Add JSON-LD structured data
    # Check if JSON-LD already exists
    if 'application/ld+json' not in content:
        # Extract song info
        song_title, artist_name = extract_song_info(content)
        
        # Create JSON-LD
        json_ld_content = create_json_ld(song_title, artist_name, slug)
        json_ld_script = f'  <script type="application/ld+json">\n{json_ld_content}\n  </script>'
        
        # Insert JSON-LD in the <head> section, right before </head>
        # Use string replacement instead of regex to avoid escape issues
        head_close_index = content.rfind('</head>')
        if head_close_index != -1:
            content = content[:head_close_index] + json_ld_script + '\n' + content[head_close_index:]
        changes_made.append("Added JSON-LD structured data")
    
    # Write the file back if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Changes made: {', '.join(changes_made)}")
        return True
    else:
        print(f"  ⏭️  No changes needed")
        return False

def main():
    """Process all song pages."""
    songs_dir = Path("/Users/bjh/kapiko/site/songs")
    
    if not songs_dir.exists():
        print(f"Error: Songs directory not found at {songs_dir}")
        return
    
    # Find all index.html files
    html_files = list(songs_dir.glob("*/index.html"))
    print(f"Found {len(html_files)} song pages to process")
    
    if len(html_files) == 0:
        print("No HTML files found to process")
        return
    
    changed_files = 0
    
    # Process each file
    for i, html_file in enumerate(html_files, 1):
        print(f"\n[{i}/{len(html_files)}]", end=" ")
        if fix_song_page(html_file):
            changed_files += 1
    
    print(f"\n\n✅ Processing complete!")
    print(f"📁 Total files processed: {len(html_files)}")
    print(f"✏️  Files changed: {changed_files}")
    print(f"⏭️  Files unchanged: {len(html_files) - changed_files}")

if __name__ == "__main__":
    main()