#!/bin/bash
# Exodus Photography Re-Embed Title — Double-click to run

clear
echo "========================================"
echo "  Exodus Photography — Re-Embed Title"
echo "========================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"

echo "Available log files:"
ls "$LOG_DIR"/*.csv 2>/dev/null | xargs -I{} basename {}
echo ""
read -p "Type the log filename (e.g. exodus_metadata_log_20260729.csv): " LOGFILE
echo ""

echo "Options:"
echo "  1. Embed title only"
echo "  2. Embed title AND rename files to match title"
echo ""
read -p "Type 1 or 2: " CHOICE
echo ""

if [ "$CHOICE" = "2" ]; then
    python3 "$SCRIPT_DIR/re-embed-title.py" --csv "$LOG_DIR/$LOGFILE" --rename
else
    python3 "$SCRIPT_DIR/re-embed-title.py" --csv "$LOG_DIR/$LOGFILE"
fi

echo ""
read -p "Press Return to close..."
