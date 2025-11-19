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
                
     def _run_signal_generation(self, session: str):
        """
        T-15min: Signal generation
        
        - Detect liquidity zones
        - Combine all factors
        - Calculate SL/TP
        - Send READY TO TRADE alert
        """
        logger.info(f"{'='*60}")
        logger.info(f"RUNNING: Signal Generation ({session} session)")
        logger.info(f"{'='*60}")
        
        try:
            pairs_to_analyze = []
            
            # Find pairs with confirmed signals
            for signal_key in list(self.active_signals.keys()):
                if session in signal_key:
                    pair_name = signal_key.split('_')[0]
                    pair = next((p for p in self.pairs if p.value == pair_name), None)
                    if pair:
                        pairs_to_analyze.append(pair)
            
            if not pairs_to_analyze:
                logger.info("No pairs ready for signal generation")
                return
            
            # Generate signals
            signals = self.signal_generator.generate_signals(pairs_to_analyze)
            
            if not signals:
                logger.info("No valid signals generated")
                return
            
            # Calculate position sizes and SL/TP for each signal
            for pair_name, signal in signals.items():
                try:
                    # Calculate position size
                    position = self.position_sizer.calculate_position_size(
                        pair=signal.pair,
                        entry_price=signal.entry_price,
                        stop_loss=signal.entry_price * 0.985  # Temporary, will be calculated properly
                    )
                    
                    # Calculate SL/TP
                    sltp_levels = self.sltp_calculator.calculate_sl_tp(
                        pair=signal.pair,
                        direction=signal.direction,
                        entry_price=signal.entry_price,
                        liquidity_zones=signal.liquidity_zones
                    )
                    
                    # Update signal with risk management
                    signal.stop_loss = sltp_levels.stop_loss
                    signal.take_profit_1 = sltp_levels.take_profit_1
                    signal.take_profit_2 = sltp_levels.take_profit_2
                    signal.take_profit_3 = sltp_levels.take_profit_3
                    signal.risk_reward = sltp_levels.r_multiple_3
                    
                    # Store complete signal
                    self.active_signals[f"{pair_name}_{session}"]['complete_signal'] = {
                        'signal': signal,
                        'position': position,
                        'sltp': sltp_levels
                    }
                    
                    # Send READY TO TRADE alert
                    if self.telegram.is_enabled():
                        asyncio.run(self._send_ready_to_trade_alert(signal, position))
                    
                    logger.info(f"✅ {pair_name}: Complete signal generated")
                    
                except Exception as e:
                    logger.error(f"Failed to complete signal for {pair_name}: {e}")
                    continue
            
            logger.info(f"✅ Signal generation complete: {len(signals)} signals ready")
            
        except Exception as e:
            logger.error(f"Signal generation failed: {e}", exc_info=True)
            if self.telegram.is_enabled():
                asyncio.run(self.telegram.send_error_alert(
                    "Signal Generation Error",
                    str(e)
                ))            
    def _run_market_reaction(self, session: str):
        """
        T-0: Market reaction monitoring
        
        - Monitor first 15-30 minutes after open
        - Check volume and price action
        - Confirm or cancel entry
        """
        logger.info(f"{'='*60}")
        logger.info(f"RUNNING: Market Reaction Monitor ({session} session)")
        logger.info(f"{'='*60}")
        
        try:
            # Find signals for this session
            for signal_key in list(self.active_signals.keys()):
                if session not in signal_key:
                    continue
                
                signal_data = self.active_signals[signal_key].get('complete_signal')
                if not signal_data:
                    continue
                
                signal = signal_data['signal']
                pair = signal.pair
                
                # Get current price
                current_price = self.market_data.get_current_price(pair)
                
                # Simple validation: check if price moved in expected direction
                direction = signal.direction
                entry = signal.entry_price
                
                # TODO: Add volume analysis and more sophisticated confirmation
                # For now, simple price movement check
                
                if direction == 'long':
                    confirmed = current_price >= entry * 0.999  # Within 0.1%
                else:
                    confirmed = current_price <= entry * 1.001
                
                # Send notification
                if self.telegram.is_enabled():
                    if confirmed:
                        asyncio.run(self.telegram.send_entry_confirmed(
                            pair=pair.value,
                            direction=direction,
                            entry_price=current_price,
                            volume_increase=150.0,  # Placeholder
                            reaction_type="Price confirms direction"
                        ))
                    else:
                        asyncio.run(self.telegram.send_entry_cancelled(
                            pair=pair.value,
                            direction=direction,
                            reason="Price moved against expected direction"
                        ))
                
                # Move to active trades if confirmed
                if confirmed:
                    self.active_trades[pair.value] = signal_data
                    logger.info(f"✅ {pair.value}: Entry confirmed, moved to active trades")
                else:
                    logger.info(f"❌ {pair.value}: Entry cancelled")
                
                # Remove from active signals
                del self.active_signals[signal_key]
            
            logger.info(f"✅ Market reaction monitoring complete")
            
        except Exception as e:
            logger.error(f"Market reaction monitoring failed: {e}", exc_info=True)
            if self.telegram.is_enabled():
                asyncio.run(self.telegram.send_error_alert(
                    "Market Reaction Error",
                    str(e)
                ))            
                
    def _run_daily_summary(self):
        """
        End of day: Daily summary
        
        - Summarize today's signals and trades
        - Calculate P&L
        - Send summary to Telegram
        """
        logger.info(f"{'='*60}")
        logger.info(f"RUNNING: Daily Summary")
        logger.info(f"{'='*60}")
        
        try:
            # TODO: Implement full daily summary with trade tracking
            
            logger.info(f"Active signals: {len(self.active_signals)}")
            logger.info(f"Active trades: {len(self.active_trades)}")
            
            # Clear old signals
            self.active_signals.clear()
            
            logger.info(f"✅ Daily summary complete")
            
        except Exception as e:
            logger.error(f"Daily summary failed: {e}", exc_info=True)    
            
    # ==================================================================
    # HELPER METHODS
    # ==================================================================
    
    def _check_trend_alignment(self, fundamental, trend) -> bool:
        """Check if trend aligns with fundamental"""
        fund_dir = fundamental.direction.value
        trend_dir = trend.direction.value
        
        if 'stronger' in fund_dir.lower() or 'bullish' in fund_dir.lower():
            return trend_dir == 'bullish'
        elif 'weaker' in fund_dir.lower() or 'bearish' in fund_dir.lower():
            return trend_dir == 'bearish'
        
        return False
    
    async def _send_startup_notification(self):
        """Send startup notification"""
        await self.telegram.send_message(
            "🚀 <b>PacifiqueTrade Indicator 2.0 Started</b>\n\n"
            f"✅ System initialized\n"
            f"📊 Monitoring: {', '.join([p.value for p in self.pairs])}\n"
            f"⏰ Scheduler: Active\n\n"
            "Ready to trade! 📈",
            parse_mode='HTML'
        )
    
    async def _send_fundamental_alert(self, pair_name, signal):
        """Send fundamental alert to Telegram"""
        events = signal.events
        if not events:
            return
        
        event = events[0]  # Main event
        
        await self.telegram.send_pre_market_alert(
            pair=pair_name,
            fundamental_signal={
                'direction': signal.direction.value,
                'event_name': event.event_name,
                'forecast': event.forecast or 'N/A',
                'previous': event.previous or 'N/A',
                'impact': 'HIGH',
                'time_to_open': '4 hours'
            }
        )
    
    async def _send_technical_alert(self, pair_name, fundamental, trends, confirms):
        """Send technical confirmation alert"""
        trend_h4 = trends['H4']
        trend_h1 = trends['H1']
        
        await self.telegram.send_technical_confirmation(
            pair=pair_name,
            fundamental_direction=fundamental.direction.value,
            trend_h4={
                'direction': trend_h4.direction.value,
                'strength': trend_h4.strength.value,
                'ema50': trend_h4.ema50,
                'ema200': trend_h4.ema200,
                'current_price': trend_h4.current_price
            },
            trend_h1={
                'direction': trend_h1.direction.value,
                'strength': trend_h1.strength.value
            },
            confirms=confirms
        )
    
    async def _send_ready_to_trade_alert(self, signal, position):
        """Send ready to trade alert"""
        signal_dict = {
            'pair': signal.pair.value,
            'direction': signal.direction.upper(),
            'strength': signal.strength.value,
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'tp1': signal.take_profit_1,
            'tp2': signal.take_profit_2,
            'tp3': signal.take_profit_3,
            'position_size_lots': position.position_size_lots,
            'risk_amount': position.risk_amount,
            'risk_reward': signal.risk_reward,
            'entry_zone_type': signal.entry_zone.zone_type.value if signal.entry_zone else None,
            'entry_zone_level': signal.entry_zone.price_level if signal.entry_zone else None
        }
        
        await self.telegram.send_ready_to_trade(signal_dict, with_buttons=True)
                
def main():
    """Test the Job Scheduler"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("JOB SCHEDULER TEST")
    print("="*60 + "\n")
    
    try:
        # Create scheduler
        scheduler = JobScheduler()
        
        print("✅ JobScheduler initialized\n")
        print("Configured pairs:")
        for pair in scheduler.pairs:
            print(f"  • {pair.value}")
        
        print("\nTelegram enabled:", scheduler.telegram.is_enabled())
        
        print("\n" + "-"*60)
        print("To start the scheduler in production:")
        print("  1. Ensure .env is properly configured")
        print("  2. Run: python main.py --schedule")
        print("  3. The system will run continuously")
        print("-"*60)
        
        print("\n" + "="*60)
        print("✅ JOB SCHEDULER TEST COMPLETE!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())                