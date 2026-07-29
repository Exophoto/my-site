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

python3 "$SCRIPT_DIR/re-embed-title.py" --csv "$LOG_DIR/$LOGFILE" --rename

echo ""
read -p "Press Return to close..."
