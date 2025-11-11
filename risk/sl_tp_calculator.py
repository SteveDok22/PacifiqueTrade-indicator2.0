"""
Stop Loss & Take Profit Calculator

Calculates SL and TP levels with 3-part position management:
- Part 1 (33%): Move to breakeven at +1R
- Part 2 (33%): Close at +2R
- Part 3 (34%): Trail to +3R or more

Ensures minimum 1:3 risk-reward ratio.
"""

from dataclasses import dataclass
from typing import Tuple, Optional, List
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import CurrencyPair
from core.exceptions import RiskManagementError
from core.config import config
from analysis.liquidity_zones import LiquidityZone


logger = logging.getLogger(__name__)


@dataclass
class SLTPLevels:
    """Stop Loss and Take Profit levels"""
    pair: CurrencyPair
    direction: str  # 'long' or 'short'
    entry_price: float
    
    # Stop Loss (3 parts)
    stop_loss: float
    stop_loss_pips: float
    
    # Take Profit levels
    take_profit_1: float  # +1R (move SL to breakeven)
    take_profit_2: float  # +2R
    take_profit_3: float  # +3R or more
    
    # R-multiples
    r_multiple_1: float
    r_multiple_2: float
    r_multiple_3: float
    
    # Position splits (percentages)
    position_split: Tuple[int, int, int] = (33, 33, 34)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'pair': self.pair.value,
            'direction': self.direction,
            'entry_price': round(self.entry_price, 5),
            'stop_loss': round(self.stop_loss, 5),
            'stop_loss_pips': round(self.stop_loss_pips, 1),
            'take_profit_1': round(self.take_profit_1, 5),
            'take_profit_2': round(self.take_profit_2, 5),
            'take_profit_3': round(self.take_profit_3, 5),
            'r_multiple_1': round(self.r_multiple_1, 1),
            'r_multiple_2': round(self.r_multiple_2, 1),
            'r_multiple_3': round(self.r_multiple_3, 1),
            'position_split': self.position_split
        }


class SLTPCalculator:
    """
    Stop Loss and Take Profit Calculator
    
    Strategy:
    1. Place initial stop loss based on liquidity zones
    2. Set 3 take profit levels
    3. Manage position in 3 parts:
       - Part 1: Move SL to breakeven when TP1 hit
       - Part 2: Close at TP2
       - Part 3: Trail stop to TP3 or beyond
    
    Minimum Risk-Reward: 1:3 (config.MIN_R_MULTIPLE)
    """
    
    def __init__(self):
        self.min_r_multiple = config.MIN_R_MULTIPLE