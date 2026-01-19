@"
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
"@ | Set-Content -Path analysis/liquidity_zones.py -Encoding UTF8