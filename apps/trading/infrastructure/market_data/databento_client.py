"""Databento market data client for fetching intraday bars.

This client fetches 1-minute OHLCV bars from Databento's historical API
for CME futures (ES, NQ, RTY). Data is stored locally to minimize API costs.

Databento dataset: GLBX.MDP3 (CME Globex MDP 3.0)
Schema: ohlcv-1m (1-minute bars)
"""
import os
import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# CME futures symbols on Databento use continuous contract symbology
DATABENTO_SYMBOLS = {
    'ES=F': 'ES.FUT',  # E-mini S&P 500 front month
    'NQ=F': 'NQ.FUT',  # E-mini Nasdaq-100 front month
    'RTY=F': 'RTY.FUT',  # E-mini Russell 2000 front month
    'YM=F': 'YM.FUT',  # E-mini Dow Jones front month
}

# Reverse mapping for storing data
YFINANCE_SYMBOLS = {v: k for k, v in DATABENTO_SYMBOLS.items()}

# Timezone constants
ET = ZoneInfo('America/New_York')
UTC = ZoneInfo('UTC')


@dataclass
class IntradayBar:
    """Represents a single 1-minute OHLCV bar."""
    timestamp: datetime  # Bar start time in UTC
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    session_type: str  # 'overnight' or 'rth'
    session_date: date  # Trading date this bar belongs to


class DatabentoClient:
    """Client for fetching intraday bar data from Databento.
    
    Uses the GLBX.MDP3 dataset for CME futures with ohlcv-1m schema.
    Designed to be called once daily to fetch previous day's data.
    """
    
    DATASET = 'GLBX.MDP3'
    SCHEMA = 'ohlcv-1m'
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Databento client.
        
        Args:
            api_key: Databento API key. If not provided, reads from
                     DATABENTO_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv('DATABENTO_API_KEY')
        if not self.api_key:
            logger.warning(
                "No Databento API key found. Set DATABENTO_API_KEY environment "
                "variable or pass api_key to constructor."
            )
        self._client = None
    
    @property
    def client(self):
        """Lazy-load the Databento client."""
        if self._client is None:
            try:
                import databento as db
                self._client = db.Historical(self.api_key)
            except ImportError:
                raise ImportError(
                    "databento package not installed. "
                    "Run: pip install databento"
                )
        return self._client
    
    def fetch_session_bars(
        self,
        instrument: str,
        session_date: date,
        include_overnight: bool = True,
    ) -> list[IntradayBar]:
        """Fetch 1-minute bars for a trading session.
        
        Args:
            instrument: Yahoo Finance style symbol (e.g., 'ES=F')
            session_date: The trading date to fetch
            include_overnight: If True, include overnight session (6PM prior day to 9:30AM)
        
        Returns:
            List of IntradayBar objects sorted by timestamp
        """
        if not self.api_key:
            logger.error("Cannot fetch data: No Databento API key configured")
            return []
        
        databento_symbol = DATABENTO_SYMBOLS.get(instrument)
        if not databento_symbol:
            logger.error(f"Unknown instrument: {instrument}")
            return []
        
        # Calculate time range in ET then convert to UTC
        # CME Equity Index Futures Schedule:
        # - Overnight: 6:00 PM prior day - 9:30 AM current day
        # - RTH + Extended: 9:30 AM - 5:00 PM (before 1-hour maintenance break)
        # - Maintenance: 5:00 PM - 6:00 PM (no trading)
        
        rth_start = datetime.combine(session_date, time(9, 30), tzinfo=ET)
        rth_end = datetime.combine(session_date, time(17, 0), tzinfo=ET)  # 5:00 PM
        
        if include_overnight:
            # Overnight session starts 6PM the prior calendar day
            prior_day = session_date - timedelta(days=1)
            start_time = datetime.combine(prior_day, time(18, 0), tzinfo=ET)
        else:
            start_time = rth_start
        
        end_time = rth_end
        
        # Convert to UTC for API call
        start_utc = start_time.astimezone(UTC)
        end_utc = end_time.astimezone(UTC)
        
        logger.info(
            f"Fetching {instrument} bars from {start_utc} to {end_utc}"
        )
        
        try:
            data = self.client.timeseries.get_range(
                dataset=self.DATASET,
                symbols=[databento_symbol],
                schema=self.SCHEMA,
                stype_in='parent',  # Use continuous contract symbology
                start=start_utc.isoformat(),
                end=end_utc.isoformat(),
            )
            
            # Convert to DataFrame for easier processing
            df = data.to_df()
            
            if df.empty:
                logger.warning(f"No data returned for {instrument} on {session_date}")
                return []
            
            bars = []
            rth_start_utc = rth_start.astimezone(UTC)
            
            for idx, row in df.iterrows():
                # idx is the ts_recv timestamp (pandas Timestamp)
                bar_time = idx.to_pydatetime()
                if bar_time.tzinfo is None:
                    bar_time = bar_time.replace(tzinfo=UTC)
                
                # Determine session type
                if bar_time < rth_start_utc:
                    session_type = 'overnight'
                else:
                    session_type = 'rth'
                
                bar = IntradayBar(
                    timestamp=bar_time,
                    open_price=Decimal(str(row['open'])),
                    high_price=Decimal(str(row['high'])),
                    low_price=Decimal(str(row['low'])),
                    close_price=Decimal(str(row['close'])),
                    volume=int(row['volume']),
                    session_type=session_type,
                    session_date=session_date,
                )
                bars.append(bar)
            
            logger.info(f"Fetched {len(bars)} bars for {instrument} on {session_date}")
            return bars
            
        except Exception as e:
            logger.exception(f"Error fetching Databento data: {e}")
            return []
    
    def estimate_cost(
        self,
        instrument: str,
        session_date: date,
        include_overnight: bool = True,
    ) -> Optional[float]:
        """Estimate cost in USD for fetching a session's data.
        
        Args:
            instrument: Yahoo Finance style symbol (e.g., 'ES=F')
            session_date: The trading date to fetch
            include_overnight: If True, include overnight session
        
        Returns:
            Estimated cost in USD, or None if unable to estimate
        """
        if not self.api_key:
            return None
        
        databento_symbol = DATABENTO_SYMBOLS.get(instrument)
        if not databento_symbol:
            return None
        
        # Same time range calculation as fetch
        rth_start = datetime.combine(session_date, time(9, 30), tzinfo=ET)
        rth_end = datetime.combine(session_date, time(16, 0), tzinfo=ET)
        
        if include_overnight:
            prior_day = session_date - timedelta(days=1)
            start_time = datetime.combine(prior_day, time(18, 0), tzinfo=ET)
        else:
            start_time = rth_start
        
        start_utc = start_time.astimezone(UTC)
        end_utc = rth_end.astimezone(UTC)
        
        try:
            cost = self.client.metadata.get_cost(
                dataset=self.DATASET,
                symbols=[databento_symbol],
                schema=self.SCHEMA,
                stype_in='parent',
                start=start_utc.isoformat(),
                end=end_utc.isoformat(),
            )
            return cost
        except Exception as e:
            logger.warning(f"Could not estimate cost: {e}")
            return None
    
    def has_data_for_date(self, session_date: date) -> bool:
        """Check if Databento has data available for a given date.
        
        Args:
            session_date: The trading date to check
        
        Returns:
            True if data is available, False otherwise
        """
        if not self.api_key:
            return False
        
        try:
            conditions = self.client.metadata.get_dataset_condition(
                dataset=self.DATASET,
                start_date=session_date.isoformat(),
                end_date=session_date.isoformat(),
            )
            
            for condition in conditions:
                if condition.get('condition') == 'available':
                    return True
            
            return False
        except Exception as e:
            logger.warning(f"Could not check data availability: {e}")
            return False
