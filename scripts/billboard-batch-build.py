#!/usr/bin/env python3
"""
Billboard Song Page Batch Builder
Builds kapiko.ai song pages from Billboard Year-End Hot 100 data.
Designed to run as a cron job — processes N songs per run, skips duplicates,
updates sitemap.xml, and git pushes.

Usage:
  python3 billboard-batch-build.py [--batch-size 100] [--dry-run] [--no-push]
"""

import json, os, re, sys, base64, time, shutil, subprocess, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

# ── Config ─────────────────────────────────────────────────────────────────
BATCH_SIZE = 100
SITE = Path.home() / 'kapiko-site' / 'site'
SONGS_DIR = SITE / 'songs'
SCRIPTS_DIR = Path.home() / 'kapiko-site' / 'scripts'
BILLBOARD_JSON = Path.home() / 'kapiko-site' / 'top-100-by-year-2000-2020.json'
PROGRESS_FILE = Path.home() / 'kapiko-site' / 'data' / 'billboard-batch-progress.json'
SITEMAP_FILE = SITE / 'sitemap.xml'
LOG_FILE = Path('/tmp/billboard-batch-build.log')

KEY_NAMES = {0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',7:'G',8:'G#',9:'A',10:'A#',11:'B'}

# Genre assignment based on artist/era heuristics
ARTIST_GENRES = {
    'destiny\'s child': 'r-n-b', 'alicia keys': 'r-n-b', 'usher': 'r-n-b',
    'beyoncé': 'r-n-b', 'beyonce': 'r-n-b', 'rihanna': 'pop', 'chris brown': 'r-n-b',
    'nelly': 'hip-hop', 'eminem': 'hip-hop', 'jay-z': 'hip-hop', '50 cent': 'hip-hop',
    'kanye west': 'hip-hop', 'lil wayne': 'hip-hop', 'drake': 'hip-hop',
    'madonna': 'pop', 'britney spears': 'pop', 'christina aguilera': 'pop',
    'justin timberlake': 'pop', 'katy perry': 'pop', 'lady gaga': 'pop',
    'taylor swift': 'pop', 'adele': 'pop', 'bruno mars': 'pop', 'ed sheeran': 'pop',
    'the weeknd': 'r-n-b', 'post malone': 'hip-hop', 'ariana grande': 'pop',
    'maroon 5': 'pop', 'onerepublic': 'pop', 'train': 'pop',
    'nickelback': 'rock', 'creed': 'rock', 'linkin park': 'rock',
    'three doors down': 'rock', '3 doors down': 'rock', 'matchbox twenty': 'alt-rock',
    'lifehouse': 'alt-rock', 'foo fighters': 'rock', 'green day': 'rock',
    'coldplay': 'alt-rock', 'imagine dragons': 'rock',
    'tim mcgraw': 'country', 'carrie underwood': 'country', 'keith urban': 'country',
    'jason aldean': 'country', 'luke bryan': 'country', 'florida georgia line': 'country',
    'outkast': 'hip-hop', 'ludacris': 'hip-hop', 't.i.': 'hip-hop',
    'sean paul': 'dancehall', 'shakira': 'latin', 'daddy yankee': 'reggaeton',
    'pitbull': 'latin', 'j balvin': 'reggaeton', 'bad bunny': 'reggaeton',
    'john legend': 'r-n-b', 'ne-yo': 'r-n-b', 'akon': 'r-n-b',
    'black eyed peas': 'pop', 'the black eyed peas': 'pop',
    'flo rida': 'hip-hop', 'jason derulo': 'pop', 'meghan trainor': 'pop',
    'sam smith': 'pop', 'sia': 'pop', 'halsey': 'pop', 'dua lipa': 'pop',
    'billie eilish': 'pop', 'lizzo': 'pop', 'lil nas x': 'hip-hop',
    'cardi b': 'hip-hop', 'migos': 'hip-hop', 'travis scott': 'hip-hop',
    'kendrick lamar': 'hip-hop', 'j. cole': 'hip-hop', 'future': 'hip-hop',
    'twenty one pilots': 'alt-rock', 'panic! at the disco': 'rock',
    'fall out boy': 'rock', 'paramore': 'rock', 'my chemical romance': 'rock',
}

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def primary_artist(artist_str):
    for sep in [' featuring ', ' feat.', ' feat ', ' ft.', ' ft ', ' Featuring ',
                ' Feat.', ' Feat ', ' x ', ' X ', ' & ', ' with ', ' With ', ',']:
        if sep in artist_str:
            return artist_str.split(sep)[0].strip()
    return artist_str.strip()

def make_slug(title, artist):
    primary = primary_artist(artist)
    text = f'{title}-{primary}'.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text

def guess_genre(artist):
    artist_lower = primary_artist(artist).lower()
    for key, genre in ARTIST_GENRES.items():
        if key in artist_lower:
            return genre
    return 'pop'  # Default

def get_spotify_token():
    cid = subprocess.check_output(['security','find-generic-password','-s','spotify-client-id','-w']).decode().strip()
    sec = subprocess.check_output(['security','find-generic-password','-s','spotify-client-secret','-w']).decode().strip()
    auth_b64 = base64.b64encode(f"{cid}:{sec}".encode()).decode()
    req = urllib.request.Request('https://accounts.spotify.com/api/token',
        data=urllib.parse.urlencode({'grant_type':'client_credentials'}).encode(),
        headers={'Authorization': f'Basic {auth_b64}', 'Content-Type':'application/x-www-form-urlencoded'})
    return json.loads(urllib.request.urlopen(req).read())['access_token']

def spotify_search(token, title, artist):
    """Search Spotify for track metadata (name, album, duration, art)."""
    q = urllib.parse.quote(f'track:{title} artist:{artist}')
    req = urllib.request.Request(
        f'https://api.spotify.com/v1/search?q={q}&type=track&limit=1',
        headers={'Authorization': f'Bearer {token}'})
    try:
        data = json.loads(urllib.request.urlopen(req).read())
        items = data.get('tracks', {}).get('items', [])
        if not items:
            return None
        t = items[0]
        return {
            'name': t['name'],
            'artists': ', '.join(a['name'] for a in t['artists']),
            'album': t['album']['name'],
            'duration_ms': t['duration_ms'],
            'album_art': t['album']['images'][0]['url'] if t['album'].get('images') else '',
            'spotify_id': t['id'],
        }
    except Exception as e:
        log(f"  Spotify search failed for {title}: {e}")
        return None

def gemini_audio_features(title, artist):
    """Use Gemini to estimate Spotify-style audio features."""
    api_key = subprocess.check_output(['security','find-generic-password','-s','google-api-key','-w']).decode().strip()
    
    prompt = f"""For the song "{title}" by {artist}, estimate Spotify-style audio features.
Return ONLY a JSON object with these exact keys and value types:
- tempo (float, BPM)
- key (string, note name: C, C#, D, D#, E, F, F#, G, G#, A, A#, B)
- mode (string, "Major" or "Minor")
- energy (float, 0.0-1.0)
- valence (float, 0.0-1.0)
- danceability (float, 0.0-1.0)
- acousticness (float, 0.0-1.0)
- instrumentalness (float, 0.0-1.0)
- speechiness (float, 0.0-1.0)
- loudness (float, dB, typically -3 to -20)
- liveness (float, 0.0-1.0)
No explanation, just the JSON object."""

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }).encode()
    
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
        data=payload,
        headers={"Content-Type": "application/json"})
    
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
        text = resp['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        log(f"  Gemini failed for {title}: {e}")
    return None

def load_progress():
    if PROGRESS_FILE.exists():
        return json.load(open(PROGRESS_FILE))
    return {"completed_slugs": [], "last_run": None, "total_created": 0}

def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump(progress, open(PROGRESS_FILE, 'w'), indent=2)

def add_to_sitemap(slugs):
    """Add new song URLs to sitemap.xml."""
    if not slugs:
        return
    
    content = SITEMAP_FILE.read_text(encoding='utf-8')
    # Remove closing tag
    content = content.rstrip()
    if content.endswith('</urlset>'):
        content = content[:-len('</urlset>')].rstrip()
    
    # Add new URLs
    for slug in slugs:
        url = f'https://kapiko.ai/songs/{slug}/'
        if url not in content:
            content += f'\n  <url><loc>{url}</loc></url>'
    
    content += '\n</urlset>\n'
    SITEMAP_FILE.write_text(content, encoding='utf-8')

def git_push(message):
    """Stage, commit, and push changes."""
    os.chdir(Path.home() / 'kapiko-site')
    subprocess.run(['git', 'add', '-A'], check=True)
    result = subprocess.run(['git', 'diff', '--cached', '--quiet'])
    if result.returncode == 0:
        log("Nothing to commit")
        return False
    subprocess.run(['git', 'commit', '-m', message], check=True)
    # Pull rebase first to avoid conflicts
    subprocess.run(['git', 'pull', '--rebase'], check=True)
    subprocess.run(['git', 'push'], check=True)
    return True

def main():
    args = sys.argv[1:]
    batch_size = BATCH_SIZE
    dry_run = '--dry-run' in args
    no_push = '--no-push' in args
    
    for i, a in enumerate(args):
        if a == '--batch-size' and i+1 < len(args):
            batch_size = int(args[i+1])
    
    log(f"=== Billboard Batch Build — {batch_size} songs {'(DRY RUN)' if dry_run else ''} ===")
    
    # Load billboard data
    billboard = json.load(open(BILLBOARD_JSON))
    
    # Load progress
    progress = load_progress()
    completed_set = set(progress['completed_slugs'])
    
    # Get existing song pages on disk
    existing_pages = set(os.listdir(SONGS_DIR)) if SONGS_DIR.exists() else set()
    
    # Build queue: all Billboard songs, ordered by year then rank
    queue = []
    for year in sorted(billboard['years'].keys()):
        for track in billboard['years'][year]:
            slug = make_slug(track['title'], track['artist'])
            # Skip if page already exists OR already completed in a prior run
            if slug in existing_pages or slug in completed_set:
                continue
            queue.append({
                'title': track['title'],
                'artist': track['artist'],
                'rank': track['rank'],
                'year': int(year),
                'slug': slug,
            })
    
    log(f"Queue: {len(queue)} songs remaining out of 2,100")
    
    if not queue:
        log("All songs have been processed!")
        return
    
    batch = queue[:batch_size]
    log(f"Processing batch of {len(batch)} songs (years {batch[0]['year']}-{batch[-1]['year']})")
    
    # Get Spotify token
    try:
        spotify_token = get_spotify_token()
        log("Spotify authenticated")
    except Exception as e:
        log(f"Spotify auth failed: {e}")
        spotify_token = None
    
    # Import page generator
    sys.path.insert(0, str(SCRIPTS_DIR))
    import generate_song_pages as gen
    gen.SITE = SITE
    
    # Load all existing genre data for similar songs feature
    all_genres_data = {}
    for g in gen.GENRES:
        apath = SITE / 'genres' / g / 'analysis.json'
        if apath.exists():
            try:
                all_genres_data[g] = json.load(open(apath))
            except:
                continue
    
    created_slugs = []
    errors = 0
    
    for i, song in enumerate(batch):
        slug = song['slug']
        song_dir = SONGS_DIR / slug
        
        # Double-check no duplicate
        if song_dir.exists() and (song_dir / 'index.html').exists():
            log(f"  SKIP (exists): {slug}")
            completed_set.add(slug)
            continue
        
        log(f"  [{i+1}/{len(batch)}] {song['title']} — {primary_artist(song['artist'])} ({song['year']} #{song['rank']})")
        
        # 1. Spotify metadata
        spotify_data = None
        if spotify_token:
            spotify_data = spotify_search(spotify_token, song['title'], primary_artist(song['artist']))
            time.sleep(0.1)  # Rate limit courtesy
        
        # 2. Gemini audio features
        features = gemini_audio_features(song['title'], primary_artist(song['artist']))
        if not features:
            log(f"    ⚠️ No audio features — skipping")
            errors += 1
            continue
        time.sleep(0.15)  # Gemini rate limit
        
        # 3. Build track object for generator
        genre = guess_genre(song['artist'])
        track_data = {
            'name': spotify_data['name'] if spotify_data else song['title'],
            'artists': spotify_data['artists'] if spotify_data else song['artist'],
            'album': spotify_data.get('album', '') if spotify_data else '',
            'popularity': 75,  # Billboard songs are popular by definition
            'tempo': features.get('tempo', 120),
            'key': features.get('key', 'C'),
            'mode': features.get('mode', 'Major'),
            'energy': features.get('energy', 0.5),
            'valence': features.get('valence', 0.5),
            'danceability': features.get('danceability', 0.5),
            'acousticness': features.get('acousticness', 0.5),
            'instrumentalness': features.get('instrumentalness', 0.0),
            'loudness': features.get('loudness', -8.0),
            'speechiness': features.get('speechiness', 0.05),
            'liveness': features.get('liveness', 0.1),
            'duration_ms': spotify_data.get('duration_ms', 210000) if spotify_data else 210000,
            'slug': slug,
            'album_art': spotify_data.get('album_art', '') if spotify_data else '',
        }
        
        # 4. Generate page
        if dry_run:
            log(f"    DRY RUN: would create {slug}")
            created_slugs.append(slug)
            completed_set.add(slug)
            continue
        
        try:
            html = gen.make_page(track_data, genre, all_genres_data)
            song_dir.mkdir(parents=True, exist_ok=True)
            (song_dir / 'index.html').write_text(html, encoding='utf-8')
            created_slugs.append(slug)
            completed_set.add(slug)
            log(f"    ✅ Created ({len(html):,} bytes)")
        except Exception as e:
            log(f"    ❌ Error: {e}")
            errors += 1
    
    # Update sitemap
    if created_slugs and not dry_run:
        add_to_sitemap(created_slugs)
        log(f"Sitemap updated with {len(created_slugs)} new URLs")
    
    # Save progress
    progress['completed_slugs'] = sorted(completed_set)
    progress['last_run'] = datetime.now(timezone.utc).isoformat()
    progress['total_created'] = progress.get('total_created', 0) + len(created_slugs)
    save_progress(progress)
    
    # Git push
    if created_slugs and not dry_run and not no_push:
        try:
            years_range = f"{batch[0]['year']}-{batch[-1]['year']}"
            msg = f"Add {len(created_slugs)} Billboard song pages (batch: {years_range})"
            if git_push(msg):
                log(f"Pushed: {msg}")
            else:
                log("Nothing to push")
        except Exception as e:
            log(f"Git push failed: {e}")
    
    log(f"\n=== Summary ===")
    log(f"Created: {len(created_slugs)}")
    log(f"Errors: {errors}")
    log(f"Remaining: {len(queue) - len(batch)}")
    log(f"Total all-time: {progress['total_created']}")

if __name__ == '__main__':
    main()
