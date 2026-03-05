#!/usr/bin/env python3
"""
fetch_resources.py  —  Bootstrap a new tour from input.json.

Reads    data/<tour>/input.json
Fetches  data/<tour>/map.kml     from url_map  (Google My Maps KML export)
Fetches  data/<tour>/cover.jpg   from url_cover (optional; generates placeholder if absent)
Writes   data/<tour>/tour.json   from name + description fields

Usage:
    python src/fetch_resources.py <tour_name>
    python src/fetch_resources.py <tour_name> --force   # re-fetch even if files exist

input.json schema:
{
  "name":        "Display name of the tour",
  "description": "One-sentence description shown on the tour card",
  "url_map":     "https://www.google.com/maps/d/u/0/view?mid=...",
  "url_cover":   "https://..." | null
}
"""

import argparse
import io
import json
import os
import ssl
import sys
import urllib.request
import urllib.parse
import zipfile

# Pillow is in requirements.txt
from PIL import Image

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_bytes(url: str) -> bytes:
    """Fetch a URL and return raw bytes. Raises on non-200."""
    req = urllib.request.Request(url, headers=HEADERS)
    # Create SSL context that verifies certificates
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        if resp.status != 200:
            raise IOError(f"HTTP {resp.status} for {url}")
        return resp.read()


def extract_map_mid(url: str) -> str:
    """
    Extract the 'mid' parameter from any Google My Maps URL variant.
    Supported formats:
      https://www.google.com/maps/d/u/0/view?mid=XXX&usp=sharing
      https://www.google.com/maps/d/viewer?mid=XXX
      https://www.google.com/maps/d/edit?mid=XXX
    """
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if "mid" not in qs:
        raise ValueError(
            f"Could not find 'mid' parameter in url_map: {url}\n"
            "Make sure you copied the full URL from Google My Maps."
        )
    return qs["mid"][0]


def kml_export_url(mid: str) -> str:
    return f"https://www.google.com/maps/d/kml?mid={mid}&forcekml=1"


def is_kmz(data: bytes) -> bool:
    """KMZ files are ZIP archives; detect by magic bytes."""
    return data[:2] == b"PK"


def kmz_to_kml(data: bytes) -> bytes:
    """Extract the primary .kml file from a KMZ (ZIP) archive."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        kml_names = [n for n in zf.namelist() if n.lower().endswith(".kml")]
        if not kml_names:
            raise ValueError("No .kml file found inside the KMZ archive.")
        with zf.open(kml_names[0]) as f:
            return f.read()


def save_cover_from_url(url: str, out_path: str) -> None:
    """Fetch an image URL, convert to JPEG, save to out_path."""
    data = fetch_bytes(url)
    img = Image.open(io.BytesIO(data))
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    img.save(out_path, "JPEG", quality=90)


def generate_placeholder_cover(tour_dir: str, tour_name: str) -> None:
    """Call create_cover.create_cover() to produce a placeholder cover.jpg."""
    # Import relative to src/
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from create_cover import create_cover
    create_cover(tour_dir, tour_name)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch map KML and cover image for a tour from input.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("tour_name", help="Tour subfolder name inside data/")
    parser.add_argument(
        "--force", "-f", action="store_true",
        help="Re-fetch files even if they already exist"
    )
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tour_dir = os.path.join(repo_root, "data", args.tour_name)
    os.makedirs(tour_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Load input.json
    # ------------------------------------------------------------------
    input_path = os.path.join(tour_dir, "input.json")
    if not os.path.exists(input_path):
        example = {
            "name": args.tour_name.replace("_", " ").title(),
            "description": "One-sentence tour description.",
            "url_map": "https://www.google.com/maps/d/u/0/view?mid=YOUR_MAP_ID",
            "url_cover": None
        }
        with open(input_path, "w") as f:
            json.dump(example, f, indent=2)
        print(f"Created template: {input_path}")
        print("Fill in name, description, url_map (and optionally url_cover), then re-run.")
        sys.exit(0)

    with open(input_path) as f:
        cfg = json.load(f)

    required = ["name", "url_map"]
    for key in required:
        if not cfg.get(key):
            print(f"Error: '{key}' is required in input.json", file=sys.stderr)
            sys.exit(1)

    tour_name_display = cfg["name"]
    description = cfg.get("description", "")
    url_map = cfg["url_map"]
    url_cover = cfg.get("url_cover") or None

    print(f"\n{'='*55}")
    print(f"  Fetching resources for: {tour_name_display}")
    print(f"{'='*55}")

    errors = []

    # ------------------------------------------------------------------
    # 1. map.kml  — fetch from Google My Maps KML export endpoint
    # ------------------------------------------------------------------
    kml_path = os.path.join(tour_dir, "map.kml")
    if os.path.exists(kml_path) and not args.force:
        print(f"  ⏭  map.kml already exists (use --force to re-fetch)")
    else:
        try:
            mid = extract_map_mid(url_map)
            export_url = kml_export_url(mid)
            print(f"  ↓  Fetching map KML (mid={mid}) ...")
            data = fetch_bytes(export_url)

            # Google sometimes returns KMZ even with forcekml=1
            if is_kmz(data):
                print(f"     Got KMZ — extracting inner KML ...")
                data = kmz_to_kml(data)

            with open(kml_path, "wb") as f:
                f.write(data)

            # Quick sanity: count placemarks
            n_placemarks = data.count(b"<Placemark")
            print(f"  ✓  map.kml  ({len(data):,} bytes, ~{n_placemarks} placemarks)")

        except Exception as e:
            errors.append(f"map.kml: {e}")
            print(f"  ✗  map.kml failed: {e}")

    # ------------------------------------------------------------------
    # 2. cover.jpg — fetch from url_cover, or generate placeholder
    # ------------------------------------------------------------------
    cover_path = os.path.join(tour_dir, "cover.jpg")
    if os.path.exists(cover_path) and not args.force:
        print(f"  ⏭  cover.jpg already exists (use --force to re-fetch)")
    elif url_cover:
        try:
            print(f"  ↓  Fetching cover image ...")
            save_cover_from_url(url_cover, cover_path)
            size = os.path.getsize(cover_path)
            print(f"  ✓  cover.jpg  ({size:,} bytes)")
        except Exception as e:
            errors.append(f"cover.jpg: {e}")
            print(f"  ✗  cover.jpg fetch failed: {e}")
            print(f"     Falling back to generated placeholder ...")
            try:
                generate_placeholder_cover(tour_dir, tour_name_display)
            except Exception as e2:
                errors.append(f"cover.jpg placeholder: {e2}")
    else:
        print(f"  ⚙  No url_cover — generating placeholder cover ...")
        try:
            generate_placeholder_cover(tour_dir, tour_name_display)
            print(f"  ✓  cover.jpg  (generated placeholder)")
        except Exception as e:
            errors.append(f"cover.jpg placeholder: {e}")
            print(f"  ✗  cover.jpg placeholder failed: {e}")

    # ------------------------------------------------------------------
    # 3. tour.json  — write from input.json name + description
    # ------------------------------------------------------------------
    tour_json_path = os.path.join(tour_dir, "tour.json")
    if os.path.exists(tour_json_path) and not args.force:
        print(f"  ⏭  tour.json already exists (use --force to overwrite)")
    else:
        tour_meta = {"name": tour_name_display, "description": description}
        with open(tour_json_path, "w") as f:
            json.dump(tour_meta, f, indent=2)
        print(f"  ✓  tour.json")

    # ------------------------------------------------------------------
    # 4. Ensure audio/ subdirectory exists
    # ------------------------------------------------------------------
    audio_dir = os.path.join(tour_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Summary + next steps
    # ------------------------------------------------------------------
    print()
    if errors:
        print(f"  Completed with {len(errors)} error(s):")
        for err in errors:
            print(f"    • {err}")
    else:
        print(f"  All resources fetched successfully.")

    print(f"""
Next steps:
  1. Review the map markers vs. existing scripts:
       python src/analyze_map.py {args.tour_name}

  2. Generate stub POI entries for any gaps:
       python src/analyze_map.py {args.tour_name} --stubs
       # → data/{args.tour_name}/candidates.json

  3. Research and write scripts for each stub (see CLAUDE.md style guide)

  4. Merge completed POIs into data/{args.tour_name}/scripts.json

  5. Generate TTS audio:
       python src/generate_audio.py {args.tour_name}
""")


if __name__ == "__main__":
    main()
