# Camino Audio Guide

A GPS-triggered audio guide app for exploring points of interest on road trips. Supports multiple tours with automatic audio playback when approaching landmarks.

## Project Structure

```
camino/
├── data/
│   └── <tour_name>/           # Each subdirectory is a tour
│       ├── scripts.json       # POIs with descriptions (required)
│       ├── audio/             # Generated MP3 files (01.mp3, 02.mp3, ...)
│       └── cover.jpg          # Tour cover image for selection screen
├── src/
│   ├── generate_audio.py      # TTS audio generation CLI
│   └── create_cover.py        # Placeholder cover image generator
├── app/
│   ├── main.py                # Kivy application
│   └── buildozer.spec         # Android build configuration
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

### 1. Generate Audio Files

The `generate_audio.py` CLI generates MP3 files from POI descriptions using Edge TTS (Microsoft's neural voices).

```bash
# List available tours
python src/generate_audio.py --list

# Generate audio for a specific tour
python src/generate_audio.py rio_grande_rift

# Generate for all tours
python src/generate_audio.py

# Force regeneration of existing files
python src/generate_audio.py rio_grande_rift --force
```

This will:
- Read `data/<tour>/scripts.json`
- Strip citation markers `[1]`, `[2]`, etc. from text
- Generate MP3 files using Edge TTS multilingual neural voice
- Save audio as `data/<tour>/audio/01.mp3`, `02.mp3`, etc.

### 2. Generate Cover Images (Optional)

If a tour doesn't have a cover image, create a placeholder:

```bash
python src/create_cover.py
```

Or add your own `cover.jpg` (recommended 800x600 or similar aspect ratio).

### 3. Run the App (Desktop Testing)

```bash
python app/main.py
```

The app will:
- Show a tour selection screen with all available tours
- Display a map with POI markers for the selected tour
- Allow manual playback of any POI audio
- Simulate GPS on desktop (real GPS on mobile)

### 4. Build Android APK

```bash
cd app
buildozer android debug
# Output: app/bin/*.apk
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

## Adding Your Own Tours

1. Create a new directory under `data/`:
   ```bash
   mkdir data/my_road_trip
   ```

2. Add a `scripts.json` file with POIs:
   ```json
   [
     {
       "num": 1,
       "name": "First Stop",
       "body": ["Description paragraph 1.", "Paragraph 2."],
       "lat": 35.123,
       "lon": -106.456
     }
   ]
   ```

3. Generate audio:
   ```bash
   python src/generate_audio.py my_road_trip
   ```

4. Add a cover image (optional):
   - Place `cover.jpg` in `data/my_road_trip/`
   - Or run `python src/create_cover.py` to generate placeholder

## Technical Notes

### TTS Engine
Uses Microsoft Edge TTS (`edge-tts`) with the `en-US-AndrewMultilingualNeural` voice for natural-sounding speech with proper Spanish word pronunciation.

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
