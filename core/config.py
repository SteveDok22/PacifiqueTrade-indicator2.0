"""
Configuration Management for PacifiqueTrade Indicator 2.0

Loads and validates all configuration from environment variables (.env file).
Provides centralized access to all system settings with type safety and validation.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from dotenv import load_dotenv


logger = logging.getLogger(__name__)


class Config:
    """
    Configuration Manager
    
    Loads configuration from .env file and provides validated access
    to all system settings. Includes validation methods to ensure
    proper configuration before system startup.
    """
    
    VERSION = "2.0.0"
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        
        # Load .env file
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"✅ Loaded configuration from {env_path}")
        else:
            logger.warning(f"⚠️  .env file not found at {env_path}")
        
        # =================================================================
        # TRADING CONFIGURATION
        # =================================================================
        
        # Trading pairs
        self.TRADING_PAIRS_STR = os.getenv('TRADING_PAIRS', 'GBP/USD,EUR/USD,USD/JPY')
        
        # Account settings
        self.ACCOUNT_BALANCE = float(os.getenv('ACCOUNT_BALANCE', '10000'))
        self.RISK_PERCENTAGE = float(os.getenv('RISK_PERCENTAGE', '1.0'))
        self.LEVERAGE = int(os.getenv('LEVERAGE', '1'))
        
        # Risk management
        self.MIN_R_MULTIPLE = float(os.getenv('MIN_R_MULTIPLE', '3.0'))
        self.MAX_OPEN_TRADES = int(os.getenv('MAX_OPEN_TRADES', '3'))
        self.MAX_CORRELATION = float(os.getenv('MAX_CORRELATION', '0.7'))
        
        # Position management (3-part system)
        self.SL_PART1 = int(os.getenv('SL_PART1', '33'))  # %
        self.SL_PART2 = int(os.getenv('SL_PART2', '33'))  # %
        self.SL_PART3 = int(os.getenv('SL_PART3', '34'))  # %
        
        # =================================================================
        # TELEGRAM CONFIGURATION
        # =================================================================
        
        self.TELEGRAM_ENABLED = self._get_bool('TELEGRAM_ENABLED', False)
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # Alert levels configuration
        self.ALERT_LEVEL_PRE_MARKET = self._get_bool('ALERT_LEVEL_PRE_MARKET', True)
        self.ALERT_LEVEL_TECHNICAL_CONFIRM = self._get_bool('ALERT_LEVEL_TECHNICAL_CONFIRM', True)
        self.ALERT_LEVEL_READY_TO_TRADE = self._get_bool('ALERT_LEVEL_READY_TO_TRADE', True)
        self.ALERT_LEVEL_ENTRY_CONFIRM = self._get_bool('ALERT_LEVEL_ENTRY_CONFIRM', True)
        self.ALERT_LEVEL_ERROR = self._get_bool('ALERT_LEVEL_ERROR', True)
        
        # =================================================================
        # PAIR-SPECIFIC CONFIGURATION
        # =================================================================
        
        # Pip values and specifications for each currency pair
        self.PAIR_CONFIG = {
            'GBP/USD': {
                'pip_value': 0.0001,      # Standard pip size
                'pip_decimals': 5,         # Decimal places (1.26543)
                'lot_size': 100000,        # Standard lot = 100,000 units
                'min_lot': 0.01,           # Minimum lot size
                'max_lot': 100.0,          # Maximum lot size
                'spread_avg': 1.5,         # Average spread in pips
            },
            'EUR/USD': {
                'pip_value': 0.0001,
                'pip_decimals': 5,
                'lot_size': 100000,
                'min_lot': 0.01,
                'max_lot': 100.0,
                'spread_avg': 1.2,
            },
            'USD/JPY': {
                'pip_value': 0.01,         # JPY pairs use 0.01
                'pip_decimals': 3,         # Decimal places (149.543)
                'lot_size': 100000,
                'min_lot': 0.01,
                'max_lot': 100.0,
                'spread_avg': 1.8,
            },
        }
        
        # =================================================================
        # TECHNICAL ANALYSIS SETTINGS
        # =================================================================
        
        # EMA settings
        self.EMA_FAST = int(os.getenv('EMA_FAST', '50'))
        self.EMA_SLOW = int(os.getenv('EMA_SLOW', '200'))
        
        # Liquidity zones
        self.EQUAL_LEVEL_TOLERANCE = float(os.getenv('EQUAL_LEVEL_TOLERANCE', '0.0015'))
        self.MIN_TOUCHES = int(os.getenv('MIN_TOUCHES', '2'))
        self.FVG_MIN_SIZE = float(os.getenv('FVG_MIN_SIZE', '0.0005'))
        
        # =================================================================
        # MARKET DATA SETTINGS
        # =================================================================
        
        self.YFINANCE_MAX_RETRIES = int(os.getenv('YFINANCE_MAX_RETRIES', '3'))
        self.YFINANCE_RETRY_DELAY = int(os.getenv('YFINANCE_RETRY_DELAY', '2'))
        self.DATA_LOOKBACK_DAYS = int(os.getenv('DATA_LOOKBACK_DAYS', '90'))
        self.MIN_BARS_M15 = int(os.getenv('MIN_BARS_M15', '100'))
        self.MIN_BARS_M30 = int(os.getenv('MIN_BARS_M30', '100'))
        self.MIN_BARS_H1 = int(os.getenv('MIN_BARS_H1', '200'))
        self.MIN_BARS_H4 = int(os.getenv('MIN_BARS_H4', '200'))
        self.MIN_BARS_D1 = int(os.getenv('MIN_BARS_D1', '100'))
       
        
        # =================================================================
        # REDIS CACHE SETTINGS
        # =================================================================
        
        self.REDIS_ENABLED = self._get_bool('REDIS_ENABLED', False)
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
        self.REDIS_DB = int(os.getenv('REDIS_DB', '0'))
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
        self.CACHE_TTL_SHORT = int(os.getenv('CACHE_TTL_SHORT', '300'))
        self.CACHE_TTL_MEDIUM = int(os.getenv('CACHE_TTL_MEDIUM', '3600'))
        self.CACHE_TTL_LONG = int(os.getenv('CACHE_TTL_LONG', '86400'))
        
        # =================================================================
        # LOGGING SETTINGS
        # =================================================================
        
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/pacifique_trade.log')
        self.LOG_COLOR_ENABLED = self._get_bool('LOG_COLOR_ENABLED', True)
        self.LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        
        # Create logs directory if it doesn't exist
        log_dir = Path(self.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # =================================================================
        # SYSTEM SETTINGS
        # =================================================================
        
        self.DRY_RUN = self._get_bool('DRY_RUN', True)
        self.TIMEZONE = os.getenv('TIMEZONE', 'UTC')
        
        # Backtesting
        self.BACKTEST_START_DATE = os.getenv('BACKTEST_START_DATE', '2024-01-01')
        self.BACKTEST_END_DATE = os.getenv('BACKTEST_END_DATE', '2024-12-31')
        
        logger.info("✅ Configuration loaded successfully")
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def get_trading_pairs(self) -> List:
        """
        Get list of CurrencyPair enums
        
        Returns:
            List of CurrencyPair enum values
        """
        from core.enums import CurrencyPair
        
        pairs = []
        for pair_str in self.TRADING_PAIRS_STR.split(','):
            pair_str = pair_str.strip()
            try:
                pair = CurrencyPair(pair_str)
                pairs.append(pair)
            except ValueError:
                logger.warning(f"Invalid currency pair in config: {pair_str}")
        
        return pairs
    
    def get_alert_levels(self) -> List:
        """
        Get enabled alert levels
        
        Returns:
            List of enabled AlertLevel enums
        """
        from core.enums import AlertLevel
        
        levels = []
        if self.ALERT_LEVEL_PRE_MARKET:
            levels.append(AlertLevel.PRE_MARKET)
        if self.ALERT_LEVEL_TECHNICAL_CONFIRM:
            levels.append(AlertLevel.TECHNICAL_CONFIRM)
        if self.ALERT_LEVEL_READY_TO_TRADE:
            levels.append(AlertLevel.READY_TO_TRADE)
        if self.ALERT_LEVEL_ENTRY_CONFIRM:
            levels.append(AlertLevel.ENTRY_CONFIRM)
        if self.ALERT_LEVEL_ERROR:
            levels.append(AlertLevel.ERROR)
        
        return levels
    
    def validate_telegram(self) -> bool:
        """Validate Telegram configuration"""
        if not self.TELEGRAM_ENABLED:
            return True
        
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required when Telegram is enabled")
        
        if not self.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CHAT_ID is required when Telegram is enabled")
        
        return True
    
    def validate_trading_config(self) -> bool:
        """Validate trading configuration"""
        if self.ACCOUNT_BALANCE <= 0:
            raise ValueError("ACCOUNT_BALANCE must be positive")
        
        if not (0 < self.RISK_PERCENTAGE <= 5):
            raise ValueError("RISK_PERCENTAGE must be between 0 and 5")
        
        if self.LEVERAGE < 1:
            raise ValueError("LEVERAGE must be at least 1")
        
        if self.MIN_R_MULTIPLE < 1:
            raise ValueError("MIN_R_MULTIPLE must be at least 1")
        
        # Validate position splits add up to 100%
        total_split = self.SL_PART1 + self.SL_PART2 + self.SL_PART3
        if total_split != 100:
            raise ValueError(f"Position splits must add to 100%, got {total_split}%")
        
        return True
    
    def validate_redis(self) -> bool:
        """Validate Redis configuration"""
        if not self.REDIS_ENABLED:
            return True
        
        if self.REDIS_PORT < 1 or self.REDIS_PORT > 65535:
            raise ValueError("REDIS_PORT must be between 1 and 65535")
        
        return True
    
    def validate_all(self) -> bool:
        """
        Validate all configuration
        
        Returns:
            True if all valid
            
        Raises:
            ValueError: If any configuration is invalid
        """
        self.validate_telegram()
        self.validate_trading_config()
        self.validate_redis()
        
        logger.info("✅ All configuration validated successfully")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return {
            'version': self.VERSION,
            'trading': {
                'pairs': self.TRADING_PAIRS_STR,
                'account_balance': self.ACCOUNT_BALANCE,
                'risk_percentage': self.RISK_PERCENTAGE,
                'leverage': self.LEVERAGE,
                'min_r_multiple': self.MIN_R_MULTIPLE,
            },
            'telegram': {
                'enabled': self.TELEGRAM_ENABLED,
                'configured': bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID),
            },
            'system': {
                'dry_run': self.DRY_RUN,
                'log_level': self.LOG_LEVEL,
                'timezone': self.TIMEZONE,
            }
        }
    
    def __repr__(self) -> str:
        """String representation"""
        return f"Config(version={self.VERSION}, pairs={self.TRADING_PAIRS_STR})"


# Global config instance
config = Config()