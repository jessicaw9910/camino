#!/usr/bin/env python3
"""
Audio Generation Script for Camino Audio Guides

This script generates MP3 audio files from scripts.json files in tour directories.
It uses Microsoft Edge TTS with multilingual neural voices for natural-sounding
audio that properly handles Spanish words within English text.

Usage:
    python generate_audio.py                    # Process all tours in data/
    python generate_audio.py rio_grande_rift    # Process specific tour
    python generate_audio.py --list             # List available tours

Requirements:
    pip install edge-tts

Each tour directory should contain:
    - scripts.json: Array of POIs with 'num', 'name', 'body', 'lat', 'lon'
    
Output:
    - audio/*.mp3: Generated audio files (01.mp3, 02.mp3, etc.)
    - audio/manifest.json: Manifest with POI data and audio file mappings
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("Error: edge-tts not installed. Run: pip install edge-tts")
    sys.exit(1)

# Multilingual voice - handles Spanish words naturally within English text
# Options: en-US-AndrewMultilingualNeural, en-US-AvaMultilingualNeural, en-US-BrianMultilingualNeural
DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.resolve()


def get_data_dir() -> Path:
    """Get the data directory."""
    return get_project_root() / 'data'


def discover_tours(data_dir: Path) -> list:
    """Discover all available tours in the data directory."""
    tours = []
    
    if not data_dir.exists():
        return tours
    
    for subdir in sorted(data_dir.iterdir()):
        if subdir.is_dir():
            scripts_file = subdir / 'scripts.json'
            if scripts_file.exists():
                try:
                    with open(scripts_file, 'r', encoding='utf-8') as f:
                        pois = json.load(f)
                    tours.append({
                        'id': subdir.name,
                        'path': subdir,
                        'poi_count': len(pois),
                    })
                except Exception as e:
                    print(f"Warning: Could not load {scripts_file}: {e}")
    
    return tours


def strip_citations(text: str) -> str:
    """
    Remove citation markers like [1], [2], etc. from text.
    Handles patterns like " [1]", "[12]", etc.
    """
    return re.sub(r'\s*\[\d+\]', '', text)


async def generate_audio_for_poi(
    poi: dict, 
    output_dir: Path, 
    voice: str = DEFAULT_VOICE,
    skip_existing: bool = True
) -> str:
    """
    Generate an MP3 audio file for a single point of interest using Edge TTS.
    
    Args:
        poi: Dictionary containing POI data with 'num', 'name', and 'body'
        output_dir: Path to save the audio file
        voice: Edge TTS voice name (default: multilingual neural voice)
        skip_existing: Skip generation if file already exists
    
    Returns:
        Path to the generated audio file, or None on failure
    """
    num = poi['num']
    name = poi['name']
    body_paragraphs = poi['body']
    
    # Generate filename (zero-padded number only)
    filename = f"{num:02d}.mp3"
    output_path = output_dir / filename
    
    # Skip if file exists and skip_existing is True
    if skip_existing and output_path.exists():
        print(f"  ⏭ Skipping {num:02d}: {name[:40]}... (already exists)")
        return str(output_path)
    
    # Combine all paragraphs and strip citations
    full_text = ' '.join(body_paragraphs)
    clean_text = strip_citations(full_text)
    
    # Add an introduction with the POI name
    intro = f"{name}. "
    final_text = intro + clean_text
    
    print(f"  Generating {num:02d}: {name[:40]}...")
    
    try:
        communicate = edge_tts.Communicate(final_text, voice)
        await communicate.save(str(output_path))
        print(f"    ✓ Saved: {filename}")
        return str(output_path)
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return None


def generate_manifest(pois: list, output_dir: Path) -> Path:
    """Generate a manifest.json file for the tour."""
    manifest_path = output_dir / 'manifest.json'
    manifest = []
    
    for poi in pois:
        num = poi['num']
        filename = f"{num:02d}.mp3"
        
        manifest.append({
            'num': num,
            'name': poi['name'],
            'lat': poi['lat'],
            'lon': poi['lon'],
            'audio_file': filename,
            'leg': poi.get('leg', ''),
            'duration': poi.get('duration', '')
        })
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    return manifest_path


async def process_tour(
    tour_path: Path, 
    voice: str = DEFAULT_VOICE,
    skip_existing: bool = True,
    force: bool = False
) -> dict:
    """
    Process a single tour directory, generating audio for all POIs.
    
    Args:
        tour_path: Path to the tour directory
        voice: TTS voice to use
        skip_existing: Skip POIs that already have audio files
        force: Force regeneration of all audio files
    
    Returns:
        Dictionary with processing statistics
    """
    scripts_file = tour_path / 'scripts.json'
    audio_dir = tour_path / 'audio'
    
    if not scripts_file.exists():
        return {'error': f'scripts.json not found in {tour_path}'}
    
    # Create audio directory
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Load POI data
    with open(scripts_file, 'r', encoding='utf-8') as f:
        pois = json.load(f)
    
    print(f"\nProcessing tour: {tour_path.name}")
    print(f"  POIs: {len(pois)}")
    print(f"  Voice: {voice}")
    print(f"  Output: {audio_dir}")
    print("-" * 50)
    
    # Generate audio for each POI
    successful = 0
    skipped = 0
    failed = 0
    
    skip = skip_existing and not force
    
    for poi in pois:
        output_file = audio_dir / f"{poi['num']:02d}.mp3"
        
        if skip and output_file.exists():
            skipped += 1
            print(f"  ⏭ {poi['num']:02d}: {poi['name'][:35]}... (exists)")
            continue
        
        result = await generate_audio_for_poi(poi, audio_dir, voice, skip_existing=False)
        if result:
            successful += 1
        else:
            failed += 1
    
    # Generate manifest
    manifest_path = generate_manifest(pois, audio_dir)
    
    print("-" * 50)
    print(f"Tour '{tour_path.name}' complete:")
    print(f"  Generated: {successful}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Manifest: {manifest_path}")
    
    return {
        'tour': tour_path.name,
        'total': len(pois),
        'generated': successful,
        'skipped': skipped,
        'failed': failed,
    }


async def main():
    parser = argparse.ArgumentParser(
        description='Generate audio files for Camino tours',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_audio.py                    # Process all tours
  python generate_audio.py rio_grande_rift    # Process specific tour
  python generate_audio.py --list             # List available tours
  python generate_audio.py --force            # Regenerate all audio files
  python generate_audio.py --voice en-US-AvaMultilingualNeural  # Use different voice
        """
    )
    
    parser.add_argument(
        'tour',
        nargs='?',
        help='Tour directory name (default: process all tours)'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available tours and exit'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force regeneration of all audio files'
    )
    parser.add_argument(
        '--voice', '-v',
        default=DEFAULT_VOICE,
        help=f'TTS voice to use (default: {DEFAULT_VOICE})'
    )
    
    args = parser.parse_args()
    
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)
    
    # List tours
    tours = discover_tours(data_dir)
    
    if args.list:
        print("Available tours:")
        print("-" * 50)
        for tour in tours:
            print(f"  {tour['id']:<30} ({tour['poi_count']} POIs)")
        if not tours:
            print("  No tours found. Add directories with scripts.json to data/")
        sys.exit(0)
    
    if not tours:
        print("No tours found in data/. Add directories with scripts.json files.")
        sys.exit(1)
    
    # Process specific tour or all tours
    if args.tour:
        tour_path = data_dir / args.tour
        if not tour_path.exists():
            print(f"Error: Tour not found: {args.tour}")
            print(f"Available tours: {', '.join(t['id'] for t in tours)}")
            sys.exit(1)
        
        await process_tour(tour_path, voice=args.voice, force=args.force)
    else:
        print(f"Processing all {len(tours)} tour(s)...")
        
        results = []
        for tour in tours:
            result = await process_tour(tour['path'], voice=args.voice, force=args.force)
            results.append(result)
        
        # Summary
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        
        total_generated = sum(r.get('generated', 0) for r in results)
        total_skipped = sum(r.get('skipped', 0) for r in results)
        total_failed = sum(r.get('failed', 0) for r in results)
        
        for result in results:
            if 'error' in result:
                print(f"  ✗ {result.get('tour', 'unknown')}: {result['error']}")
            else:
                print(f"  ✓ {result['tour']}: {result['generated']} generated, {result['skipped']} skipped, {result['failed']} failed")
        
        print("-" * 50)
        print(f"Total: {total_generated} generated, {total_skipped} skipped, {total_failed} failed")


if __name__ == '__main__':
    asyncio.run(main())
