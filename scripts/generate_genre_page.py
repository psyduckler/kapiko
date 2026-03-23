#!/usr/bin/env python3
"""Generate a kapiko genre analysis page from analysis.json data."""

import json
import sys
import os
import html as htmlmod

def generate_genre_page(genre_slug, analysis_path, output_path):
    with open(analysis_path, 'r') as f:
        data = json.load(f)
    
    genre_name = data['genre']
    display_name = genre_name.replace('-', ' ').title()
    track_count = data['track_count']
    
    # Genre-specific emoji and descriptions
    genre_meta = {
        'piano': {'emoji': '🎹', 'color_accent': '#4ecdc4', 'desc': 'Piano music spans classical, contemporary, and ambient — one of the most versatile instruments in music generation.'},
        'sleep': {'emoji': '🌙', 'color_accent': '#9b7fd4', 'desc': 'Sleep music is functional audio designed to facilitate rest. Ultra-low energy, minimal dynamics, and calming frequencies.'},
        'chill': {'emoji': '😌', 'color_accent': '#5b9bd5', 'desc': 'Chill spans soft electronic, ambient pop, and lo-fi — music designed for relaxation without falling asleep.'},
        'study': {'emoji': '📚', 'color_accent': '#4ecdc4', 'desc': 'Study music occupies the productive middle ground — enough energy to focus, not enough to distract. The Goldilocks zone.'},
        'classical': {'emoji': '🎻', 'color_accent': '#9b7fd4', 'desc': 'Classical music encompasses centuries of orchestral, chamber, and solo compositions with complex harmonic structures.'},
        'jazz': {'emoji': '🎷', 'color_accent': '#5b9bd5', 'desc': 'Jazz features complex harmony, improvisation, and swing. From bebop to smooth jazz to fusion — wildly varied audio profiles.'},
        'acoustic': {'emoji': '🎸', 'color_accent': '#4ecdc4', 'desc': 'Acoustic music emphasizes natural, unplugged sound — organic warmth, singer-songwriter intimacy, and live room feel.'},
        'electronic': {'emoji': '⚡', 'color_accent': '#9b7fd4', 'desc': 'Electronic music spans ambient to high-energy EDM. Synthesizers, drum machines, and digital production define the genre.'},
        'hip-hop': {'emoji': '🎤', 'color_accent': '#5b9bd5', 'desc': 'Hip-hop is the biggest streaming genre. Beat-driven, rhythmic, with strong bass profiles and vocal-forward production.'},
        'soul': {'emoji': '🎙️', 'color_accent': '#4ecdc4', 'desc': 'Soul music features rich, warm vocals and organic instrumentation. Gospel-influenced harmonies with deep emotional expression.'},
    }
    
    meta = genre_meta.get(genre_slug, {'emoji': '🎵', 'color_accent': '#4ecdc4', 'desc': f'Audio analysis of {display_name} music.'})
    
    # Stats
    bpm = data['bpm']
    energy = data['energy']
    valence = data['valence']
    acousticness = data['acousticness']
    instrumentalness = data['instrumentalness']
    danceability = data['danceability']
    loudness = data['loudness']
    speechiness = data['speechiness']
    
    # Key distribution
    key_dist = data['key_distribution']
    top_key = list(key_dist.keys())[0] if key_dist else 'C'
    top_key_count = list(key_dist.values())[0] if key_dist else 0
    
    # Mode distribution
    mode_dist = data['mode_distribution']
    major_pct = round(mode_dist.get('Major', 0) / track_count * 100) if track_count else 0
    minor_pct = 100 - major_pct
    
    # Top artists
    top_artists = data['top_artists'][:15]
    
    # Tracks
    tracks = data['tracks']
    
    # BPM histogram data
    bpm_hist = bpm.get('histogram', {})
    bpm_labels = sorted(bpm_hist.keys(), key=lambda x: int(x.split('-')[0]))
    bpm_values = [bpm_hist[k] for k in bpm_labels]
    
    # Key distribution chart data
    key_labels = list(key_dist.keys())
    key_values = list(key_dist.values())
    
    # Energy-valence scatter
    ev_scatter = data.get('energy_valence_scatter', [])
    
    # Acoustic-instrumental scatter
    ai_scatter = data.get('acoustic_instrumental_scatter', [])
    
    # Duration stats
    duration = data.get('duration', {})
    avg_duration_ms = duration.get('mean', 200000)
    avg_duration_s = avg_duration_ms / 1000
    avg_duration_str = f"{int(avg_duration_s // 60)}:{int(avg_duration_s % 60):02d}"
    
    # Genre-specific prompt lab content
    prompt_descriptions = {
        'piano': {'style_tags': 'piano, solo piano, neo-classical, melodic, contemplative', 'instruments': 'grand piano, soft piano, piano arpeggios', 'mood_words': 'reflective, intimate, graceful, meditative'},
        'sleep': {'style_tags': 'sleep, ambient, drone, minimal, quiet', 'instruments': 'soft pads, ambient textures, gentle drones', 'mood_words': 'peaceful, drowsy, weightless, serene'},
        'chill': {'style_tags': 'chill, downtempo, soft electronic, lo-fi, relaxed', 'instruments': 'synth pads, soft beats, warm bass, electric piano', 'mood_words': 'laid-back, dreamy, mellow, soothing'},
        'study': {'style_tags': 'study, focus, lo-fi beats, instrumental, ambient', 'instruments': 'lo-fi piano, soft drums, ambient pads, gentle guitar', 'mood_words': 'focused, calm, productive, steady'},
        'classical': {'style_tags': 'classical, orchestral, chamber, symphony, concert', 'instruments': 'strings, orchestra, violin, cello, flute, oboe', 'mood_words': 'elegant, dramatic, refined, majestic'},
        'jazz': {'style_tags': 'jazz, smooth jazz, jazz piano, swing, bebop', 'instruments': 'saxophone, jazz piano, upright bass, brushed drums, trumpet', 'mood_words': 'sophisticated, groovy, warm, improvisational'},
        'acoustic': {'style_tags': 'acoustic, singer-songwriter, folk, unplugged, organic', 'instruments': 'acoustic guitar, fingerpicking, cajon, harmonica, banjo', 'mood_words': 'warm, intimate, honest, earthy'},
        'electronic': {'style_tags': 'electronic, synth, EDM, ambient electronic, synthwave', 'instruments': 'synthesizer, drum machine, arpeggiated synths, bass synth, vocoder', 'mood_words': 'futuristic, driving, immersive, pulsing'},
        'hip-hop': {'style_tags': 'hip-hop, rap, trap, boom bap, beats', 'instruments': '808 bass, hi-hats, snare, sample chops, vinyl crackle', 'mood_words': 'confident, rhythmic, bold, raw'},
        'soul': {'style_tags': 'soul, R&B, neo-soul, gospel-influenced, vintage soul', 'instruments': 'warm vocals, organ, electric piano, bass guitar, horn section', 'mood_words': 'passionate, warm, soulful, heartfelt'},
    }
    
    prompt = prompt_descriptions.get(genre_slug, {
        'style_tags': f'{genre_name}, instrumental, atmospheric',
        'instruments': 'various instruments',
        'mood_words': 'expressive, dynamic, engaging'
    })
    
    # Escape for JS
    def js_str(s):
        return json.dumps(s)
    
    # Build HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{display_name} — kapiko music analytics</title>
  <meta name="description" content="Audio feature analysis of top {track_count} {display_name} tracks. BPM, key, energy, valence distributions and AI music generation prompts.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:            #0b0c1a;
      --bg-card:       #111222;
      --bg-header:     #0d0e20;
      --border:        rgba(255, 255, 255, 0.07);
      --border-accent: rgba(78, 205, 196, 0.22);
      --text:          #dde1f0;
      --text-muted:    #6b7099;
      --text-dim:      #3d4060;
      --teal:          #4ecdc4;
      --purple:        #9b7fd4;
      --blue:          #5b9bd5;
      --teal-glow:     rgba(78, 205, 196, 0.12);
      --purple-glow:   rgba(155, 127, 212, 0.12);
    }}

    html {{ scroll-behavior: smooth; }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }}

    header {{
      background: var(--bg-header);
      border-bottom: 1px solid var(--border);
      position: relative;
      overflow: hidden;
    }}

    header::before {{
      content: '';
      position: absolute;
      inset: 0;
      background:
        radial-gradient(ellipse 60% 80% at 10% 50%, rgba(78, 205, 196, 0.07) 0%, transparent 70%),
        radial-gradient(ellipse 40% 60% at 85% 20%, rgba(155, 127, 212, 0.06) 0%, transparent 70%);
      pointer-events: none;
    }}

    .header-inner {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 56px 28px 52px;
      position: relative;
    }}

    .brand {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: var(--teal);
      margin-bottom: 24px;
    }}

    .brand-dot {{
      width: 6px; height: 6px;
      background: var(--teal);
      border-radius: 50%;
    }}

    .brand a {{ color: var(--teal); text-decoration: none; }}
    .brand a:hover {{ text-decoration: underline; }}

    .genre-pill {{
      display: inline-block;
      background: rgba(78, 205, 196, 0.12);
      color: var(--teal);
      border: 1px solid rgba(78, 205, 196, 0.25);
      border-radius: 20px;
      padding: 4px 14px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 16px;
    }}

    h1 {{
      font-size: clamp(2rem, 5vw, 3.2rem);
      font-weight: 700;
      line-height: 1.15;
      margin-bottom: 12px;
    }}

    .subtitle {{
      font-size: 1rem;
      color: var(--text-muted);
      max-width: 560px;
    }}

    .stat-row {{
      display: flex;
      gap: 32px;
      margin-top: 32px;
      flex-wrap: wrap;
    }}

    .stat-item {{ text-align: left; }}
    .stat-big {{
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--teal);
    }}
    .stat-label {{
      font-size: 0.72rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-top: 2px;
    }}

    .content {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 40px 28px 80px;
    }}

    .section-label {{
      margin: 48px 0 20px;
      position: relative;
      padding-bottom: 12px;
    }}

    .section-label:first-child {{ margin-top: 0; }}

    .section-label h2 {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      color: var(--teal);
      font-weight: 600;
    }}

    .section-label::after {{
      content: '';
      position: absolute;
      bottom: 0; left: 0;
      width: 40px; height: 2px;
      background: linear-gradient(90deg, var(--teal), transparent);
    }}

    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;
    }}

    .chart-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      transition: border-color 0.3s;
    }}

    .chart-card:hover {{ border-color: var(--border-accent); }}
    .chart-card.full {{ grid-column: 1 / -1; }}

    .chart-title {{
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 4px;
    }}

    .chart-analysis {{
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-bottom: 16px;
      line-height: 1.5;
    }}

    .chart-wrap {{
      position: relative;
      height: 260px;
    }}

    .feature-bars {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .feature-item {{
      display: grid;
      grid-template-columns: 120px 48px 1fr;
      align-items: center;
      gap: 8px;
    }}

    .feature-label {{
      font-size: 0.78rem;
      color: var(--text-muted);
    }}

    .feature-val {{
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text);
      text-align: right;
    }}

    .feature-track {{
      height: 6px;
      background: rgba(255, 255, 255, 0.04);
      border-radius: 3px;
      overflow: hidden;
    }}

    .feature-fill {{
      height: 100%;
      border-radius: 3px;
      background: linear-gradient(90deg, var(--teal), var(--purple));
    }}

    /* Top Artists */
    .artists-bar {{ display: flex; flex-direction: column; gap: 8px; }}
    .artist-row {{
      display: grid;
      grid-template-columns: 160px 1fr 40px;
      align-items: center;
      gap: 8px;
    }}
    .artist-name {{ font-size: 0.82rem; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .artist-bar-track {{ height: 8px; background: rgba(255,255,255,0.04); border-radius: 4px; overflow: hidden; }}
    .artist-bar-fill {{ height: 100%; border-radius: 4px; }}
    .artist-count {{ font-size: 0.78rem; color: var(--text-muted); text-align: right; }}

    /* Top Tracks Table */
    .tracks-table {{ width: 100%; border-collapse: separate; border-spacing: 0; }}
    .tracks-table th {{
      text-align: left; font-size: 0.7rem; text-transform: uppercase;
      letter-spacing: 0.1em; color: var(--text-muted); padding: 8px 12px;
      border-bottom: 1px solid var(--border);
    }}
    .tracks-table td {{
      padding: 10px 12px; font-size: 0.85rem; border-bottom: 1px solid rgba(255,255,255,0.03);
    }}
    .tracks-table tr:hover td {{ background: rgba(78,205,196,0.04); }}
    .track-name {{ color: var(--text); font-weight: 500; }}
    .track-name a {{ color: var(--teal); text-decoration: none; }}
    .track-name a:hover {{ text-decoration: underline; }}
    .track-artist {{ color: var(--text-muted); font-size: 0.8rem; }}
    .track-num {{ color: var(--text-dim); font-size: 0.78rem; }}
    .show-more-btn {{
      display: block; width: 100%; margin-top: 12px; padding: 10px;
      background: rgba(78,205,196,0.08); border: 1px solid rgba(78,205,196,0.2);
      border-radius: 8px; color: var(--teal); font-size: 0.82rem;
      cursor: pointer; font-family: inherit; transition: all 0.2s;
    }}
    .show-more-btn:hover {{ background: rgba(78,205,196,0.15); }}

    /* Prompt Lab */
    .prompt-lab-section {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 32px;
    }}
    .prompt-lab-intro {{ margin-bottom: 24px; }}
    .prompt-lab-intro h3 {{ font-size: 1.3rem; font-weight: 700; margin-bottom: 8px; }}
    .prompt-lab-intro p {{ color: var(--text-muted); font-size: 0.92rem; line-height: 1.6; }}
    .prompt-label {{
      font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em;
      color: var(--teal); font-weight: 600; margin-bottom: 8px;
    }}
    .prompt-box {{
      background: rgba(0,0,0,0.3); border: 1px solid var(--border);
      border-radius: 8px; padding: 16px; position: relative;
      font-size: 0.88rem; line-height: 1.7; color: var(--text);
      margin-bottom: 16px;
    }}
    .copy-btn {{
      position: absolute; top: 8px; right: 8px;
      background: rgba(78,205,196,0.15); color: var(--teal);
      border: 1px solid rgba(78,205,196,0.3); border-radius: 6px;
      padding: 4px 12px; font-size: 0.72rem; cursor: pointer;
      font-family: inherit; transition: all 0.2s;
    }}
    .copy-btn:hover {{ background: rgba(78,205,196,0.25); }}

    /* Correlation */
    .corr-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
    }}
    .corr-cell {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      text-align: center;
    }}
    .corr-pair {{ font-size: 0.72rem; color: var(--text-muted); margin-bottom: 4px; }}
    .corr-val {{ font-size: 1.1rem; font-weight: 700; }}

    footer {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 28px;
      border-top: 1px solid var(--border);
      text-align: center;
      color: var(--text-dim);
      font-size: 0.78rem;
    }}
    footer a {{ color: var(--teal); text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}

    @media (max-width: 768px) {{
      .charts-grid {{ grid-template-columns: 1fr; }}
      .stat-row {{ gap: 20px; }}
      .artist-row {{ grid-template-columns: 120px 1fr 36px; }}
    }}
  </style>
</head>
<body>

<header>
  <div class="header-inner">
    <div class="brand">
      <span class="brand-dot"></span>
      <a href="/">kapiko</a> · <a href="/data/">music analytics</a>
    </div>
    <div class="genre-pill">Genre Report</div>
    <h1>{meta["emoji"]} {display_name}</h1>
    <p class="subtitle">Spotify Audio Features Analysis · Top {track_count} Tracks</p>
    <div class="stat-row">
      <div class="stat-item">
        <div class="stat-big">{bpm['median']:.0f}</div>
        <div class="stat-label">Median BPM</div>
      </div>
      <div class="stat-item">
        <div class="stat-big">{energy['median']*100:.0f}%</div>
        <div class="stat-label">Energy</div>
      </div>
      <div class="stat-item">
        <div class="stat-big">{valence['median']*100:.0f}%</div>
        <div class="stat-label">Valence</div>
      </div>
      <div class="stat-item">
        <div class="stat-big">{top_key}</div>
        <div class="stat-label">Top Key</div>
      </div>
      <div class="stat-item">
        <div class="stat-big">{acousticness['median']*100:.0f}%</div>
        <div class="stat-label">Acoustic</div>
      </div>
    </div>
  </div>
</header>

<div class="content">

  <!-- ── Audio DNA ── -->
  <div class="section-label"><h2>🧬 Audio DNA</h2></div>
  <div class="chart-card">
    <div class="chart-title">Feature Summary</div>
    <div class="chart-analysis">
      {meta['desc']}
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: start;">
      <div class="chart-wrap">
        <canvas id="chartRadar"></canvas>
      </div>
      <div class="feature-bars">
        <div class="feature-item"><div class="feature-label">Energy</div><div class="feature-val">{energy['median']*100:.0f}%</div><div class="feature-track"><div class="feature-fill" style="width:{energy['median']*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Danceability</div><div class="feature-val">{danceability['median']*100:.0f}%</div><div class="feature-track"><div class="feature-fill" style="width:{danceability['median']*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Valence</div><div class="feature-val">{valence['median']*100:.0f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(valence['median']*100, 2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Acousticness</div><div class="feature-val">{acousticness['median']*100:.0f}%</div><div class="feature-track"><div class="feature-fill" style="width:{acousticness['median']*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Instrumentalness</div><div class="feature-val">{instrumentalness['median']*100:.0f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(instrumentalness['median']*100, 2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Speechiness</div><div class="feature-val">{speechiness['median']*100:.0f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(speechiness['median']*100, 2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Loudness</div><div class="feature-val">{loudness['median']:.1f} dB</div><div class="feature-track"><div class="feature-fill" style="width:{max(0, min(100, (60 + loudness['median']) / 60 * 100)):.0f}%"></div></div></div>
      </div>
    </div>
  </div>

  <!-- ── Rhythm & Tonality ── -->
  <div class="section-label"><h2>🎵 Rhythm &amp; Tonality</h2></div>
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-title">BPM Distribution</div>
      <div class="chart-analysis">Median tempo: {bpm['median']:.0f} BPM (range {bpm['min']:.0f}–{bpm['max']:.0f})</div>
      <div class="chart-wrap"><canvas id="chartBPM"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Key Distribution</div>
      <div class="chart-analysis">Most common key: {top_key} ({top_key_count} tracks)</div>
      <div class="chart-wrap"><canvas id="chartKey"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Mode Distribution</div>
      <div class="chart-analysis">{major_pct}% Major / {minor_pct}% Minor</div>
      <div class="chart-wrap"><canvas id="chartMode"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Duration Distribution</div>
      <div class="chart-analysis">Average duration: {avg_duration_str}</div>
      <div class="chart-wrap"><canvas id="chartDuration"></canvas></div>
    </div>
  </div>

  <!-- ── Emotional Fingerprint ── -->
  <div class="section-label"><h2>💠 Emotional Fingerprint</h2></div>
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-title">Energy vs Valence</div>
      <div class="chart-analysis">Each dot is a track. Cluster position reveals the genre's emotional character.</div>
      <div class="chart-wrap"><canvas id="chartEV"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Acousticness vs Instrumentalness</div>
      <div class="chart-analysis">Acoustic + instrumental = pure soundscape. Low on both = vocal-driven electronic.</div>
      <div class="chart-wrap"><canvas id="chartAI"></canvas></div>
    </div>
  </div>

  <!-- ── Prompt Lab ── -->
  <div class="section-label"><h2>✨ Prompt Lab</h2></div>
  <div class="prompt-lab-section">
    <div class="prompt-lab-intro">
      <h3>Generate {display_name} Music</h3>
      <p>Use these data-driven prompts with Suno, Udio, or any AI music generation service. Parameters derived from analysis of {track_count} top {display_name.lower()} tracks.</p>
    </div>

    <div class="prompt-label">Suno / General Prompt</div>
    <div class="prompt-box" id="prompt-suno">
      <button class="copy-btn" onclick="copyPrompt('prompt-suno')">Copy</button>
      Create a {display_name.lower()} track at {bpm['median']:.0f} BPM in {top_key} {'Major' if major_pct > minor_pct else 'Minor'}. {prompt['style_tags']}. Target energy {energy['median']*100:.0f}%, valence {valence['median']*100:.0f}%. Instruments: {prompt['instruments']}. Mood: {prompt['mood_words']}.
    </div>

    <div class="prompt-label">Agent JSON</div>
    <div class="prompt-box" id="prompt-json" style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; white-space: pre;">
      <button class="copy-btn" onclick="copyPrompt('prompt-json')">Copy</button>
{{
  "genre": "{genre_name}",
  "bpm": {bpm['median']:.0f},
  "key": "{top_key