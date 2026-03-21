#!/usr/bin/env python3
"""
Piano Track Scorer — Compare generated piano tracks against reference masterpieces.

Uses Gemini to compare a candidate track against 3 reference tracks:
  1. Ludovico Einaudi - Nuvole Bianche
  2. Yiruma - River Flows in You
  3. Yann Tiersen - Comptine d'un autre été

Usage:
  python3 scripts/piano-score.py <candidate.mp3>
  python3 scripts/piano-score.py <candidate1.mp3> <candidate2.mp3> ...
  python3 scripts/piano-score.py --batch <directory>
  python3 scripts/piano-score.py --json <candidate.mp3>        # JSON output
  python3 scripts/piano-score.py --model gemini-2.5-pro <candidate.mp3>

Reference tracks expected in: ~/Documents/music/
"""

import google.genai as genai
import os
import sys
import json
import glob
import argparse
import time

REFERENCE_DIR = os.path.expanduser("~/Documents/music")
REFERENCES = [
    ("Ludovico Einaudi - Nuvole Bianche (Official Visualiser).mp3", "Ludovico Einaudi - Nuvole Bianche"),
    ("Yiruma, (이루마) - River Flows in You.mp3", "Yiruma - River Flows in You"),
    ("Yann Tiersen - Comptine d'un autre été (Amélie).mp3", "Yann Tiersen - Comptine d'un autre été"),
]

PROMPT = """You are an expert music producer and playlist curator specializing in solo piano music.

You have 3 REFERENCE tracks — these are established masterpieces that define the gold standard for the modern solo piano playlist aesthetic (think Spotify's "Peaceful Piano" or "Piano in the Background"):

- Reference 1: Ludovico Einaudi - Nuvole Bianche
- Reference 2: Yiruma - River Flows in You  
- Reference 3: Yann Tiersen - Comptine d'un autre été

Then you have one or more CANDIDATE tracks to evaluate.

For each CANDIDATE track, answer these questions:

1. **Playlist Fit Score (1-10):** Would this track fit seamlessly on the same playlist as the 3 references? 10 = indistinguishable quality, a listener wouldn't skip. 1 = obviously AI/amateur, instant skip.

2. **Closest Reference:** Which reference track is it most similar to in feel, and why? (one sentence)

3. **Quality Gap:** Would a listener notice a quality drop if this played right after the references? Be brutally honest. What specifically sounds worse (or better)?

4. **Production Match (1-10):** How close is the recording/production quality? Consider: piano tone realism, reverb/space, dynamic range, mastering loudness, absence of artifacts.

5. **Emotional Authenticity (1-10):** Does it feel like a real musician expressing something, or does it feel algorithmically generated? What gives it away (if anything)?

6. **Verdict:** PASS (playlist-ready, 7+), BORDERLINE (5-6, needs work), or FAIL (<5, not usable).

7. **Overall Score (1-10):** Single number, weighted toward playlist fit and production match.

Respond in this exact JSON format for each candidate:
```json
{
  "candidates": [
    {
      "filename": "<name>",
      "playlist_fit": <1-10>,
      "closest_reference": "<reference name>",
      "closest_reference_reason": "<one sentence>",
      "quality_gap": "<honest assessment>",
      "production_match": <1-10>,
      "emotional_authenticity": <1-10>,
      "verdict": "PASS|BORDERLINE|FAIL",
      "overall_score": <1-10>,
      "summary": "<2-3 sentence overall take>"
    }
  ]
}
```

Be ruthlessly honest. These are Suno-generated tracks competing against real recordings by world-class pianists. Grade accordingly."""


def upload_file_safe(client, filepath, display_name):
    """Upload file, handling non-ASCII filenames by copying to temp."""
    try:
        return client.files.upload(file=filepath)
    except UnicodeEncodeError:
        import shutil
        import tempfile
        ext = os.path.splitext(filepath)[1]
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False, prefix="piano_ref_")
        shutil.copy2(filepath, tmp.name)
        tmp.close()
        return client.files.upload(file=tmp.name)


def score_candidates(candidate_paths, model="gemini-2.5-flash", output_json=False):
    api_key = os.popen('security find-generic-password -s "google-api-key" -w').read().strip()
    if not api_key:
        print("ERROR: Could not read google-api-key from keychain", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Upload reference tracks
    ref_files = []
    for filename, display_name in REFERENCES:
        path = os.path.join(REFERENCE_DIR, filename)
        if not os.path.exists(path):
            print(f"ERROR: Reference track not found: {path}", file=sys.stderr)
            sys.exit(1)
        print(f"  📎 Uploading reference: {display_name}...", file=sys.stderr)
        f = upload_file_safe(client, path, display_name)
        ref_files.append((f, display_name))

    # Upload candidate tracks
    cand_files = []
    for path in candidate_paths:
        if not os.path.exists(path):
            print(f"ERROR: Candidate not found: {path}", file=sys.stderr)
            sys.exit(1)
        name = os.path.basename(path)
        print(f"  📎 Uploading candidate: {name}...", file=sys.stderr)
        f = upload_file_safe(client, path, name)
        cand_files.append((f, name))

    # Build content parts
    parts = []
    for i, (f, name) in enumerate(ref_files):
        parts.append(f"\n--- REFERENCE {i+1}: {name} ---\n")
        parts.append(f)

    for i, (f, name) in enumerate(cand_files):
        parts.append(f"\n--- CANDIDATE {i+1}: {name} ---\n")
        parts.append(f)

    print(f"\n  🎹 Scoring {len(cand_files)} candidate(s) against 3 references...\n", file=sys.stderr)

    response = client.models.generate_content(
        model=model,
        contents=[PROMPT] + parts,
    )

    raw = response.text

    # Parse JSON from response
    try:
        # Extract JSON block if wrapped in markdown
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw.strip()
        result = json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        if output_json:
            print(json.dumps({"error": "Failed to parse JSON", "raw": raw}))
        else:
            print(raw)
        return

    if output_json:
        print(json.dumps(result, indent=2))
        return

    # Pretty print results
    for c in result.get("candidates", []):
        verdict_emoji = {"PASS": "✅", "BORDERLINE": "⚠️", "FAIL": "❌"}.get(c.get("verdict", ""), "❓")
        print(f"{'='*60}")
        print(f"🎵 {c.get('filename', 'Unknown')}")
        print(f"{'='*60}")
        print(f"  Overall Score:          {c.get('overall_score', '?')}/10  {verdict_emoji} {c.get('verdict', '?')}")
        print(f"  Playlist Fit:           {c.get('playlist_fit', '?')}/10")
        print(f"  Production Match:       {c.get('production_match', '?')}/10")
        print(f"  Emotional Authenticity: {c.get('emotional_authenticity', '?')}/10")
        print(f"  Closest Reference:      {c.get('closest_reference', '?')}")
        print(f"                          {c.get('closest_reference_reason', '')}")
        print(f"  Quality Gap:            {c.get('quality_gap', '')}")
        print(f"  Summary:                {c.get('summary', '')}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Score piano tracks against reference masterpieces")
    parser.add_argument("candidates", nargs="*", help="Candidate MP3 file(s) to score")
    parser.add_argument("--batch", metavar="DIR", help="Score all MP3s in a directory")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Output raw JSON")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model (default: gemini-2.5-flash)")
    args = parser.parse_args()

    if args.batch:
        candidates = sorted(glob.glob(os.path.join(args.batch, "*.mp3")))
        if not candidates:
            print(f"No MP3 files found in {args.batch}", file=sys.stderr)
            sys.exit(1)
    elif args.candidates:
        candidates = args.candidates
    else:
        parser.print_help()
        sys.exit(1)

    print(f"\n🎹 Piano Scorer — {len(candidates)} candidate(s) vs 3 references\n", file=sys.stderr)
    score_candidates(candidates, model=args.model, output_json=args.output_json)


if __name__ == "__main__":
    main()
