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
        
    def calculate_sl_tp(
        self,
        pair: CurrencyPair,
        direction: str,
        entry_price: float,
        liquidity_zones: Optional[List[LiquidityZone]] = None,
        custom_sl: Optional[float] = None
    ) -> SLTPLevels:
        """
        Calculate Stop Loss and Take Profit levels
        
        Args:
            pair: Currency pair
            direction: 'long' or 'short'
            entry_price: Entry price
            liquidity_zones: Optional liquidity zones for SL placement
            custom_sl: Optional custom stop loss level
            
        Returns:
            SLTPLevels object
        """
        logger.info(f"Calculating SL/TP for {pair.value} {direction} @ {entry_price:.5f}")
        
        try:
            # Calculate stop loss
            if custom_sl:
                stop_loss = custom_sl
            else:
                stop_loss = self._calculate_stop_loss(
                    pair, direction, entry_price, liquidity_zones
                )
            
            # Validate stop loss
            self._validate_stop_loss(direction, entry_price, stop_loss)
            
            # Calculate pip size and stop distance
            pip_size = config.PAIR_CONFIG[pair.value]['pip_value']
            stop_distance = abs(entry_price - stop_loss)
            stop_distance_pips = stop_distance / pip_size
            
            logger.debug(f"Stop loss: {stop_loss:.5f} ({stop_distance_pips:.1f} pips)")
            
            # Calculate take profit levels
            tp1, tp2, tp3 = self._calculate_take_profits(
                direction, entry_price, stop_loss, stop_distance
            )
            
            # Calculate R-multiples
            r1 = abs(tp1 - entry_price) / stop_distance
            r2 = abs(tp2 - entry_price) / stop_distance
            r3 = abs(tp3 - entry_price) / stop_distance
            
            logger.info(f"Take profits: TP1={tp1:.5f} (+{r1:.1f}R), "
                       f"TP2={tp2:.5f} (+{r2:.1f}R), "
                       f"TP3={tp3:.5f} (+{r3:.1f}R)")
            
            # Get position splits from config
            splits = (config.SL_PART1, config.SL_PART2, config.SL_PART3)
            
            levels = SLTPLevels(
                pair=pair,
                direction=direction,
                entry_price=entry_price,
                stop_loss=stop_loss,
                stop_loss_pips=stop_distance_pips,
                take_profit_1=tp1,
                take_profit_2=tp2,
                take_profit_3=tp3,
                r_multiple_1=r1,
                r_multiple_2=r2,
                r_multiple_3=r3,
                position_split=splits
            )
            
            return levels
            
        except Exception as e:
            logger.error(f"SL/TP calculation failed: {e}")
            raise RiskManagementError(
                f"Failed to calculate SL/TP: {e}",
                account_balance=None
            )
    
    def _calculate_stop_loss(
        self,
        pair: CurrencyPair,
        direction: str,
        entry_price: float,
        liquidity_zones: Optional[List[LiquidityZone]]
    ) -> float:
        """
        Calculate stop loss based on liquidity zones
        
        Strategy:
        - For longs: Place SL below nearest support zone
        - For shorts: Place SL above nearest resistance zone
        - If no zones: Use 1.5% default
        """
        pip_size = config.PAIR_CONFIG[pair.value]['pip_value']
        
        if liquidity_zones:
            # Find nearest zone in opposite direction
            if direction == 'long':
                # Find support zones below entry
                support_zones = [
                    z for z in liquidity_zones
                    if z.price_level < entry_price
                ]
                
                if support_zones:
                    # Place SL below nearest support
                    nearest_support = max(support_zones, key=lambda z: z.price_level)
                    stop_loss = nearest_support.price_range[0] - (5 * pip_size)
                    logger.debug(f"SL placed below support zone @ {nearest_support.price_level:.5f}")
                    return stop_loss
            
            else:  # short
                # Find resistance zones above entry
                resistance_zones = [
                    z for z in liquidity_zones
                    if z.price_level > entry_price
                ]
                
                if resistance_zones:
                    # Place SL above nearest resistance
                    nearest_resistance = min(resistance_zones, key=lambda z: z.price_level)
                    stop_loss = nearest_resistance.price_range[1] + (5 * pip_size)
                    logger.debug(f"SL placed above resistance zone @ {nearest_resistance.price_level:.5f}")
                    return stop_loss
        
        # Default: 1.5% stop loss
        default_sl_pct = 0.015
        
        if direction == 'long':
            stop_loss = entry_price * (1 - default_sl_pct)
        else:
            stop_loss = entry_price * (1 + default_sl_pct)
        
        logger.debug(f"Using default SL: {default_sl_pct * 100}%")
        return stop_loss
    
    def _validate_stop_loss(
        self,
        direction: str,
        entry_price: float,
        stop_loss: float
    ):
        """Validate stop loss placement"""
        if direction == 'long' and stop_loss >= entry_price:
            raise RiskManagementError(
                "Stop loss must be below entry for long trades",
                details={'entry': entry_price, 'sl': stop_loss}
            )
        
        if direction == 'short' and stop_loss <= entry_price:
            raise RiskManagementError(
                "Stop loss must be above entry for short trades",
                details={'entry': entry_price, 'sl': stop_loss}
            )
        
        # Check if stop is not too tight or too wide
        stop_distance_pct = abs(entry_price - stop_loss) / entry_price
        
        if stop_distance_pct < 0.002:  # Less than 0.2%
            logger.warning(f"Stop loss very tight: {stop_distance_pct * 100:.2f}%")
        
        if stop_distance_pct > 0.05:  # More than 5%
            logger.warning(f"Stop loss very wide: {stop_distance_pct * 100:.2f}%")
    
    def _calculate_take_profits(
        self,
        direction: str,
        entry_price: float,
        stop_loss: float,
        stop_distance: float
    ) -> Tuple[float, float, float]:
        """
        Calculate 3 take profit levels
        
        TP1: +1R (move SL to breakeven)
        TP2: +2R
        TP3: +3R (or min_r_multiple from config)
        """
        # Use minimum R-multiple from config for TP3
        r3_multiple = max(3.0, self.min_r_multiple)
        
        if direction == 'long':
            tp1 = entry_price + (stop_distance * 1.0)
            tp2 = entry_price + (stop_distance * 2.0)
            tp3 = entry_price + (stop_distance * r3_multiple)
        else:  # short
            tp1 = entry_price - (stop_distance * 1.0)
            tp2 = entry_price - (stop_distance * 2.0)
            tp3 = entry_price - (stop_distance * r3_multiple)
        
        return tp1, tp2, tp3
    
    def calculate_profit_at_tp(
        self,
        levels: SLTPLevels,
        position_size_lots: float,
        pip_value: float
    ) -> Tuple[float, float, float]:
        """
        Calculate profit in dollars at each TP level
        
        Returns:
            (profit_at_tp1, profit_at_tp2, profit_at_tp3)
        """
        pip_size = config.PAIR_CONFIG[levels.pair.value]['pip_value']
        
        # Calculate pip distance to each TP
        tp1_pips = abs(levels.take_profit_1 - levels.entry_price) / pip_size
        tp2_pips = abs(levels.take_profit_2 - levels.entry_price) / pip_size
        tp3_pips = abs(levels.take_profit_3 - levels.entry_price) / pip_size
        
        # Calculate profit for each part
        part1_lots = position_size_lots * (levels.position_split[0] / 100)
        part2_lots = position_size_lots * (levels.position_split[1] / 100)
        part3_lots = position_size_lots * (levels.position_split[2] / 100)
        
        profit_tp1 = tp1_pips * pip_value * part1_lots
        profit_tp2 = tp2_pips * pip_value * part2_lots
        profit_tp3 = tp3_pips * pip_value * part3_lots
        
        return profit_tp1, profit_tp2, profit_tp3
    
    def calculate_total_profit(
        self,
        levels: SLTPLevels,
        position_size_lots: float,
        pip_value: float
    ) -> float:
        """Calculate total profit if all TPs hit"""
        profits = self.calculate_profit_at_tp(levels, position_size_lots, pip_value)
        return sum(profits)


def main():
    """Test the SL/TP Calculator"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("SL/TP CALCULATOR TEST")
    print("="*60 + "\n")
    
    try:
        calculator = SLTPCalculator()
        
        # Test 1: Long trade for GBP/USD
        print("Test 1: Long trade - GBP/USD\n")
        print("Scenario:")
        print("  Direction: LONG")
        print("  Entry: 1.2700")
        print("  No liquidity zones (using default 1.5% SL)\n")
        
        levels = calculator.calculate_sl_tp(
            pair=CurrencyPair.GBP_USD,
            direction='long',
            entry_price=1.2700
        )
        
        print("✅ SL/TP Levels Calculated:\n")
        print(f"  Entry: {levels.entry_price:.5f}")
        print(f"  Stop Loss: {levels.stop_loss:.5f} ({levels.stop_loss_pips:.1f} pips)")
        print(f"\n  Take Profits:")
        print(f"    TP1: {levels.take_profit_1:.5f} (+{levels.r_multiple_1:.1f}R) - Move SL to breakeven")
        print(f"    TP2: {levels.take_profit_2:.5f} (+{levels.r_multiple_2:.1f}R) - Close 33%")
        print(f"    TP3: {levels.take_profit_3:.5f} (+{levels.r_multiple_3:.1f}R) - Trail remaining 34%")
        print(f"\n  Position Split: {levels.position_split[0]}% / {levels.position_split[1]}% / {levels.position_split[2]}%\n")
        
        # Test 2: Short trade for EUR/USD
        print("-"*60)
        print("Test 2: Short trade - EUR/USD\n")
        
        levels2 = calculator.calculate_sl_tp(
            pair=CurrencyPair.EUR_USD,
            direction='short',
            entry_price=1.0850
        )
        
        print("✅ SL/TP Levels:\n")
        print(f"  Entry: {levels2.entry_price:.5f}")
        print(f"  Stop Loss: {levels2.stop_loss:.5f}")
        print(f"  TP1: {levels2.take_profit_1:.5f} (+{levels2.r_multiple_1:.1f}R)")
        print(f"  TP2: {levels2.take_profit_2:.5f} (+{levels2.r_multiple_2:.1f}R)")
        print(f"  TP3: {levels2.take_profit_3:.5f} (+{levels2.r_multiple_3:.1f}R)\n")
        
        # Test 3: Calculate profits
        print("-"*60)
        print("Test 3: Profit calculation\n")
        
        position_size = 0.2  # 0.2 lots
        pip_value = 10.0     # $10 per pip for standard lot
        
        profits = calculator.calculate_profit_at_tp(levels, position_size, pip_value)
        total_profit = calculator.calculate_total_profit(levels, position_size, pip_value)
        
        print(f"Position: {position_size} lots\n")
        print(f"  Profit at TP1 (33%): ${profits[0]:.2f}")
        print(f"  Profit at TP2 (33%): ${profits[1]:.2f}")
        print(f"  Profit at TP3 (34%): ${profits[2]:.2f}")
        print(f"\n  Total if all TPs hit: ${total_profit:.2f}\n")
        
        print("="*60)
        print("✅ SL/TP CALCULATOR TEST COMPLETE!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())