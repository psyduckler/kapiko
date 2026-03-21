#!/usr/bin/env python3
"""
Kapiko Image Generator — Generate YouTube-optimized capybara landscape art.

Takes a mood analysis JSON (from kapiko-mood-analyzer.py) or a raw prompt,
generates via Nano Banana 2, and resizes to exact 1920x1080 for YouTube.

Usage:
  python3 scripts/kapiko-image-gen.py --mood mood.json --output capybara.png
  python3 scripts/kapiko-image-gen.py --prompt "Watercolor illustration..." --output capybara.png
  python3 scripts/kapiko-image-gen.py --mood mood.json  # auto-names output
"""

import subprocess
import os
import sys
import json
import argparse
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NB2_SCRIPT = os.path.join(SCRIPT_DIR, "..", "skills", "nano-banana-pro", "scripts", "generate_image.py")

# YouTube standard: 1920x1080, 16:9
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080


def get_api_key():
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "google-api-key", "-w"],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def generate_image(prompt, output_path):
    """Generate image via NB2 and resize to 1920x1080."""
    api_key = get_api_key()
    if not api_key:
        print("❌ Could not read google-api-key from keychain", file=sys.stderr)
        sys.exit(1)

    # Generate with NB2 at 2K resolution
    raw_path = output_path + ".raw.png"
    cmd = [
        sys.executable, NB2_SCRIPT,
        "--prompt", prompt,
        "--filename", raw_path,
        "--resolution", "2K",
    ]

    env = os.environ.copy()
    env["GEMINI_API_KEY"] = api_key

    print(f"  🎨 Generating image via Nano Banana 2...")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ NB2 failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(raw_path):
        print(f"❌ No image generated at {raw_path}", file=sys.stderr)
        sys.exit(1)

    # Resize to exact 1920x1080
    img = Image.open(raw_path)
    w, h = img.size
    print(f"  📐 Raw size: {w}x{h} (ratio: {w/h:.3f})")

    resized = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.LANCZOS)
    resized.save(output_path, quality=95)

    # Clean up raw file
    os.remove(raw_path)

    final_size = os.path.getsize(output_path)
    print(f"  ✅ Saved: {output_path} ({TARGET_WIDTH}x{TARGET_HEIGHT}, {final_size/1024:.0f}KB)")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Kapiko image generator — YouTube-optimized capybara landscapes")
    parser.add_argument("--mood", help="Mood analysis JSON file (from kapiko-mood-analyzer.py)")
    parser.add_argument("--prompt", help="Direct image prompt (overrides mood file)")
    parser.add_argument("--output", "-o", help="Output PNG path")
    args = parser.parse_args()

    # Get the image prompt
    if args.prompt:
        prompt = args.prompt
        title = "custom"
    elif args.mood:
        with open(args.mood) as f:
            mood = json.load(f)
        prompt = mood.get("image_prompt", "")
        if not prompt:
            print("❌ No image_prompt found in mood JSON", file=sys.stderr)
            sys.exit(1)
        title = mood.get("landscape_type", "landscape")
    else:
        print("❌ Provide either --mood or --prompt", file=sys.stderr)
        sys.exit(1)

    # Ensure prompt requests 16:9
    if "16:9" not in prompt:
        prompt = "Wide 16:9 landscape format. " + prompt

    # Output path
    if args.output:
        output_path = args.output
    else:
        safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in title).strip("-")
        output_path = f"/tmp/kapiko-{safe_title}.png"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    print(f"\n🎹 Kapiko Image Generator")
    print(f"   Output: {output_path}")
    print(f"   Target: {TARGET_WIDTH}x{TARGET_HEIGHT} (YouTube 16:9)\n")

    generate_image(prompt, output_path)


if __name__ == "__main__":
    main()
