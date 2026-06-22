"""ExifTool wrapper for embedding IPTC + XMP metadata into JPEG files."""

import shutil
import subprocess
from pathlib import Path

CREATOR = "Rick, Exodus Photography"
COPYRIGHT_NOTICE = "© 2026 Exodus Photography. All Rights Reserved."
USAGE_TERMS = "Contact rick@exodusphotography.com for licensing"
CREATOR_TOOL = "Exodus Photography Metadata Agent"


def check_exiftool_installed() -> str:
    """Return the installed exiftool version, or raise RuntimeError if missing."""
    path = shutil.which("exiftool")
    if not path:
        raise RuntimeError(
            "ExifTool not found on PATH. Install it first:\n"
            "  brew install exiftool\n"
            "Then verify with: exiftool -ver"
        )
    result = subprocess.run(["exiftool", "-ver"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def embed_metadata(filepath: Path, metadata: dict, keep_backup: bool = False) -> None:
    """Write IPTC + XMP metadata into a JPEG file in place using exiftool.

    metadata keys: title, description, keywords (list[str]), alt_text, category
    """
    keywords = metadata["keywords"]

    args = [
        "exiftool",
        "-overwrite_original" if not keep_backup else "-P",
        f"-IPTC:Headline={metadata['title']}",
        f"-XMP:Title={metadata['title']}",
        f"-IPTC:Caption-Abstract={metadata['description']}",
        f"-XMP:Description={metadata['description']}",
        f"-XMP-iptcExt:AltTextAccessibility={metadata['alt_text']}",
        f"-IPTC:By-line={CREATOR}",
        f"-XMP:Creator={CREATOR}",
        f"-IPTC:CopyrightNotice={COPYRIGHT_NOTICE}",
        f"-XMP:Rights={COPYRIGHT_NOTICE}",
        f"-XMP:UsageTerms={USAGE_TERMS}",
        f"-XMP:CreatorTool={CREATOR_TOOL}",
        "-IPTC:Keywords=",
        "-XMP:Subject=",
    ]

    for kw in keywords:
        args.append(f"-IPTC:Keywords+={kw}")
        args.append(f"-XMP:Subject+={kw}")

    args.append(f"-XMP:Subject+={metadata['category']}")

    args.append(str(filepath))

    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "exiftool failed with no error message")

    if not keep_backup:
        backup = filepath.with_name(filepath.name + "_original")
        if backup.exists():
            backup.unlink()
