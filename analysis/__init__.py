"""
Analysis module for PacifiqueTrade Indicator 2.0

This module contains all trading analysis components:
- Fundamental analysis (economic news screening)
- Trend detection (EMA, HH/HL)
- Liquidity zone detection (Equal H/L, Stop-Hunt, FVG)
- Signal generation (combining all factors)
"""

from .fundamental import FundamentalAnalyzer, FundamentalSignal
from .trend_detector import TrendDetector, TrendAnalysis
from .liquidity_zones import LiquidityZoneDetector, LiquidityZone
from .signal_generator import SignalGenerator, TradingSignal

__all__ = [
    'FundamentalAnalyzer',
    'FundamentalSignal',
    'TrendDetector',
    'TrendAnalysis',
    'LiquidityZoneDetector',
    'LiquidityZone',
    'SignalGenerator',
    'TradingSignal',
]

__version__ = '2.0.0'