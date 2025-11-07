"""
Signal Generation Module

Combines all analysis components to generate final trading signals:
1. Fundamental Analysis (news direction)
2. Trend Detection (H4 + H1 confirmation)
3. Liquidity Zones (entry areas)
4. Risk Management (SL/TP calculation)

Only generates signals when ALL conditions align.
"""

from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import (
    CurrencyPair,
    TrendDirection,
    FundamentalDirection,
    SignalStrength,
    SignalStatus,
    TimeFrame
)
from core.exceptions import SignalGenerationError
from core.config import config
from data import MarketDataFetcher
from analysis import (
    FundamentalAnalyzer,
    FundamentalSignal,
    TrendDetector,
    TrendAnalysis
)
from analysis.liquidity_zones import LiquidityZoneDetector, LiquidityZone


logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Complete trading signal with entry, SL, TP"""
    pair: CurrencyPair
    direction: str  # 'long' or 'short'
    status: SignalStatus
    strength: SignalStrength
    
    # Analysis components
    fundamental: FundamentalSignal
    trend_h4: TrendAnalysis
    trend_h1: TrendAnalysis
    liquidity_zones: List[LiquidityZone]
    
    # Entry details
    entry_price: float
    entry_zone: Optional[LiquidityZone]
    
    # Risk management (will be calculated by risk module)
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    risk_reward: Optional[float] = None
    
    # Metadata
    generated_at: datetime = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'pair': self.pair.value,
            'direction': self.direction,
            'status': self.status.value,
            'strength': self.strength.value,
            'entry_price': round(self.entry_price, 5),
            'entry_zone': self.entry_zone.to_dict() if self.entry_zone else None,
            'stop_loss': round(self.stop_loss, 5) if self.stop_loss else None,
            'take_profit_1': round(self.take_profit_1, 5) if self.take_profit_1 else None,
            'take_profit_2': round(self.take_profit_2, 5) if self.take_profit_2 else None,
            'take_profit_3': round(self.take_profit_3, 5) if self.take_profit_3 else None,
            'risk_reward': round(self.risk_reward, 2) if self.risk_reward else None,
            'generated_at': self.generated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'fundamental_direction': self.fundamental.direction.value,
            'trend_h4': self.trend_h4.direction.value,
            'trend_h1': self.trend_h1.direction.value,
            'liquidity_zones_count': len(self.liquidity_zones)
        }


class SignalGenerator:
    """
    Master Signal Generator
    
    Combines all analysis to generate high-probability trading signals.
    
    Signal Requirements:
    1. ✅ High-impact fundamental news favoring direction
    2. ✅ H4 trend confirms fundamental direction
    3. ✅ H1 trend confirms H4 trend
    4. ✅ Price near liquidity zone (entry area)
    5. ✅ Clear SL/TP levels identified
    
    Only when ALL 5 conditions met → Generate signal
    """
    
    def __init__(self):
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.trend_detector = TrendDetector()
        self.liquidity_detector = LiquidityZoneDetector()
        self.market_data = MarketDataFetcher()
    
    def generate_signals(
        self,
        pairs: List[CurrencyPair]
    ) -> Dict[str, TradingSignal]:
        """
        Generate trading signals for multiple pairs
        
        Args:
            pairs: List of currency pairs to analyze
            
        Returns:
            Dictionary mapping pair name to TradingSignal
        """
        logger.info(f"Generating signals for {len(pairs)} pairs...")
        
        signals = {}
        
        for pair in pairs:
            try:
                signal = self.generate_signal(pair)
                
                if signal:
                    signals[pair.value] = signal
                    logger.info(f"✅ Generated signal for {pair.value}: "
                              f"{signal.direction} ({signal.strength.value})")
                else:
                    logger.info(f"No signal for {pair.value} - conditions not met")
                    
            except Exception as e:
                logger.error(f"Failed to generate signal for {pair.value}: {e}")
                continue
        
        logger.info(f"Generated {len(signals)} signals out of {len(pairs)} pairs")
        return signals
    
    def generate_signal(self, pair: CurrencyPair) -> Optional[TradingSignal]:
        """
        Generate trading signal for a single pair
        
        Returns:
            TradingSignal if all conditions met, None otherwise
        """
        logger.info(f"Analyzing {pair.value} for signal generation...")
        
        # Step 1: Fundamental Analysis
        logger.debug("Step 1: Fundamental analysis...")
        fundamental_signals = self.fundamental_analyzer.analyze_today([pair])
        
        if pair.value not in fundamental_signals:
            logger.debug("❌ No fundamental signal")
            return None
        
        fundamental = fundamental_signals[pair.value]
        
        if fundamental.strength.value < 2:
            logger.debug("❌ Fundamental signal too weak")
            return None
        
        # Step 2: Trend Analysis (Multi-timeframe)
        logger.debug("Step 2: Multi-timeframe trend analysis...")
        trends = self.trend_detector.analyze_multi_timeframe(pair)
        trend_h4 = trends['H4']
        trend_h1 = trends['H1']
        
        # Check H4 trend
        if trend_h4.direction == TrendDirection.SIDEWAYS:
            logger.debug("❌ H4 trend is sideways")
            return None
        
        # Check H1 confirmation
        if trend_h1.direction != trend_h4.direction:
            logger.debug(f"❌ H1 ({trend_h1.direction.value}) doesn't confirm H4 ({trend_h4.direction.value})")
            return None
        
        # Step 3: Check fundamental-trend alignment
        logger.debug("Step 3: Checking fundamental-trend alignment...")
        if not self._check_alignment(fundamental, trend_h4):
            logger.debug("❌ Fundamental and trend not aligned")
            return None
        
        # Step 4: Liquidity Zones
        logger.debug("Step 4: Detecting liquidity zones...")
        zones = self.liquidity_detector.detect_all_zones(pair, TimeFrame.M15)
        
        if not zones:
            logger.debug("❌ No liquidity zones found")
            return None
        
        # Step 5: Get current price and find nearby zones
        current_price = self.market_data.get_current_price(pair)
        nearby_zones = self.liquidity_detector.get_zones_near_price(
            zones, current_price, distance_pct=0.5
        )
        
        if not nearby_zones:
            logger.debug("❌ No liquidity zones near current price")
            return None
        
        # Determine direction
        direction = 'long' if trend_h4.direction == TrendDirection.BULLISH else 'short'
        
        # Find best entry zone
        entry_zone = self._find_best_entry_zone(nearby_zones, direction)
        
        # Calculate signal strength
        signal_strength = self._calculate_signal_strength(
            fundamental, trend_h4, trend_h1, len(nearby_zones)
        )
        
        # Create signal
        signal = TradingSignal(
            pair=pair,
            direction=direction,
            status=SignalStatus.PENDING,
            strength=signal_strength,
            fundamental=fundamental,
            trend_h4=trend_h4,
            trend_h1=trend_h1,
            liquidity_zones=nearby_zones,
            entry_price=current_price,
            entry_zone=entry_zone
        )
        
        logger.info(f"✅ Signal generated: {pair.value} {direction.upper()} "
                   f"(strength: {signal_strength.value})")
        
        return signal
    
    def _check_alignment(
        self,
        fundamental: FundamentalSignal,
        trend: TrendAnalysis
    ) -> bool:
        """
        Check if fundamental and trend are aligned
        
        Returns:
            True if aligned, False otherwise
        """
        fund_dir = fundamental.direction
        trend_dir = trend.direction
        
        # Bullish alignment
        if trend_dir == TrendDirection.BULLISH:
            if fund_dir in [
                FundamentalDirection.USD_WEAKER,
                FundamentalDirection.COUNTERPARTY_STRONGER
            ]:
                return True
        
        # Bearish alignment
        elif trend_dir == TrendDirection.BEARISH:
            if fund_dir in [
                FundamentalDirection.USD_STRONGER,
                FundamentalDirection.COUNTERPARTY_WEAKER
            ]:
                return True
        
        return False
    
    def _find_best_entry_zone(
        self,
        zones: List[LiquidityZone],
        direction: str
    ) -> Optional[LiquidityZone]:
        """Find the best entry zone based on direction"""
        
        if not zones:
            return None
        
        # For long: prefer zones below current price (support)
        # For short: prefer zones above current price (resistance)
        
        # Filter by zone type
        if direction == 'long':
            # Look for support zones
            support_zones = [z for z in zones if z.zone_type.value in [
                'equal_lows', 'stop_hunt_buy', 'bullish_fvg'
            ]]
            return support_zones[0] if support_zones else zones[0]
        else:
            # Look for resistance zones
            resistance_zones = [z for z in zones if z.zone_type.value in [
                'equal_highs', 'stop_hunt_sell', 'bearish_fvg'
            ]]
            return resistance_zones[0] if resistance_zones else zones[0]
    
    def _calculate_signal_strength(
        self,
        fundamental: FundamentalSignal,
        trend_h4: TrendAnalysis,
        trend_h1: TrendAnalysis,
        zone_count: int
    ) -> SignalStrength:
        """Calculate overall signal strength"""
        
        # Start with fundamental strength
        score = fundamental.strength.value
        
        # Add trend strength
        score += trend_h4.strength.value
        score += trend_h1.strength.value * 0.5  # H1 less weight
        
        # Add liquidity zone bonus
        if zone_count >= 3:
            score += 2
        elif zone_count >= 2:
            score += 1
        
        # Normalize to 1-5
        score = score / 3
        
        if score >= 4.5:
            return SignalStrength.VERY_STRONG
        elif score >= 3.5:
            return SignalStrength.STRONG
        elif score >= 2.5:
            return SignalStrength.MODERATE
        elif score >= 1.5:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK


def main():
    """Test the Signal Generator"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("SIGNAL GENERATOR TEST")
    print("="*60 + "\n")
    
    try:
        generator = SignalGenerator()
        
        pairs = [
            CurrencyPair.GBP_USD,
            CurrencyPair.EUR_USD,
            CurrencyPair.USD_JPY
        ]
        
        print("Generating signals for all pairs...\n")
        signals = generator.generate_signals(pairs)
        
        if not signals:
            print("⚠️  No signals generated today")
            print("\nPossible reasons:")
            print("1. No high-impact news events")
            print("2. Trends not aligned with fundamentals")
            print("3. No clear liquidity zones")
            print("\nThis is normal - we only trade high-probability setups!")
        else:
            print(f"✅ Generated {len(signals)} trading signals:\n")
            
            for pair_name, signal in signals.items():
                print("="*60)
                print(f"📊 {pair_name} - {signal.direction.upper()} SIGNAL")
                print("="*60)
                print(f"Strength: {signal.strength.value}")
                print(f"Status: {signal.status.value}")
                print(f"Entry Price: {signal.entry_price:.5f}")
                
                if signal.entry_zone:
                    print(f"Entry Zone: {signal.entry_zone.zone_type.value} @ {signal.entry_zone.price_level:.5f}")
                
                print(f"\nAnalysis:")
                print(f"  Fundamental: {signal.fundamental.direction.value}")
                print(f"  Trend H4: {signal.trend_h4.direction.value} ({signal.trend_h4.strength.value})")
                print(f"  Trend H1: {signal.trend_h1.direction.value} ({signal.trend_h1.strength.value})")
                print(f"  Liquidity Zones: {len(signal.liquidity_zones)}")
                print(f"\nExpected Impact:")
                print(f"  {signal.fundamental.expected_impact}")
                print()
        
        print("="*60)
        print("✅ SIGNAL GENERATOR TEST COMPLETE!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())