"""
Liquidity Zone Detection Module

Detects institutional liquidity zones:
1. Equal Highs / Equal Lows
2. Stop-Hunt Zones (fake breakouts + reversal)
3. Fair Value Gaps (FVG) - 3-candle imbalances
4. Order Blocks
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
    price_range: Tuple[float, float]
    strength: int
    touches: int
    time_detected: datetime
    candle_index: int
    
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
    """Advanced Liquidity Zone Detector"""
    
    def __init__(self):
        self.fetcher = MarketDataFetcher()
        self.equal_level_tolerance = config.EQUAL_LEVEL_TOLERANCE
        self.min_touches = config.MIN_TOUCHES
        self.swing_detection_window = 5
    
    def detect_all_zones(self, pair: CurrencyPair, timeframe: TimeFrame) -> List[LiquidityZone]:
        """Detect all types of liquidity zones"""
        logger.info(f"Detecting liquidity zones for {pair.value} on {timeframe.value}")
        
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
            
            logger.info(f"✅ Detected {len(zones)} liquidity zones "
                       f"(EH/EL: {len(equal_highs) + len(equal_lows)}, "
                       f"Stop-Hunt: {len(stop_hunts)}, FVG: {len(fvgs)})")
            
            return zones
            
        except Exception as e:
            logger.error(f"Liquidity zone detection failed: {e}")
            raise LiquidityZoneError(pair=pair.value, zone_type="all", reason=str(e))
    
    def _detect_equal_highs(self, data: pd.DataFrame, tolerance: float = None) -> List[LiquidityZone]:
        """Detect Equal Highs"""
        if tolerance is None:
            tolerance = self.equal_level_tolerance
        
        zones = []
        
        swing_highs = data[data['high'] == data['high'].rolling(
            window=self.swing_detection_window, center=True).max()].copy()
        
        if len(swing_highs) < 2:
            return zones
        
        swing_highs_list = [(idx, row['high']) for idx, row in swing_highs.iterrows()]
        processed = set()