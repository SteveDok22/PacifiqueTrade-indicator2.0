"""
Telegram Bot Module

Sends trading alerts to Telegram with:
- 4-level alert system (Pre-market, Technical, Ready, Entry)
- Interactive buttons
- Command handlers (/status, /signals, /help)
- Error handling and retry logic
"""

import asyncio
from typing import Optional, Dict, List
from datetime import datetime
import logging
from enum import Enum

try:
    from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    from telegram.error import TelegramError, NetworkError, TimedOut
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Bot = None
    TelegramError = Exception

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import config
from core.exceptions import TelegramError as CustomTelegramError
from core.enums import AlertLevel
from notification.message_templates import MessageFormatter


logger = logging.getLogger(__name__)


class TelegramCommand(Enum):
    """Telegram bot commands"""
    STATUS = "status"
    SIGNALS = "signals"
    HELP = "help"
    PAIRS = "pairs"
    SETTINGS = "settings"


class TelegramNotifier:
    """
    Telegram Notification System
    
    Sends multi-level alerts to Telegram:
    1. Pre-Market Alert (T-4h)
    2. Technical Confirmation (T-2h)
    3. Ready to Trade (T-15min)
    4. Entry Confirmation (T-0)
    
    Also handles commands and interactive buttons.
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        """
        Initialize Telegram Notifier
        
        Args:
            token: Bot token (default: from config)
            chat_id: Chat ID (default: from config)
        """
        if not TELEGRAM_AVAILABLE:
            logger.error("python-telegram-bot not installed. Install with: pip install python-telegram-bot")
            self.enabled = False
            return
        
        if not config.TELEGRAM_ENABLED:
            logger.warning("Telegram notifications disabled in config")
            self.enabled = False
            return
        
        self.token = token or config.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or config.TELEGRAM_CHAT_ID
        
        if not self.token or not self.chat_id:
            logger.error("Telegram token or chat_id missing")
            self.enabled = False
            return
        
        self.bot = Bot(token=self.token)
        self.formatter = MessageFormatter()
        self.enabled = True
        
        # Alert level configuration
        self.enabled_alerts = config.get_alert_levels()
        
        logger.info(f"✅ Telegram Notifier initialized (Chat ID: {self.chat_id})")
    
    async def send_message(
        self,
        message: str,
        parse_mode: str = 'HTML',
        disable_notification: bool = False,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        retry_count: int = 3
    ) -> bool:
        """
        Send message to Telegram
        
        Args:
            message: Message text
            parse_mode: 'HTML' or 'Markdown'
            disable_notification: Silent notification
            reply_markup: Keyboard buttons
            retry_count: Number of retries on failure
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Telegram not enabled, message not sent")
            return False
        
        for attempt in range(retry_count):
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification,
                    reply_markup=reply_markup
                )
                
                logger.debug("Message sent successfully")
                return True
                
            except NetworkError as e:
                logger.warning(f"Network error on attempt {attempt + 1}/{retry_count}: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except TimedOut as e:
                logger.warning(f"Timeout on attempt {attempt + 1}/{retry_count}: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    
            except TelegramError as e:
                logger.error(f"Telegram error: {e}")
                raise CustomTelegramError(
                    message=str(e),
                    chat_id=self.chat_id
                )
            
            except Exception as e:
                logger.error(f"Unexpected error sending message: {e}")
                return False
        
        logger.error(f"Failed to send message after {retry_count} attempts")
        return False