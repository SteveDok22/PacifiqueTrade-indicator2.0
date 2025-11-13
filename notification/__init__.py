"""
Notification module for PacifiqueTrade Indicator 2.0

This module handles all notification systems:
- Telegram bot with multi-level alerts
- Message formatting and templates
- Interactive buttons and commands
"""

from .telegram_bot import TelegramNotifier, TelegramCommand
from .message_templates import MessageFormatter

__all__ = [
    'TelegramNotifier',
    'TelegramCommand',
    'MessageFormatter',
]

__version__ = '2.0.0' 