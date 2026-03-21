#!/usr/bin/env python3
"""Score solo piano mp3s using Gemini audio analysis."""
import subprocess, json, sys, os, base64, time
import google.generativeai as genai

# Get API key
api_key = subprocess.run(
    ["security", "find-generic-password", "-s", "google-api-key", "-w"],
    capture_output=True, text=True
).stdout.strip()
genai.configure(api_key=api_key)

SCORING_PROMPT = """You are an expert music critic and Spotify playlist curator specializing in solo piano covers.

Score this solo piano audio clip on these 5 criteria (1-10 scale):

1. **Emotional Impact** — Does it move you? Does it capture feeling, not just notes?
2. **Piano Tone Quality** — Is the piano sound warm, natural, rich? Or thin, digital, harsh?
3. **Arrangement Sophistication** — Beyond just playing the melody. Are there interesting harmonies, voicings, dynamics?
4. **Spotify Playlist Fit** — Would this blend into "Peaceful Piano" or "Piano Covers" playlists? Professional enough?
5. **Replay Value** — Would you listen again? Is there a memorable moment or hook?

Also evaluate:
- **Is it actually solo piano?** (deduct heavily if there are vocals, drums, or other instruments)
- **Does it sound like a recognizable cover of "Cruel Summer"?** (bonus if the melody is clearly identifiable)
- **Recording quality** — any artifacts, clipping, or unnatural sounds?

Return your response as JSON only, no other text:
{
  "emotional_impact": <1-10>,
  "piano_tone": <1-10>,
  "arrangement": <1-10>,
  "playlist_fit": <1-10>,
  "replay_value": <1-10>,
  "overall_score": <1-10>,
  "is_solo_piano": true/false,
  "recognizable_melody": true/false,
  "one_line_review": "<brief one-line review>",
  "standout_quality": "<what makes this clip special or weak>",
  "deductions": "<any issues: vocals, artifacts, wrong instrument, etc.>"
}
"""

def score_clip(filepath):
    """Score a single mp3 file using Gemini."""
    print(f"  Scoring: {os.path.basename(filepath)}...")
    
    # Upload the file
    audio_file = genai.upload_file(filepath, mime_type="audio/mpeg")
    
    # Wait for processing
    while audio_file.state.name == "PROCESSING":
        time.sleep(2)
        audio_file = genai.get_file(audio_file.name)
    
    if audio_file.state.name == "FAILED":
        return {"error": f"Upload failed for {filepath}"}
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        [SCORING_PROMPT, audio_file],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.3
        )
    )
    
    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        text = response.text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            result = json.loads(text[start:end])
        else:
            result = {"error": "Could not parse response", "raw": text[:500]}
    
    # Clean up uploaded file
    try:
        genai.delete_file(audio_file.name)
    except:
        pass
    
    return result

def main():
    mp3_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/suno-piano"
    
    # Find all piano mp3s (exclude old "unknown" files)
    mp3s = sorted([
        os.path.join(mp3_dir, f) for f in os.listdir(mp3_dir)
        if f.endswith('.mp3') and not f.startswith('unknown')
    ])
    
    if not mp3s:
        print("No mp3 files found!")
        return
    
    print(f"Scoring {len(mp3s)} clips...\n")
    
    results = []
    for filepath in mp3s:
        try:
            score = score_clip(filepath)
            score['filename'] = os.path.basename(filepath)
            score['filepath'] = filepath
            results.append(score)
            
            if 'error' not in score:
                print(f"    → {score.get('overall_score', '?')}/10 | {score.get('one_line_review', 'N/A')}")
            else:
                print(f"    → ERROR: {score['error']}")
            
            time.sleep(1)  # Rate limit courtesy
        except Exception as e:
            print(f"    → EXCEPTION: {e}")
            results.append({'filename': os.path.basename(filepath), 'error': str(e)})
    
    # Sort by overall score
    scored = [r for r in results if 'error' not in r and 'overall_score' in r]
    scored.sort(key=lambda x: x['overall_score'], reverse=True)
    
    print(f"\n{'='*60}")
    print("RANKINGS")
    print(f"{'='*60}")
    for i, r in enumerate(scored):
        piano = "🎹" if r.get('is_solo_piano') else "⚠️"
        melody = "✅" if r.get('recognizable_melody') else "❌"
        print(f"\n#{i+1} {piano} {r['filename']}")
        print(f"   Overall: {r['overall_score']}/10 | Emotion: {r['emotional_impact']} | Tone: {r['piano_tone']} | Arrangement: {r['arrangement']} | Playlist: {r['playlist_fit']} | Replay: {r['replay_value']}")
        print(f"   Melody recognizable: {melody}")
        print(f"   Review: {r['one_line_review']}")
        print(f"   Standout: {r.get('standout_quality', 'N/A')}")
        if r.get('deductions'):
            print(f"   Deductions: {r['deductions']}")
    
    print(f"\n{'='*60}")
    print("TOP 3 PICKS")
    print(f"{'='*60}")
    for i, r in enumerate(scored[:3]):
        print(f"  🏆 #{i+1}: {r['filename']} — {r['overall_score']}/10 — {r['one_line_review']}")
    
    # Save full results
    output_path = os.path.join(mp3_dir, "gemini-scores.json")
    with open(output_path, 'w') as f:
        json.dump({'rankings': scored, 'all_results': results}, f, indent=2)
    print(f"\nFull results saved to {output_path}")

if __name__ == "__main__":
    main()
