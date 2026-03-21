#!/usr/bin/env python3
"""
Kapiko Video Prompt Generator — Analyze the generated image and create a
subtle looping animation prompt for MiniMax I2V.

Takes the mood JSON + generated image, analyzes the image content,
and outputs a video prompt designed for seamless looping with minimal movement.

Usage:
  python3 scripts/kapiko-video-prompt.py --mood mood.json --image capybara.png
  python3 scripts/kapiko-video-prompt.py --mood mood.json --image capybara.png --json
"""

import google.genai as genai
import os
import sys
import json
import argparse
import subprocess
from PIL import Image
import base64

PROMPT = """You are a cinematographer creating a living painting — a still illustration brought to life with gentle, dreamy motion.

I'm giving you:
1. A watercolor illustration of a capybara in a natural landscape
2. Context about the mood and scene

Your job: write a VIDEO ANIMATION PROMPT for an image-to-video AI model (MiniMax Hailuo).
The video should feel like a peaceful animated painting — visible movement but calm and dreamy.

RULES:
- NO camera movement (no pan, no zoom, no tilt — the frame stays still)
- The capybara stays mostly still (small ear twitch or gentle breathing is OK)
- Animate 2-4 natural elements: water flowing, grass swaying, clouds moving, leaves drifting, light shifting, mist rolling, fireflies, rain, snow, aurora, reflections rippling
- Motion should be smooth, gentle, and continuous — like a lo-fi animation loop
- Think Studio Ghibli background art come to life — everything gently breathing and moving

BAD examples (too much):
- "The capybara walks across the scene" ❌
- "Camera pans across the landscape" ❌
- "Dramatic storm rolls in" ❌

GOOD examples (gentle but visible):
- "Gentle breeze sways the tall grass and reeds. Water flows with soft ripples and light reflections dancing on the surface. Clouds drift slowly overhead. The capybara sits peacefully, breathing gently."
- "Mist rolls slowly through the forest. Leaves drift down lazily from the canopy. Dappled light shifts softly on the ground. Serene and dreamlike."
- "Snow falls gently in large soft flakes. Northern lights shimmer and undulate slowly in the sky. The capybara's breath is faintly visible in the cold air."

Look at the actual image and identify which specific elements would look best animated.

Respond in JSON:
{{
  "animated_elements": ["<element 1>", "<element 2>", "<element 3 if applicable>"],
  "video_prompt": "<the actual prompt for MiniMax I2V, 2-3 sentences, describing gentle but visible ambient motion>",
  "loop_notes": "<why this motion will loop well>"
}}"""


def analyze_and_prompt(image_path, mood_data, model="gemini-2.5-flash", output_json=False):
    """Analyze image and generate a subtle animation prompt."""
    api_key = subprocess.run(
        ["security", "find-generic-password", "-s", "google-api-key", "-w"],
        capture_output=True, text=True
    ).stdout.strip()

    if not api_key:
        print("❌ Could not read google-api-key from keychain", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Upload image
    print(f"  📎 Uploading image...", file=sys.stderr)
    img_file = client.files.upload(file=image_path)

    # Build context from mood data
    context = ""
    if mood_data:
        context = f"""
Scene context:
- Mood: {mood_data.get('mood', '?')}
- Landscape: {mood_data.get('landscape_type', '?')}
- Description: {mood_data.get('landscape_description', '?')}
- Time of day: {mood_data.get('time_of_day', '?')}
- Season: {mood_data.get('season', '?')}
- Capybara is: {mood_data.get('capybara_action', '?')}
"""

    print(f"  🎬 Generating video prompt...", file=sys.stderr)

    response = client.models.generate_content(
        model=model,
        contents=[PROMPT + context, img_file],
    )

    raw = response.text

    # Parse JSON
    try:
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw.strip()
        result = json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        print(f"⚠️  Could not parse response:\n{raw}", file=sys.stderr)
        if output_json:
            print(json.dumps({"error": "parse_failed", "raw": raw}))
        return None

    # Add metadata
    result["source_image"] = os.path.basename(image_path)

    if output_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  🎬 Video Prompt")
        print(f"{'='*60}")
        print(f"  Animated: {', '.join(result.get('animated_elements', []))}")
        print(f"  Loop:     {result.get('loop_notes', '?')}")
        print(f"\n  📝 Prompt:")
        print(f"  {result.get('video_prompt', '?')}")
        print()

    return result


def main():
    parser = argparse.ArgumentParser(description="Generate subtle looping video prompt from capybara image")
    parser.add_argument("--image", required=True, help="Generated capybara landscape PNG")
    parser.add_argument("--mood", help="Mood analysis JSON (from kapiko-mood-analyzer.py)")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Output JSON")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model")
    parser.add_argument("--output", help="Save JSON result to file")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"❌ Image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    mood_data = None
    if args.mood:
        with open(args.mood) as f:
            mood_data = json.load(f)

    result = analyze_and_prompt(args.image, mood_data, model=args.model, output_json=args.output_json)

    if args.output and result:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        if not args.output_json:
            print(f"  📁 Saved: {args.output}")


if __name__ == "__main__":
    main()
