# Exodus Metadata Agent — Quick Reference

## Every Time You Run It

1. Plug in Rick's Lacie
2. Open Terminal
3. Run these commands:

```bash
# Step 1 — Navigate to the script
cd ~/Documents/exodus-metadata-agent/exodus-metadata-agent

# Step 2 — Test run (first 5 images, safe mode — do this first on any new folder)
python exodus_metadata_agent.py --path "/Volumes/Rick's Lacie/Botanicals" --test --keep-backups

# Step 3 — Full run once you're happy with the test results
python exodus_metadata_agent.py --path "/Volumes/Rick's Lacie/Botanicals"
```

Change `Botanicals` to whatever folder you want to process.

---

## First-Time Setup (Do Once on Your Mac)

```bash
# 1. Install Homebrew (Mac package manager)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/homebrew/install/HEAD/install.sh)"

# 2. Install ExifTool
brew install exiftool
exiftool -ver   # should show a version number like 13.x

# 3. Download the script to your Mac
cd ~/Documents
git clone https://github.com/exophoto/my-site exodus-metadata-agent
cd exodus-metadata-agent/exodus-metadata-agent

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Add your API key
cp .env.example .env
open -e .env
# Replace "your_key_here" with your Anthropic API key, then save and close
```

---

## Verify Metadata Was Written (Spot-Check a File)

```bash
exiftool -IPTC:all -XMP:all "/Volumes/Rick's Lacie/Botanicals/yourfile.jpg"
```

---

## Folder Path Examples

| Folder on Rick's Lacie | Command path to use |
|---|---|
| Botanicals | `"/Volumes/Rick's Lacie/Botanicals"` |
| Oklahoma Landscapes | `"/Volumes/Rick's Lacie/Oklahoma Landscapes"` |
| Food Art | `"/Volumes/Rick's Lacie/Food Art"` |
| Entire drive | `"/Volumes/Rick's Lacie"` |

---

## If Something Goes Wrong

- **"exiftool: command not found"** — run `brew install exiftool`
- **"No module named anthropic"** — run `pip install -r requirements.txt`
- **"Invalid API key"** — open `.env` and check your Anthropic API key
- **Agent stops mid-run** — just run it again; it skips files already marked success in today's log

---

## Key Facts to Remember

- Your **photos are never moved or copied** — the agent writes metadata into files right where they sit on Rick's Lacie
- The **original image pixel data is never touched** — only the metadata header changes
- A **CSV log** of every processed file is saved to the `logs/` folder inside the script directory
- If a run is interrupted, **re-running picks up where it left off** automatically
