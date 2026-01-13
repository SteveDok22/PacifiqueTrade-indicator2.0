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
    def get_tradingview_url(pair: str, interval: str = "15") -> str:
        """
        Generate TradingView chart URL
        
        Args:
            pair: Currency pair (e.g., "GBP/USD")
            interval: Timeframe in minutes (5, 15, 30, 60, 240, D, W)
        
        Returns:
            TradingView URL
        """
        symbol = pair.replace("/", "")
        url = f"https://www.tradingview.com/chart/?symbol=FX_IDC:{symbol}&interval={interval}"
        return url
    
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
        """Format pre-market alert (T-4h)"""
        message = (
            "🔔 <b>PRE-MARKET ALERT</b> 🔔\n\n"
            f"📊 <b>Pair:</b> {pair}\n"
            f"🌍 <b>Event:</b> {event_name}\n"
            "⚡ <b>Impact:</b> 🔴🔴🔴 HIGH\n\n"
            f"📈 <b>Expected Direction:</b> {fundamental_direction}\n\n"
            "📋 <b>Data:</b>\n"
            f"  • Forecast: {forecast}\n"
            f"  • Previous: {previous}\n\n"
            f"⏰ <b>Market Opens In:</b> {time_to_open}\n\n"
            "💡 <b>Note:</b> Get ready for technical analysis in 2 hours."
        )
        return message
    
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
        """Format technical confirmation alert (T-2h)"""
        confirm_icon = "✅" if confirms_fundamental else "❌"
        confirm_text = "CONFIRMED - Trend matches fundamental!" if confirms_fundamental else "CONFLICTING - No trade today"
        next_step = "Final check in 1h 45min" if confirms_fundamental else "Monitoring continues"
        
        message = (
            "📊 <b>TECHNICAL CONFIRMATION</b> 📊\n\n"
            f"📈 <b>Pair:</b> {pair}\n"
            f"💹 <b>Current Price:</b> {current_price:.5f}\n\n"
            f"🎯 <b>Fundamental:</b> {fundamental_direction}\n\n"
            f"📉 <b>H4 Trend:</b> {trend_h4.upper()} ({h4_strength})\n"
            f"  • EMA50: {ema50_h4:.5f}\n"
            f"  • EMA200: {ema200_h4:.5f}\n\n"
            f"📈 <b>H1 Trend:</b> {trend_h1.upper()} ({h1_strength})\n\n"
            f"{confirm_icon} <b>Alignment:</b> {confirm_text}\n\n"
            f"⏰ <b>Next Step:</b> {next_step}"
        )
        return message
    
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
        """Format ready to trade alert (T-15min)"""
        direction_emoji = "🟢" if direction.lower() == "long" else "🔴"
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
        message = (
            "🚨 <b>READY TO TRADE</b> 🚨\n\n"
            f"{direction_emoji} <b>Pair:</b> {pair}\n"
            f"📍 <b>Direction:</b> {direction.upper()}\n"
            f"⚡ <b>Strength:</b> {strength.upper()}\n\n"
            "💰 <b>ENTRY DETAILS:</b>\n"
            f"  • Entry Price: {entry_price:.5f}\n"
            f"  • Position Size: {position_size_lots:.2f} lots\n"
            f"  • Risk Amount: ${risk_amount:.2f}\n"
        )
        
        if entry_zone_type and entry_zone_level:
            message += f"\n🎯 <b>Entry Zone:</b> {entry_zone_type} @ {entry_zone_level:.5f}\n"
        
        message += (
            f"\n🛑 <b>STOP LOSS (3-Part System):</b>\n"
            f"  • SL: {stop_loss:.5f}\n"
            "  • Part 1 (33%): Move to BE at TP1\n"
            "  • Part 2 (33%): Close at TP2\n"
            "  • Part 3 (34%): Trail to TP3+\n\n"
            "🎯 <b>TAKE PROFIT LEVELS:</b>\n"
            f"  • TP1: {take_profit_1:.5f} (+1R)\n"
            f"  • TP2: {take_profit_2:.5f} (+2R)\n"
            f"  • TP3: {take_profit_3:.5f} (+3R)\n\n"
            f"📊 <b>Risk/Reward:</b> 1:{risk_reward:.1f}\n\n"
            f"⏰ <b>Market Opens:</b> {time_to_open}\n\n"
            f"📊 <b>Chart:</b> <a href=\"{tv_url}\">Open on TradingView</a>\n\n"
            "✅ <b>Action:</b> Prepare to enter on market open!"
        )
        return message
    
    @staticmethod
    def format_entry_confirmed(
        pair: str,
        direction: str,
        entry_price: float,
        volume_increase: float,
        reaction_type: str
    ) -> str:
        """Format entry confirmation (T-0, after market open)"""
        tv_url = MessageFormatter.get_tradingview_url(pair, "5")
        
        message = (
            "✅ <b>ENTRY CONFIRMED</b> ✅\n\n"
            f"📊 <b>Pair:</b> {pair}\n"
            f"📍 <b>Direction:</b> {direction.upper()}\n"
            f"💰 <b>Entry Price:</b> {entry_price:.5f}\n\n"
            f"🎯 <b>Market Reaction:</b> {reaction_type}\n"
            f"📈 <b>Volume:</b> +{volume_increase:.0f}% above average\n\n"
            "✅ <b>Status:</b> ALL SYSTEMS GO!\n\n"
            f"📊 <b>Chart:</b> <a href=\"{tv_url}\">Open on TradingView</a>\n\n"
            "💡 <b>Action:</b> Enter the trade now!\n"
            "📝 <b>Remember:</b> Follow your SL/TP plan exactly"
        )
        return message
    
    @staticmethod
    def format_entry_cancelled(
        pair: str,
        direction: str,
        cancellation_reason: str
    ) -> str:
        """Format entry cancellation (T-0, after market open)"""
        message = (
            "❌ <b>SIGNAL CANCELLED</b> ❌\n\n"
            f"📊 <b>Pair:</b> {pair}\n"
            f"📍 <b>Direction:</b> {direction.upper()}\n\n"
            f"⚠️ <b>Reason:</b> {cancellation_reason}\n\n"
            "💡 <b>Action:</b> DO NOT ENTER\n"
            "🔍 <b>Status:</b> Wait for next opportunity\n\n"
            "Remember: Not every signal becomes a trade. We only take HIGH PROBABILITY setups!"
        )
        return message
    
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
        """Format position update (during trade)"""
        profit_emoji = "📈" if current_profit_pips > 0 else "📉"
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
        message = (
            f"{profit_emoji} <b>POSITION UPDATE</b> {profit_emoji}\n\n"
            f"📊 <b>Pair:</b> {pair} ({direction.upper()})\n\n"
            "💰 <b>Current Status:</b>\n"
            f"  • Entry: {entry_price:.5f}\n"
            f"  • Current: {current_price:.5f}\n"
            f"  • Profit: {current_profit_pips:.1f} pips (${current_profit_usd:.2f})\n"
            f"  • R-Multiple: +{r_multiple:.1f}R\n\n"
            f"🎯 <b>Next Target:</b> {next_tp:.5f}\n\n"
            f"✅ <b>Action Taken:</b> {action}\n\n"
            f"📊 <b>Chart:</b> <a href=\"{tv_url}\">Open on TradingView</a>\n\n"
            "💡 Keep monitoring. Let profits run!"
        )
        return message
    
    @staticmethod
    def format_error_alert(
        error_type: str,
        error_message: str,
        timestamp: Optional[datetime] = None
    ) -> str:
        """Format error alert"""
        if timestamp is None:
            timestamp = datetime.now()
        
        message = (
            "⚠️ <b>SYSTEM ERROR</b> ⚠️\n\n"
            f"🔴 <b>Type:</b> {error_type}\n"
            f"📝 <b>Message:</b> {error_message}\n"
            f"⏰ <b>Time:</b> {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "💡 The system will attempt to recover automatically.\n"
            "Check logs for details."
        )
        return message
    
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
        result_emoji = "🎉 Great day!" if total_profit_loss > 0 else "📚 Learn and improve!"
        
        message = (
            "📊 <b>DAILY SUMMARY</b> 📊\n\n"
            f"📅 <b>Date:</b> {date}\n\n"
            f"📈 <b>Signals:</b> {signals_generated} generated\n"
            f"🎯 <b>Trades:</b> {trades_taken} taken\n\n"
            f"✅ <b>Winners:</b> {trades_won}\n"
            f"❌ <b>Losers:</b> {trades_lost}\n"
            f"📊 <b>Win Rate:</b> {win_rate:.1f}%\n\n"
            f"💰 <b>P&L:</b> ${total_profit_loss:+.2f}\n\n"
            f"{result_emoji}"
        )
        return message
    
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
        
        message = (
            f"{status_emoji} <b>SYSTEM STATUS</b>\n\n"
            f"⚙️ <b>Status:</b> {system_status.upper()}\n\n"
            f"📊 <b>Active Signals:</b> {active_signals}\n"
            f"💹 <b>Active Trades:</b> {active_trades}\n\n"
            f"💰 <b>Account:</b> ${account_balance:,.2f}\n"
            f"📈 <b>Today P&L:</b> ${today_pnl:+.2f}\n\n"
            "✅ All systems operational"
        )
        return message


def main():
    """Test message formatting"""
    
    print("\n" + "="*60)
    print("MESSAGE FORMATTER TEST")
    print("="*60 + "\n")
    
    formatter = MessageFormatter()
    
    # Test 1: TradingView URL
    print("Test 1: TradingView URL Generation\n")
    url = formatter.get_tradingview_url("GBP/USD", "15")
    print(f"URL: {url}\n")
    
    # Test 2: Pre-Market Alert
    print("Test 2: Pre-Market Alert\n")
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
    
    # Test 3: Ready to Trade Alert
    print("Test 3: Ready to Trade Alert\n")
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
    
    # Test 4: Entry Confirmed
    print("Test 4: Entry Confirmed\n")
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