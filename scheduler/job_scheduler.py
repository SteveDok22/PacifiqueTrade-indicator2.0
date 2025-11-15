"""
Job Scheduler Module

Orchestrates the entire trading system with time-based automation:
- T-4h: Fundamental screening
- T-2h: Technical analysis
- T-15min: Signal generation
- T-0: Market reaction monitoring

Uses APScheduler for cron-style job scheduling.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import asyncio
import logging
import pytz

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import config
from core.enums import CurrencyPair, MarketSession
from core.exceptions import SchedulerError
from data import MarketDataFetcher
from analysis import (
    FundamentalAnalyzer,
    TrendDetector,
    LiquidityZoneDetector,
    SignalGenerator
)
from risk import PositionSizer, SLTPCalculator
from notification import TelegramNotifier


logger = logging.getLogger(__name__)


class TradingJob(Enum):
    """Types of trading jobs"""
    FUNDAMENTAL_SCREENING = "fundamental_screening"
    TECHNICAL_ANALYSIS = "technical_analysis"
    SIGNAL_GENERATION = "signal_generation"
    MARKET_REACTION = "market_reaction"
    DAILY_SUMMARY = "daily_summary"


class JobScheduler:
    """
    Master Job Scheduler
    
    Orchestrates all trading activities with precise timing:
    
    London Session (08:00 UTC):
      - 04:00 UTC: Fundamental screening
      - 06:00 UTC: Technical analysis
      - 07:45 UTC: Signal generation
      - 08:00 UTC: Market reaction monitoring
    
    New York Session (13:30 UTC):
      - 09:30 UTC: Fundamental screening
      - 11:30 UTC: Technical analysis
      - 13:15 UTC: Signal generation
      - 13:30 UTC: Market reaction monitoring
    
    End of Day:
      - 22:00 UTC: Daily summary
    """
    
    def __init__(self):
        """Initialize the scheduler and all components"""
        
        logger.info("Initializing JobScheduler...")
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler(timezone=pytz.UTC)
        
        # Initialize trading components
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.trend_detector = TrendDetector()
        self.liquidity_detector = LiquidityZoneDetector()
        self.signal_generator = SignalGenerator()
        self.position_sizer = PositionSizer()
        self.sltp_calculator = SLTPCalculator()
        self.market_data = MarketDataFetcher()
        
        # Initialize Telegram notifier
        self.telegram = TelegramNotifier()
        
        # Get trading pairs from config
        self.pairs = config.get_trading_pairs()
        
        # Storage for active signals
        self.active_signals: Dict[str, Dict] = {}
        self.active_trades: Dict[str, Dict] = {}
        
        logger.info(f"✅ JobScheduler initialized for pairs: {[p.value for p in self.pairs]}")