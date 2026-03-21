#!/usr/bin/env python3
"""
Piano Tiebreaker — Force-rank tied top clips head-to-head.

Takes a batch directory with scores.json, finds all clips tied at the top score,
uploads them to Gemini for comparative ranking, and picks a single winner.

Usage:
  python3 scripts/piano-tiebreaker.py <batch_dir>
  python3 scripts/piano-tiebreaker.py <batch_dir> --json
  python3 scripts/piano-tiebreaker.py <batch_dir> --model gemini-2.5-pro
"""

import google.genai as genai
import os
import sys
import json
import glob
import argparse

TIEBREAKER_PROMPT = """You are an expert playlist curator for Spotify's "Peaceful Piano" playlist.

You have {count} solo piano tracks that all scored equally well in initial screening. Your job is to listen to ALL of them and FORCE-RANK them from best (#1) to worst (#{count}).

NO TIES ALLOWED. You must pick a single #1.

Ranking criteria (in priority order):
1. **Would you actually add this to a real playlist?** — gut feeling, the "I'd listen to this again" test
2. **Emotional resonance** — does it make you feel something genuine?
3. **Production quality** — does the piano sound real, warm, natural?
4. **Memorability** — is there a hook, a moment, something that sticks?
5. **Flow** — does the track have a satisfying arc (beginning → middle → end)?

For each track, give:
- Rank (1 = best)
- One sentence on why it ranked where it did
- A "vibe tag" (2-3 words capturing the mood, e.g. "rainy nostalgia", "quiet triumph")

Respond in this exact JSON format:
```json
{{
  "rankings": [
    {{
      "rank": 1,
      "filename": "<name>",
      "reason": "<one sentence>",
      "vibe_tag": "<2-3 word mood>"
    }}
  ],
  "winner_summary": "<2-3 sentences on why #1 is the best of this batch>"
}}
```

Be decisive. Trust your ear. Pick the one you'd actually want to hear again."""


def upload_file_safe(client, filepath):
    """Upload file, handling non-ASCII filenames."""
    try:
        return client.files.upload(file=filepath)
    except UnicodeEncodeError:
        import shutil, tempfile
        ext = os.path.splitext(filepath)[1]
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False, prefix="tiebreak_")
        shutil.copy2(filepath, tmp.name)
        tmp.close()
        return client.files.upload(file=tmp.name)


def run_tiebreaker(batch_dir, model="gemini-2.5-flash", output_json=False):
    """Run tiebreaker on tied top-scoring clips in a batch."""
    scores_file = os.path.join(batch_dir, "scores.json")
    if not os.path.exists(scores_file):
        print(f"❌ No scores.json found in {batch_dir}", file=sys.stderr)
        sys.exit(1)

    with open(scores_file) as f:
        scores = json.load(f)

    candidates = scores.get("candidates", [])
    if not candidates:
        print("❌ No candidates in scores.json", file=sys.stderr)
        sys.exit(1)

    # Find the top score and all clips with that score
    top_score = max(c.get("overall_score", 0) for c in candidates)
    tied = [c for c in candidates if c.get("overall_score", 0) == top_score]

    if len(tied) <= 1:
        winner = tied[0] if tied else candidates[0]
        print(f"\n🏆 No tie — clear winner: {winner.get('filename', '?')} ({top_score}/10)")
        if output_json:
            print(json.dumps({"winner": winner, "tie": False}))
        return winner

    print(f"\n🔄 Tiebreaker needed: {len(tied)} clips tied at {top_score}/10", file=sys.stderr)
    for c in tied:
        print(f"   • {c.get('filename', '?')}", file=sys.stderr)

    # Find the actual mp3 files
    tied_files = []
    for c in tied:
        filename = c.get("filename", "")
        # Try exact match first, then glob
        filepath = os.path.join(batch_dir, filename)
        if not os.path.exists(filepath):
            # Try finding by partial name
            matches = glob.glob(os.path.join(batch_dir, f"*{filename}*"))
            if not matches:
                # Try without extension
                base = os.path.splitext(filename)[0]
                matches = glob.glob(os.path.join(batch_dir, f"*{base}*"))
            if matches:
                filepath = matches[0]
            else:
                print(f"  ⚠️  Can't find mp3 for {filename}, skipping", file=sys.stderr)
                continue

        tied_files.append((filepath, filename, c))

    if len(tied_files) <= 1:
        winner = tied_files[0][2] if tied_files else tied[0]
        print(f"\n🏆 Only one file found — winner by default: {winner.get('filename', '?')}")
        if output_json:
            print(json.dumps({"winner": winner, "tie": False}))
        return winner

    # Upload to Gemini for head-to-head
    api_key = os.popen('security find-generic-password -s "google-api-key" -w').read().strip()
    if not api_key:
        print("❌ Could not read google-api-key from keychain", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    parts = []
    for i, (filepath, filename, _) in enumerate(tied_files):
        print(f"  📎 Uploading: {filename}...", file=sys.stderr)
        f = upload_file_safe(client, filepath)
        parts.append(f"\n--- TRACK {i+1}: {filename} ---\n")
        parts.append(f)

    prompt = TIEBREAKER_PROMPT.format(count=len(tied_files))
    print(f"\n  🎧 Head-to-head ranking {len(tied_files)} clips...\n", file=sys.stderr)

    response = client.models.generate_content(
        model=model,
        contents=[prompt] + parts,
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
        print(f"⚠️  Could not parse tiebreaker response:\n{raw}", file=sys.stderr)
        # Fall back to first tied candidate
        winner = tied[0]
        if output_json:
            print(json.dumps({"winner": winner, "tie": True, "parse_error": True}))
        return winner

    # Save tiebreaker results
    tiebreaker_file = os.path.join(batch_dir, "tiebreaker.json")
    with open(tiebreaker_file, "w") as f:
        json.dump(result, f, indent=2)

    if output_json:
        print(json.dumps(result, indent=2))
    else:
        rankings = result.get("rankings", [])
        rankings.sort(key=lambda r: r.get("rank", 99))

        print(f"\n{'='*60}")
        print(f"  🎧 TIEBREAKER RESULTS ({len(rankings)} clips, all scored {top_score}/10)")
        print(f"{'='*60}\n")

        medals = ["🥇", "🥈", "🥉"] + [f"{i+1}." for i in range(3, 20)]
        for r in rankings:
            rank = r.get("rank", "?")
            medal = medals[rank - 1] if isinstance(rank, int) and rank <= len(medals) else f"#{rank}"
            print(f"  {medal} {r.get('filename', '?')}  [{r.get('vibe_tag', '')}]")
            print(f"     {r.get('reason', '')}")
            print()

        winner_summary = result.get("winner_summary", "")
        if winner_summary:
            print(f"  💬 {winner_summary}")

        print(f"\n  📁 Saved: {tiebreaker_file}")

    # Return the winner's original score data merged with tiebreaker info
    if result.get("rankings"):
        winner_filename = result["rankings"][0].get("filename", "")
        for _, fname, score_data in tied_files:
            if fname == winner_filename:
                score_data["tiebreaker_rank"] = 1
                score_data["vibe_tag"] = result["rankings"][0].get("vibe_tag", "")
                return score_data

    return tied[0]


def main():
    parser = argparse.ArgumentParser(description="Piano tiebreaker — force-rank tied top clips")
    parser.add_argument("batch_dir", help="Batch directory containing scores.json + mp3s")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Output JSON")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model")
    args = parser.parse_args()

    run_tiebreaker(args.batch_dir, model=args.model, output_json=args.output_json)


if __name__ == "__main__":
    main()
