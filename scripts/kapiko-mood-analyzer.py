#!/usr/bin/env python3
"""
Kapiko Mood Analyzer — Listen to a piano track and infer a matching natural landscape.

Uploads an mp3 to Gemini, analyzes mood/emotion/energy, and outputs a
descriptive natural landscape scene for image generation.

Usage:
  python3 scripts/kapiko-mood-analyzer.py <track.mp3>
  python3 scripts/kapiko-mood-analyzer.py <track.mp3> --json
  python3 scripts/kapiko-mood-analyzer.py <track.mp3> --model gemini-2.5-pro
"""

import google.genai as genai
import os
import sys
import json
import argparse

PROMPT = """You are a synesthete — you see vivid landscapes when you hear music.

Listen to this solo piano track carefully. Pay attention to:
- Tempo and energy (slow/contemplative vs fast/energetic)
- Key and tonality (major/bright vs minor/melancholic)
- Dynamics (quiet/intimate vs loud/dramatic)
- Emotional arc (how the piece evolves)
- Overall mood and feeling

Based on what you hear, describe the ONE natural landscape that best matches this music.

Rules:
- Must be a real, natural landscape (no cities, buildings, or people)
- Be specific — not just "mountains" but the exact scene, time of day, weather, light, season
- The landscape should FEEL like the music sounds
- The capybara is ALWAYS wearing over-ear headphones and listening to music — this is non-negotiable

Examples of the specificity I want:
- "A misty bamboo forest at dawn, soft golden light filtering through, dew on leaves, a still pond reflecting the canopy"
- "A vast frozen lake under northern lights, deep blue and green aurora, snow-covered pines on the shore, absolute stillness"
- "A sun-drenched Mediterranean cliff at golden hour, warm limestone, wild herbs, endless turquoise sea below"

Respond in this exact JSON format:
{
  "mood": "<2-3 words: the emotional core>",
  "energy": "<low/medium/high>",
  "tonality": "<bright/warm/neutral/melancholic/dark>",
  "season": "<spring/summer/autumn/winter/timeless>",
  "time_of_day": "<dawn/morning/midday/afternoon/golden_hour/dusk/night>",
  "landscape_type": "<e.g. mountains, ocean, forest, desert, tundra, lake, meadow, canyon, volcano, hot_springs, river, wetland, glacier, cave, waterfall, coral_reef, savanna, rainforest>",
  "landscape_description": "<2-3 sentence vivid scene description — this will be used as an image generation prompt>",
  "capybara_action": "<what the capybara is doing in this scene while wearing headphones and listening to music, one short phrase>",
  "color_palette": ["<3-5 dominant colors that match the mood, e.g. 'deep indigo', 'soft amber', 'mist grey'>"],
  "image_prompt": "<a complete, ready-to-use prompt for Nano Banana 2 image generation: MUST start with 'Wide 16:9 landscape format.' then watercolor illustration style, the landscape scene with a small cute capybara wearing over-ear headphones listening to music, specific details from above, art style guidance>"
}"""


def analyze_mood(filepath, model="gemini-2.5-flash", output_json=False):
    """Analyze a track's mood and generate a matching landscape."""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    api_key = os.popen('security find-generic-password -s "google-api-key" -w').read().strip()
    if not api_key:
        print("❌ Could not read google-api-key from keychain", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    filename = os.path.basename(filepath)
    print(f"  📎 Uploading: {filename}...", file=sys.stderr)

    try:
        audio_file = client.files.upload(file=filepath)
    except UnicodeEncodeError:
        import shutil, tempfile
        ext = os.path.splitext(filepath)[1]
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False, prefix="mood_")
        shutil.copy2(filepath, tmp.name)
        tmp.close()
        audio_file = client.files.upload(file=tmp.name)

    print(f"  🎧 Analyzing mood...", file=sys.stderr)

    response = client.models.generate_content(
        model=model,
        contents=[PROMPT, audio_file],
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

    # Add source metadata
    result["source_file"] = filename
    result["source_path"] = os.path.abspath(filepath)

    if output_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  🎵 {filename}")
        print(f"{'='*60}")
        print(f"  Mood:       {result.get('mood', '?')}")
        print(f"  Energy:     {result.get('energy', '?')}")
        print(f"  Tonality:   {result.get('tonality', '?')}")
        print(f"  Season:     {result.get('season', '?')}")
        print(f"  Time:       {result.get('time_of_day', '?')}")
        print(f"  Landscape:  {result.get('landscape_type', '?')}")
        print(f"  Colors:     {', '.join(result.get('color_palette', []))}")
        print(f"\n  🏞️  {result.get('landscape_description', '?')}")
        print(f"  🦫 Capybara: {result.get('capybara_action', '?')}")
        print(f"\n  🎨 Image prompt:")
        print(f"  {result.get('image_prompt', '?')}")
        print()

    return result


def main():
    parser = argparse.ArgumentParser(description="Analyze piano track mood → natural landscape")
    parser.add_argument("track", help="MP3 file to analyze")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Output JSON")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model")
    parser.add_argument("--output", help="Save JSON result to file")
    args = parser.parse_args()

    result = analyze_mood(args.track, model=args.model, output_json=args.output_json)

    if args.output and result:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        if not args.output_json:
            print(f"  📁 Saved: {args.output}")


if __name__ == "__main__":
    main()
