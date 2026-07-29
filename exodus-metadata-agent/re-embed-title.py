#!/usr/bin/env python3
"""Re-embed chosen titles from a reviewed CSV log back into JPEG files.

Workflow:
  1. Run exodus_metadata_agent.py on a folder — generates CSV with title_1/2/3
  2. Open the CSV, delete the two titles you don't want, leave your chosen title
  3. Run this script pointing at that CSV:
       python3 re-embed-title.py --csv logs/exodus_metadata_log_20260709.csv

  Optional: add --rename to also rename the JPEG file to match the chosen title.
       python3 re-embed-title.py --csv logs/exodus_metadata_log_20260709.csv --rename

  Optional: add --dry-run to preview all changes without writing anything.
       python3 re-embed-title.py --csv logs/exodus_metadata_log_20260709.csv --rename --dry-run
"""

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Re-embed chosen titles into JPEG files")
    parser.add_argument("--csv", required=True, help="Path to the reviewed CSV log file")
    parser.add_argument(
        "--rename",
        action="store_true",
        help="Also rename each JPEG file to match the chosen title",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without writing any changes",
    )
    return parser.parse_args()


def find_chosen_title(row: dict) -> str:
    """Return the chosen title from the CSV row.

    Checks 'chosen_title' column first, then whichever of title_1/2/3
    is the only non-empty one remaining after the photographer's review.
    """
    chosen = row.get("chosen_title", "").strip()
    if chosen:
        return chosen

    candidates = [
        row.get(key, "").strip()
        for key in ["title_1", "title_2", "title_3"]
        if row.get(key, "").strip()
    ]

    return candidates[0] if candidates else ""


def title_to_filename(title: str) -> str:
    """Convert a title string to a clean dash-separated filename.

    'Ascent — Symmetry in Steel and Glass' →
    'Ascent-Symmetry-in-Steel-and-Glass.jpg'
    """
    # Replace em-dashes, en-dashes, colons, and other punctuation with a space
    cleaned = re.sub(r"[—–\/:*?\"<>|]", " ", title)
    # Replace any remaining non-alphanumeric characters (except spaces) with nothing
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    # Collapse multiple spaces, strip edges
    cleaned = " ".join(cleaned.split())
    # Replace spaces with dashes
    dashed = cleaned.replace(" ", "-")
    return dashed + ".jpg"


def embed_title(filepath: Path, title: str, dry_run: bool) -> str:
    """Write title into IPTC:Headline and XMP:Title. Returns 'success' or error message."""
    if not filepath.exists():
        return f"File not found: {filepath}"
    if dry_run:
        return "dry-run"

    result = subprocess.run(
        [
            "exiftool",
            "-overwrite_original",
            f"-IPTC:Headline={title}",
            f"-XMP:Title={title}",
            str(filepath),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return result.stderr.strip() or "exiftool failed"
    return "success"


def rename_file(filepath: Path, new_name: str, dry_run: bool) -> tuple[Path, str]:
    """Rename the file to new_name in the same folder. Returns (new_path, status)."""
    new_path = filepath.parent / new_name

    if new_path == filepath:
        return filepath, "unchanged"

    if new_path.exists():
        return filepath, f"Skipped rename — file already exists: {new_name}"

    if dry_run:
        return new_path, "dry-run"

    filepath.rename(new_path)
    return new_path, "renamed"


def main():
    args = parse_args()
    csv_path = Path(args.csv).expanduser().resolve()

    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("No rows found in CSV.")
        return

    eligible = [r for r in rows if r.get("embed_status") == "success"]
    if not eligible:
        print("No successfully processed rows found in CSV.")
        return

    print(f"Found {len(eligible)} image(s) to update.")
    if args.dry_run:
        print("DRY RUN — no files will be modified.\n")

    success_count = 0
    error_count = 0

    for row in eligible:
        filepath = Path(row["filepath"])
        title = find_chosen_title(row)

        if not title:
            print(f"  SKIP (no title found): {row['filename']}")
            continue

        # Embed the title
        embed_status = embed_title(filepath, title, dry_run=args.dry_run)

        if embed_status not in ("success", "dry-run"):
            print(f"  ERROR embedding: {row['filename']} — {embed_status}")
            error_count += 1
            continue

        # Rename if requested
        new_filename = title_to_filename(title)
        if args.rename:
            filepath, rename_status = rename_file(filepath, new_filename, dry_run=args.dry_run)
        else:
            rename_status = "not requested"

        # Report
        if args.dry_run:
            print(f"  {row['filename']}")
            print(f"    Title:  {title}")
            if args.rename:
                print(f"    Rename: {new_filename}")
        else:
            print(f"  OK: {row['filename']}")
            print(f"    Title:  {title}")
            if args.rename and rename_status == "renamed":
                print(f"    Renamed to: {new_filename}")
            elif args.rename:
                print(f"    Rename: {rename_status}")
            success_count += 1

    if not args.dry_run:
        print(f"\nDone. {success_count} updated, {error_count} errors.")


if __name__ == "__main__":
    main()
