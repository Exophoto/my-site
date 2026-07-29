#!/usr/bin/env python3
"""Re-embed chosen titles from a reviewed CSV log back into JPEG files.

Workflow:
  1. Run exodus_metadata_agent.py on a folder — generates CSV with title_1/2/3
  2. Open the CSV, delete the two titles you don't want, leave your chosen title
     in the 'chosen_title' column (or just leave title_1/2/3 and we pick the
     non-empty one)
  3. Run this script pointing at that CSV:
       python3 re-embed-title.py --csv logs/exodus_metadata_log_20260709.csv

The script reads each row, finds your chosen title, and writes it into the
JPEG file's IPTC:Headline and XMP:Title fields — leaving all other metadata
(description, keywords, alt text) untouched.
"""

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Re-embed chosen titles into JPEG files")
    parser.add_argument("--csv", required=True, help="Path to the reviewed CSV log file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be embedded without actually writing to files",
    )
    return parser.parse_args()


def find_chosen_title(row: dict) -> str:
    """Find the chosen title from the CSV row.

    Looks for a non-empty 'chosen_title' column first.
    Falls back to whichever of title_1/2/3 is the only one remaining.
    """
    chosen = row.get("chosen_title", "").strip()
    if chosen:
        return chosen

    candidates = []
    for key in ["title_1", "title_2", "title_3"]:
        val = row.get(key, "").strip()
        if val:
            candidates.append(val)

    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        return candidates[0]
    return ""


def embed_title(filepath: Path, title: str, dry_run: bool) -> str:
    """Write the title into IPTC:Headline and XMP:Title. Returns 'success' or error."""
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


def main():
    args = parse_args()
    csv_path = Path(args.csv).expanduser().resolve()

    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("No rows found in CSV.")
        return

    # Only process rows that were successfully embedded originally
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

        status = embed_title(filepath, title, dry_run=args.dry_run)

        if args.dry_run:
            print(f"  Would embed: {row['filename']}")
            print(f"    Title: {title}")
        elif status == "success":
            print(f"  OK: {row['filename']}")
            print(f"    Title: {title}")
            success_count += 1
        else:
            print(f"  ERROR: {row['filename']} — {status}")
            error_count += 1

    if not args.dry_run:
        print(f"\nDone. {success_count} updated, {error_count} errors.")


if __name__ == "__main__":
    main()
