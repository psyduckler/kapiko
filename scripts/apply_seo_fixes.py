#!/usr/bin/env python3
"""
Apply SEO/AEO fixes to all 118 kapiko genre pages.
"""

import os
import re
import json
import glob
from pathlib import Path

SITE_DIR = Path("/Users/psy/kapiko-site/site/genres")

# ── Related genres mapping ──────────────────────────────────────────────────
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

# ── Key names mapping ────────────────────────────────────────────────────────
KEY_NAMES = {
    "C": "C major", "C#/Db": "C♯/D♭ major", "D": "D major",
    "D#/Eb": "D♯/E♭ major", "E": "E major", "F": "F major",
    "F#/Gb": "F♯/G♭ major", "G": "G major", "G#/Ab": "G♯/A♭ major",
    "A": "A major", "A#/Bb": "A♯/B♭ major", "B": "B major",
}


def get_related_genres(slug: str) -> list[tuple[str, str]]:
    """Return list of (slug, display_name) for related genres, filtering out ones that don't exist."""
    related = RELATED_MAP.get(slug, [])
    if not related:
        # Fall back: pick some common genres
        related = ["electronic", "ambient", "pop", "indie", "chill"]
        related = [r for r in related if r != slug][:4]

    # Filter to genres that actually exist in the site
    existing = set(os.listdir(SITE_DIR))
    result = []
    for r in related:
        if r in existing and r != slug:
            # Make display name from slug
            display = r.replace("-", " ").title()
            display = display.replace("R N B", "R&B").replace("J Pop", "J-Pop").replace("K Pop", "K-Pop").replace("Edm", "EDM")
            result.append((r, display))
    return result[:5]


def extract_stats(analysis: dict) -> dict:
    """Extract key stats from analysis.json for FAQ schema."""
    stats = {}

    # BPM
    bpm = analysis.get("bpm", {})
    stats["median_bpm"] = round(bpm.get("median", 0), 1)
    stats["std_bpm"] = round(bpm.get("stdev", 0), 1)
    # BPM range (25th-75th percentile approx from raw)
    raw_bpm = bpm.get("raw", [])
    if raw_bpm:
        raw_sorted = sorted(raw_bpm)
        n = len(raw_sorted)
        stats["bpm_low"] = round(raw_sorted[n // 4], 1)
        stats["bpm_high"] = round(raw_sorted[3 * n // 4], 1)
    else:
        stats["bpm_low"] = max(0, round(stats["median_bpm"] - stats["std_bpm"], 1))
        stats["bpm_high"] = round(stats["median_bpm"] + stats["std_bpm"], 1)

    # Key
    key_dist = analysis.get("key_distribution", {})
    if key_dist:
        top_key = max(key_dist, key=key_dist.get)
        stats["top_key"] = top_key
    else:
        stats["top_key"] = "C"

    # Mode
    mode_dist = analysis.get("mode_distribution", {})
    major_count = mode_dist.get("Major", 0)
    total = sum(mode_dist.values()) if mode_dist else 100
    stats["major_pct"] = round(100 * major_count / total) if total else 74

    # Energy
    energy = analysis.get("energy", {})
    stats["energy"] = round(energy.get("median", energy.get("mean", 0.5)) * 100)

    # Valence
    valence = analysis.get("valence", {})
    stats["valence"] = round(valence.get("median", valence.get("mean", 0.5)) * 100)

    return stats


def build_nav() -> str:
    return '''\n<nav style="background:rgba(11,12,26,0.95);border-bottom:1px solid rgba(255,255,255,0.07);padding:12px 28px;position:sticky;top:0;z-index:100;backdrop-filter:blur(12px)">\n  <div style="max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between">\n    <a href="/" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase">kapiko</a>\n    <div style="display:flex;gap:24px;align-items:center">\n      <a href="/genres/" style="color:#6b7099;text-decoration:none;font-size:13px;font-weight:500;transition:color 0.2s" onmouseover="this.style.color=\'#dde1f0\'" onmouseout="this.style.color=\'#6b7099\'">Genres</a>\n      <a href="/songs/" style="color:#6b7099;text-decoration:none;font-size:13px;font-weight:500;transition:color 0.2s" onmouseover="this.style.color=\'#dde1f0\'" onmouseout="this.style.color=\'#6b7099\'">Songs</a>\n    </div>\n  </div>\n</nav>\n'''


def build_breadcrumb(genre_name: str) -> str:
    return f'''\n    <nav aria-label="Breadcrumb" style="margin-bottom:16px;font-size:12px">\n      <a href="/" style="color:#6b7099;text-decoration:none">kapiko</a>\n      <span style="color:#3d4060;margin:0 6px">›</span>\n      <a href="/genres/" style="color:#6b7099;text-decoration:none">Genres</a>\n      <span style="color:#3d4060;margin:0 6px">›</span>\n      <span style="color:#dde1f0">{genre_name}</span>\n    </nav>\n'''


def build_intro(genre_name: str) -> str:
    g = genre_name.lower()
    return f'''\n    <p style="font-size:14px;color:#6b7099;line-height:1.7;margin-top:28px;max-width:700px">A data-driven breakdown of {g} music based on Spotify audio features and Gemini AI analysis of the top 100 tracks. Use these insights to understand what makes {g} music sound the way it does — and to generate your own.</p>\n    <a href="#prompt-lab" style="display:inline-flex;align-items:center;gap:6px;margin-top:16px;padding:10px 20px;background:rgba(78,205,196,0.1);border:1px solid rgba(78,205,196,0.25);border-radius:8px;color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:600;letter-spacing:0.03em;transition:background 0.2s" onmouseover="this.style.background=\'rgba(78,205,196,0.2)\'" onmouseout="this.style.background=\'rgba(78,205,196,0.1)\'">Jump to Prompt Lab ↓</a>\n'''


def build_toc() -> str:
    return '''  <nav aria-label="Table of contents" style="margin-bottom:36px;padding:20px 24px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:14px">
    <div style="font-size:10.5px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:#6b7099;margin-bottom:12px">On This Page</div>
    <div style="display:flex;flex-wrap:wrap;gap:8px 20px">
      <a href="#audio-dna" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Audio DNA</a>
      <a href="#prompt-lab" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Prompt Lab</a>
      <a href="#rhythm-tonality" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Rhythm &amp; Tonality</a>
      <a href="#ai-analysis" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">AI Audio Analysis</a>
      <a href="#emotional" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Emotional Fingerprint</a>
      <a href="#top-artists" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Top Artists</a>
      <a href="#hit-factors" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">What Makes a Hit</a>
      <a href="#correlations" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Feature Correlations</a>
      <a href="#production" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Production Profile</a>
      <a href="#top-tracks" style="color:#4ecdc4;text-decoration:none;font-size:13px;font-weight:500">Top Tracks</a>
    </div>
  </nav>\n'''


def build_schema(genre_name: str, slug: str, stats: dict) -> str:
    g = genre_name.lower()
    top_key_display = stats["top_key"]
    breadcrumb = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "kapiko", "item": "https://kapiko.ai/"},
            {"@type": "ListItem", "position": 2, "name": "Genres", "item": "https://kapiko.ai/genres/"},
            {"@type": "ListItem", "position": 3, "name": genre_name}
        ]
    }, indent=2)

    faq = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"What BPM is {g} music?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Based on analysis of the top 100 {g} tracks on Spotify, the median BPM is {stats['median_bpm']} with a standard deviation of {stats['std_bpm']}. The typical range falls between {stats['bpm_low']} and {stats['bpm_high']} BPM."
                }
            },
            {
                "@type": "Question",
                "name": f"What key is {g} music usually in?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"The most common key in {g} music is {top_key_display}, and {stats['major_pct']}% of tracks are in a major key."
                }
            },
            {
                "@type": "Question",
                "name": f"How do I make {g} music with AI?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Use AI music generators like Suno or Udio with genre-specific prompts. Key parameters for {g}: BPM around {stats['median_bpm']}, energy level around {stats['energy']}%, and valence around {stats['valence']}%. Visit the Prompt Lab section on this page for a ready-to-copy prompt template."
                }
            }
        ]
    }, indent=2)

    return f'\n<script type="application/ld+json">\n{breadcrumb}\n</script>\n<script type="application/ld+json">\n{faq}\n</script>\n'


def build_related(related: list[tuple[str, str]]) -> str:
    if not related:
        return ""
    links = "\n".join(
        f'    <a href="/genres/{slug}/" style="display:inline-block;padding:8px 18px;background:rgba(155,127,212,0.08);border:1px solid rgba(155,127,212,0.2);border-radius:20px;color:#9b7fd4;text-decoration:none;font-size:13px;font-weight:500;transition:background 0.2s" onmouseover="this.style.background=\'rgba(155,127,212,0.16)\'" onmouseout="this.style.background=\'rgba(155,127,212,0.08)\'">{name}</a>'
        for slug, name in related
    )
    return f'  <div class="section-label" id="related"><h2>Related Genres</h2></div>\n  <div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:32px">\n{links}\n  </div>\n'


def build_methodology(genre_name: str) -> str:
    g = genre_name.lower()
    return f'''  <div class="section-label" id="methodology"><h2>Sources &amp; Methodology</h2></div>
  <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:24px 28px;margin-bottom:8px">
    <p style="font-size:13.5px;color:#6b7099;line-height:1.7;margin-bottom:12px">This analysis is based on Spotify Audio Features API data for the top 100 {g} tracks by popularity, supplemented by Gemini AI audio analysis of 30-second preview clips.</p>
    <p style="font-size:13.5px;color:#6b7099;line-height:1.7;margin-bottom:12px">Audio features (energy, valence, acousticness, instrumentalness, danceability, speechiness, tempo, key, mode, loudness, duration) are sourced directly from Spotify\'s audio analysis pipeline. Production insights, mood classifications, and instrumentation details are generated by Gemini AI.</p>
    <p style="font-size:13.5px;color:#6b7099;line-height:1.7">Data was collected and analyzed by <a href="https://kapiko.ai" style="color:#4ecdc4;text-decoration:none">kapiko</a> — a music analytics platform for AI-era music production.</p>
  </div>
'''


def apply_section_ids(html: str) -> str:
    """Add id attributes to section-label divs."""
    replacements = [
        ('<div class="section-label"><h2>Audio DNA</h2></div>', '<div class="section-label" id="audio-dna"><h2>Audio DNA</h2></div>'),
        ('<div class="section-label"><h2>Rhythm &amp; Tonality</h2></div>', '<div class="section-label" id="rhythm-tonality"><h2>Rhythm &amp; Tonality</h2></div>'),
        ('<div class="section-label"><h2>AI Audio Analysis</h2></div>', '<div class="section-label" id="ai-analysis"><h2>AI Audio Analysis</h2></div>'),
        ('<div class="section-label"><h2>Emotional Fingerprint</h2></div>', '<div class="section-label" id="emotional"><h2>Emotional Fingerprint</h2></div>'),
        ('<div class="section-label"><h2>Top Artists</h2></div>', '<div class="section-label" id="top-artists"><h2>Top Artists</h2></div>'),
        ('<div class="section-label"><h2>What Makes a Hit</h2></div>', '<div class="section-label" id="hit-factors"><h2>What Makes a Hit</h2></div>'),
        ('<div class="section-label"><h2>Feature Correlations</h2></div>', '<div class="section-label" id="correlations"><h2>Feature Correlations</h2></div>'),
        ('<div class="section-label"><h2>Production Profile</h2></div>', '<div class="section-label" id="production"><h2>Production Profile</h2></div>'),
        ('<div class="section-label"><h2>Top Tracks</h2></div>', '<div class="section-label" id="top-tracks"><h2>Top Tracks</h2></div>'),
        # Prompt Lab with emoji
        ('<div class="section-label"><h2>✨ Prompt Lab</h2></div>', '<div class="section-label" id="prompt-lab"><h2>Prompt Lab</h2></div>'),
        # Prompt Lab without emoji (just in case)
        ('<div class="section-label"><h2>Prompt Lab</h2></div>', '<div class="section-label" id="prompt-lab"><h2>Prompt Lab</h2></div>'),
    ]
    for old, new in replacements:
        html = html.replace(old, new)
    return html


def process_genre(genre_dir: Path) -> bool:
    slug = genre_dir.name
    html_path = genre_dir / "index.html"
    json_path = genre_dir / "analysis.json"

    if not html_path.exists():
        print(f"  SKIP {slug}: no index.html")
        return False

    # Read files
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Skip if already processed (check for our nav marker)
    if 'backdrop-filter:blur(12px)' in html:
        print(f"  SKIP {slug}: already processed")
        return False

    # Load analysis.json
    stats = {"median_bpm": 120, "std_bpm": 20, "bpm_low": 100, "bpm_high": 140,
             "top_key": "C", "major_pct": 70, "energy": 50, "valence": 50}
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                analysis = json.load(f)
            stats = extract_stats(analysis)
        except Exception as e:
            print(f"  WARN {slug}: failed to read analysis.json: {e}")

    # Extract genre display name from h1
    h1_match = re.search(r'<h1>([^<]+)</h1>', html)
    if not h1_match:
        print(f"  SKIP {slug}: no h1 found")
        return False
    genre_name = h1_match.group(1).strip()
    g_lower = genre_name.lower()

    # ── 1. Meta tags ────────────────────────────────────────────────────────
    meta_block = f'''<meta name="description" content="{genre_name} music decoded: BPM, key, energy, mood &amp; production analysis of Spotify&#39;s top 100 {g_lower} tracks. Copy-paste AI prompts for Suno, Udio &amp; more.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://kapiko.ai/genres/{slug}/">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{genre_name} Music: Audio Features, Prompt Guide &amp; Production DNA — kapiko">
  <meta property="og:description" content="{genre_name} music decoded: BPM, key, energy, mood &amp; production analysis of Spotify&#39;s top 100 {g_lower} tracks.">
  <meta property="og:url" content="https://kapiko.ai/genres/{slug}/">
  <meta property="og:site_name" content="kapiko">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{genre_name} Music: Audio Features, Prompt Guide &amp; Production DNA — kapiko">
  <meta name="twitter:description" content="{genre_name} music decoded: BPM, key, energy, mood &amp; production analysis of Spotify&#39;s top 100 {g_lower} tracks.">
  '''

    html = html.replace(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f'<meta name="viewport" content="width=device-width, initial-scale=1.0">\n  {meta_block}'
    )

    # ── 2. Title tag ────────────────────────────────────────────────────────
    old_title_pattern = re.compile(r'<title>[^<]+ — kapiko music analytics</title>')
    new_title = f'<title>{genre_name} Music: Audio Features, AI Prompt Guide &amp; Production DNA — kapiko</title>'
    html = old_title_pattern.sub(new_title, html)

    # ── 3. Visually hidden H1 subtitle ─────────────────────────────────────
    h1_tag = f'<h1>{genre_name}</h1>'
    subtitle_hidden = f'<h1>{genre_name}</h1>\n    <p class="subtitle-seo" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap">{genre_name} Music Genre Analysis: Audio Features, AI Prompts &amp; Production Profile</p>'
    html = html.replace(h1_tag, subtitle_hidden, 1)

    # ── 4. Navigation bar ───────────────────────────────────────────────────
    html = html.replace('<body>\n', '<body>\n' + build_nav(), 1)

    # ── 5. Breadcrumbs ──────────────────────────────────────────────────────
    html = html.replace(
        '  <div class="header-inner">\n    <div class="brand">',
        f'  <div class="header-inner">\n{build_breadcrumb(genre_name)}    <div class="brand">'
    )

    # ── 6. Intro paragraph + Jump link ──────────────────────────────────────
    # Add after </div> that closes stat-cards div, before </div> that closes header-inner
    # Pattern: the stat-cards closing </div> then a newline then header-inner closing </div>
    html = html.replace(
        '    </div>\n  </div>\n</header>',
        f'    </div>\n{build_intro(genre_name)}  </div>\n</header>',
        1
    )

    # ── 7 & 9. Section IDs (including Prompt Lab emoji removal) ─────────────
    html = apply_section_ids(html)

    # ── 8. Table of contents ─────────────────────────────────────────────────
    # Insert ToC right after <main> opening
    html = html.replace('<main>\n\n  <!-- Section: Audio DNA -->', f'<main>\n\n{build_toc()}  <!-- Section: Audio DNA -->', 1)
    # Fallback if no comment
    if build_toc() not in html:
        html = html.replace('<main>\n', f'<main>\n\n{build_toc()}', 1)

    # ── 10. BreadcrumbList + FAQPage schema ──────────────────────────────────
    schema_block = build_schema(genre_name, slug, stats)
    html = html.replace('</head>', f'{schema_block}</head>', 1)

    # ── 11 & 12. Related genres + Methodology before </main> ─────────────────
    related = get_related_genres(slug)
    related_block = build_related(related)
    methodology_block = build_methodology(genre_name)

    html = html.replace('</main>', f'\n{related_block}\n{methodology_block}</main>', 1)

    # Write back
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return True


def main():
    genre_dirs = sorted([d for d in SITE_DIR.iterdir() if d.is_dir()])
    total = len(genre_dirs)
    processed = 0
    skipped = 0

    print(f"Processing {total} genres...")

    for genre_dir in genre_dirs:
        result = process_genre(genre_dir)
        if result:
            processed += 1
            print(f"  ✓ {genre_dir.name}")
        else:
            skipped += 1

    print(f"\nDone! Processed: {processed}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
