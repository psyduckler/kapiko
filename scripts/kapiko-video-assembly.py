#!/usr/bin/env python3
"""
Kapiko Video Assembly — Loop clip + text overlay + mux audio → YouTube-ready video.

Takes a video clip, mp3 audio, and song title. Loops the clip to match audio length,
adds Pacifico text overlays (song name top-left, "kapiko" bottom-right), muxes audio.

Usage:
  python3 scripts/kapiko-video-assembly.py --clip clip.mp4 --audio track.mp3 --title "Golden Wetland Drift"
  python3 scripts/kapiko-video-assembly.py --clip clip.mp4 --audio track.mp3 --title "Song Name" --output final.mp4
  python3 scripts/kapiko-video-assembly.py --clip clip.mp4 --audio track.mp3 --title "Song Name" --publish

Output: 1920x1080 H.264 MP4, AAC audio, YouTube-optimized.
"""

import subprocess
import os
import sys
import json
import argparse
import tempfile

FONT = "/Users/psy/Library/Fonts/Pacifico-Regular.ttf"


def get_duration(filepath):
    """Get duration in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", filepath],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def assemble_video(clip_path, audio_path, song_title, output_path, crf=23):
    """Loop clip, add text overlays, mux audio."""
    audio_duration = get_duration(audio_path)

    print(f"  🎵 Audio: {audio_duration:.1f}s ({audio_duration/60:.1f} min)")
    print(f"  🎬 Clip: {get_duration(clip_path):.1f}s (will loop)")
    print(f"  📝 Title: {song_title}")
    print(f"  📁 Output: {output_path}")

    # Write song title to temp file (avoids FFmpeg special char issues)
    title_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, prefix='kapiko_title_')
    title_file.write(song_title)
    title_file.close()

    # FFmpeg command:
    # - stream_loop -1: loop video infinitely
    # - shortest + -t: stop at audio end
    # - drawtext #1: song title, top-left, 72px white, black highlight box
    # - drawtext #2: "kapiko", bottom-right, 48px white @ 80% opacity
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", clip_path,
        "-i", audio_path,
        "-filter_complex",
        f"[0:v]drawtext=fontfile={FONT}:textfile={title_file.name}:fontsize=72:fontcolor=white:x=60:y=60:box=1:boxcolor=black@0.6:boxborderw=12,"
        f"drawtext=fontfile={FONT}:text='kapiko':fontsize=48:fontcolor=white@0.8:x=w-tw-60:y=h-th-60",
        "-shortest", "-t", str(audio_duration),
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path,
    ]

    print(f"\n  ⚙️  Encoding...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up temp file
    os.unlink(title_file.name)

    if result.returncode != 0:
        print(f"❌ FFmpeg failed:\n{result.stderr[-500:]}", file=sys.stderr)
        sys.exit(1)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    duration = get_duration(output_path)
    print(f"  ✅ Done: {output_path} ({size_mb:.1f}MB, {duration:.0f}s)")

    return output_path


def build_youtube_metadata(song_title, mood_data=None, instrument="piano"):
    """Build YouTube title, description, and tags from song + mood context."""
    # Instrument display name for titles/descriptions
    instrument_map = {
        "piano": {"label": "Solo Piano", "emoji": "🎹", "short": "piano"},
        "guitar": {"label": "Solo Guitar", "emoji": "🎸", "short": "guitar"},
    }
    inst = instrument_map.get(instrument, instrument_map["piano"])
    
    # Title format: "Song Name [Single - Solo Piano] - kapiko" or "Song Name [Single - Solo Guitar] - kapiko"
    yt_title = f"{song_title} [Single - {inst['label']}] - kapiko"

    # Build keyword-rich description from mood data
    mood = mood_data.get("mood", "peaceful, reflective") if mood_data else "peaceful, reflective"
    landscape = mood_data.get("landscape_type", "nature") if mood_data else "nature"
    landscape_desc = mood_data.get("landscape_description", "") if mood_data else ""
    vibe_tag = mood_data.get("vibe_tag", "") if mood_data else ""
    season = mood_data.get("season", "") if mood_data else ""
    time_of_day = mood_data.get("time_of_day", "") if mood_data else ""
    colors = ", ".join(mood_data.get("color_palette", [])) if mood_data else ""

    description_lines = [
        f"{song_title} — an original solo {inst['short']} piece by kapiko.",
        "",
        f"Mood: {mood}",
    ]
    if landscape_desc:
        description_lines.append(f"Inspired by: {landscape_desc}")
    description_lines += [
        "",
        "Perfect for studying, relaxation, meditation, focus, sleep, reading, yoga, and peaceful moments.",
        "",
        f"{inst['emoji']} {inst['label']} | {mood} | {landscape} | kapiko",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"kapiko creates original solo {inst['short']} music — ambient, cinematic, classical, jazz, and everything in between.",
        "",
        f"Subscribe for daily solo {inst['short']}: https://www.youtube.com/@kapiko-music",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"#{inst['short']} #solo{inst['short']} #relaxing #studymusic #sleepmusic #meditation #focus #calm #peaceful #ambient #kapiko",
    ]

    # Build rich tags from mood
    base_tags = [
        inst['short'], f"solo {inst['short']}", f"relaxing {inst['short']}", f"calm {inst['short']}", f"peaceful {inst['short']}",
        "study music", "sleep music", "meditation music", "focus music",
        f"ambient {inst['short']}", "kapiko", f"{inst['short']} music", "relaxing music",
        f"instrumental {inst['short']}", f"{inst['short']} for studying", f"{inst['short']} for sleeping",
        f"beautiful {inst['short']}", f"soothing {inst['short']}",
    ]
    # Add mood-specific tags
    if mood:
        for word in mood.lower().replace(",", "").split():
            if word not in ("and", "the", "a"):
                base_tags.append(f"{word} piano")
    if landscape:
        base_tags.append(f"{landscape} music")
    if vibe_tag:
        base_tags.append(vibe_tag)

    tags = ",".join(base_tags[:30])  # YouTube max ~500 chars

    return yt_title, "\n".join(description_lines), tags


def publish_youtube(video_path, song_title, mood_data=None, instrument="piano"):
    """Publish to YouTube @kapiko channel."""
    yt_title, description, tags = build_youtube_metadata(song_title, mood_data, instrument=instrument)

    # Always use youtube-upload.py with kapiko credentials (not the tabiji publish script)
    upload_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube-upload.py")
    if not os.path.exists(upload_script):
        print(f"  ⚠️  No YouTube upload script found: {upload_script}", file=sys.stderr)
        return False

    # youtube-upload.py uses youtube-refresh-token by default (@tabijiai).
    # For kapiko, we need to temporarily swap in the kapiko refresh token.
    import google.oauth2.credentials
    import googleapiclient.discovery
    import googleapiclient.http

    kapiko_rt = subprocess.run(
        ["security", "find-generic-password", "-s", "kapiko-youtube-refresh-token", "-w"],
        capture_output=True, text=True
    ).stdout.strip()
    client_id = subprocess.run(
        ["security", "find-generic-password", "-s", "youtube-client-id", "-w"],
        capture_output=True, text=True
    ).stdout.strip()
    client_secret = subprocess.run(
        ["security", "find-generic-password", "-s", "youtube-client-secret", "-w"],
        capture_output=True, text=True
    ).stdout.strip()

    if not kapiko_rt or not client_id or not client_secret:
        print("  ❌ Missing kapiko YouTube credentials", file=sys.stderr)
        return False

    print(f"\n  📤 Uploading to YouTube @kapiko-music...")
    print(f"  📝 Title: {yt_title}")

    creds = google.oauth2.credentials.Credentials(
        token=None,
        refresh_token=kapiko_rt,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
    )

    yt = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": yt_title,
            "description": description,
            "tags": tags.split(","),
            "categoryId": "10",  # Music
        },
        "status": {"privacyStatus": "public"},
    }

    media = googleapiclient.http.MediaFileUpload(
        video_path, mimetype="video/mp4", resumable=True, chunksize=4 * 1024 * 1024
    )

    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response.get("id", "")
    print(f"  ✅ Published! https://youtube.com/watch?v={video_id}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Kapiko video assembly — loop + overlay + mux + publish")
    parser.add_argument("--clip", required=True, help="Video clip to loop (mp4)")
    parser.add_argument("--audio", required=True, help="Audio track (mp3)")
    parser.add_argument("--title", required=True, help="Song title for overlay")
    parser.add_argument("--output", "-o", help="Output path (default: auto)")
    parser.add_argument("--crf", type=int, default=23, help="Video quality (lower = better, default: 23)")
    parser.add_argument("--mood", help="Mood JSON file (from kapiko-mood-analyzer.py) — enriches YouTube metadata")
    parser.add_argument("--instrument", default="piano", choices=["piano", "guitar"], help="Instrument for YouTube metadata (default: piano)")
    parser.add_argument("--publish", action="store_true", help="Upload to YouTube @kapiko after assembly")
    parser.add_argument("--print-metadata", action="store_true", help="Print YouTube metadata and exit")
    args = parser.parse_args()

    if not os.path.exists(args.clip):
        print(f"❌ Clip not found: {args.clip}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.audio):
        print(f"❌ Audio not found: {args.audio}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(FONT):
        print(f"❌ Pacifico font not found: {FONT}", file=sys.stderr)
        sys.exit(1)

    # Auto output path
    if args.output:
        output_path = args.output
    else:
        safe_title = "".join(c if c.isalnum() or c in "-_ " else "" for c in args.title).strip().replace(" ", "-").lower()
        output_path = f"/tmp/kapiko-{safe_title}.mp4"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Load mood data if provided
    mood_data = None
    if args.mood:
        with open(args.mood) as f:
            mood_data = json.load(f)

    if args.print_metadata:
        yt_title, description, tags = build_youtube_metadata(args.title, mood_data, instrument=args.instrument)
        print(json.dumps({
            "title": yt_title,
            "description": description,
            "tags": tags,
        }, indent=2))
        sys.exit(0)

    print(f"\n🎹 Kapiko Video Assembly\n")

    video_path = assemble_video(args.clip, args.audio, args.title, output_path, crf=args.crf)

    if args.publish:
        publish_youtube(video_path, args.title, mood_data=mood_data, instrument=args.instrument)

    print(f"\n  🏁 Complete: {video_path}")


if __name__ == "__main__":
    main()
