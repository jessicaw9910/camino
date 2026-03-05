#!/bin/bash
# Prepare audio files for bundling into the Android APK

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

AUDIO_SOURCE="$PROJECT_ROOT/data/rio_grande_rift/audio"
AUDIO_DEST="$PROJECT_ROOT/app/audio"

echo "Copying audio files for Android build..."

# Check if source exists
if [ ! -d "$AUDIO_SOURCE" ]; then
    echo "Error: Audio directory not found at $AUDIO_SOURCE"
    echo "Run 'python src/generate_audio.py' first to generate audio files."
    exit 1
fi

# Create destination directory
mkdir -p "$AUDIO_DEST"

# Copy audio files and manifest
cp -r "$AUDIO_SOURCE/"* "$AUDIO_DEST/"

echo "Copied files to $AUDIO_DEST:"
ls -la "$AUDIO_DEST" | head -20

# Count files
MP3_COUNT=$(find "$AUDIO_DEST" -name "*.mp3" | wc -l)
echo ""
echo "Total MP3 files: $MP3_COUNT"
echo "Audio files ready for bundling!"
