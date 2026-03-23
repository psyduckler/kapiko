#!/usr/bin/env python3
"""
Generate Prompt Lab sections for kapiko.ai song pages.
Reads song data from HTML files and injects prompt lab sections.
"""

import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def extract_song_data(html_content: str) -> Optional[Dict]:
    """Extract all song data from the HTML content."""
    
    # Extract basic stats from stat cards
    bpm_match = re.search(r'<div class="stat-val">(\d+)</div><div class="stat-label">BPM</div>', html_content)
    key_match = re.search(r'<div class="stat-val">([^<]+)</div><div class="stat-label">Key</div>', html_content)
    energy_match = re.search(r'<div class="stat-val">([0-9.]+)%</div><div class="stat-label">Energy</div>', html_content)
    duration_match = re.search(r'<div class="stat-val">([^<]+)</div><div class="stat-label">Duration</div>', html_content)
    
    # Extract title and artist from header
    title_match = re.search(r'<div class="song-title">([^<]+)</div>', html_content)
    artist_match = re.search(r'<div class="song-artist">([^<]+)</div>', html_content)
    
    # Check if song has AI analysis
    if 'AI Audio Analysis' not in html_content:
        return None
    
    # Extract audio features from feature bars
    valence_match = re.search(r'<div class="feature-label">Valence</div><div class="feature-val">([0-9.]+)%</div>', html_content)
    acousticness_match = re.search(r'<div class="feature-label">Acousticness</div><div class="feature-val">([0-9.]+)%</div>', html_content)
    instrumentalness_match = re.search(r'<div class="feature-label">Instrumentalness</div><div class="feature-val">([0-9.]+)%</div>', html_content)
    
    # Extract instrumentation pills
    instruments_section = re.search(r'<h3>Instrumentation</h3>\s*<div class="pills">(.*?)</div>', html_content, re.DOTALL)
    instruments = []
    primary_instrument = None
    
    if instruments_section:
        pill_matches = re.findall(r'<span class="pill">([^<]+)</span>', instruments_section.group(1))
        instruments = pill_matches
        
        # Extract primary instrument
        primary_match = re.search(r'Primary: <strong>([^<]+)</strong>', html_content)
        if primary_match:
            primary_instrument = primary_match.group(1)
        elif instruments:
            primary_instrument = instruments[0]
    
    # Extract mood
    mood_section = re.search(r'<h3>Mood & Atmosphere</h3>\s*<div class="mood-tags">(.*?)</div>', html_content, re.DOTALL)
    mood = None
    atmosphere = None
    
    if mood_section:
        mood_primary = re.search(r'<span class="mood-primary">([^<]+)</span>', mood_section.group(1))
        mood_atmo = re.search(r'<span class="mood-atmo">([^<]+)</span>', mood_section.group(1))
        if mood_primary:
            mood = mood_primary.group(1)
        if mood_atmo:
            atmosphere = mood_atmo.group(1)
    
    # Extract production style
    production_section = re.search(r'<h3>Production & Sound Design</h3>\s*<p class="prod-style">([^<]+)</p>', html_content)
    production_style = None
    if production_section:
        production_style = production_section.group(1)
    
    # Extract sound design effects
    sd_pills_section = re.search(r'<h3>Production & Sound Design</h3>.*?<div class="pills">(.*?)</div>', html_content, re.DOTALL)
    sound_effects = []
    if sd_pills_section:
        sd_matches = re.findall(r'<span class="pill sd">([^<]+)</span>', sd_pills_section.group(1))
        sound_effects = sd_matches
    
    # Extract production metadata (texture, dynamics, stereo)
    texture = dynamics = stereo = None
    texture_match = re.search(r'Texture: <strong>([^<]+)</strong>', html_content)
    dynamics_match = re.search(r'Dynamics: <strong>([^<]+)</strong>', html_content)
    stereo_match = re.search(r'Stereo: <strong>([^<]+)</strong>', html_content)
    
    if texture_match:
        texture = texture_match.group(1)
    if dynamics_match:
        dynamics = dynamics_match.group(1)
    if stereo_match:
        stereo = stereo_match.group(1)
    
    # Extract genres
    genre_section = re.search(r'<h3>Genre Tags</h3>\s*<div class="pills">(.*?)</div>', html_content, re.DOTALL)
    genres = []
    if genre_section:
        genre_matches = re.findall(r'<span class="pill genre">([^<]+)</span>', genre_section.group(1))
        genres = genre_matches
    
    # Extract similar artists
    artists_section = re.search(r'<h3>Similar Artists</h3>\s*<div class="pills">(.*?)</div>', html_content, re.DOTALL)
    similar_artists = []
    if artists_section:
        artist_matches = re.findall(r'<span class="pill artist">([^<]+)</span>', artists_section.group(1))
        similar_artists = artist_matches
    
    # Extract character traits
    vocals = harmony = rhythm = None
    vocals_match = re.search(r'<div class="char-label">Vocals</div>\s*<div class="char-value">([^<]+)</div>', html_content)
    harmony_match = re.search(r'<div class="char-label">Harmony</div>\s*<div class="char-value">([^<]+)</div>', html_content)
    rhythm_match = re.search(r'<div class="char-label">Rhythm</div>\s*<div class="char-value">([^<]+)</div>', html_content)
    
    if vocals_match:
        vocals = vocals_match.group(1)
    if harmony_match:
        harmony = harmony_match.group(1)
    if rhythm_match:
        rhythm = rhythm_match.group(1)
    
    # Extract "What Makes This Track Unique"
    unique_section = re.search(r'<h3>What Makes This Track Unique</h3>\s*<p>([^<]+)</p>', html_content)
    unique_text = None
    if unique_section:
        unique_text = unique_section.group(1)
    
    # Return data dict
    return {
        'title': title_match.group(1) if title_match else None,
        'artist': artist_match.group(1) if artist_match else None,
        'bpm': int(bpm_match.group(1)) if bpm_match else None,
        'key': key_match.group(1) if key_match else None,
        'energy': float(energy_match.group(1)) if energy_match else None,
        'valence': float(valence_match.group(1)) if valence_match else None,
        'acousticness': float(acousticness_match.group(1)) if acousticness_match else None,
        'instrumentalness': float(instrumentalness_match.group(1)) if instrumentalness_match else None,
        'duration': duration_match.group(1) if duration_match else None,
        'instruments': instruments,
        'primary_instrument': primary_instrument,
        'mood': mood,
        'atmosphere': atmosphere,
        'production_style': production_style,
        'sound_effects': sound_effects,
        'texture': texture,
        'dynamics': dynamics,
        'stereo': stereo,
        'genres': genres,
        'similar_artists': similar_artists,
        'vocals': vocals,
        'harmony': harmony,
        'rhythm': rhythm,
        'unique_text': unique_text,
    }

def get_tempo_words(bpm: int) -> List[str]:
    """Generate tempo descriptor words based on BPM value."""
    if bpm < 80:
        return ["slow", "glacial", "drifting", "suspended"]
    elif bpm < 110:
        return ["mid-tempo", "unhurried", "steady", "gentle"]
    elif bpm < 140:
        return ["upbeat", "driving", "energetic", "lively"]
    else:
        return ["fast", "urgent", "propulsive", "rapid"]

def get_energy_words(energy: float) -> List[str]:
    """Generate energy descriptor words based on energy percentage."""
    if energy < 30:
        return ["whisper-quiet", "delicate", "gentle", "featherlight"]
    elif energy < 50:
        return ["subdued", "restrained", "understated", "soft"]
    elif energy < 70:
        return ["moderate", "balanced", "present", "warm"]
    else:
        return ["powerful", "driving", "intense", "dynamic"]

def get_valence_words(valence: float) -> List[str]:
    """Generate mood descriptor words based on valence percentage."""
    if valence < 20:
        return ["melancholic", "somber", "introspective", "contemplative"]
    elif valence < 40:
        return ["contemplative", "wistful", "bittersweet", "nostalgic"]
    elif valence < 60:
        return ["neutral", "balanced", "steady", "calm"]
    elif valence < 80:
        return ["warm", "hopeful", "uplifting", "positive"]
    else:
        return ["euphoric", "joyful", "radiant", "ecstatic"]

def generate_main_prompt(data: Dict) -> str:
    """Generate the main ready-to-use prompt text — natural, non-repetitive."""
    parts = []

    # Opening: duration + genre + tempo + key
    genre_text = data['genres'][0] if data['genres'] else 'ambient'
    parts.append(f"Create a {data['duration']} {genre_text} track at {data['bpm']} BPM in {data['key']}.")

    # Instrumentation sentence
    if data['vocals'] and data['vocals'] != 'None':
        supporting = [i for i in data['instruments'] if i != data['primary_instrument']][:3]
        if supporting:
            parts.append(f"{data['primary_instrument'].capitalize()} over {', '.join(supporting)}.")
        else:
            parts.append(f"Featuring {data['primary_instrument']}.")
    else:
        parts.append(f"Instrumental — {', '.join(data['instruments'][:4])}.")

    # Mood + atmosphere (one sentence, no repeats)
    mood_text = data['mood'] or 'contemplative'
    atmo_text = data['atmosphere']
    if atmo_text:
        parts.append(f"{mood_text.capitalize()} and {atmo_text}.")
    else:
        parts.append(f"{mood_text.capitalize()}.")

    # Production (combine style + effects + metadata into one flowing sentence)
    prod_bits = []
    if data['production_style']:
        prod_bits.append(data['production_style'].capitalize())
    if data['sound_effects']:
        prod_bits.append('with ' + ' and '.join(data['sound_effects']))

    meta_bits = []
    if data['texture']:
        meta_bits.append(f"{data['texture']} texture")
    if data['dynamics']:
        meta_bits.append(f"{data['dynamics']} dynamics")
    if data['stereo']:
        meta_bits.append(f"{data['stereo']} stereo field")

    if prod_bits or meta_bits:
        prod_str = ', '.join(prod_bits)
        if meta_bits:
            prod_str += ('. ' if prod_str else '') + ', '.join(meta_bits).capitalize() + '.'
        else:
            prod_str += '.'
        parts.append(prod_str)

    # Energy + valence as descriptive colour
    energy_word = get_energy_words(data['energy'])[0] if data['energy'] else 'moderate'
    valence_word = get_valence_words(data['valence'])[0] if data['valence'] else 'neutral'
    parts.append(f"{energy_word.capitalize()} energy ({data['energy']:.0f}%), {valence_word} mood ({data['valence']:.0f}%).")

    # Artist reference (avoid repeating the mood word already used)
    if len(data['similar_artists']) >= 2:
        parts.append(f"Think {data['similar_artists'][0]} meets {data['similar_artists'][1]}.")

    return ' '.join(parts)

def generate_prompt_lab_html(data: Dict) -> str:
    """Generate the complete Prompt Lab HTML section."""
    
    main_prompt = generate_main_prompt(data)
    
    html = f'''
  <!-- ════════════════════════════════════════════════════ Prompt Lab ════════ -->
  <div class="section-label"><h2>Prompt Lab</h2></div>
  
  <div class="prompt-lab">
    <div class="prompt-lab-intro">
      <h3>🧪 Recreate This Track</h3>
      <p>Use these prompt ingredients with Suno, Udio, MusicGen, or any AI music generation service to recreate the vibe of {data['title']} by {data['artist']}.</p>
    </div>

    <!-- Ready-to-copy prompt -->
    <div class="prompt-card prompt-card-main">
      <div class="prompt-card-header">
        <span class="prompt-card-label">Ready-to-Use Prompt</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="mainPrompt">Copy</button>
      </div>
      <div class="prompt-text" id="mainPrompt">{main_prompt}</div>
    </div>

    <!-- Parameter cards -->
    <div class="prompt-params">

      <div class="prompt-param-card">
        <div class="prompt-param-label">Tempo</div>
        <div class="prompt-param-value">{data['bpm']} BPM</div>
        <div class="prompt-param-detail">{'Mid-tempo' if 80 <= data['bpm'] < 110 else 'Slow' if data['bpm'] < 80 else 'Upbeat' if data['bpm'] < 140 else 'Fast'} pace. Natural rhythm for the genre.</div>
        <div class="prompt-param-words">'''
    
    # Add tempo words
    for word in get_tempo_words(data['bpm'])[:4]:
        html += f'\n          <span class="prompt-word">{word}</span>'
    
    html += f'''
        </div>
      </div>

      <div class="prompt-param-card">
        <div class="prompt-param-label">Energy</div>
        <div class="prompt-param-value">{data['energy']:.1f}%</div>
        <div class="prompt-param-detail">{'Very low' if data['energy'] < 30 else 'Low to moderate' if data['energy'] < 50 else 'Moderate' if data['energy'] < 70 else 'High'} energy level. Sets the dynamic intensity.</div>
        <div class="prompt-param-words">'''
    
    # Add energy words
    for word in get_energy_words(data['energy'])[:4]:
        html += f'\n          <span class="prompt-word">{word}</span>'
    
    html += f'''
        </div>
      </div>

      <div class="prompt-param-card">
        <div class="prompt-param-label">Mood</div>
        <div class="prompt-param-value">{data['valence']:.1f}% Valence</div>
        <div class="prompt-param-detail">{data['mood'] if data['mood'] else 'Contemplative'} mood with {data['atmosphere'] if data['atmosphere'] else 'atmospheric'} atmosphere.</div>
        <div class="prompt-param-words">'''
    
    # Add mood words
    for word in get_valence_words(data['valence'])[:3]:
        html += f'\n          <span class="prompt-word">{word}</span>'
    
    if data['atmosphere']:
        html += f'\n          <span class="prompt-word">{data["atmosphere"]}</span>'
    
    html += f'''
        </div>
      </div>

      <div class="prompt-param-card">
        <div class="prompt-param-label">Instrumentation</div>
        <div class="prompt-param-value">{len(data['instruments'])} Instruments</div>
        <div class="prompt-param-detail">Primary: {data['primary_instrument']}. Full arrangement with {', '.join(data['instruments'][:3])}.</div>
        <div class="prompt-param-words">'''
    
    # Add instrument words
    for instrument in data['instruments'][:4]:
        html += f'\n          <span class="prompt-word">{instrument.replace(" ", "-")}</span>'
    
    html += f'''
        </div>
      </div>

      <div class="prompt-param-card">
        <div class="prompt-param-label">Key & Tonality</div>
        <div class="prompt-param-value">{data['key']}</div>
        <div class="prompt-param-detail">{'Major key' if 'Major' in data['key'] else 'Minor key' if 'minor' in data['key'] else 'Tonal center'}. Harmonic foundation with {data['harmony'].lower() if data['harmony'] else 'moderate progressions'}.</div>
        <div class="prompt-param-words">
          <span class="prompt-word">{"major" if "Major" in data['key'] else "minor" if "minor" in data['key'] else "tonal"}</span>
          <span class="prompt-word">{"bright" if "Major" in data['key'] else "dark" if "minor" in data['key'] else "modal"}</span>'''
    
    if data['harmony']:
        harmony_word = data['harmony'].lower().replace(' ', '-')
        html += f'\n          <span class="prompt-word">{harmony_word}</span>'
    
    html += f'''
        </div>
      </div>

      <div class="prompt-param-card">
        <div class="prompt-param-label">Production</div>
        <div class="prompt-param-value">{data['production_style'] if data['production_style'] else 'Studio production'}</div>
        <div class="prompt-param-detail">{', '.join(data['sound_effects']) if data['sound_effects'] else 'Clean recording'}. {data['texture'] if data['texture'] else 'Balanced'} texture, {data['dynamics'] if data['dynamics'] else 'moderate'} dynamics.</div>
        <div class="prompt-param-words">'''
    
    # Add production words
    if data['sound_effects']:
        for effect in data['sound_effects'][:3]:
            html += f'\n          <span class="prompt-word">{effect.replace(" ", "-")}</span>'
    
    if data['texture']:
        html += f'\n          <span class="prompt-word">{data["texture"]}</span>'
    
    if data['stereo']:
        html += f'\n          <span class="prompt-word">{data["stereo"]}-stereo</span>'
    
    html += '''
        </div>
      </div>

    </div>
  </div>
'''
    
    return html

def get_prompt_lab_css() -> str:
    """Return the Prompt Lab CSS to be injected."""
    return '''
    /* ── Prompt Lab ── */
    .prompt-lab {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      margin-bottom: 2rem;
    }
    .prompt-lab-intro h3 {
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 0.5rem;
    }
    .prompt-lab-intro p {
      color: var(--text-muted);
      font-size: 0.95rem;
      line-height: 1.6;
    }
    .prompt-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.5rem;
      position: relative;
    }
    .prompt-card-main {
      border-color: rgba(78,205,196,0.25);
      background: linear-gradient(135deg, rgba(78,205,196,0.04), rgba(155,127,212,0.04));
    }
    .prompt-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    .prompt-card-label {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--teal);
      font-weight: 600;
    }
    .copy-btn {
      background: rgba(78,205,196,0.15);
      color: var(--teal);
      border: 1px solid rgba(78,205,196,0.3);
      border-radius: 8px;
      padding: 0.4rem 1rem;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s;
    }
    .copy-btn:hover {
      background: rgba(78,205,196,0.25);
    }
    .prompt-text {
      font-size: 0.95rem;
      line-height: 1.7;
      color: var(--text);
      font-family: 'Inter', sans-serif;
    }
    .prompt-params {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 1rem;
    }
    .prompt-param-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.2rem;
    }
    .prompt-param-label {
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--text-muted);
      margin-bottom: 0.3rem;
    }
    .prompt-param-value {
      font-size: 1.2rem;
      font-weight: 700;
      color: var(--teal);
      margin-bottom: 0.5rem;
    }
    .prompt-param-detail {
      font-size: 0.85rem;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 0.6rem;
    }
    .prompt-param-words {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .prompt-word {
      background: rgba(78,205,196,0.08);
      color: var(--teal);
      border: 1px solid rgba(78,205,196,0.15);
      border-radius: 6px;
      padding: 0.2rem 0.6rem;
      font-size: 0.75rem;
    }'''

def get_copy_prompt_js() -> str:
    """Return the JavaScript copyPrompt function."""
    return '''
function copyPrompt(btn) {
  const id = btn.getAttribute('data-target');
  const text = document.getElementById(id).textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.style.background = 'rgba(78,205,196,0.3)';
    setTimeout(() => {
      btn.textContent = 'Copy';
      btn.style.background = '';
    }, 2000);
  });
}'''

def inject_prompt_lab(file_path: str) -> bool:
    """Inject Prompt Lab section into a song page HTML file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract song data
    data = extract_song_data(content)
    if not data:
        print(f"Skipping {file_path} - no AI analysis found")
        return False
    
    # Check if Prompt Lab already exists
    if 'Prompt Lab' in content:
        print(f"Skipping {file_path} - Prompt Lab already exists")
        return False
    
    # Generate Prompt Lab HTML
    prompt_lab_html = generate_prompt_lab_html(data)
    
    # Inject CSS into existing <style> block
    css = get_prompt_lab_css()
    style_pattern = r'(</style>)'
    content = re.sub(style_pattern, css + r'\n  \1', content)
    
    # Inject Prompt Lab HTML before footer
    footer_pattern = r'(\s*</div>\s*<footer>)'
    content = re.sub(footer_pattern, prompt_lab_html + r'\1', content)
    
    # Inject JavaScript - check if <script> already exists
    js_function = get_copy_prompt_js()
    
    if '<script>' in content:
        # Add to existing script block
        script_pattern = r'(</script>\s*</body>)'
        content = re.sub(script_pattern, js_function + r'\n\1', content)
    else:
        # Create new script block before </body>
        content = re.sub(r'(</body>)', f'<script>\n{js_function}\n</script>\n\\1', content)
    
    # Write the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Added Prompt Lab to {os.path.basename(os.path.dirname(file_path))}")
    return True

def main():
    """Main function to process all song pages."""
    
    songs_dir = "/Users/bjh/kapiko/site/songs"
    pattern = os.path.join(songs_dir, "*/index.html")
    
    song_files = glob.glob(pattern)
    
    print(f"Found {len(song_files)} song pages")
    print("Processing songs with AI analysis...")
    print()
    
    processed = 0
    skipped = 0
    
    for file_path in sorted(song_files):
        if inject_prompt_lab(file_path):
            processed += 1
        else:
            skipped += 1
    
    print()
    print(f"✅ Processed: {processed} songs")
    print(f"⏭️  Skipped: {skipped} songs (no AI analysis)")
    print(f"📊 Total: {processed + skipped} songs")

if __name__ == "__main__":
    main()