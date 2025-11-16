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