#!/usr/bin/env python3
"""
Kapiko Daily Prompt Generator
Picks a random solo piano sub-genre, generates 50 unique Suno prompts.
Output: JSON file ready for suno batch script.

Usage:
  python3 scripts/kapiko-prompt-generator.py [--subgenre "Jazz Ballad"] [--output /tmp/kapiko-prompts.json]
"""

import json, random, sys, argparse
from datetime import datetime

SUBGENRES = [
    # Classical & Traditional
    {"name": "Classical Nocturne", "desc": "Chopin-esque, expressive rubato, lyrical singing melodies, dynamic contrast", "tags": "rubato, lyrical melody, dynamic shading, romantic era, singing tone"},
    {"name": "Romantic Étude", "desc": "Virtuosic technical passages with emotional depth, Liszt/Rachmaninoff energy", "tags": "virtuosic runs, octave passages, dramatic build, concert hall, powerful"},
    {"name": "Baroque Invention", "desc": "Contrapuntal two-voice writing, Bach-inspired, precise and mathematical", "tags": "counterpoint, two-voice, precise articulation, harpsichord-like, structured"},
    {"name": "Classical Sonata", "desc": "Mozart/Beethoven clarity, structured themes, development, elegant phrasing", "tags": "classical form, clear melody, Alberti bass, elegant, balanced"},
    {"name": "Impressionist", "desc": "Debussy/Ravel washes, whole-tone scales, lush harmonies, dreamy color", "tags": "whole-tone, parallel chords, pedal wash, dreamy, colorful harmonies"},
    {"name": "Waltz", "desc": "3/4 time, sweeping elegance, ballroom grace, Strauss to Chopin spectrum", "tags": "3/4 time, sweeping, graceful, dance rhythm, elegant"},

    # Modern Classical & Art Music
    {"name": "Minimalist", "desc": "Philip Glass/Steve Reich, repeating evolving patterns, hypnotic and meditative", "tags": "repeating patterns, additive process, hypnotic, slowly evolving, trance-like"},
    {"name": "Neo-Classical", "desc": "Ólafur Arnalds/Nils Frahm, modern classical meets subtle electronic sensibility", "tags": "modern classical, intimate, subtle felt piano, contemplative, sparse"},
    {"name": "Post-Minimalist", "desc": "Max Richter style, emotional minimalism, slow-building orchestral piano writing", "tags": "emotional, slow build, sustained notes, cinematic scope, deeply felt"},
    {"name": "Spectral Piano", "desc": "Overtone-focused, resonance exploration, sustained pedal, shimmering harmonics", "tags": "overtones, resonance, sustained pedal, shimmering, ethereal"},
    {"name": "Prepared Piano", "desc": "John Cage inspired, unusual timbres, percussive elements, experimental sounds", "tags": "altered timbre, percussive, experimental, metallic, unconventional"},
    {"name": "Aleatoric", "desc": "Controlled randomness, chance-based clusters, Lutosławski-inspired texture", "tags": "clusters, chance elements, textural, unpredictable, atmospheric"},

    # Jazz & Blues
    {"name": "Jazz Ballad", "desc": "Bill Evans voicings, extended chords, introspective swing, late-night intimacy", "tags": "extended chords, 9ths 13ths, rootless voicings, swing feel, intimate"},
    {"name": "Bebop Piano", "desc": "Fast, angular lines, Bud Powell/Thelonious Monk, sharp rhythmic accents", "tags": "angular melody, fast tempo, chromatic runs, syncopated accents, energetic"},
    {"name": "Stride Piano", "desc": "Art Tatum/Fats Waller, leaping left hand, showmanship, exuberant swing", "tags": "stride bass, leaping left hand, swing, exuberant, virtuosic"},
    {"name": "Cool Jazz Piano", "desc": "Dave Brubeck/Ahmad Jamal, relaxed, spacious, sophisticated understatement", "tags": "spacious, cool tone, sophisticated harmony, relaxed swing, understated"},
    {"name": "Blues Piano", "desc": "Soulful, 12-bar progressions, bent-note feel, smoky and raw", "tags": "12-bar blues, bent notes, raw emotion, walking bass, smoky"},
    {"name": "Gospel Piano", "desc": "Churchy voicings, jubilant runs, call-and-response feel, soulful spirit", "tags": "churchy chords, jubilant, runs and fills, soulful, uplifting"},
    {"name": "Boogie-Woogie", "desc": "Rolling left-hand ostinato, infectious groove, high energy, rhythmic drive", "tags": "rolling bass, ostinato, infectious rhythm, high energy, driving"},
    {"name": "Latin Jazz Piano", "desc": "Montuno patterns, Afro-Cuban rhythms, syncopated groove, tropical warmth", "tags": "montuno, syncopated, Afro-Cuban, rhythmic groove, warm"},

    # Ambient & Atmospheric
    {"name": "Ambient Piano", "desc": "Floating sustained tones, reverb-heavy, Brian Eno-influenced, weightless", "tags": "sustained, reverb wash, floating, weightless, atmospheric"},
    {"name": "Dark Ambient Piano", "desc": "Brooding low register, dissonant undertones, unsettling beauty, cinematic tension", "tags": "low register, brooding, dissonant, tense, unsettling beauty"},
    {"name": "New Age Piano", "desc": "George Winston/Yanni, gentle pentatonic melodies, healing, nature-inspired", "tags": "pentatonic, gentle, healing, flowing, nature-inspired"},
    {"name": "Drone Piano", "desc": "Long sustained bass notes, overtone exploration, meditative stillness", "tags": "drone bass, sustained, overtones, meditative, still"},
    {"name": "Celestial Piano", "desc": "Upper register sparkle, crystalline arpeggios, starlight and cosmic wonder", "tags": "upper register, crystalline, arpeggios, sparkling, cosmic"},

    # Cinematic & Emotional
    {"name": "Cinematic Emotional", "desc": "Yiruma/Einaudi, big emotional arcs, accessible melody, builds and releases", "tags": "emotional arc, accessible melody, gradual build, cathartic, sweeping"},
    {"name": "Film Noir Piano", "desc": "Smoky detective drama, minor keys, sultry melodic lines, mysterious tension", "tags": "noir, smoky, minor key, sultry, mysterious tension"},
    {"name": "Epic Cinematic", "desc": "Hans Zimmer-scale drama at the piano, thundering bass, soaring climax", "tags": "dramatic, thundering bass, soaring melody, climactic, powerful"},
    {"name": "Horror Piano", "desc": "Dissonant intervals, creeping chromatic lines, jump-scare dynamics, eerie", "tags": "dissonant, chromatic, eerie, sudden dynamics, unsettling"},
    {"name": "Romantic Film Score", "desc": "Sweeping love-theme piano, soaring strings-like melodies, heartfelt and warm", "tags": "love theme, soaring melody, heartfelt, warm, sweeping"},

    # World & Folk-Influenced
    {"name": "Tango Piano", "desc": "Piazzolla-inspired, dramatic passion, staccato rhythms, Buenos Aires fire", "tags": "tango rhythm, staccato, dramatic, passionate, Argentine"},
    {"name": "Celtic Piano", "desc": "Modal melodies, Irish/Scottish folk influence, lilting 6/8 jigs, green hills", "tags": "modal, Celtic melody, 6/8 jig, lilting, folk-inspired"},
    {"name": "Japanese Piano", "desc": "Pentatonic scales, Joe Hisaishi/Ryuichi Sakamoto, wabi-sabi beauty, restraint", "tags": "pentatonic, Japanese scale, restrained, wabi-sabi, delicate"},
    {"name": "Flamenco Piano", "desc": "Spanish Phrygian mode, rapid flourishes, dramatic pauses, fiery passion", "tags": "Phrygian mode, rapid runs, dramatic pause, Spanish, fiery"},
    {"name": "Nordic Piano", "desc": "Cold open spaces, Scandinavian melancholy, crystalline clarity, winter light", "tags": "Nordic, cold clarity, open voicings, melancholic, winter"},
    {"name": "Klezmer Piano", "desc": "Eastern European Jewish folk, augmented 2nds, laughing-crying duality, festive", "tags": "augmented 2nd, Eastern European, festive, emotional, ornamental"},
    {"name": "Bossa Nova Piano", "desc": "Brazilian gentle sway, Jobim-inspired harmonies, warm lazy afternoon feel", "tags": "bossa rhythm, gentle sway, warm harmony, Brazilian, laid-back"},

    # Contemporary & Pop-Adjacent
    {"name": "Lo-Fi Piano", "desc": "Warm tape saturation, vinyl crackle aesthetic, chill beats feel, nostalgic haze", "tags": "lo-fi warmth, tape saturation, chill, nostalgic, slightly detuned"},
    {"name": "Singer-Songwriter Piano", "desc": "Adele/Sara Bareilles-style accompaniment, but instrumental, emotive chords", "tags": "pop ballad chords, emotive, singer-songwriter feel, accessible, warm"},
    {"name": "R&B Piano", "desc": "Smooth neo-soul voicings, jazzy extended chords, Alicia Keys feel, groove", "tags": "neo-soul, smooth, jazzy chords, groove, R&B feel"},
    {"name": "Hymn/Chorale Piano", "desc": "Four-part harmony, reverent and stately, church-like warmth, sustained chords", "tags": "chorale, four-part harmony, reverent, sustained, hymn-like"},
    {"name": "Music Box Piano", "desc": "High register tinkling, simple repeated melody, childlike innocence, delicate", "tags": "music box, high register, simple melody, innocent, tinkling"},

    # Experimental & Genre-Bending
    {"name": "Glitch Piano", "desc": "Stuttering repetitions, rhythmic disruptions, digital artifact aesthetic", "tags": "stuttering, glitchy, rhythmic disruption, fragmented, digital feel"},
    {"name": "Deconstructed Piano", "desc": "Fragments of melody, long silences, Feldman-esque patience, space as music", "tags": "fragmented, long silence, sparse, patient, deconstructed"},
    {"name": "Polyrhythmic Piano", "desc": "Afrobeat-influenced layered rhythms, 3-against-4, hypnotic complexity", "tags": "polyrhythm, 3 against 4, layered rhythm, hypnotic, complex groove"},
    {"name": "Ragtime", "desc": "Scott Joplin syncopation, bouncy left hand, playful charm, turn-of-century joy", "tags": "syncopated, bouncy, playful, ragtime stride, joyful"},
    {"name": "Lullaby Piano", "desc": "Gentle rocking rhythm, simple soothing melody, music for sleep, tender", "tags": "lullaby, rocking rhythm, soothing, tender, sleep-inducing"},
    {"name": "Pastoral Piano", "desc": "Gentle countryside imagery, birdsong-like trills, warm major keys, idyllic", "tags": "pastoral, gentle, trills, warm major, countryside"},
    {"name": "Thunderstorm Piano", "desc": "Dramatic contrasts, crashing bass chords, agitated runs, stormy intensity", "tags": "stormy, crashing chords, agitated runs, intense, dramatic contrasts"},
    {"name": "Toy Piano", "desc": "Quirky detuned character, playful minimalism, Satie-meets-childhood", "tags": "toy piano, quirky, detuned, playful, Satie-like"},
]

# --- Prompt building blocks ---

KEYS_MAJOR = ["C major", "D major", "E-flat major", "F major", "G major", "A-flat major", "B-flat major", "A major", "E major", "D-flat major"]
KEYS_MINOR = ["A minor", "C minor", "D minor", "E minor", "F minor", "G minor", "B minor", "F-sharp minor", "C-sharp minor", "B-flat minor"]

TEMPOS = {
    "very slow": ["very slow", "largo", "adagio", "glacial pace", "extremely slow and deliberate"],
    "slow": ["slow", "gentle tempo", "unhurried", "andante", "leisurely"],
    "moderate": ["moderate tempo", "flowing pace", "steady", "moderato", "walking pace"],
    "upbeat": ["upbeat", "allegro", "lively tempo", "brisk", "spirited pace"],
    "fast": ["fast", "vivace", "presto", "rapid", "high energy tempo"],
}

DYNAMICS = [
    "pianissimo to mezzo-forte", "soft throughout", "builds from whisper to powerful climax",
    "gentle with sudden forte outbursts", "mezzo-piano, tender", "starts bold, fades to nothing",
    "constantly shifting dynamics", "powerful and commanding", "intimate and hushed",
    "dramatic crescendo-decrescendo arc", "quiet intensity throughout", "explosive then dissolving",
]

RECORDING = [
    "close-miked Steinway, warm natural tone",
    "concert hall ambience, natural reverb",
    "intimate studio recording, dry and close",
    "slightly roomy recording, felt hammers audible",
    "pristine studio quality, rich bass resonance",
    "warm close-mic'd grand piano, clean recording",
    "natural room sound, no added reverb",
    "studio Bösendorfer, deep warm low end",
    "bright Yamaha concert grand, crystal clear",
    "vintage upright piano, slightly worn character",
]

MOODS = [
    "melancholic", "hopeful", "bittersweet", "serene", "yearning", "triumphant",
    "wistful", "contemplative", "ecstatic", "mournful", "playful", "tender",
    "mysterious", "nostalgic", "euphoric", "restless", "peaceful", "aching",
    "defiant", "dreamy", "longing", "jubilant", "solemn", "ethereal",
    "fiery", "gentle", "haunting", "introspective", "radiant", "somber",
]

TECHNIQUES = [
    "arpeggiated chords", "block chords", "broken octaves", "cascading runs",
    "chromatic passing tones", "cross-hand passages", "grace notes", "legato melody",
    "left-hand melody", "octave doubling", "ostinato bass", "pedal point",
    "repeating motif", "rolled chords", "scale passages", "singing right-hand melody",
    "staccato articulation", "sustained pedal", "syncopated rhythm", "trill ornaments",
    "tremolo", "wide leaps", "inner voice melody", "bell-like repeated notes",
    "walking bass line", "contrary motion", "parallel thirds", "cluster chords",
]

# Evocative name components
NAME_PARTS_A = [
    "Amber", "Autumn", "Blue", "Broken", "Burning", "Cedar", "Cloud", "Cobalt",
    "Cold", "Copper", "Coral", "Crimson", "Crystal", "Dappled", "Dark", "Dawn",
    "Deep", "Distant", "Drifting", "Dusk", "Dusty", "Fading", "Fallen", "Firefly",
    "First", "Floating", "Fog", "Forgotten", "Frost", "Ghost", "Glass", "Gold",
    "Half", "Haze", "Hidden", "Hollow", "Honey", "Indigo", "Iron", "Ivory",
    "Jade", "Last", "Late", "Lavender", "Lemon", "Light", "Lily", "Lost",
    "Lunar", "Marble", "Midnight", "Milk", "Moss", "Moth", "Muted", "Opal",
    "Orchid", "Pale", "Paper", "Pearl", "Pine", "Porcelain", "Quiet", "Rain",
    "River", "Rose", "Rust", "Saffron", "Salt", "Sapphire", "Scarlet", "Shadow",
    "Shell", "Silent", "Silver", "Silk", "Slate", "Slow", "Smoke", "Snow",
    "Soft", "Solar", "Starlight", "Still", "Stone", "Storm", "Summer", "Sun",
    "Teal", "Thin", "Thistle", "Thorn", "Thunder", "Tide", "Twilight", "Velvet",
    "Violet", "Warm", "Water", "White", "Wild", "Willow", "Wind", "Winter",
]

NAME_PARTS_B = [
    "Aria", "Ashes", "Bloom", "Bones", "Breath", "Bridge", "Candle", "Cathedral",
    "Chapel", "Cradle", "Creek", "Dance", "Door", "Dream", "Drift", "Dust",
    "Echo", "Edge", "Ember", "Eve", "Falls", "Field", "Flame", "Flight",
    "Flicker", "Fog", "Garden", "Gate", "Glass", "Glow", "Grace", "Harbor",
    "Haven", "Heart", "Haze", "Hills", "Horizon", "Hour", "Hymn", "Isle",
    "Kiss", "Lake", "Lane", "Letter", "Light", "Lullaby", "Meadow", "Memory",
    "Mile", "Mirror", "Moon", "Morning", "Moss", "Mountain", "Murmur", "Night",
    "Nocturne", "Notes", "Ocean", "Page", "Passage", "Path", "Petal", "Prayer",
    "Promise", "Pulse", "Rain", "Requiem", "Ridge", "River", "Road", "Ruins",
    "Sea", "Season", "Shade", "Shore", "Signal", "Sky", "Song", "Sorrow",
    "Spring", "Steps", "Stone", "Stream", "Sunset", "Temple", "Tide", "Tower",
    "Trail", "Veil", "Wake", "Waltz", "Wave", "Whisper", "Window", "Wings",
]

def generate_name():
    """Generate an evocative two-word track name."""
    return f"{random.choice(NAME_PARTS_A)} {random.choice(NAME_PARTS_B)}"

def pick_tempo_for_subgenre(subgenre_name):
    """Pick appropriate tempo range based on sub-genre character."""
    fast_genres = {"Bebop Piano", "Boogie-Woogie", "Stride Piano", "Ragtime", "Flamenco Piano", "Thunderstorm Piano"}
    slow_genres = {"Ambient Piano", "Dark Ambient Piano", "Drone Piano", "Deconstructed Piano", "Lullaby Piano", "Spectral Piano"}
    moderate_genres = {"Bossa Nova Piano", "Celtic Piano", "Hymn/Chorale Piano", "Pastoral Piano"}

    if subgenre_name in fast_genres:
        return random.choice(["upbeat", "fast"])
    elif subgenre_name in slow_genres:
        return random.choice(["very slow", "slow"])
    elif subgenre_name in moderate_genres:
        return random.choice(["slow", "moderate"])
    else:
        return random.choice(["very slow", "slow", "moderate", "upbeat"])

def generate_prompt(subgenre):
    """Generate a single unique Suno prompt for a sub-genre. Max 200 chars (Suno limit)."""
    # Pick components
    is_minor = random.random() < 0.5
    key = random.choice(KEYS_MINOR if is_minor else KEYS_MAJOR)
    tempo_cat = pick_tempo_for_subgenre(subgenre["name"])
    tempo = random.choice(TEMPOS[tempo_cat])
    mood = random.choice(MOODS)
    technique = random.choice(TECHNIQUES)

    # Build compact prompt — must stay ≤200 chars
    prompt = f"Solo piano, {subgenre['name'].lower()}. {mood}, {tempo}. {key}, {technique}."

    # If still over 200, trim technique
    if len(prompt) > 200:
        prompt = f"Solo piano, {subgenre['name'].lower()}. {mood}, {tempo}. {key}."

    # Final safety net
    if len(prompt) > 200:
        prompt = prompt[:197] + "..."

    title = generate_name()
    return {"title": title, "prompt": prompt, "subgenre": subgenre["name"]}

def generate_batch(subgenre=None, count=50):
    """Generate a batch of prompts for a random (or specified) sub-genre."""
    if subgenre is None:
        subgenre = random.choice(SUBGENRES)

    prompts = []
    used_titles = set()
    for _ in range(count):
        p = generate_prompt(subgenre)
        # Ensure unique titles
        while p["title"] in used_titles:
            p["title"] = generate_name()
        used_titles.add(p["title"])
        prompts.append(p)

    return subgenre, prompts

def main():
    parser = argparse.ArgumentParser(description="Kapiko daily prompt generator")
    parser.add_argument("--subgenre", type=str, help="Force a specific sub-genre (by name)")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--count", type=int, default=50, help="Number of prompts to generate")
    parser.add_argument("--list-subgenres", action="store_true", help="List all sub-genres and exit")
    args = parser.parse_args()

    if args.list_subgenres:
        print(f"\n{'#':<4} {'Sub-Genre':<25} Description")
        print("-" * 80)
        for i, sg in enumerate(SUBGENRES, 1):
            print(f"{i:<4} {sg['name']:<25} {sg['desc'][:50]}...")
        print(f"\nTotal: {len(SUBGENRES)} sub-genres")
        return

    # Find sub-genre
    sg = None
    if args.subgenre:
        matches = [s for s in SUBGENRES if s["name"].lower() == args.subgenre.lower()]
        if not matches:
            print(f"Unknown sub-genre: {args.subgenre}")
            print("Use --list-subgenres to see all options")
            sys.exit(1)
        sg = matches[0]

    subgenre, prompts = generate_batch(sg, args.count)

    # Output path
    if args.output:
        out_path = args.output
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        out_path = f"/tmp/kapiko-prompts-{date_str}.json"

    # Write output
    output = {
        "generated_at": datetime.now().isoformat(),
        "subgenre": subgenre["name"],
        "subgenre_description": subgenre["desc"],
        "count": len(prompts),
        "prompts": prompts,
    }

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n🎹 Kapiko Prompt Generator")
    print(f"   Sub-genre: {subgenre['name']}")
    print(f"   Description: {subgenre['desc']}")
    print(f"   Prompts: {len(prompts)}")
    print(f"   Output: {out_path}")
    print(f"\n   Sample prompts:")
    for p in prompts[:3]:
        print(f"   • [{p['title']}] {p['prompt'][:100]}...")

if __name__ == "__main__":
    main()
