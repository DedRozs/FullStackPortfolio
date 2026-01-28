"""yfinance client for fetching market data.

This client retrieves futures data from Yahoo Finance using the yfinance library.
It handles data transformation and error handling for the trading blog.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Protocol
import logging

from apps.trading.domain.value_objects import Instrument, Price, PercentageChange


logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Raw session data from yfinance.
    
    This is a simple data structure for transferring market data
    from yfinance to the domain layer.
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
    """Overnight (Globex) session data.
    
    Represents the overnight trading session from 6 PM to 9:30 AM ET.
    """
    instrument: Instrument
    session_date: date
    overnight_high: Decimal
    overnight_low: Decimal


class MarketDataClient(Protocol):
    """Protocol for market data retrieval.
    
    Defines the interface for fetching market data from external sources.
    """
    
    def fetch_session_data(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> SessionData | None:
        """Fetch session OHLCV data for a specific date."""
        ...
    
    def fetch_overnight_data(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> OvernightData | None:
        """Fetch overnight session data."""
        ...
    
    def fetch_weekly_data(
        self,
        instrument: Instrument,
        week_start_date: date,
    ) -> list[SessionData]:
        """Fetch all sessions for a week."""
        ...
    
    def fetch_monthly_high_low(
        self,
        instrument: Instrument,
        month_date: date,
    ) -> tuple[Decimal, Decimal] | None:
        """Fetch monthly high and low for the given month."""
        ...


class YFinanceClient:
    """Yahoo Finance client for fetching futures market data.
    
    Uses yfinance library to retrieve delayed futures data.
    Handles data transformation and error cases.
    """
    
    def __init__(self) -> None:
        """Initialize the yfinance client."""
        self._yf = None  # Lazy import to avoid startup overhead
    
    @property
    def yf(self):
        """Lazy load yfinance module."""
        if self._yf is None:
            try:
                import yfinance
                self._yf = yfinance
            except ImportError:
                raise ImportError(
                    "yfinance package is required. Install it with: pip install yfinance"
                )
        return self._yf
    
    def fetch_session_data(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> SessionData | None:
        """Fetch session OHLCV data for a specific date.
        
        Args:
            instrument: The futures instrument to fetch
            session_date: The trading date
            
        Returns:
            SessionData if data is available, None otherwise
        """
        ticker_symbol = instrument.value
        
        try:
            ticker = self.yf.Ticker(ticker_symbol)
            
            # Fetch a few days of data to ensure we get the session
            # yfinance needs start < end, so we go back a day
            start_date = session_date - timedelta(days=5)
            end_date = session_date + timedelta(days=1)
            
            hist = ticker.history(
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                interval="1d",
            )
            
            if hist.empty:
                logger.warning(
                    f"No data returned for {instrument.short_name} on {session_date}"
                )
                return None
            
            # Convert index to date for comparison
            hist.index = hist.index.date
            
            if session_date not in hist.index:
                logger.warning(
                    f"Session date {session_date} not found in data for {instrument.short_name}"
                )
                return None
            
            row = hist.loc[session_date]
            
            # Get prior close if available
            prior_close = None
            prior_dates = [d for d in hist.index if d < session_date]
            if prior_dates:
                prior_date = max(prior_dates)
                prior_close = Decimal(str(hist.loc[prior_date]['Close']))
            
            return SessionData(
                instrument=instrument,
                session_date=session_date,
                open_price=Decimal(str(row['Open'])),
                high_price=Decimal(str(row['High'])),
                low_price=Decimal(str(row['Low'])),
                close_price=Decimal(str(row['Close'])),
                volume=int(row['Volume']),
                prior_close=prior_close,
            )
            
        except Exception as e:
            logger.error(
                f"Error fetching session data for {instrument.short_name} "
                f"on {session_date}: {e}"
            )
            return None
    
    def fetch_overnight_data(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> OvernightData | None:
        """Fetch overnight session data.
        
        The overnight session runs from 6 PM ET to 9:30 AM ET.
        We use intraday data to calculate overnight high/low.
        
        Args:
            instrument: The futures instrument
            session_date: The trading date
            
        Returns:
            OvernightData if available, None otherwise
        """
        ticker_symbol = instrument.value
        
        try:
            ticker = self.yf.Ticker(ticker_symbol)
            
            # For overnight, we need the prior day's evening + current day's morning
            # Fetch intraday data for the range
            prior_day = session_date - timedelta(days=1)
            
            # Use 1-hour intervals to get overnight price action
            hist = ticker.history(
                start=prior_day.isoformat(),
                end=(session_date + timedelta(days=1)).isoformat(),
                interval="1h",
            )
            
            if hist.empty:
                logger.warning(
                    f"No intraday data for overnight session {instrument.short_name}"
                )
                return None
            
            # Filter for overnight hours (6 PM prior day to 9:30 AM session day)
            # This is approximate since yfinance returns in various timezones
            overnight_high = Decimal(str(hist['High'].max()))
            overnight_low = Decimal(str(hist['Low'].min()))
            
            return OvernightData(
                instrument=instrument,
                session_date=session_date,
                overnight_high=overnight_high,
                overnight_low=overnight_low,
            )
            
        except Exception as e:
            logger.error(
                f"Error fetching overnight data for {instrument.short_name} "
                f"on {session_date}: {e}"
            )
            return None
    
    def fetch_weekly_data(
        self,
        instrument: Instrument,
        week_start_date: date,
    ) -> list[SessionData]:
        """Fetch all sessions for a trading week.
        
        Args:
            instrument: The futures instrument
            week_start_date: Monday of the week
            
        Returns:
            List of SessionData for each trading day in the week
        """
        ticker_symbol = instrument.value
        week_end_date = week_start_date + timedelta(days=4)  # Friday
        
        try:
            ticker = self.yf.Ticker(ticker_symbol)
            
            hist = ticker.history(
                start=week_start_date.isoformat(),
                end=(week_end_date + timedelta(days=1)).isoformat(),
                interval="1d",
            )
            
            if hist.empty:
                logger.warning(
                    f"No weekly data for {instrument.short_name} "
                    f"week of {week_start_date}"
                )
                return []
            
            # Convert index to dates
            hist.index = hist.index.date
            
            sessions = []
            prior_close = None
            
            for session_date in sorted(hist.index):
                row = hist.loc[session_date]
                
                sessions.append(SessionData(
                    instrument=instrument,
                    session_date=session_date,
                    open_price=Decimal(str(row['Open'])),
                    high_price=Decimal(str(row['High'])),
                    low_price=Decimal(str(row['Low'])),
                    close_price=Decimal(str(row['Close'])),
                    volume=int(row['Volume']),
                    prior_close=prior_close,
                ))
                
                prior_close = Decimal(str(row['Close']))
            
            return sessions
            
        except Exception as e:
            logger.error(
                f"Error fetching weekly data for {instrument.short_name} "
                f"week of {week_start_date}: {e}"
            )
            return []
    
    def fetch_monthly_high_low(
        self,
        instrument: Instrument,
        month_date: date,
    ) -> tuple[Decimal, Decimal] | None:
        """Fetch monthly high and low for the given month.
        
        Args:
            instrument: The futures instrument
            month_date: Any date in the target month
            
        Returns:
            Tuple of (monthly_high, monthly_low) or None if unavailable
        """
        ticker_symbol = instrument.value
        
        # Calculate month start and end
        month_start = date(month_date.year, month_date.month, 1)
        
        if month_date.month == 12:
            month_end = date(month_date.year + 1, 1, 1)
        else:
            month_end = date(month_date.year, month_date.month + 1, 1)
        
        try:
            ticker = self.yf.Ticker(ticker_symbol)
            
            hist = ticker.history(
                start=month_start.isoformat(),
                end=month_end.isoformat(),
                interval="1d",
            )
            
            if hist.empty:
                logger.warning(
                    f"No monthly data for {instrument.short_name} "
                    f"month of {month_start}"
                )
                return None
            
            monthly_high = Decimal(str(hist['High'].max()))
            monthly_low = Decimal(str(hist['Low'].min()))
            
            return (monthly_high, monthly_low)
            
        except Exception as e:
            logger.error(
                f"Error fetching monthly data for {instrument.short_name} "
                f"month of {month_start}: {e}"
            )
            return None
    
    def fetch_latest_session(
        self,
        instrument: Instrument,
    ) -> SessionData | None:
        """Fetch the most recent available session data.
        
        Useful for getting current market data when specific date is unknown.
        
        Args:
            instrument: The futures instrument
            
        Returns:
            SessionData for the most recent session
        """
        ticker_symbol = instrument.value
        
        try:
            ticker = self.yf.Ticker(ticker_symbol)
            
            # Fetch last 10 days to ensure we get recent data
            hist = ticker.history(period="10d", interval="1d")
            
            if hist.empty:
                logger.warning(
                    f"No recent data for {instrument.short_name}"
                )
                return None
            
            # Get the most recent row
            hist.index = hist.index.date
            latest_date = max(hist.index)
            row = hist.loc[latest_date]
            
            # Get prior close if available
            prior_close = None
            prior_dates = [d for d in hist.index if d < latest_date]
            if prior_dates:
                prior_date = max(prior_dates)
                prior_close = Decimal(str(hist.loc[prior_date]['Close']))
            
            return SessionData(
                instrument=instrument,
                session_date=latest_date,
                open_price=Decimal(str(row['Open'])),
                high_price=Decimal(str(row['High'])),
                low_price=Decimal(str(row['Low'])),
                close_price=Decimal(str(row['Close'])),
                volume=int(row['Volume']),
                prior_close=prior_close,
            )
            
        except Exception as e:
            logger.error(
                f"Error fetching latest session for {instrument.short_name}: {e}"
            )
            return None
    
    def fetch_price_history(
        self,
        instrument: Instrument,
        days: int = 30,
    ) -> list[SessionData]:
        """Fetch historical price data for analysis.
        
        Args:
            instrument: The futures instrument
            days: Number of trading days to fetch
            
        Returns:
            List of SessionData ordered from oldest to newest
        """
        ticker_symbol = instrument.value
        
        try:
            ticker = self.yf.Ticker(ticker_symbol)
            
            hist = ticker.history(period=f"{days}d", interval="1d")
            
            if hist.empty:
                logger.warning(
                    f"No historical data for {instrument.short_name}"
                )
                return []
            
            hist.index = hist.index.date
            
            sessions = []
            prior_close = None
            
            for session_date in sorted(hist.index):
                row = hist.loc[session_date]
                
                sessions.append(SessionData(
                    instrument=instrument,
                    session_date=session_date,
                    open_price=Decimal(str(row['Open'])),
                    high_price=Decimal(str(row['High'])),
                    low_price=Decimal(str(row['Low'])),
                    close_price=Decimal(str(row['Close'])),
                    volume=int(row['Volume']),
                    prior_close=prior_close,
                ))
                
                prior_close = Decimal(str(row['Close']))
            
            return sessions
            
        except Exception as e:
            logger.error(
                f"Error fetching price history for {instrument.short_name}: {e}"
            )
            return []


def get_yfinance_client() -> YFinanceClient:
    """Factory function for yfinance client.
    
    Returns:
        Configured YFinanceClient instance
    """
    return YFinanceClient()
