"""
set_repertory.py
----------------
Automatically sets the `repertory` field on films played in 2000 or later.

Rule:
  - If the IMDb year is 4 or more years older than the year the film played
    → repertory = True
  - Otherwise
    → repertory = False
  - Films played before 2000, or films with no IMDb match, are left unchanged.

Usage:
  python3 set_repertory.py belcourt_project_2026-04-16.json
  python3 set_repertory.py belcourt_project_2026-04-16.json --gap 5   # change the year gap
  python3 set_repertory.py belcourt_project_2026-04-16.json --dry-run # preview without saving
"""

import json
import sys
import os
import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Set repertory field in Belcourt project file.")
    parser.add_argument("input", help="Path to belcourt_project_*.json")
    parser.add_argument("--gap", type=int, default=4,
                        help="Year gap threshold for repertory classification (default: 4)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing any files")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: file not found: {args.input}")
        sys.exit(1)

    print(f"Loading {args.input}…")
    with open(args.input, encoding="utf-8") as f:
        project = json.load(f)

    films = project.get("films", [])
    if not films:
        print("Error: no 'films' array found in project file.")
        sys.exit(1)

    # Legacy project files may still have a separate customFilms array — merge it in
    legacy_custom = project.get("customFilms", [])
    if legacy_custom:
        films = films + legacy_custom
        print(f"  Note: merged {len(legacy_custom):,} legacy customFilms into films array.")

    # Build merged results lookup: preloadedResults + saved decisions
    results = dict(project.get("preloadedResults", {}))
    results.update(project.get("results", {}))

    print(f"  Total films to process: {len(films):,}")

    # --- Apply the rule ---
    stats = {
        "set_repertory": 0,
        "set_new_release": 0,
        "skipped_pre_2000": 0,
        "skipped_no_imdb": 0,
    }
    changes = []  # (film_id, title, played_year, imdb_year, old_rep, new_rep)

    for film in films:
        played_year = film.get("y")

        # Only process 2000 and later
        if not played_year or played_year < 2000:
            stats["skipped_pre_2000"] += 1
            continue

        # Look up IMDb year
        r = results.get(str(film["id"]))
        imdb_year_raw = r and r.get("imdbData", {}) and r["imdbData"].get("year")

        if not imdb_year_raw:
            stats["skipped_no_imdb"] += 1
            continue

        try:
            imdb_year = int(str(imdb_year_raw)[:4])
        except ValueError:
            stats["skipped_no_imdb"] += 1
            continue

        old_rep = film.get("repertory")
        new_rep = True if (played_year - imdb_year) >= args.gap else False

        if old_rep != new_rep:
            changes.append((film["id"], film["t"], played_year, imdb_year, old_rep, new_rep))
            if not args.dry_run:
                film["repertory"] = new_rep

        if new_rep:
            stats["set_repertory"] += 1
        else:
            stats["set_new_release"] += 1

    # --- Report ---
    print(f"\nResults (gap = {args.gap} years):")
    print(f"  Repertory (True):    {stats['set_repertory']:,}")
    print(f"  New release (False): {stats['set_new_release']:,}")
    print(f"  Skipped — pre-2000: {stats['skipped_pre_2000']:,}")
    print(f"  Skipped — no IMDb:  {stats['skipped_no_imdb']:,}")
    print(f"  Fields changed:     {len(changes):,}")

    if changes:
        print(f"\nSample of changes (first 20):")
        print(f"  {'ID':<8} {'Title':<40} {'Played':<7} {'IMDb':<6} {'Old':<10} → New")
        print(f"  {'-'*8} {'-'*40} {'-'*7} {'-'*6} {'-'*10}   {'-'*10}")
        for fid, title, py, iy, old, new in changes[:20]:
            title_str = (title[:38] + "…") if len(title) > 39 else title
            print(f"  {fid:<8} {title_str:<40} {py:<7} {iy:<6} {str(old):<10} → {new}")
        if len(changes) > 20:
            print(f"  … and {len(changes) - 20:,} more")

    if args.dry_run:
        print("\nDry run — no files written.")
        return

    # --- Save updated project file ---
    date_str = datetime.now().strftime("%Y-%m-%d")
    base, ext = os.path.splitext(args.input)
    output_path = f"{base}_repertory_updated{ext}"

    # Avoid overwriting an existing output file
    counter = 1
    while os.path.exists(output_path):
        output_path = f"{base}_repertory_updated_{counter}{ext}"
        counter += 1

    project["films"] = films          # write back (includes merged legacy custom films)
    project["customFilms"] = []       # clear — all entries now live in films
    project["savedAt"] = datetime.utcnow().isoformat() + "Z"

    print(f"\nWriting updated project to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(project, f, separators=(",", ":"))

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"Done. ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
