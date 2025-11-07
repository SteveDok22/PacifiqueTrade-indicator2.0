import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

async def send_test_message():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    print("="*60)
    print("TESTING TELEGRAM MESSAGE SENDING")
    print("="*60)
    print(f"\nBot Token: {token[:20]}...")
    print(f"Chat ID: {chat_id}")
    
    bot = Bot(token=token)
    
    try:
        async with bot:
            print("\n📤 Sending test message...")
            
            message = """
🤖 <b>PacifiqueTrade Indicator 2.0</b>

✅ Telegram connection is working!

This is a test message from your trading indicator bot.

<b>System Status:</b>
- Bot Token: Valid ✅
- Chat ID: Connected ✅
- API: Working ✅

<i>Ready to start trading analysis!</i>
"""
            
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            print("✅ Message sent successfully!")
            print("\n📱 Check your Telegram - you should see the message!")
            print("="*60)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPossible issues:")
        print("1. Check TELEGRAM_CHAT_ID in .env is correct")
        print("2. Make sure bot token is valid")

asyncio.run(send_test_message())