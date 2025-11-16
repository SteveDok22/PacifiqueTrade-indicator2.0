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