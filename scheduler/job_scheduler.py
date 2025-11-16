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
        
    def start(self):
        """Start the scheduler"""
        
        logger.info("Starting JobScheduler...")
        
        try:
            # Schedule London session jobs
            self._schedule_london_session()
            
            # Schedule New York session jobs
            self._schedule_newyork_session()
            
            # Schedule daily summary
            self._schedule_daily_summary()
            
            # Start the scheduler
            self.scheduler.start()
            
            logger.info("✅ JobScheduler started successfully!")
            logger.info("Scheduled jobs:")
            for job in self.scheduler.get_jobs():
                logger.info(f"  - {job.name} (Next run: {job.next_run_time})")
            
            # Send startup notification
            if self.telegram.is_enabled():
                asyncio.run(self._send_startup_notification())
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise SchedulerError(
                job_name="startup",
                message=str(e)
            )
    
    def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping JobScheduler...")
        self.scheduler.shutdown()
        logger.info("✅ JobScheduler stopped")
        
    def _schedule_london_session(self):
        """Schedule jobs for London session (08:00 UTC)"""
        
        # T-4h: Fundamental screening (04:00 UTC)
        self.scheduler.add_job(
            func=self._run_fundamental_screening,
            trigger=CronTrigger(hour=4, minute=0, timezone=pytz.UTC),
            args=['London'],
            id='london_fundamental',
            name='London: Fundamental Screening (T-4h)',
            misfire_grace_time=300  # 5 minutes grace
        )
        
        # T-2h: Technical analysis (06:00 UTC)
        self.scheduler.add_job(
            func=self._run_technical_analysis,
            trigger=CronTrigger(hour=6, minute=0, timezone=pytz.UTC),
            args=['London'],
            id='london_technical',
            name='London: Technical Analysis (T-2h)',
            misfire_grace_time=300
        )
        
        # T-15min: Signal generation (07:45 UTC)
        self.scheduler.add_job(
            func=self._run_signal_generation,
            trigger=CronTrigger(hour=7, minute=45, timezone=pytz.UTC),
            args=['London'],
            id='london_signals',
            name='London: Signal Generation (T-15min)',
            misfire_grace_time=120
        )
        
        # T-0: Market reaction (08:00 UTC)
        self.scheduler.add_job(
            func=self._run_market_reaction,
            trigger=CronTrigger(hour=8, minute=0, timezone=pytz.UTC),
            args=['London'],
            id='london_reaction',
            name='London: Market Reaction Monitor (T-0)',
            misfire_grace_time=60
        )
        
        logger.info("✅ London session jobs scheduled")
    
    def _schedule_newyork_session(self):
        """Schedule jobs for New York session (13:30 UTC)"""
        
        # T-4h: Fundamental screening (09:30 UTC)
        self.scheduler.add_job(
            func=self._run_fundamental_screening,
            trigger=CronTrigger(hour=9, minute=30, timezone=pytz.UTC),
            args=['NewYork'],
            id='ny_fundamental',
            name='NY: Fundamental Screening (T-4h)',
            misfire_grace_time=300
        )
        
        # T-2h: Technical analysis (11:30 UTC)
        self.scheduler.add_job(
            func=self._run_technical_analysis,
            trigger=CronTrigger(hour=11, minute=30, timezone=pytz.UTC),
            args=['NewYork'],
            id='ny_technical',
            name='NY: Technical Analysis (T-2h)',
            misfire_grace_time=300
        )
        
        # T-15min: Signal generation (13:15 UTC)
        self.scheduler.add_job(
            func=self._run_signal_generation,
            trigger=CronTrigger(hour=13, minute=15, timezone=pytz.UTC),
            args=['NewYork'],
            id='ny_signals',
            name='NY: Signal Generation (T-15min)',
            misfire_grace_time=120
        )
        
        # T-0: Market reaction (13:30 UTC)
        self.scheduler.add_job(
            func=self._run_market_reaction,
            trigger=CronTrigger(hour=13, minute=30, timezone=pytz.UTC),
            args=['NewYork'],
            id='ny_reaction',
            name='NY: Market Reaction Monitor (T-0)',
            misfire_grace_time=60
        )
        
        logger.info("✅ New York session jobs scheduled")    
        
    def _schedule_daily_summary(self):
        """Schedule daily summary (22:00 UTC)"""
        
        self.scheduler.add_job(
            func=self._run_daily_summary,
            trigger=CronTrigger(hour=22, minute=0, timezone=pytz.UTC),
            id='daily_summary',
            name='Daily Summary',
            misfire_grace_time=600
        )
        
        logger.info("✅ Daily summary job scheduled")    
        
    # ==================================================================
    # JOB EXECUTION METHODS
    # ==================================================================
    
    def _run_fundamental_screening(self, session: str):
        """
        T-4h: Fundamental screening
        
        - Fetch economic calendar
        - Filter high-impact news
        - Send Telegram alert
        """
        logger.info(f"{'='*60}")
        logger.info(f"RUNNING: Fundamental Screening ({session} session)")
        logger.info(f"{'='*60}")
        
        try:
            # Run fundamental analysis
            fundamental_signals = self.fundamental_analyzer.analyze_today(self.pairs)
            
            if not fundamental_signals:
                logger.info("No high-impact news today")
                return
            
            # Store signals
            for pair_name, signal in fundamental_signals.items():
                self.active_signals[f"{pair_name}_{session}"] = {
                    'session': session,
                    'fundamental': signal,
                    'timestamp': datetime.now(pytz.UTC)
                }
            
            # Send Telegram alerts
            if self.telegram.is_enabled():
                for pair_name, signal in fundamental_signals.items():
                    asyncio.run(self._send_fundamental_alert(pair_name, signal))
            
            logger.info(f"✅ Fundamental screening complete: {len(fundamental_signals)} signals")
            
        except Exception as e:
            logger.error(f"Fundamental screening failed: {e}", exc_info=True)
            if self.telegram.is_enabled():
                asyncio.run(self.telegram.send_error_alert(
                    "Fundamental Screening Error",
                    str(e)
                ))    
                
     def _run_technical_analysis(self, session: str):
        """
        T-2h: Technical analysis
        
        - Analyze H4 and H1 trends
        - Compare with fundamental
        - Send confirmation alert
        """
        logger.info(f"{'='*60}")
        logger.info(f"RUNNING: Technical Analysis ({session} session)")
        logger.info(f"{'='*60}")
        
        try:
            for pair in self.pairs:
                signal_key = f"{pair.value}_{session}"
                
                if signal_key not in self.active_signals:
                    logger.debug(f"No fundamental signal for {pair.value}, skipping")
                    continue
                
                # Analyze trends
                trends = self.trend_detector.analyze_multi_timeframe(pair)
                
                # Store in signal
                self.active_signals[signal_key]['trends'] = trends
                
                # Check alignment
                fundamental = self.active_signals[signal_key]['fundamental']
                confirms = self._check_trend_alignment(fundamental, trends['H4'])
                
                # Send Telegram alert
                if self.telegram.is_enabled():
                    asyncio.run(self._send_technical_alert(
                        pair.value, fundamental, trends, confirms
                    ))
                
                if not confirms:
                    logger.info(f"❌ {pair.value}: Trend doesn't confirm fundamental, removing signal")
                    del self.active_signals[signal_key]
                else:
                    logger.info(f"✅ {pair.value}: Trend confirms fundamental")
            
            logger.info(f"✅ Technical analysis complete")
            
        except Exception as e:
            logger.error(f"Technical analysis failed: {e}", exc_info=True)
            if self.telegram.is_enabled():
                asyncio.run(self.telegram.send_error_alert(
                    "Technical Analysis Error",
                    str(e)
                ))
                
                