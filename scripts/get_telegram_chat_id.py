"""
Get Telegram Chat ID Helper Script

This script helps you find your Telegram chat ID.
Run this script and send a message to your bot to see your chat ID.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# Load environment
ENV_PATH = PROJECT_ROOT / ".env"
if not ENV_PATH.exists():
    print("❌ Error: .env file not found!")
    print("Please copy .env.example to .env and add your TELEGRAM_BOT_TOKEN")
    sys.exit(1)

load_dotenv(ENV_PATH)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file!")
    print("Please add your bot token from @BotFather to .env file")
    sys.exit(1)
    
def get_chat_id():
    """Get chat ID from Telegram"""
    try:
        from telegram import Bot
        from telegram.error import TelegramError
    except ImportError:
        print("❌ python-telegram-bot not installed")
        print("Run: pip install python-telegram-bot")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("📱 TELEGRAM CHAT ID FINDER")
    print("="*60)
    print("\nBot Token:", TELEGRAM_BOT_TOKEN[:20] + "..." + TELEGRAM_BOT_TOKEN[-10:])
    print("\n📋 Instructions:")
    print("1. Open Telegram on your phone or computer")
    print("2. Search for your bot (the one you created with @BotFather)")
    print("3. Send ANY message to your bot (e.g., type 'hello')")
    print("4. Wait a few seconds...")
    print("\n⏳ Waiting for messages...\n")
    
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Get bot info
        bot_info = bot.get_me()
        print(f"✅ Connected to bot: @{bot_info.username}")
        print(f"   Bot name: {bot_info.first_name}")
        
        # Get updates
        updates = bot.get_updates()
        
        if not updates:
            print("\n⚠️  No messages found yet!")
            print("   Please send a message to your bot and try again")
            print("\n   Then run this script again:")
            print("   python scripts/get_telegram_chat_id.py")
            return
        
        # Display all chat IDs
        print("\n" + "="*60)
        print("✅ FOUND CHAT IDs:")
        print("="*60)
        
        seen_chat_ids = set()
        for update in updates:
            if update.message:
                chat_id = update.message.chat.id
                username = update.message.chat.username or "N/A"
                first_name = update.message.chat.first_name or "Unknown"
                
                if chat_id not in seen_chat_ids:
                    print(f"\nChat ID: {chat_id}")
                    print(f"Name: {first_name}")
                    print(f"Username: @{username}" if username != "N/A" else "Username: Not set")
                    print(f"Message: {update.message.text}")
                    seen_chat_ids.add(chat_id)
        
        print("\n" + "="*60)
        print("📝 NEXT STEPS:")
        print("="*60)
        print("\n1. Copy YOUR chat ID from above")
        print("2. Open .env file in your text editor")
        print("3. Update this line:")
        print(f"   TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE")
        print("\n4. Save the .env file")
        print("5. Test the connection:")
        print("   python notification/telegram_bot.py")
        print("\n" + "="*60)
    
    except TelegramError as e:
        print(f"\n❌ Telegram Error: {e}")
        print("\nPossible issues:")
        print("1. Invalid bot token - check your TELEGRAM_BOT_TOKEN in .env")
        print("2. Network connection issues")
        print("3. Bot was deleted or blocked")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your bot token and try again")


if __name__ == "__main__":
    get_chat_id()    