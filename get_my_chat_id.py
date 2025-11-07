import asyncio
from telegram import Bot
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    print("\n" + "="*60)
    print("GETTING YOUR TELEGRAM CHAT ID")
    print("="*60)
    
    bot = Bot(token=token)
    
    async with bot:
        # Get bot info
        me = await bot.get_me()
        print(f"\n✅ Bot: @{me.username}")
        
        # Get updates
        updates = await bot.get_updates()
        
        print(f"\n📩 Found {len(updates)} messages")
        
        if updates:
            print("\n" + "="*60)
            print("YOUR CHAT IDs:")
            print("="*60)
            
            for update in updates:
                if update.message:
                    chat_id = update.message.chat.id
                    name = update.message.chat.first_name
                    print(f"\n👤 Name: {name}")
                    print(f"🆔 CHAT ID: {chat_id}")
                    print(f"💬 Message: {update.message.text}")
                    print("-" * 60)
        else:
            print("\n❌ No messages found!")
            print("\n📱 Please:")
            print("1. Open Telegram")
            print(f"2. Find your bot: @{me.username}")
            print("3. Send a message (any text)")
            print("4. Run this script again")
    
    print("\n" + "="*60)
    print("NEXT STEP:")
    print("="*60)
    print("\nCopy your CHAT ID number above")
    print("Update .env file:")
    print("TELEGRAM_CHAT_ID=YOUR_NUMBER_HERE")
    print("="*60 + "\n")

asyncio.run(main())