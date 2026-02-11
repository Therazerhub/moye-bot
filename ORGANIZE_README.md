# Channel Organizer - README

## What It Does
Automatically sorts your video collection into 3 categories based on StashDB match quality:

1. **CLEAN (90%+ match)** → Properly renamed with performer, title, studio
2. **REVIEW (70-89% match)** → Good match but needs human verification
3. **UNSORTED (<70% match)** → Manual review needed

## Setup Steps

### 1. Create 3 New Telegram Channels
- Create a new channel for CLEAN videos
- Create a new channel for REVIEW videos  
- Create a new channel for UNSORTED videos

### 2. Add Bot to Channels
- Add your bot as admin to all 3 channels
- Send one test message in each channel

### 3. Get Channel IDs
Run this to find your channel IDs:
```bash
cd /home/ubuntu/.openclaw/workspace/stash_bot
source venv/bin/activate
python3 -c "
from telethon import TelegramClient
import asyncio

async def main():
    client = TelegramClient('test_session', API_ID, API_HASH)
    await client.start()
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            print(f'{dialog.title}: {dialog.id}')
    await client.disconnect()

asyncio.run(main())
"
```

### 4. Edit organize_channel.py
Update these lines with your channel IDs:
```python
CLEAN_CHANNEL_ID = -1001234567890     # Your clean channel
REVIEW_CHANNEL_ID = -1001234567891    # Your review channel  
UNSORTED_CHANNEL_ID = -1001234567892  # Your unsorted channel
```

### 5. Run the Organizer
```bash
cd /home/ubuntu/.openclaw/workspace/stash_bot
source venv/bin/activate
python3 organize_channel.py
```

## How It Works

1. Reads each video from your source channel
2. Queries StashDB for metadata
3. Calculates match score (performer + title similarity)
4. Forwards to appropriate channel with new filename
5. Saves progress to `organize.db`

## Match Score Formula
- Title match: 60% weight
- Performer match: 40% weight
- Combined score decides category

## Example Results

**Input:** `Jia Lissa [Blacked.com] Go Ahead Have F.part001`

**90%+ Match (CLEAN):**
- New name: `Blacked - Jia Lissa - Go Ahead Have Fun.mp4`
- Forwards to clean channel with full metadata

**70-89% Match (REVIEW):**
- New name: `Blacked - Jia Lissa - Go Ahead Have Fun.mp4`
- Forwards to review channel (verify before keeping)

**<70% Match (UNSORTED):**
- Keeps original name
- Forwards to unsorted channel for manual fixing

## Resume Capability
The script tracks progress in `organize.db`. If interrupted, run again - it will skip already processed videos.

## Safety
- **NEVER** deletes original videos
- Only forwards/copies messages
- You can run it multiple times safely
