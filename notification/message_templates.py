"""
Message Templates Module

Formats messages for Telegram notifications.
Creates beautiful, readable alerts with emojis and formatting.
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import AlertLevel, TrendDirection, SignalStrength


logger = logging.getLogger(__name__)