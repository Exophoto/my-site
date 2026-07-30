#!/usr/bin/env python3
"""Exodus Photography File Scanner.

Scans Rick's Lacie for:
  - JPEGs over 5MB  → copied to /Volumes/Ricks Lacie/HRJPEGs/ (preserving folder structure)
  - TIFF and PSD files → copied to /Volumes/Ricks Lacie/HRRAW/ (preserving folder structure)

Skips the HRJPEGs and HRRAW folders themselves to avoid copying into a loop.
Logs all results to a CSV in the Desktop Exodus-Metadata-Agent/logs folder.
"""

import csv
import shutil
import sys
from datetime import date
from pathlib import Path

DRIVE = Path("/Volumes/Ricks Lacie")
HRJPEGS = DRIVE / "HRJPEGs"
HRRAW = DRIVE / "HRRAW"
SKIP_FOLDERS = {"HRJPEGs", "HRRAW"}

JPEG_EXTENSIONS = {".jpg", ".jpeg"}
RAW_EXTENSIONS = {".tif", ".tiff", ".psd"}
MIN_JPEG_BYTES = 5 * 1024 * 1024  # 5MB

LOG_DIR = Path.home() / "Desktop" / "Exodus-Metadata-Agent" / "logs"
CSV_COLUMNS = [
    "original_path",
    "destination_path",
    "file_type",
    "size_mb",
    "status",
    "error_message",
]


def find_files(drive: Path) -> tuple[list[Path], list[Path]]:
    """Return (jpeg_files_over_5mb, raw_files) skipping output folders."""
    jpegs = []
    raws = []

    for p in sorted(drive.rglob("*")):
        # Skip the output folders entirely
        if any(part in SKIP_FOLDERS for part in p.parts):
            continue
        if not p.is_file():
            continue

        ext = p.suffix.lower()
        if ext in JPEG_EXTENSIONS and p.stat().st_size >= MIN_JPEG_BYTES:
            jpegs.append(p)
        elif ext in RAW_EXTENSIONS:
            raws.append(p)

    return jpegs, raws


def destination_path(source: Path, drive: Path, output_folder: Path) -> Path:
    """Build the destination path preserving folder structure relative to drive root."""
    relative = source.relative_to(drive)
    return output_folder / relative


def copy_file(source: Path, dest: Path) -> str:
    """Copy source to dest, creating parent folders as needed. Returns status."""
    if dest.exists():
        return "already_exists"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return "copied"


def size_mb(path: Path) -> str:
    return f"{path.stat().st_size / (1024 * 1024):.1f}"


def main():
    if not DRIVE.exists():
        print("ERROR: Rick's Lacie is not connected. Please plug in the drive and try again.")
        sys.exit(1)

    print("=" * 50)
    print("  Exodus Photography File Scanner")
    print("=" * 50)
    print(f"\nScanning {DRIVE} ...")
    print("This may take a moment on a large drive.\n")

    jpegs, raws = find_files(DRIVE)

    print(f"Found {len(jpegs)} JPEGs over 5MB")
    print(f"Found {len(raws)} TIFF/PSD files")
    print()

    if not jpegs and not raws:
        print("Nothing to copy.")
        return

    total = len(jpegs) + len(raws)
    confirm = input(f"Copy {total} files to HRJPEGs and HRRAW on Rick's Lacie? (y/n) ")
    if confirm.strip().lower() != "y":
        print("Aborted.")
        return

    print()
    HRJPEGS.mkdir(exist_ok=True)
    HRRAW.mkdir(exist_ok=True)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"file_scanner_log_{date.today().strftime('%Y%m%d')}.csv"
    write_header = not log_path.exists() or log_path.stat().st_size == 0

    copied = 0
    skipped = 0
    errors = 0

    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()

        all_files = [(p, "JPEG", HRJPEGS) for p in jpegs] + \
                    [(p, "RAW/PSD", HRRAW) for p in raws]

        for i, (source, file_type, output_folder) in enumerate(all_files, start=1):
            dest = destination_path(source, DRIVE, output_folder)
            print(f"[{i}/{total}] {file_type}: {source.name}")

            row = {
                "original_path": str(source),
                "destination_path": str(dest),
                "file_type": file_type,
                "size_mb": size_mb(source),
                "status": "",
                "error_message": "",
            }

            try:
                status = copy_file(source, dest)
                row["status"] = status
                if status == "copied":
                    copied += 1
                else:
                    skipped += 1
                    print(f"  Skipped — already exists")
            except Exception as exc:
                row["status"] = "error"
                row["error_message"] = str(exc)
                errors += 1
                print(f"  ERROR: {exc}")

            writer.writerow(row)

    print(f"\nDone. {copied} copied, {skipped} already existed, {errors} errors.")
    print(f"Log saved to {log_path}")


if __name__ == "__main__":
    main()
