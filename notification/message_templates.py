"""
Message Templates Module

Formats messages for Telegram notifications.
Creates beautiful, readable alerts with emojis and formatting.
Includes TradingView integration for chart links.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
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
    5. TradingView Entry Zone (Webhook)
    """
    
    # =========================================================================
    # TRADINGVIEW URL GENERATION
    # =========================================================================
    
    @staticmethod
    def get_tradingview_url(
        pair: str,
        interval: str = "15"
    ) -> str:
        """
        Generate TradingView chart URL
        
        Args:
            pair: Currency pair (e.g., "GBP/USD")
            interval: Timeframe in minutes (1, 5, 15, 30, 60, 240, D, W, M)
                     1 = 1 minute
                     5 = 5 minutes
                     15 = 15 minutes
                     30 = 30 minutes
                     60 = 1 hour
                     240 = 4 hours
                     D = Daily
                     W = Weekly
                     M = Monthly
        
        Returns:
            TradingView URL with symbol and interval
        """
        # Convert pair format (GBP/USD → GBPUSD)
        symbol = pair.replace("/", "").replace(" ", "").upper()
        
        # Build URL - use FX_IDC for forex pairs
        url = f"https://www.tradingview.com/chart/?symbol=FX_IDC:{symbol}&interval={interval}"
        
        return url
    
    @staticmethod
    def get_tradingview_urls_all_timeframes(pair: str) -> Dict[str, str]:
        """
        Get TradingView URLs for all relevant timeframes
        
        Args:
            pair: Currency pair
            
        Returns:
            Dictionary with timeframe names and URLs
        """
        symbol = pair.replace("/", "").replace(" ", "").upper()
        base_url = f"https://www.tradingview.com/chart/?symbol=FX_IDC:{symbol}"
        
        return {
            'M15': f"{base_url}&interval=15",
            'M30': f"{base_url}&interval=30",
            'H1': f"{base_url}&interval=60",
            'H4': f"{base_url}&interval=240",
            'D1': f"{base_url}&interval=D",
        }
    
    # =========================================================================
    # CORE ALERT MESSAGES
    # =========================================================================
    
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
        tv_url = MessageFormatter.get_tradingview_url(pair, "240")  # H4 for overview
        
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

📊 <a href="{tv_url}">Open Chart on TradingView (H4)</a>

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
        tv_url_h4 = MessageFormatter.get_tradingview_url(pair, "240")
        tv_url_h1 = MessageFormatter.get_tradingview_url(pair, "60")
        
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

📊 <b>Charts:</b>
  • <a href="{tv_url_h4}">H4 Chart</a> | <a href="{tv_url_h1}">H1 Chart</a>

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
        Includes TradingView links for all relevant timeframes
        """
        direction_emoji = "🟢" if direction.lower() == "long" else "🔴"
        
        # Get TradingView URLs
        tv_url_m15 = MessageFormatter.get_tradingview_url(pair, "15")
        tv_url_h1 = MessageFormatter.get_tradingview_url(pair, "60")
        tv_url_h4 = MessageFormatter.get_tradingview_url(pair, "240")
        
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

📊 <b>TradingView Charts:</b>
  • <a href="{tv_url_m15}">M15 (Entry)</a>
  • <a href="{tv_url_h1}">H1 (Trend)</a>
  • <a href="{tv_url_h4}">H4 (Bias)</a>

✅ <b>Action:</b> Open TradingView and watch for Entry Zone!
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
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
        message = f"""
✅ <b>ENTRY CONFIRMED</b> ✅

📊 <b>Pair:</b> {pair}
📍 <b>Direction:</b> {direction.upper()}
💰 <b>Entry Price:</b> {entry_price:.5f}

🎯 <b>Market Reaction:</b> {reaction_type}
📈 <b>Volume:</b> +{volume_increase:.0f}% above average

✅ <b>Status:</b> ALL SYSTEMS GO!

📊 <a href="{tv_url}">Execute on TradingView</a>

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
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
        message = f"""
❌ <b>SIGNAL CANCELLED</b> ❌

📊 <b>Pair:</b> {pair}
📍 <b>Direction:</b> {direction.upper()}

⚠️ <b>Reason:</b> {cancellation_reason}

💡 <b>Action:</b> DO NOT ENTER
🔍 <b>Status:</b> Wait for next opportunity

📊 <a href="{tv_url}">Review on TradingView</a>

Remember: Not every signal becomes a trade. We only take HIGH PROBABILITY setups!
"""
        return message.strip()
    
    # =========================================================================
    # TRADINGVIEW ENTRY ZONE MESSAGES (NEW!)
    # =========================================================================
    
    @staticmethod
    def format_tradingview_entry_zone(
        pair: str,
        direction: str,
        current_price: float,
        fvg_top: Optional[float] = None,
        fvg_bottom: Optional[float] = None,
        liquidity_sweep: bool = False,
        rsi_extreme: bool = False,
        volume_burst: bool = False,
        fvg_active: bool = False
    ) -> str:
        """
        Format TradingView Entry Zone alert (from webhook)
        
        This is the AUTOMATIC T-0 trigger from TradingView indicator
        """
        direction_emoji = "🟢" if direction.upper() == "LONG" else "🔴"
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
        # Build conditions checklist
        conditions = []
        if liquidity_sweep:
            conditions.append("✅ Liquidity Sweep")
        else:
            conditions.append("⬜ Liquidity Sweep")
        
        if rsi_extreme:
            conditions.append("✅ RSI Extremum")
        else:
            conditions.append("⬜ RSI Extremum")
        
        if volume_burst:
            conditions.append("✅ Volume Burst (>MA99)")
        else:
            conditions.append("⬜ Volume Burst")
        
        if fvg_active:
            conditions.append("✅ FVG Zone Active")
        else:
            conditions.append("⬜ FVG Zone")
        
        conditions_str = "\n  ".join(conditions)
        
        message = f"""
🎯 <b>ENTRY ZONE DETECTED!</b> 🎯

{direction_emoji} <b>Pair:</b> {pair}
📍 <b>Direction:</b> {direction.upper()}
💰 <b>Current Price:</b> {current_price:.5f}
"""
        
        if fvg_top and fvg_bottom:
            fvg_size = abs(fvg_top - fvg_bottom)
            fvg_pct = (fvg_size / current_price) * 100
            message += f"""
📦 <b>FVG Zone:</b>
  • Top: {fvg_top:.5f}
  • Bottom: {fvg_bottom:.5f}
  • Size: {fvg_size:.5f} ({fvg_pct:.2f}%)
"""
        
        message += f"""
🔍 <b>Entry Conditions:</b>
  {conditions_str}

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S UTC')}

📊 <a href="{tv_url}">🔴 OPEN CHART NOW!</a>

🔔 <b>This is an AUTOMATIC alert from TradingView indicator!</b>
⚡ <b>ACTION REQUIRED:</b> Check chart and enter if valid!
"""
        return message.strip()
    
    @staticmethod
    def format_fvg_filled(
        pair: str,
        direction: str,
        fvg_top: float,
        fvg_bottom: float,
        fill_price: float
    ) -> str:
        """
        Format FVG filled notification
        
        When price fills (closes) the FVG zone
        """
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
        message = f"""
🔄 <b>FVG ZONE FILLED</b>

📊 <b>Pair:</b> {pair}
📍 <b>Direction:</b> {direction.upper()}

📦 <b>Filled Zone:</b>
  • Top: {fvg_top:.5f}
  • Bottom: {fvg_bottom:.5f}
  • Fill Price: {fill_price:.5f}

💡 <b>Status:</b> Zone is now inactive (transparent on chart)

📊 <a href="{tv_url}">View on TradingView</a>
"""
        return message.strip()
    
    @staticmethod
    def format_liquidity_sweep_detected(
        pair: str,
        sweep_type: str,
        sweep_price: float,
        recent_level: float,
        current_price: float
    ) -> str:
        """
        Format Liquidity Sweep detection alert
        
        Args:
            sweep_type: "BUY" or "SELL"
            sweep_price: Price where sweep occurred
            recent_level: The liquidity level that was swept
        """
        sweep_emoji = "💎" if sweep_type.upper() == "BUY" else "💎"
        direction = "LONG opportunity" if sweep_type.upper() == "BUY" else "SHORT opportunity"
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
        message = f"""
{sweep_emoji} <b>LIQUIDITY SWEEP DETECTED</b> {sweep_emoji}

📊 <b>Pair:</b> {pair}
🎯 <b>Type:</b> {sweep_type.upper()} SWEEP

📍 <b>Details:</b>
  • Sweep Level: {sweep_price:.5f}
  • Liquidity Was: {recent_level:.5f}
  • Current Price: {current_price:.5f}

💡 <b>Implication:</b> {direction}

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S UTC')}

📊 <a href="{tv_url}">View on TradingView</a>

⚠️ Wait for RSI + Volume confirmation before entry!
"""
        return message.strip()
    
    @staticmethod
    def format_volume_burst_alert(
        pair: str,
        current_volume: float,
        average_volume: float,
        burst_multiplier: float,
        price: float,
        direction_hint: str = None
    ) -> str:
        """
        Format Volume Burst alert
        
        When volume exceeds MA99 by specified multiplier
        """
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
        message = f"""
🔥 <b>VOLUME BURST DETECTED</b> 🔥

📊 <b>Pair:</b> {pair}
💰 <b>Price:</b> {price:.5f}

📈 <b>Volume Analysis:</b>
  • Current: {current_volume:,.0f}
  • Average (MA99): {average_volume:,.0f}
  • Multiplier: {burst_multiplier:.1f}x

"""
        if direction_hint:
            message += f"💡 <b>Direction Hint:</b> {direction_hint}\n\n"
        
        message += f"""⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S UTC')}

📊 <a href="{tv_url}">View on TradingView</a>

⚠️ Volume burst often precedes significant moves!
"""
        return message.strip()
    
    # =========================================================================
    # POSITION & SYSTEM MESSAGES
    # =========================================================================
    
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
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
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

📊 <a href="{tv_url}">Monitor on TradingView</a>

💡 Keep monitoring. Let profits run!
"""
        return message.strip()
    
    @staticmethod
    def format_tp_hit(
        pair: str,
        direction: str,
        tp_level: int,
        tp_price: float,
        profit_pips: float,
        profit_usd: float,
        position_closed_pct: int,
        new_sl: Optional[float] = None
    ) -> str:
        """
        Format Take Profit hit notification
        """
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
        message = f"""
🎉 <b>TAKE PROFIT {tp_level} HIT!</b> 🎉

📊 <b>Pair:</b> {pair} ({direction.upper()})
🎯 <b>TP{tp_level} Price:</b> {tp_price:.5f}

💰 <b>Profit Locked:</b>
  • Pips: +{profit_pips:.1f}
  • USD: +${profit_usd:.2f}

📍 <b>Position:</b> {position_closed_pct}% closed
"""
        
        if new_sl:
            message += f"\n🛡️ <b>New Stop Loss:</b> {new_sl:.5f} (moved to +{tp_level-1}R)\n"
        
        message += f"""
📊 <a href="{tv_url}">View on TradingView</a>

{"🏆 Great trade! Remaining position trailing..." if tp_level < 3 else "🏆 FULL TARGET HIT! Trade closed."}
"""
        return message.strip()
    
    @staticmethod
    def format_trailing_stop_moved(
        pair: str,
        direction: str,
        old_sl: float,
        new_sl: float,
        current_price: float,
        profit_locked_pips: float,
        reason: str
    ) -> str:
        """
        Format trailing stop move notification
        """
        tv_url = MessageFormatter.get_tradingview_url(pair, "15")
        
        message = f"""
🛡️ <b>TRAILING STOP MOVED</b>

📊 <b>Pair:</b> {pair} ({direction.upper()})
💹 <b>Current Price:</b> {current_price:.5f}

🔄 <b>Stop Loss Update:</b>
  • Old SL: {old_sl:.5f}
  • New SL: {new_sl:.5f}
  • Profit Locked: +{profit_locked_pips:.1f} pips

📝 <b>Reason:</b> {reason}

📊 <a href="{tv_url}">Monitor on TradingView</a>

💡 Profits are protected. Let it run!
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
        performance_emoji = "🎉" if total_profit_loss > 0 else "📚"
        
        message = f"""
📊 <b>DAILY SUMMARY</b> 📊

📅 <b>Date:</b> {date}

📈 <b>Signals:</b> {signals_generated} generated
🎯 <b>Trades:</b> {trades_taken} taken

✅ <b>Winners:</b> {trades_won}
❌ <b>Losers:</b> {trades_lost}
📊 <b>Win Rate:</b> {win_rate:.1f}%

💰 <b>P&L:</b> ${total_profit_loss:+.2f}

{performance_emoji} {"Great day! Keep it up!" if total_profit_loss > 0 else "Learn and improve! Every loss is a lesson."}
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
    
    @staticmethod
    def format_startup_message(
        pairs: List[str],
        telegram_enabled: bool,
        redis_enabled: bool,
        dry_run: bool
    ) -> str:
        """Format system startup message"""
        pairs_str = ", ".join(pairs)
        
        message = f"""
🚀 <b>PACIFIQUETRADE INDICATOR 2.0 STARTED</b>

✅ <b>System Initialized</b>

📊 <b>Monitoring:</b> {pairs_str}

⚙️ <b>Configuration:</b>
  • Telegram: {"✅ Enabled" if telegram_enabled else "❌ Disabled"}
  • Redis Cache: {"✅ Enabled" if redis_enabled else "❌ Disabled"}
  • Mode: {"🔒 DRY RUN (safe)" if dry_run else "⚠️ LIVE TRADING"}

📅 <b>Schedule:</b>
  • T-4h: Fundamental Screening
  • T-2h: Technical Analysis
  • T-15min: Signal Generation
  • T-0: Entry Confirmation

⏰ <b>Started at:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

💡 Ready to trade! You will receive alerts automatically.
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
    
    # Test 2: Ready to Trade Alert (with TradingView links!)
    print("Test 2: Ready to Trade Alert (with TradingView links)\n")
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
    
    # Test 3: TradingView Entry Zone (NEW!)
    print("Test 3: TradingView Entry Zone Alert (NEW!)\n")
    msg3 = formatter.format_tradingview_entry_zone(
        pair="GBP/USD",
        direction="LONG",
        current_price=1.2695,
        fvg_top=1.2710,
        fvg_bottom=1.2690,
        liquidity_sweep=True,
        rsi_extreme=True,
        volume_burst=True,
        fvg_active=True
    )
    print(msg3)
    print("\n" + "-"*60 + "\n")
    
    # Test 4: Liquidity Sweep Alert (NEW!)
    print("Test 4: Liquidity Sweep Alert (NEW!)\n")
    msg4 = formatter.format_liquidity_sweep_detected(
        pair="EUR/USD",
        sweep_type="BUY",
        sweep_price=1.0845,
        recent_level=1.0850,
        current_price=1.0855
    )
    print(msg4)
    print("\n" + "-"*60 + "\n")
    
    # Test 5: TP Hit Alert (NEW!)
    print("Test 5: Take Profit Hit Alert (NEW!)\n")
    msg5 = formatter.format_tp_hit(
        pair="GBP/USD",
        direction="LONG",
        tp_level=1,
        tp_price=1.2750,
        profit_pips=50,
        profit_usd=100.0,
        position_closed_pct=33,
        new_sl=1.2700
    )
    print(msg5)
    print("\n" + "-"*60 + "\n")
    
    # Test 6: Startup Message (NEW!)
    print("Test 6: Startup Message (NEW!)\n")
    msg6 = formatter.format_startup_message(
        pairs=["GBP/USD", "EUR/USD", "USD/JPY"],
        telegram_enabled=True,
        redis_enabled=False,
        dry_run=True
    )
    print(msg6)
    
    # Test TradingView URL generation
    print("\n" + "-"*60 + "\n")
    print("Test 7: TradingView URL Generation\n")
    
    url = formatter.get_tradingview_url("GBP/USD", "15")
    print(f"GBP/USD M15: {url}")
    
    all_urls = formatter.get_tradingview_urls_all_timeframes("EUR/USD")
    print("\nEUR/USD all timeframes:")
    for tf, url in all_urls.items():
        print(f"  {tf}: {url}")
    
    print("\n" + "="*60)
    print("✅ MESSAGE FORMATTER TEST COMPLETE!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()