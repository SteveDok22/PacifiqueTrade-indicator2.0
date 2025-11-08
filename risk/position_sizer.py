"""
Position Sizing Module

Calculates optimal position size based on:
- Account balance
- Risk percentage (default: 1%)
- Stop loss distance
- Leverage (if applicable)

Ensures proper risk management for every trade.
"""

from dataclasses import dataclass
from typing import Optional
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import CurrencyPair
from core.exceptions import RiskManagementError
from core.config import config


logger = logging.getLogger(__name__)


@dataclass
class PositionSize:
    """Position size calculation result"""
    pair: CurrencyPair
    account_balance: float
    risk_percentage: float
    risk_amount: float
    entry_price: float
    stop_loss: float
    stop_distance_pips: float
    position_size_lots: float
    position_size_units: float
    pip_value: float
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'pair': self.pair.value,
            'account_balance': round(self.account_balance, 2),
            'risk_percentage': self.risk_percentage,
            'risk_amount': round(self.risk_amount, 2),
            'entry_price': round(self.entry_price, 5),
            'stop_loss': round(self.stop_loss, 5),
            'stop_distance_pips': round(self.stop_distance_pips, 1),
            'position_size_lots': round(self.position_size_lots, 2),
            'position_size_units': round(self.position_size_units, 0),
            'pip_value': round(self.pip_value, 2)
        }


class PositionSizer:
    """
    Position Size Calculator
    
    Calculates the optimal position size to risk exactly X% of account.
    
    Formula:
    Risk Amount = Account Balance × Risk %
    Stop Distance (pips) = |Entry - Stop Loss| / Pip Size
    Position Size = Risk Amount / (Stop Distance × Pip Value)
    
    Example:
    - Account: $10,000
    - Risk: 1% = $100
    - Entry: 1.2700
    - Stop: 1.2650
    - Distance: 50 pips
    - Pip Value: $10 (for 1 standard lot)
    - Position: $100 / (50 × $10) = 0.2 lots
    """
    
    def __init__(
        self,
        account_balance: Optional[float] = None,
        risk_percentage: Optional[float] = None,
        leverage: Optional[int] = None
    ):
        """
        Initialize Position Sizer
        
        Args:
            account_balance: Account balance (default: from config)
            risk_percentage: Risk % per trade (default: from config)
            leverage: Leverage multiplier (default: from config)
        """
        self.account_balance = account_balance or config.ACCOUNT_BALANCE
        self.risk_percentage = risk_percentage or config.RISK_PERCENTAGE
        self.leverage = leverage or config.LEVERAGE
        
        logger.info(f"Position Sizer initialized: "
                   f"Balance=${self.account_balance:,.2f}, "
                   f"Risk={self.risk_percentage}%, "
                   f"Leverage={self.leverage}:1")