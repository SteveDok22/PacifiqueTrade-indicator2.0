"""
Configuration management for PacifiqueTrade Indicator 2.0

Loads configuration from environment variables and provides
a centralized config object for the entire system.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)


class Config:
    """Central configuration class for PacifiqueTrade Indicator"""
    
    # ==========================================================================
    # APPLICATION INFO
    # ==========================================================================
    APP_NAME = "PacifiqueTrade Indicator"
    VERSION = "2.0.0"
    AUTHOR = "Stiven"
    
    # ==========================================================================
    # TELEGRAM CONFIGURATION
    # ==========================================================================
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "true").lower() == "true"
    
    @classmethod
    def validate_telegram_config(cls):
        """Validate Telegram configuration"""
        if cls.TELEGRAM_ENABLED:
            if not cls.TELEGRAM_BOT_TOKEN:
                from .exceptions import ConfigurationError
                raise ConfigurationError(
                    "TELEGRAM_BOT_TOKEN",
                    "Required when TELEGRAM_ENABLED=true"
                )
            if not cls.TELEGRAM_CHAT_ID:
                from .exceptions import ConfigurationError
                raise ConfigurationError(
                    "TELEGRAM_CHAT_ID",
                    "Required when TELEGRAM_ENABLED=true"
                )
    
    # ==========================================================================
    # TRADING CONFIGURATION
    # ==========================================================================
    TRADING_PAIRS_STR = os.getenv("TRADING_PAIRS", "GBP/USD,EUR/USD,USD/JPY")
    RISK_PERCENTAGE = float(os.getenv("RISK_PERCENTAGE", "1.0"))
    ACCOUNT_BALANCE = float(os.getenv("ACCOUNT_BALANCE", "10000"))
    LEVERAGE = int(os.getenv("LEVERAGE", "1"))
    MIN_R_MULTIPLE = float(os.getenv("MIN_R_MULTIPLE", "3"))
    
    # ==========================================================================
    # MARKET TIMING CONFIGURATION (UTC)
    # ==========================================================================
    LONDON_OPEN = os.getenv("LONDON_OPEN", "08:00")
    NEWYORK_OPEN = os.getenv("NEWYORK_OPEN", "13:30")
    TOKYO_OPEN = os.getenv("TOKYO_OPEN", "00:00")
    PRE_MARKET_ENABLED = os.getenv("PRE_MARKET_ENABLED", "true").lower() == "true"
    
    # Pre-market timing offsets (in hours before market open)
    T_4H_OFFSET = 4  # Fundamental screening
    T_2H_OFFSET = 2  # Technical analysis
    T_15MIN_OFFSET = 0.25  # Final liquidity check (15 minutes)
    
    TIMEZONE = pytz.UTC
    
    # ==========================================================================
    # API CONFIGURATION
    # ==========================================================================
    FOREX_FACTORY_URL = os.getenv(
        "FOREX_FACTORY_URL",
        "https://www.forexfactory.com/calendar.php"
    )
    YFINANCE_ENABLED = os.getenv("YFINANCE_ENABLED", "true").lower() == "true"
    
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "30"))
    
    # ==========================================================================
    # TECHNICAL INDICATOR SETTINGS
    # ==========================================================================
    EMA_FAST = int(os.getenv("EMA_FAST", "50"))
    EMA_SLOW = int(os.getenv("EMA_SLOW", "200"))
    EMA_ENTRY = int(os.getenv("EMA_ENTRY", "21"))
    
    RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
    RSI_OVERBOUGHT = int(os.getenv("RSI_OVERBOUGHT", "70"))
    RSI_OVERSOLD = int(os.getenv("RSI_OVERSOLD", "30"))
    
    # Minimum bars required for calculations
    MIN_BARS_H4 = 250
    MIN_BARS_H1 = 250
    MIN_BARS_M15 = 100
    
    # ==========================================================================
    # LIQUIDITY ZONE DETECTION
    # ==========================================================================
    EQUAL_LEVEL_TOLERANCE = float(os.getenv("EQUAL_LEVEL_TOLERANCE", "0.0002"))
    MIN_TOUCHES = int(os.getenv("MIN_TOUCHES", "2"))
    FVG_MIN_SIZE = float(os.getenv("FVG_MIN_SIZE", "0.0005"))
    STOP_HUNT_SENSITIVITY = int(os.getenv("STOP_HUNT_SENSITIVITY", "5"))
    
    # ==========================================================================
    # REDIS CACHE CONFIGURATION
    # ==========================================================================
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    
    # Cache TTL (Time To Live) in seconds
    CACHE_TTL_FUNDAMENTAL = int(os.getenv("CACHE_TTL_FUNDAMENTAL", "14400"))
    CACHE_TTL_TECHNICAL = int(os.getenv("CACHE_TTL_TECHNICAL", "7200"))
    CACHE_TTL_LIQUIDITY = int(os.getenv("CACHE_TTL_LIQUIDITY", "900"))
    
    # ==========================================================================
    # LOGGING CONFIGURATION
    # ==========================================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = os.getenv("LOG_FILE", "logs/pacifique_trade.log")
    LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", "10"))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    LOG_COLOR_ENABLED = os.getenv("LOG_COLOR_ENABLED", "true").lower() == "true"
    
    # Ensure logs directory exists
    LOG_DIR = Path(LOG_FILE).parent
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # ==========================================================================
    # RISK MANAGEMENT
    # ==========================================================================
    THREE_PART_SL = os.getenv("THREE_PART_SL", "true").lower() == "true"
    
    SL_PART1 = int(os.getenv("SL_PART1", "33"))
    SL_PART2 = int(os.getenv("SL_PART2", "33"))
    SL_PART3 = int(os.getenv("SL_PART3", "34"))
    
    @classmethod
    def validate_sl_parts(cls):
        """Validate SL parts sum to 100"""
        total = cls.SL_PART1 + cls.SL_PART2 + cls.SL_PART3
        if total != 100:
            from .exceptions import ConfigurationError
            raise ConfigurationError(
                "SL_PARTS",
                f"SL parts must sum to 100%, got {total}%"
            )
    
    MAX_DRAWDOWN_PERCENT = float(os.getenv("MAX_DRAWDOWN_PERCENT", "5"))
    MAX_CONCURRENT_TRADES = int(os.getenv("MAX_CONCURRENT_TRADES", "3"))
    
    # ==========================================================================
    # ADVANCED SETTINGS
    # ==========================================================================
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
    PROFILING_ENABLED = os.getenv("PROFILING_ENABLED", "false").lower() == "true"
    
    # ==========================================================================
    # VALIDATION
    # ==========================================================================
    @classmethod
    def validate_all(cls):
        """Validate all configuration"""
        cls.validate_telegram_config()
        cls.validate_sl_parts()
        
        # Validate risk percentage
        if not 0.1 <= cls.RISK_PERCENTAGE <= 5.0:
            from .exceptions import ConfigurationError
            raise ConfigurationError(
                "RISK_PERCENTAGE",
                f"Must be between 0.1 and 5.0, got {cls.RISK_PERCENTAGE}"
            )
        
        # Validate account balance
        if cls.ACCOUNT_BALANCE <= 0:
            from .exceptions import ConfigurationError
            raise ConfigurationError(
                "ACCOUNT_BALANCE",
                f"Must be positive, got {cls.ACCOUNT_BALANCE}"
            )
        
        # Validate EMA periods
        if cls.EMA_FAST >= cls.EMA_SLOW:
            from .exceptions import ConfigurationError
            raise ConfigurationError(
                "EMA_PERIODS",
                f"EMA_FAST ({cls.EMA_FAST}) must be less than EMA_SLOW ({cls.EMA_SLOW})"
            )
        
        print(f"✅ Configuration validated successfully")
        print(f"   Trading Pairs: {cls.TRADING_PAIRS_STR}")
        print(f"   Risk: {cls.RISK_PERCENTAGE}% per trade")
        print(f"   Account: ${cls.ACCOUNT_BALANCE:,.2f}")
        print(f"   Telegram: {'Enabled' if cls.TELEGRAM_ENABLED else 'Disabled'}")
        print(f"   Redis Cache: {'Enabled' if cls.REDIS_ENABLED else 'Disabled'}")
        print(f"   Dry Run: {'Yes' if cls.DRY_RUN else 'No (LIVE TRADING)'}")


# Singleton instance
config = Config()