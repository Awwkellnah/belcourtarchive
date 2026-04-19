"""
set_35mm.py
-----------
Automatically sets the `35mm` field on films whose title contains "(35mm)"
(case-insensitive).

Rule:
  - If the title field contains "(35mm)" → 35mm = True
  - Otherwise                            → 35mm = False
  - Films with no title are skipped.

Usage:
  python3 set_35mm.py belcourt_project_2026-04-16.json
  python3 set_35mm.py belcourt_project_2026-04-16.json --dry-run  # preview without saving
"""

import json
import sys
import os
import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Set 35mm field in Belcourt project file.")
    parser.add_argument("input", help="Path to belcourt_project_*.json")
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

    print("  Total films to process: %s" % "{:,}".format(len(films)))

    stats = {
        "set_true":  0,
        "set_false": 0,
        "skipped":   0,
    }
    changes = []  # (film_id, title, old_val, new_val)

    for film in films:
        title = film.get("t", "")
        if not title:
            stats["skipped"] += 1
            continue

        new_val = "(35mm)" in title.lower()
        old_val = film.get("35mm")

        if old_val != new_val:
            changes.append((film["id"], title, old_val, new_val))
            if not args.dry_run:
                film["35mm"] = new_val

        if new_val:
            stats["set_true"] += 1
        else:
            stats["set_false"] += 1

    # --- Report ---
    print("\nResults:")
    print("  35mm = True:  %s" % "{:,}".format(stats["set_true"]))
    print("  35mm = False: %s" % "{:,}".format(stats["set_false"]))
    print("  Skipped:      %s" % "{:,}".format(stats["skipped"]))
    print("  Fields changed: %s" % "{:,}".format(len(changes)))

    if changes:
        print("\nSample of changes (first 20):")
        print("  %-8s  %-50s  %-10s  -> New" % ("ID", "Title", "Old"))
        print("  %s  %s  %s     %s" % ("-"*8, "-"*50, "-"*10, "-"*5))
        for fid, title, old, new in changes[:20]:
            title_str = (title[:48] + "…") if len(title) > 49 else title
            print("  %-8s  %-50s  %-10s  -> %s" % (fid, title_str, str(old), new))
        if len(changes) > 20:
            print("  … and %s more" % "{:,}".format(len(changes) - 20))

    if args.dry_run:
        print("\nDry run — no files written.")
        return

    # --- Save updated project file ---
    base, ext = os.path.splitext(args.input)
    output_path = "%s_35mm_updated%s" % (base, ext)

    counter = 1
    while os.path.exists(output_path):
        output_path = "%s_35mm_updated_%d%s" % (base, counter, ext)
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
