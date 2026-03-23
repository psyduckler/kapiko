#!/usr/bin/env python3
"""Generate kapiko song pages from genre analysis.json files.

Usage:
  python3 generate_song_pages.py          # all songs
  python3 generate_song_pages.py 0 200    # slice [0:200]
"""

import json, os, sys, re, html as H
from pathlib import Path

SITE = Path.home() / 'kapiko' / 'site'
GENRES = ['piano','sleep','chill','study','classical','jazz','acoustic','electronic','hip-hop','soul']

def esc(t): return H.escape(str(t))

def fmt_dur(ms):
    s = ms / 1000
    return f"{int(s//60)}:{int(s%60):02d}"

def loud_pct(db):
    return max(0, min(100, (60+db)/60*100))

def infer_mood(energy, valence):
    if energy < 0.3 and valence < 0.3: return 'melancholic, introspective'
    if energy < 0.3 and valence >= 0.3: return 'peaceful, serene'
    if energy < 0.5 and valence < 0.4: return 'contemplative, moody'
    if energy < 0.5 and valence >= 0.4: return 'relaxed, warm'
    if energy < 0.7 and valence < 0.4: return 'intense, brooding'
    if energy < 0.7 and valence >= 0.4: return 'upbeat, groovy'
    if valence >= 0.5: return 'energetic, joyful'
    return 'powerful, dark'

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
    }.get(genre, ['various instruments'])
    return ', '.join(base)

def infer_style(genre, energy, acousticness):
    if acousticness > 0.7: return 'organic, warm, natural'
    if energy > 0.7: return 'driving, energetic, produced'
    if energy < 0.3: return 'minimal, ambient, sparse'
    return 'polished, balanced, studio-quality'

GENRE_DISPLAY = {
    'piano':'Piano','sleep':'Sleep','chill':'Chill','study':'Study',
    'classical':'Classical','jazz':'Jazz','acoustic':'Acoustic',
    'electronic':'Electronic','hip-hop':'Hip-Hop','soul':'Soul',
    'ambient':'Ambient','lofi-hip-hop':'Lo-Fi Hip Hop',
    'neo-classical':'Neo-Classical','focus':'Focus','jazz-piano':'Jazz Piano'
}

def make_page(t, genre):
    name = t['name']
    artist = t['artists']
    slug = t.get('slug', '')
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
    loud = t.get('loudness', -8.0)
    dur_ms = t.get('duration_ms', 210000)
    
    dur_str = fmt_dur(dur_ms)
    mood = infer_mood(e, v)
    instruments = infer_instruments(genre, a, ins, e)
    style = infer_style(genre, e, a)
    gdisp = GENRE_DISPLAY.get(genre, genre.replace('-',' ').title())
    
    key_mode = f"{key} {mode}"
    
    gen_prompt = f"Create a {gdisp.lower()} track at {tempo:.0f} BPM in {key_mode}. {instruments}. Mood: {mood}. Style: {style}. Target energy {e*100:.0f}%, valence {v*100:.0f}%."
    suno_prompt = f"{gdisp.lower()}, {mood}, {instruments}, {style}, {tempo:.0f} BPM"
    udio_prompt = f"A {gdisp.lower()} track that feels {mood} with {instruments} — {style} in the style of {artist.split(';')[0]}"
    agent_json = json.dumps({
        "track_reference": {"title": name, "artist": artist},
        "generation_params": {"bpm": round(tempo), "key": key_mode, "duration": dur_str, "energy": round(e,3), "valence": round(v,3), "acousticness": round(a,3), "instrumentalness": round(ins,3)},
        "style": {"genre": genre, "mood": mood, "instruments": instruments.split(', '), "production": style},
        "prompt": gen_prompt
    }, indent=2)
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(name)} — Analysis + Prompt Template - kapiko</title>
  <meta name="description" content="Audio analysis of {esc(name)} by {esc(artist)}. BPM, key, energy, mood, and AI music generation prompts.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    :root{{--bg:#0b0c1a;--bg-card:#111222;--border:rgba(255,255,255,0.07);--text:#dde1f0;--text-muted:#6b7099;--teal:#4ecdc4;--purple:#9b7fd4;--blue:#5b9bd5}}
    body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
    .container{{max-width:900px;margin:0 auto;padding:0 1.5rem}}
    header{{background:#0d0e20;border-bottom:1px solid var(--border);padding:2rem 0}}
    .breadcrumb{{color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem}}
    .breadcrumb a{{color:var(--teal);text-decoration:none}}.breadcrumb a:hover{{text-decoration:underline}}
    .song-title{{font-size:2rem;font-weight:700;margin-bottom:0.3rem}}
    .song-artist{{font-size:1.1rem;color:var(--purple);font-weight:500}}
    .stats-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1rem;margin:2rem 0}}
    .stat-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1rem;text-align:center}}
    .stat-val{{font-size:1.5rem;font-weight:700;color:var(--teal)}}
    .stat-label{{font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.05em;margin-top:0.2rem}}
    .section-label{{margin:2.5rem 0 1rem}}.section-label h2{{font-size:0.8rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--teal);font-weight:600}}
    .chart-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem}}
    .chart-wrap{{height:280px;position:relative}}
    .feature-bars{{display:flex;flex-direction:column;gap:0.8rem;margin-top:1rem}}
    .feature-item{{display:grid;grid-template-columns:130px 50px 1fr;align-items:center;gap:0.5rem}}
    .feature-label{{font-size:0.85rem;color:var(--text-muted)}}
    .feature-val{{font-size:0.85rem;font-weight:600;text-align:right}}
    .feature-track{{height:6px;background:rgba(255,255,255,0.05);border-radius:3px;overflow:hidden}}
    .feature-fill{{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--teal),var(--purple))}}
    .prompt-lab{{display:flex;flex-direction:column;gap:1.5rem;margin-bottom:2rem}}
    .prompt-lab-intro h3{{font-size:1.3rem;font-weight:700;margin-bottom:0.5rem}}
    .prompt-lab-intro p{{color:var(--text-muted);font-size:0.95rem;line-height:1.6}}
    .prompt-tabs{{display:flex;gap:0.5rem;flex-wrap:wrap}}
    .prompt-tab{{background:rgba(255,255,255,0.04);color:var(--text-muted);border:1px solid var(--border);border-radius:8px;padding:0.5rem 1.2rem;font-size:0.85rem;font-weight:500;cursor:pointer;transition:all 0.2s;font-family:'Inter',sans-serif}}
    .prompt-tab:hover{{background:rgba(78,205,196,0.08);color:var(--text)}}
    .prompt-tab.active{{background:rgba(78,205,196,0.15);color:var(--teal);border-color:rgba(78,205,196,0.3)}}
    .prompt-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.5rem;position:relative}}
    .prompt-card-main{{border-color:rgba(78,205,196,0.25);background:linear-gradient(135deg,rgba(78,205,196,0.04),rgba(155,127,212,0.04))}}
    .prompt-card-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem}}
    .prompt-card-label{{font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--teal);font-weight:600}}
    .prompt-hint{{font-size:0.85rem;color:var(--text-muted);margin-bottom:0.8rem;line-height:1.5}}
    .prompt-hint strong{{color:var(--text)}}
    .copy-btn{{background:rgba(78,205,196,0.15);color:var(--teal);border:1px solid rgba(78,205,196,0.3);border-radius:8px;padding:0.4rem 1rem;font-size:0.8rem;cursor:pointer;transition:all 0.2s;font-family:'Inter',sans-serif}}
    .copy-btn:hover{{background:rgba(78,205,196,0.25)}}
    .prompt-text{{font-size:0.95rem;line-height:1.7;color:var(--text);font-family:'Inter',sans-serif}}
    .prompt-code{{font-size:0.82rem;line-height:1.6;color:var(--teal);font-family:'JetBrains Mono','Fira Code',monospace;background:rgba(0,0,0,0.3);border-radius:8px;padding:1rem;overflow-x:auto;white-space:pre;margin:0}}
    footer{{margin-top:3rem;padding:1.5rem 0;border-top:1px solid var(--border);text-align:center;color:var(--text-muted);font-size:0.8rem}}
    footer a{{color:var(--teal);text-decoration:none}}
    @media(max-width:600px){{.song-title{{font-size:1.5rem}}.stats-row{{grid-template-columns:repeat(2,1fr)}}.feature-item{{grid-template-columns:100px 45px 1fr}}}}
  </style>
</head>
<body>
<header>
  <div class="container">
    <div class="breadcrumb"><a href="/genres/{esc(genre)}/">{esc(gdisp)}</a> &rarr; Song Analysis</div>
    <div class="song-title">{esc(name)}</div>
    <div class="song-artist">{esc(artist)}</div>
  </div>
</header>

<div class="container">
  <div class="stats-row">
    <div class="stat-card"><div class="stat-val">{tempo:.0f}</div><div class="stat-label">BPM</div></div>
    <div class="stat-card"><div class="stat-val">{esc(key_mode)}</div><div class="stat-label">Key</div></div>
    <div class="stat-card"><div class="stat-val">{e*100:.0f}%</div><div class="stat-label">Energy</div></div>
    <div class="stat-card"><div class="stat-val">{dur_str}</div><div class="stat-label">Duration</div></div>
    <div class="stat-card"><div class="stat-val">{pop}</div><div class="stat-label">Popularity</div></div>
  </div>

  <div class="section-label"><h2>Audio Features</h2></div>
  <div class="chart-card">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem;align-items:start">
      <div class="chart-wrap" style="height:250px">
        <canvas id="radarChart"></canvas>
      </div>
      <div class="feature-bars">
        <div class="feature-item"><div class="feature-label">Energy</div><div class="feature-val">{e*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{e*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Danceability</div><div class="feature-val">{d*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{d*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Valence</div><div class="feature-val">{v*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(v*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Acousticness</div><div class="feature-val">{a*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{a*100:.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Instrumentalness</div><div class="feature-val">{ins*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(ins*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Speechiness</div><div class="feature-val">{sp*100:.1f}%</div><div class="feature-track"><div class="feature-fill" style="width:{max(sp*100,2):.0f}%"></div></div></div>
        <div class="feature-item"><div class="feature-label">Loudness</div><div class="feature-val">{loud:.1f} dB</div><div class="feature-track"><div class="feature-fill" style="width:{loud_pct(loud):.0f}%"></div></div></div>
      </div>
    </div>
  </div>

  <div class="section-label"><h2>Prompt Lab</h2></div>
  <div class="prompt-lab">
    <div class="prompt-lab-intro">
      <h3>&#x1f9ea; Recreate This Track</h3>
      <p>Use these prompt ingredients with <strong>Suno</strong>, <strong>Udio</strong>, or any AI music generation service to recreate the vibe of <em>{esc(name)}</em> by <em>{esc(artist)}</em>.</p>
    </div>

    <div class="prompt-tabs">
      <button class="prompt-tab active" onclick="switchTab(this,'general')">General</button>
      <button class="prompt-tab" onclick="switchTab(this,'suno')">Suno</button>
      <button class="prompt-tab" onclick="switchTab(this,'udio')">Udio</button>
      <button class="prompt-tab" onclick="switchTab(this,'agent')">Agent JSON</button>
    </div>

    <div class="prompt-card prompt-card-main prompt-panel" id="panel-general">
      <div class="prompt-card-header">
        <span class="prompt-card-label">Ready-to-Use Prompt</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptGeneral">Copy</button>
      </div>
      <div class="prompt-text" id="promptGeneral">{esc(gen_prompt)}</div>
    </div>

    <div class="prompt-card prompt-card-main prompt-panel" id="panel-suno" style="display:none">
      <div class="prompt-card-header">
        <span class="prompt-card-label">Suno Style Tags</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptSuno">Copy</button>
      </div>
      <div class="prompt-hint">Paste into the <strong>Style of Music</strong> field. Set BPM to {tempo:.0f}.</div>
      <div class="prompt-text" id="promptSuno">{esc(suno_prompt)}</div>
    </div>

    <div class="prompt-card prompt-card-main prompt-panel" id="panel-udio" style="display:none">
      <div class="prompt-card-header">
        <span class="prompt-card-label">Udio Prompt</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptUdio">Copy</button>
      </div>
      <div class="prompt-hint">Use manual mode to set BPM ({tempo:.0f}) and key ({esc(key_mode)}).</div>
      <div class="prompt-text" id="promptUdio">{esc(udio_prompt)}</div>
    </div>

    <div class="prompt-card prompt-card-main prompt-panel" id="panel-agent" style="display:none">
      <div class="prompt-card-header">
        <span class="prompt-card-label">Structured Data for Agents</span>
        <button class="copy-btn" onclick="copyPrompt(this)" data-target="promptAgent">Copy</button>
      </div>
      <pre class="prompt-code" id="promptAgent">{esc(agent_json)}</pre>
    </div>
  </div>
</div>

<footer>
  <div class="container">
    <p>Data from Spotify audio features. <a href="/genres/{esc(genre)}/">&larr; Back to {esc(gdisp)}</a></p>
    <p style="margin-top:0.3rem"><a href="/">kapiko.ai</a></p>
  </div>
</footer>

<script>
const ctx=document.getElementById('radarChart');
if(ctx){{new Chart(ctx,{{type:'radar',data:{{labels:['Energy','Danceability','Valence','Acousticness','Instrumentalness','Speechiness'],datasets:[{{data:[{e},{d},{v},{a},{ins},{sp}],backgroundColor:'rgba(78,205,196,0.15)',borderColor:'#4ecdc4',borderWidth:2,pointBackgroundColor:'#4ecdc4',pointRadius:4}}]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{r:{{beginAtZero:true,max:1,ticks:{{display:false}},grid:{{color:'rgba(255,255,255,0.06)'}},pointLabels:{{color:'#6b7099',font:{{size:11}}}},angleLines:{{color:'rgba(255,255,255,0.06)'}}}}}}}}}})}};
function copyPrompt(btn){{const id=btn.getAttribute('data-target');const text=document.getElementById(id).textContent;navigator.clipboard.writeText(text).then(()=>{{btn.textContent='Copied!';btn.style.background='rgba(78,205,196,0.3)';setTimeout(()=>{{btn.textContent='Copy';btn.style.background=''}},2000)}})}}
function switchTab(btn,panel){{document.querySelectorAll('.prompt-tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.prompt-panel').forEach(p=>p.style.display='none');btn.classList.add('active');const el=document.getElementById('panel-'+panel);if(el)el.style.display=''}}
</script>
</body>
</html>'''

def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 999999
    
    # Collect all unique songs across all genres
    all_songs = {}  # slug -> (track_data, genre)
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
            html = make_page(t, g)
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
