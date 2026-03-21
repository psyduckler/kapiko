#!/usr/bin/env python3
"""
Kapiko YouTube uploader — A Tapestry of Solitude batch upload.
Uses kapiko-youtube-refresh-token from macOS Keychain.
Category: 10 (Music)
"""

import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

WORKDIR = "/Users/psy/.openclaw/workspace"


def get_keychain(key):
    result = subprocess.run(
        ["security", "find-generic-password", "-s", key, "-w"],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def get_access_token():
    client_id = get_keychain("youtube-client-id")
    client_secret = get_keychain("youtube-client-secret")
    refresh_token = get_keychain("kapiko-youtube-refresh-token")

    token_data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read().decode())
    return tokens["access_token"]


def upload_video(video_path, title, description, tags, access_token):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    file_size = os.path.getsize(video_path)
    print(f"  File size: {file_size / 1024 / 1024:.1f} MB")

    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "10",  # Music
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    params = urllib.parse.urlencode({
        "uploadType": "resumable",
        "part": "snippet,status",
    })

    init_req = urllib.request.Request(
        f"https://www.googleapis.com/upload/youtube/v3/videos?{params}",
        data=json.dumps(metadata).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(file_size),
            "X-Upload-Content-Type": "video/mp4",
        },
    )

    try:
        with urllib.request.urlopen(init_req) as resp:
            upload_url = resp.headers.get("Location")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Init failed {e.code}: {body}")

    if not upload_url:
        raise RuntimeError("No upload URL returned from YouTube")

    print(f"  Uploading video data...")
    with open(video_path, "rb") as f:
        video_data = f.read()

    upload_req = urllib.request.Request(
        upload_url,
        data=video_data,
        method="PUT",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "video/mp4",
            "Content-Length": str(file_size),
        },
    )

    with urllib.request.urlopen(upload_req) as resp:
        result = json.loads(resp.read().decode())

    video_id = result.get("id")
    upload_status = result.get("status", {}).get("uploadStatus", "unknown")
    return video_id, upload_status


def main():
    album = "A Tapestry of Solitude"

    tracks = [
        {
            "file": "kapiko-sunset's-gentle-invitation.mp4",
            "song": "Sunset's Gentle Invitation",
        },
        {
            "file": "kapiko-flickering-hearthside-echo.mp4",
            "song": "Flickering Hearthside Echo",
        },
        {
            "file": "kapiko-silent-echoes-in-sepia.mp4",
            "song": "Silent Echoes in Sepia",
        },
        {
            "file": "kapiko-moonlit-petals-drift.mp4",
            "song": "Moonlit Petals Drift",
        },
    ]

    tags = [
        "solo piano", "relaxing piano", "study music", "sleep music",
        "ambient piano", "instrumental", "kapiko", "piano music",
        "peaceful music", "focus music", "meditation music",
        "A Tapestry of Solitude", "classical piano", "lofi piano"
    ]

    print("Getting access token...")
    access_token = get_access_token()
    print("✅ Token obtained\n")

    results = []

    for track in tracks:
        song = os.environ.get("KAPIKO_SONG", track["song"])
        # Use env var override if set, else use track default
        # (env var mechanism for apostrophe safety — pass per-run if needed)
        song = track["song"]  # always use the track dict value here (safe in Python)

        video_path = os.path.join(WORKDIR, track["file"])
        title = f"{song} \u2014 kapiko | {album}"
        description = (
            f"{song} by kapiko, from the album \"{album}\".\n\n"
            f"A piece of relaxing solo piano music to help you study, sleep, focus, or unwind.\n\n"
            f"#solopiano #relaxingpiano #studymusic #sleepmusic #pianomusic #kapiko\n\n"
            f"\u00a9 kapiko 2026. All rights reserved."
        )

        print(f"Uploading: {title}")
        print(f"  File: {track['file']}")

        try:
            video_id, status = upload_video(video_path, title, description, tags, access_token)
            url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"  ✅ Uploaded! ID: {video_id} | Status: {status}")
            print(f"  URL: {url}\n")
            results.append({"song": song, "video_id": video_id, "url": url, "status": status, "ok": True})
        except Exception as e:
            print(f"  ❌ FAILED: {e}\n")
            results.append({"song": song, "error": str(e), "ok": False})

    print("\n=== BATCH SUMMARY ===")
    for r in results:
        if r["ok"]:
            print(f"✅ {r['song']}: {r['url']}")
        else:
            print(f"❌ {r['song']}: {r['error']}")

    # Write results JSON for the calling script to pick up
    results_path = "/tmp/kapiko-upload-results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {results_path}")


if __name__ == "__main__":
    main()
