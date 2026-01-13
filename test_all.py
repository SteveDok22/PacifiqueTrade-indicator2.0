"""
Complete System Test Script
Проверяет все модули системы
"""

import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("\n" + "="*70)
print("🔥 PACIFIQUETRADE INDICATOR 2.0 - ПОЛНАЯ ПРОВЕРКА")
print("="*70 + "\n")

results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

def test_module(name, test_func):
    """Test a module"""
    try:
        print(f"\n{'='*70}")
        print(f"Тест {results['passed'] + results['failed'] + 1}: {name}")
        print("-"*70)
        test_func()
        print(f"✅ {name} - PASSED")
        results["passed"] += 1
        return True
    except Exception as e:
        print(f"❌ {name} - FAILED: {e}")
        results["failed"] += 1
        results["errors"].append({"test": name, "error": str(e)})
        return False

# =============================================================================
# TEST 1: Core Configuration
# =============================================================================
def test_core_config():
    from core.config import config
    print(f"Trading Pairs: {config.TRADING_PAIRS_STR}")
    print(f"Account Balance: ${config.ACCOUNT_BALANCE:,.2f}")
    print(f"Risk: {config.RISK_PERCENTAGE}%")
    print(f"Telegram Enabled: {config.TELEGRAM_ENABLED}")
    assert config.ACCOUNT_BALANCE > 0, "Account balance must be positive"
    config.validate_all()

test_module("Core Configuration", test_core_config)

# =============================================================================
# TEST 2: Enums & Exceptions
# =============================================================================
def test_enums_exceptions():
    from core.enums import CurrencyPair, TrendDirection, SignalStrength
    from core.exceptions import PacifiqueTradeError
    gbp_usd = CurrencyPair.GBP_USD
    print(f"Currency Pair: {gbp_usd.value}")
    print(f"Base Currency: {gbp_usd.base_currency}")
    print(f"Quote Currency: {gbp_usd.quote_currency}")
    print(f"yfinance Ticker: {gbp_usd.yfinance_ticker}")

test_module("Enums & Exceptions", test_enums_exceptions)

# =============================================================================
# TEST 3: Forex Factory API
# =============================================================================
def test_forex_factory():
    from data import ForexFactoryAPI
    from core.enums import CurrencyPair
    
    api = ForexFactoryAPI()
    events = api.fetch_calendar()
    print(f"Fetched {len(events)} economic events")
    
    if events:
        print(f"Sample event: {events[0].event_name} ({events[0].currency})")
    
    high_impact = api.filter_high_impact(events)
    print(f"High-impact events: {len(high_impact)}")

test_module("Forex Factory API", test_forex_factory)

# =============================================================================
# TEST 4: Market Data (yfinance)
# =============================================================================
def test_market_data():
    from data import MarketDataFetcher
    from core.enums import CurrencyPair, TimeFrame
    
    fetcher = MarketDataFetcher()
    df = fetcher.fetch_data(CurrencyPair.GBP_USD, TimeFrame.H4)
    
    print(f"Fetched {len(df)} H4 bars")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print(f"Latest close: {df['close'].iloc[-1]:.5f}")
    
    current_price = fetcher.get_current_price(CurrencyPair.GBP_USD)
    print(f"Current GBP/USD: {current_price:.5f}")

test_module("Market Data (yfinance)", test_market_data)

# =============================================================================
# TEST 5: Fundamental Analysis
# =============================================================================
def test_fundamental_analysis():
    from analysis import FundamentalAnalyzer
    from core.enums import CurrencyPair
    
    analyzer = FundamentalAnalyzer()
    pairs = [CurrencyPair.GBP_USD, CurrencyPair.EUR_USD]
    
    signals = analyzer.analyze_today(pairs)
    print(f"Generated {len(signals)} fundamental signals")
    
    if signals:
        for pair_name, signal in signals.items():
            print(f"  {pair_name}: {signal.direction.value} (strength: {signal.strength.value})")
    else:
        print("  No high-impact news today (это нормально)")

test_module("Fundamental Analysis", test_fundamental_analysis)

# =============================================================================
# TEST 6: Trend Detection
# =============================================================================
def test_trend_detection():
    from analysis import TrendDetector
    from core.enums import CurrencyPair, TimeFrame
    
    detector = TrendDetector()
    analysis = detector.analyze_trend(CurrencyPair.GBP_USD, TimeFrame.H4)
    
    print(f"Pair: {analysis.pair.value}")
    print(f"Trend: {analysis.direction.value}")
    print(f"Strength: {analysis.strength.value}")
    print(f"EMA50: {analysis.ema50:.5f}")
    print(f"EMA200: {analysis.ema200:.5f}")
    print(f"Current Price: {analysis.current_price:.5f}")

test_module("Trend Detection", test_trend_detection)

# =============================================================================
# TEST 7: Liquidity Zones
# =============================================================================
def test_liquidity_zones():
    from analysis.liquidity_zones import LiquidityZoneDetector
    from core.enums import CurrencyPair, TimeFrame
    
    detector = LiquidityZoneDetector()
    zones = detector.detect_all_zones(CurrencyPair.GBP_USD, TimeFrame.M15)
    
    print(f"Detected {len(zones)} liquidity zones")
    
    if zones:
        strongest = detector.get_strongest_zones(zones, count=3)
        print("Top 3 strongest zones:")
        for i, zone in enumerate(strongest, 1):
            print(f"  {i}. {zone.zone_type.value} @ {zone.price_level:.5f} (strength: {zone.strength}/5)")

test_module("Liquidity Zone Detection", test_liquidity_zones)

# =============================================================================
# TEST 8: Signal Generator
# =============================================================================
def test_signal_generator():
    from analysis import SignalGenerator
    from core.enums import CurrencyPair
    
    generator = SignalGenerator()
    pairs = [CurrencyPair.GBP_USD]
    
    signals = generator.generate_signals(pairs)
    print(f"Generated {len(signals)} trading signals")
    
    if signals:
        for pair_name, signal in signals.items():
            print(f"  {pair_name}: {signal.direction.upper()} (strength: {signal.strength.value})")
    else:
        print("  No valid signals (условия не совпали)")

test_module("Signal Generator", test_signal_generator)

# =============================================================================
# TEST 9: Position Sizer
# =============================================================================
def test_position_sizer():
    from risk import PositionSizer
    from core.enums import CurrencyPair
    
    sizer = PositionSizer()
    position = sizer.calculate_position_size(
        pair=CurrencyPair.GBP_USD,
        entry_price=1.2700,
        stop_loss=1.2650
    )
    
    print(f"Position Size: {position.position_size_lots:.2f} lots")
    print(f"Risk Amount: ${position.risk_amount:.2f}")
    print(f"Stop Distance: {position.stop_distance_pips:.1f} pips")

test_module("Position Sizer", test_position_sizer)

# =============================================================================
# TEST 10: SL/TP Calculator
# =============================================================================
def test_sltp_calculator():
    from risk import SLTPCalculator
    from core.enums import CurrencyPair
    
    calculator = SLTPCalculator()
    levels = calculator.calculate_sl_tp(
        pair=CurrencyPair.GBP_USD,
        direction='long',
        entry_price=1.2700
    )
    
    print(f"Entry: {levels.entry_price:.5f}")
    print(f"Stop Loss: {levels.stop_loss:.5f}")
    print(f"TP1: {levels.take_profit_1:.5f} (+{levels.r_multiple_1:.1f}R)")
    print(f"TP2: {levels.take_profit_2:.5f} (+{levels.r_multiple_2:.1f}R)")
    print(f"TP3: {levels.take_profit_3:.5f} (+{levels.r_multiple_3:.1f}R)")

test_module("SL/TP Calculator", test_sltp_calculator)

# =============================================================================
# TEST 11: Trailing Stop Manager
# =============================================================================
def test_trailing_stop():
    from risk import TrailingStopManager
    
    manager = TrailingStopManager()
    
    r_achieved = 1.0
    update = manager.should_update_stop(
        direction='long',
        entry_price=1.2700,
        current_price=1.2750,
        current_stop=1.2650,
        r_achieved=r_achieved
    )
    
    if update:
        print(f"Stop update triggered: {update.reason}")
        print(f"Old Stop: {update.old_stop:.5f}")
        print(f"New Stop: {update.new_stop:.5f}")
    else:
        print("No stop update needed")

test_module("Trailing Stop Manager", test_trailing_stop)

# =============================================================================
# TEST 12: Message Templates
# =============================================================================
def test_message_templates():
    from notification import MessageFormatter
    
    formatter = MessageFormatter()
    
    msg = formatter.format_pre_market_alert(
        pair="GBP/USD",
        fundamental_direction="USD Weaker",
        event_name="US CPI",
        forecast="3.2%",
        previous="3.5%",
        impact="HIGH",
        time_to_open="4 hours"
    )
    
    print("Sample message length:", len(msg))
    assert len(msg) > 50, "Message too short"

test_module("Message Templates", test_message_templates)

# =============================================================================
# TEST 13: Telegram Bot
# =============================================================================
def test_telegram_bot():
    from notification import TelegramNotifier
    from core.config import config
    
    if not config.TELEGRAM_ENABLED:
        print("⚠️  Telegram disabled in .env (это нормально для тестирования)")
        return
    
    telegram = TelegramNotifier()
    
    if telegram.is_enabled():
        print(f"✅ Telegram connected (Chat ID: {config.TELEGRAM_CHAT_ID})")
        print("⚠️  Не отправляем тестовое сообщение чтобы не спамить")
    else:
        print("⚠️  Telegram not configured")

test_module("Telegram Bot", test_telegram_bot)

# =============================================================================
# TEST 14: Job Scheduler
# =============================================================================
def test_scheduler():
    from scheduler import JobScheduler
    
    scheduler = JobScheduler()
    print(f"Scheduler initialized")
    print(f"Monitoring pairs: {[p.value for p in scheduler.pairs]}")
    print(f"Telegram enabled: {scheduler.telegram.is_enabled()}")
    print(f"Position Monitor: {'Active' if scheduler.position_monitor else 'Disabled'}")

test_module("Job Scheduler", test_scheduler)

# =============================================================================
# FINAL RESULTS
# =============================================================================
print("\n" + "="*70)
print("📊 РЕЗУЛЬТАТЫ ТЕСТОВ")
print("="*70)
print(f"✅ Passed: {results['passed']}")
print(f"❌ Failed: {results['failed']}")
print(f"📊 Success Rate: {results['passed']/(results['passed']+results['failed'])*100:.1f}%")

if results['failed'] > 0:
    print("\n❌ Ошибки:")
    for error in results['errors']:
        print(f"  • {error['test']}: {error['error']}")

print("\n" + "="*70)

if results['failed'] == 0:
    print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    print("Система готова к запуску!")
    print("\n🚀 Запускай: python main.py --schedule")
else:
    print("⚠️  Некоторые тесты не прошли. Проверь ошибки выше.")

print("="*70 + "\n")

sys.exit(0 if results['failed'] == 0 else 1)