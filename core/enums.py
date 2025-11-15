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
    
class NewsImpact(Enum):
    """Economic news impact level"""
    HIGH = "high"           # 3 bulls / red flag
    MEDIUM = "medium"       # 2 bulls / orange flag
    LOW = "low"             # 1 bull / yellow flag
    NONE = "none"           # No impact


class SignalStatus(Enum):
    """Status of trading signal"""
    PENDING = "pending"             # Signal generated, waiting for confirmation
    CONFIRMED = "confirmed"         # All conditions met, ready to trade
    ACTIVE = "active"               # Trade is open
    COMPLETED = "completed"         # Trade closed with profit/loss
    CANCELLED = "cancelled"         # Signal cancelled due to market conditions
    EXPIRED = "expired"             # Signal expired (time window passed)


class TimeFrame(Enum):
    """Chart timeframes"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN1 = "1mo"


class LiquidityZoneType(Enum):
    """Types of liquidity zones"""
    EQUAL_HIGHS = "equal_highs"
    EQUAL_LOWS = "equal_lows"
    STOP_HUNT_BUY = "stop_hunt_buy"
    STOP_HUNT_SELL = "stop_hunt_sell"
    FAIR_VALUE_GAP_BULLISH = "fvg_bullish"
    FAIR_VALUE_GAP_BEARISH = "fvg_bearish"
    ORDER_BLOCK = "order_block"


class OrderType(Enum):
    """Types of orders"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class PositionSide(Enum):
    """Position direction"""
    LONG = "long"
    SHORT = "short"


class CurrencyPair(Enum):
    """Supported currency pairs"""
    GBP_USD = "GBP/USD"
    EUR_USD = "EUR/USD"
    USD_JPY = "USD/JPY"
    
    @property
    def base_currency(self) -> str:
        """Get base currency (first in pair)"""
        return self.value.split("/")[0]
    
    @property
    def quote_currency(self) -> str:
        """Get quote currency (second in pair)"""
        return self.value.split("/")[1]
    
    @property
    def yfinance_ticker(self) -> str:
        """Convert to yfinance ticker format"""
        return self.value.replace("/", "") + "=X"
