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