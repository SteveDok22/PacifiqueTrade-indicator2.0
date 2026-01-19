"""
Liquidity Zone Detection Module
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
    zone_type: LiquidityZoneType
    price_level: float
    price_range: Tuple[float, float]
    strength: int
    touches: int
    time_detected: datetime
    candle_index: int
    
    def to_dict(self) -> Dict:
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
        return (self.price_range[0] * (1 - tolerance) <= current_price <= 
                self.price_range[1] * (1 + tolerance))


class LiquidityZoneDetector:
    def __init__(self):
        self.fetcher = MarketDataFetcher()
        self.equal_level_tolerance = config.EQUAL_LEVEL_TOLERANCE
        self.min_touches = config.MIN_TOUCHES
        self.swing_detection_window = 5
    
    def detect_all_zones(self, pair: CurrencyPair, timeframe: TimeFrame) -> List[LiquidityZone]:
        logger.info(f'Detecting liquidity zones for {pair.value} on {timeframe.value}')
        
        try:
            df = self.fetcher.fetch_data(pair, timeframe)
            zones = []
            
            equal_highs = self._detect_equal_highs(df)
            equal_lows = self._detect_equal_lows(df)
            zones.extend(equal_highs)
            zones.extend(equal_lows)
            
            stop_hunts = self._detect_stop_hunts(df)
            zones.extend(stop_hunts)
            
            fvgs = self._detect_fair_value_gaps(df)
            zones.extend(fvgs)
            
            zones.sort(key=lambda z: z.strength, reverse=True)
            
            logger.info(f'Detected {len(zones)} liquidity zones')
            
            return zones
            
        except Exception as e:
            logger.error(f'Liquidity zone detection failed: {e}')
            raise LiquidityZoneError(pair=pair.value, zone_type='all', reason=str(e))
    
    def _detect_equal_highs(self, data: pd.DataFrame, tolerance: float = None) -> List[LiquidityZone]:
        if tolerance is None:
            tolerance = self.equal_level_tolerance
        
        zones = []
        
        swing_highs = data[data['high'] == data['high'].rolling(
            window=self.swing_detection_window, center=True).max()].copy()
        
        if len(swing_highs) < 2:
            return zones
        
        swing_highs_list = [(idx, row['high']) for idx, row in swing_highs.iterrows()]
        processed = set()
        
        for i, (current_idx, current_high) in enumerate(swing_highs_list):
            if i in processed:
                continue
            
            similar_highs = []
            similar_indices = []
            
            for j, (compare_idx, compare_high) in enumerate(swing_highs_list):
                if j in processed:
                    continue
                
                if abs(compare_high - current_high) / current_high <= tolerance:
                    similar_highs.append(compare_high)
                    similar_indices.append(compare_idx)
                    processed.add(j)
            
            if len(similar_highs) >= self.min_touches:
                avg_level = sum(similar_highs) / len(similar_highs)
                
                zone = LiquidityZone(
                    zone_type=LiquidityZoneType.EQUAL_HIGHS,
                    price_level=avg_level,
                    price_range=(min(similar_highs), max(similar_highs)),
                    strength=min(len(similar_highs), 5),
                    touches=len(similar_highs),
                    time_detected=current_idx,
                    candle_index=data.index.get_loc(current_idx)
                )
                
                zones.append(zone)
        
        return zones
        
    def _detect_equal_lows(self, data: pd.DataFrame, tolerance: float = None) -> List[LiquidityZone]:
        if tolerance is None:
            tolerance = self.equal_level_tolerance
        
        zones = []
        
        swing_lows = data[data['low'] == data['low'].rolling(
            window=self.swing_detection_window, center=True).min()].copy()
        
        if len(swing_lows) < 2:
            return zones
        
        swing_lows_list = [(idx, row['low']) for idx, row in swing_lows.iterrows()]
        processed = set()
        
        for i, (current_idx, current_low) in enumerate(swing_lows_list):
            if i in processed:
                continue
            
            similar_lows = []
            similar_indices = []
            
            for j, (compare_idx, compare_low) in enumerate(swing_lows_list):
                if j in processed:
                    continue
                
                if abs(compare_low - current_low) / current_low <= tolerance:
                    similar_lows.append(compare_low)
                    similar_indices.append(compare_idx)
                    processed.add(j)
            
            if len(similar_lows) >= self.min_touches:
                avg_level = sum(similar_lows) / len(similar_lows)
                
                zone = LiquidityZone(
                    zone_type=LiquidityZoneType.EQUAL_LOWS,
                    price_level=avg_level,
                    price_range=(min(similar_lows), max(similar_lows)),
                    strength=min(len(similar_lows), 5),
                    touches=len(similar_lows),
                    time_detected=current_idx,
                    candle_index=data.index.get_loc(current_idx)
                )
                
                zones.append(zone)
        
        return zones
    
    def _detect_stop_hunts(self, df: pd.DataFrame) -> List[LiquidityZone]:
        zones = []
        lookback = 20
        
        for i in range(lookback, len(df) - 1):
            candle = df.iloc[i]
            next_candle = df.iloc[i+1]
            
            recent_high = df.iloc[i-lookback:i]['high'].max()
            recent_low = df.iloc[i-lookback:i]['low'].min()
            
            if (candle['low'] < recent_low and 
                candle['close'] > candle['open'] and 
                next_candle['close'] > candle['close']):
                
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
            
            elif (candle['high'] > recent_high and 
                  candle['close'] < candle['open'] and 
                  next_candle['close'] < candle['close']):
                
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
        
        return zones
    
    def _detect_fair_value_gaps(self, df: pd.DataFrame) -> List[LiquidityZone]:
        zones = []
        min_gap_size = config.FVG_MIN_SIZE
        
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]
            candle3 = df.iloc[i]
            
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
        
        return zones
    
    def get_zones_near_price(self, zones: List[LiquidityZone], current_price: float, distance_pct: float = 0.5) -> List[LiquidityZone]:
        nearby_zones = []
        
        for zone in zones:
            distance = abs(zone.price_level - current_price) / current_price
            if distance <= distance_pct / 100:
                nearby_zones.append(zone)
        
        nearby_zones.sort(key=lambda z: abs(z.price_level - current_price))
        return nearby_zones
    
    def get_strongest_zones(self, zones: List[LiquidityZone], count: int = 5) -> List[LiquidityZone]:
        return sorted(zones, key=lambda z: z.strength, reverse=True)[:count]


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print('\n' + '='*60)
    print('LIQUIDITY ZONE DETECTOR TEST')
    print('='*60 + '\n')
    
    try:
        from core.enums import CurrencyPair, TimeFrame
        
        detector = LiquidityZoneDetector()
        
        print('Test 1: Detecting zones for GBP/USD (M15)...')
        zones = detector.detect_all_zones(CurrencyPair.GBP_USD, TimeFrame.M15)
        
        print(f'Found {len(zones)} total zones\n')
        
        zone_counts = {}
        for zone in zones:
            zone_type = zone.zone_type.value
            zone_counts[zone_type] = zone_counts.get(zone_type, 0) + 1
        
        print('Zones by type:')
        for zone_type, count in zone_counts.items():
            print(f'  - {zone_type}: {count}')
        
        print('\n' + '-'*60)
        print('Test 2: Top 5 strongest zones:\n')
        
        strongest = detector.get_strongest_zones(zones, count=5)
        
        for i, zone in enumerate(strongest, 1):
            print(f'{i}. {zone.zone_type.value}')
            print(f'   Level: {zone.price_level:.5f}')
            print(f'   Strength: {zone.strength}/5\n')
        
        print('='*60)
        print('TEST COMPLETE!')
        print('='*60 + '\n')
        
        return 0
        
    except Exception as e:
        print(f'\nERROR: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
