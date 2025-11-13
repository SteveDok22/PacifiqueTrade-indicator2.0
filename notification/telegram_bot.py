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
    
    async def send_pre_market_alert(
        self,
        pair: str,
        fundamental_signal: Dict
    ) -> bool:
        """Send pre-market alert (T-4h)"""
        
        if AlertLevel.PRE_MARKET not in self.enabled_alerts:
            logger.debug("Pre-market alerts disabled")
            return False
        
        message = self.formatter.format_pre_market_alert(
            pair=pair,
            fundamental_direction=fundamental_signal['direction'],
            event_name=fundamental_signal['event_name'],
            forecast=fundamental_signal.get('forecast', 'N/A'),
            previous=fundamental_signal.get('previous', 'N/A'),
            impact=fundamental_signal['impact'],
            time_to_open=fundamental_signal.get('time_to_open', '4 hours')
        )
        
        return await self.send_message(message)
    
    async def send_technical_confirmation(
        self,
        pair: str,
        fundamental_direction: str,
        trend_h4: Dict,
        trend_h1: Dict,
        confirms: bool
    ) -> bool:
        """Send technical confirmation alert (T-2h)"""
        
        if AlertLevel.TECHNICAL_CONFIRM not in self.enabled_alerts:
            logger.debug("Technical confirmation alerts disabled")
            return False
        
        message = self.formatter.format_technical_confirmation(
            pair=pair,
            fundamental_direction=fundamental_direction,
            trend_h4=trend_h4['direction'],
            trend_h1=trend_h1['direction'],
            h4_strength=trend_h4['strength'],
            h1_strength=trend_h1['strength'],
            ema50_h4=trend_h4['ema50'],
            ema200_h4=trend_h4['ema200'],
            current_price=trend_h4['current_price'],
            confirms_fundamental=confirms
        )
        
        return await self.send_message(message)
    
    async def send_ready_to_trade(
        self,
        signal: Dict,
        with_buttons: bool = True
    ) -> bool:
        """
        Send ready to trade alert (T-15min)
        
        THE MAIN ALERT - Includes interactive buttons
        """
        if AlertLevel.READY_TO_TRADE not in self.enabled_alerts:
            logger.debug("Ready to trade alerts disabled")
            return False
        
        message = self.formatter.format_ready_to_trade(
            pair=signal['pair'],
            direction=signal['direction'],
            strength=signal['strength'],
            entry_price=signal['entry_price'],
            stop_loss=signal['stop_loss'],
            take_profit_1=signal['tp1'],
            take_profit_2=signal['tp2'],
            take_profit_3=signal['tp3'],
            position_size_lots=signal['position_size_lots'],
            risk_amount=signal['risk_amount'],
            risk_reward=signal['risk_reward'],
            entry_zone_type=signal.get('entry_zone_type'),
            entry_zone_level=signal.get('entry_zone_level')
        )
        
        # Add interactive buttons
        keyboard = None
        if with_buttons:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Will Take", callback_data=f"accept_{signal['pair']}"),
                    InlineKeyboardButton("❌ Will Skip", callback_data=f"reject_{signal['pair']}")
                ],
                [
                    InlineKeyboardButton("📊 Chart", url=f"https://www.tradingview.com/chart/?symbol={signal['pair'].replace('/', '')}")
                ]
            ])
        
        return await self.send_message(message, reply_markup=keyboard)