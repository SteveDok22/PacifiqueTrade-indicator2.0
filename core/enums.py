"""
Enumerations for PacifiqueTrade Indicator 2.0

Contains all enum types used throughout the trading system
for type safety and clarity.
"""

from enum import Enum, auto


class TrendDirection(Enum):
    """Trend direction on different timeframes"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    UNDEFINED = "undefined"


class SignalStrength(Enum):
    """Strength of trading signal"""
    VERY_STRONG = 5
    STRONG = 4
    MODERATE = 3
    WEAK = 2
    VERY_WEAK = 1
    NO_SIGNAL = 0


class MarketSession(Enum):
    """Major market trading sessions"""
    TOKYO = "tokyo"
    LONDON = "london"
    NEW_YORK = "newyork"
    SYDNEY = "sydney"
    CLOSED = "closed"