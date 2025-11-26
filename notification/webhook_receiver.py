"""
TradingView Webhook Receiver

Receives webhook alerts from TradingView Pine Script
and forwards them to Telegram
"""

from flask import Flask, request, jsonify
import asyncio
import json
import logging
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from notification import TelegramNotifier
from core.config import config

logger = logging.getLogger(__name__)

app = Flask(__name__)
telegram = TelegramNotifier()


@app.route('/webhook/tradingview', methods=['POST'])
def tradingview_webhook():
    """
    Receive webhook from TradingView
    
    Expected JSON format:
    {
        "type": "LONG_ENTRY" or "SHORT_ENTRY",
        "pair": "GBPUSD",
        "price": 1.2700,
        "fvg_top": 1.2710,
        "fvg_bottom": 1.2690
    }
    """
    try:
        # Get webhook data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        logger.info(f"Received TradingView webhook: {data}")
        
        # Extract data
        signal_type = data.get('type')
        pair = data.get('pair')
        price = data.get('price')
        fvg_top = data.get('fvg_top')
        fvg_bottom = data.get('fvg_bottom')
        
        # Validate
        if not all([signal_type, pair, price]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Format pair (GBPUSD → GBP/USD)
        if '/' not in pair:
            pair = f"{pair[:3]}/{pair[3:]}"
        
        # Send to Telegram
        message = format_entry_zone_alert(
            signal_type, pair, price, fvg_top, fvg_bottom
        )
        
        # Send async
        asyncio.run(telegram.send_message(message, parse_mode='HTML'))
        
        logger.info(f"✅ Webhook processed and sent to Telegram")
        
        return jsonify({"status": "success", "message": "Alert sent"}), 200
    
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def format_entry_zone_alert(
    signal_type: str,
    pair: str,
    price: float,
    fvg_top: float = None,
    fvg_bottom: float = None
) -> str:
    """Format Entry Zone alert for Telegram"""
    
    direction_emoji = "🟢" if "LONG" in signal_type else "🔴"
    direction = "LONG" if "LONG" in signal_type else "SHORT"
    
    message = f"""
🎯 <b>TRADINGVIEW ENTRY ZONE DETECTED</b> 🎯

{direction_emoji} <b>Pair:</b> {pair}
📍 <b>Direction:</b> {direction}
💰 <b>Current Price:</b> {price:.5f}
"""
    
    if fvg_top and fvg_bottom:
        message += f"""
📦 <b>FVG Zone:</b>
  • Top: {fvg_top:.5f}
  • Bottom: {fvg_bottom:.5f}
  • Size: {(fvg_top - fvg_bottom):.5f} ({((fvg_top - fvg_bottom)/price*100):.2f}%)
"""
    
    message += f"""
✅ <b>Conditions Met:</b>
  • Liquidity Sweep ✅
  • RSI Extremum ✅
  • Volume Burst ✅
  • FVG Zone ✅

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S UTC')}

🔔 <b>This is an AUTOMATIC alert from TradingView!</b>
Check the chart immediately!
"""
    
    return message.strip()


@app.route('/health', methods=['GET'])