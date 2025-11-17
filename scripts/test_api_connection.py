"""
API Connection Test Script

Tests all external API connections:
- Forex Factory (economic calendar)
- yfinance (market data)
- Telegram (notifications)
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("\n" + "="*60)
print("API CONNECTION TEST")
print("="*60 + "\n") 

# Test 1: Forex Factory
print("Test 1: Forex Factory API")
print("-" * 60)
try:
    from data import ForexFactoryAPI
    from core.enums import CurrencyPair
    
    api = ForexFactoryAPI()
    events = api.fetch_calendar()
    
    print(f"✅ Success! Fetched {len(events)} economic events")
    if events:
        print(f"   Latest event: {events[0].event_name}")
except Exception as e:
    print(f"❌ Failed: {e}")

print()

# Test 2: yfinance (Market Data)
print("Test 2: yfinance Market Data")
print("-" * 60)
try:
    from data import MarketDataFetcher
    from core.enums import CurrencyPair, TimeFrame
    
    fetcher = MarketDataFetcher()
    df = fetcher.fetch_data(CurrencyPair.GBP_USD, TimeFrame.H1)
    
    print(f"✅ Success! Fetched {len(df)} candles for GBP/USD")
    print(f"   Latest price: {df['close'].iloc[-1]:.5f}")
except Exception as e:
    print(f"❌ Failed: {e}")

print()

# Test 3: Telegram
print("Test 3: Telegram Bot")
print("-" * 60)
try:
    from notification import TelegramNotifier
    from core.config import config
    
    if not config.TELEGRAM_ENABLED:
        print("⚠️  Telegram is disabled in .env")
    else:
        telegram = TelegramNotifier()
        
        if telegram.is_enabled():
            print(f"✅ Success! Connected to Telegram")
            print(f"   Chat ID: {config.TELEGRAM_CHAT_ID}")
        else:
            print("❌ Telegram not properly configured")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*60)
print("✅ API CONNECTION TEST COMPLETE")
print("="*60 + "\n")