"""
set_venue.py
------------
Sets the `co` (venue) field to "Belcourt Theatre" on every film
played in 2000 or later.

Films played before 2000 are left unchanged.

Usage:
  python3 set_venue.py belcourt_project_2026-04-16.json
  python3 set_venue.py belcourt_project_2026-04-16.json --venue "Belcourt Theatre"
  python3 set_venue.py belcourt_project_2026-04-16.json --dry-run
"""

import json
import sys
import os
import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Set venue field in Belcourt project file.")
    parser.add_argument("input", help="Path to belcourt_project_*.json")
    parser.add_argument("--venue", default="Belcourt Theatre",
                        help='Venue name to set (default: "Belcourt Theatre")')
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing any files")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print("Error: file not found: %s" % args.input)
        sys.exit(1)

    print("Loading %s..." % args.input)
    with open(args.input, encoding="utf-8") as f:
        project = json.load(f)

    films = project.get("films", [])
    if not films:
        print("Error: no 'films' array found in project file.")
        sys.exit(1)

    # Merge legacy customFilms if present
    legacy_custom = project.get("customFilms", [])
    if legacy_custom:
        films = films + legacy_custom
        print("  Note: merged %d legacy customFilms into films array." % len(legacy_custom))

    print("  Total films: %s" % "{:,}".format(len(films)))

    stats = {
        "updated":        0,
        "already_set":    0,
        "skipped_pre_2000": 0,
        "skipped_no_year":  0,
    }
    changes = []  # (film_id, title, played_year, old_venue, new_venue)

    for film in films:
        played_year = film.get("y")

        if not played_year:
            stats["skipped_no_year"] += 1
            continue

        if played_year < 2000:
            stats["skipped_pre_2000"] += 1
            continue

        old_venue = film.get("co")

        if old_venue == args.venue:
            stats["already_set"] += 1
            continue

        changes.append((film["id"], film["t"], played_year, old_venue, args.venue))
        stats["updated"] += 1
        if not args.dry_run:
            film["co"] = args.venue

    # --- Report ---
    print("\nResults:")
    print("  Updated:          %s" % "{:,}".format(stats["updated"]))
    print("  Already correct:  %s" % "{:,}".format(stats["already_set"]))
    print("  Skipped — pre-2000: %s" % "{:,}".format(stats["skipped_pre_2000"]))
    print("  Skipped — no year:  %s" % "{:,}".format(stats["skipped_no_year"]))

    if changes:
        print("\nSample of changes (first 20):")
        print("  %-8s  %-40s  %-7s  Old venue" % ("ID", "Title", "Played"))
        print("  %s  %s  %s  %s" % ("-"*8, "-"*40, "-"*7, "-"*30))
        for fid, title, py, old, new in changes[:20]:
            title_str = (title[:38] + "...") if len(title) > 39 else title
            old_str = old if old else "(none)"
            print("  %-8s  %-40s  %-7s  %s" % (fid, title_str, py, old_str))
        if len(changes) > 20:
            print("  ... and %s more" % "{:,}".format(len(changes) - 20))

    if args.dry_run:
        print("\nDry run — no files written.")
        return

    # --- Save updated project file ---
    base, ext = os.path.splitext(args.input)
    output_path = "%s_venue_updated%s" % (base, ext)

    counter = 1
    while os.path.exists(output_path):
        output_path = "%s_venue_updated_%d%s" % (base, counter, ext)
        counter += 1

    project["films"] = films
    project["customFilms"] = []
    project["savedAt"] = datetime.utcnow().isoformat() + "Z"

    print("\nWriting updated project to: %s" % output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(project, f, separators=(",", ":"))

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print("Done. (%.1f MB)" % size_mb)


if __name__ == "__main__":
    main()
