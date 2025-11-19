"""
PacifiqueTrade Indicator 2.0 - Main Entry Point

This is the main entry point for the trading indicator system.
Run this file to start the indicator in scheduled mode.
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import Config, config
from core.exceptions import PacifiqueTradeError, ConfigurationError


# ASCII Art Logo
LOGO = r"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██████╗  █████╗  ██████╗██╗███████╗██╗ ██████╗ ██╗   ██╗███████╗║
║   ██╔══██╗██╔══██╗██╔════╝██║██╔════╝██║██╔═══██╗██║   ██║██╔════╝║
║   ██████╔╝███████║██║     ██║█████╗  ██║██║   ██║██║   ██║█████╗  ║
║   ██╔═══╝ ██╔══██║██║     ██║██╔══╝  ██║██║▄▄ ██║██║   ██║██╔══╝  ║
║   ██║     ██║  ██║╚██████╗██║██║     ██║╚██████╔╝╚██████╔╝███████╗║
║   ╚═╝     ╚═╝  ╚═╝ ╚═════╝╚═╝╚═╝     ╚═╝ ╚══▀▀═╝  ╚═════╝ ╚══════╝║
║                                                           ║
║             T R A D E   I N D I C A T O R   2.0           ║
║                                                           ║
║                                                           ║
║               Built by Stiven | Version 2.0.0             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""

def setup_logging():
    """Configure logging for the application"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if config.LOG_COLOR_ENABLED:
        try:
            import colorlog
            formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        except ImportError:
            formatter = logging.Formatter(log_format)
    else:
        formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="PacifiqueTrade Indicator 2.0 - Forex Trading Signal System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Run in scheduled mode (default)
  python main.py --manual                 # Run manual analysis for today
  python main.py --pair GBP/USD           # Analyze specific pair
  python main.py --backtest               # Run backtesting mode
  python main.py --validate-config        # Validate configuration only
        """
    )
    
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run in scheduled mode (default)'
    )
    
    parser.add_argument(
        '--manual',
        action='store_true',
        help='Run manual analysis for today'
    )
    
    parser.add_argument(
        '--pair',
        type=str,
        choices=['GBP/USD', 'EUR/USD', 'USD/JPY'],
        help='Analyze specific currency pair'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        default='today',
        help='Date for analysis (YYYY-MM-DD or "today"/"tomorrow")'
    )
    
    parser.add_argument(
        '--backtest',
        action='store_true',
        help='Run backtesting mode'
    )
    
    parser.add_argument(
        '--start',
        type=str,
        help='Backtest start date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end',
        type=str,
        help='Backtest end date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration and exit'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'PacifiqueTrade Indicator {Config.VERSION}'
    )
    
    return parser.parse_args()

def print_system_info(logger):
    """Print system information and configuration"""
    logger.info("=" * 60)
    logger.info(f"PacifiqueTrade Indicator {Config.VERSION}")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("=" * 60)
    logger.info(f"Trading Pairs: {config.TRADING_PAIRS_STR}")
    logger.info(f"Risk per Trade: {config.RISK_PERCENTAGE}%")
    logger.info(f"Account Balance: ${config.ACCOUNT_BALANCE:,.2f}")
    logger.info(f"Telegram Alerts: {'Enabled' if config.TELEGRAM_ENABLED else 'Disabled'}")
    logger.info(f"Redis Cache: {'Enabled' if config.REDIS_ENABLED else 'Disabled'}")
    logger.info(f"Mode: {'DRY RUN' if config.DRY_RUN else '⚠️  LIVE TRADING ⚠️'}")
    logger.info("=" * 60)
    
def run_scheduled_mode(logger):
    """Run the indicator in scheduled mode"""
    logger.info("Starting scheduled mode...")
    logger.info("Indicator will monitor markets and send alerts based on schedule")
    
    try:
        from scheduler import JobScheduler
        
        scheduler = JobScheduler()
        scheduler.start()
        
        logger.info("\n" + "="*60)
        logger.info("🚀 PACIFIQUETRADE INDICATOR 2.0 - RUNNING")
        logger.info("="*60)
        logger.info("The system is now monitoring markets 24/7")
        logger.info("You will receive Telegram alerts at:")
        logger.info("  • T-4h: Pre-market fundamental screening")
        logger.info("  • T-2h: Technical confirmation")
        logger.info("  • T-15min: READY TO TRADE signals")
        logger.info("  • T-0: Entry confirmation")
        logger.info("\nPress Ctrl+C to stop")
        logger.info("="*60 + "\n")
        
        # Keep running
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping scheduler...")
        scheduler.stop()
        logger.info("✅ Shutdown complete")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        raise    