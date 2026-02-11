#!/bin/bash
# Stash Bot Process Manager
# Keeps the bot running forever

cd /home/ubuntu/.openclaw/workspace/stash_bot
source venv/bin/activate

while true; do
    echo "$(date): Starting bot..." >> bot.log
    python bot.py 2>&1 | tee -a bot.log
    echo "$(date): Bot crashed/exited with code $?. Restarting in 3 seconds..." >> bot.log
    sleep 3
done
