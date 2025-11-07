"""
Market Data Module

Fetches OHLCV (Open, High, Low, Close, Volume) data from yfinance.
Supports multiple timeframes and data validation.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import logging
from dataclasses import dataclass
import pytz

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import CurrencyPair, TimeFrame
from core.exceptions import MarketDataError, InsufficientDataError
from core.config import config


logger = logging.getLogger(__name__)


@dataclass
class MarketCandle:
    """Represents a single market candle"""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    def to_dict(self):
        return {
            'time': self.time,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }


class MarketDataFetcher:
    """
    Market Data Fetcher using yfinance
    
    Fetches OHLCV data for forex pairs from Yahoo Finance.
    Supports multiple timeframes: M15, M30, H1, H4, D1
    """
    
    # Timeframe mapping: our format -> yfinance format
    TIMEFRAME_MAP = {
        TimeFrame.M15: '15m',
        TimeFrame.M30: '30m',
        TimeFrame.H1: '1h',
        TimeFrame.H4: '4h',
        TimeFrame.D1: '1d',
    }
    
    # Period mapping for different timeframes
    PERIOD_MAP = {
        TimeFrame.M15: '7d',    # 7 days of M15 data
        TimeFrame.M30: '14d',   # 14 days of M30 data
        TimeFrame.H1: '60d',    # 60 days of H1 data
        TimeFrame.H4: '120d',   # 120 days of H4 data
        TimeFrame.D1: '2y',     # 2 years of daily data
    }
    
    def __init__(self):
        self.cache = {}
    
    def fetch_data(
        self,
        pair: CurrencyPair,
        timeframe: TimeFrame,
        period: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a currency pair
        
        Args:
            pair: Currency pair to fetch
            timeframe: Timeframe (M15, M30, H1, H4, D1)
            period: Period string (e.g., '7d', '60d', '1y')
            start_date: Start date (alternative to period)
            end_date: End date (alternative to period)
            
        Returns:
            DataFrame with OHLCV data
            
        Raises:
            MarketDataError: If fetch fails
        """
        ticker = pair.yfinance_ticker
        interval = self.TIMEFRAME_MAP.get(timeframe)
        
        if not interval:
            raise MarketDataError(
                pair=pair.value,
                timeframe=timeframe.value,
                message=f"Unsupported timeframe: {timeframe}"
            )
        
        logger.info(f"Fetching {pair.value} data ({timeframe.value})")
        
        try:
            # Create ticker object
            ticker_obj = yf.Ticker(ticker)
            
            # Fetch data
            if start_date and end_date:
                df = ticker_obj.history(
                    start=start_date,
                    end=end_date,
                    interval=interval
                )
            else:
                if period is None:
                    period = self.PERIOD_MAP.get(timeframe, '60d')
                
                df = ticker_obj.history(
                    period=period,
                    interval=interval
                )
            
            if df.empty:
                raise MarketDataError(
                    pair=pair.value,
                    timeframe=timeframe.value,
                    message="No data returned from yfinance"
                )
            
            # Validate data
            self._validate_data(df, pair, timeframe)
            
            # Clean data
            df = self._clean_data(df)
            
            logger.info(f"✅ Fetched {len(df)} bars for {pair.value} ({timeframe.value})")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {pair.value}: {e}")
            raise MarketDataError(
                pair=pair.value,
                timeframe=timeframe.value,
                message=str(e)
            )
    
    def _validate_data(self, df: pd.DataFrame, pair: CurrencyPair, timeframe: TimeFrame):
        """Validate fetched data"""
        
        # Check minimum bars
        min_bars = {
            TimeFrame.M15: config.MIN_BARS_M15,
            TimeFrame.M30: config.MIN_BARS_M15,
            TimeFrame.H1: config.MIN_BARS_H1,
            TimeFrame.H4: config.MIN_BARS_H4,
        }.get(timeframe, 50)
        
        if len(df) < min_bars:
            raise InsufficientDataError(
                required=min_bars,
                available=len(df),
                data_type=f"{pair.value} {timeframe.value}"
            )
        
        # Check for NaN values
        nan_count = df.isnull().sum().sum()
        if nan_count > len(df) * 0.05:  # More than 5% NaN
            logger.warning(f"High NaN count in data: {nan_count}/{len(df)}")
        
        # Check for gaps
        time_diff = df.index.to_series().diff()
        expected_diff = pd.Timedelta(timeframe.value)
        gaps = (time_diff > expected_diff * 2).sum()
        
        if gaps > 0:
            logger.warning(f"Found {gaps} gaps in {pair.value} data")
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare data"""
        
        # Remove timezone info for consistency
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Fill NaN with forward fill
        df = df.fillna(method='ffill')
        
        # Remove any remaining NaN
        df = df.dropna()
        
        # Rename columns to lowercase
        df.columns = [col.lower() for col in df.columns]
        
        return df
    
    def get_latest_candles(
        self,
        pair: CurrencyPair,
        timeframe: TimeFrame,
        count: int = 1
    ) -> List[MarketCandle]:
        """
        Get the latest N candles
        
        Args:
            pair: Currency pair
            timeframe: Timeframe
            count: Number of candles to return
            
        Returns:
            List of MarketCandle objects (most recent first)
        """
        df = self.fetch_data(pair, timeframe)
        
        # Get last N rows
        latest = df.tail(count)
        
        candles = []
        for idx, row in latest.iterrows():
            candle = MarketCandle(
                time=idx,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
            candles.append(candle)
        
        return list(reversed(candles))  # Most recent first
    
    def get_current_price(self, pair: CurrencyPair) -> float:
        """Get current market price"""
        candles = self.get_latest_candles(pair, TimeFrame.M15, count=1)
        return candles[0].close if candles else 0.0


def main():
    """Test the Market Data Fetcher"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("MARKET DATA FETCHER TEST")
    print("="*60 + "\n")
    
    try:
        fetcher = MarketDataFetcher()
        
        # Test 1: Fetch H4 data for GBP/USD
        print("Test 1: Fetching GBP/USD H4 data...")
        df_h4 = fetcher.fetch_data(CurrencyPair.GBP_USD, TimeFrame.H4)
        print(f"✅ Fetched {len(df_h4)} H4 bars")
        print(f"Date range: {df_h4.index[0]} to {df_h4.index[-1]}")
        print(f"Latest close: {df_h4['close'].iloc[-1]:.5f}\n")
        
        # Test 2: Fetch M15 data
        print("Test 2: Fetching EUR/USD M15 data...")
        df_m15 = fetcher.fetch_data(CurrencyPair.EUR_USD, TimeFrame.M15)
        print(f"✅ Fetched {len(df_m15)} M15 bars")
        print(f"Latest close: {df_m15['close'].iloc[-1]:.5f}\n")
        
        # Test 3: Get latest candles
        print("Test 3: Getting latest 5 candles for USD/JPY H1...")
        candles = fetcher.get_latest_candles(CurrencyPair.USD_JPY, TimeFrame.H1, count=5)
        print(f"✅ Got {len(candles)} candles\n")
        
        for i, candle in enumerate(candles, 1):
            print(f"{i}. [{candle.time}] O:{candle.open:.2f} H:{candle.high:.2f} "
                  f"L:{candle.low:.2f} C:{candle.close:.2f}")
        
        # Test 4: Get current price
        print("\nTest 4: Getting current prices...")
        for pair in [CurrencyPair.GBP_USD, CurrencyPair.EUR_USD, CurrencyPair.USD_JPY]:
            price = fetcher.get_current_price(pair)
            print(f"{pair.value}: {price:.5f}")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())