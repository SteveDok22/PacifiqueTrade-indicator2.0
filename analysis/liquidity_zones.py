"""
Liquidity Zone Detection Module

Detects institutional liquidity zones:
1. Equal Highs / Equal Lows
2. Stop-Hunt Zones (fake breakouts + reversal)
3. Fair Value Gaps (FVG) - 3-candle imbalances
4. Order Blocks

These zones represent areas where institutions hunt retail stops
and where price is likely to reverse or react strongly.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import CurrencyPair, TimeFrame, LiquidityZoneType
from core.exceptions import LiquidityZoneError
from core.config import config
from data import MarketDataFetcher


logger = logging.getLogger(__name__)


@dataclass
class LiquidityZone:
    """Represents a liquidity zone"""
    zone_type: LiquidityZoneType
    price_level: float
    price_range: Tuple[float, float]  # (low, high)
    strength: int  # 1-5, higher is stronger
    touches: int  # Number of times price touched this level
    time_detected: datetime
    candle_index: int  # Index in the dataframe
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'type': self.zone_type.value,
            'price_level': round(self.price_level, 5),
            'price_range': [round(self.price_range[0], 5), round(self.price_range[1], 5)],
            'strength': self.strength,
            'touches': self.touches,
            'time_detected': self.time_detected.isoformat(),
            'candle_index': self.candle_index
        }
    
    def is_near_price(self, current_price: float, tolerance: float = 0.001) -> bool:
        """Check if current price is near this zone"""
        return (self.price_range[0] * (1 - tolerance) <= current_price <= 
                self.price_range[1] * (1 + tolerance))


class LiquidityZoneDetector:
    """
    Advanced Liquidity Zone Detector
    
    Identifies key liquidity zones where institutions:
    1. Hunt stop losses (Equal Highs/Lows)
    2. Fake breakouts and reverse (Stop-Hunt zones)
    3. Leave imbalances (Fair Value Gaps)
    4. Place large orders (Order Blocks)
    
    These zones are high-probability reversal or continuation areas.
    """
    
    def __init__(self):
        self.fetcher = MarketDataFetcher()
    
    def detect_all_zones(
        self,
        pair: CurrencyPair,
        timeframe: TimeFrame
    ) -> List[LiquidityZone]:
        """
        Detect all types of liquidity zones
        
        Args:
            pair: Currency pair
            timeframe: Timeframe (M15 or M30 recommended)
            
        Returns:
            List of detected liquidity zones
        """
        logger.info(f"Detecting liquidity zones for {pair.value} on {timeframe.value}")
        
        try:
            # Fetch data
            df = self.fetcher.fetch_data(pair, timeframe)
            
            zones = []
            
            # 1. Equal Highs/Lows
            equal_highs = self._detect_equal_highs(df)
            equal_lows = self._detect_equal_lows(df)
            zones.extend(equal_highs)
            zones.extend(equal_lows)
            
            # 2. Stop-Hunt Zones
            stop_hunts = self._detect_stop_hunts(df)
            zones.extend(stop_hunts)
            
            # 3. Fair Value Gaps
            fvgs = self._detect_fair_value_gaps(df)
            zones.extend(fvgs)
            
            # Sort by strength (strongest first)
            zones.sort(key=lambda z: z.strength, reverse=True)
            
            logger.info(f"✅ Detected {len(zones)} liquidity zones "
                       f"(EH/EL: {len(equal_highs) + len(equal_lows)}, "
                       f"Stop-Hunt: {len(stop_hunts)}, FVG: {len(fvgs)})")
            
            return zones
            
        except Exception as e:
            logger.error(f"Liquidity zone detection failed: {e}")
            raise LiquidityZoneError(
                pair=pair.value,
                zone_type="all",
                reason=str(e)
            )
    
    def _detect_equal_highs(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """
        Detect Equal Highs
        
        Equal Highs = Multiple swing highs at approximately same level
        Indicates resistance and potential sell-side liquidity
        """
        zones = []
        tolerance = config.EQUAL_LEVEL_TOLERANCE
        min_touches = config.MIN_TOUCHES
        
        # Find swing highs
        df['swing_high'] = (
            (df['high'] > df['high'].shift(1)) &
            (df['high'] > df['high'].shift(-1))
        )
        
        swing_highs = df[df['swing_high']].copy()
        
        if len(swing_highs) < min_touches:
            return zones
        
        # Group similar highs
        high_levels = swing_highs['high'].values
        indices = swing_highs.index.tolist()
        
        for i, level in enumerate(high_levels):
            similar_highs = []
            similar_indices = []
            
            for j, other_level in enumerate(high_levels):
                # Check if within tolerance
                if abs(level - other_level) / level <= tolerance:
                    similar_highs.append(other_level)
                    similar_indices.append(indices[j])
            
            if len(similar_highs) >= min_touches:
                # Calculate average level and range
                avg_level = np.mean(similar_highs)
                price_range = (min(similar_highs), max(similar_highs))
                
                # Calculate strength based on touches
                strength = min(5, len(similar_highs))
                
                zone = LiquidityZone(
                    zone_type=LiquidityZoneType.EQUAL_HIGHS,
                    price_level=avg_level,
                    price_range=price_range,
                    strength=strength,
                    touches=len(similar_highs),
                    time_detected=df.iloc[similar_indices[-1]].name,
                    candle_index=similar_indices[-1]
                )
                
                # Avoid duplicates
                if not any(z.zone_type == LiquidityZoneType.EQUAL_HIGHS and 
                          abs(z.price_level - zone.price_level) / zone.price_level < tolerance 
                          for z in zones):
                    zones.append(zone)
        
        logger.debug(f"Found {len(zones)} Equal Highs zones")
        return zones
    
    def _detect_equal_lows(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """
        Detect Equal Lows
        
        Equal Lows = Multiple swing lows at approximately same level
        Indicates support and potential buy-side liquidity
        """
        zones = []
        tolerance = config.EQUAL_LEVEL_TOLERANCE
        min_touches = config.MIN_TOUCHES
        
        # Find swing lows
        df['swing_low'] = (
            (df['low'] < df['low'].shift(1)) &
            (df['low'] < df['low'].shift(-1))
        )
        
        swing_lows = df[df['swing_low']].copy()
        
        if len(swing_lows) < min_touches:
            return zones
        
        # Group similar lows
        low_levels = swing_lows['low'].values
        indices = swing_lows.index.tolist()
        
        for i, level in enumerate(low_levels):
            similar_lows = []
            similar_indices = []
            
            for j, other_level in enumerate(low_levels):
                # Check if within tolerance
                if abs(level - other_level) / level <= tolerance:
                    similar_lows.append(other_level)
                    similar_indices.append(indices[j])
            
            if len(similar_lows) >= min_touches:
                # Calculate average level and range
                avg_level = np.mean(similar_lows)
                price_range = (min(similar_lows), max(similar_lows))
                
                # Calculate strength
                strength = min(5, len(similar_lows))
                
                zone = LiquidityZone(
                    zone_type=LiquidityZoneType.EQUAL_LOWS,
                    price_level=avg_level,
                    price_range=price_range,
                    strength=strength,
                    touches=len(similar_lows),
                    time_detected=df.iloc[similar_indices[-1]].name,
                    candle_index=similar_indices[-1]
                )
                
                # Avoid duplicates
                if not any(z.zone_type == LiquidityZoneType.EQUAL_LOWS and 
                          abs(z.price_level - zone.price_level) / zone.price_level < tolerance 
                          for z in zones):
                    zones.append(zone)
        
        logger.debug(f"Found {len(zones)} Equal Lows zones")
        return zones
    
    def _detect_stop_hunts(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """
        Detect Stop-Hunt Zones
        
        Stop-Hunt = Price spikes through a level then quickly reverses
        Pattern: Break → Immediate reversal → Close back inside
        
        Buy Stop-Hunt: Spike above resistance → drop
        Sell Stop-Hunt: Spike below support → rally
        """
        zones = []
        lookback = 20
        
        for i in range(lookback, len(df) - 1):
            candle = df.iloc[i]
            prev_candle = df.iloc[i-1]
            next_candle = df.iloc[i+1]
            
            # Recent high/low
            recent_high = df.iloc[i-lookback:i]['high'].max()
            recent_low = df.iloc[i-lookback:i]['low'].min()
            
            # Buy Stop-Hunt (spike down, then up)
            if (candle['low'] < recent_low and  # Broke below recent low
                candle['close'] > candle['open'] and  # But closed bullish
                next_candle['close'] > candle['close']):  # Continued up
                
                zone = LiquidityZone(
                    zone_type=LiquidityZoneType.STOP_HUNT_BUY,
                    price_level=candle['low'],
                    price_range=(candle['low'], candle['low'] * 1.001),
                    strength=4,
                    touches=1,
                    time_detected=candle.name,
                    candle_index=i
                )
                zones.append(zone)
            
            # Sell Stop-Hunt (spike up, then down)
            elif (candle['high'] > recent_high and  # Broke above recent high
                  candle['close'] < candle['open'] and  # But closed bearish
                  next_candle['close'] < candle['close']):  # Continued down
                
                zone = LiquidityZone(
                    zone_type=LiquidityZoneType.STOP_HUNT_SELL,
                    price_level=candle['high'],
                    price_range=(candle['high'] * 0.999, candle['high']),
                    strength=4,
                    touches=1,
                    time_detected=candle.name,
                    candle_index=i
                )
                zones.append(zone)
        
        logger.debug(f"Found {len(zones)} Stop-Hunt zones")
        return zones
    
    def _detect_fair_value_gaps(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """
        Detect Fair Value Gaps (FVG)
        
        FVG = 3-candle pattern with a gap (imbalance)
        
        Bullish FVG:
        - Candle 1 high < Candle 3 low
        - Gap between = unfilled area
        
        Bearish FVG:
        - Candle 1 low > Candle 3 high
        - Gap between = unfilled area
        """
        zones = []
        min_gap_size = config.FVG_MIN_SIZE
        
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]
            candle2 = df.iloc[i-1]
            candle3 = df.iloc[i]
            
            # Bullish FVG (gap between candle1.high and candle3.low)
            if candle1['high'] < candle3['low']:
                gap_size = (candle3['low'] - candle1['high']) / candle1['high']
                
                if gap_size >= min_gap_size:
                    zone = LiquidityZone(
                        zone_type=LiquidityZoneType.FAIR_VALUE_GAP_BULLISH,
                        price_level=(candle1['high'] + candle3['low']) / 2,
                        price_range=(candle1['high'], candle3['low']),
                        strength=3,
                        touches=0,
                        time_detected=candle3.name,
                        candle_index=i
                    )
                    zones.append(zone)
            
            # Bearish FVG (gap between candle1.low and candle3.high)
            elif candle1['low'] > candle3['high']:
                gap_size = (candle1['low'] - candle3['high']) / candle3['high']
                
                if gap_size >= min_gap_size:
                    zone = LiquidityZone(
                        zone_type=LiquidityZoneType.FAIR_VALUE_GAP_BEARISH,
                        price_level=(candle1['low'] + candle3['high']) / 2,
                        price_range=(candle3['high'], candle1['low']),
                        strength=3,
                        touches=0,
                        time_detected=candle3.name,
                        candle_index=i
                    )
                    zones.append(zone)
        
        logger.debug(f"Found {len(zones)} Fair Value Gap zones")
        return zones
    
    def get_zones_near_price(
        self,
        zones: List[LiquidityZone],
        current_price: float,
        distance_pct: float = 0.5
    ) -> List[LiquidityZone]:
        """
        Filter zones that are near current price
        
        Args:
            zones: All detected zones
            current_price: Current market price
            distance_pct: Maximum distance as percentage (0.5 = 0.5%)
            
        Returns:
            List of zones within distance
        """
        nearby_zones = []
        
        for zone in zones:
            distance = abs(zone.price_level - current_price) / current_price
            
            if distance <= distance_pct / 100:
                nearby_zones.append(zone)
        
        # Sort by distance (closest first)
        nearby_zones.sort(key=lambda z: abs(z.price_level - current_price))
        
        logger.debug(f"Found {len(nearby_zones)} zones within {distance_pct}% of price")
        return nearby_zones
    
    def get_strongest_zones(
        self,
        zones: List[LiquidityZone],
        count: int = 5
    ) -> List[LiquidityZone]:
        """Get the strongest N zones"""
        return sorted(zones, key=lambda z: z.strength, reverse=True)[:count]


def main():
    """Test the Liquidity Zone Detector"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("LIQUIDITY ZONE DETECTOR TEST")
    print("="*60 + "\n")
    
    try:
        detector = LiquidityZoneDetector()
        
        # Test 1: Detect all zones for GBP/USD M15
        print("Test 1: Detecting all liquidity zones for GBP/USD (M15)...")
        zones = detector.detect_all_zones(CurrencyPair.GBP_USD, TimeFrame.M15)
        
        print(f"✅ Detected {len(zones)} total liquidity zones\n")
        
        # Count by type
        zone_counts = {}
        for zone in zones:
            zone_type = zone.zone_type.value
            zone_counts[zone_type] = zone_counts.get(zone_type, 0) + 1
        
        print("Zones by type:")
        for zone_type, count in zone_counts.items():
            print(f"   {zone_type}: {count}")
        
        # Test 2: Show strongest zones
        print("\n" + "-"*60)
        print("Test 2: Top 5 strongest zones:\n")
        
        strongest = detector.get_strongest_zones(zones, count=5)
        
        for i, zone in enumerate(strongest, 1):
            print(f"{i}. {zone.zone_type.value}")
            print(f"   Level: {zone.price_level:.5f}")
            print(f"   Range: {zone.price_range[0]:.5f} - {zone.price_range[1]:.5f}")
            print(f"   Strength: {zone.strength}/5")
            print(f"   Touches: {zone.touches}")
            print()
        
        # Test 3: Get zones near current price
        print("-"*60)
        print("Test 3: Zones near current price (within 0.3%)...\n")
        
        # Get current price
        fetcher = MarketDataFetcher()
        current_price = fetcher.get_current_price(CurrencyPair.GBP_USD)
        
        nearby = detector.get_zones_near_price(zones, current_price, distance_pct=0.3)
        
        print(f"Current price: {current_price:.5f}")
        print(f"Found {len(nearby)} nearby zones:\n")
        
        for zone in nearby[:5]:
            distance = abs(zone.price_level - current_price) / current_price * 100
            print(f"   • {zone.zone_type.value} @ {zone.price_level:.5f} "
                  f"(distance: {distance:.2f}%)")
        
        print("\n" + "="*60)
        print("✅ LIQUIDITY ZONE DETECTOR TEST COMPLETE!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())