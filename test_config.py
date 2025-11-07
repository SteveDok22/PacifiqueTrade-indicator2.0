import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("="*60)
print("TESTING CONFIGURATION")
print("="*60)

try:
    print("\n1. Loading environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    print("   ✅ Loaded")
    
    print("\n2. Importing core modules...")
    from core import config
    print("   ✅ Core imported")
    
    print("\n3. Checking environment values...")
    import os
    print(f"   Bot Token: {os.getenv('TELEGRAM_BOT_TOKEN')[:20]}...")
    print(f"   Chat ID: {os.getenv('TELEGRAM_CHAT_ID')}")
    print(f"   Trading Pairs: {os.getenv('TRADING_PAIRS')}")
    
    print("\n4. Testing config object...")
    print(f"   Config.TELEGRAM_BOT_TOKEN: {config.TELEGRAM_BOT_TOKEN[:20] if config.TELEGRAM_BOT_TOKEN else 'None'}...")
    print(f"   Config.TELEGRAM_CHAT_ID: {config.TELEGRAM_CHAT_ID}")
    print(f"   Config.TRADING_PAIRS_STR: {config.TRADING_PAIRS_STR}")
    
    print("\n5. Running validation...")
    config.validate_all()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    
except Exception as e:
    print("\n" + "="*60)
    print("❌ ERROR FOUND:")
    print("="*60)
    print(f"\nError Type: {type(e).__name__}")
    print(f"Error Message: {e}")
    print("\nFull traceback:")
    import traceback
    traceback.print_exc()
    print("="*60)