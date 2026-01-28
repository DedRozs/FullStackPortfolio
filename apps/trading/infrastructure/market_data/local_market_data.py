"""Local market data service that reads from stored intraday bars.

This service replaces external API calls (yfinance) by computing daily/weekly/monthly
aggregates from locally stored 1-minute bars fetched from Databento.

Architecture:
1. Daily scheduled task fetches intraday bars from Databento → IntradayBarModel
2. This service queries IntradayBarModel to compute session aggregates
3. Pipeline uses this service (never calls external APIs)

Benefits:
- No external API calls during content generation
- Consistent data source (same 1m bars used for OHLC and intraday context)
- Cost control (Databento charges per GB, fetch once and reuse)
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional, List
from zoneinfo import ZoneInfo

from django.db.models import Min, Max, Sum, F
from django.db.models.functions import TruncDate

from apps.trading.infrastructure.models import IntradayBarModel
from apps.trading.domain.value_objects import Instrument

logger = logging.getLogger(__name__)

ET = ZoneInfo('America/New_York')
UTC = ZoneInfo('UTC')


@dataclass
class SessionData:
    """Daily session data computed from intraday bars.
    
    Compatible with the old SessionData from yfinance_client for
    seamless integration with existing pipeline code.
    """
    instrument: Instrument
    session_date: date
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    prior_close: Decimal | None = None


@dataclass
class OvernightData:
    """Overnight (Globex) session data computed from intraday bars."""
    instrument: Instrument
    session_date: date
    overnight_high: Decimal
    overnight_low: Decimal
    overnight_close: Decimal | None = None


class DataNotAvailableError(Exception):
    """Raised when required data is not available in the database."""
    def __init__(self, instrument: str, session_date: date, data_type: str = "session"):
        self.instrument = instrument
        self.session_date = session_date
        self.data_type = data_type
        super().__init__(
            f"No {data_type} data available for {instrument} on {session_date}. "
            f"Run 'python manage.py fetch_intraday_bars --date {session_date} "
            f"--instruments {instrument.replace('=F', '')}' first."
        )


class LocalMarketDataService:
    """Service that computes market data aggregates from stored intraday bars.
    
    This is the sole data source for the content generation pipeline.
    All session/weekly/monthly data is derived from IntradayBarModel.
    
    Implements the same interface as the old YFinanceClient for compatibility.
    """
    
    def has_data_for_session(
        self,
        instrument: Instrument,
        session_date: date,
        require_rth: bool = True,
    ) -> bool:
        """Check if we have sufficient data for a session.
        
        Args:
            instrument: The instrument to check
            session_date: The trading date
            require_rth: If True, require at least RTH data (not just overnight)
            
        Returns:
            True if data exists, False otherwise
        """
        query = IntradayBarModel.objects.filter(
            instrument=instrument.value,
            session_date=session_date,
        )
        
        if require_rth:
            query = query.filter(session_type='rth')
        
        return query.exists()
    
    def get_bar_count(self, instrument: Instrument, session_date: date) -> dict:
        """Get bar counts for a session (useful for debugging).
        
        Returns:
            Dict with 'rth' and 'overnight' bar counts
        """
        rth_count = IntradayBarModel.objects.filter(
            instrument=instrument.value,
            session_date=session_date,
            session_type='rth',
        ).count()
        
        overnight_count = IntradayBarModel.objects.filter(
            instrument=instrument.value,
            session_date=session_date,
            session_type='overnight',
        ).count()
        
        return {
            'rth': rth_count,
            'overnight': overnight_count,
            'total': rth_count + overnight_count,
        }
    
    def fetch_session_data(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> SessionData | None:
        """Compute RTH session OHLCV from stored 1-minute bars.
        
        Args:
            instrument: The futures instrument
            session_date: The trading date
            
        Returns:
            SessionData if data exists, None otherwise
        """
        # Get RTH bars for the session
        rth_bars = IntradayBarModel.objects.filter(
            instrument=instrument.value,
            session_date=session_date,
            session_type='rth',
        ).order_by('timestamp')
        
        if not rth_bars.exists():
            logger.warning(
                f"No RTH data for {instrument.value} on {session_date}. "
                f"Run fetch_intraday_bars first."
            )
            return None
        
        # Aggregate OHLCV
        first_bar = rth_bars.first()
        last_bar = rth_bars.last()
        
        # These are guaranteed non-None since exists() returned True
        assert first_bar is not None
        assert last_bar is not None
        
        aggregates = rth_bars.aggregate(
            high=Max('high_price'),
            low=Min('low_price'),
            total_volume=Sum('volume'),
        )
        
        # Get prior close (from previous session)
        prior_close = self._get_prior_close(instrument, session_date)
        
        return SessionData(
            instrument=instrument,
            session_date=session_date,
            open_price=first_bar.open_price,
            high_price=aggregates['high'],
            low_price=aggregates['low'],
            close_price=last_bar.close_price,
            volume=aggregates['total_volume'] or 0,
            prior_close=prior_close,
        )
    
    def fetch_overnight_data(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> OvernightData | None:
        """Compute overnight session high/low from stored bars.
        
        Args:
            instrument: The futures instrument
            session_date: The trading date (overnight leads into this date)
            
        Returns:
            OvernightData if data exists, None otherwise
        """
        overnight_bars = IntradayBarModel.objects.filter(
            instrument=instrument.value,
            session_date=session_date,
            session_type='overnight',
        ).order_by('timestamp')
        
        if not overnight_bars.exists():
            logger.debug(f"No overnight data for {instrument.value} on {session_date}")
            return None
        
        last_bar = overnight_bars.last()
        aggregates = overnight_bars.aggregate(
            high=Max('high_price'),
            low=Min('low_price'),
        )
        
        return OvernightData(
            instrument=instrument,
            session_date=session_date,
            overnight_high=aggregates['high'],
            overnight_low=aggregates['low'],
            overnight_close=last_bar.close_price if last_bar else None,
        )
    
    def fetch_weekly_data(
        self,
        instrument: Instrument,
        week_start_date: date,
    ) -> list[SessionData]:
        """Fetch all sessions for a week.
        
        Args:
            instrument: The futures instrument
            week_start_date: Monday of the week
            
        Returns:
            List of SessionData for each trading day in the week
        """
        sessions = []
        
        # Trading days are Monday through Friday
        for day_offset in range(5):
            session_date = week_start_date + timedelta(days=day_offset)
            session_data = self.fetch_session_data(instrument, session_date)
            
            if session_data:
                sessions.append(session_data)
        
        return sessions
    
    def fetch_monthly_high_low(
        self,
        instrument: Instrument,
        month_date: date,
    ) -> tuple[Decimal, Decimal] | None:
        """Compute monthly high and low from stored bars.
        
        Args:
            instrument: The futures instrument
            month_date: Any date in the target month
            
        Returns:
            Tuple of (high, low) if data exists, None otherwise
        """
        # Get first and last day of the month
        first_of_month = month_date.replace(day=1)
        
        if month_date.month == 12:
            last_of_month = date(month_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            last_of_month = date(month_date.year, month_date.month + 1, 1) - timedelta(days=1)
        
        # Only consider RTH bars for monthly extremes
        bars = IntradayBarModel.objects.filter(
            instrument=instrument.value,
            session_date__gte=first_of_month,
            session_date__lte=last_of_month,
            session_type='rth',
        )
        
        if not bars.exists():
            logger.warning(
                f"No data for {instrument.value} in month {month_date.year}-{month_date.month:02d}"
            )
            return None
        
        aggregates = bars.aggregate(
            high=Max('high_price'),
            low=Min('low_price'),
        )
        
        return (aggregates['high'], aggregates['low'])
    
    def _get_prior_close(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> Decimal | None:
        """Get the prior session's close price.
        
        Looks back up to 5 calendar days to find the previous trading session.
        """
        for days_back in range(1, 6):
            prior_date = session_date - timedelta(days=days_back)
            
            # Get last RTH bar from prior session
            last_bar = IntradayBarModel.objects.filter(
                instrument=instrument.value,
                session_date=prior_date,
                session_type='rth',
            ).order_by('-timestamp').first()
            
            if last_bar:
                return last_bar.close_price
        
        return None
    
    def get_missing_dates(
        self,
        instrument: Instrument,
        start_date: date,
        end_date: date,
    ) -> list[date]:
        """Find dates in range that have no data stored.
        
        Useful for backfill operations to avoid re-fetching existing data.
        
        Args:
            instrument: The instrument to check
            start_date: Start of range (inclusive)
            end_date: End of range (inclusive)
            
        Returns:
            List of dates with no stored bars
        """
        # Get all dates that have data
        stored_dates = set(
            IntradayBarModel.objects.filter(
                instrument=instrument.value,
                session_date__gte=start_date,
                session_date__lte=end_date,
            ).values_list('session_date', flat=True).distinct()
        )
        
        # Find missing weekdays (skip weekends)
        missing = []
        current = start_date
        while current <= end_date:
            if current.weekday() < 5 and current not in stored_dates:  # Mon-Fri
                missing.append(current)
            current += timedelta(days=1)
        
        return missing
    
    def validate_data_integrity(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> dict:
        """Check data integrity for a session.
        
        Returns:
            Dict with validation results
        """
        rth_bars = IntradayBarModel.objects.filter(
            instrument=instrument.value,
            session_date=session_date,
            session_type='rth',
        ).order_by('timestamp')
        
        if not rth_bars.exists():
            return {
                'valid': False,
                'error': 'No RTH data',
                'rth_bar_count': 0,
            }
        
        bar_count = rth_bars.count()
        first_bar = rth_bars.first()
        last_bar = rth_bars.last()
        
        # RTH should have approximately 390 1-minute bars (6.5 hours)
        # Allow some tolerance for holidays/early closes
        expected_min = 200  # Shortened session minimum
        expected_max = 400  # Normal session max
        
        issues = []
        
        if bar_count < expected_min:
            issues.append(f"Low bar count: {bar_count} (expected >= {expected_min})")
        elif bar_count > expected_max:
            issues.append(f"High bar count: {bar_count} (expected <= {expected_max})")
        
        # Check for gaps
        timestamps = list(rth_bars.values_list('timestamp', flat=True))
        gaps = []
        for i in range(1, len(timestamps)):
            diff = (timestamps[i] - timestamps[i-1]).total_seconds()
            if diff > 120:  # More than 2 minute gap
                gaps.append({
                    'from': timestamps[i-1].isoformat(),
                    'to': timestamps[i].isoformat(),
                    'gap_minutes': diff / 60,
                })
        
        if gaps:
            issues.append(f"Found {len(gaps)} gaps in data")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'rth_bar_count': bar_count,
            'first_bar': first_bar.timestamp.isoformat() if first_bar else None,
            'last_bar': last_bar.timestamp.isoformat() if last_bar else None,
            'gaps': gaps[:5],  # Limit to first 5 gaps
        }


def get_local_market_data_service() -> LocalMarketDataService:
    """Factory function for LocalMarketDataService.
    
    Returns:
        Configured LocalMarketDataService instance
    """
    return LocalMarketDataService()
