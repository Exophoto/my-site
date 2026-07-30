#!/bin/bash
# Exodus Photography File Scanner — Double-click to run

clear
echo "========================================"
echo "  Exodus Photography File Scanner"
echo "========================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "/Volumes/Ricks Lacie" ]; then
    echo "ERROR: Rick's Lacie is not connected."
    echo "Please plug in the drive and double-click this again."
    echo ""
    read -p "Press Return to close..."
    exit 1
fi

python3 "$SCRIPT_DIR/file_scanner.py"

echo ""
read -p "Press Return to close..."
