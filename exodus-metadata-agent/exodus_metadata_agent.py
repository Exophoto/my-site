#!/usr/bin/env python3
"""Exodus Photography Metadata Agent.

Scans a folder for JPEG files, generates SEO metadata via the Claude vision API,
embeds it directly into each file's IPTC/XMP headers, and logs the results to CSV.
"""

import argparse
import base64
import csv
import io
import json
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

import embedder
from prompts import VISION_SYSTEM_PROMPT

MIN_FILE_SIZE_BYTES = 50 * 1024
JPEG_EXTENSIONS = {".jpg", ".jpeg"}
LOG_DIR = Path(__file__).parent / "logs"
CSV_COLUMNS = [
    "filename",
    "filepath",
    "title_1",
    "title_2",
    "title_3",
    "title_embedded",
    "description",
    "keywords",
    "alt_text",
    "category",
    "embed_status",
    "error_message",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Exodus Photography Metadata Agent")
    parser.add_argument("--path", required=True, help="Folder to scan for JPEG files")
    parser.add_argument("--test", action="store_true", help="Process only the first 5 images")
    parser.add_argument(
        "--keep-backups",
        action="store_true",
        help="Keep .jpg_original backup files created by exiftool",
    )
    return parser.parse_args()


def find_jpegs(folder: Path) -> list[Path]:
    files = [
        p
        for p in sorted(folder.rglob("*"))
        if p.is_file()
        and p.suffix.lower() in JPEG_EXTENSIONS
        and p.stat().st_size >= MIN_FILE_SIZE_BYTES
    ]
    return files


def todays_log_path() -> Path:
    LOG_DIR.mkdir(exist_ok=True)
    return LOG_DIR / f"exodus_metadata_log_{date.today().strftime('%Y%m%d')}.csv"


def load_already_processed(log_path: Path) -> set[str]:
    if not log_path.exists():
        return set()
    processed = set()
    with open(log_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("embed_status") == "success":
                processed.add(row["filepath"])
    return processed


def append_log_row(log_path: Path, row: dict, write_header: bool) -> None:
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


MAX_API_BYTES = 9 * 1024 * 1024  # 9MB — safely under Claude's 10MB limit


def prepare_image_bytes(filepath: Path) -> bytes:
    """Return image bytes ready for the API, resizing in memory if over the limit."""
    raw = filepath.read_bytes()
    if len(raw) <= MAX_API_BYTES:
        return raw

    img = Image.open(filepath)
    quality = 85
    scale = 0.9
    while True:
        buf = io.BytesIO()
        width = int(img.width * scale)
        height = int(img.height * scale)
        resized = img.resize((width, height), Image.LANCZOS)
        resized.save(buf, format="JPEG", quality=quality)
        data = buf.getvalue()
        if len(data) <= MAX_API_BYTES:
            return data
        scale *= 0.85
        quality = max(quality - 5, 60)


def analyze_image(client, filepath: Path) -> dict:
    image_bytes = prepare_image_bytes(filepath)
    media_type = "image/jpeg"
    b64_data = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1536,
        system=VISION_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Analyze this photograph and return the metadata JSON object.",
                    },
                ],
            }
        ],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def process_file(client, filepath: Path, keep_backups: bool) -> dict:
    row = {col: "" for col in CSV_COLUMNS}
    row["filename"] = filepath.name
    row["filepath"] = str(filepath)

    try:
        metadata = analyze_image(client, filepath)
        row["title_1"] = metadata.get("title_1", "")
        row["title_2"] = metadata.get("title_2", "")
        row["title_3"] = metadata.get("title_3", "")
        row["description"] = metadata.get("description", "")
        row["keywords"] = ", ".join(metadata.get("keywords", []))
        row["alt_text"] = metadata.get("alt_text", "")
        row["category"] = metadata.get("category", "")

        # title_1 is embedded into the file; review CSV to pick your preferred title
        metadata["title"] = metadata.get("title_1", "")
        row["title_embedded"] = metadata["title"]

        embedder.embed_metadata(filepath, metadata, keep_backup=keep_backups)

        row["embed_status"] = "success"
    except Exception as exc:
        row["embed_status"] = "error"
        row["error_message"] = str(exc)

    return row


def main():
    load_dotenv()
    args = parse_args()

    try:
        version = embedder.check_exiftool_installed()
        print(f"ExifTool detected (v{version})")
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    folder = Path(args.path).expanduser().resolve()
    if not folder.is_dir():
        print(f"Error: {folder} is not a valid directory")
        sys.exit(1)

    files = find_jpegs(folder)
    if not files:
        print("No JPEG files found.")
        return

    log_path = todays_log_path()
    already_processed = load_already_processed(log_path)
    write_header = not log_path.exists() or log_path.stat().st_size == 0

    pending = [f for f in files if str(f) not in already_processed]
    if not pending:
        print("All files already processed in today's log.")
        return

    if args.test:
        pending = pending[:5]

    print(f"Found {len(files)} JPEG files. {len(pending)} pending processing.")
    if not args.test:
        confirm = input("Proceed with metadata embedding? (y/n) ")
        if confirm.strip().lower() != "y":
            print("Aborted.")
            return

    import anthropic

    client = anthropic.Anthropic()

    for i, filepath in enumerate(pending, start=1):
        print(f"[{i}/{len(pending)}] Processing: {filepath.name}")
        row = process_file(client, filepath, keep_backups=args.keep_backups)
        append_log_row(log_path, row, write_header)
        write_header = False
        if row["embed_status"] == "error":
            print(f"  Error: {row['error_message']}")

    print(f"Done. Log written to {log_path}")


if __name__ == "__main__":
    main()
