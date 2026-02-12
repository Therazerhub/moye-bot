#!/bin/bash
# Setup script for weekly performer database updates
# Run this to add the update job to crontab

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPDATE_SCRIPT="$SCRIPT_DIR/update_performer_db.py"
LOG_FILE="$SCRIPT_DIR/logs/performer_db_update.log"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Check if update script exists
if [ ! -f "$UPDATE_SCRIPT" ]; then
    echo "❌ Error: update_performer_db.py not found at $UPDATE_SCRIPT"
    exit 1
fi

# Make update script executable
chmod +x "$UPDATE_SCRIPT"

echo "Setting up weekly performer database update..."
echo "  Script: $UPDATE_SCRIPT"
echo "  Log: $LOG_FILE"
echo ""

# Create cron job (every Sunday at 3 AM)
CRON_JOB="0 3 * * 0 cd $SCRIPT_DIR && /usr/bin/python3 $UPDATE_SCRIPT >> $LOG_FILE 2>&1"

# Check if already in crontab
if crontab -l 2>/dev/null | grep -q "$UPDATE_SCRIPT"; then
    echo "⚠️  Cron job already exists."
    echo ""
    echo "Current crontab entry:"
    crontab -l | grep "$UPDATE_SCRIPT"
    echo ""
    read -p "Replace it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old entry and add new one
        crontab -l 2>/dev/null | grep -v "$UPDATE_SCRIPT" | crontab -
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        echo "✅ Cron job updated!"
    else
        echo "Cancelled."
        exit 0
    fi
else
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added!"
fi

echo ""
echo "Schedule: Every Sunday at 3:00 AM"
echo ""
echo "To verify:"
echo "  crontab -l"
echo ""
echo "To run manually now:"
echo "  python3 $UPDATE_SCRIPT"
