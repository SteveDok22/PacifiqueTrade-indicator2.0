"""
Position Monitor - Real-time position tracking

Monitors open positions and sends updates to Telegram:
- TP1 hit → Move to breakeven
- TP2 hit → Close 33%
- TP3 hit → Trail stop
- Stop loss updates
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import CurrencyPair
from data import MarketDataFetcher
from risk import TrailingStopManager
from notification import TelegramNotifier


logger = logging.getLogger(__name__)


class PositionMonitor:
    """
    Real-time Position Monitor
    
    Tracks active positions and sends Telegram updates on:
    - TP levels hit
    - Stop loss movements
    - Position closed
    """
    
    def __init__(self):
        self.market_data = MarketDataFetcher()
        self.trailing_manager = TrailingStopManager()
        self.telegram = TelegramNotifier()
        
        # Active positions storage
        self.active_positions: Dict[str, Dict] = {}
    
    def add_position(
        self,
        pair: CurrencyPair,
        direction: str,
        entry_price: float,
        stop_loss: float,
        tp1: float,
        tp2: float,
        tp3: float,
        position_size_lots: float
    ):
        """Add position to monitoring"""
        
        position_key = f"{pair.value}_{datetime.now().timestamp()}"
        
        self.active_positions[position_key] = {
            'pair': pair,
            'direction': direction,
            'entry_price': entry_price,
            'current_stop': stop_loss,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'tp1_hit': False,
            'tp2_hit': False,
            'tp3_hit': False,
            'position_size_lots': position_size_lots,
            'opened_at': datetime.now(),
            'updates_sent': []
        }
        
        logger.info(f"Added position to monitor: {pair.value} {direction}")
    
    async def check_positions(self):
        """Check all active positions"""
        
        if not self.active_positions:
            return
        
        for position_key, position in list(self.active_positions.items()):
            try:
                await self._check_single_position(position_key, position)
            except Exception as e:
                logger.error(f"Error checking position {position_key}: {e}")
    
    async def _check_single_position(self, position_key: str, position: Dict):
        """Check a single position"""
        
        pair = position['pair']
        direction = position['direction']
        entry = position['entry_price']
        current_stop = position['current_stop']
        
        # Get current price
        current_price = self.market_data.get_current_price(pair)
        
        # Calculate profit
        if direction == 'long':
            profit_pips = (current_price - entry) / 0.0001
            profit_pct = (current_price - entry) / entry * 100
        else:
            profit_pips = (entry - current_price) / 0.0001
            profit_pct = (entry - current_price) / entry * 100
        
        # Calculate profit in USD (simplified)
        profit_usd = profit_pips * 10 * position['position_size_lots']  # $10 per pip per lot
        
        # Calculate R-multiple
        r_multiple = self.trailing_manager.calculate_r_multiple(
            direction, entry, current_price, current_stop
        )
        
        # Check TP1 hit
        if not position['tp1_hit']:
            tp1_hit = (direction == 'long' and current_price >= position['tp1']) or \
                      (direction == 'short' and current_price <= position['tp1'])
            
            if tp1_hit:
                position['tp1_hit'] = True
                await self._send_tp_hit_alert(
                    position, 1, current_price, profit_pips, profit_usd, r_multiple
                )
                
                # Move stop to breakeven
                position['current_stop'] = entry
        
        # Check TP2 hit
        if position['tp1_hit'] and not position['tp2_hit']:
            tp2_hit = (direction == 'long' and current_price >= position['tp2']) or \
                      (direction == 'short' and current_price <= position['tp2'])
            
            if tp2_hit:
                position['tp2_hit'] = True
                await self._send_tp_hit_alert(
                    position, 2, current_price, profit_pips, profit_usd, r_multiple
                )
                
                # Move stop to +1R
                stop_distance = abs(entry - position['current_stop'])
                if direction == 'long':
                    position['current_stop'] = entry + stop_distance
                else:
                    position['current_stop'] = entry - stop_distance
        
        # Check TP3 or trail stop
        if position['tp2_hit']:
            tp3_hit = (direction == 'long' and current_price >= position['tp3']) or \
                      (direction == 'short' and current_price <= position['tp3'])
            
            if tp3_hit and not position['tp3_hit']:
                position['tp3_hit'] = True
                await self._send_tp_hit_alert(
                    position, 3, current_price, profit_pips, profit_usd, r_multiple
                )
                
                # Close position
                del self.active_positions[position_key]
                await self._send_position_closed_alert(position, profit_usd)
            
            # Check trailing stop updates
            else:
                update = self.trailing_manager.should_update_stop(
                    direction, entry, current_price, current_stop, r_multiple
                )
                
                if update:
                    position['current_stop'] = update.new_stop
                    await self._send_stop_update_alert(position, update, current_price)
        
        # Check if stop loss hit
        stop_hit = (direction == 'long' and current_price <= current_stop) or \
                   (direction == 'short' and current_price >= current_stop)
        
        if stop_hit:
            del self.active_positions[position_key]
            await self._send_stop_hit_alert(position, current_price, profit_usd)

    async def _send_tp_hit_alert(
        self,
        position: Dict,
        tp_level: int,
        current_price: float,
        profit_pips: float,
        profit_usd: float,
        r_multiple: float
    ):
        """Send TP hit alert"""
        
        actions = {
            1: "Moved stop to BREAKEVEN (33% position)",
            2: "Closed 33% position at +2R, trailing remaining 34%",
            3: "All TPs hit! Position fully closed"
        }
        
        message = f"""
🎯 <b>TP{tp_level} HIT!</b> 🎯

📊 <b>Pair:</b> {position['pair'].value}
📍 <b>Direction:</b> {position['direction'].upper()}

💰 <b>Status:</b>
  • Entry: {position['entry_price']:.5f}
  • Current: {current_price:.5f}
  • TP{tp_level}: {position[f'tp{tp_level}']:.5f}

📈 <b>Profit:</b>
  • Pips: +{profit_pips:.1f}
  • USD: +${profit_usd:.2f}
  • R-Multiple: +{r_multiple:.1f}R

✅ <b>Action:</b> {actions[tp_level]}

{"🎉 Position fully closed with profit!" if tp_level == 3 else "💡 Let remaining position run!"}
"""
        
        await self.telegram.send_message(message.strip(), parse_mode='HTML')
    
    async def _send_stop_update_alert(
        self,
        position: Dict,
        update,
        current_price: float
    ):
        """Send trailing stop update alert"""
        
        message = f"""
📊 <b>TRAILING STOP UPDATED</b> 📊

📈 <b>Pair:</b> {position['pair'].value}

✅ <b>Update:</b>
  • Old Stop: {update.old_stop:.5f}
  • New Stop: {update.new_stop:.5f}
  • Current Price: {current_price:.5f}

💡 <b>Reason:</b> {update.reason}

🔒 Profit locked in: {update.profit_locked:.5f} points
""" 
        await self.telegram.send_message(message.strip(), parse_mode='HTML')
    
    async def _send_stop_hit_alert(
        self,
        position: Dict,
        exit_price: float,
        profit_usd: float
    ):
        """Send stop loss hit alert"""
        
        result_emoji = "✅" if profit_usd > 0 else "❌"
        result_text = "PROFIT" if profit_usd > 0 else "LOSS"
        
        message = f"""
{result_emoji} <b>STOP HIT - POSITION CLOSED</b>

📊 <b>Pair:</b> {position['pair'].value}
📍 <b>Direction:</b> {position['direction'].upper()}

💰 <b>Final Result:</b>
  • Entry: {position['entry_price']:.5f}
  • Exit: {exit_price:.5f}
  • P&L: ${profit_usd:+.2f}

📊 <b>Status:</b> {result_text}

{"🎉 Trade successful!" if profit_usd > 0 else "📚 Review and learn from this trade"}
"""
        
        await self.telegram.send_message(message.strip(), parse_mode='HTML')
    
    async def _send_position_closed_alert(self, position: Dict, profit_usd: float):
        """Send position fully closed alert"""
        
        duration = datetime.now() - position['opened_at']
        hours = duration.total_seconds() / 3600
        
        message = f"""
🎉 <b>POSITION FULLY CLOSED</b> 🎉

📊 <b>Pair:</b> {position['pair'].value}
📍 <b>Direction:</b> {position['direction'].upper()}

✅ <b>All TPs Hit:</b>
  • TP1: ✅ (Moved to BE)
  • TP2: ✅ (Closed 33%)
  • TP3: ✅ (Closed 67%)

💰 <b>Total Profit:</b> ${profit_usd:+.2f}

⏱️ <b>Duration:</b> {hours:.1f} hours

🎯 <b>Perfect execution!</b> Well done!
"""
        
        await self.telegram.send_message(message.strip(), parse_mode='HTML')


async def monitor_loop(monitor: PositionMonitor, interval: int = 60):
    """Main monitoring loop"""
    logger.info(f"Starting position monitor (check every {interval}s)")
    
    while True:
        try:
            await monitor.check_positions()
            await asyncio.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Monitor error: {e}", exc_info=True)
            await asyncio.sleep(interval)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("📊 POSITION MONITOR TEST")
    print("="*60 + "\n")
    
    from core.enums import CurrencyPair
    
    monitor = PositionMonitor()
    
    # Add test position
    monitor.add_position(
        pair=CurrencyPair.GBP_USD,
        direction='long',
        entry_price=1.2700,
        stop_loss=1.2650,
        tp1=1.2750,
        tp2=1.2800,
        tp3=1.2850,
        position_size_lots=0.2
    )
    
    print("✅ Test position added")
    print(f"Active positions: {len(monitor.active_positions)}")
    print("\nStarting monitor loop...")
    print("Press Ctrl+C to stop\n")
    
    # Run monitor
    asyncio.run(monitor_loop(monitor, interval=10))