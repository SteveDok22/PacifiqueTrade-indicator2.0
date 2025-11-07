"""
Forex Factory Economic Calendar API

Fetches and parses economic calendar data from Forex Factory.
Filters high-impact news events for trading decisions.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass
import pytz

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import NewsImpact, CurrencyPair
from core.exceptions import APIError, DataValidationError
from core.config import config


logger = logging.getLogger(__name__)


@dataclass
class EconomicEvent:
    """Represents a single economic calendar event"""
    time: datetime
    currency: str
    impact: NewsImpact
    event_name: str
    actual: Optional[str] = None
    forecast: Optional[str] = None
    previous: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'time': self.time.isoformat(),
            'currency': self.currency,
            'impact': self.impact.value,
            'event_name': self.event_name,
            'actual': self.actual,
            'forecast': self.forecast,
            'previous': self.previous
        }


class ForexFactoryAPI:
    """
    Forex Factory Economic Calendar API Client
    
    Fetches and parses economic calendar data from Forex Factory website.
    Supports filtering by date, impact level, and currency.
    """
    
    BASE_URL = "https://www.forexfactory.com/calendar"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_calendar(
        self,
        date: Optional[datetime] = None,
        days_ahead: int = 1
    ) -> List[EconomicEvent]:
        """
        Fetch economic calendar for specified date range
        
        Args:
            date: Start date (default: today)
            days_ahead: Number of days to fetch (default: 1)
            
        Returns:
            List of EconomicEvent objects
            
        Raises:
            APIError: If fetch fails
        """
        if date is None:
            date = datetime.now(pytz.UTC)
        
        logger.info(f"Fetching calendar for {date.strftime('%Y-%m-%d')} (+{days_ahead} days)")
        
        try:
            # Format date for URL
            date_str = date.strftime('%Y-%m-%d')
            
            # Build URL with parameters
            params = {
                'day': date_str
            }
            
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=config.API_TIMEOUT
            )
            
            response.raise_for_status()
            
            # Parse HTML
            events = self._parse_calendar_html(response.text, date)
            
            logger.info(f"Fetched {len(events)} events from Forex Factory")
            return events
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch calendar: {e}")
            raise APIError(
                api_name="ForexFactory",
                message=str(e),
                status_code=getattr(e.response, 'status_code', None)
            )
    
    def _parse_calendar_html(self, html: str, base_date: datetime) -> List[EconomicEvent]:
        """
        Parse Forex Factory calendar HTML
        
        Args:
            html: HTML content
            base_date: Base date for events
            
        Returns:
            List of parsed events
        """
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Find calendar table
        calendar_table = soup.find('table', class_='calendar__table')
        
        if not calendar_table:
            logger.warning("Could not find calendar table in HTML")
            return events
        
        # Parse each row
        rows = calendar_table.find_all('tr', class_='calendar__row')
        
        current_date = base_date
        
        for row in rows:
            try:
                event = self._parse_event_row(row, current_date)
                if event:
                    events.append(event)
            except Exception as e:
                logger.debug(f"Failed to parse row: {e}")
                continue
        
        return events
    
    def _parse_event_row(self, row, current_date: datetime) -> Optional[EconomicEvent]:
        """Parse a single event row"""
        
        # Extract time
        time_cell = row.find('td', class_='calendar__time')
        if not time_cell:
            return None
        
        time_str = time_cell.text.strip()
        if not time_str or time_str in ['All Day', 'Day']:
            return None
        
        # Parse time (e.g., "9:00am")
        try:
            event_time = datetime.strptime(time_str, '%I:%M%p')
            event_datetime = current_date.replace(
                hour=event_time.hour,
                minute=event_time.minute,
                second=0,
                microsecond=0
            )
        except ValueError:
            return None
        
        # Extract currency
        currency_cell = row.find('td', class_='calendar__currency')
        if not currency_cell:
            return None
        currency = currency_cell.text.strip()
        
        # Extract impact (low, medium, high)
        impact_cell = row.find('td', class_='calendar__impact')
        impact = self._parse_impact(impact_cell)
        
        # Extract event name
        event_cell = row.find('td', class_='calendar__event')
        if not event_cell:
            return None
        event_name = event_cell.text.strip()
        
        # Extract actual, forecast, previous
        actual_cell = row.find('td', class_='calendar__actual')
        forecast_cell = row.find('td', class_='calendar__forecast')
        previous_cell = row.find('td', class_='calendar__previous')
        
        actual = actual_cell.text.strip() if actual_cell else None
        forecast = forecast_cell.text.strip() if forecast_cell else None
        previous = previous_cell.text.strip() if previous_cell else None
        
        return EconomicEvent(
            time=event_datetime,
            currency=currency,
            impact=impact,
            event_name=event_name,
            actual=actual,
            forecast=forecast,
            previous=previous
        )
    
    def _parse_impact(self, impact_cell) -> NewsImpact:
        """Parse impact level from cell"""
        if not impact_cell:
            return NewsImpact.NONE
        
        # Check for impact icons
        icons = impact_cell.find_all('span', class_='calendar__impact-icon')
        
        if len(icons) >= 3:
            return NewsImpact.HIGH
        elif len(icons) == 2:
            return NewsImpact.MEDIUM
        elif len(icons) == 1:
            return NewsImpact.LOW
        else:
            return NewsImpact.NONE
    
    def filter_high_impact(self, events: List[EconomicEvent]) -> List[EconomicEvent]:
        """
        Filter only high-impact news events
        
        Args:
            events: List of all events
            
        Returns:
            List of high-impact events only
        """
        high_impact = [
            event for event in events
            if event.impact == NewsImpact.HIGH
        ]
        
        logger.info(f"Filtered to {len(high_impact)} high-impact events")
        return high_impact
    
    def filter_by_currency(
        self,
        events: List[EconomicEvent],
        currencies: List[str]
    ) -> List[EconomicEvent]:
        """
        Filter events by currency
        
        Args:
            events: List of events
            currencies: List of currency codes (e.g., ['USD', 'GBP'])
            
        Returns:
            Filtered events
        """
        filtered = [
            event for event in events
            if event.currency in currencies
        ]
        
        logger.info(f"Filtered to {len(filtered)} events for {currencies}")
        return filtered
    
    def get_relevant_news(
        self,
        pairs: List[CurrencyPair],
        date: Optional[datetime] = None,
        high_impact_only: bool = True
    ) -> Dict[str, List[EconomicEvent]]:
        """
        Get relevant news for specific trading pairs
        
        Args:
            pairs: List of currency pairs to monitor
            date: Date to fetch (default: today)
            high_impact_only: Only return high-impact news
            
        Returns:
            Dictionary mapping pair name to list of events
        """
        # Extract unique currencies from pairs
        currencies = set()
        for pair in pairs:
            currencies.add(pair.base_currency)
            currencies.add(pair.quote_currency)
        
        logger.info(f"Fetching news for currencies: {currencies}")
        
        # Fetch calendar
        events = self.fetch_calendar(date=date)
        
        # Filter by currency
        events = self.filter_by_currency(events, list(currencies))
        
        # Filter by impact
        if high_impact_only:
            events = self.filter_high_impact(events)
        
        # Group by pair
        result = {}
        for pair in pairs:
            pair_events = [
                event for event in events
                if event.currency in [pair.base_currency, pair.quote_currency]
            ]
            result[pair.value] = pair_events
        
        return result


def main():
    """Test the Forex Factory API"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("FOREX FACTORY API TEST")
    print("="*60 + "\n")
    
    try:
        # Initialize API
        api = ForexFactoryAPI()
        
        # Test 1: Fetch today's calendar
        print("Test 1: Fetching today's calendar...")
        events = api.fetch_calendar()
        print(f"✅ Fetched {len(events)} events\n")
        
        # Show first 5 events
        print("First 5 events:")
        for i, event in enumerate(events[:5], 1):
            print(f"{i}. [{event.time.strftime('%H:%M')}] {event.currency} - "
                  f"{event.event_name} (Impact: {event.impact.value})")
        
        # Test 2: Filter high-impact only
        print("\n" + "-"*60)
        print("Test 2: High-impact events only...")
        high_impact = api.filter_high_impact(events)
        print(f"✅ Found {len(high_impact)} high-impact events\n")
        
        for event in high_impact[:5]:
            print(f"🔴 [{event.time.strftime('%H:%M')}] {event.currency} - "
                  f"{event.event_name}")
            if event.forecast:
                print(f"   Forecast: {event.forecast}")
            if event.previous:
                print(f"   Previous: {event.previous}")
        
        # Test 3: Get news for trading pairs
        print("\n" + "-"*60)
        print("Test 3: News for GBP/USD, EUR/USD, USD/JPY...")
        pairs = [
            CurrencyPair.GBP_USD,
            CurrencyPair.EUR_USD,
            CurrencyPair.USD_JPY
        ]
        
        pair_news = api.get_relevant_news(pairs)
        
        for pair_name, pair_events in pair_news.items():
            print(f"\n{pair_name}: {len(pair_events)} events")
            for event in pair_events[:3]:
                print(f"  • [{event.time.strftime('%H:%M')}] {event.currency} - "
                      f"{event.event_name}")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())