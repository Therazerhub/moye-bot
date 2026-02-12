"""
Bulk video sender using Telethon for efficient queue-based sending
Handles large categories without overloading the bot
"""

import asyncio
import logging
from typing import List, Tuple
from telethon import TelegramClient
from telethon.tl.functions.messages import SendMediaRequest
from telethon.tl.types import InputMediaDocument, DocumentAttributeVideo

logger = logging.getLogger(__name__)

class BulkVideoSender:
    """Queue-based video sender that handles large batches efficiently"""
    
    def __init__(self, api_id: int, api_hash: str, session_name: str = 'bulk_sender'):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = None
        self._sending = False
        
    async def _get_client(self) -> TelegramClient:
        """Get or create Telethon client"""
        if self.client is None or not self.client.is_connected():
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.connect()
            if not await self.client.is_user_authorized():
                logger.error("Telethon client not authorized!")
                return None
        return self.client
    
    async def send_videos_batch(
        self, 
        chat_id: int, 
        videos: List[Tuple[int, str, str, int]],  # (video_id, file_id, title, duration)
        bot,
        progress_callback=None,
        batch_size: int = 20,
        delay_between: float = 0.5
    ) -> dict:
        """
        Send videos in batches with progress updates
        
        Args:
            chat_id: Target chat ID
            videos: List of (video_id, file_id, title, duration)
            bot: Bot instance for sending progress messages
            progress_callback: Optional callback for progress updates
            batch_size: How many videos per batch
            delay_between: Delay between videos (seconds)
            
        Returns:
            dict with sent_count, failed_count, total
        """
        if not videos:
            return {'sent': 0, 'failed': 0, 'total': 0}
        
        total = len(videos)
        sent_count = 0
        failed_count = 0
        current_batch = []
        
        # Send initial status
        status_msg = await bot.send_message(
            chat_id=chat_id,
            text=f"📤 Starting bulk send...\nTotal: {total} videos"
        )
        
        try:
            for idx, (video_id, file_ref, title, duration) in enumerate(videos):
                # Build caption
                mins = duration // 60 if duration else 0
                secs = duration % 60 if duration else 0
                duration_str = f"{mins}:{secs:02d}" if duration else "?"
                caption = f"📤 {title[:50]}{'...' if len(title) > 50 else ''}\n⏱ `{duration_str}`"
                
                try:
                    # Try to send via bot first (faster for recent videos)
                    if not file_ref.startswith('user_ref:'):
                        await bot.send_video(
                            chat_id=chat_id,
                            video=file_ref,
                            caption=caption,
                            parse_mode='Markdown'
                        )
                    else:
                        # Handle Telethon references
                        parts = file_ref.split(':')
                        if len(parts) == 3:
                            from_channel = int(parts[1])
                            msg_id = int(parts[2])
                            await bot.copy_message(
                                chat_id=chat_id,
                                from_chat_id=from_channel,
                                message_id=msg_id,
                                caption=caption,
                                parse_mode='Markdown'
                            )
                    
                    sent_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send video {video_id}: {e}")
                    failed_count += 1
                
                # Update progress every batch_size videos
                if (idx + 1) % batch_size == 0:
                    try:
                        await status_msg.edit_text(
                            f"📤 Sending videos...\n"
                            f"Progress: {idx + 1}/{total}\n"
                            f"✅ Sent: {sent_count}\n"
                            f"❌ Failed: {failed_count}"
                        )
                    except:
                        pass
                
                # Rate limiting
                await asyncio.sleep(delay_between)
                
                # Every 50 videos, add extra delay to avoid flood limits
                if (idx + 1) % 50 == 0:
                    await asyncio.sleep(2)
            
            # Final update
            try:
                await status_msg.edit_text(
                    f"✅ Bulk send complete!\n"
                    f"📤 Total: {total}\n"
                    f"✅ Sent: {sent_count}\n"
                    f"❌ Failed: {failed_count}"
                )
            except:
                pass
                
        except Exception as e:
            logger.error(f"Bulk send error: {e}")
        
        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': total
        }
    
    async def send_with_telethon(
        self,
        chat_id: int,
        videos: List[Tuple[int, str, str, int, int]],  # (video_id, file_id, title, duration, msg_id)
        bot,
        progress_callback=None
    ) -> dict:
        """
        Send videos using Telethon (more efficient for large batches)
        Requires videos to have message IDs from the source channel
        """
        client = await self._get_client()
        if not client:
            logger.error("Cannot use Telethon - not authorized")
            return await self.send_videos_batch(chat_id, videos, bot, progress_callback)
        
        total = len(videos)
        sent_count = 0
        failed_count = 0
        
        # Send progress message
        try:
            progress_msg = await bot.send_message(
                chat_id=chat_id,
                text=f"📤 Starting bulk send (Telethon mode)...\nTotal: {total} videos"
            )
        except:
            progress_msg = None
        
        for idx, video_data in enumerate(videos):
            try:
                video_id, file_ref, title, duration, msg_id = video_data
                
                # Forward the message using Telethon
                await client.forward_messages(
                    entity=chat_id,
                    messages=msg_id,
                    from_peer=TARGET_CHANNEL_ID
                )
                
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Telethon forward failed for video {video_id}: {e}")
                failed_count += 1
            
            # Progress update
            if progress_msg and (idx + 1) % 20 == 0:
                try:
                    await progress_msg.edit_text(
                        f"📤 Sending... {idx + 1}/{total}\n"
                        f"✅ {sent_count} | ❌ {failed_count}"
                    )
                except:
                    pass
            
            # Rate limiting for Telethon (more lenient)
            await asyncio.sleep(0.3)
            
            # Extra delay every 100 videos
            if (idx + 1) % 100 == 0:
                await asyncio.sleep(5)
        
        # Final update
        if progress_msg:
            try:
                await progress_msg.edit_text(
                    f"✅ Done!\n📤 {total} | ✅ {sent_count} | ❌ {failed_count}"
                )
            except:
                pass
        
        return {'sent': sent_count, 'failed': failed_count, 'total': total}


# Global instance
_bulk_sender = None

def get_bulk_sender(api_id: int = None, api_hash: str = None) -> BulkVideoSender:
    """Get or create bulk sender instance"""
    global _bulk_sender
    if _bulk_sender is None and api_id and api_hash:
        _bulk_sender = BulkVideoSender(api_id, api_hash)
    return _bulk_sender
