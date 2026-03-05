#!/usr/bin/env python3
"""
validate_triggers.py  —  Check POI GPS triggers against the KML route geometry.

For each POI in scripts.json, computes the minimum distance from its lat/lon
to the nearest point on any route line in map.kml and reports whether it falls
within the app's configurable trigger radius.

Usage:
    python src/validate_triggers.py <tour_name>
    python src/validate_triggers.py <tour_name> --warn 500 --fail 2000
    python src/validate_triggers.py <tour_name> --suggest-fixes
    python src/validate_triggers.py <tour_name> --suggest-fixes --only-new

Thresholds (metres):
    --warn  default 500   POIs beyond this are flagged ⚠
    --fail  default 2000  POIs beyond this are flagged ✗ (hard problem)

    The app's trigger-radius slider spans 50–500 m (default 150 m).
    A POI trigger more than 500 m from the route line will never fire at
    default settings; beyond 2000 m it cannot fire even at maximum radius.

--suggest-fixes
    For each ⚠/✗ POI, finds the closest point on the route and prints
    the corrected lat/lon. Does NOT modify scripts.json automatically —
    review suggestions before applying.

--only-new
    Only report POIs whose name contains a known new-POI string, or whose
    num appears in a comma-separated list passed via --nums.
"""

import argparse
import json
import math
import os
import sys
import xml.etree.ElementTree as ET


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def closest_point_on_segment(plat, plon, alat, alon, blat, blon):
    """
    Return (closest_lat, closest_lon, distance_m) for point P to segment AB.
    Uses a flat approximation — accurate enough for segments < ~50 km.
    """
    dx, dy = blon - alon, blat - alat
    len2 = dx * dx + dy * dy
    if len2 == 0:
        return alat, alon, haversine_m(plat, plon, alat, alon)
    t = max(0.0, min(1.0, ((plon - alon) * dx + (plat - alat) * dy) / len2))
    clat, clon = alat + t * dy, alon + t * dx
    return clat, clon, haversine_m(plat, plon, clat, clon)


def closest_point_on_route(plat, plon, route_segments):
    """
    Return (closest_lat, closest_lon, distance_m) across all route segments.
    route_segments: list of (alon, alat, blon, blat) tuples.
    """
    best_d, best_lat, best_lon = float("inf"), plat, plon
    for alon, alat, blon, blat in route_segments:
        clat, clon, d = closest_point_on_segment(plat, plon, alat, alon, blat, blon)
        if d < best_d:
            best_d, best_lat, best_lon = d, clat, clon
    return best_lat, best_lon, best_d


# ---------------------------------------------------------------------------
# KML loading
# ---------------------------------------------------------------------------

def load_route_segments(tour_dir):
    """
    Parse map.kml and return a flat list of (alon, alat, blon, blat) tuples
    representing every consecutive pair of points in every LineString.
    """
    kml_path = os.path.join(tour_dir, "map.kml")
    if not os.path.exists(kml_path):
        raise FileNotFoundError(
            f"No map.kml in {tour_dir}. Run: python src/fetch_resources.py <tour>"
        )

    tree = ET.parse(kml_path)
    root = tree.getroot()
    ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""

    segments = []
    for pm in root.iter(f"{ns}Placemark"):
        ls = pm.find(f"{ns}LineString")
        if ls is None:
            continue
        coords_text = ls.findtext(f"{ns}coordinates", "")
        pts = []
        for c in coords_text.strip().split():
            parts = c.split(",")
            if len(parts) >= 2:
                try:
                    pts.append((float(parts[0]), float(parts[1])))  # (lon, lat)
                except ValueError:
                    pass
        for i in range(len(pts) - 1):
            alon, alat = pts[i]
            blon, blat = pts[i + 1]
            segments.append((alon, alat, blon, blat))

    return segments


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate POI GPS triggers against the KML route geometry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("tour_name", help="Tour subfolder name inside data/")
    parser.add_argument(
        "--warn", type=float, default=500, metavar="M",
        help="Distance in metres beyond which a POI is flagged ⚠ (default 500)"
    )
    parser.add_argument(
        "--fail", type=float, default=2000, metavar="M",
        help="Distance in metres beyond which a POI is flagged ✗ (default 2000)"
    )
    parser.add_argument(
        "--suggest-fixes", action="store_true",
        help="For each ⚠/✗ POI, print the nearest route point as a suggested fix"
    )
    parser.add_argument(
        "--nums", default="",
        help="Comma-separated POI numbers to check (default: all)"
    )
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tour_dir = os.path.join(repo_root, "data", args.tour_name)

    filter_nums = set()
    if args.nums:
        for n in args.nums.split(","):
            try:
                filter_nums.add(int(n.strip()))
            except ValueError:
                pass

    # Load data
    segments = load_route_segments(tour_dir)
    scripts_path = os.path.join(tour_dir, "scripts.json")
    with open(scripts_path) as f:
        pois = json.load(f)

    if filter_nums:
        pois = [p for p in pois if p.get("num") in filter_nums]

    print(f"\n{'='*72}")
    print(f"  Trigger validation: {args.tour_name}")
    print(f"{'='*72}")
    print(f"  POIs     : {len(pois)}")
    print(f"  Route pts: {len(segments) + 1:,}")
    print(f"  ⚠  warn  : > {args.warn:.0f} m")
    print(f"  ✗  fail  : > {args.fail:.0f} m")
    print(f"  (App radius slider: 50–500 m, default 150 m)")
    print()

    warn_count = fail_count = 0
    fixes = []

    print(f"  {'#':>3}  {'Name':<46}  {'Dist':>8}  Status")
    print(f"  {'-'*70}")

    for p in pois:
        clat, clon, d = closest_point_on_route(p["lat"], p["lon"], segments)

        if d > args.fail:
            flag = "✗"
            fail_count += 1
        elif d > args.warn:
            flag = "⚠"
            warn_count += 1
        else:
            flag = "✓"

        print(f"  {p['num']:>3}  {p['name']:<46}  {d:>6.0f} m  {flag}")

        if flag in ("⚠", "✗") and args.suggest_fixes:
            fixes.append((p, clat, clon, d))

    print()
    ok = len(pois) - warn_count - fail_count
    print(f"  ✓ OK   : {ok}")
    print(f"  ⚠ Warn : {warn_count}")
    print(f"  ✗ Fail : {fail_count}")

    if fixes:
        print(f"\n{'='*72}")
        print(f"  Suggested coordinate fixes (nearest point on route line)")
        print(f"  Review carefully — road nearest to POI may not be the right")
        print(f"  trigger point (e.g. for sites on side roads or detours).")
        print(f"{'='*72}")
        for p, clat, clon, d in fixes:
            print(f"\n  POI {p['num']}: {p['name']}")
            print(f"    Current : lat {p['lat']},  lon {p['lon']}  ({d:.0f} m off route)")
            print(f"    Nearest : lat {clat:.6f},  lon {clon:.6f}")

    if fail_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
