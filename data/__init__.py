"""
Data module for PacifiqueTrade Indicator 2.0

This module handles all data fetching and caching:
- Forex Factory economic calendar
- Market data (OHLCV) from yfinance
- Redis caching layer
"""

from .forex_factory_api import ForexFactoryAPI, EconomicEvent
from .market_data import MarketDataFetcher, MarketCandle

# Optional: only import cache if Redis is enabled
try:
    from .cache import DataCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    DataCache = None

__all__ = [
    'ForexFactoryAPI',
    'EconomicEvent',
    'MarketDataFetcher',
    'MarketCandle',
    'DataCache',
    'CACHE_AVAILABLE'
]

__version__ = '2.0.0'