# PacifiqueTrade Indicator 2.0

> **Trading Indicator System for Forex Markets**  
> Combining fundamental analysis, multi-timeframe technical analysis, and liquidity zone detection with automated Telegram notifications.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [System Architecture](#system-architecture)
4. [Prerequisites](#prerequisites)
5. [Installation Guide](#installation-guide)
6. [Configuration](#configuration)
7. [Usage](#usage)
8. [Development Roadmap](#development-roadmap)
9. [Project Structure](#project-structure)
10. [Contributing](#contributing)

---

## 🎯 Overview

**PacifiqueTrade Indicator 2.0** is an advanced trading indicator system designed for serious Forex traders who trade **USD/GBP**, **USD/EUR**, and **USD/JPY** pairs. 

The system implements a comprehensive **2026-27 Trading Strategy** that combines:
- 📰 **Fundamental Analysis** - Economic calendar screening (high-impact news)
- 📊 **Multi-Timeframe Technical Analysis** - H1/H4 trend detection with EMA50/200
- 💧 **Liquidity Zone Detection** - Equal Highs/Lows, Stop-Hunt zones, Fair Value Gaps
- ⏰ **Pre-Market Timing** - Alerts at T-4h, T-2h, T-15min before London/NY open
- 📱 **Telegram Integration** - Multi-level notifications with interactive buttons
- 🛡️ **Risk Management** - Automated SL/TP calculation with 3-part position management

---

## ✨ Features

### Core Functionality
- ✅ **Forex Factory API Integration** - Real-time economic calendar data
- ✅ **Automated Fundamental Screening** - Filters high-impact news (3-bull/red flag events)
- ✅ **Trend Confirmation System** - H1/H4 EMA crossovers + Higher High/Lower Low detection
- ✅ **Advanced Liquidity Analysis** - Detects institutional liquidity zones
- ✅ **Multi-Stage Telegram Alerts** - 4 alert levels from pre-market to market open
- ✅ **Position Size Calculator** - 1% risk per trade with 3-part SL management
- ✅ **Scheduled Execution** - APScheduler for time-based triggers

### Planned Features (Phase 2)
- 🔄 **Backtesting Engine** - Historical strategy validation
- 📈 **Web Dashboard** - Real-time monitoring interface
- 📊 **TradingView Integration** - Pine Script overlay indicator
- 🗄️ **Signal Database** - PostgreSQL logging for performance tracking
- 📧 **Email Notifications** - Alternative to Telegram
- 🤖 **Machine Learning Models** - Enhanced signal prediction

---

## 🏗️ System Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed flowchart and component diagrams.

### High-Level Flow
```
T-4h: Fundamental Screening → Telegram Alert 1 (Pre-Market)
  ↓
T-2h: Technical Analysis (H1/H4) → Telegram Alert 2 (Trend Confirmation)
  ↓
T-15min: Liquidity Zones (M15/M30) → Telegram Alert 3 (READY TO TRADE)
  ↓
T-0: Market Open + Reaction Monitor → Telegram Alert 4 (CONFIRMED/CANCELLED)
```

---

## 🔧 Prerequisites

### Required Software
- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **VS Code** - Already installed ✅
- **Git** - [Download](https://git-scm.com/downloads)
- **Redis** (optional, for caching) - [Download](https://redis.io/download/)

### Required Accounts
- **Telegram Bot** - [Create via BotFather](https://t.me/botfather)
- **Forex Factory** - Free API access (no registration needed)
- **TradingView** (optional) - For Pine Script overlay

### System Requirements
- **OS**: Windows 10/11
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 500MB free space
- **Internet**: Stable connection for API calls

---

## 📦 Installation Guide

### Step 1: Clone the Repository
```bash
# Open VS Code Terminal (Ctrl + `)
cd C:\Users\YourUsername\Documents
git clone https://github.com/yourusername/PacifiqueTrade-indicator2.0.git
cd PacifiqueTrade-indicator2.0
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

### Step 3: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 4: Create Configuration File
```bash
# Copy the example environment file
copy .env.example .env

# Open .env in VS Code and fill in your credentials
code .env
```

### Step 5: Set Up Telegram Bot
1. **Open Telegram** and search for `@BotFather`
2. **Send** `/newbot` command
3. **Follow prompts** to create your bot
4. **Copy the API token** and paste into `.env` file
5. **Get your Chat ID**:
   ```bash
   # Run the helper script
   python scripts/get_telegram_chat_id.py
   
   # Send a message to your bot
   # The script will display your Chat ID
   ```

### Step 6: Test Installation
```bash
# Run the test suite
python -m pytest tests/ -v

# Expected output: All tests passing ✅
```

---

## ⚙️ Configuration

### Environment Variables (.env)
```ini
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Trading Configuration
TRADING_PAIRS=GBP/USD,EUR/USD,USD/JPY
RISK_PERCENTAGE=1.0
ACCOUNT_BALANCE=10000

# Market Open Times (UTC)
LONDON_OPEN=08:00
NEWYORK_OPEN=13:30

# API Configuration
FOREX_FACTORY_API=https://www.forexfactory.com/calendar.php

# Technical Indicators
EMA_FAST=50
EMA_SLOW=200
EMA_ENTRY=21

# Liquidity Detection
EQUAL_LEVEL_TOLERANCE=0.0002
MIN_TOUCHES=2

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/pacifique_trade.log
```

### Trading Pairs Configuration (core/config.py)
```python
# Customize your trading setup
PAIRS = {
    "GBP/USD": {
        "news_focus": ["UK_CPI", "BOE_RATES", "UK_PMI", "US_NFP", "US_CPI"],
        "min_spread": 0.0001,
        "max_spread": 0.0003
    },
    "EUR/USD": {
        "news_focus": ["ECB_RATES", "EU_CPI", "EU_GDP", "US_NFP"],
        "min_spread": 0.0001,
        "max_spread": 0.0002
    },
    "USD/JPY": {
        "news_focus": ["BOJ_RATES", "JP_TANKAN", "JP_CPI", "US_YIELDS"],
        "min_spread": 0.01,
        "max_spread": 0.03
    }
}
```

---

## 🚀 Usage

### Quick Start
```bash
# Make sure virtual environment is activated
.\venv\Scripts\activate

# Run the indicator (manual mode)
python main.py

# Run in scheduled mode (automatic)
python main.py --schedule
```

### Manual Analysis
```bash
# Analyze specific pair for today
python main.py --pair GBP/USD --date today

# Analyze all pairs for tomorrow
python main.py --date tomorrow

# Backtest on historical data
python main.py --backtest --start 2024-01-01 --end 2024-12-31
```

### Telegram Commands
Send these commands to your bot:
- `/status` - Check system status
- `/signals` - View active signals
- `/pairs` - List monitored pairs
- `/help` - Show available commands
- `/settings` - Adjust notifications

---

## 📅 Development Roadmap

### ✅ Phase 1: Core Infrastructure (Weeks 1-2)
**Current Status: IN PROGRESS**

- [x] Project structure setup
- [x] README and documentation
- [ ] Core configuration system
- [ ] Forex Factory API integration
- [ ] Market data fetching (yfinance)
- [ ] Basic Telegram bot
- [ ] Logging system

### 🔄 Phase 2: Analysis Modules (Weeks 3-4)
- [ ] Fundamental analyzer (economic calendar parsing)
- [ ] Trend detector (EMA50/200, HH/HL)
- [ ] Liquidity zone detector (Equal H/L, Stop-Hunt, FVG)
- [ ] Signal generator (combine all factors)
- [ ] Risk manager (SL/TP calculator)

### 🔄 Phase 3: Automation & Alerts (Week 5)
- [ ] APScheduler integration
- [ ] Multi-stage Telegram alerts (4 levels)
- [ ] Market reaction monitor
- [ ] Position tracking
- [ ] Error handling & recovery

### 🔄 Phase 4: Testing & Optimization (Week 6)
- [ ] Unit tests for all modules
- [ ] Integration tests
- [ ] Backtesting engine
- [ ] Performance optimization
- [ ] Documentation refinement

### 🔮 Phase 5: Advanced Features (Future)
- [ ] Web dashboard (Flask/FastAPI)
- [ ] TradingView Pine Script overlay
- [ ] PostgreSQL signal database
- [ ] Machine learning price prediction
- [ ] Multi-account support

---

## 📁 Project Structure

```
PacifiqueTrade-indicator2.0/
│
├── 📂 core/                          # Core configuration
│   ├── __init__.py
│   ├── config.py                    # Main configuration
│   ├── enums.py                     # Enums (TrendDirection, SignalStrength)
│   └── exceptions.py                # Custom exceptions
│
├── 📂 data/                          # Data fetching & storage
│   ├── __init__.py
│   ├── forex_factory_api.py         # Economic calendar API
│   ├── market_data.py               # OHLCV data fetching
│   └── cache.py                     # Redis caching layer
│
├── 📂 analysis/                      # Analysis modules
│   ├── __init__.py
│   ├── fundamental.py               # Fundamental screener
│   ├── trend_detector.py            # Multi-timeframe trend
│   ├── liquidity_zones.py           # Liquidity analysis
│   └── signal_generator.py          # Final signal logic
│
├── 📂 risk/                          # Risk management
│   ├── __init__.py
│   ├── position_sizer.py            # 1% risk calculator
│   ├── sl_tp_calculator.py          # 3-part SL/TP
│   └── trailing_stop.py             # Dynamic trailing
│
├── 📂 notification/                  # Alert systems
│   ├── __init__.py
│   ├── telegram_bot.py              # Telegram integration
│   └── message_templates.py         # Message formatting
│
├── 📂 scheduler/                     # Job scheduling
│   ├── __init__.py
│   └── job_scheduler.py             # APScheduler setup
│
├── 📂 visualization/                 # Charts & overlays
│   ├── __init__.py
│   ├── plotly_charts.py             # Interactive charts
│   └── tradingview_overlay.py       # Pine Script generator
│
├── 📂 tests/                         # Test suite
│   ├── test_fundamental.py
│   ├── test_trend.py
│   ├── test_liquidity.py
│   └── test_signals.py
│
├── 📂 scripts/                       # Utility scripts
│   ├── get_telegram_chat_id.py
│   ├── test_api_connection.py
│   └── backtest_runner.py
│
├── 📂 logs/                          # Log files
│   └── .gitkeep
│
├── 📂 docs/                          # Additional documentation
│   ├── ARCHITECTURE.md              # System flowchart
│   ├── API_REFERENCE.md
│   ├── STRATEGY_GUIDE.md
│   └── TROUBLESHOOTING.md
│
├── .env.example                      # Environment template
├── .gitignore                        # Git ignore rules
├── requirements.txt                  # Python dependencies
├── main.py                          # Main entry point
└── README.md                        # This file
```

---

## 🤝 Contributing

This is a personal trading project, but suggestions are welcome:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Forex Factory** - Economic calendar data
- **TradingView** - Charting inspiration
- **Code Institute** - Training foundation
- **Claude.ai** - Development assistance

---

## 📞 Support

For issues or questions:
- 🐛 Issues: [GitHub Issues](https://github.com/SteveDok22/PacifiqueTrade-indicator2.0/issues)
- 📖 Documentation: Check `/docs` folder for detailed guides

---

## ⚠️ Disclaimer

**This software is for testing & educational purposes only. Trading Forex carries a high level of risk and may not be suitable for all investors. Past performance is not indicative of future results. Always trade responsibly and never risk more than you can afford to lose.**

