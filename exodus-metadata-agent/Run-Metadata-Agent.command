#!/bin/bash
# Exodus Photography Metadata Agent — Double-click to run

clear
echo "========================================"
echo "  Exodus Photography Metadata Agent"
echo "========================================"
echo ""

# Check Rick's Lacie is plugged in
if [ ! -d "/Volumes/Ricks Lacie" ]; then
    echo "ERROR: Rick's Lacie is not plugged in or not found."
    echo "Please connect the drive and try again."
    echo ""
    read -p "Press Return to close..."
    exit 1
fi

echo "Rick's Lacie is connected."
echo ""
echo "Folders available on Rick's Lacie:"
ls "/Volumes/Ricks Lacie"
echo ""
read -p "Type the folder name to process: " FOLDER
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

python3 "$SCRIPT_DIR/exodus_metadata_agent.py" --path "/Volumes/Ricks Lacie/$FOLDER"

echo ""
read -p "Press Return to close..."
