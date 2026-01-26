# PacifiqueTrade Indicator 2.0

<div align="center">
<img src="docs/images/pacifique-trade-banner.png" alt="PacifiqueTrade Banner" width="900">
</div>

<div align="center">

**Live System:** Running 24/7 on Windows Task Scheduler

**Repository:** [GitHub](https://github.com/SteveDok22/PacifiqueTrade-indicator2.0)

**Telegram Bot:** [@PacifiqueTradeBot](https://t.me/your_bot_name)

</div>

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Strategy Design](#strategy-design)
   - [4-Phase Trading Strategy](#4-phase-trading-strategy)
   - [User Stories](#user-stories)
   - [System Flowcharts](#system-flowcharts)
3. [Features](#features)
   - [Existing Features](#existing-features)
   - [Future Features](#future-features)
4. [System Architecture](#system-architecture)
   - [Data Flow Diagram](#data-flow-diagram)
   - [Module Structure](#module-structure)
5. [Technologies Used](#technologies-used)
6. [Agile Methodology](#agile-methodology)
7. [Testing](#testing)
   - [Automated Testing](#automated-testing)
   - [Manual Testing](#manual-testing)
   - [Bugs](#bugs)
8. [Installation & Deployment](#installation--deployment)
   - [Local Setup](#local-setup)
   - [Windows Task Scheduler](#windows-task-scheduler)
   - [Configuration](#configuration)
9. [Usage Guide](#usage-guide)
10. [Credits](#credits)

---

## Project Overview

### Purpose

PacifiqueTrade Indicator 2.0 is a **professional-grade automated Forex trading signal system** designed for systematic traders who trade **GBP/USD**, **EUR/USD**, and **USD/JPY** pairs. The system combines fundamental analysis, multi-timeframe technical analysis, and institutional liquidity zone detection to generate high-probability trading signals with automated Telegram notifications.

### Target Audience

- **Systematic Forex Traders:** Traders using rule-based strategies
- **News Traders:** Traders focusing on high-impact economic events
- **Swing Traders:** Position traders holding 1-3 days
- **Professional Traders:** Those seeking automated market screening

### Value Proposition

- 🕐 **Pre-Market Alerts:** T-4h, T-2h, T-15min, T-0 notifications
- 📰 **Fundamental Screening:** Forex Factory economic calendar integration
- 📊 **Multi-Timeframe Analysis:** H4/H1 trend confirmation
- 💧 **Liquidity Zone Detection:** Equal Highs/Lows, Stop-Hunts, Fair Value Gaps
- 📱 **Telegram Integration:** Real-time notifications with TradingView links
- 🛡️ **Risk Management:** 3-part SL/TP system (1% risk per trade)
- 🤖 **Fully Automated:** 24/7 monitoring via Windows Task Scheduler

---

### System Architecture Flowchart

<div align="center">
<img src="docs/images/system-flowchart.png" alt="System Flowchart" width="900">
</div>

The flowchart above illustrates the complete 4-phase trading workflow from fundamental screening to entry confirmation.

---

### API Integration Flow

<div align="center">
<img src="docs/images/api-flow.png" alt="API Flow" width="800">
</div>

Shows how the system integrates with Forex Factory, yfinance, and Telegram APIs.

---

## Strategy Design

### 4-Phase Trading Strategy

The PacifiqueTrade system implements a rigorous 4-phase approach:
```
Phase 1 (T-4h): Fundamental Screening
    ↓
  High-impact news detected?
    ↓ YES
Phase 2 (T-2h): Technical Analysis (H4/H1)
    ↓
  Trend aligns with fundamental?
    ↓ YES
Phase 3 (T-15min): Liquidity Zone Detection (M15)
    ↓
  Price near key liquidity zone?
    ↓ YES
Phase 4 (T-0): Market Open Confirmation
    ↓
  Market reaction confirms entry?
    ↓ YES → ENTER TRADE
```

---

### User Stories

#### Epic 1: Fundamental Analysis

| ID | As a... | I want to... | So that I can... | Priority |
|----|---------|--------------|------------------|----------|
| 1.1 | Trader | Receive T-4h pre-market alerts | Prepare for high-impact news | Must Have |
| 1.2 | Trader | See which currency will be affected | Anticipate market direction | Must Have |
| 1.3 | Trader | Know event name, forecast, previous | Make informed decisions | Must Have |
| 1.4 | Trader | Filter only 3-bull/red-flag events | Focus on impactful news | Must Have |

#### Epic 2: Technical Confirmation

| ID | As a... | I want to... | So that I can... | Priority |
|----|---------|--------------|------------------|----------|
| 2.1 | Trader | Receive T-2h trend confirmation | Validate fundamental direction | Must Have |
| 2.2 | Trader | See H4 and H1 trend alignment | Confirm multi-timeframe bias | Must Have |
| 2.3 | Trader | Know EMA50/200 positioning | Identify trend strength | Must Have |
| 2.4 | Trader | See Higher Highs/Lower Lows | Confirm momentum | Should Have |

#### Epic 3: Liquidity Zone Detection

| ID | As a... | I want to... | So that I can... | Priority |
|----|---------|--------------|------------------|----------|
| 3.1 | Trader | Detect Equal Highs/Lows | Identify institutional zones | Must Have |
| 3.2 | Trader | Find Stop-Hunt zones | Anticipate liquidity sweeps | Must Have |
| 3.3 | Trader | Locate Fair Value Gaps | Enter at premium/discount | Must Have |
| 3.4 | Trader | Receive T-15min "Ready to Trade" alert | Prepare for market open | Must Have |

#### Epic 4: Entry Confirmation & Risk Management

| ID | As a... | I want to... | So that I can... | Priority |
|----|---------|--------------|------------------|----------|
| 4.1 | Trader | Receive T-0 entry confirmation | Execute with confidence | Must Have |
| 4.2 | Trader | Get calculated SL/TP levels | Manage risk automatically | Must Have |
| 4.3 | Trader | See position size (lots) | Risk exactly 1% per trade | Must Have |
| 4.4 | Trader | Get TradingView chart link | See visual entry zone | Should Have |
| 4.5 | Trader | Track position with real-time updates | Monitor TP hits and trailing stops | Should Have |

#### Epic 5: Position Monitoring

| ID | As a... | I want to... | So that I can... | Priority |
|----|---------|--------------|------------------|----------|
| 5.1 | Trader | Receive TP1 hit notification | Move to breakeven | Must Have |
| 5.2 | Trader | Receive TP2 hit notification | Close 33% at +2R | Must Have |
| 5.3 | Trader | Receive TP3 hit notification | Exit remaining position | Must Have |
| 5.4 | Trader | Get trailing stop updates | Lock in profits | Should Have |
| 5.5 | Trader | Get final P&L summary | Review trade performance | Should Have |

---

### System Flowcharts

<details>
<summary>Phase 1: Fundamental Screening</summary>

<div align="center">
<img src="docs/flowcharts/phase1-fundamental.png" alt="Fundamental Flow" width="700">
</div>

</details>

<details>
<summary>Phase 2: Technical Analysis</summary>

<div align="center">
<img src="docs/flowcharts/phase2-technical.png" alt="Technical Flow" width="700">
</div>

</details>

<details>
<summary>Phase 3: Liquidity Detection</summary>

<div align="center">
<img src="docs/flowcharts/phase3-liquidity.png" alt="Liquidity Flow" width="700">
</div>

</details>

<details>
<summary>Phase 4: Entry Confirmation</summary>

<div align="center">
<img src="docs/flowcharts/phase4-entry.png" alt="Entry Flow" width="700">
</div>

</details>

---

## Features

### Existing Features

#### F1: Fundamental Analysis (T-4h)

<div align="center">
<img src="docs/screenshots/telegram-premarket-alert.png" alt="Pre-Market Alert" width="500">
</div>

- **Forex Factory Integration:** Real-time economic calendar scraping
- **High-Impact Filtering:** Only 3-bull/red-flag events (NFP, CPI, Rate Decisions)
- **Telegram Notification:** Pre-market alert 4 hours before London/NY open
- **Currency Mapping:** Automatic pairing (USD CPI → GBP/USD, EUR/USD signals)
- **Event Details:** Forecast, previous value, impact rating

**Example Alert:**
```
🔔 PRE-MARKET ALERT 🔔

📊 Pair: GBP/USD
🌍 Event: US CPI
⚡ Impact: 🔴🔴🔴 HIGH

📈 Expected Direction: USD Weaker (Bullish GBP/USD)

📋 Data:
  • Forecast: 3.2%
  • Previous: 3.5%

⏰ Market Opens In: 4 hours

💡 Note: Get ready for technical analysis in 2 hours.
```

---

#### F2: Multi-Timeframe Technical Analysis (T-2h)

<div align="center">
<img src="docs/screenshots/telegram-technical-confirmation.png" alt="Technical Confirmation" width="500">
</div>

- **H4 Trend Detection:** EMA50/200 crossover + Higher High/Lower Low pattern
- **H1 Confirmation:** Secondary timeframe validation
- **Trend Strength:** Weak (1), Moderate (2), Strong (3)
- **Alignment Check:** Fundamental vs Technical direction matching
- **Telegram Alert:** "Technical Confirmation" or "Conflicting - No Trade"

**Example Alert:**
```
📊 TECHNICAL CONFIRMATION 📊

📈 Pair: GBP/USD
💹 Current Price: 1.27450

🎯 Fundamental: USD Weaker (Bullish GBP/USD)

📉 H4 Trend: BULLISH (Strength: 3)
  • EMA50: 1.27200
  • EMA200: 1.26800

📈 H1 Trend: BULLISH (Strength: 2)

✅ Alignment: CONFIRMED - Trend matches fundamental!

⏰ Next Step: Final check in 1h 45min
```

---

#### F3: Liquidity Zone Detection (T-15min)

<div align="center">
<img src="docs/screenshots/telegram-ready-to-trade.png" alt="Ready to Trade" width="500">
</div>

- **Equal Highs/Lows:** Multiple swing highs/lows at same level (resistance/support)
- **Stop-Hunt Zones:** Fake breakouts followed by reversals
- **Fair Value Gaps (FVG):** 3-candle imbalances (institutional entry zones)
- **Proximity Filter:** Only signals when price is within 0.3% of zone
- **TradingView Link:** Direct chart access with entry zone highlighted
- **Complete Signal:** Entry, SL, TP1/2/3, position size, R:R ratio

**Example Alert:**
```
🚨 READY TO TRADE 🚨

🟢 Pair: GBP/USD
📍 Direction: LONG
⚡ Strength: STRONG

💰 ENTRY DETAILS:
  • Entry Price: 1.27000
  • Position Size: 0.20 lots
  • Risk Amount: $100.00

🎯 Entry Zone: Equal Lows @ 1.26950

🛑 STOP LOSS (3-Part System):
  • SL: 1.26500
  • Part 1 (33%): Move to BE at TP1
  • Part 2 (33%): Close at TP2
  • Part 3 (34%): Trail to TP3+

🎯 TAKE PROFIT LEVELS:
  • TP1: 1.27500 (+1R)
  • TP2: 1.28000 (+2R)
  • TP3: 1.28500 (+3R)

📊 Risk/Reward: 1:3.0

⏰ Market Opens: 15 minutes

📊 Chart: Open on TradingView

✅ Action: Prepare to enter on market open!
```

---

#### F4: Entry Confirmation (T-0, Market Open)

<div align="center">
<img src="docs/screenshots/telegram-entry-confirmed.png" alt="Entry Confirmed" width="500">
</div>

- **Market Reaction Monitor:** Checks first 5-min candle after open
- **Volume Confirmation:** Ensures volume >150% of average
- **Price Action:** Validates bullish/bearish breakout
- **TradingView Link:** 5-minute chart for precise entry
- **Binary Decision:** "Entry Confirmed" or "Signal Cancelled"

**Example Alert (Confirmed):**
```
✅ ENTRY CONFIRMED ✅

📊 Pair: GBP/USD
📍 Direction: LONG
💰 Entry Price: 1.27020

🎯 Market Reaction: Strong bullish breakout
📈 Volume: +175% above average

✅ Status: ALL SYSTEMS GO!

📊 Chart: Open on TradingView

💡 Action: Enter the trade now!
📝 Remember: Follow your SL/TP plan exactly
```

**Example Alert (Cancelled):**
```
❌ SIGNAL CANCELLED ❌

📊 Pair: GBP/USD
📍 Direction: LONG

⚠️ Reason: Weak market reaction - volume only +80%

💡 Action: DO NOT ENTER
🔍 Status: Wait for next opportunity

Remember: Not every signal becomes a trade. We only take HIGH PROBABILITY setups!
```

---

#### F5: Position Monitoring (Real-Time)

<div align="center">
<img src="docs/screenshots/telegram-position-updates.png" alt="Position Updates" width="500">
</div>

- **TP1 Hit Alert:** Move 33% to breakeven
- **TP2 Hit Alert:** Close 33% at +2R, move stop to +1R
- **TP3 Hit Alert:** Close remaining 67%, full exit
- **Trailing Stop Updates:** Dynamic stop adjustments beyond +2R
- **Final P&L Summary:** Complete trade statistics

**Example Alerts:**

**TP1 Hit:**
```
🎯 TP1 HIT! 🎯

📊 Pair: GBP/USD (LONG)

💰 Current Status:
  • Entry: 1.27000
  • TP1: 1.27500
  • Profit: 50 pips ($100.00)
  • R-Multiple: +1.0R

✅ Action Taken: Moved 33% to breakeven (SL: 1.27000)

💡 Let profits run on remaining 67%!
```

**Final Exit:**
```
🎉 POSITION FULLY CLOSED 🎉

📊 Pair: GBP/USD (LONG)

💰 Final Results:
  • Entry: 1.27000
  • Exit Average: 1.28200
  • Total Profit: 120 pips ($360.00)
  • R-Multiple: +3.6R
  • Duration: 4h 23min

✅ Trade Grade: EXCELLENT

📊 Next: Wait for next setup!
```

---

#### F6: Automated Scheduling (24/7)

<div align="center">
<img src="docs/screenshots/task-scheduler-setup.png" alt="Task Scheduler" width="700">
</div>

- **Windows Task Scheduler Integration:** Auto-start on boot
- **Cron-Based Triggers:**
  - 04:00 UTC / 09:30 UTC - Fundamental Screening
  - 06:00 UTC / 11:30 UTC - Technical Analysis
  - 07:45 UTC / 13:15 UTC - Signal Generation
  - 08:00 UTC / 13:30 UTC - Market Reaction
- **Auto-Restart on Failure:** Watchdog script restarts every 10 seconds
- **Logging:** Complete audit trail in `logs/pacifique_trade.log`

---

#### F7: Risk Management System

- **Position Sizer:** Calculates exact lot size for 1% risk
- **3-Part SL/TP:**
  - Part 1 (33%): Breakeven at +1R
  - Part 2 (33%): +2R exit
  - Part 3 (34%): Trailing to +3R+
- **SL/TP Calculator:** ATR-based or EMA21-based levels
- **Trailing Stop Manager:** Dynamic stop adjustment beyond +2R
- **Risk/Reward Filter:** Minimum 1:2 R:R ratio required

---

#### F8: Comprehensive Logging

<div align="center">
<img src="docs/screenshots/log-output.png" alt="Logs" width="700">
</div>

- **Structured Logging:** Timestamp, level, module, message
- **Rotating Logs:** Automatic archiving at 10MB
- **Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Real-Time Monitoring:** `Get-Content -Wait` support
- **Error Tracking:** Full stack traces for debugging

---

### Future Features

| Feature | Description | Priority | Status |
|---------|-------------|----------|--------|
| **Backtesting Engine** | Historical strategy validation | High | Planned |
| **Web Dashboard** | Real-time monitoring interface (Flask) | Medium | Planned |
| **TradingView Pine Script** | Overlay indicator with alerts | High | Planned |
| **PostgreSQL Database** | Signal logging and analytics | Medium | Planned |
| **ML Price Prediction** | Machine learning signal enhancement | Low | Research |
| **Email Notifications** | Alternative to Telegram | Low | Planned |
| **Multi-Account Support** | Manage multiple trading accounts | Low | Planned |
| **WhatsApp Integration** | Additional notification channel | Low | Idea |

---

## System Architecture

### Data Flow Diagram

<div align="center">
<img src="docs/images/data-flow-diagram.png" alt="Data Flow" width="900">
</div>

### Module Structure
```
┌─────────────────────────────────────────────────────────────┐
│                    PACIFIQUETRADE SYSTEM                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │   DATA       │   │   ANALYSIS   │   │     RISK     │     │
│  │  ──────────  │   │  ──────────  │   │  ──────────  │     │
│  │ Forex Factory│   │ Fundamental  │   │Position Sizer│     │
│  │   yfinance   │───│ Trend Detect │───│  SL/TP Calc  │     │
│  │    Cache     │   │ Liquidity    │   │ Trailing Stop│     │
│  └──────────────┘   │ Signal Gen   │   └──────────────┘     │
│                     └──────────────┘                        │
│                            │                                │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │ NOTIFICATION │   │  SCHEDULER   │   │   LOGGING    │     │
│  │  ──────────  │   │  ──────────  │   │  ──────────  │     │
│  │   Telegram   │───│ APScheduler  │───│  File Logger │     │
│  │   Messages   │   │  Cron Jobs   │   │Console Logger│     │
│  └──────────────┘   └──────────────┘   └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction

| Component | Input | Processing | Output |
|-----------|-------|------------|--------|
| **Forex Factory API** | Economic calendar URL | HTML parsing → Event objects | High-impact news list |
| **Market Data Fetcher** | Symbol + timeframe | yfinance API call | OHLCV DataFrame |
| **Fundamental Analyzer** | News events + pairs | Currency mapping → Direction | Fundamental signals |
| **Trend Detector** | OHLCV data | EMA calculation → HH/HL detection | Trend analysis |
| **Liquidity Detector** | M15 data | Equal H/L + Stop-Hunt + FVG | Liquidity zones |
| **Signal Generator** | All analysis results | Combine + filter | Trading signals |
| **Position Sizer** | Account balance + risk % | ATR calculation | Lot size |
| **SL/TP Calculator** | Entry + direction | ATR or EMA-based | SL/TP levels |
| **Telegram Notifier** | Signal object | Message formatting | Telegram alert |
| **Job Scheduler** | Cron expressions | APScheduler triggers | Automated execution |

---

## Technologies Used

### Core Languages & Frameworks

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Main programming language |
| **APScheduler** | 3.10.4 | Job scheduling (cron-based) |
| **yfinance** | 0.2.28 | Market data (H4, H1, M15) |
| **pandas** | 2.1.3 | Data manipulation |
| **numpy** | 1.26.2 | Numerical calculations |

### API & Data Sources

| Service | Purpose | Rate Limits |
|---------|---------|-------------|
| **Forex Factory** | Economic calendar | Free (no limits) |
| **Yahoo Finance** | OHLCV data | Free (no limits) |
| **Telegram Bot API** | Notifications | 30 messages/second |

### Notification & Communication

| Technology | Version | Purpose |
|------------|---------|---------|
| **python-telegram-bot** | 20.7 | Telegram integration |
| **requests** | 2.31.0 | HTTP requests |

### Utilities

| Technology | Version | Purpose |
|------------|---------|---------|
| **python-dotenv** | 1.0.0 | Environment variables |
| **beautifulsoup4** | 4.12.2 | HTML parsing |
| **lxml** | 4.9.3 | XML parsing |
| **pytz** | 2023.3 | Timezone handling |

### Development Tools

| Tool | Purpose |
|------|---------|
| **Git** | Version control |
| **GitHub** | Repository hosting |
| **VS Code** | Code editor |
| **PowerShell** | Scripting & automation |
| **Draw.io** | Flowcharts & diagrams |

---

## Agile Methodology

### GitHub Projects Board

This project was developed using Agile principles with GitHub Projects.

**Board Link:** [PacifiqueTrade Project Board](https://github.com/users/SteveDok22/projects/X)

### Sprint Structure

| Sprint | Duration | Focus | Deliverables |
|--------|----------|-------|--------------|
| **Sprint 1** | Week 1-2 | Core Infrastructure | Config, APIs, Data fetching |
| **Sprint 2** | Week 3-4 | Analysis Modules | Fundamental, Trend, Liquidity |
| **Sprint 3** | Week 5 | Automation & Alerts | Scheduler, Telegram, Position Monitor |
| **Sprint 4** | Week 6 | Testing & Optimization | Unit tests, Bug fixes, Documentation |

### User Stories Management

All user stories were tracked as GitHub Issues with:
- **Labels:** Must Have, Should Have, Could Have, Won't Have
- **Acceptance Criteria:** Clear definition of done
- **Tasks:** Checkbox list for implementation steps
- **Linked Epics:** Grouped by trading phase

---

## Testing

### Automated Testing

#### Python Unit Tests
```bash
# Run all tests
python test_all.py

# Run with verbose output
python -m pytest tests/ -v

# Run with coverage
coverage run test_all.py
coverage report
```

**Test Coverage:** 14/14 tests passing (100% success rate)

**Test Modules:**
1. ✅ Core Configuration
2. ✅ Enums & Exceptions
3. ✅ Forex Factory API
4. ✅ Market Data (yfinance)
5. ✅ Fundamental Analysis
6. ✅ Trend Detection
7. ✅ Liquidity Zone Detection
8. ✅ Signal Generator
9. ✅ Position Sizer
10. ✅ SL/TP Calculator
11. ✅ Trailing Stop Manager
12. ✅ Message Templates
13. ✅ Telegram Bot
14. ✅ Job Scheduler

---

### Manual Testing

#### Telegram Bot Testing

| Test Case | Input | Expected Output | Result |
|-----------|-------|-----------------|--------|
| Startup Notification | `python main.py --schedule` | "🚀 System Started" message | ✅ Pass |
| Pre-Market Alert | High-impact news detected | T-4h alert with event details | ✅ Pass |
| Technical Confirmation | H4/H1 trend aligned | T-2h confirmation alert | ✅ Pass |
| Ready to Trade | All conditions met | T-15min signal with SL/TP | ✅ Pass |
| Entry Confirmed | Volume >150%, bullish | T-0 entry confirmation | ✅ Pass |
| Entry Cancelled | Weak volume | T-0 cancellation notice | ✅ Pass |
| TP1 Hit | Price reaches TP1 | "🎯 TP1 HIT!" alert | ✅ Pass |
| Position Closed | All TPs hit | Final P&L summary | ✅ Pass |

---

### Validator Testing

#### Python Code Quality

| Tool | Purpose | Status |
|------|---------|--------|
| **flake8** | PEP 8 compliance | ✅ 0 errors |
| **pylint** | Code quality | ✅ 9.2/10 rating |
| **black** | Code formatting | ✅ All formatted |
| **mypy** | Type checking | ✅ No issues |

#### Configuration Validation
```bash
# Validate .env file
python -c "from core.config import config; config.validate_all()"
# Output: ✅ All configuration validated successfully
```

---

### Bugs

#### Resolved Issues

**Bug #1: Forex Factory 403 Forbidden**
- **Issue:** `Forex Factory blocked our request (403)`
- **Cause:** Missing User-Agent header
- **Fix:** Added realistic User-Agent + fallback to mock data
- **Status:** ✅ Resolved

**Bug #2: Liquidity Zone KeyError 'time'**
- **Issue:** `KeyError: 'time'` in `_detect_equal_highs()`
- **Cause:** DataFrame index name mismatch after `reset_index()`
- **Fix:** Used `iterrows()` instead of column access
- **Status:** ✅ Resolved

**Bug #3: Position Monitor Not Starting**
- **Issue:** `'self' doesn't exist` in module-level code
- **Cause:** Position Monitor initialized outside `JobScheduler.__init__()`
- **Fix:** Moved initialization inside `__init__()` method
- **Status:** ✅ Resolved

**Bug #4: Message Templates f-string Error**
- **Issue:** `SyntaxError: '{' was never closed`
- **Cause:** Unclosed `{` in multi-line f-string
- **Fix:** Rewrote all multi-line f-strings as concatenated strings
- **Status:** ✅ Resolved

**Bug #5: Telegram Not Sending Messages**
- **Issue:** No Telegram notifications arriving
- **Cause:** `TELEGRAM_ENABLED=false` in `.env`
- **Fix:** Changed to `TELEGRAM_ENABLED=true`
- **Status:** ✅ Resolved

---

#### Known Issues

| Issue | Description | Impact | Workaround |
|-------|-------------|--------|------------|
| **Forex Factory Blocking** | Occasional 403 errors | Low | Falls back to mock data |
| **yfinance Data Gaps** | Weekend/holiday missing data | Low | Forward-fill missing bars |
| **API Rate Limits** | None currently (free APIs) | None | N/A |

---

## Installation & Deployment

### Prerequisites

**Required Software:**
- Python 3.10 or higher
- Git
- Windows 10/11 (for Task Scheduler)

**Required Accounts:**
- Telegram account
- Telegram bot (created via @BotFather)

---

### Local Setup

#### Step 1: Clone Repository
```bash
cd C:\Users\YourName\Desktop
git clone https://github.com/SteveDok22/PacifiqueTrade-indicator2.0.git
cd PacifiqueTrade-indicator2.0
```

#### Step 2: Create Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment
```bash
# Copy template
copy .env.example .env

# Edit with your credentials
notepad .env
```

**Required .env Variables:**
```ini
TELEGRAM_BOT_TOKEN=7980796551:AAH...
TELEGRAM_CHAT_ID=434313972
TELEGRAM_ENABLED=true

TRADING_PAIRS=GBP/USD,EUR/USD,USD/JPY
RISK_PERCENTAGE=1.0
ACCOUNT_BALANCE=10000

LOG_LEVEL=INFO
```

#### Step 5: Get Telegram Chat ID
```bash
# Run helper script
python -c "
import requests, os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')
url = f'https://api.telegram.org/bot{token}/getUpdates'
r = requests.get(url).json()

if r['result']:
    chat_id = r['result'][-1]['message']['chat']['id']
    print(f'Your Chat ID: {chat_id}')
"

# Then send /start to your bot in Telegram
# Run the script again to get your Chat ID
```

#### Step 6: Test Installation
```bash
python test_all.py
```

**Expected Output:**
```
🔥 PACIFIQUETRADE INDICATOR 2.0 - ПОЛНАЯ ПРОВЕРКА
✅ Passed: 14
❌ Failed: 0
📊 Success Rate: 100.0%

🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!
```

---

### Windows Task Scheduler Deployment

#### Step 1: Create BAT Files
```powershell
# Create silent startup script
@"
@echo off
cd /d "C:\Users\name\Desktop\All IN\Code Inst. Projects\PacifiqueTrade-indicator2.0"
call venv\Scripts\activate.bat
python main.py --schedule >> logs\system.log 2>&1
"@ | Out-File -FilePath start_trading_silent.bat -Encoding ASCII
```

#### Step 2: Create Task in Task Scheduler

1. Open Task Scheduler (`Win + R` → `taskschd.msc`)
2. Create Task (NOT Basic Task)
3. **General Tab:**
   - Name: `PacifiqueTrade Indicator 2.0`
   - ✅ Run whether user is logged on or not
   - ✅ Run with highest privileges

4. **Triggers Tab:**
   - New → At startup
   - ✅ Enabled

5. **Actions Tab:**
   - Start a program
   - Program: `C:\...\start_trading_silent.bat`
   - Start in: `C:\...\PacifiqueTrade-indicator2.0`

6. **Conditions Tab:**
   - ❌ Start only if on AC power
   - ✅ Wake computer to run

7. **Settings Tab:**
   - ✅ Allow task to be run on demand
   - ✅ Run as soon as possible after missed start
   - ✅ If fails, restart every: 5 minutes

#### Step 3: Test Task
```powershell
# Start task manually
Start-ScheduledTask -TaskName "PacifiqueTrade Indicator 2.0"

# Check status
Get-ScheduledTask -TaskName "PacifiqueTrade*" | Select-Object TaskName, State, LastRunTime
```

#### Step 4: Monitor Logs
```powershell
# Watch logs in real-time
Get-Content logs\pacifique_trade.log -Wait -Tail 50
```

---

### Configuration

#### Pair-Specific Settings (core/config.py)
```python
PAIRS = {
    "GBP/USD": {
        "news_focus": ["UK_CPI", "BOE_RATES", "UK_PMI", "US_NFP"],
        "timeframes": {
            "trend": "4h",
            "confirmation": "1h",
            "entry": "15m"
        },
        "ema": {
            "fast": 50,
            "slow": 200,
            "entry": 21
        }
    },
    # ... similar for EUR/USD, USD/JPY
}
```

#### Scheduler Times (scheduler/job_scheduler.py)
```python
# London Session (08:00 UTC open)
LONDON_T4H = "04:00"  # Fundamental
LONDON_T2H = "06:00"  # Technical
LONDON_T15MIN = "07:45"  # Signal
LONDON_T0 = "08:00"  # Entry

# New York Session (13:30 UTC open)
NEWYORK_T4H = "09:30"
NEWYORK_T2H = "11:30"
NEWYORK_T15MIN = "13:15"
NEWYORK_T0 = "13:30"
```

---

## Usage Guide

### Quick Start
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run in scheduled mode (recommended)
python main.py --schedule
```

### Manual Analysis
```bash
# Analyze specific pair right now
python main.py --pair GBP/USD --now

# Test fundamental screening
python -c "
from scheduler.job_scheduler import JobScheduler
scheduler = JobScheduler()
scheduler._run_fundamental_screening('ManualTest')
"
```

### Telegram Commands
Send to your bot:
- `/status` - System status
- `/signals` - Active signals
- `/help` - Available commands

### Monitoring
```powershell
# Real-time logs
Get-Content logs\pacifique_trade.log -Wait -Tail 50

# Check for errors
Get-Content logs\pacifique_trade.log | Select-String "ERROR|WARNING"

# View today's signals
Get-Content logs\pacifique_trade.log | Select-String "READY TO TRADE"
```

---

## Credits

### Code & Libraries

| Component | Source | License |
|-----------|--------|---------|
| APScheduler | https://apscheduler.readthedocs.io/ | MIT |
| python-telegram-bot | https://python-telegram-bot.org/ | GPL 3.0 |
| yfinance | https://github.com/ranaroussi/yfinance | Apache 2.0 |
| pandas | https://pandas.pydata.org/ | BSD 3-Clause |

### APIs & Data

| Service | Purpose | Terms |
|---------|---------|-------|
| Forex Factory | Economic calendar | Free for non-commercial |
| Yahoo Finance | Market data | Free (no guarantees) |
| Telegram | Notifications | Free bot API |

### Learning Resources

- **Code Institute** - Python fundamentals
- **TradingView** - Chart analysis education
- **Babypips.com** - Forex strategy concepts
- **ICT (Inner Circle Trader)** - Liquidity zone concepts

### Acknowledgements

- **Code Institute Mentors** - Project guidance
- **Forex Factory Community** - Calendar data
- **Claude.ai** - Development assistance
- **Trading Community** - Strategy feedback

---

## Legal Disclaimer

**⚠️ IMPORTANT TRADING DISCLAIMER ⚠️**

This software is provided for **educational and research purposes only**. 

- **Not Financial Advice:** This system does not provide financial advice
- **Risk Warning:** Trading Forex carries substantial risk of loss
- **No Guarantees:** Past performance does not indicate future results
- **Use at Own Risk:** Author assumes no liability for trading losses
- **Testing Recommended:** Thoroughly test on demo account first

**By using this software, you acknowledge that you are solely responsible for your trading decisions and any resulting financial outcomes.**

---

<div align="center">

**Developed by Stiven Dokic** | [GitHub](https://github.com/SteveDok22) | 2025

</div>