#!/usr/bin/env python3
"""
Kapiko Prompt Generator v2
Lessons from Mar 14-15: diverse sub-genres + artist references + deep prompts = quality.

Key changes from v1:
  1. Multi-subgenre batches (5-10 genres per 50 prompts, not 1)
  2. Every subgenre has reference artist anchors
  3. Rich prompts (300-450 chars) — uses full Suno 500-char limit
  4. Emotional variation strategies per prompt
  5. Recording/production texture baked in
  6. No more "mood, tempo. key, technique." templates — each prompt is a paragraph

Usage:
  python3 scripts/kapiko-prompt-generator-v2.py [--count 50] [--output /tmp/prompts.json]
  python3 scripts/kapiko-prompt-generator-v2.py --subgenre "Jazz Ballad"
  python3 scripts/kapiko-prompt-generator-v2.py --list-subgenres
  python3 scripts/kapiko-prompt-generator-v2.py --subgenres 3   # pick 3 random genres
"""

import json, random, sys, argparse
from datetime import datetime

# ─── Sub-genres with reference artists ─────────────────────────────────────────
# Each has 2-4 reference artists that give Suno a concrete sonic target.
# "palette" = musical building blocks the prompt can draw from.
SUBGENRES = [
    # Classical & Traditional
    {
        "name": "Classical Nocturne",
        "artists": ["Chopin", "John Field", "Gabriel Fauré"],
        "palette": ["expressive rubato", "singing right-hand melody", "gentle left-hand arpeggios", "dynamic shading from pp to mf", "lyrical phrasing", "pedal-sustained harmonies", "bel canto melodic line", "tender ornamental turns"],
        "recording": ["close-miked Steinway, warm natural reverb", "intimate recital hall, felt hammers audible"],
        "core_feel": "Late-night intimacy, a single candle flickering. The melody should sing like a human voice.",
    },
    {
        "name": "Romantic Étude",
        "artists": ["Liszt", "Rachmaninoff", "Scriabin"],
        "palette": ["virtuosic octave passages", "thundering bass", "soaring melodic climax", "dramatic dynamic arc", "rapid scale runs", "thick chordal texture", "passionate rubato", "heroic theme"],
        "recording": ["concert hall ambience, full resonance", "Steinway D, rich bass, brilliant treble"],
        "core_feel": "Grand romantic statement. Technical brilliance in service of overwhelming emotion.",
    },
    {
        "name": "Impressionist",
        "artists": ["Debussy", "Ravel", "Satie"],
        "palette": ["whole-tone washes", "parallel chords moving in blocks", "pentatonic melody floating over rich harmony", "sustained pedal creating color clouds", "gentle modal shifts", "bell-like upper register", "liquid arpeggios", "unresolved harmonies"],
        "recording": ["roomy recording with natural decay", "soft-pedaled Bösendorfer, warm and round"],
        "core_feel": "Watercolor in sound. Colors and textures over strict melody. Dreamy, shimmering, never heavy.",
    },
    {
        "name": "Classical Sonata",
        "artists": ["Mozart", "Beethoven", "Schubert"],
        "palette": ["clear melodic themes", "Alberti bass accompaniment", "elegant phrasing", "balanced dynamics", "development and recapitulation", "precise articulation", "singing legato passages"],
        "recording": ["bright concert grand, crystal clarity", "pristine studio, clean and balanced"],
        "core_feel": "Architectural beauty. Every note purposeful, structured yet deeply expressive.",
    },

    # Modern Classical & Art Music
    {
        "name": "Minimalist",
        "artists": ["Philip Glass", "Steve Reich", "Terry Riley"],
        "palette": ["repeating arpeggiated patterns that slowly evolve", "additive rhythmic process", "hypnotic pulse", "gradual harmonic shifts over long spans", "interlocking patterns", "trance-like repetition with micro-variations"],
        "recording": ["close-miked, dry studio, every note precise", "intimate room, minimal reverb"],
        "core_feel": "Meditative and hypnotic. The repetition isn't boring — it's transcendent. Small changes feel enormous.",
    },
    {
        "name": "Neo-Classical",
        "artists": ["Ólafur Arnalds", "Nils Frahm", "Joep Beving"],
        "palette": ["sparse tender melody", "felt piano warmth", "subtle electronic-influenced sensibility", "long pauses that breathe", "simple chords with complex emotion", "intimate close-miked imperfections"],
        "recording": ["felt piano, very close mic, room noise audible", "warm intimate studio, slightly lo-fi"],
        "core_feel": "Modern, intimate, slightly melancholic. The space between notes matters as much as the notes.",
    },
    {
        "name": "Post-Minimalist",
        "artists": ["Max Richter", "Dustin O'Halloran", "Jóhann Jóhannsson"],
        "palette": ["slow-building emotional arc", "sustained notes with long decay", "simple theme that accumulates power through repetition", "cinematic scope at the piano", "deep bass register anchoring", "cathartic release after patient build"],
        "recording": ["concert hall reverb, spacious and deep", "studio grand with generous natural reverb"],
        "core_feel": "Emotional minimalism with cinematic weight. Patient, profound, building toward catharsis.",
    },

    # Jazz & Blues
    {
        "name": "Jazz Ballad",
        "artists": ["Bill Evans", "Keith Jarrett", "Brad Mehldau"],
        "palette": ["rootless voicings with 9ths and 13ths", "introspective swing feel", "reharmonized standards feel", "subtle left-hand comping", "right-hand improvisatory melody", "suspended chords resolving unexpectedly", "rubato phrasing over implied time"],
        "recording": ["intimate jazz club, close-miked, slight room ambience", "warm studio Steinway, clean and dry"],
        "core_feel": "2 AM at the Village Vanguard. Sophisticated harmony, but the emotion is what hits you. Never show-offy — deeply felt.",
    },
    {
        "name": "Stride Piano",
        "artists": ["Art Tatum", "Fats Waller", "Oscar Peterson"],
        "palette": ["leaping left-hand stride bass", "rapid right-hand runs", "exuberant swing", "virtuosic showmanship", "playful rhythmic surprises", "boogie-woogie left-hand patterns", "ornamental flourishes"],
        "recording": ["warm vintage recording feel", "bright studio piano, full dynamic range"],
        "core_feel": "Joyful virtuosity. The left hand is the whole rhythm section. Infectious, swinging, irresistible.",
    },
    {
        "name": "Blues Piano",
        "artists": ["Otis Spann", "Professor Longhair", "Ray Charles"],
        "palette": ["12-bar blues progression", "bent-note blues feel", "walking bass in left hand", "call-and-response between hands", "raw emotional phrasing", "tremolo and vibrato effects", "smoky minor pentatonic melody"],
        "recording": ["slightly overdriven vintage mic, warm and raw", "honky-tonk room feel, lived-in sound"],
        "core_feel": "Smoky, soulful, lived-in. Every note carries the weight of experience. Raw over polished.",
    },
    {
        "name": "Gospel Piano",
        "artists": ["Thelonious Monk's churchy side", "Ray Charles", "Aretha Franklin's pianist"],
        "palette": ["jubilant chord runs", "call-and-response feel", "soulful bass-register chords", "right-hand gospel runs and fills", "building intensity like a sermon", "major key triumph", "rhythmic drive and clapping feel"],
        "recording": ["roomy church-like reverb", "warm and present, full-bodied"],
        "core_feel": "Sunday morning uplift. Jubilant, soulful, building to a praise break. Infectious joy.",
    },
    {
        "name": "Cool Jazz Piano",
        "artists": ["Dave Brubeck", "Ahmad Jamal", "Thelonious Monk"],
        "palette": ["spacious voicings with room to breathe", "sophisticated harmony", "relaxed swing feel", "unexpected rhythmic accents", "understated elegance", "odd-time feel possibilities"],
        "recording": ["classic Blue Note recording aesthetic", "warm studio, slight room reverb"],
        "core_feel": "Effortlessly sophisticated. Cool but not cold. The spaces and silences are as important as the notes.",
    },

    # Ambient & Atmospheric
    {
        "name": "Ambient Piano",
        "artists": ["Brian Eno", "Harold Budd", "Lubomyr Melnyk"],
        "palette": ["long sustained tones with heavy reverb", "floating arpeggios in upper register", "no clear pulse or rhythm", "notes bleeding into each other", "overtone-rich sustained pedal", "weightless and hovering"],
        "recording": ["drenched in reverb, cathedral-like space", "distant mic placement, atmospheric"],
        "core_feel": "Sound as environment. Not a performance — an atmosphere. Weightless, timeless, dissolving.",
    },
    {
        "name": "Dark Ambient Piano",
        "artists": ["Nils Frahm's darker work", "The Caretaker", "William Basinski"],
        "palette": ["deep bass register rumble", "dissonant undertones", "sparse notes in low register", "unsettling beauty", "slow decay into silence", "minor 2nd intervals creating tension", "isolated single notes with long reverb tails"],
        "recording": ["cavernous reverb, distant and cold", "lo-fi degraded quality, tape-worn"],
        "core_feel": "Beautiful but unsettling. An empty cathedral at midnight. Tension that never fully resolves.",
    },
    {
        "name": "Celestial Piano",
        "artists": ["Goldmund", "Ólafur Arnalds", "Yiruma"],
        "palette": ["crystalline upper-register arpeggios", "sparkling repeated patterns", "bell-like clarity", "ascending melodic lines", "major/lydian tonality", "delicate grace notes", "shimmering tremolo"],
        "recording": ["pristine studio, crystal clear, bright", "close-miked with sparkle EQ"],
        "core_feel": "Starlight translated to sound. Crystalline, ascending, wonder-filled. Light and sparkling.",
    },

    # Cinematic & Emotional
    {
        "name": "Cinematic Emotional",
        "artists": ["Yiruma", "Ludovico Einaudi", "Alexis Ffrench"],
        "palette": ["accessible sweeping melody", "gradual emotional build from sparse to full", "arpeggiated left-hand foundation", "right-hand melody that sings", "cathartic dynamic climax then gentle resolution", "repeating motif that gains power each time"],
        "recording": ["warm studio grand, rich and full", "close-miked with gentle room reverb"],
        "core_feel": "The movie scene where everything comes together. Accessible, sweeping, emotional without being cheesy.",
    },
    {
        "name": "Film Noir Piano",
        "artists": ["Thelonious Monk", "Duke Ellington", "Henry Mancini"],
        "palette": ["smoky minor-key melody", "sultry chromatic lines", "mysterious tension", "jazz-inflected harmony", "sparse left-hand punctuation", "dim7 and augmented chords", "suspenseful pauses"],
        "recording": ["vintage warm recording, slight saturation", "intimate, dark, close-miked"],
        "core_feel": "Rain on a detective's window. Smoky, mysterious, seductive. Every note has a shadow.",
    },

    # World & Folk-Influenced
    {
        "name": "Tango Piano",
        "artists": ["Astor Piazzolla", "Pugliese", "Gotan Project"],
        "palette": ["dramatic staccato rhythms", "passionate rubato", "habanera-like bass patterns", "sudden dynamic contrasts", "virtuosic right-hand runs over rhythmic left", "minor key intensity", "bandoneon-like melodic phrasing"],
        "recording": ["warm close-mic, dramatic and present", "live Buenos Aires café feel"],
        "core_feel": "Buenos Aires at midnight. Passionate, dramatic, the push-pull of tango rhythm. Fire and restraint.",
    },
    {
        "name": "Japanese Piano",
        "artists": ["Joe Hisaishi", "Ryuichi Sakamoto", "Takashi Yoshimatsu"],
        "palette": ["pentatonic melodies with wabi-sabi restraint", "delicate grace notes", "space and silence as musical elements", "simple theme stated with profound emotion", "gentle modal shifts", "clean precise articulation"],
        "recording": ["pristine studio, clean and clear", "intimate room, natural acoustic"],
        "core_feel": "The beauty of impermanence. Restrained, delicate, every note placed with care. Less is more.",
    },
    {
        "name": "Celtic Piano",
        "artists": ["Mícheál Ó Súilleabháin", "Phil Coulter", "Patrick Doyle"],
        "palette": ["modal melodies in Dorian or Mixolydian", "lilting 6/8 or 3/4 dance feel", "ornamental turns and mordents", "drone-like left-hand fifths", "folk melody with classical technique"],
        "recording": ["warm natural room, organic feel", "rich resonant grand piano"],
        "core_feel": "Green hills and ancient stories. Folk melody elevated to art. Lilting, warm, Celtic twilight.",
    },
    {
        "name": "Bossa Nova Piano",
        "artists": ["Antonio Carlos Jobim", "João Gilberto", "Eliane Elias"],
        "palette": ["gentle syncopated bossa rhythm", "rich extended jazz harmonies", "warm lazy melodic lines", "subtle left-hand comping", "major 7th and 9th chords", "relaxed Brazilian groove"],
        "recording": ["warm intimate studio, close and dry", "gentle room ambience, soft and round"],
        "core_feel": "Lazy afternoon in Ipanema. Warm, sophisticated, effortlessly beautiful. Never rushed.",
    },
    {
        "name": "Nordic Piano",
        "artists": ["Edvard Grieg", "Jan Garbarek", "Ketil Bjørnstad"],
        "palette": ["open voicings with wide intervals", "crystalline clarity in cold register", "Scandinavian melancholy", "folk-modal harmonies", "spacious phrasing", "winter-light dynamics"],
        "recording": ["bright clear recording, like cold air", "natural reverb, spacious and open"],
        "core_feel": "Fjords and winter light. Open, clear, melancholic but not bleak. The beauty of vast cold spaces.",
    },
    {
        "name": "Flamenco Piano",
        "artists": ["Chick Corea's Spanish work", "Paco de Lucía (adapted)", "Federico Mompou"],
        "palette": ["Phrygian mode", "rapid right-hand flourishes", "dramatic pauses and silence", "fiery staccato passages", "tense harmonic minor feel", "rhythmic foot-stamping energy in bass"],
        "recording": ["close and present, dry studio", "dramatic and immediate"],
        "core_feel": "Andalusian fire. Rapid flourishes exploding from tense silence. Drama, passion, precision.",
    },

    # Contemporary & Pop-Adjacent
    {
        "name": "Lo-Fi Piano",
        "artists": ["Idealism", "Kupla", "Hanz Zimmer's quieter work"],
        "palette": ["warm slightly detuned tone", "vinyl crackle aesthetic", "simple nostalgic melody", "tape-saturated warmth", "gentle repetitive chords", "dreamy haze", "imperfect and charming"],
        "recording": ["lo-fi warmth, tape saturation, vinyl texture", "slightly degraded warm quality"],
        "core_feel": "Nostalgia in a haze. Warm, imperfect, like a memory half-remembered. Cozy and wistful.",
    },
    {
        "name": "R&B Piano",
        "artists": ["Alicia Keys", "D'Angelo", "Robert Glasper"],
        "palette": ["smooth neo-soul voicings", "jazzy extended chords with groove", "rhythmic left-hand patterns", "soulful melodic lines", "9th and 13th chords", "subtle syncopation"],
        "recording": ["warm intimate studio, close-miked", "rich bass, smooth top end"],
        "core_feel": "Smooth, groovy, soulful. Piano as rhythm instrument and melody. Late-night R&B sophistication.",
    },
    {
        "name": "Ragtime",
        "artists": ["Scott Joplin", "Jelly Roll Morton", "Eubie Blake"],
        "palette": ["syncopated right-hand melody", "steady oom-pah left hand", "playful rhythmic bounce", "chromatic passing tones", "energetic and cheerful", "ornamental turns"],
        "recording": ["bright upright piano, slightly honky-tonk", "vintage character, warm and bouncy"],
        "core_feel": "Turn-of-century joy. Bouncy, syncopated, irresistible charm. Makes you want to tap your feet.",
    },

    # Experimental
    {
        "name": "Polyrhythmic Piano",
        "artists": ["Fela Kuti (adapted)", "Steve Reich", "Tigran Hamasyan"],
        "palette": ["3-against-4 layered rhythms", "West African-influenced patterns", "hypnotic interlocking grooves", "building rhythmic complexity", "trance-like repetition with shifting accents"],
        "recording": ["close-miked, percussive attack prominent", "dry studio, rhythmic clarity"],
        "core_feel": "Hypnotic rhythmic complexity. The brain tries to lock on and keeps shifting. Groove-driven and cerebral.",
    },
    {
        "name": "Thunderstorm Piano",
        "artists": ["Beethoven's Appassionata", "Prokofiev", "Bartók"],
        "palette": ["crashing low-register chords", "agitated rapid runs", "extreme dynamic contrasts", "sforzando accents", "stormy arpeggios", "relentless driving rhythm", "moments of eerie calm"],
        "recording": ["concert hall, full resonance", "dramatic and powerful, no compression"],
        "core_feel": "Raw elemental power. Thunder in the bass, lightning in the treble. Intense, dramatic, cathartic.",
    },
]

# ─── Emotional variation strategies ────────────────────────────────────────────
# Applied per-prompt to create variety even within a sub-genre
EMOTIONAL_LENSES = [
    {"name": "Yearning", "desc": "aching with longing, reaching for something just out of grasp, bittersweet",
     "modifiers": ["aching with longing", "bittersweet yearning", "reaching for something lost", "nostalgic and wistful"]},
    {"name": "Cathartic", "desc": "building tension that finally releases, like crying and then feeling relief",
     "modifiers": ["building tension to cathartic release", "tears turning to relief", "emotional dam breaking", "grief transforming into acceptance"]},
    {"name": "Joyful", "desc": "genuine happiness, playful lightness, the feeling of sunlight on your face",
     "modifiers": ["genuine warmth and joy", "playful lightness", "sunlit and hopeful", "dancing with gentle happiness"]},
    {"name": "Contemplative", "desc": "sitting with a thought, turning it over, neither happy nor sad — just present",
     "modifiers": ["deep in thought", "quietly contemplative", "turning a memory over and over", "present and still"]},
    {"name": "Defiant", "desc": "strength through adversity, standing firm, powerful and unbreaking",
     "modifiers": ["fierce determination", "standing firm against the storm", "defiant strength", "unbreakable will"]},
    {"name": "Ethereal", "desc": "otherworldly, floating between dream and waking, weightless beauty",
     "modifiers": ["otherworldly and floating", "dream-like and weightless", "between sleep and waking", "shimmering and transcendent"]},
    {"name": "Haunted", "desc": "a beautiful ghost, memory that won't let go, beauty mixed with sorrow",
     "modifiers": ["haunted by memory", "ghostly and lingering", "beauty wrapped in sorrow", "echo of something beautiful that's gone"]},
    {"name": "Tender", "desc": "gentle care, like holding something fragile, intimacy and vulnerability",
     "modifiers": ["gentle and fragile", "tender vulnerability", "holding something precious", "intimate and hushed"]},
    {"name": "Epic", "desc": "vast scope, cinematic grandeur, the feeling of standing on a mountain peak",
     "modifiers": ["vast and cinematic", "sweeping grandeur", "standing on a precipice", "expansive and awe-inspiring"]},
    {"name": "Playful", "desc": "mischievous, light, a wink and a smile, dancing fingers",
     "modifiers": ["mischievous and light", "playful wit", "fingers dancing with a smile", "cheeky and charming"]},
]

# ─── Recording textures ───────────────────────────────────────────────────────
RECORDING_DETAILS = [
    "Recorded on a warm Steinway Model D, close-miked with natural room reverb.",
    "Intimate studio recording on a Bösendorfer Imperial, rich bass, warm top.",
    "Close-miked grand piano, felt hammers audible, human imperfections intact.",
    "Natural concert hall acoustic, spacious reverb, full dynamic range.",
    "Studio Yamaha CFX, pristine clarity, bright and articulate.",
    "Warm close-mic'd Fazioli, clean and present, subtle room ambience.",
    "Vintage Steinway with character, slightly worn hammers, lived-in warmth.",
    "Pristine studio recording, balanced EQ, professional mastering.",
]

# ─── Musical direction snippets ───────────────────────────────────────────────
MUSICAL_DIRECTIONS = [
    "The performance should breathe like a human — rubato where emotion demands it, never metronomic.",
    "Let silence do the heavy lifting. The pauses between phrases should feel intentional.",
    "Build gradually — start intimate, let the emotion accumulate naturally, don't rush the climax.",
    "Play with dynamics constantly. Whisper-quiet passages make the louder moments devastating.",
    "The left hand should feel like a conversation partner, not just accompaniment.",
    "Every repetition of the theme should reveal something new — a different voicing, a new color.",
    "Keep it honest. No flashy technique for its own sake — every note serves the emotion.",
    "Vary the touch — some notes pressed gently, others with weight. A real pianist's fingerprint.",
    "The ending matters. Don't just fade — resolve with intention, whether gently or dramatically.",
    "Middle register melody, warm and vocal. The piano should sing, not just play.",
]

# ─── Name generation (same as v1 but expanded) ────────────────────────────────
NAME_A = [
    "Amber", "Autumn", "Blue", "Broken", "Burning", "Cedar", "Cloud", "Cobalt",
    "Cold", "Copper", "Coral", "Crimson", "Crystal", "Dappled", "Dark", "Dawn",
    "Deep", "Distant", "Drifting", "Dusk", "Dusty", "Fading", "Fallen", "Firefly",
    "First", "Floating", "Fog", "Forgotten", "Frost", "Ghost", "Glass", "Gold",
    "Half", "Haze", "Hidden", "Hollow", "Honey", "Indigo", "Iron", "Ivory",
    "Jade", "Last", "Late", "Lavender", "Lemon", "Light", "Lily", "Lost",
    "Lunar", "Marble", "Midnight", "Milk", "Moss", "Moth", "Muted", "Opal",
    "Paper", "Pearl", "Pine", "Porcelain", "Quiet", "Rain", "River", "Rose",
    "Rust", "Saffron", "Salt", "Sapphire", "Scarlet", "Shadow", "Shell", "Silent",
    "Silver", "Silk", "Slate", "Slow", "Smoke", "Snow", "Soft", "Starlight",
    "Still", "Stone", "Storm", "Summer", "Teal", "Thin", "Thorn", "Thunder",
    "Tide", "Twilight", "Velvet", "Violet", "Warm", "Water", "White", "Wild",
    "Willow", "Wind", "Winter", "Woven",
]

NAME_B = [
    "Aria", "Ashes", "Bloom", "Bones", "Breath", "Bridge", "Candle", "Cathedral",
    "Chapel", "Cradle", "Creek", "Dance", "Door", "Dream", "Drift", "Dust",
    "Echo", "Edge", "Ember", "Eve", "Falls", "Field", "Flame", "Flight",
    "Flicker", "Garden", "Gate", "Glass", "Glow", "Grace", "Harbor", "Haven",
    "Heart", "Haze", "Hills", "Horizon", "Hour", "Hymn", "Isle", "Kiss",
    "Lake", "Lane", "Letter", "Light", "Lullaby", "Meadow", "Memory", "Mile",
    "Mirror", "Moon", "Morning", "Moss", "Mountain", "Murmur", "Night",
    "Nocturne", "Notes", "Ocean", "Page", "Passage", "Path", "Petal", "Prayer",
    "Promise", "Pulse", "Rain", "Requiem", "Ridge", "River", "Road", "Ruins",
    "Sea", "Season", "Shade", "Shore", "Signal", "Sky", "Song", "Sorrow",
    "Spring", "Steps", "Stone", "Stream", "Sunset", "Temple", "Tide", "Tower",
    "Trail", "Veil", "Wake", "Waltz", "Wave", "Whisper", "Window", "Wings",
]


def generate_name(used):
    """Generate unique evocative two-word name."""
    for _ in range(100):
        name = f"{random.choice(NAME_A)} {random.choice(NAME_B)}"
        if name not in used:
            used.add(name)
            return name
    # Fallback
    name = f"{random.choice(NAME_A)} {random.choice(NAME_B)} {random.randint(1,99)}"
    used.add(name)
    return name


def build_prompt(subgenre, emotional_lens):
    """
    Build a rich, detailed Suno prompt. Target: 300-450 chars (Suno limit: 500).

    Structure:
      1. Genre + style description (NO artist names — Suno blocks them)
      2. Musical palette (2-3 specific techniques)
      3. Emotional lens + core feel
      4. Recording/production detail
      5. Performance direction
    """
    # 1. Opening: genre + style (no artist names — Suno rejects them)
    genre_name = subgenre["name"].lower()
    opener = f"Solo piano, {genre_name}. {subgenre['core_feel'].split('.')[0]}."

    # 2. Musical palette (pick 2-3 elements)
    palette_picks = random.sample(subgenre["palette"], min(3, len(subgenre["palette"])))
    palette_str = ", ".join(palette_picks)

    # 3. Emotional direction
    emotion = random.choice(emotional_lens["modifiers"])

    # 4. Remaining core feel sentences (skip first — already in opener)
    core_sentences = subgenre["core_feel"].split(". ")
    core_rest = ". ".join(core_sentences[1:]).strip() if len(core_sentences) > 1 else ""

    # 5. Recording
    if "recording" in subgenre and subgenre["recording"]:
        recording = random.choice(subgenre["recording"])
    else:
        recording = random.choice(RECORDING_DETAILS)

    # 6. Performance direction
    direction = random.choice(MUSICAL_DIRECTIONS)

    # Assemble — aim for 300-450 chars
    core_part = f" {core_rest}" if core_rest else ""
    prompt = f"{opener} {palette_str.capitalize()}. {emotion.capitalize()}.{core_part} {recording} {direction}"

    # Trim if over 500 (Suno hard limit)
    if len(prompt) > 495:
        # Drop direction first
        prompt = f"{opener} {palette_str.capitalize()}. {emotion.capitalize()}.{core_part} {recording}"
    if len(prompt) > 495:
        # Drop core rest
        prompt = f"{opener} {palette_str.capitalize()}. {emotion.capitalize()}. {recording}"
    if len(prompt) > 495:
        prompt = prompt[:492] + "..."

    return prompt


def generate_batch(count=50, forced_subgenre=None, num_subgenres=None):
    """
    Generate a diverse batch of prompts.

    Strategy:
    - Pick 5-10 sub-genres (or use forced_subgenre for single-genre mode)
    - Distribute prompts roughly evenly across genres
    - Apply different emotional lenses to create variety
    - Shuffle the final order
    """
    if forced_subgenre:
        # Single genre mode — still use all emotional lenses for variety
        selected_genres = [forced_subgenre]
    else:
        n = num_subgenres or random.randint(5, 10)
        n = min(n, len(SUBGENRES))
        selected_genres = random.sample(SUBGENRES, n)

    # Distribute prompts across genres
    per_genre = count // len(selected_genres)
    remainder = count % len(selected_genres)

    prompts = []
    used_names = set()
    genre_summary = {}

    for i, genre in enumerate(selected_genres):
        n_prompts = per_genre + (1 if i < remainder else 0)
        genre_summary[genre["name"]] = n_prompts

        # Cycle through emotional lenses for variety within genre
        lenses = random.sample(EMOTIONAL_LENSES, min(n_prompts, len(EMOTIONAL_LENSES)))
        if n_prompts > len(EMOTIONAL_LENSES):
            # Need more prompts than lenses — repeat with shuffle
            extra = n_prompts - len(EMOTIONAL_LENSES)
            lenses += random.sample(EMOTIONAL_LENSES, extra)

        for j in range(n_prompts):
            lens = lenses[j]
            prompt_text = build_prompt(genre, lens)
            title = generate_name(used_names)
            prompts.append({
                "title": title,
                "prompt": prompt_text,
                "subgenre": genre["name"],
                "emotional_lens": lens["name"],
                "char_count": len(prompt_text),
            })

    # Shuffle so genres are interleaved (avoids monotony in batch processing)
    random.shuffle(prompts)

    return prompts, genre_summary, selected_genres


def main():
    parser = argparse.ArgumentParser(description="Kapiko Prompt Generator v2 — diverse, rich, artist-anchored")
    parser.add_argument("--subgenre", type=str, help="Force a specific sub-genre (by name)")
    parser.add_argument("--subgenres", type=int, help="Number of random sub-genres to use (default: 5-10)")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--count", type=int, default=30, help="Number of prompts (default: 30)")
    parser.add_argument("--list-subgenres", action="store_true", help="List all sub-genres and exit")
    parser.add_argument("--preview", action="store_true", help="Print prompts to stdout instead of saving")
    args = parser.parse_args()

    if args.list_subgenres:
        print(f"\n{'#':<4} {'Sub-Genre':<25} {'Artists':<40}")
        print("-" * 85)
        for i, sg in enumerate(SUBGENRES, 1):
            artists = ", ".join(sg["artists"])
            print(f"{i:<4} {sg['name']:<25} {artists[:40]}")
        print(f"\nTotal: {len(SUBGENRES)} sub-genres")
        return

    # Find sub-genre if forced
    forced = None
    if args.subgenre:
        matches = [s for s in SUBGENRES if s["name"].lower() == args.subgenre.lower()]
        if not matches:
            print(f"Unknown sub-genre: '{args.subgenre}'")
            print("Use --list-subgenres to see options")
            sys.exit(1)
        forced = matches[0]

    prompts, genre_summary, selected = generate_batch(
        count=args.count,
        forced_subgenre=forced,
        num_subgenres=args.subgenres,
    )

    if args.preview:
        for p in prompts:
            print(f"\n[{p['subgenre']} / {p['emotional_lens']}] {p['title']}")
            print(f"  {p['prompt']}")
            print(f"  ({p['char_count']} chars)")
        print(f"\n--- Genre distribution ---")
        for g, n in genre_summary.items():
            if n > 0:
                print(f"  {g}: {n} prompts")
        return

    # Output
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    if args.output:
        out_path = args.output
    else:
        out_path = f"/tmp/kapiko-prompts-v2-{ts}.json"

    output = {
        "generated_at": datetime.now().isoformat(),
        "generator": "kapiko-prompt-generator-v2",
        "total_prompts": len(prompts),
        "genre_distribution": {g: n for g, n in genre_summary.items() if n > 0},
        "selected_subgenres": [
            {"name": s["name"], "artists": s["artists"]} for s in selected
        ],
        "prompts": prompts,
    }

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n🎹 Kapiko Prompt Generator v2")
    print(f"   Prompts: {len(prompts)}")
    print(f"   Sub-genres: {len(genre_summary)}")
    for g, n in genre_summary.items():
        if n > 0:
            print(f"     • {g}: {n}")
    print(f"   Output: {out_path}")
    avg_chars = sum(p["char_count"] for p in prompts) / len(prompts)
    print(f"   Avg prompt length: {avg_chars:.0f} chars (v1 was ~60)")
    print(f"\n   Sample prompts:")
    for p in prompts[:3]:
        print(f"\n   [{p['subgenre']} / {p['emotional_lens']}] \"{p['title']}\"")
        print(f"   {p['prompt'][:200]}...")


if __name__ == "__main__":
    main()
