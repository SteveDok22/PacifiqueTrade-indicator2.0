"""
Fundamental Analysis Module

Analyzes economic calendar events to determine market direction.
Filters high-impact news and determines USD strength/weakness.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import (
    CurrencyPair,
    NewsImpact,
    FundamentalDirection,
    SignalStrength
)
from core.exceptions import SignalGenerationError
from core.config import config
from data import ForexFactoryAPI, EconomicEvent


logger = logging.getLogger(__name__)


@dataclass
class FundamentalSignal:
    """Represents a fundamental analysis signal"""
    pair: CurrencyPair
    direction: FundamentalDirection
    strength: SignalStrength
    events: List[EconomicEvent]
    analysis_time: datetime
    expected_impact: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'pair': self.pair.value,
            'direction': self.direction.value,
            'strength': self.strength.value,
            'events_count': len(self.events),
            'analysis_time': self.analysis_time.isoformat(),
            'expected_impact': self.expected_impact
        }


class FundamentalAnalyzer:
    """
    Fundamental Analysis Engine
    
    Analyzes economic calendar events and determines:
    1. USD strength/weakness based on news
    2. Impact on specific currency pairs
    3. Expected market direction
    
    Strategy Logic:
    - Better than expected US data → USD strengthens (short EUR/USD, GBP/USD, long USD/JPY)
    - Worse than expected US data → USD weakens (long EUR/USD, GBP/USD, short USD/JPY)
    - Focus on high-impact events: NFP, CPI, FOMC, BoE, ECB, BoJ rates
    """
    
    # Events that strongly affect each currency
    CURRENCY_EVENTS = {
        'USD': ['NFP', 'CPI', 'FOMC', 'GDP', 'RETAIL_SALES', 'JOBLESS'],
        'GBP': ['BOE', 'CPI', 'GDP', 'PMI', 'RETAIL'],
        'EUR': ['ECB', 'CPI', 'GDP', 'PMI', 'ZEW', 'IFO'],
        'JPY': ['BOJ', 'CPI', 'TANKAN', 'GDP']
    }
    
    def __init__(self):
        self.api = ForexFactoryAPI()
    
    def analyze_today(
        self,
        pairs: List[CurrencyPair]
    ) -> Dict[str, FundamentalSignal]:
        """
        Analyze fundamental outlook for today
        
        Args:
            pairs: List of currency pairs to analyze
            
        Returns:
            Dictionary mapping pair name to FundamentalSignal
        """
        logger.info("Running fundamental analysis for today")
        
        # Fetch today's high-impact news
        news = self.api.get_relevant_news(pairs, high_impact_only=True)
        
        signals = {}
        
        for pair in pairs:
            pair_events = news.get(pair.value, [])
            
            if not pair_events:
                logger.info(f"No high-impact news for {pair.value} today")
                continue
            
            # Analyze the pair
            signal = self._analyze_pair(pair, pair_events)
            
            if signal:
                signals[pair.value] = signal
                logger.info(f"Generated fundamental signal for {pair.value}: "
                          f"{signal.direction.value} (strength: {signal.strength.value})")
        
        return signals
    
    def _analyze_pair(
        self,
        pair: CurrencyPair,
        events: List[EconomicEvent]
    ) -> Optional[FundamentalSignal]:
        """
        Analyze fundamental direction for a specific pair
        
        Args:
            pair: Currency pair
            events: List of economic events affecting this pair
            
        Returns:
            FundamentalSignal or None
        """
        base_currency = pair.base_currency
        quote_currency = pair.quote_currency
        
        # Score each currency based on news
        base_score = self._calculate_currency_score(base_currency, events)
        quote_score = self._calculate_currency_score(quote_currency, events)
        
        logger.debug(f"{pair.value} scores: {base_currency}={base_score}, {quote_currency}={quote_score}")
        
        # Determine direction
        score_diff = base_score - quote_score
        
        if abs(score_diff) < 1:
            # Not enough conviction
            return None
        
        # Determine direction and strength
        if score_diff > 0:
            # Base currency stronger
            if pair.quote_currency == 'USD':
                direction = FundamentalDirection.USD_WEAKER
            else:
                direction = FundamentalDirection.COUNTERPARTY_STRONGER
        else:
            # Quote currency stronger
            if pair.quote_currency == 'USD':
                direction = FundamentalDirection.USD_STRONGER
            else:
                direction = FundamentalDirection.COUNTERPARTY_WEAKER
        
        # Calculate signal strength
        strength = self._calculate_strength(abs(score_diff), len(events))
        
        # Generate expected impact description
        expected_impact = self._generate_impact_description(pair, direction, events)
        
        signal = FundamentalSignal(
            pair=pair,
            direction=direction,
            strength=strength,
            events=events,
            analysis_time=datetime.now(),
            expected_impact=expected_impact
        )
        
        return signal
    
    def _calculate_currency_score(
        self,
        currency: str,
        events: List[EconomicEvent]
    ) -> float:
        """
        Calculate currency strength score based on news
        
        Positive score = currency strengthening
        Negative score = currency weakening
        
        Args:
            currency: Currency code (e.g., 'USD', 'GBP')
            events: Economic events
            
        Returns:
            Score (-10 to +10)
        """
        score = 0.0
        
        currency_events = [e for e in events if e.currency == currency]
        
        for event in currency_events:
            # Skip if no forecast or actual
            if not event.forecast or not event.actual:
                continue
            
            try:
                # Parse values (remove %, K, M, B suffixes)
                actual = self._parse_economic_value(event.actual)
                forecast = self._parse_economic_value(event.forecast)
                
                if actual is None or forecast is None:
                    continue
                
                # Calculate surprise (actual - forecast)
                surprise = actual - forecast
                
                # Determine if higher is better for this event
                higher_is_better = self._is_higher_better(event.event_name)
                
                # Calculate impact
                if higher_is_better:
                    event_score = surprise
                else:
                    event_score = -surprise
                
                # Weight by event importance
                weight = 3.0  # High impact already filtered
                
                score += event_score * weight
                
                logger.debug(f"{event.event_name} ({currency}): "
                           f"actual={actual}, forecast={forecast}, score_contribution={event_score * weight}")
                
            except Exception as e:
                logger.warning(f"Failed to parse event {event.event_name}: {e}")
                continue
        
        # Normalize score to -10 to +10 range
        score = max(-10, min(10, score))
        
        return score
    
    def _parse_economic_value(self, value_str: str) -> Optional[float]:
        """Parse economic value from string"""
        if not value_str or value_str.strip() == '':
            return None
        
        # Remove common suffixes and symbols
        value_str = value_str.replace('%', '').replace('K', '000').replace('M', '000000')
        value_str = value_str.replace('B', '000000000').replace(',', '').strip()
        
        try:
            return float(value_str)
        except ValueError:
            return None
    
    def _is_higher_better(self, event_name: str) -> bool:
        """
        Determine if higher value is better for the currency
        
        Higher is better for: GDP, Employment, Retail Sales, PMI
        Lower is better for: Unemployment, Inflation (sometimes), Deficits
        """
        event_upper = event_name.upper()
        
        # Higher is good
        if any(keyword in event_upper for keyword in [
            'GDP', 'EMPLOYMENT', 'RETAIL', 'PMI', 'SALES', 'CONSUMER', 'CONFIDENCE'
        ]):
            return True
        
        # Lower is good
        if any(keyword in event_upper for keyword in [
            'UNEMPLOYMENT', 'JOBLESS', 'CLAIMS', 'DEFICIT'
        ]):
            return False
        
        # For inflation (CPI, PPI) - context dependent, assume higher is neutral/slightly negative
        if any(keyword in event_upper for keyword in ['CPI', 'PPI', 'INFLATION']):
            return False
        
        # Default: higher is better
        return True
    
    def _calculate_strength(self, score_diff: float, event_count: int) -> SignalStrength:
        """Calculate signal strength based on score difference and event count"""
        
        # More events = stronger signal
        event_multiplier = min(event_count / 3.0, 1.5)
        adjusted_score = score_diff * event_multiplier
        
        if adjusted_score >= 8:
            return SignalStrength.VERY_STRONG
        elif adjusted_score >= 5:
            return SignalStrength.STRONG
        elif adjusted_score >= 3:
            return SignalStrength.MODERATE
        elif adjusted_score >= 1.5:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK
    
    def _generate_impact_description(
        self,
        pair: CurrencyPair,
        direction: FundamentalDirection,
        events: List[EconomicEvent]
    ) -> str:
        """Generate human-readable impact description"""
        
        event_names = [e.event_name for e in events[:3]]  # Top 3 events
        events_str = ', '.join(event_names)
        
        if direction == FundamentalDirection.USD_STRONGER:
            return f"USD strengthening due to {events_str}. Expect {pair.value} to move down."
        elif direction == FundamentalDirection.USD_WEAKER:
            return f"USD weakening due to {events_str}. Expect {pair.value} to move up."
        elif direction == FundamentalDirection.COUNTERPARTY_STRONGER:
            return f"{pair.base_currency} strengthening due to {events_str}. Expect {pair.value} to move up."
        else:
            return f"{pair.base_currency} weakening due to {events_str}. Expect {pair.value} to move down."
    
    def should_trade_today(self, pair: CurrencyPair) -> bool:
        """
        Quick check: Should we consider trading this pair today?
        
        Returns True if there are high-impact news events
        """
        news = self.api.get_relevant_news([pair], high_impact_only=True)
        return len(news.get(pair.value, [])) > 0


def main():
    """Test the Fundamental Analyzer"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("FUNDAMENTAL ANALYZER TEST")
    print("="*60 + "\n")
    
    try:
        analyzer = FundamentalAnalyzer()
        
        pairs = [
            CurrencyPair.GBP_USD,
            CurrencyPair.EUR_USD,
            CurrencyPair.USD_JPY
        ]
        
        # Test 1: Analyze today's fundamentals
        print("Test 1: Analyzing today's fundamentals...\n")
        signals = analyzer.analyze_today(pairs)
        
        if not signals:
            print("⚠️  No high-impact news found for today")
            print("   This is normal if there are no major events scheduled")
        else:
            print(f"✅ Generated {len(signals)} fundamental signals:\n")
            
            for pair_name, signal in signals.items():
                print(f"📊 {pair_name}")
                print(f"   Direction: {signal.direction.value}")
                print(f"   Strength: {signal.strength.value}")
                print(f"   Events: {len(signal.events)}")
                print(f"   Impact: {signal.expected_impact}")
                print()
        
        # Test 2: Check if should trade
        print("\nTest 2: Checking if pairs are tradeable today...")
        for pair in pairs:
            tradeable = analyzer.should_trade_today(pair)
            status = "✅ YES" if tradeable else "❌ NO"
            print(f"{pair.value}: {status}")
        
        print("\n" + "="*60)
        print("✅ FUNDAMENTAL ANALYZER TEST COMPLETE!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())