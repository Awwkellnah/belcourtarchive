#!/usr/bin/env python3
"""
populate_genre_country.py

Populates (or overwrites) each film's top-level `genre` and `country` fields
from the matched IMDb data in the same file.

Supports two file formats produced by the Belcourt enrichment tool:
  1. Enriched JSON export  – a flat array of film objects, each containing an
                             `enrichment.imdbData` sub-object.
  2. Project JSON file     – an object with separate `films` and `results` dicts,
                             keyed by film id.

Usage:
    python3 populate_genre_country.py <input.json> [output.json]

If output.json is omitted the input file is updated in-place.
"""

import json
import sys
from pathlib import Path


def get_imdb_data(film, results):
    """Return the best available imdbData dict for a film, or None."""
    film_id = str(film.get("id", ""))

    # Project format: look up in results dict
    if results is not None:
        entry = results.get(film_id) or {}
        imdb = entry.get("imdbData")
        if imdb:
            return imdb
        # Fall back to selected candidate details if imdbData wasn't fetched
        selected = entry.get("selected")
        candidates = entry.get("candidates") or []
        if selected and candidates:
            for c in candidates:
                if c.get("imdbID") == selected:
                    return c.get("details")

    # Enriched-export format: enrichment sub-object lives on the film itself
    enrichment = film.get("enrichment") or {}
    imdb = enrichment.get("imdbData")
    if imdb:
        return imdb
    # Fall back to selected candidate details
    selected = enrichment.get("selected")
    candidates = enrichment.get("candidates") or []
    if selected and candidates:
        for c in candidates:
            if c.get("imdbID") == selected:
                return c.get("details")

    return None


def process(data):
    """Mutate data in-place; return (updated_count, skipped_count)."""
    # Detect format
    if isinstance(data, list):
        films = data
        results = None
    elif isinstance(data, dict) and "films" in data:
        films = data["films"]
        results = data.get("results") or {}
    else:
        raise ValueError("Unrecognised JSON structure – expected an array or a project object.")

    updated = 0
    skipped = 0

    for film in films:
        imdb = get_imdb_data(film, results)
        if not imdb:
            skipped += 1
            continue

        changed = False
        for field in ("genre", "country"):
            value = imdb.get(field)
            if value:
                film[field] = value
                changed = True

        if changed:
            updated += 1
        else:
            skipped += 1

    return updated, skipped


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else input_path

    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {input_path} …")
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    updated, skipped = process(data)

    print(f"Writing {output_path} …")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Done — {updated} film(s) updated, {skipped} skipped (no IMDb match or no genre/country data).")


if __name__ == "__main__":
    main()
