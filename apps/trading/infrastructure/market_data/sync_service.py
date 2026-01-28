"""Market data synchronization service.

This service ensures intraday bar data is available before content generation.
It automatically fetches from Databento when local data is missing.

Key Design Principle: Fetch on-demand, not on a schedule
- Data is fetched immediately before each content generation
- Only missing data is fetched (cost efficient)
- Eliminates "stale data" risk from scheduled imports

Usage:
    sync_service = MarketDataSyncService()
    
    # Ensure data is ready for post-market recap
    sync_service.ensure_session_data(Instrument.ES, date(2026, 1, 27))
    
    # Then generate content (data is guaranteed fresh)
    pipeline.generate_postmarket_posts(...)
"""
import logging
from datetime import date, timedelta
from typing import List, Optional

from django.db import transaction

from apps.trading.infrastructure.market_data.databento_client import DatabentoClient
from apps.trading.infrastructure.models import IntradayBarModel
from apps.trading.domain.value_objects import Instrument
from apps.trading.domain.tick_validation import create_tick_validator

logger = logging.getLogger(__name__)


class DataFetchError(Exception):
    """Raised when data cannot be fetched from Databento."""
    pass


class MarketDataSyncService:
    """Service that ensures market data is available, fetching if needed.
    
    This service bridges the gap between "data exists locally" and 
    "we need to fetch from Databento". It's called by the pipeline
    before generating any content.
    
    Cost Control:
    - Only fetches if local data is missing
    - Tracks what's been fetched this session to avoid duplicate checks
    - Logs all fetch operations for cost auditing
    """
    
    def __init__(self, databento_client: Optional[DatabentoClient] = None):
        """Initialize the sync service.
        
        Args:
            databento_client: Optional Databento client. Created if not provided.
        """
        self._databento = databento_client or DatabentoClient()
        self._fetched_this_session: set[tuple[str, date]] = set()
    
    def has_local_data(
        self,
        instrument: Instrument,
        session_date: date,
        require_rth: bool = True,
    ) -> bool:
        """Check if we have local data for a session.
        
        Args:
            instrument: The futures instrument
            session_date: The trading date
            require_rth: If True, require RTH data (not just overnight)
            
        Returns:
            True if sufficient data exists locally
        """
        query = IntradayBarModel.objects.filter(
            instrument=instrument.value,
            session_date=session_date,
        )
        
        if require_rth:
            query = query.filter(session_type='rth')
        
        # Require minimum bar count to consider data complete
        # RTH is 6.5 hours = 390 minutes, allow for some tolerance
        MIN_RTH_BARS = 200  # ~3.3 hours minimum
        
        return query.count() >= MIN_RTH_BARS
    
    def ensure_session_data(
        self,
        instrument: Instrument,
        session_date: date,
        include_overnight: bool = True,
    ) -> bool:
        """Ensure data is available for a session, fetching if needed.
        
        This is the main entry point. Call this before any content generation.
        
        Args:
            instrument: The futures instrument
            session_date: The trading date needed
            include_overnight: Whether overnight data is also needed
            
        Returns:
            True if data is now available, False if fetch failed
            
        Raises:
            DataFetchError: If Databento API is not configured
        """
        key = (instrument.value, session_date)
        
        # Already fetched this session? Skip re-check
        if key in self._fetched_this_session:
            logger.debug(f"Already fetched {instrument.value} {session_date} this session")
            return True
        
        # Check local data
        if self.has_local_data(instrument, session_date, require_rth=True):
            logger.debug(f"Local data exists for {instrument.value} {session_date}")
            self._fetched_this_session.add(key)
            return True
        
        # Need to fetch from Databento
        logger.info(f"Fetching {instrument.value} {session_date} from Databento...")
        
        if not self._databento.api_key:
            raise DataFetchError(
                f"Cannot fetch data: DATABENTO_API_KEY not configured. "
                f"Set the environment variable or fetch data manually with: "
                f"python manage.py fetch_intraday_bars --date {session_date} "
                f"--instruments {instrument.value.replace('=F', '')}"
            )
        
        success = self._fetch_and_store(instrument, session_date, include_overnight)
        
        if success:
            self._fetched_this_session.add(key)
        
        return success
    
    def ensure_week_data(
        self,
        instrument: Instrument,
        week_start: date,
    ) -> bool:
        """Ensure data is available for an entire week (for weekly recap).
        
        Args:
            instrument: The futures instrument
            week_start: Monday of the week
            
        Returns:
            True if all weekday data is available
        """
        all_success = True
        
        for day_offset in range(5):  # Mon-Fri
            session_date = week_start + timedelta(days=day_offset)
            
            # Skip if weekend (shouldn't happen with Mon-Fri range)
            if session_date.weekday() >= 5:
                continue
            
            # Skip future dates
            if session_date > date.today():
                continue
            
            if not self.ensure_session_data(instrument, session_date):
                logger.warning(f"Failed to ensure data for {instrument.value} {session_date}")
                all_success = False
        
        return all_success
    
    def ensure_prior_session(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> bool:
        """Ensure prior trading session data is available (for pre-market).
        
        Args:
            instrument: The futures instrument
            session_date: The current trading date (we need prior day's data)
            
        Returns:
            True if prior session data is available
        """
        prior_date = self._get_prior_trading_day(session_date)
        return self.ensure_session_data(instrument, prior_date)
    
    def _fetch_and_store(
        self,
        instrument: Instrument,
        session_date: date,
        include_overnight: bool,
    ) -> bool:
        """Fetch from Databento and store locally.
        
        Includes tick validation to filter erroneous bars before storage.
        See apps.trading.domain.tick_validation for filtering logic.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            bars = self._databento.fetch_session_bars(
                instrument=instrument.value,
                session_date=session_date,
                include_overnight=include_overnight,
            )
            
            if not bars:
                logger.warning(f"No data returned from Databento for {instrument.value} {session_date}")
                return False
            
            # Filter erroneous ticks before storing
            # Uses dynamic reference from existing DB data (if any)
            validator = create_tick_validator(instrument.value, use_db_reference=True)
            original_count = len(bars)
            bars = validator.filter_bars(bars, session_date=session_date, log_filtered=True)
            
            if len(bars) < original_count:
                logger.info(
                    f"Tick validation removed {original_count - len(bars)} erroneous bars "
                    f"for {instrument.value} {session_date}"
                )
            
            if not bars:
                logger.warning(
                    f"All bars filtered as erroneous for {instrument.value} {session_date}"
                )
                return False
            
            # Convert to model instances
            bar_models = [
                IntradayBarModel(
                    instrument=instrument.value,
                    timestamp=bar.timestamp,
                    open_price=bar.open_price,
                    high_price=bar.high_price,
                    low_price=bar.low_price,
                    close_price=bar.close_price,
                    volume=bar.volume,
                    session_date=bar.session_date,
                    session_type=bar.session_type,
                )
                for bar in bars
            ]
            
            # Store with conflict handling
            with transaction.atomic():
                IntradayBarModel.objects.bulk_create(
                    bar_models,
                    ignore_conflicts=True,
                )
            
            logger.info(f"Stored {len(bars)} bars for {instrument.value} {session_date}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to fetch/store data: {e}")
            return False
    
    def _get_prior_trading_day(self, session_date: date) -> date:
        """Get the prior trading day (skipping weekends)."""
        prior = session_date - timedelta(days=1)
        
        # Skip Sunday
        if prior.weekday() == 6:
            prior = prior - timedelta(days=2)
        # Skip Saturday
        elif prior.weekday() == 5:
            prior = prior - timedelta(days=1)
        
        return prior
    
    def get_fetch_summary(self) -> dict:
        """Get summary of what was fetched this session.
        
        Returns:
            Dict with fetch statistics for logging/auditing
        """
        return {
            'sessions_fetched': len(self._fetched_this_session),
            'instruments_dates': [
                {'instrument': inst, 'date': dt.isoformat()}
                for inst, dt in sorted(self._fetched_this_session)
            ],
        }


def get_market_data_sync_service() -> MarketDataSyncService:
    """Factory function for MarketDataSyncService."""
    return MarketDataSyncService()
