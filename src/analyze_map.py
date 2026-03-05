#!/usr/bin/env python3
"""
analyze_map.py  —  Compare a Google My Maps KML/KMZ export to existing scripts.json.

Reads   data/<tour>/map.kml  (or map.kmz)
Reads   data/<tour>/scripts.json
Reports which map markers lack a nearby script (gaps), and which are covered.

Usage:
    python src/analyze_map.py <tour_name>
    python src/analyze_map.py <tour_name> --threshold 8
    python src/analyze_map.py <tour_name> --gaps-only
    python src/analyze_map.py <tour_name> --stubs      # writes candidates.json

To export from Google My Maps:
    Open your map → ⋮ menu → Export to KML/KMZ
    Check "Export to a .KML file" (not KMZ) for plain text.
    Save as  data/<tour_name>/map.kml
"""

import argparse
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# KML loading and parsing
# ---------------------------------------------------------------------------

def load_kml_text(tour_dir):
    """Return raw KML text from map.kml or map.kmz in tour_dir."""
    kml_path = os.path.join(tour_dir, "map.kml")
    kmz_path = os.path.join(tour_dir, "map.kmz")

    if os.path.exists(kml_path):
        with open(kml_path, encoding="utf-8") as f:
            return f.read()

    if os.path.exists(kmz_path):
        with zipfile.ZipFile(kmz_path) as zf:
            kml_names = [n for n in zf.namelist() if n.lower().endswith(".kml")]
            if not kml_names:
                raise FileNotFoundError("No .kml file found inside map.kmz")
            with zf.open(kml_names[0]) as f:
                return f.read().decode("utf-8")

    raise FileNotFoundError(
        f"No map.kml or map.kmz found in {tour_dir}\n"
        "\n"
        "To export from Google My Maps:\n"
        "  1. Open your map in a browser\n"
        "  2. Click the ⋮ menu next to the map title\n"
        "  3. Choose 'Export to KML/KMZ'\n"
        "  4. Select 'Export as .KML file' (not KMZ)\n"
        f"  5. Save as  {kml_path}"
    )


def strip_html(text):
    """Remove HTML tags and decode common entities from a KML description."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    return " ".join(text.split())


def parse_kml(kml_text):
    """
    Parse KML and return a list of layers, each containing point placemarks.

    Returns:
        [
            {
                "name": "Layer / Folder name",
                "placemarks": [
                    {"name": str, "lat": float, "lon": float, "desc": str},
                    ...
                ]
            },
            ...
        ]
    Lines and polygons are silently skipped — only Points are returned.
    """
    root = ET.fromstring(kml_text)

    # Detect namespace (Google My Maps uses http://www.opengis.net/kml/2.2)
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    def tag(name):
        return f"{ns}{name}"

    def text_of(el, child, default=""):
        t = el.find(tag(child))
        return t.text.strip() if (t is not None and t.text) else default

    def parse_placemark(pm):
        """Return a dict for a Point placemark, or None if not a Point."""
        point = pm.find(tag("Point"))
        if point is None:
            return None
        coords_text = text_of(point, "coordinates")
        if not coords_text:
            return None
        parts = coords_text.strip().split(",")
        if len(parts) < 2:
            return None
        try:
            lon, lat = float(parts[0]), float(parts[1])
        except ValueError:
            return None
        return {
            "name": text_of(pm, "name") or "Unnamed",
            "lat": lat,
            "lon": lon,
            "desc": strip_html(text_of(pm, "description")),
        }

    # Locate Document root
    doc = root.find(tag("Document")) or root

    # Google My Maps: one Folder per layer
    folders = doc.findall(tag("Folder"))
    if not folders:
        folders = [doc]  # flat structure

    layers = []
    for folder in folders:
        layer_name = text_of(folder, "name") or "Unnamed Layer"
        placemarks = []
        for pm in folder.findall(tag("Placemark")):
            parsed = parse_placemark(pm)
            if parsed:
                placemarks.append(parsed)
        if placemarks:
            layers.append({"name": layer_name, "placemarks": placemarks})

    return layers


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------

def nearest_script(lat, lon, scripts):
    """Return (script_dict, distance_km) of the script nearest to lat/lon."""
    best, best_d = None, float("inf")
    for s in scripts:
        d = haversine_km(lat, lon, s.get("lat", 0), s.get("lon", 0))
        if d < best_d:
            best_d, best = d, s
    return best, best_d


def make_stub(marker, layer_name, idx):
    """Return a template scripts.json entry for a gap marker."""
    return {
        "num": f"CANDIDATE_{idx}",
        "name": marker["name"],
        "leg": layer_name,
        "duration": "3:00",
        "words": 450,
        "lat": round(marker["lat"], 6),
        "lon": round(marker["lon"], 6),
        "cited": False,
        "_map_description": marker["desc"] or "(no description in source map)",
        "_status": "STUB — research needed; replace body + sources before merging",
        "body": [
            f"[Script needed for: {marker['name']}. "
            f"GPS: {marker['lat']:.4f}, {marker['lon']:.4f}]"
        ],
        "sources": []
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze a Google My Maps KML export against existing scripts.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("tour_name", help="Tour subfolder name inside data/")
    parser.add_argument(
        "--threshold", "-t", type=float, default=5.0, metavar="KM",
        help="km radius within which a map marker is considered 'covered' by an existing script (default: 5.0)"
    )
    parser.add_argument(
        "--gaps-only", action="store_true",
        help="Print only uncovered markers (suppress covered-marker output)"
    )
    parser.add_argument(
        "--stubs", action="store_true",
        help="Write stub POI entries for all gaps to data/<tour>/candidates.json"
    )
    args = parser.parse_args()

    # Locate tour directory relative to this script's parent
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tour_dir = os.path.join(repo_root, "data", args.tour_name)

    if not os.path.isdir(tour_dir):
        print(f"Error: tour directory not found: {tour_dir}", file=sys.stderr)
        sys.exit(1)

    # Load
    kml_text = load_kml_text(tour_dir)
    layers = parse_kml(kml_text)

    scripts_path = os.path.join(tour_dir, "scripts.json")
    scripts = []
    if os.path.exists(scripts_path):
        with open(scripts_path) as f:
            scripts = json.load(f)

    total_markers = sum(len(l["placemarks"]) for l in layers)
    all_gaps = []
    candidate_idx = 1

    # Header
    print(f"\n{'='*60}")
    print(f"  Map Analysis: {args.tour_name}")
    print(f"{'='*60}")
    print(f"  Layers   : {len(layers)}")
    print(f"  Markers  : {total_markers}")
    print(f"  Scripts  : {len(scripts)}")
    print(f"  Threshold: {args.threshold} km")
    print()

    # Per-layer report
    for layer in layers:
        covered = []
        gaps = []

        for pm in layer["placemarks"]:
            script, dist = nearest_script(pm["lat"], pm["lon"], scripts)
            if dist <= args.threshold:
                covered.append((pm, script, dist))
            else:
                stub = make_stub(pm, layer["name"], candidate_idx)
                candidate_idx += 1
                gaps.append((pm, stub, dist))
                all_gaps.append(stub)

        if not args.gaps_only:
            label = f"── {layer['name']} ({len(layer['placemarks'])} markers)"
            print(label)

            for pm, script, dist in covered:
                print(f"  ✓  {pm['name']}")
                print(f"       → POI {script['num']}: {script['name']}  ({dist:.1f} km)")

            for pm, stub, dist in gaps:
                nearest_script_obj, nearest_dist = nearest_script(pm["lat"], pm["lon"], scripts)
                print(f"  ✗  {pm['name']}  [{pm['lat']:.4f}, {pm['lon']:.4f}]")
                if nearest_script_obj:
                    print(f"       → nearest script: POI {nearest_script_obj['num']} "
                          f"'{nearest_script_obj['name']}'  ({nearest_dist:.1f} km)  [GAP]")
                else:
                    print(f"       → no scripts found  [GAP]")
            print()

        else:
            for pm, stub, dist in gaps:
                print(f"  ✗  [{layer['name']}]  {pm['name']}  "
                      f"({pm['lat']:.4f}, {pm['lon']:.4f})")

    # Summary
    n_covered = total_markers - len(all_gaps)
    print(f"{'='*60}")
    print(f"  Covered : {n_covered} / {total_markers}  ({100*n_covered//total_markers}%)")
    print(f"  Gaps    : {len(all_gaps)}")

    if all_gaps:
        if args.stubs:
            out_path = os.path.join(tour_dir, "candidates.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(all_gaps, f, indent=2, ensure_ascii=False)
            print(f"\n  Stubs written → {out_path}")
            print(f"  Next steps:")
            print(f"    1. Open candidates.json and research each stub")
            print(f"    2. Replace the placeholder body[] with a real script")
            print(f"    3. Add sources[], set cited: true")
            print(f"    4. Merge into scripts.json (maintain route order)")
            print(f"    5. Run: python src/generate_audio.py {args.tour_name}")
        else:
            print(f"\n  Run with --stubs to write candidate entries to candidates.json")
    print()


if __name__ == "__main__":
    main()
