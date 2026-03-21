#!/usr/bin/env python3
"""Score fingerstyle guitar mp3s using Gemini audio analysis.

Uses the modern google.genai SDK. Scores each track individually on
emotion, tone, arrangement, production, and replay value.

Usage:
  python3 scripts/gemini-guitar-scorer.py <directory>
  python3 scripts/gemini-guitar-scorer.py <file1.mp3> <file2.mp3> ...
  python3 scripts/gemini-guitar-scorer.py --json <directory>
"""
import subprocess, json, sys, os, time, glob, argparse
import google.genai as genai

SCORING_PROMPT = """You are an expert music critic and guitar aficionado specializing in fingerstyle acoustic guitar.

Score this audio clip on these 5 criteria (1-10 scale):

1. **Emotional Impact** — Does it move you? Does it capture feeling and mood?
2. **Guitar Tone Quality** — Is the guitar sound warm, natural, rich, resonant? Or thin, digital, harsh?
3. **Arrangement & Technique** — Interesting fingerpicking patterns, harmonics, percussive elements, tapping, dynamic variation?
4. **Production Quality** — Clean recording, good mix, no artifacts or clipping?
5. **Replay Value** — Would you listen again? Is there a memorable hook or moment?

Also evaluate:
- **Is it actually acoustic fingerstyle guitar?** (deduct heavily if it's electric, has vocals, drums, or heavy production)
- **Complexity** — Is the playing sophisticated or basic strumming?
- **Any issues** — artifacts, clipping, unnatural sounds, wrong instrument?

Return your response as JSON only, no other text:
{
  "emotional_impact": <1-10>,
  "guitar_tone": <1-10>,
  "arrangement": <1-10>,
  "production": <1-10>,
  "replay_value": <1-10>,
  "overall_score": <1-10>,
  "is_fingerstyle_guitar": true/false,
  "one_line_review": "<brief one-line review>",
  "standout_quality": "<what makes this clip special or weak>",
  "deductions": "<any issues: vocals, artifacts, wrong instrument, etc.>"
}
"""

BATCH_PROMPT = """You are an expert music critic and guitar aficionado specializing in fingerstyle acoustic guitar.

You will hear multiple CANDIDATE audio clips. Score EACH clip on these 5 criteria (1-10 scale):

1. **Emotional Impact** — Does it move you? Does it capture feeling and mood?
2. **Guitar Tone Quality** — Is the guitar sound warm, natural, rich, resonant? Or thin, digital, harsh?
3. **Arrangement & Technique** — Interesting fingerpicking patterns, harmonics, percussive elements, tapping, dynamic variation?
4. **Production Quality** — Clean recording, good mix, no artifacts or clipping?
5. **Replay Value** — Would you listen again? Is there a memorable hook or moment?

Also evaluate per clip:
- **Is it actually acoustic fingerstyle guitar?** (deduct heavily if it's electric, has vocals, drums, or heavy production)
- **Complexity** — Is the playing sophisticated or basic strumming?
- **Any issues** — artifacts, clipping, unnatural sounds, wrong instrument?

Return your response as a JSON object with a "candidates" array. Each entry:
{
  "candidates": [
    {
      "filename": "<name of the clip>",
      "emotional_impact": <1-10>,
      "guitar_tone": <1-10>,
      "arrangement": <1-10>,
      "production": <1-10>,
      "replay_value": <1-10>,
      "overall_score": <1-10>,
      "is_fingerstyle_guitar": true/false,
      "one_line_review": "<brief one-line review>",
      "standout_quality": "<what makes this clip special or weak>",
      "deductions": "<any issues: vocals, artifacts, wrong instrument, etc.>"
    }
  ]
}

Be ruthlessly honest. These are AI-generated tracks competing against real recordings by world-class guitarists like Don Ross, Andy McKee, and Lance Allen. Grade accordingly.
"""


def get_api_key():
    api_key = os.popen('security find-generic-password -s "google-api-key" -w').read().strip()
    if not api_key:
        print("ERROR: Could not read google-api-key from keychain", file=sys.stderr)
        sys.exit(1)
    return api_key


def score_batch(client, mp3_paths, model="gemini-2.5-flash"):
    """Score a batch of mp3s in a single Gemini call (up to ~10 at a time)."""
    # Upload all files
    uploaded = []
    for path in mp3_paths:
        name = os.path.basename(path)
        print(f"  📎 Uploading: {name}...", file=sys.stderr)
        try:
            f = client.files.upload(file=path)
            uploaded.append((f, name))
        except Exception as e:
            print(f"  ⚠️  Upload failed for {name}: {e}", file=sys.stderr)

    if not uploaded:
        return []

    # Build content parts
    parts = [BATCH_PROMPT]
    for i, (f, name) in enumerate(uploaded):
        parts.append(f"\n--- CANDIDATE {i+1}: {name} ---\n")
        parts.append(f)

    print(f"\n  🎸 Scoring {len(uploaded)} guitar track(s)...\n", file=sys.stderr)

    response = client.models.generate_content(
        model=model,
        contents=parts,
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
        print(f"  ⚠️  Failed to parse JSON response", file=sys.stderr)
        return []

    candidates = result.get("candidates", [])

    # Cleanup uploaded files
    for f, _ in uploaded:
        try:
            client.files.delete(name=f.name)
        except:
            pass

    return candidates


def main():
    parser = argparse.ArgumentParser(description="Score guitar tracks with Gemini")
    parser.add_argument("paths", nargs="+", help="MP3 files or directory")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Output raw JSON")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model")
    parser.add_argument("--batch-size", type=int, default=10, help="Tracks per Gemini call (default: 10)")
    args = parser.parse_args()

    # Collect mp3 paths
    mp3s = []
    for p in args.paths:
        if os.path.isdir(p):
            mp3s.extend(sorted(glob.glob(os.path.join(p, "*.mp3"))))
        elif p.endswith(".mp3") and os.path.exists(p):
            mp3s.append(p)

    if not mp3s:
        print("No MP3 files found!", file=sys.stderr)
        sys.exit(1)

    print(f"\n🎸 Guitar Scorer — {len(mp3s)} track(s)\n", file=sys.stderr)

    client = genai.Client(api_key=get_api_key())
    all_results = []

    # Process in batches
    for i in range(0, len(mp3s), args.batch_size):
        batch = mp3s[i:i + args.batch_size]
        batch_num = (i // args.batch_size) + 1
        total_batches = (len(mp3s) + args.batch_size - 1) // args.batch_size
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} tracks)", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        try:
            candidates = score_batch(client, batch, model=args.model)
            for c in candidates:
                # Ensure filename is set
                if not c.get("filename"):
                    # Try to match by position
                    idx = candidates.index(c)
                    if idx < len(batch):
                        c["filename"] = os.path.basename(batch[idx])
                # Add filepath for convenience
                for mp3_path in batch:
                    if os.path.basename(mp3_path) == c.get("filename"):
                        c["filepath"] = mp3_path
                        break
                all_results.append(c)

                if not args.output_json:
                    guitar = "🎸" if c.get("is_fingerstyle_guitar") else "⚠️"
                    print(f"    {guitar} {c.get('overall_score', '?')}/10 | {c.get('filename', '?')} — {c.get('one_line_review', '')}")
        except Exception as e:
            print(f"  ❌ Batch {batch_num} failed: {e}", file=sys.stderr)

        # Rate limit between batches
        if i + args.batch_size < len(mp3s):
            time.sleep(2)

    # Sort by score
    scored = sorted(
        [r for r in all_results if "overall_score" in r],
        key=lambda x: x["overall_score"],
        reverse=True,
    )

    # Output
    output = {"rankings": scored, "all_results": all_results}

    if args.output_json:
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'='*60}")
        print("RANKINGS")
        print(f"{'='*60}")
        for i, r in enumerate(scored[:20]):  # Top 20
            guitar = "🎸" if r.get("is_fingerstyle_guitar") else "⚠️"
            print(f"\n#{i+1} {guitar} {r.get('filename', '?')}")
            print(f"   Overall: {r['overall_score']}/10 | Emotion: {r.get('emotional_impact', '?')} | Tone: {r.get('guitar_tone', '?')} | Arr: {r.get('arrangement', '?')} | Prod: {r.get('production', '?')} | Replay: {r.get('replay_value', '?')}")
            print(f"   Review: {r.get('one_line_review', '')}")

    # Save results to directory (if input was a directory)
    for p in args.paths:
        if os.path.isdir(p):
            output_path = os.path.join(p, "guitar-scores.json")
            with open(output_path, "w") as f:
                json.dump(output, f, indent=2)
            print(f"\nResults saved to {output_path}", file=sys.stderr)
            break


if __name__ == "__main__":
    main()
