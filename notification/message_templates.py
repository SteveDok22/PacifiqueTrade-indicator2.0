"""
Message Templates Module

Formats messages for Telegram notifications.
Creates beautiful, readable alerts with emojis and formatting.
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import AlertLevel, TrendDirection, SignalStrength


logger = logging.getLogger(__name__)

class MessageFormatter:
    """
    Message Formatter for Telegram
    
    Creates formatted messages for different alert levels:
    1. Pre-Market Alert (T-4h)
    2. Technical Confirmation (T-2h)
    3. Ready to Trade (T-15min)
    4. Entry Confirmation (T-0)
    """
    
    @staticmethod
    def format_pre_market_alert(
        pair: str,
        fundamental_direction: str,
        event_name: str,
        forecast: str,
        previous: str,
        impact: str,
        time_to_open: str
    ) -> str:
        """
        Format pre-market alert (T-4h)
        
        Notifies about upcoming high-impact news
        """
        message = f"""
🔔 <b>PRE-MARKET ALERT</b> 🔔

📊 <b>Pair:</b> {pair}
🌍 <b>Event:</b> {event_name}
⚡ <b>Impact:</b> {'🔴' * 3} HIGH

📈 <b>Expected Direction:</b> {fundamental_direction}

📋 <b>Data:</b>
  • Forecast: {forecast}
  • Previous: {previous}

⏰ <b>Market Opens In:</b> {time_to_open}

💡 <b>Note:</b> Get ready for technical analysis in 2 hours.
"""
        return message.strip()
    
    @staticmethod
    def format_technical_confirmation(
        pair: str,
        fundamental_direction: str,
        trend_h4: str,
        trend_h1: str,
        h4_strength: str,
        h1_strength: str,
        ema50_h4: float,
        ema200_h4: float,
        current_price: float,
        confirms_fundamental: bool
    ) -> str:
        """
        Format technical confirmation alert (T-2h)
        
        Confirms trend aligns with fundamental
        """
        confirm_icon = "✅" if confirms_fundamental else "❌"
        
        message = f"""
📊 <b>TECHNICAL CONFIRMATION</b> 📊

📈 <b>Pair:</b> {pair}
💹 <b>Current Price:</b> {current_price:.5f}

🎯 <b>Fundamental:</b> {fundamental_direction}

📉 <b>H4 Trend:</b> {trend_h4.upper()} ({h4_strength})
  • EMA50: {ema50_h4:.5f}
  • EMA200: {ema200_h4:.5f}

📈 <b>H1 Trend:</b> {trend_h1.upper()} ({h1_strength})

{confirm_icon} <b>Alignment:</b> {"CONFIRMED - Trend matches fundamental!" if confirms_fundamental else "CONFLICTING - No trade today"}

⏰ <b>Next Step:</b> {"Final check in 1h 45min" if confirms_fundamental else "Monitoring continues"}
"""
        return message.strip()
    
    @staticmethod
    def format_ready_to_trade(
        pair: str,
        direction: str,
        strength: str,
        entry_price: float,
        stop_loss: float,
        take_profit_1: float,
        take_profit_2: float,
        take_profit_3: float,
        position_size_lots: float,
        risk_amount: float,
        risk_reward: float,
        entry_zone_type: Optional[str] = None,
        entry_zone_level: Optional[float] = None,
        time_to_open: str = "15 minutes"
    ) -> str:
        """
        Format ready to trade alert (T-15min)
        
        THE MAIN SIGNAL - All conditions met
        """
        direction_emoji = "🟢" if direction.lower() == "long" else "🔴"
        
        message = f"""
🚨 <b>READY TO TRADE</b> 🚨

{direction_emoji} <b>Pair:</b> {pair}
📍 <b>Direction:</b> {direction.upper()}
⚡ <b>Strength:</b> {strength.upper()}

💰 <b>ENTRY DETAILS:</b>
  • Entry Price: {entry_price:.5f}
  • Position Size: {position_size_lots:.2f} lots
  • Risk Amount: ${risk_amount:.2f}
"""
        
        if entry_zone_type and entry_zone_level:
            message += f"\n🎯 <b>Entry Zone:</b> {entry_zone_type} @ {entry_zone_level:.5f}\n"
        
        message += f"""
🛑 <b>STOP LOSS (3-Part System):</b>
  • SL: {stop_loss:.5f}
  • Part 1 (33%): Move to BE at TP1
  • Part 2 (33%): Close at TP2
  • Part 3 (34%): Trail to TP3+

🎯 <b>TAKE PROFIT LEVELS:</b>
  • TP1: {take_profit_1:.5f} (+1R)
  • TP2: {take_profit_2:.5f} (+2R)
  • TP3: {take_profit_3:.5f} (+3R)

📊 <b>Risk/Reward:</b> 1:{risk_reward:.1f}

⏰ <b>Market Opens:</b> {time_to_open}

✅ <b>Action:</b> Prepare to enter on market open!
"""
        return message.strip()
    
    @staticmethod
    def format_entry_confirmed(
        pair: str,
        direction: str,
        entry_price: float,
        volume_increase: float,
        reaction_type: str
    ) -> str:
        """
        Format entry confirmation (T-0, after market open)
        
        Confirms market reaction supports entry
        """
        message = f"""
✅ <b>ENTRY CONFIRMED</b> ✅

📊 <b>Pair:</b> {pair}
📍 <b>Direction:</b> {direction.upper()}
💰 <b>Entry Price:</b> {entry_price:.5f}

🎯 <b>Market Reaction:</b> {reaction_type}
📈 <b>Volume:</b> +{volume_increase:.0f}% above average

✅ <b>Status:</b> ALL SYSTEMS GO!

💡 <b>Action:</b> Enter the trade now!
📝 <b>Remember:</b> Follow your SL/TP plan exactly
"""
        return message.strip()
    
    @staticmethod
    def format_entry_cancelled(
        pair: str,
        direction: str,
        cancellation_reason: str
    ) -> str:
        """
        Format entry cancellation (T-0, after market open)
        
        Market didn't confirm, cancel the trade
        """
        message = f"""
❌ <b>SIGNAL CANCELLED</b> ❌

📊 <b>Pair:</b> {pair}
📍 <b>Direction:</b> {direction.upper()}

⚠️ <b>Reason:</b> {cancellation_reason}

💡 <b>Action:</b> DO NOT ENTER
🔍 <b>Status:</b> Wait for next opportunity

Remember: Not every signal becomes a trade. We only take HIGH PROBABILITY setups!
"""
        return message.strip()
    
    @staticmethod
    def format_position_update(
        pair: str,
        direction: str,
        entry_price: float,
        current_price: float,
        current_profit_pips: float,
        current_profit_usd: float,
        r_multiple: float,
        next_tp: float,
        action: str
    ) -> str:
        """
        Format position update (during trade)
        
        Updates on TP hits and trailing stops
        """
        profit_emoji = "📈" if current_profit_pips > 0 else "📉"
        
        message = f"""
{profit_emoji} <b>POSITION UPDATE</b> {profit_emoji}

📊 <b>Pair:</b> {pair} ({direction.upper()})

💰 <b>Current Status:</b>
  • Entry: {entry_price:.5f}
  • Current: {current_price:.5f}
  • Profit: {current_profit_pips:.1f} pips (${current_profit_usd:.2f})
  • R-Multiple: +{r_multiple:.1f}R

🎯 <b>Next Target:</b> {next_tp:.5f}

✅ <b>Action Taken:</b> {action}

💡 Keep monitoring. Let profits run!
"""
        return message.strip()
    
    @staticmethod
    def format_error_alert(
        error_type: str,
        error_message: str,
        timestamp: Optional[datetime] = None
    ) -> str:
        """Format error alert"""
        if timestamp is None:
            timestamp = datetime.now()
        
        message = f"""
⚠️ <b>SYSTEM ERROR</b> ⚠️

🔴 <b>Type:</b> {error_type}
📝 <b>Message:</b> {error_message}
⏰ <b>Time:</b> {timestamp.strftime('%Y-%m-%d %H:%M:%S')}

💡 The system will attempt to recover automatically.
Check logs for details.
"""
        return message.strip()
    
    @staticmethod
    def format_daily_summary(
        date: str,
        signals_generated: int,
        trades_taken: int,
        trades_won: int,
        trades_lost: int,
        total_profit_loss: float,
        win_rate: float
    ) -> str:
        """Format daily summary"""
        message = f"""
📊 <b>DAILY SUMMARY</b> 📊

📅 <b>Date:</b> {date}

📈 <b>Signals:</b> {signals_generated} generated
🎯 <b>Trades:</b> {trades_taken} taken

✅ <b>Winners:</b> {trades_won}
❌ <b>Losers:</b> {trades_lost}
📊 <b>Win Rate:</b> {win_rate:.1f}%

💰 <b>P&L:</b> ${total_profit_loss:+.2f}

{"🎉 Great day!" if total_profit_loss > 0 else "📚 Learn and improve!"}
"""
        return message.strip()
    
    @staticmethod
    def format_status_message(
        system_status: str,
        active_signals: int,
        active_trades: int,
        account_balance: float,
        today_pnl: float
    ) -> str:
        """Format system status message"""
        status_emoji = "🟢" if system_status == "running" else "🔴"
        
        message = f"""
{status_emoji} <b>SYSTEM STATUS</b>

⚙️ <b>Status:</b> {system_status.upper()}

📊 <b>Active Signals:</b> {active_signals}
💹 <b>Active Trades:</b> {active_trades}

💰 <b>Account:</b> ${account_balance:,.2f}
📈 <b>Today P&L:</b> ${today_pnl:+.2f}

✅ All systems operational
"""
        return message.strip()

def main():
    """Test message formatting"""
    
    print("\n" + "="*60)
    print("MESSAGE FORMATTER TEST")
    print("="*60 + "\n")
    
    formatter = MessageFormatter()
    
    # Test 1: Pre-Market Alert
    print("Test 1: Pre-Market Alert\n")
    msg1 = formatter.format_pre_market_alert(
        pair="GBP/USD",
        fundamental_direction="USD Weaker (Bullish GBP/USD)",
        event_name="US CPI",
        forecast="3.2%",
        previous="3.5%",
        impact="HIGH",
        time_to_open="4 hours"
    )
    print(msg1)
    print("\n" + "-"*60 + "\n")
    
    # Test 2: Ready to Trade Alert
    print("Test 2: Ready to Trade Alert\n")
    msg2 = formatter.format_ready_to_trade(
        pair="GBP/USD",
        direction="LONG",
        strength="STRONG",
        entry_price=1.2700,
        stop_loss=1.2650,
        take_profit_1=1.2750,
        take_profit_2=1.2800,
        take_profit_3=1.2850,
        position_size_lots=0.20,
        risk_amount=100.0,
        risk_reward=3.0,
        entry_zone_type="Equal Lows",
        entry_zone_level=1.2695
    )
    print(msg2)
    print("\n" + "-"*60 + "\n")
    
    # Test 3: Entry Confirmed
    print("Test 3: Entry Confirmed\n")
    msg3 = formatter.format_entry_confirmed(
        pair="GBP/USD",
        direction="LONG",
        entry_price=1.2702,
        volume_increase=175,
        reaction_type="Strong bullish breakout"
    )
    print(msg3)
    
    print("\n" + "="*60)
    print("✅ MESSAGE FORMATTER TEST COMPLETE!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()