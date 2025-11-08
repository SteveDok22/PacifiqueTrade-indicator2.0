"""
Risk Management module for PacifiqueTrade Indicator 2.0

This module handles all risk management and position sizing:
- Position size calculation (1% risk per trade)
- Stop Loss and Take Profit calculation (3-part system)
- Trailing stop management
- Risk-reward ratio validation
"""

from .position_sizer import PositionSizer, PositionSize
from .sl_tp_calculator import SLTPCalculator, SLTPLevels
from .trailing_stop import TrailingStopManager, TrailingStopUpdate

__all__ = [
    'PositionSizer',
    'PositionSize',
    'SLTPCalculator',
    'SLTPLevels',
    'TrailingStopManager',
    'TrailingStopUpdate',
]

__version__ = '2.0.0'