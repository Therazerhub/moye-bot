"""
Bulk Import Script for Stash Bot - USER ACCOUNT VERSION
Uses Telethon with a user account (not bot) to read channel history
"""

import os
import sys
import sqlite3
import asyncio
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from dotenv import load_dotenv

load_dotenv()

# Telethon credentials
API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '')
DB_PATH = 'stash.db'

# Session name for user account
SESSION_NAME = 'stash_user_session'

async def import_with_user_account(channel_id_str, phone_number):
    """
    Import videos using a user account (can read history!)
    
    First run will ask for login code
    """
    
    if not API_ID or not API_HASH:
        print("❌ ERROR: Need TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")
        return
    
    # Parse channel ID
    try:
        channel_id = int(channel_id_str)
    except:
        print(f"❌ Invalid channel ID: {channel_id_str}")
        return
    
    # Connect using USER account (not bot!)
    # This allows reading history
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        print("🍑💦 Lilly's Bulk Import Tool (User Account)\n")
        
        # Start with phone number - will ask for code first time
        await client.start(phone=phone_number)
        
        me = await client.get_me()
        print(f"✅ Logged in as: {me.first_name} (@{me.username or 'no_username'})\n")
        
        # Connect to DB
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get channel
        try:
            # Handle the -100 prefix
            raw_id = channel_id
            if str(channel_id).startswith('-100'):
                raw_id = int(str(channel_id)[4:])
            
            peer = PeerChannel(raw_id)
            channel = await client.get_entity(peer)
            
        except Exception as e:
            print(f"❌ Can't access channel: {e}")
            print("\nMake sure:")
            print("1. The secondary account JOINED the channel")
            print("2. Channel ID is correct")
            return
        
        print(f"📺 Channel: {channel.title}")
        print(f"🆔 ID: {channel_id}")
        print(f"🚀 Starting bulk import of ALL videos...\n")
        print("⚠️  This will take time. Don't close the terminal!\n")
        
        saved = 0
        skipped = 0
        total_checked = 0
        videos_found = 0
        last_saved_title = ""
        
        # Iterate through ALL messages (no limit!)
        async for message in client.iter_messages(channel, limit=None):
            total_checked += 1
            
            # Progress report every 500 messages
            if total_checked % 500 == 0:
                print(f"📊 Progress: Checked {total_checked} messages | Videos: {videos_found} | Saved: {saved} | Skipped: {skipped}")
                if last_saved_title:
                    print(f"   Last saved: {last_saved_title[:50]}...")
                print()
            
            # Check for video
            if message.video or (message.document and message.document.mime_type and message.document.mime_type.startswith('video/')):
                videos_found += 1
                
                try:
                    doc = message.video or message.document
                    
                    # Get duration
                    duration = 0
                    if doc.attributes:
                        for attr in doc.attributes:
                            if hasattr(attr, 'duration'):
                                duration = attr.duration
                                break
                    
                    # Get title
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
                        title = f"Video_{message.id}"
                    
                    # Store reference: user_account:channel_id:message_id
                    # The bot can later use this to request the file
                    file_ref = f"user_ref:{channel_id}:{message.id}"
                    
                    # Save to DB
                    try:
                        c.execute("""
                            INSERT INTO videos (file_id, title, duration, source_channel)
                            VALUES (?, ?, ?, ?)
                        """, (file_ref, title, duration, channel.title))
                        conn.commit()
                        saved += 1
                        last_saved_title = title
                        
                        # Print every 10 saves
                        if saved % 10 == 0:
                            print(f"✅ Saved ({saved}): {title[:60]}")
                            
                    except sqlite3.IntegrityError:
                        skipped += 1
                    except Exception as e:
                        print(f"⚠️ DB error: {e}")
                    
                    # Small delay to be nice to Telegram
                    await asyncio.sleep(0.1)
                        
                except Exception as e:
                    print(f"⚠️ Error with message {message.id}: {e}")
                    continue
        
        conn.close()
        
        print(f"\n" + "="*60)
        print(f"🎉 IMPORT COMPLETE!")
        print(f"="*60)
        print(f"📊 Total messages scanned: {total_checked:,}")
        print(f"🎥 Videos found: {videos_found:,}")
        print(f"✅ New videos saved: {saved:,}")
        print(f"⏭ Already had (skipped): {skipped:,}")
        print(f"="*60)
        print(f"\nYour stash is ready! 🍑💦")
        print(f"Use /random in the bot to test!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("\n👋 Logged out safely")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python bulk_import_user.py -1001234567890 +919876543210")
        print("")
        print("Arguments:")
        print("  1. Channel ID (with -100 prefix)")
        print("  2. Phone number of secondary account")
        print("")
        print("First run will ask for the login code sent to your phone")
        sys.exit(1)
    
    channel_id = sys.argv[1]
    phone = sys.argv[2]
    
    asyncio.run(import_with_user_account(channel_id, phone))
