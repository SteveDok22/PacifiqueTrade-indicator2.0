"""
Trend Detection Module

Detects market trends using:
- EMA50 and EMA200 crossovers
- Higher Highs / Higher Lows (bullish)
- Lower Highs / Lower Lows (bearish)
- Multi-timeframe confirmation (H1 + H4)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import CurrencyPair, TrendDirection, TimeFrame, SignalStrength
from core.exceptions import TrendDetectionError, InsufficientDataError
from core.config import config
from data import MarketDataFetcher


logger = logging.getLogger(__name__)


@dataclass
class TrendAnalysis:
    """Results of trend analysis"""
    pair: CurrencyPair
    timeframe: TimeFrame
    direction: TrendDirection
    strength: SignalStrength
    ema50: float
    ema200: float
    current_price: float
    higher_highs: bool
    higher_lows: bool
    lower_highs: bool
    lower_lows: bool
    analysis_time: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'pair': self.pair.value,
            'timeframe': self.timeframe.value,
            'direction': self.direction.value,
            'strength': self.strength.value,
            'ema50': round(self.ema50, 5),
            'ema200': round(self.ema200, 5),
            'current_price': round(self.current_price, 5),
            'higher_highs': self.higher_highs,
            'higher_lows': self.higher_lows,
            'lower_highs': self.lower_highs,
            'lower_lows': self.lower_lows,
            'analysis_time': self.analysis_time.isoformat()
        }
    
    def confirms_fundamental(self, fundamental_direction: str) -> bool:
        """
        Check if trend confirms fundamental direction
        
        Args:
            fundamental_direction: 'bullish' or 'bearish'
            
        Returns:
            True if trend and fundamental align
        """
        if fundamental_direction.lower() == 'bullish':
            return self.direction == TrendDirection.BULLISH
        elif fundamental_direction.lower() == 'bearish':
            return self.direction == TrendDirection.BEARISH
        return False


class TrendDetector:
    """
    Multi-Timeframe Trend Detector
    
    Detects trends using:
    1. EMA50/200 crossover (golden cross / death cross)
    2. Higher High / Higher Low pattern (bullish)
    3. Lower High / Lower Low pattern (bearish)
    4. Multi-timeframe confirmation
    
    Strategy:
    - H4 for overall trend direction
    - H1 for entry timing confirmation
    """
    
    def __init__(self):
        self.fetcher = MarketDataFetcher()
    
    def analyze_trend(
        self,
        pair: CurrencyPair,
        timeframe: TimeFrame
    ) -> TrendAnalysis:
        """
        Analyze trend for a pair on specific timeframe
        
        Args:
            pair: Currency pair
            timeframe: Timeframe to analyze
            
        Returns:
            TrendAnalysis object
            
        Raises:
            TrendDetectionError: If analysis fails
        """
        logger.info(f"Analyzing trend for {pair.value} on {timeframe.value}")
        
        try:
            # Fetch data
            df = self.fetcher.fetch_data(pair, timeframe)
            
            # Calculate indicators
            df = self._calculate_emas(df)
            
            # Detect patterns
            higher_highs = self._detect_higher_highs(df)
            higher_lows = self._detect_higher_lows(df)
            lower_highs = self._detect_lower_highs(df)
            lower_lows = self._detect_lower_lows(df)
            
            # Determine trend direction
            direction = self._determine_trend(
                df,
                higher_highs,
                higher_lows,
                lower_highs,
                lower_lows
            )
            
            # Calculate strength
            strength = self._calculate_trend_strength(
                df,
                direction,
                higher_highs,
                higher_lows,
                lower_highs,
                lower_lows
            )
            
            # Get latest values
            latest = df.iloc[-1]
            
            analysis = TrendAnalysis(
                pair=pair,
                timeframe=timeframe,
                direction=direction,
                strength=strength,
                ema50=latest['ema50'],
                ema200=latest['ema200'],
                current_price=latest['close'],
                higher_highs=higher_highs,
                higher_lows=higher_lows,
                lower_highs=lower_highs,
                lower_lows=lower_lows,
                analysis_time=datetime.now()
            )
            
            logger.info(f"✅ Trend detected: {direction.value} (strength: {strength.value})")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Trend detection failed for {pair.value}: {e}")
            raise TrendDetectionError(
                pair=pair.value,
                timeframe=timeframe.value,
                reason=str(e)
            )
    
    def analyze_multi_timeframe(
        self,
        pair: CurrencyPair
    ) -> Dict[str, TrendAnalysis]:
        """
        Analyze trend on both H4 and H1 timeframes
        
        Returns:
            Dictionary with 'H4' and 'H1' trend analyses
        """
        logger.info(f"Multi-timeframe analysis for {pair.value}")
        
        h4_trend = self.analyze_trend(pair, TimeFrame.H4)
        h1_trend = self.analyze_trend(pair, TimeFrame.H1)
        
        return {
            'H4': h4_trend,
            'H1': h1_trend
        }
    
    def _calculate_emas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA50 and EMA200"""
        df['ema50'] = df['close'].ewm(span=config.EMA_FAST, adjust=False).mean()
        df['ema200'] = df['close'].ewm(span=config.EMA_SLOW, adjust=False).mean()
        return df
    
    def _detect_higher_highs(self, df: pd.DataFrame, lookback: int = 10) -> bool:
        """
        Detect Higher Highs pattern
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Number of bars to check
            
        Returns:
            True if Higher Highs detected
        """
        highs = df['high'].tail(lookback).values
        
        # Need at least 3 highs to confirm pattern
        if len(highs) < 3:
            return False
        
        # Check if recent highs are generally increasing
        recent_high = highs[-1]
        previous_high = max(highs[:-3])
        
        return recent_high > previous_high
    
    def _detect_higher_lows(self, df: pd.DataFrame, lookback: int = 10) -> bool:
        """Detect Higher Lows pattern"""
        lows = df['low'].tail(lookback).values
        
        if len(lows) < 3:
            return False
        
        recent_low = lows[-1]
        previous_low = min(lows[:-3])
        
        return recent_low > previous_low
    
    def _detect_lower_highs(self, df: pd.DataFrame, lookback: int = 10) -> bool:
        """Detect Lower Highs pattern"""
        highs = df['high'].tail(lookback).values
        
        if len(highs) < 3:
            return False
        
        recent_high = highs[-1]
        previous_high = max(highs[:-3])
        
        return recent_high < previous_high
    
    def _detect_lower_lows(self, df: pd.DataFrame, lookback: int = 10) -> bool:
        """Detect Lower Lows pattern"""
        lows = df['low'].tail(lookback).values
        
        if len(lows) < 3:
            return False
        
        recent_low = lows[-1]
        previous_low = min(lows[:-3])
        
        return recent_low < previous_low
    
    def _determine_trend(
        self,
        df: pd.DataFrame,
        higher_highs: bool,
        higher_lows: bool,
        lower_highs: bool,
        lower_lows: bool
    ) -> TrendDirection:
        """Determine overall trend direction"""
        
        latest = df.iloc[-1]
        ema50 = latest['ema50']
        ema200 = latest['ema200']
        
        # Primary: EMA crossover
        if ema50 > ema200:
            # Potential bullish trend
            if higher_highs and higher_lows:
                return TrendDirection.BULLISH
            elif not (lower_highs and lower_lows):
                return TrendDirection.BULLISH
            else:
                return TrendDirection.SIDEWAYS
        
        elif ema50 < ema200:
            # Potential bearish trend
            if lower_highs and lower_lows:
                return TrendDirection.BEARISH
            elif not (higher_highs and higher_lows):
                return TrendDirection.BEARISH
            else:
                return TrendDirection.SIDEWAYS
        
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_trend_strength(
        self,
        df: pd.DataFrame,
        direction: TrendDirection,
        higher_highs: bool,
        higher_lows: bool,
        lower_highs: bool,
        lower_lows: bool
    ) -> SignalStrength:
        """Calculate trend strength based on multiple factors"""
        
        if direction == TrendDirection.SIDEWAYS:
            return SignalStrength.NO_SIGNAL
        
        latest = df.iloc[-1]
        ema50 = latest['ema50']
        ema200 = latest['ema200']
        
        # Calculate EMA separation (as percentage)
        ema_separation = abs(ema50 - ema200) / ema200 * 100
        
        # Calculate score
        score = 0
        
        # EMA separation
        if ema_separation > 0.5:
            score += 2
        elif ema_separation > 0.3:
            score += 1
        
        # Pattern confirmation
        if direction == TrendDirection.BULLISH:
            if higher_highs and higher_lows:
                score += 3
            elif higher_highs or higher_lows:
                score += 1
        elif direction == TrendDirection.BEARISH:
            if lower_highs and lower_lows:
                score += 3
            elif lower_highs or lower_lows:
                score += 1
        
        # Map score to strength
        if score >= 5:
            return SignalStrength.VERY_STRONG
        elif score >= 4:
            return SignalStrength.STRONG
        elif score >= 3:
            return SignalStrength.MODERATE
        elif score >= 2:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK


def main():
    """Test the Trend Detector"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("TREND DETECTOR TEST")
    print("="*60 + "\n")
    
    try:
        detector = TrendDetector()
        
        # Test 1: Single timeframe analysis
        print("Test 1: Analyzing GBP/USD on H4...")
        analysis = detector.analyze_trend(CurrencyPair.GBP_USD, TimeFrame.H4)
        
        print(f"✅ Trend Analysis Complete:\n")
        print(f"   Pair: {analysis.pair.value}")
        print(f"   Timeframe: {analysis.timeframe.value}")
        print(f"   Direction: {analysis.direction.value}")
        print(f"   Strength: {analysis.strength.value}")
        print(f"   Current Price: {analysis.current_price:.5f}")
        print(f"   EMA50: {analysis.ema50:.5f}")
        print(f"   EMA200: {analysis.ema200:.5f}")
        print(f"   Higher Highs: {analysis.higher_highs}")
        print(f"   Higher Lows: {analysis.higher_lows}")
        
        # Test 2: Multi-timeframe analysis
        print("\n" + "-"*60)
        print("Test 2: Multi-timeframe analysis for EUR/USD...")
        
        mtf_analysis = detector.analyze_multi_timeframe(CurrencyPair.EUR_USD)
        
        print(f"✅ Multi-Timeframe Analysis:\n")
        for tf_name, tf_analysis in mtf_analysis.items():
            print(f"   {tf_name}: {tf_analysis.direction.value} ({tf_analysis.strength.value})")
        
        # Test 3: Check H4 and H1 alignment
        h4_direction = mtf_analysis['H4'].direction
        h1_direction = mtf_analysis['H1'].direction
        
        if h4_direction == h1_direction and h4_direction != TrendDirection.SIDEWAYS:
            print(f"\n   ✅ ALIGNED: Both timeframes show {h4_direction.value} trend!")
        else:
            print(f"\n   ⚠️  CONFLICTING: H4={h4_direction.value}, H1={h1_direction.value}")
        
        print("\n" + "="*60)
        print("✅ TREND DETECTOR TEST COMPLETE!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())