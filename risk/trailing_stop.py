"""
Trailing Stop Manager

Manages dynamic trailing stop loss as price moves in our favor.

Strategy:
- Part 1 (33%): Move to breakeven when +1R hit
- Part 2 (33%): Already closed at +2R
- Part 3 (34%): Trail by EMA21 or key levels

Protects profits while letting winners run.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import CurrencyPair
from core.exceptions import RiskManagementError


logger = logging.getLogger(__name__)


@dataclass
class TrailingStopUpdate:
    """Trailing stop update event"""
    pair: CurrencyPair
    direction: str
    current_price: float
    old_stop: float
    new_stop: float
    reason: str
    timestamp: datetime
    profit_locked: float  # Profit locked in pips
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'pair': self.pair.value,
            'direction': self.direction,
            'current_price': round(self.current_price, 5),
            'old_stop': round(self.old_stop, 5),
            'new_stop': round(self.new_stop, 5),
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat(),
            'profit_locked': round(self.profit_locked, 1)
        }


class TrailingStopManager:
    """
    Trailing Stop Loss Manager
    
    Manages stop loss updates as trade moves in profit:
    
    1. At +1R: Move SL to breakeven (no loss possible)
    2. At +2R: SL to +1R (lock minimum profit)
    3. Beyond +2R: Trail by EMA21 or recent swing points
    
    Never moves stop loss against us (only in profit direction).
    """
    
     def __init__(self):
        pass
    
    def should_update_stop(
        self,
        direction: str,
        entry_price: float,
        current_price: float,
        current_stop: float,
        r_achieved: float,
        ema21: Optional[float] = None
    ) -> Optional[TrailingStopUpdate]:
        """
        Check if stop loss should be updated
        
        Args:
            direction: 'long' or 'short'
            entry_price: Original entry price
            current_price: Current market price
            current_stop: Current stop loss level
            r_achieved: R-multiple achieved (e.g., 1.5 = +1.5R)
            ema21: Optional EMA21 value for trailing
            
        Returns:
            TrailingStopUpdate if stop should be moved, None otherwise
        """
        logger.debug(f"Checking trailing stop: direction={direction}, "
                    f"price={current_price:.5f}, R={r_achieved:.1f}")
        
        # Rule 1: At +1R, move to breakeven
        if 0.9 <= r_achieved < 1.5:
            new_stop = self._move_to_breakeven(
                direction, entry_price, current_stop
            )
            
            if new_stop and new_stop != current_stop:
                return self._create_update(
                    direction, current_price, current_stop, new_stop,
                    "Moved to breakeven at +1R", entry_price
                )
        
        # Rule 2: At +2R, move SL to +1R
        elif 1.5 <= r_achieved < 2.5:
            new_stop = self._move_to_plus_1r(
                direction, entry_price, current_stop
            )
            
            if new_stop and new_stop != current_stop:
                return self._create_update(
                    direction, current_price, current_stop, new_stop,
                    "Moved to +1R at +2R achieved", entry_price
                )
        
        # Rule 3: Beyond +2R, trail by EMA21 or swing points
        elif r_achieved >= 2.5:
            new_stop = self._trail_by_ema_or_swing(
                direction, current_price, current_stop, ema21
            )
            
            if new_stop and new_stop != current_stop:
                return self._create_update(
                    direction, current_price, current_stop, new_stop,
                    "Trailing stop by EMA21/swing", entry_price
                )
        
        return None
    
    def _move_to_breakeven(
        self,
        direction: str,
        entry_price: float,
        current_stop: float
    ) -> Optional[float]:
        """Move stop to breakeven (entry price)"""
        
        if direction == 'long':
            # Only move if current stop is below entry
            if current_stop < entry_price:
                logger.info(f"Moving SL to breakeven: {current_stop:.5f} → {entry_price:.5f}")
                return entry_price
        else:  # short
            # Only move if current stop is above entry
            if current_stop > entry_price:
                logger.info(f"Moving SL to breakeven: {current_stop:.5f} → {entry_price:.5f}")
                return entry_price
        
        return None
    
    def _move_to_plus_1r(
        self,
        direction: str,
        entry_price: float,
        current_stop: float
    ) -> Optional[float]:
        """Move stop to +1R (lock in minimum profit)"""
        
        # Calculate +1R level
        stop_distance = abs(entry_price - current_stop)
        
        if direction == 'long':
            plus_1r = entry_price + stop_distance
            
            if current_stop < plus_1r:
                logger.info(f"Moving SL to +1R: {current_stop:.5f} → {plus_1r:.5f}")
                return plus_1r
        else:  # short
            plus_1r = entry_price - stop_distance
            
            if current_stop > plus_1r:
                logger.info(f"Moving SL to +1R: {current_stop:.5f} → {plus_1r:.5f}")
                return plus_1r
        
        return None
    
    def _trail_by_ema_or_swing(
        self,
        direction: str,
        current_price: float,
        current_stop: float,
        ema21: Optional[float]
    ) -> Optional[float]:
        """
        Trail stop by EMA21 or use percentage-based trailing
        
        If EMA21 available: Use it
        Else: Trail by 1.5% from current price
        """
        if ema21:
            # Use EMA21 as trailing stop
            if direction == 'long':
                # Place stop below EMA21
                new_stop = ema21 * 0.998  # 0.2% below EMA21
                
                # Only move if it's better than current
                if new_stop > current_stop and new_stop < current_price:
                    logger.info(f"Trailing by EMA21: {current_stop:.5f} → {new_stop:.5f}")
                    return new_stop
            
            else:  # short
                # Place stop above EMA21
                new_stop = ema21 * 1.002  # 0.2% above EMA21
                
                if new_stop < current_stop and new_stop > current_price:
                    logger.info(f"Trailing by EMA21: {current_stop:.5f} → {new_stop:.5f}")
                    return new_stop
        
        else:
            # Percentage-based trailing (1.5% from current price)
            trail_pct = 0.015
            
            if direction == 'long':
                new_stop = current_price * (1 - trail_pct)
                
                if new_stop > current_stop:
                    logger.info(f"Trailing by {trail_pct*100}%: {current_stop:.5f} → {new_stop:.5f}")
                    return new_stop
            
            else:  # short
                new_stop = current_price * (1 + trail_pct)
                
                if new_stop < current_stop:
                    logger.info(f"Trailing by {trail_pct*100}%: {current_stop:.5f} → {new_stop:.5f}")
                    return new_stop
        
        return None