# Camino Audio Guide

A GPS-triggered audio guide app for exploring points of interest on road trips. Supports multiple tours with automatic audio playback when approaching landmarks.

## Project Structure

```
camino/
├── data/
│   └── <tour_name>/           # Each subdirectory is a tour
│       ├── input.json         # Tour config: name, map URL, cover URL, voice
│       ├── scripts.json       # POIs with narration scripts (required for app)
│       ├── tour.json          # Tour metadata for app display
│       ├── map.kml            # Google My Maps export (for validation/analysis)
│       ├── cover.jpg          # Tour cover image for selection screen
│       └── audio/             # Generated MP3 files (01.mp3, 02.mp3, ...)
├── src/
│   ├── generate_audio.py      # TTS audio generation CLI
│   ├── fetch_resources.py     # Bootstrap tour from Google My Maps
│   ├── analyze_map.py         # Gap analysis: KML markers vs scripts
│   ├── validate_triggers.py   # Check POI GPS triggers against route
│   ├── create_cover.py        # Placeholder cover image generator
│   └── create_icon.py         # App icon generator
├── app/
│   └── main.py                # Kivy application (single-file)
├── main.py                    # Entry point for Buildozer/Android
├── buildozer.spec             # Android build configuration
├── icon.png                   # App icon (512x512)
├── requirements.txt
└── README.md
```

## Setup

### Prerequisites

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# For Android builds
pip install buildozer
```

## App Features

### Tour Selection
- Landing screen shows all discovered tours
- Each tour displays cover image, name, and POI count
- Tours auto-discovered from `data/` subdirectories containing `scripts.json`

### GPS Tracking
- Toggle GPS on/off with button in header
- Configurable trigger radius (50m - 500m slider)
- Automatic audio playback when entering a POI's radius
- Each POI plays only once per trip (tap "Reset" to replay)

### Map View
- Interactive map with POI markers
- Tap markers to see POI name and play audio
- Map centers on user location when GPS enabled

### Manual Playback
- Play/Pause button for selected POI
- Stop button to halt playback
- Works independently of GPS mode

## Creating a New Tour

### Step 1: Set up `input.json`

Create a directory for your tour and add an `input.json` file:

```bash
mkdir data/my_tour
```

```json
{
  "name": "My Tour",
  "description": "A GPS-triggered audio guide of ...",
  "url_map": "https://www.google.com/maps/d/u/0/view?mid=YOUR_MAP_ID",
  "url_cover": "https://example.com/cover-image.jpg",
  "voice": "en-US-AvaMultilingualNeural"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name on the tour card |
| `description` | Yes | One-sentence tour description |
| `url_map` | Yes | Google My Maps share URL (must contain `mid=` param, map must be publicly shared) |
| `url_cover` | No | Public image URL for cover; if omitted, a placeholder is generated |
| `voice` | No | Edge TTS voice name; defaults to `en-US-AndrewMultilingualNeural` |

### Step 2: Fetch resources

```bash
python src/fetch_resources.py my_tour
```

This downloads from your Google My Maps and cover URL to produce:
- `data/my_tour/map.kml` — route and marker data
- `data/my_tour/cover.jpg` — tour card image
- `data/my_tour/tour.json` — metadata (name + description)

### Step 3: Write `scripts.json`

This is the core content file — an array of POI objects with narration scripts, GPS triggers, and citations. See `CLAUDE.md` for the full schema, style guide, and citation rules.

You can bootstrap it from the KML:

```bash
# Analyze map markers and identify gaps
python src/analyze_map.py my_tour

# Generate stub POI entries from map markers
python src/analyze_map.py my_tour --stubs
#    → data/my_tour/candidates.json
```

Then write the narration scripts for each POI (body text, sources, coordinates) and merge completed entries into `data/my_tour/scripts.json` in route order.

Each POI has a `type` field that controls marker color on the map:
- `"car"` — red (default if omitted, for backwards compatibility)
- `"train"` — orange
- `"walking"` — yellow

### Step 4: Validate

```bash
# Check that POI GPS triggers are near the KML route
python src/validate_triggers.py my_tour
python src/validate_triggers.py my_tour --suggest-fixes   # show nearest route coords for outliers
```

### Step 5: Generate audio

```bash
# Generate TTS audio (requires internet — uses Microsoft Edge TTS service)
python src/generate_audio.py my_tour

# Force regeneration of all files
python src/generate_audio.py my_tour --force

# Override the voice from input.json
python src/generate_audio.py my_tour --voice en-US-BrianMultilingualNeural
```

This reads `scripts.json`, strips citation markers, and generates:
- `data/my_tour/audio/01.mp3`, `02.mp3`, ...
- `data/my_tour/audio/manifest.json`

### Step 6: Run the App (Desktop Testing)

```bash
python app/main.py
```

The app will:
- Show a tour selection screen with all available tours
- Display a map with POI markers for the selected tour
- Allow manual playback of any POI audio
- Simulate GPS on desktop (real GPS on mobile)

### Step 7: Build Android APK

All tour data under `data/` (audio, scripts, covers) is bundled automatically via `buildozer.spec` — no manual copying step is needed.

```bash
# First build — compiles the full Android toolchain + all Python dependencies.
# Takes 15-30+ minutes. Run from the project root (where buildozer.spec lives):
buildozer android debug
# Output: bin/camino-*-debug.apk

# Subsequent builds — reuses compiled dependencies, only repackages app code
# and data. Much faster (1-3 minutes):
buildozer android debug

# Install directly to a connected device via USB:
buildozer android debug deploy

# Build + deploy + stream device logs:
buildozer android debug deploy run logcat
```

The first `buildozer android debug` downloads the Android SDK/NDK, compiles Python and all C-extension dependencies (Kivy, Pillow, etc.) — this is a one-time cost stored in `.buildozer/`. Subsequent builds skip all of that and only repackage your Python source and data files, which is significantly faster.

If you need to force a full rebuild of dependencies (e.g., after changing `requirements` in `buildozer.spec`):

```bash
# Clean the build and start fresh
buildozer android clean
buildozer android debug
```

## Technical Notes

### TTS Engine
Uses Microsoft Edge TTS (`edge-tts`) with multilingual neural voices. The voice is configured per tour in `input.json` (default: `en-US-AndrewMultilingualNeural`). Requires an internet connection — audio is streamed from Microsoft's servers.

### GPS on Android
The app uses Plyer for cross-platform GPS. Requires:
- `ACCESS_FINE_LOCATION` permission
- `ACCESS_COARSE_LOCATION` permission

### Map Tiles
Uses OpenStreetMap tiles via kivy-garden.mapview. Requires internet for initial tile loading; tiles are cached locally.

## Troubleshooting

### "No tours found"
Ensure each tour directory contains a valid `scripts.json` file.

### "MapView not available"
Install: `pip install kivy-garden.mapview`

### "GPS not available"
On desktop, the app uses a simulated location. Real GPS requires:
- Android device with GPS hardware
- Location permissions granted

### Build fails on macOS
Ensure you have:
- Java JDK 8+
- Xcode command line tools: `xcode-select --install`

## License

MIT
