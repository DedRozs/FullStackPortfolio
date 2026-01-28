"""Trading-specific value objects."""
from dataclasses import dataclass, field, asdict
from enum import Enum
from decimal import Decimal
from typing import List, Dict, Any, Optional
from datetime import date
import re


# Mechanical disclaimer - rendered in template, not AI-generated
TRADING_DISCLAIMER = (
    "This analysis is for informational purposes only and does not constitute "
    "financial advice. Trading futures involves substantial risk of loss and is "
    "not suitable for all investors. Past performance is not indicative of future "
    "results. Always conduct your own research before trading."
)


class Instrument(Enum):
    """Futures instrument identifiers.
    
    Represents the index futures contracts covered by the trading blog.
    Each value contains the ticker symbol used by yfinance.
    """
    NQ = "NQ=F"   # E-mini Nasdaq-100 Futures
    ES = "ES=F"   # E-mini S&P 500 Futures
    RTY = "RTY=F"  # E-mini Russell 2000 Futures
    YM = "YM=F"   # E-mini Dow Jones Futures
    
    @property
    def display_name(self) -> str:
        """Human-readable instrument name."""
        names = {
            "NQ=F": "E-mini Nasdaq-100",
            "ES=F": "E-mini S&P 500",
            "RTY=F": "E-mini Russell 2000",
            "YM=F": "E-mini Dow Jones",
        }
        return names[self.value]
    
    @property
    def short_name(self) -> str:
        """Short name for URLs and display."""
        return self.name  # NQ, ES, RTY, YM
    
    @classmethod
    def from_short_name(cls, name: str) -> "Instrument":
        """Get instrument from short name (NQ, ES, RTY, YM)."""
        name_upper = name.upper()
        for instrument in cls:
            if instrument.name == name_upper:
                return instrument
        raise ValueError(f"Unknown instrument: {name}")


class PostType(Enum):
    """Type of trading blog post.
    
    Determines the content template and data requirements.
    """
    PRE_MARKET = "pre_market"      # Morning analysis with key levels
    POST_MARKET = "post_market"    # End of day recap
    WEEKLY_RECAP = "weekly_recap"  # Saturday weekly summary
    
    @property
    def display_name(self) -> str:
        """Human-readable post type name."""
        names = {
            "pre_market": "Pre-Market Analysis",
            "post_market": "Session Recap",
            "weekly_recap": "Weekly Recap",
        }
        return names[self.value]


class LevelType(Enum):
    """Type of price level for support/resistance analysis.
    
    Each level type represents a significant price point derived
    from prior sessions or calculated ranges.
    """
    PRIOR_HIGH = "prior_high"
    PRIOR_LOW = "prior_low"
    PRIOR_CLOSE = "prior_close"
    OVERNIGHT_HIGH = "overnight_high"
    OVERNIGHT_LOW = "overnight_low"
    WEEKLY_OPEN = "weekly_open"
    WEEKLY_HIGH = "weekly_high"
    WEEKLY_LOW = "weekly_low"
    MONTHLY_HIGH = "monthly_high"
    MONTHLY_LOW = "monthly_low"
    
    @property
    def display_name(self) -> str:
        """Human-readable level name."""
        return self.value.replace("_", " ").title()


@dataclass(frozen=True)
class Price:
    """Price value object with decimal precision.
    
    Ensures consistent handling of financial values.
    """
    value: Decimal
    
    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            # Convert to Decimal if needed, then validate
            object.__setattr__(self, 'value', Decimal(str(self.value)))
        if self.value < 0:
            raise ValueError("Price cannot be negative")
    
    def __str__(self) -> str:
        return f"{self.value:,.2f}"
    
    def __float__(self) -> float:
        return float(self.value)


@dataclass(frozen=True)
class TradingSlug:
    """URL-friendly slug for trading posts.
    
    Format: {instrument}-{post_type}-{date}
    Example: nq-pre-market-2026-01-28
    """
    value: str
    
    def __post_init__(self) -> None:
        if not self._is_valid_slug(self.value):
            raise ValueError(f"Invalid trading slug: {self.value}")
    
    @staticmethod
    def _is_valid_slug(slug: str) -> bool:
        """Slug must be lowercase alphanumeric with hyphens."""
        pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
        return bool(re.match(pattern, slug)) and len(slug) <= 200
    
    @classmethod
    def create(
        cls,
        instrument: "Instrument",
        post_type: "PostType",
        date_str: str,
    ) -> "TradingSlug":
        """Generate a slug from components.
        
        Args:
            instrument: The futures instrument
            post_type: Type of post (pre_market, post_market, weekly_recap)
            date_str: Date string in YYYY-MM-DD format
        """
        slug_parts = [
            instrument.short_name.lower(),
            post_type.value.replace("_", "-"),
            date_str,
        ]
        return cls("-".join(slug_parts))
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PercentageChange:
    """Percentage change value object.
    
    Represents price changes as percentages with consistent formatting.
    """
    value: Decimal
    
    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, 'value', Decimal(str(self.value)))
    
    @property
    def is_positive(self) -> bool:
        """Check if change is positive."""
        return self.value > 0
    
    @property
    def is_negative(self) -> bool:
        """Check if change is negative."""
        return self.value < 0
    
    @property
    def direction(self) -> str:
        """Get direction indicator."""
        if self.value > 0:
            return "up"
        elif self.value < 0:
            return "down"
        return "flat"
    
    def __str__(self) -> str:
        sign = "+" if self.value > 0 else ""
        return f"{sign}{self.value:.2f}%"


@dataclass(frozen=True)
class SessionRange:
    """Trading session range value object.
    
    Represents the high-low range for a trading session.
    """
    high: Price
    low: Price
    
    def __post_init__(self) -> None:
        if self.high.value < self.low.value:
            raise ValueError("Session high must be >= low")
    
    @property
    def range_points(self) -> Decimal:
        """Calculate range in points."""
        return self.high.value - self.low.value
    
    @property
    def midpoint(self) -> Price:
        """Calculate session midpoint."""
        mid = (self.high.value + self.low.value) / 2
        return Price(mid)
    
    def __str__(self) -> str:
        return f"Range: {self.low} - {self.high} ({self.range_points:.2f} pts)"


# =============================================================================
# Structured Data Schemas for JSON Storage
# =============================================================================
# These dataclasses define the JSON structure stored in TradingPostModel.structured_data
# Enables: weekly recaps pulling from daily data, frontend rendering, regeneration consistency


@dataclass
class SessionOHLC:
    """OHLC data for a single session - JSON serializable."""
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    
    @property
    def range_points(self) -> float:
        return self.high - self.low
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "range": round(self.range_points, 2),
        }


@dataclass
class DailySessionData:
    """Daily session data for structured storage."""
    date: str  # ISO format YYYY-MM-DD
    day_name: str  # Monday, Tuesday, etc.
    ohlc: SessionOHLC
    change_points: Optional[float] = None
    change_percent: Optional[float] = None
    prior_close: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "day_name": self.day_name,
            "ohlc": self.ohlc.to_dict(),
            "change_points": self.change_points,
            "change_percent": self.change_percent,
            "prior_close": self.prior_close,
        }


@dataclass
class PriceLevelData:
    """Price level for structured storage."""
    level_type: str  # e.g., "prior_high", "weekly_open"
    price: float
    label: str  # Human-readable label
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level_type": self.level_type,
            "price": self.price,
            "label": self.label,
        }


@dataclass
class PostMarketStructuredData:
    """Structured data schema for post-market recap posts."""
    schema_version: str = "1.0"
    post_type: str = "post_market"
    
    # Core session data
    instrument: str = ""
    session_date: str = ""
    session: Optional[Dict[str, Any]] = None  # DailySessionData.to_dict()
    
    # Price levels used in analysis
    levels: List[Dict[str, Any]] = field(default_factory=list)
    
    # Weekly/monthly context
    weekly_high: Optional[float] = None
    weekly_low: Optional[float] = None
    monthly_high: Optional[float] = None
    monthly_low: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "post_type": self.post_type,
            "instrument": self.instrument,
            "session_date": self.session_date,
            "session": self.session,
            "levels": self.levels,
            "weekly_high": self.weekly_high,
            "weekly_low": self.weekly_low,
            "monthly_high": self.monthly_high,
            "monthly_low": self.monthly_low,
        }


@dataclass
class PreMarketStructuredData:
    """Structured data schema for pre-market analysis posts."""
    schema_version: str = "1.0"
    post_type: str = "pre_market"
    
    # Core data
    instrument: str = ""
    session_date: str = ""
    
    # Prior session
    prior_session: Optional[Dict[str, Any]] = None  # DailySessionData.to_dict()
    
    # Overnight data
    overnight_high: Optional[float] = None
    overnight_low: Optional[float] = None
    
    # Price levels
    levels: List[Dict[str, Any]] = field(default_factory=list)
    
    # Context
    weekly_open: Optional[float] = None
    weekly_high: Optional[float] = None
    weekly_low: Optional[float] = None
    monthly_high: Optional[float] = None
    monthly_low: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "post_type": self.post_type,
            "instrument": self.instrument,
            "session_date": self.session_date,
            "prior_session": self.prior_session,
            "overnight_high": self.overnight_high,
            "overnight_low": self.overnight_low,
            "levels": self.levels,
            "weekly_open": self.weekly_open,
            "weekly_high": self.weekly_high,
            "weekly_low": self.weekly_low,
            "monthly_high": self.monthly_high,
            "monthly_low": self.monthly_low,
        }


@dataclass
class WeeklyRecapStructuredData:
    """Structured data schema for weekly recap posts."""
    schema_version: str = "1.0"
    post_type: str = "weekly_recap"
    
    # Core data
    instrument: str = ""
    week_start_date: str = ""
    week_end_date: str = ""
    
    # Weekly OHLC
    weekly_ohlc: Optional[Dict[str, Any]] = None
    change_points: Optional[float] = None
    change_percent: Optional[float] = None
    
    # Daily breakdown - list of DailySessionData.to_dict()
    daily_sessions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Key levels
    levels: List[Dict[str, Any]] = field(default_factory=list)
    
    # Monthly context
    monthly_high: Optional[float] = None
    monthly_low: Optional[float] = None
    prior_week_close: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "post_type": self.post_type,
            "instrument": self.instrument,
            "week_start_date": self.week_start_date,
            "week_end_date": self.week_end_date,
            "weekly_ohlc": self.weekly_ohlc,
            "change_points": self.change_points,
            "change_percent": self.change_percent,
            "daily_sessions": self.daily_sessions,
            "levels": self.levels,
            "monthly_high": self.monthly_high,
            "monthly_low": self.monthly_low,
            "prior_week_close": self.prior_week_close,
        }
