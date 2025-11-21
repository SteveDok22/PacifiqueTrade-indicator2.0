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
    
    def is_enabled(self) -> bool:
        """Check if Telegram is enabled"""
        return self.enabled
    
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
    
    async def send_entry_confirmed(
        self,
        pair: str,
        direction: str,
        entry_price: float,
        volume_increase: float,
        reaction_type: str
    ) -> bool:
        """Send entry confirmation alert (T-0)"""
        
        if AlertLevel.ENTRY_CONFIRM not in self.enabled_alerts:
            logger.debug("Entry confirmation alerts disabled")
            return False
        
        message = self.formatter.format_entry_confirmed(
            pair=pair,
            direction=direction,
            entry_price=entry_price,
            volume_increase=volume_increase,
            reaction_type=reaction_type
        )
        
        return await self.send_message(message)
    
    async def send_entry_cancelled(
        self,
        pair: str,
        direction: str,
        reason: str
    ) -> bool:
        """Send entry cancellation alert (T-0)"""
        
        if AlertLevel.ENTRY_CONFIRM not in self.enabled_alerts:
            return False
        
        message = self.formatter.format_entry_cancelled(
            pair=pair,
            direction=direction,
            cancellation_reason=reason
        )
        
        return await self.send_message(message)
    
    async def send_position_update(
        self,
        position_data: Dict
    ) -> bool:
        """Send position update (TP hit, trailing stop moved)"""
        
        message = self.formatter.format_position_update(
            pair=position_data['pair'],
            direction=position_data['direction'],
            entry_price=position_data['entry_price'],
            current_price=position_data['current_price'],
            current_profit_pips=position_data['profit_pips'],
            current_profit_usd=position_data['profit_usd'],
            r_multiple=position_data['r_multiple'],
            next_tp=position_data['next_tp'],
            action=position_data['action']
        )
        
        return await self.send_message(message)
    
    async def send_error_alert(
        self,
        error_type: str,
        error_message: str
    ) -> bool:
        """Send error alert"""
        
        if AlertLevel.ERROR not in self.enabled_alerts:
            return False
        
        message = self.formatter.format_error_alert(
            error_type=error_type,
            error_message=error_message
        )
        
        return await self.send_message(message, disable_notification=False)
    
    async def send_status(self) -> bool:
        """Send system status"""
        
        message = self.formatter.format_status_message(
            system_status="running",
            active_signals=0,
            active_trades=0,
            account_balance=config.ACCOUNT_BALANCE,
            today_pnl=0.0
        )
        
        return await self.send_message(message)


def main():
    """Test Telegram bot"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("TELEGRAM BOT TEST")
    print("="*60 + "\n")
    
    if not TELEGRAM_AVAILABLE:
        print("❌ python-telegram-bot not installed")
        print("   Install with: pip install python-telegram-bot")
        return 1
    
    if not config.TELEGRAM_ENABLED:
        print("❌ Telegram is disabled in .env")
        print("   Set TELEGRAM_ENABLED=true in .env file")
        return 1
    
    try:
        notifier = TelegramNotifier()
        
        if not notifier.is_enabled():
            print("❌ Telegram notifier not enabled")
            print("   Check your .env file configuration")
            return 1
        
        print("✅ Telegram notifier initialized\n")
        
        # Test 1: Send simple status message
        print("Test 1: Sending status message...")
        
        async def test_status():
            success = await notifier.send_status()
            return success
        
        result = asyncio.run(test_status())
        
        if result:
            print("✅ Status message sent! Check your Telegram.\n")
        else:
            print("❌ Failed to send message\n")
            return 1
        
        # Test 2: Send test ready-to-trade alert
        print("Test 2: Sending test 'Ready to Trade' alert...")
        
        test_signal = {
            'pair': 'GBP/USD',
            'direction': 'LONG',
            'strength': 'STRONG',
            'entry_price': 1.2700,
            'stop_loss': 1.2650,
            'tp1': 1.2750,
            'tp2': 1.2800,
            'tp3': 1.2850,
            'position_size_lots': 0.20,
            'risk_amount': 100.0,
            'risk_reward': 3.0,
            'entry_zone_type': 'Equal Lows',
            'entry_zone_level': 1.2695
        }
        
        async def test_ready():
            success = await notifier.send_ready_to_trade(test_signal, with_buttons=True)
            return success
        
        result = asyncio.run(test_ready())
        
        if result:
            print("✅ Ready to Trade alert sent! Check your Telegram.\n")
        else:
            print("❌ Failed to send alert\n")
        
        print("="*60)
        print("✅ TELEGRAM BOT TEST COMPLETE!")
        print("="*60 + "\n")
        print("💡 Check your Telegram for the test messages!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())