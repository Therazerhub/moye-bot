"""
Bulk Import Script for Stash Bot
Uses Telethon to efficiently scrape videos from channels
"""

import os
import sys
import sqlite3
import asyncio
import re
from telethon import TelegramClient
from telethon.tl.types import Channel
from dotenv import load_dotenv

load_dotenv()

# Telethon credentials
API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '')
BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_PATH = 'stash.db'

# Domain to category mapping (same as bot.py)
DOMAIN_CATEGORIES = {
    'brazzers': 'Brazzers',
    'brazzer': 'Brazzers',
    'pornhub': 'Pornhub',
    'ph': 'Pornhub',
    'xvideos': 'XVideos',
    'xnxx': 'XNXX',
    'youporn': 'YouPorn',
    'redtube': 'RedTube',
    'spankbang': 'SpankBang',
    'chaturbate': 'Chaturbate',
    'onlyfans': 'OnlyFans',
    'manyvids': 'ManyVids',
    'clips4sale': 'Clips4Sale',
    'realitykings': 'Reality Kings',
    'bangbros': 'BangBros',
    'naughtyamerica': 'Naughty America',
    'digitalplayground': 'Digital Playground',
    'mofos': 'Mofos',
    'teamskeet': 'TeamSkeet',
    'fakehub': 'FakeHub',
    'vixen': 'Vixen',
    'tushy': 'Tushy',
    'blacked': 'Blacked',
    'blackedraw': 'Blacked Raw',
    'deeper': 'Deeper',
    'julesjordan': 'Jules Jordan',
    'evilangel': 'Evil Angel',
    'milf': 'MILF',
    'anal': 'Anal',
    'lesbian': 'Lesbian',
    'threesome': 'Threesome',
    'teen': 'Teen',
    'amateur': 'Amateur',
    'homemade': 'Homemade',
    'webcam': 'Webcam',
    'casting': 'Casting',
    'massage': 'Massage',
}

def extract_category_from_title(title):
    """Extract category from video title based on domains/keywords"""
    if not title:
        return None
    
    title_lower = title.lower()
    
    # Check for domain patterns
    patterns = [
        r'\[([^\]]+)\]',
        r'\(([^\)]+)\)',
        r'www\.([a-z0-9]+)',
        r'([a-z0-9]+)\.com',
        r'([a-z0-9]+)\.net',
        r'([a-z0-9]+)\.org',
        r'([a-z0-9]+)\.tv',
        r'([a-z0-9]+)\.xxx',
        r'([a-z0-9]+)_',
        r'_([a-z0-9]+)',
        r'-([a-z0-9]+)-',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, title_lower)
        for match in matches:
            clean_match = match.strip().replace('.', '').replace('-', '').replace('_', '')
            if clean_match in DOMAIN_CATEGORIES:
                return DOMAIN_CATEGORIES[clean_match]
    
    # Direct keyword matching
    for keyword, category in DOMAIN_CATEGORIES.items():
        if keyword in title_lower:
            return category
    
    return None

async def import_from_channel(channel_id_str):
    """Import videos from channel using the bot"""
    
    if not API_ID or not API_HASH:
        print("❌ ERROR: Need TELEGRAM_API_ID and TELEGRAM_API_HASH")
        return
    
    # Parse channel ID
    try:
        channel_id = int(channel_id_str)
    except:
        print(f"❌ Invalid channel ID: {channel_id_str}")
        return
    
    # Connect using bot token
    client = TelegramClient('stash_import_session', API_ID, API_HASH)
    
    try:
        print("🍑💦 Lilly's Bulk Import Tool\n")
        await client.start(bot_token=BOT_TOKEN)
        
        me = await client.get_me()
        print(f"✅ Connected as @{me.username}\n")
        
        # Connect to DB
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Try to get channel using the integer ID directly
        try:
            # For private channels with -100 prefix, construct the peer
            from telethon.tl.types import PeerChannel
            
            # Remove the -100 prefix if present for the raw ID
            raw_id = channel_id
            if str(channel_id).startswith('-100'):
                raw_id = int(str(channel_id)[4:])
            
            peer = PeerChannel(raw_id)
            channel = await client.get_entity(peer)
            
        except Exception as e:
            print(f"❌ Can't access channel: {e}")
            print("\nMake sure:")
            print("1. Bot is admin in the channel")
            print("2. Channel ID is correct")
            print("3. The -100 prefix is included if present")
            return
        
        print(f"📺 Channel: {channel.title}")
        print(f"🆔 ID: {channel_id}")
        print(f"🚀 Starting import...\n")
        
        saved = 0
        skipped = 0
        total_checked = 0
        videos_found = 0
        
        # Iterate through ALL messages
        async for message in client.iter_messages(channel, limit=None):
            total_checked += 1
            
            # Progress every 100 messages
            if total_checked % 100 == 0:
                print(f"📊 Checked: {total_checked} | Videos: {videos_found} | Saved: {saved} | Skipped: {skipped}")
            
            # Check for video
            if message.video or (message.document and message.document.mime_type and message.document.mime_type.startswith('video/')):
                videos_found += 1
                
                try:
                    # Get video details
                    doc = message.video or message.document
                    
                    # Get duration
                    duration = 0
                    if doc.attributes:
                        for attr in doc.attributes:
                            if hasattr(attr, 'duration'):
                                duration = attr.duration
                                break
                    
                    # Get title from filename or caption
                    title = None
                    if doc.attributes:
                        for attr in doc.attributes:
                            if hasattr(attr, 'file_name') and attr.file_name:
                                import os
                                title = os.path.splitext(attr.file_name)[0].replace('_', ' ').replace('-', ' ')
                                break
                    
                    if not title and message.message:
                        title = message.message[:100]
                    
                    if not title:
                        title = f"Video {message.id}"
                    
                    # Extract category from title
                    category = extract_category_from_title(title)
                    
                    # We need to forward to the bot to get a usable file_id
                    # Forward the message to the bot itself
                    try:
                        from telethon.tl.types import InputPeerSelf
                        
                        # Forward to ourselves (the bot)
                        forwarded = await client.forward_messages('me', message)
                        
                        if forwarded and (forwarded.video or forwarded.document):
                            # The file_id format for bot API can't be directly obtained from Telethon
                            # But we can store a reference that lets us resend
                            # Format: telethon_ref:channel_id:message_id
                            file_ref = f"telethon_ref:{channel_id}:{message.id}"
                            
                            # Try to save
                            try:
                                c.execute("""
                                    INSERT INTO videos (file_id, title, duration, category, source_channel)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (file_ref, title, duration, category, channel.title))
                                conn.commit()
                                saved += 1
                                cat_info = f" [{category}]" if category else ""
                                print(f"✅ Saved: {title[:60]}{cat_info}")
                            except sqlite3.IntegrityError:
                                skipped += 1
                            except Exception as e:
                                print(f"⚠️ DB error: {e}")
                            
                            # Delete forwarded message to keep clean
                            await forwarded.delete()
                            
                            # Small delay to not flood
                            await asyncio.sleep(0.2)
                            
                    except Exception as e:
                        print(f"⚠️ Forward error: {e}")
                        continue
                        
                except Exception as e:
                    print(f"⚠️ Error processing message {message.id}: {e}")
                    continue
        
        conn.close()
        
        print(f"\n" + "="*50)
        print(f"✅ IMPORT COMPLETE!")
        print(f"="*50)
        print(f"📊 Messages checked: {total_checked}")
        print(f"🎥 Videos found: {videos_found}")
        print(f"✅ New saved: {saved}")
        print(f"⏭ Duplicates skipped: {skipped}")
        print(f"="*50)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python bulk_import.py -1001234567890")
        print("")
        print("Note: Use the full channel ID with -100 prefix")
        sys.exit(1)
    
    channel_id = sys.argv[1]
    
    asyncio.run(import_from_channel(channel_id))
