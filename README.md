# kapiko 🎵🐭

AI music factory — daily automated music generation, scoring, video assembly, and YouTube publishing.

## What is kapiko?

kapiko is an end-to-end pipeline that:
1. Generates music prompts for specific genres/instruments
2. Creates 100 clips via Suno AI
3. Scores them against masterpiece references using Gemini
4. Analyzes mood and generates matching artwork (Nano Banana 2)
5. Creates cinemagraph video (MiniMax I2V)
6. Assembles final video with overlays (FFmpeg)
7. Publishes to YouTube (@kapiko-music)

## Pipeline

```
Random sub-genre → 50 Suno prompts → 100 clips → Gemini scoring → Tiebreaker
→ Mood analysis → NB2 capybara art → MiniMax I2V → FFmpeg assembly → YouTube
```

## Scripts

| Script | Purpose |
|--------|---------|
| `kapiko-daily.py` | Main orchestrator — runs the full pipeline |
| `kapiko-prompt-generator.py` | Generates Suno prompts for a genre |
| `kapiko-prompt-generator-v2.py` | V2 prompt generator with improvements |
| `gemini-piano-scorer.py` | Scores piano tracks against masterpieces |
| `gemini-guitar-scorer.py` | Scores guitar tracks against masterpieces |
| `piano-score.py` | Legacy piano scorer |
| `piano-tiebreaker.py` | Breaks ties between top-scoring tracks |
| `kapiko-mood-analyzer.py` | Analyzes winning track mood for artwork |
| `kapiko-image-gen.py` | Generates capybara artwork via NB2 |
| `kapiko-video-prompt.py` | Creates video prompt from mood |
| `kapiko-video-assembly.py` | FFmpeg assembly with overlays |
| `kapiko-overlay.sh` | Text overlay helper |
| `kapiko-youtube-upload.py` | YouTube upload via OAuth2 |

## Rules

- Capybara always wears over-ear headphones
- Pacifico font for text overlays
- "Living painting" animation style (no camera movement)
- Title format: `Song Name [Single - Solo Piano] - kapiko`

## Cost

~500 Suno credits + ~$0.31 cash per run

## YouTube

Channel: [@kapiko-music](https://youtube.com/@kapiko-music) (`UCiAd8cFRo58SzdhfE-oxnvA`)
