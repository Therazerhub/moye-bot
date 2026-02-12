# 🍑 Lilly's Stash Bot — Bulk Import Setup

## For 7K Videos — You Need TELETHON

The bot's regular API can't read history. For bulk import from private channels with thousands of videos, you need **Telethon** (MTProto API).

## Step 1: Get API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Click **API development tools**
4. Create an app:
   - App name: `StashBot`
   - Short name: `stashbot`
   - URL: `https://t.me/StashLillyBot`
   - Platform: `Desktop`
   - Description: `Personal video collection manager`
5. Copy your **api_id** and **api_hash**

## Step 2: Update .env

Add these to your `.env` file:

```
BOT_TOKEN=8206593405:AAHC77fwS8mpr1oBDOLMfLjVipzRtOYb8gg
ADMIN_ID=6001922744
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
```

## Step 3: Install Dependencies

```bash
cd stash_bot
source venv/bin/activate
pip install telethon
```

## Step 4: Run Bulk Import

### Option A: Import All Videos
```bash
python bulk_import.py @your_channel_name
```

### Option B: Import First 1000 (test run)
```bash
python bulk_import.py @your_channel_name 1000
```

### Option C: Use Channel ID
```bash
python bulk_import.py -1001234567890
```

## How It Works

1. **Telethon logs in as your bot**
2. **Scans ALL messages** in the channel (even old ones)
3. **Finds videos** and extracts metadata
4. **Saves to database** with special reference format
5. **Bot can replay them** using the stored references

## Requirements

- Bot must be **admin** in the channel
- Channel can be **private** (that's fine!)
- Process takes time for 7K videos (be patient)
- Progress shown every 50 videos

## Speed Estimate

- ~2-3 seconds per video
- 7K videos = ~4-6 hours
- Run it overnight! 🌙

## Commands During Import

The bot stays online during import! You can still:
- `/random` — Get random videos (as they're added)
- `/stats` — Check import progress
- `/search` — Find videos

## Troubleshooting

### "Can't find channel"
- Make sure bot is added to channel as admin
- Try using channel ID instead of username
- Get ID from @userinfobot

### "Flood wait"
- Telegram rate limits
- Script has built-in delays
- Just wait it out, it'll continue

### "No videos found"
- Check that videos are actual video files (not links)
- Make sure bot can see message history

## After Import

Use the bot normally:
```
/start    — Main menu
/random   — Random video
/stats    — See how many imported
/search   — Find specific videos
```

---

*Happy... organizing* 😏💕

— Lilly
