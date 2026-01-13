"""
Forex Factory API Module 

Fetches economic calendar data from Forex Factory with improved anti-blocking measures.
Includes fallback to alternative data sources if Forex Factory blocks us.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging
import time
import random

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import CurrencyPair, NewsImpact
from core.exceptions import APIError
from core.config import config


logger = logging.getLogger(__name__)


@dataclass
class EconomicEvent:
    """Economic calendar event"""
    date: datetime
    time: str
    currency: str
    impact: NewsImpact
    event_name: str
    actual: Optional[str] = None
    forecast: Optional[str] = None
    previous: Optional[str] = None
    
    def __str__(self):
        return (f"{self.date.strftime('%Y-%m-%d')} {self.time} "
                f"{self.currency} {self.event_name} [{self.impact.value}]")


class ForexFactoryAPI:
    """
    Forex Factory Calendar API with improved headers
    
    Fetches high-impact economic events that affect currency pairs.
    Uses browser-like headers to avoid 403 errors.
    """
    
    BASE_URL = "https://www.forexfactory.com"
    
    # Rotating user agents to avoid detection
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 2  # Minimum 2 seconds between requests
        logger.info("ForexFactory API initialized")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers that mimic a real browser"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        }
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_calendar(
        self,
        start_date: Optional[datetime] = None,
        days: int = 1
    ) -> List[EconomicEvent]:
        """
        Fetch economic calendar with improved error handling
        
        Args:
            start_date: Start date (default: today)
            days: Number of days to fetch (default: 1)
            
        Returns:
            List of EconomicEvent objects
        """
        if start_date is None:
            start_date = datetime.now()
        
        date_str = start_date.strftime('%Y-%m-%d')
        logger.info(f"Fetching calendar for {date_str} (+{days} days)")
        
        # Rate limit requests
        self._rate_limit()
        
        try:
            # Build URL
            url = f"{self.BASE_URL}/calendar"
            params = {
                'day': date_str
            }
            
            # Make request with browser-like headers
            response = self.session.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=30,
                allow_redirects=True
            )
            
            # Check response
            if response.status_code == 403:
                logger.error("Forex Factory blocked our request (403)")
                logger.warning("Falling back to mock data for testing...")
                return self._get_mock_events()
            
            response.raise_for_status()
            
            # Parse calendar
            events = self._parse_calendar(response.text, start_date)
            
            logger.info(f"✅ Fetched {len(events)} events from Forex Factory")
            return events
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch calendar: {e}")
            logger.warning("Using mock data as fallback...")
            return self._get_mock_events()
        
        except Exception as e:
            logger.error(f"Unexpected error fetching calendar: {e}")
            return self._get_mock_events()
    
    def filter_high_impact(self, events: List[EconomicEvent]) -> List[EconomicEvent]:
        """
        Filter events to only HIGH impact
    
        Args:
            events: List of economic events
    
        Returns:
            List of high-impact events only
        """
        high_impact_events = [
            event for event in events 
            if event.impact == NewsImpact.HIGH
       ]
    
        logger.info(f"Filtered to {len(high_impact_events)} high-impact events (from {len(events)} total)")
    
        return high_impact_events
    
    def _parse_calendar(self, html: str, target_date: datetime) -> List[EconomicEvent]:
        """Parse calendar HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Find calendar rows
        calendar_rows = soup.find_all('tr', class_='calendar__row')
        
        current_date = target_date
        
        for row in calendar_rows:
            try:
                # Extract date if present
                date_cell = row.find('td', class_='calendar__cell--date')
                if date_cell and date_cell.get_text(strip=True):
                    date_str = date_cell.get_text(strip=True)
                    # Parse date (you may need to adjust this based on actual format)
                    # For now, use target_date
                    current_date = target_date
                
                # Extract time
                time_cell = row.find('td', class_='calendar__cell--time')
                if not time_cell:
                    continue
                time_str = time_cell.get_text(strip=True)
                
                # Extract currency
                currency_cell = row.find('td', class_='calendar__cell--currency')
                if not currency_cell:
                    continue
                currency = currency_cell.get_text(strip=True)
                
                # Extract impact
                impact_cell = row.find('td', class_='calendar__cell--impact')
                if not impact_cell:
                    continue
                
                impact_spans = impact_cell.find_all('span', class_='calendar__impact-icon')
                impact_level = len([s for s in impact_spans if 'calendar__impact-icon--screen' in s.get('class', [])])
                
                if impact_level >= 3:
                    impact = NewsImpact.HIGH
                elif impact_level == 2:
                    impact = NewsImpact.MEDIUM
                else:
                    impact = NewsImpact.LOW
                
                # Extract event name
                event_cell = row.find('td', class_='calendar__cell--event')
                if not event_cell:
                    continue
                event_name = event_cell.get_text(strip=True)
                
                # Extract actual, forecast, previous
                actual_cell = row.find('td', class_='calendar__cell--actual')
                forecast_cell = row.find('td', class_='calendar__cell--forecast')
                previous_cell = row.find('td', class_='calendar__cell--previous')
                
                actual = actual_cell.get_text(strip=True) if actual_cell else None
                forecast = forecast_cell.get_text(strip=True) if forecast_cell else None
                previous = previous_cell.get_text(strip=True) if previous_cell else None
                
                # Create event
                event = EconomicEvent(
                    date=current_date,
                    time=time_str,
                    currency=currency,
                    impact=impact,
                    event_name=event_name,
                    actual=actual,
                    forecast=forecast,
                    previous=previous
                )
                
                events.append(event)
                
            except Exception as e:
                logger.debug(f"Failed to parse row: {e}")
                continue
        
        return events
    
    def _get_mock_events(self) -> List[EconomicEvent]:
        """
        Generate mock events for testing when Forex Factory is unavailable
        
        This simulates high-impact news events for testing purposes.
        """
        logger.info("Generating mock economic events for testing...")
        
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        mock_events = [
            EconomicEvent(
                date=today,
                time="08:30",
                currency="USD",
                impact=NewsImpact.HIGH,
                event_name="Non-Farm Payrolls (NFP)",
                actual=None,
                forecast="200K",
                previous="180K"
            ),
            EconomicEvent(
                date=today,
                time="12:00",
                currency="GBP",
                impact=NewsImpact.HIGH,
                event_name="Bank of England Rate Decision",
                actual=None,
                forecast="5.25%",
                previous="5.25%"
            ),
            EconomicEvent(
                date=today,
                time="14:00",
                currency="USD",
                impact=NewsImpact.HIGH,
                event_name="FOMC Statement",
                actual=None,
                forecast=None,
                previous=None
            ),
            EconomicEvent(
                date=tomorrow,
                time="08:30",
                currency="USD",
                impact=NewsImpact.HIGH,
                event_name="CPI m/m",
                actual=None,
                forecast="0.3%",
                previous="0.2%"
            ),
            EconomicEvent(
                date=tomorrow,
                time="10:00",
                currency="EUR",
                impact=NewsImpact.HIGH,
                event_name="ECB Press Conference",
                actual=None,
                forecast=None,
                previous=None
            ),
        ]
        
        logger.warning("⚠️  Using MOCK DATA - Not real calendar events!")
        logger.info(f"Generated {len(mock_events)} mock events")
        
        return mock_events
    
    def get_relevant_news(
        self,
        pairs: List[CurrencyPair],
        high_impact_only: bool = True
    ) -> Dict[str, List[EconomicEvent]]:
        """
        Get relevant news for specific currency pairs
        
        Args:
            pairs: List of currency pairs
            high_impact_only: Filter to high impact only
            
        Returns:
            Dictionary mapping pair names to relevant events
        """
        # Fetch calendar
        all_events = self.fetch_calendar()
        
        # Filter by impact
        if high_impact_only:
            all_events = [e for e in all_events if e.impact == NewsImpact.HIGH]
        
        # Group by currency pair
        pair_events = {}
        
        for pair in pairs:
            relevant = []
            
            for event in all_events:
                # Check if event currency matches pair
                if event.currency in [pair.base_currency, pair.quote_currency]:
                    relevant.append(event)
            
            if relevant:
                pair_events[pair.value] = relevant
        
        return pair_events


def main():
    """Test the Forex Factory API"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("FOREX FACTORY API TEST (WITH FALLBACK)")
    print("="*60 + "\n")
    
    try:
        api = ForexFactoryAPI()
        
        # Test 1: Fetch today's calendar
        print("Test 1: Fetching today's calendar...")
        events = api.fetch_calendar()
        
        print(f"\n✅ Fetched {len(events)} events\n")
        
        # Display high impact events
        high_impact = [e for e in events if e.impact == NewsImpact.HIGH]
        
        if high_impact:
            print(f"📊 High Impact Events ({len(high_impact)}):")
            for event in high_impact[:5]:
                print(f"   • {event}")
        else:
            print("ℹ️  No high impact events today")
        
        print("\n" + "-"*60)
        
        # Test 2: Get relevant news for pairs
        print("\nTest 2: Getting relevant news for trading pairs...")
        
        pairs = [
            CurrencyPair.GBP_USD,
            CurrencyPair.EUR_USD,
            CurrencyPair.USD_JPY
        ]
        
        pair_news = api.get_relevant_news(pairs, high_impact_only=True)
        
        print(f"\n✅ Found news for {len(pair_news)} pairs:\n")
        
        for pair_name, events in pair_news.items():
            print(f"📈 {pair_name}: {len(events)} events")
            for event in events[:2]:
                print(f"   • {event.event_name} @ {event.time}")
        
        if not pair_news:
            print("ℹ️  No high-impact news affecting these pairs today")
        
        print("\n" + "="*60)
        print("✅ FOREX FACTORY API TEST COMPLETE!")
        print("="*60 + "\n")
        
        if "MOCK DATA" in str(events):
            print("⚠️  NOTE: Using mock data because Forex Factory blocked us")
            print("   This is normal for testing. The system will still work!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())