#!/bin/bash
# kapiko-overlay.sh — Add text overlay to kapiko YouTube videos + upload
#
# Usage:
#   ./scripts/kapiko-overlay.sh <audio_file> "<song_name>" [--upload]
#
# Album name "A Tapestry of Solitude" and artist "kapiko" are hardcoded.
# Uses capybara-looped-clean.mp4 as the base loop (no baked-in text).
#
# Layout:
#   Bottom-left:  Album name (24pt, black box) + Song name (36pt, black box)
#   Bottom-right:  kapiko (33pt, shadow only, no box)
#
# Examples:
#   ./scripts/kapiko-overlay.sh song.mp3 "Iron Will, Shattered Dawn"
#   ./scripts/kapiko-overlay.sh song.mp3 "Fallen Leaves" --upload

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"

AUDIO="${1:?Usage: kapiko-overlay.sh <audio_file> \"song name\" [--upload]}"
SONG_NAME="${2:?Missing song name}"
UPLOAD="${3:-}"

ALBUM_NAME="A Tapestry of Solitude"
ARTIST="kapiko"
LOOP_VIDEO="${WORKSPACE}/capybara-looped-clean.mp4"
SLUG=$(echo "$SONG_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ,' '-' | tr -s '-')
OUTPUT="${WORKSPACE}/kapiko-${SLUG}.mp4"

PACIFICO="/Users/psy/Library/Fonts/Pacifico-Regular.ttf"

# Temp files for textfile approach
SONG_FILE=$(mktemp /tmp/kapiko-song-XXXXXX.txt)
ALBUM_FILE=$(mktemp /tmp/kapiko-album-XXXXXX.txt)
ARTIST_FILE=$(mktemp /tmp/kapiko-artist-XXXXXX.txt)
trap "rm -f $SONG_FILE $ALBUM_FILE $ARTIST_FILE" EXIT

echo -n "$SONG_NAME" > "$SONG_FILE"
echo -n "$ALBUM_NAME" > "$ALBUM_FILE"
echo -n "$ARTIST" > "$ARTIST_FILE"

AUDIO_DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$AUDIO")
AUDIO_DURATION_INT=$(printf "%.0f" "$AUDIO_DURATION")

echo "🎵 ${ARTIST} — ${ALBUM_NAME} — ${SONG_NAME}"
echo "⏱  Duration: ${AUDIO_DURATION_INT}s"
echo "💾 Output: ${OUTPUT}"

ffmpeg -y \
  -stream_loop -1 -i "$LOOP_VIDEO" \
  -i "$AUDIO" \
  -filter_complex "
    [0:v]drawtext=textfile=${ALBUM_FILE}:fontfile=${PACIFICO}:fontsize=24:fontcolor=white@0.9:x=50:y=h-145:shadowcolor=black@0.3:shadowx=1:shadowy=1:box=1:boxcolor=black@0.8:boxborderw=8,
    drawtext=textfile=${SONG_FILE}:fontfile=${PACIFICO}:fontsize=36:fontcolor=white@0.95:x=50:y=h-85:shadowcolor=black@0.3:shadowx=1:shadowy=1:box=1:boxcolor=black@0.8:boxborderw=10,
    drawtext=textfile=${ARTIST_FILE}:fontfile=${PACIFICO}:fontsize=33:fontcolor=white@0.85:x=w-tw-50:y=h-80:shadowcolor=black@0.5:shadowx=2:shadowy=2[v]
  " \
  -map "[v]" -map 1:a \
  -c:v libx264 -preset medium -crf 20 \
  -c:a aac -b:a 192k \
  -shortest \
  -movflags +faststart \
  "$OUTPUT"

echo "✅ Video: $OUTPUT ($(du -h "$OUTPUT" | cut -f1))"

if [ "$UPLOAD" = "--upload" ]; then
  echo "📤 Uploading to YouTube (@kapiko-music)..."
  
  KAPIKO_SONG="$SONG_NAME" KAPIKO_ALBUM="$ALBUM_NAME" KAPIKO_VIDEO="$OUTPUT" python3 << 'PYEOF'
import json, urllib.request, urllib.parse, os

client_id = os.popen('security find-generic-password -s "youtube-client-id" -w').read().strip()
client_secret = os.popen('security find-generic-password -s "youtube-client-secret" -w').read().strip()
refresh_token = os.popen('security find-generic-password -s "kapiko-youtube-refresh-token" -w').read().strip()

data = urllib.parse.urlencode({
    'client_id': client_id, 'client_secret': client_secret,
    'refresh_token': refresh_token, 'grant_type': 'refresh_token'
}).encode()
token = json.loads(urllib.request.urlopen(urllib.request.Request('https://oauth2.googleapis.com/token', data)).read())['access_token']

song = os.environ['KAPIKO_SONG']
album = os.environ['KAPIKO_ALBUM']
video_path = os.environ['KAPIKO_VIDEO']

metadata = {
    'snippet': {
        'title': f'{song} — kapiko | {album}',
        'description': f'{song} by kapiko\nFrom the album "{album}"\n\nRelaxing solo piano for studying, sleeping, and peaceful moments.\n\n🎹 Stream kapiko:\n→ YouTube: @kapiko-music\n\n#solopiano #relaxingpiano #studymusic #sleepmusic #peacefulpiano #pianomusic #ambientpiano #calmpiano #focusmusic #chillpiano #instrumentalpiano #softpiano #meditationmusic #kapiko\n\n© kapiko 2026. All rights reserved.',
        'tags': ['solo piano','relaxing piano','study music','sleep music','peaceful piano','piano music','ambient piano','calm piano','focus music','chill piano','instrumental piano','soft piano','meditation music','kapiko',album,song,'lofi piano','piano for studying','piano for sleeping','relaxing music','background music'],
        'categoryId': '10'
    },
    'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
}

video_size = os.path.getsize(video_path)
meta_bytes = json.dumps(metadata).encode()

init_url = 'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status'
init_req = urllib.request.Request(init_url, meta_bytes, {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json; charset=UTF-8',
    'X-Upload-Content-Type': 'video/mp4',
    'X-Upload-Content-Length': str(video_size),
})
upload_url = urllib.request.urlopen(init_req).headers['Location']

with open(video_path, 'rb') as f:
    video_data = f.read()
upload_req = urllib.request.Request(upload_url, video_data, {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'video/mp4',
    'Content-Length': str(video_size),
})
result = json.loads(urllib.request.urlopen(upload_req).read())
print(f"✅ https://youtube.com/watch?v={result['id']}")
PYEOF
fi
