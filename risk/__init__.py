"""
Risk Management module for PacifiqueTrade Indicator 2.0

This module handles all risk management and position sizing:
- Position size calculation (1% risk per trade)
- Stop Loss and Take Profit calculation (3-part system)
- Trailing stop management
- Risk-reward ratio validation
- Position monitoring (real-time tracking)
"""

from .position_sizer import PositionSizer, PositionSize
from .sl_tp_calculator import SLTPCalculator, SLTPLevels
from .trailing_stop import TrailingStopManager, TrailingStopUpdate

# Position Monitor is optional (requires async)
try:
    from .position_monitor import PositionMonitor, monitor_loop
    POSITION_MONITOR_AVAILABLE = True
except ImportError:
    POSITION_MONITOR_AVAILABLE = False
    PositionMonitor = None
    monitor_loop = None

__all__ = [
    'PositionSizer',
    'PositionSize',
    'SLTPCalculator',
    'SLTPLevels',
    'TrailingStopManager',
    'TrailingStopUpdate',
    'PositionMonitor',
    'monitor_loop',
    'POSITION_MONITOR_AVAILABLE',
]

__version__ = '2.0.0'