# Exodus Photography — Metadata Agent

Scans a folder of JPEGs, generates SEO metadata via the Claude vision API, and embeds
it directly into each file's IPTC/XMP headers (so it travels with the file regardless
of where it's uploaded). Logs results to CSV for reference.

## Setup

```bash
brew install exiftool
exiftool -ver   # verify install

pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

## Usage

```bash
# Test run — first 5 images only, keep backup files
python exodus_metadata_agent.py --path "/Volumes/ExodusDrive/Botanicals" --test --keep-backups

# Full run on a category folder
python exodus_metadata_agent.py --path "/Volumes/ExodusDrive/Botanicals"

# Full run keeping backup originals
python exodus_metadata_agent.py --path "/Volumes/ExodusDrive" --keep-backups

# Verify metadata was written correctly on one file
exiftool -IPTC:all -XMP:all "/Volumes/ExodusDrive/Botanicals/DSC_0042.jpg"
```

Resuming: if today's CSV log (`logs/exodus_metadata_log_YYYYMMDD.csv`) already has a
file marked `success`, it's skipped on the next run.
