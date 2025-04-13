import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import aiohttp
import os

from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import InputPeerEmpty, Channel

from database.storage import Storage
from utils.summarizer import generate_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramMonitor:
    def __init__(
        self,
        name: str,
        api_id: int,
        api_hash: str,
        phone: str,
        groups: List[str],
        storage: Storage
    ):
        self.name = name
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.groups = groups
        self.storage = storage
        self.client = None
        self.webhook_url = None
        self.webhook_interval = 60  # Default: 60 minutes
        self.running = False
        self.summary_task = None
        
        # Create session directory if it doesn't exist
        os.makedirs("sessions", exist_ok=True)
        
    async def start(self):
        """Start the Telegram monitoring bot"""
        if self.running:
            logger.info(f"Bot {self.name} is already running")
            return
        
        logger.info(f"Starting bot {self.name}")
        
        try:
            # Initialize Telegram client with session in the sessions directory
            session_path = os.path.join("sessions", self.name)
            self.client = TelegramClient(
                session_path,
                self.api_id,
                self.api_hash
            )
            
            # Connect to Telegram
            await self.client.connect()
            
            # Check if already authorized
            if not await self.client.is_user_authorized():
                logger.info(f"Not authorized. Sending code request to {self.phone}")
                await self.client.send_code_request(self.phone)
                
                # This will prompt for the code in the console
                logger.info("Please check your Telegram messages and enter the code:")
                code = input("Enter the code: ")
                
                try:
                    await self.client.sign_in(self.phone, code)
                except Exception as e:
                    logger.error(f"Error during sign in: {str(e)}")
                    return
            
            logger.info("Successfully authenticated")
            
            # Join groups
            await self._join_groups()
            
            # Register message handler
            @self.client.on(events.NewMessage)
            async def handler(event):
                await self._process_message(event)
            
            self.running = True
            
            # Start summary task if webhook is set
            if self.webhook_url:
                self._start_summary_task()
            
            # Keep the client running
            logger.info("Bot is now monitoring messages")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            raise
    
    async def _join_groups(self):
        """Join the specified Telegram groups"""
        logger.info(f"Joining {len(self.groups)} groups")
        
        try:
            # Get dialogs to find groups
            dialogs = await self.client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=100,
                hash=0
            ))
            
            # Find existing groups
            existing_groups = {}
            for dialog in dialogs.dialogs:
                try:
                    entity = await self.client.get_entity(dialog.peer)
                    if isinstance(entity, Channel):
                        username = getattr(entity, 'username', '')
                        if username:
                            existing_groups[username.lower()] = entity
                except Exception as e:
                    logger.error(f"Error getting entity: {str(e)}")
            
            # Join new groups
            for group in self.groups:
                group_username = group.replace('@', '').lower()
                
                if group_username in existing_groups:
                    logger.info(f"Already a member of {group}")
                    continue
                
                try:
                    # Try to join the group
                    await self.client(JoinChannelRequest(group))
                    logger.info(f"Successfully joined {group}")
                    
                    # Wait a bit to avoid rate limiting
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Failed to join {group}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error joining groups: {str(e)}")
    
    async def _process_message(self, event):
        """Process and store a new message"""
        try:
            # Get message data
            message = event.message
            
            # Get chat information
            chat = await event.get_chat()
            chat_id = chat.id
            chat_title = getattr(chat, 'title', str(chat_id))
            
            # Get sender information
            sender_id = None
            sender_name = None
            
            if message.sender_id:
                try:
                    sender = await event.get_sender()
                    sender_id = sender.id
                    sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', str(sender_id))
                except Exception as e:
                    logger.error(f"Error getting sender: {str(e)}")
            
            # Extract message content
            content = message.message if message.message else "[No text content]"
            
            # Store in database
            await self.storage.store_message(
                group_id=chat_id,
                group_name=chat_title,
                sender_id=sender_id,
                sender_name=sender_name,
                message_id=message.id,
                content=content,
                timestamp=datetime.now(),
                has_media=bool(message.media)
            )
            
            logger.debug(f"Stored message from {chat_title}: {content[:50]}...")
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    async def set_webhook(self, url: str, interval_minutes: int):
        """Set or update the webhook configuration"""
        self.webhook_url = url
        self.webhook_interval = interval_minutes
        
        # Restart summary task if running
        if self.running:
            self._start_summary_task()
        
        logger.info(f"Webhook set to {url} with interval {interval_minutes} minutes")
    
    def _start_summary_task(self):
        """Start or restart the periodic summary task"""
        if self.summary_task:
            self.summary_task.cancel()
        
        self.summary_task = asyncio.create_task(self._periodic_summary())
    
    async def _periodic_summary(self):
        """Periodically generate and send summaries to the webhook"""
        while self.running and self.webhook_url:
            try:
                # Wait for the specified interval
                await asyncio.sleep(self.webhook_interval * 60)
                
                # Generate summary
                summary = await generate_summary(self.storage)
                
                # Send to webhook
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.webhook_url,
                        json=summary
                    ) as response:
                        if response.status != 200:
                            logger.error(f"Webhook error: {response.status}")
                        else:
                            logger.info("Summary sent to webhook successfully")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic summary: {str(e)}")
                await asyncio.sleep(60)  # Wait a bit before retrying
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        if not self.storage:
            return {}
        
        try:
            stats = await self.storage.get_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"error": str(e)}
