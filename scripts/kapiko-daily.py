#!/usr/bin/env python3
"""
Kapiko Daily Pipeline — Full End-to-End Music Production

  1. Generate 50 Suno prompts (v2: multi-genre + artist-anchored + rich prompts)
  2. Fire all at Suno API → 100 clips
  3. Score each against 3 reference masterpieces
  4. Tiebreaker if needed → single winner
  5. Mood analysis → landscape + image prompt
  6. Nano Banana 2 → 1920x1080 capybara art
  7. Video prompt → subtle animation description
  8. MiniMax I2V → 6s cinemagraph clip
  9. FFmpeg assembly → loop clip + text overlay + mux audio
  10. Publish to YouTube @kapiko

Usage:
  python3 scripts/kapiko-daily.py                           # Full auto run
  python3 scripts/kapiko-daily.py --subgenre "Jazz Ballad"  # Force sub-genre
  python3 scripts/kapiko-daily.py --count 25                # Fewer prompts
  python3 scripts/kapiko-daily.py --skip-score              # Generate only
  python3 scripts/kapiko-daily.py --skip-video              # Audio pipeline only
  python3 scripts/kapiko-daily.py --no-publish              # Everything except YouTube upload
  python3 scripts/kapiko-daily.py --dry-run                 # Generate prompts only

Credits per run: 500 Suno + ~$0.30 MiniMax + ~$0.01 Gemini ≈ $0.31 + Suno credits
Time: ~45 min (Suno) + ~5 min (scoring) + ~5 min (video) ≈ ~55 min total
"""

import subprocess
import sys
import os
import json
import argparse
import time
import tempfile
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_GENERATOR = os.path.join(SCRIPT_DIR, "kapiko-prompt-generator-v2.py")
BATCH_SCRIPT = os.path.join(SCRIPT_DIR, "suno-piano-batch.py")
TIEBREAKER_SCRIPT = os.path.join(SCRIPT_DIR, "piano-tiebreaker.py")
PIANO_SCORER = os.path.join(SCRIPT_DIR, "piano-score.py")
GUITAR_SCORER = os.path.join(SCRIPT_DIR, "gemini-guitar-scorer.py")
MOOD_ANALYZER = os.path.join(SCRIPT_DIR, "kapiko-mood-analyzer.py")
IMAGE_GEN = os.path.join(SCRIPT_DIR, "kapiko-image-gen.py")
VIDEO_PROMPT = os.path.join(SCRIPT_DIR, "kapiko-video-prompt.py")
MINIMAX_VIDEO = os.path.join(SCRIPT_DIR, "minimax-video.py")
VIDEO_ASSEMBLY = os.path.join(SCRIPT_DIR, "kapiko-video-assembly.py")
OUTPUT_BASE = os.path.expanduser("~/Documents/music/kapiko")


def run_step(label, cmd, check=True, capture=False):
    """Run a command, stream output, return result."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}\n")
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    else:
        result = subprocess.run(cmd, text=True)
    if check and result.returncode != 0:
        print(f"\n❌ Step failed: {label}", file=sys.stderr)
        if capture and result.stderr:
            print(result.stderr[-500:], file=sys.stderr)
        return None
    return result


def resolve_mp3_path(batch_dir, filename):
    """Resolve an mp3 filename to its full path in the batch directory."""
    import glob
    if not filename:
        return None
    filepath = os.path.join(batch_dir, filename)
    if os.path.exists(filepath):
        return filepath
    matches = glob.glob(os.path.join(batch_dir, f"*{filename}*"))
    if matches:
        return matches[0]
    base = os.path.splitext(filename)[0]
    matches = glob.glob(os.path.join(batch_dir, f"*{base}*"))
    if matches:
        return matches[0]
    return None


def find_top_n_mp3s(batch_dir, scores_file, tiebreaker_file=None, n=1):
    """Find the top N mp3 file paths from scores. Returns list of (path, title)."""
    ranked_filenames = []

    # Check tiebreaker first (it has a definitive ranking)
    if tiebreaker_file and os.path.exists(tiebreaker_file):
        with open(tiebreaker_file) as f:
            tb = json.load(f)
        rankings = tb.get("rankings", [])
        if rankings:
            rankings.sort(key=lambda r: r.get("rank", 99))
            ranked_filenames = [r.get("filename", "") for r in rankings]

    # Fall back to / supplement with scores
    if len(ranked_filenames) < n and os.path.exists(scores_file):
        with open(scores_file) as f:
            scores = json.load(f)
        candidates = scores.get("candidates", [])
        if candidates:
            candidates.sort(key=lambda c: c.get("overall_score", 0), reverse=True)
            for c in candidates:
                fn = c.get("filename", "")
                if fn and fn not in ranked_filenames:
                    ranked_filenames.append(fn)

    # Resolve to actual paths and clean titles
    results = []
    for fn in ranked_filenames[:n]:
        path = resolve_mp3_path(batch_dir, fn)
        if path:
            title = os.path.splitext(os.path.basename(path))[0]
            if "-" in title:
                parts = title.rsplit("-", 1)
                if len(parts[1]) == 8:
                    title = parts[0].replace("-", " ").strip()
            results.append((path, title))

    return results


def find_winner_mp3(batch_dir, scores_file, tiebreaker_file=None):
    """Find the winning mp3 file path from scores (legacy single-winner)."""
    results = find_top_n_mp3s(batch_dir, scores_file, tiebreaker_file, n=1)
    return results[0][0] if results else None


def main():
    parser = argparse.ArgumentParser(description="Kapiko Daily Pipeline — Full End-to-End")
    parser.add_argument("--subgenre", type=str, help="Force a specific sub-genre")
    parser.add_argument("--subgenres", type=int, help="Number of random sub-genres (default: 5-10)")
    parser.add_argument("--count", type=int, default=30, help="Number of prompts (default: 30)")
    parser.add_argument("--model", default="chirp-crow", help="Suno model (default: chirp-crow/v5)")
    parser.add_argument("--skip-score", action="store_true", help="Skip scoring step")
    parser.add_argument("--skip-video", action="store_true", help="Skip video pipeline (audio only)")
    parser.add_argument("--no-publish", action="store_true", help="Skip YouTube upload")
    parser.add_argument("--dry-run", action="store_true", help="Generate prompts only")
    parser.add_argument("--delay", type=int, default=5, help="Seconds between Suno submissions")
    parser.add_argument("--poll-interval", type=int, default=20, help="Seconds between status polls")
    parser.add_argument("--timeout", type=int, default=1800, help="Max seconds for Suno generation")
    parser.add_argument("--top", type=int, default=1, help="Publish top N winners (default: 1)")
    parser.add_argument("--prompts-file", help="Use pre-written prompts JSON file (skip prompt generation)")
    parser.add_argument("--instrument", default="piano", choices=["piano", "guitar"], help="Instrument for YouTube metadata (default: piano)")
    # Resume from a specific step with existing files
    parser.add_argument("--winner-mp3", help="Skip to video pipeline with this mp3")
    parser.add_argument("--winner-title", help="Song title (used with --winner-mp3)")
    args = parser.parse_args()

    date_str = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(OUTPUT_BASE, date_str)
    os.makedirs(run_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  🎹 KAPIKO DAILY PIPELINE — {date_str}")
    print(f"{'='*60}")
    print(f"  Prompts: {args.count} | Model: {args.model}")
    print(f"  Output: {run_dir}")
    print(f"  Video: {'skip' if args.skip_video else 'yes'} | Publish: {'skip' if args.no_publish else 'yes'}")

    winner_mp3 = None
    winner_title = None
    subgenre = "Unknown"
    batch_dir = None

    winners = []  # list of (mp3_path, title) tuples

    # ─── RESUME MODE ───
    if args.winner_mp3:
        winner_mp3 = args.winner_mp3
        winner_title = args.winner_title or os.path.splitext(os.path.basename(winner_mp3))[0]
        winners = [(winner_mp3, winner_title)]
        print(f"\n  ⏩ Resuming from video pipeline with: {winner_mp3}")
    else:
        # ─── STEP 1: Generate/Load Prompts ───
        if args.prompts_file:
            # Use pre-written prompts file directly
            prompts_file = args.prompts_file
            print(f"\n  📂 Using pre-written prompts: {prompts_file}")
            with open(prompts_file) as f:
                prompt_data = json.load(f)
            # Pre-written files are just [{title, prompt}] arrays
            if isinstance(prompt_data, list):
                num_prompts = len(prompt_data)
                subgenre = "Acoustic Guitar (pre-written)"
                print(f"  📝 {num_prompts} prompts loaded")
            elif "genre_distribution" in prompt_data:
                genres = prompt_data["genre_distribution"]
                subgenre = " + ".join(genres.keys())
                print(f"\n  🎲 Today's sub-genres ({len(genres)}):")
                for g, n in genres.items():
                    print(f"     • {g}: {n} prompts")
            else:
                subgenre = prompt_data.get("subgenre", "Unknown")
                print(f"\n  🎲 Today's sub-genre: {subgenre}")
        else:
            prompts_file = os.path.join(run_dir, f"prompts-{timestamp}.json")
            gen_cmd = [
                sys.executable, PROMPT_GENERATOR,
                "--count", str(args.count),
                "--output", prompts_file,
            ]
            if args.subgenre:
                gen_cmd += ["--subgenre", args.subgenre]
            if args.subgenres:
                gen_cmd += ["--subgenres", str(args.subgenres)]

            result = run_step("STEP 1: Generate Prompts", gen_cmd)
            if result is None:
                sys.exit(1)

            with open(prompts_file) as f:
                prompt_data = json.load(f)
            if "genre_distribution" in prompt_data:
                genres = prompt_data["genre_distribution"]
                subgenre = " + ".join(genres.keys())
                print(f"\n  🎲 Today's sub-genres ({len(genres)}):")
                for g, n in genres.items():
                    print(f"     • {g}: {n} prompts")
            else:
                subgenre = prompt_data.get("subgenre", "Unknown")
                print(f"\n  🎲 Today's sub-genre: {subgenre}")

        if args.dry_run:
            print(f"\n  🏁 Dry run complete. Prompts: {prompts_file}")
            return

        # ─── STEP 2: Generate + Download ───
        batch_cmd = [
            sys.executable, BATCH_SCRIPT,
            "--prompts-file", prompts_file,
            "--model", args.model,
            "--output-dir", run_dir,
            "--delay", str(args.delay),
            "--poll-interval", str(args.poll_interval),
            "--timeout", str(args.timeout),
            "--skip-score",  # We handle scoring separately for tiebreaker
        ]
        result = run_step("STEP 2: Generate + Download", batch_cmd)
        if result is None:
            sys.exit(1)

        # Find the batch subdirectory
        subdirs = sorted([
            d for d in os.listdir(run_dir)
            if os.path.isdir(os.path.join(run_dir, d)) and d[0].isdigit()
        ])
        if not subdirs:
            print("❌ No batch directory found", file=sys.stderr)
            sys.exit(1)

        batch_dir = os.path.join(run_dir, subdirs[-1])
        scores_file = os.path.join(batch_dir, "scores.json")
        tiebreaker_file = os.path.join(batch_dir, "tiebreaker.json")

        if not args.skip_score:
            # ─── STEP 3: Score tracks ───
            import glob
            mp3s = sorted(glob.glob(os.path.join(batch_dir, "*.mp3")))
            if not mp3s:
                print("❌ No mp3s found in batch directory", file=sys.stderr)
                sys.exit(1)

            if args.instrument == "guitar":
                # Use guitar-specific scorer (no reference tracks — standalone eval)
                score_cmd = [
                    sys.executable, GUITAR_SCORER,
                    batch_dir,
                ]
                result = run_step("STEP 3: Score Guitar Tracks (Gemini)", score_cmd, capture=False)
                # gemini-guitar-scorer.py writes guitar-scores.json into batch_dir
                guitar_scores_file = os.path.join(batch_dir, "guitar-scores.json")
                if os.path.exists(guitar_scores_file):
                    with open(guitar_scores_file) as f:
                        guitar_data = json.load(f)
                    # Convert guitar scorer format to standard candidates format
                    candidates = []
                    for r in guitar_data.get("rankings", guitar_data.get("all_results", [])):
                        if "error" not in r and "overall_score" in r:
                            candidates.append({
                                "filename": r.get("filename", ""),
                                "overall_score": r.get("overall_score", 0),
                                "playlist_fit": r.get("replay_value", 0),
                                "production_match": r.get("production", 0),
                                "emotional_authenticity": r.get("emotional_impact", 0),
                                "verdict": "PASS" if r.get("overall_score", 0) >= 7 else "BORDERLINE" if r.get("overall_score", 0) >= 5 else "FAIL",
                                "summary": r.get("one_line_review", ""),
                            })
                    score_data = {"candidates": candidates}
                    with open(scores_file, "w") as f:
                        json.dump(score_data, f, indent=2)
                    print(f"  📁 Guitar scores converted & saved: {scores_file}")
            else:
                # Piano: score against reference masterpieces
                score_cmd = [
                    sys.executable, PIANO_SCORER,
                    "--json", "--model", "gemini-2.5-flash",
                ] + mp3s

                result = run_step("STEP 3: Score Against Piano Masterpieces", score_cmd, capture=True)
                if result and result.stdout:
                    # Save scores
                    try:
                        score_data = json.loads(result.stdout)
                        with open(scores_file, "w") as f:
                            json.dump(score_data, f, indent=2)
                        print(f"  📁 Scores saved: {scores_file}")
                    except json.JSONDecodeError:
                        print("  ⚠️  Could not parse scores JSON", file=sys.stderr)

            # ─── STEP 4: Tiebreaker if needed ───
            if os.path.exists(scores_file):
                with open(scores_file) as f:
                    scores = json.load(f)
                candidates = scores.get("candidates", [])
                if candidates:
                    top_score = max(c.get("overall_score", 0) for c in candidates)
                    tied = [c for c in candidates if c.get("overall_score", 0) == top_score]

                    if len(tied) > 1:
                        run_step(
                            f"STEP 4: Tiebreaker — {len(tied)} clips tied at {top_score}/10",
                            [sys.executable, TIEBREAKER_SCRIPT, batch_dir],
                        )
                    else:
                        print(f"\n  🏆 Clear winner at {top_score}/10 — no tiebreaker needed")

            # Find top N winners
            winners = find_top_n_mp3s(batch_dir, scores_file, tiebreaker_file, n=args.top)
            if not winners:
                # Fall back to first mp3(s)
                mp3s = sorted(glob.glob(os.path.join(batch_dir, "*.mp3")))
                if mp3s:
                    for mp3_path in mp3s[:args.top]:
                        title = os.path.splitext(os.path.basename(mp3_path))[0]
                        winners.append((mp3_path, title))
                    print(f"\n  ⚠️  Could not determine winners from scores, using first {len(winners)} track(s)")
                else:
                    print("❌ No mp3s available", file=sys.stderr)
                    sys.exit(1)

            for i, (wp, wt) in enumerate(winners):
                print(f"\n  🏆 #{i+1}: {wt}")
                print(f"     File: {wp}")

    # Legacy compat
    winner_mp3 = winners[0][0] if winners else None
    winner_title = winners[0][1] if winners else None

    if args.skip_video:
        print(f"\n  🏁 Audio pipeline complete. {len(winners)} winner(s):")
        for i, (wp, wt) in enumerate(winners):
            print(f"     #{i+1}: {wt}")
        run_info = {
            "date": date_str,
            "subgenre": subgenre,
            "winners": [{"mp3": wp, "title": wt} for wp, wt in winners],
            "winner_mp3": winner_mp3,
            "winner_title": winner_title,
            "batch_dir": batch_dir,
        }
        with open(os.path.join(run_dir, "run-info.json"), "w") as f:
            json.dump(run_info, f, indent=2)
        return

    # ═══════════════════════════════════════════
    #  VIDEO PIPELINE (Steps 5-10) — per winner
    # ═══════════════════════════════════════════

    all_videos = []
    all_moods = []

    for wi, (w_mp3, w_title) in enumerate(winners):
        suffix = f"-{wi+1}" if len(winners) > 1 else ""
        print(f"\n{'='*60}")
        print(f"  🎬 VIDEO PIPELINE — Winner #{wi+1}/{len(winners)}: {w_title}")
        print(f"{'='*60}")

        mood_file = os.path.join(run_dir, f"mood{suffix}.json")
        image_file = os.path.join(run_dir, f"capybara{suffix}.png")
        video_prompt_file = os.path.join(run_dir, f"video-prompt{suffix}.json")
        clip_file = os.path.join(run_dir, f"clip{suffix}.mp4")
        final_video = os.path.join(run_dir, f"kapiko-{date_str}{suffix}.mp4")

        # ─── STEP 5: Mood Analysis ───
        result = run_step(
            f"STEP 5.{wi+1}: Mood Analysis — {w_title}",
            [sys.executable, MOOD_ANALYZER, w_mp3, "--json", "--output", mood_file],
            capture=True,
        )
        if result and result.stdout:
            try:
                mood_data = json.loads(result.stdout)
                with open(mood_file, "w") as f:
                    json.dump(mood_data, f, indent=2)
            except json.JSONDecodeError:
                pass

        if not os.path.exists(mood_file):
            print(f"❌ Mood analysis failed for winner #{wi+1}", file=sys.stderr)
            continue

        with open(mood_file) as f:
            mood_data = json.load(f)

        print(f"  🎨 Mood: {mood_data.get('mood', '?')}")
        print(f"  🏞️  Landscape: {mood_data.get('landscape_type', '?')}")

        # ─── STEP 6: Image Generation ───
        result = run_step(
            f"STEP 6.{wi+1}: Image Generation — Nano Banana 2 capybara art",
            [sys.executable, IMAGE_GEN, "--mood", mood_file, "--output", image_file],
        )
        if result is None or not os.path.exists(image_file):
            print(f"❌ Image generation failed for winner #{wi+1}", file=sys.stderr)
            continue

        # ─── STEP 7: Video Prompt ───
        result = run_step(
            f"STEP 7.{wi+1}: Video Prompt — Analyze image, create animation",
            [sys.executable, VIDEO_PROMPT, "--image", image_file, "--mood", mood_file, "--json", "--output", video_prompt_file],
            capture=True,
        )
        if result and result.stdout:
            try:
                vp_data = json.loads(result.stdout)
                with open(video_prompt_file, "w") as f:
                    json.dump(vp_data, f, indent=2)
            except json.JSONDecodeError:
                pass

        if not os.path.exists(video_prompt_file):
            print(f"❌ Video prompt generation failed for winner #{wi+1}", file=sys.stderr)
            continue

        with open(video_prompt_file) as f:
            vp_data = json.load(f)

        animation_prompt = vp_data.get("video_prompt", "")
        print(f"  🎬 Animation: {animation_prompt[:80]}...")

        # ─── STEP 8: MiniMax I2V ───
        result = run_step(
            f"STEP 8.{wi+1}: MiniMax I2V — Generate 6s cinemagraph clip",
            [
                sys.executable, MINIMAX_VIDEO, "i2v",
                image_file,
                "-p", animation_prompt,
                "-o", clip_file,
                "-r", "1080P",
                "-a", "16:9",
                "--no-optimize",
            ],
        )
        if result is None or not os.path.exists(clip_file):
            print(f"❌ MiniMax I2V failed for winner #{wi+1}", file=sys.stderr)
            continue

        # ─── STEP 9: Video Assembly ───
        assembly_cmd = [
            sys.executable, VIDEO_ASSEMBLY,
            "--clip", clip_file,
            "--audio", w_mp3,
            "--title", w_title,
            "--mood", mood_file,
            "--instrument", args.instrument,
            "--output", final_video,
        ]
        if not args.no_publish:
            assembly_cmd.append("--publish")

        result = run_step(
            f"STEP 9.{wi+1}: Video Assembly — Loop + overlay + mux + publish",
            assembly_cmd,
        )

        if os.path.exists(final_video):
            all_videos.append({"title": w_title, "path": final_video, "mood": mood_data})
            all_moods.append(mood_data)

    # ─── FINAL SUMMARY ───
    print(f"\n{'='*60}")
    print(f"  🏁 KAPIKO DAILY COMPLETE — {date_str}")
    print(f"{'='*60}")
    print(f"  Sub-genre:  {subgenre}")
    print(f"  Winners:    {len(winners)} selected, {len(all_videos)} published")
    for i, v in enumerate(all_videos):
        size_mb = os.path.getsize(v["path"]) / (1024 * 1024) if os.path.exists(v["path"]) else 0
        print(f"  #{i+1}: {v['title']} ({size_mb:.1f}MB) — mood: {v['mood'].get('mood', '?')}")
    print(f"  Published:  {'yes' if not args.no_publish else 'no'}")
    print(f"  📁 Run dir: {run_dir}")

    # Save full run manifest
    run_manifest = {
        "date": date_str,
        "timestamp": timestamp,
        "subgenre": subgenre,
        "winners": [{"title": wt, "mp3": wp} for wp, wt in winners],
        "videos": all_videos,
        "batch_dir": batch_dir,
        "published": not args.no_publish,
    }
    with open(os.path.join(run_dir, "manifest.json"), "w") as f:
        json.dump(run_manifest, f, indent=2)

    print(f"\n  ✅ All done. kapiko out. 🦫🎹\n")


if __name__ == "__main__":
    main()
