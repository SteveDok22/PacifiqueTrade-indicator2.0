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