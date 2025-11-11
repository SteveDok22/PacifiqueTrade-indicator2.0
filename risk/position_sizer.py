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
    
    def calculate_position_size(
        self,
        pair: CurrencyPair,
        entry_price: float,
        stop_loss: float
    ) -> PositionSize:
        """
        Calculate optimal position size
        
        Args:
            pair: Currency pair
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            PositionSize object with all calculations
            
        Raises:
            RiskManagementError: If calculation fails
        """
        try:
            # Validate inputs
            if entry_price <= 0 or stop_loss <= 0:
                raise RiskManagementError(
                    "Entry price and stop loss must be positive",
                    account_balance=self.account_balance
                )
            
            if entry_price == stop_loss:
                raise RiskManagementError(
                    "Entry price cannot equal stop loss",
                    account_balance=self.account_balance
                )
            
            # Calculate risk amount
            risk_amount = self.account_balance * (self.risk_percentage / 100)
            
            logger.debug(f"Risk amount: ${risk_amount:.2f} "
                        f"({self.risk_percentage}% of ${self.account_balance:,.2f})")
            
            # Get pip value for this pair
            pip_size = config.PAIR_CONFIG[pair.value]['pip_value']
            
            # Calculate stop distance in pips
            stop_distance = abs(entry_price - stop_loss)
            stop_distance_pips = stop_distance / pip_size
            
            logger.debug(f"Stop distance: {stop_distance_pips:.1f} pips "
                        f"({abs(entry_price - stop_loss):.5f} points)")
            
            # Calculate pip value per standard lot (100,000 units)
            # For most pairs: pip value = (0.0001 / exchange rate) × 100,000
            # Simplified: $10 per pip for EUR/USD, GBP/USD
            # For JPY pairs: $9.16 per pip (approximately)
            
            if pair.quote_currency == 'JPY':
                pip_value_per_lot = 9.16  # Approximate for JPY pairs
            else:
                pip_value_per_lot = 10.0  # Standard for USD pairs
            
            # Calculate position size in lots
            # Position Size = Risk Amount / (Stop Distance Pips × Pip Value)
            position_size_lots = risk_amount / (stop_distance_pips * pip_value_per_lot)
            
            # Calculate position size in units
            position_size_units = position_size_lots * 100000
            
            # Apply leverage constraint (optional)
            max_position = (self.account_balance * self.leverage) / entry_price
            if position_size_units > max_position:
                logger.warning(f"Position size exceeds leverage limit. "
                             f"Capping at {max_position:.0f} units")
                position_size_units = max_position
                position_size_lots = position_size_units / 100000
            
            logger.info(f"Calculated position size: {position_size_lots:.2f} lots "
                       f"({position_size_units:.0f} units)")
            
            result = PositionSize(
                pair=pair,
                account_balance=self.account_balance,
                risk_percentage=self.risk_percentage,
                risk_amount=risk_amount,
                entry_price=entry_price,
                stop_loss=stop_loss,
                stop_distance_pips=stop_distance_pips,
                position_size_lots=position_size_lots,
                position_size_units=position_size_units,
                pip_value=pip_value_per_lot
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Position size calculation failed: {e}")
            raise RiskManagementError(
                f"Failed to calculate position size: {e}",
                account_balance=self.account_balance
            )
    
    def validate_position_size(
        self,
        position_size: PositionSize,
        min_lot_size: float = 0.01,
        max_lot_size: float = 100.0
    ) -> bool:
        """
        Validate if position size is within acceptable limits
        
        Args:
            position_size: Calculated position size
            min_lot_size: Minimum allowed lot size
            max_lot_size: Maximum allowed lot size
            
        Returns:
            True if valid, False otherwise
        """
        lots = position_size.position_size_lots
        
        if lots < min_lot_size:
            logger.warning(f"Position size {lots:.2f} lots below minimum {min_lot_size}")
            return False
        
        if lots > max_lot_size:
            logger.warning(f"Position size {lots:.2f} lots above maximum {max_lot_size}")
            return False
        
        # Check if risk amount is reasonable
        if position_size.risk_amount > self.account_balance * 0.05:
            logger.warning(f"Risk amount ${position_size.risk_amount:.2f} "
                         f"exceeds 5% of account")
            return False
        
        return True
    
    def calculate_max_loss(
        self,
        position_size: PositionSize
    ) -> float:
        """
        Calculate maximum loss if stop loss is hit
        
        Returns:
            Loss amount in dollars
        """
        return position_size.stop_distance_pips * position_size.pip_value * position_size.position_size_lots
    
    def calculate_required_margin(
        self,
        position_size: PositionSize
    ) -> float:
        """
        Calculate required margin for the position
        
        Returns:
            Required margin in dollars
        """
        position_value = position_size.position_size_units * position_size.entry_price
        required_margin = position_value / self.leverage
        return required_margin
    
    def update_account_balance(self, new_balance: float):
        """Update account balance"""
        old_balance = self.account_balance
        self.account_balance = new_balance
        logger.info(f"Account balance updated: ${old_balance:,.2f} → ${new_balance:,.2f}")


def main():
    """Test the Position Sizer"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("POSITION SIZER TEST")
    print("="*60 + "\n")
    
    try:
        # Initialize with default config values
        sizer = PositionSizer()
        
        # Test 1: Calculate position for GBP/USD
        print("Test 1: Position size for GBP/USD long trade\n")
        print("Scenario:")
        print("  Account: $10,000")
        print("  Risk: 1%")
        print("  Entry: 1.2700")
        print("  Stop Loss: 1.2650")
        print("  Distance: 50 pips\n")
        
        position = sizer.calculate_position_size(
            pair=CurrencyPair.GBP_USD,
            entry_price=1.2700,
            stop_loss=1.2650
        )
        
        print("✅ Position Calculation:")
        print(f"  Risk Amount: ${position.risk_amount:.2f}")
        print(f"  Stop Distance: {position.stop_distance_pips:.1f} pips")
        print(f"  Position Size: {position.position_size_lots:.2f} lots")
        print(f"  Position Units: {position.position_size_units:,.0f} units")
        print(f"  Pip Value: ${position.pip_value:.2f} per lot\n")
        
        # Validate
        is_valid = sizer.validate_position_size(position)
        print(f"  Valid: {'✅ YES' if is_valid else '❌ NO'}\n")
        
        # Calculate actual loss if SL hit
        max_loss = sizer.calculate_max_loss(position)
        print(f"  Max Loss if SL hit: ${max_loss:.2f}")
        
        # Required margin
        margin = sizer.calculate_required_margin(position)
        print(f"  Required Margin: ${margin:.2f}\n")
        
        # Test 2: Different stop distance
        print("-"*60)
        print("Test 2: Tighter stop (20 pips)\n")
        
        position2 = sizer.calculate_position_size(
            pair=CurrencyPair.EUR_USD,
            entry_price=1.0850,
            stop_loss=1.0830
        )
        
        print(f"✅ Position Size: {position2.position_size_lots:.2f} lots")
        print(f"   (Notice: tighter stop = larger position size)\n")
        
        # Test 3: USD/JPY (different pip calculation)
        print("-"*60)
        print("Test 3: USD/JPY trade\n")
        
        position3 = sizer.calculate_position_size(
            pair=CurrencyPair.USD_JPY,
            entry_price=149.50,
            stop_loss=149.00
        )
        
        print(f"✅ Position Size: {position3.position_size_lots:.2f} lots")
        print(f"   Stop Distance: {position3.stop_distance_pips:.1f} pips")
        print(f"   Risk Amount: ${position3.risk_amount:.2f}\n")
        
        print("="*60)
        print("✅ POSITION SIZER TEST COMPLETE!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())    