# 🍑 Lilly's Stash Bot

A Telegram bot for managing your video collection with 7,911+ videos. Features random video selection, multi-part support, StashDB/FansDB integration, and more!

## Features

- 🎲 **Random Video** — Pick a random video from your collection
- 📁 **Multi-Part Support** — Automatically detects and sends all parts of split videos
- 🔍 **Search** — Find videos by title, performer, or tags
- ⭐ **Favorites** — Save your best videos
- 📊 **Stats** — View collection statistics
- 🏷️ **Auto-Caption** — Formats video captions with performer and title
- 📥 **Bulk Import** — Import thousands of videos from Telegram channels

## Screenshots

```
🎲 Surprise Pick 💦

📌 Performer Name - Scene Title
⏱ 45:16 | 👁 1
[🎲 Another] [⭐ Save]
[🔙 Menu]
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/THERAZERHUB/stash-bot.git
cd stash-bot
```

### 2. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

### 4. Required Credentials

#### From @BotFather (Telegram)
- **Bot Token**: Message [@BotFather](https://t.me/BotFather), create new bot

#### From my.telegram.org
- **API ID**: Create app at https://my.telegram.org/apps
- **API Hash**: Same as above

#### Optional: StashDB / FansDB (for auto-captions)
- **StashDB API Key**: Get from https://stashdb.org/settings
- **FansDB API Key**: Get from https://fansdb.cc/settings

### 5. Run the Bot

```bash
python bot.py
```

The bot will start polling for messages.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ Yes | Telegram bot token from @BotFather |
| `ADMIN_ID` | ✅ Yes | Your Telegram user ID |
| `TELEGRAM_API_ID` | ✅ Yes | From my.telegram.org |
| `TELEGRAM_API_HASH` | ✅ Yes | From my.telegram.org |
| `STASHDB_API_KEY` | ❌ No | For scene metadata lookup |
| `STASHDB_GRAPHQL_URL` | ❌ No | https://stashdb.org/graphql |
| `FANSDB_API_KEY` | ❌ No | Backup API for metadata |
| `FANSDB_GRAPHQL_URL` | ❌ No | https://fansdb.cc/graphql |

## Usage

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/random` | Get random video |
| `/search <term>` | Search collection |
| `/stats` | View statistics |

### Bulk Import

Import videos from a Telegram channel:

```bash
python bulk_import_user.py -1001234567890 +919876543210
```

1. Replace with your channel ID and phone number
2. Enter the login code sent to your phone
3. The script will scan and save all videos

### Channel Auto-Caption

Forward videos to your channel and the bot will:
1. Detect the video
2. Extract filename
3. Format caption: `🔥🎬 Performer - Title ✨`
4. Add hashtags from StashDB/FansDB (if APIs configured)

## Database Schema

SQLite database (`stash.db`) with tables:

### videos
- `id` - Primary key
- `file_id` - Telegram file reference
- `title` - Video title
- `tags` - Comma-separated tags
- `category` - Category
- `duration` - Duration in seconds
- `view_count` - Times viewed
- `source_channel` - Origin channel

### favorites
- `id` - Primary key
- `video_id` - Reference to videos table

## Multi-Part Video Logic

Videos with `.part001`, `.part002`, etc. in filename are automatically detected:

1. Bot finds all parts matching the base name
2. Sorts by part number
3. Sends Part 1 with full caption and buttons
4. Sends remaining parts with simple captions

## Troubleshooting

### Bot not responding
- Check bot token is correct
- Ensure you're using `/start` command (not old buttons)
- Check logs: `tail -f bot.log`

### Duplicate videos being sent
- Make sure only ONE bot instance is running
- Check: `pgrep -f "bot.py"` should return 1 PID

### API not working (StashDB/FansDB)
- Keys may be expired, regenerate them
- FansDB is more reliable (unrestricted)
- Bot falls back to filename parsing if APIs fail

## File Structure

```
stash_bot/
├── bot.py                    # Main bot
├── stashdb_integration.py    # StashDB/FansDB API
├── bulk_import_user.py       # Bulk import script
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
├── .env                     # Your credentials (not in git)
├── stash.db                 # SQLite database
├── README.md                # This file
└── bot.log                  # Log file
```

## Credits

Made with 💕 by Lilly for Razer

Powered by:
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Telethon](https://github.com/LonamiWebs/Telethon)
- [StashDB](https://stashdb.org)
- [FansDB](https://fansdb.cc)

## License

Private use only. Not for redistribution.
