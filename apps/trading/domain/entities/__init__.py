"""Trading domain entities."""
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Dict
from uuid import UUID, uuid4

from django.utils import timezone

from apps.trading.domain.value_objects import (
    Instrument,
    PostType,
    LevelType,
    Price,
    TradingSlug,
    PercentageChange,
    SessionRange,
)


class TradingPostStatus(Enum):
    """Publication status of a trading post."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class PriceLevel:
    """Individual price level entity.
    
    Represents a specific support/resistance level with its type and value.
    """
    id: UUID
    level_type: LevelType
    price: Price
    session_date: date
    instrument: Instrument
    created_at: datetime
    
    def __init__(
        self,
        level_type: LevelType,
        price: Price,
        session_date: date,
        instrument: Instrument,
        id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id or uuid4()
        self.level_type = level_type
        self.price = price
        self.session_date = session_date
        self.instrument = instrument
        self.created_at = created_at or timezone.now()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PriceLevel):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class MarketSession:
    """Market session entity.
    
    Represents one trading day's data for a single instrument.
    Contains OHLC data and calculated levels.
    """
    id: UUID
    instrument: Instrument
    session_date: date
    
    # Session OHLC
    open_price: Price
    high_price: Price
    low_price: Price
    close_price: Price
    
    # Overnight session (Globex)
    overnight_high: Price | None
    overnight_low: Price | None
    
    # Volume data
    volume: int
    
    # Prior session reference
    prior_close: Price | None
    
    # Calculated metrics
    change_points: Decimal | None
    change_percent: PercentageChange | None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    def __init__(
        self,
        instrument: Instrument,
        session_date: date,
        open_price: Price,
        high_price: Price,
        low_price: Price,
        close_price: Price,
        volume: int = 0,
        overnight_high: Price | None = None,
        overnight_low: Price | None = None,
        prior_close: Price | None = None,
        id: UUID | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.id = id or uuid4()
        self.instrument = instrument
        self.session_date = session_date
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.overnight_high = overnight_high
        self.overnight_low = overnight_low
        self.prior_close = prior_close
        self.created_at = created_at or timezone.now()
        self.updated_at = updated_at or timezone.now()
        
        # Calculate change metrics
        self._calculate_change()
    
    def _calculate_change(self) -> None:
        """Calculate change from prior close."""
        if self.prior_close:
            self.change_points = self.close_price.value - self.prior_close.value
            pct = (self.change_points / self.prior_close.value) * 100
            self.change_percent = PercentageChange(pct)
        else:
            self.change_points = None
            self.change_percent = None
    
    @property
    def session_range(self) -> SessionRange:
        """Get the session's high-low range."""
        return SessionRange(high=self.high_price, low=self.low_price)
    
    def get_price_levels(self) -> List[PriceLevel]:
        """Generate price level entities from session data."""
        levels = [
            PriceLevel(
                level_type=LevelType.PRIOR_HIGH,
                price=self.high_price,
                session_date=self.session_date,
                instrument=self.instrument,
            ),
            PriceLevel(
                level_type=LevelType.PRIOR_LOW,
                price=self.low_price,
                session_date=self.session_date,
                instrument=self.instrument,
            ),
            PriceLevel(
                level_type=LevelType.PRIOR_CLOSE,
                price=self.close_price,
                session_date=self.session_date,
                instrument=self.instrument,
            ),
        ]
        
        if self.overnight_high:
            levels.append(
                PriceLevel(
                    level_type=LevelType.OVERNIGHT_HIGH,
                    price=self.overnight_high,
                    session_date=self.session_date,
                    instrument=self.instrument,
                )
            )
        
        if self.overnight_low:
            levels.append(
                PriceLevel(
                    level_type=LevelType.OVERNIGHT_LOW,
                    price=self.overnight_low,
                    session_date=self.session_date,
                    instrument=self.instrument,
                )
            )
        
        return levels
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MarketSession):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class WeeklySession:
    """Aggregated weekly session entity.
    
    Represents a week's worth of data for weekly recap posts.
    """
    id: UUID
    instrument: Instrument
    week_start_date: date  # Monday of the week
    week_end_date: date    # Friday of the week
    
    # Weekly OHLC
    open_price: Price
    high_price: Price
    low_price: Price
    close_price: Price
    
    # Performance metrics
    change_points: Decimal
    change_percent: PercentageChange
    
    # Daily sessions that make up this week
    daily_sessions: List[MarketSession]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    def __init__(
        self,
        instrument: Instrument,
        week_start_date: date,
        week_end_date: date,
        daily_sessions: List[MarketSession],
        id: UUID | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        if not daily_sessions:
            raise ValueError("Weekly session must have at least one daily session")
        
        self.id = id or uuid4()
        self.instrument = instrument
        self.week_start_date = week_start_date
        self.week_end_date = week_end_date
        self.daily_sessions = sorted(daily_sessions, key=lambda s: s.session_date)
        self.created_at = created_at or timezone.now()
        self.updated_at = updated_at or timezone.now()
        
        # Calculate weekly aggregates
        self._calculate_aggregates()
    
    def _calculate_aggregates(self) -> None:
        """Calculate weekly OHLC and change metrics."""
        first_session = self.daily_sessions[0]
        last_session = self.daily_sessions[-1]
        
        self.open_price = first_session.open_price
        self.close_price = last_session.close_price
        
        # Find weekly high and low
        all_highs = [s.high_price.value for s in self.daily_sessions]
        all_lows = [s.low_price.value for s in self.daily_sessions]
        
        self.high_price = Price(max(all_highs))
        self.low_price = Price(min(all_lows))
        
        # Calculate weekly change
        self.change_points = self.close_price.value - self.open_price.value
        pct = (self.change_points / self.open_price.value) * 100
        self.change_percent = PercentageChange(pct)
    
    @property
    def weekly_range(self) -> SessionRange:
        """Get the week's high-low range."""
        return SessionRange(high=self.high_price, low=self.low_price)
    
    @property
    def trading_days(self) -> int:
        """Number of trading days in the week."""
        return len(self.daily_sessions)
    
    @property
    def total_volume(self) -> int:
        """Total volume for the week."""
        return sum(s.volume for s in self.daily_sessions)
    
    def get_price_levels(self) -> List[PriceLevel]:
        """Generate weekly price levels."""
        return [
            PriceLevel(
                level_type=LevelType.WEEKLY_OPEN,
                price=self.open_price,
                session_date=self.week_start_date,
                instrument=self.instrument,
            ),
            PriceLevel(
                level_type=LevelType.WEEKLY_HIGH,
                price=self.high_price,
                session_date=self.week_start_date,
                instrument=self.instrument,
            ),
            PriceLevel(
                level_type=LevelType.WEEKLY_LOW,
                price=self.low_price,
                session_date=self.week_start_date,
                instrument=self.instrument,
            ),
        ]
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WeeklySession):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class TradingPost:
    """Aggregate root for trading blog posts.
    
    Represents a single trading analysis post for one instrument.
    """
    id: UUID
    instrument: Instrument
    post_type: PostType
    title: str
    slug: TradingSlug
    content: str  # Markdown content
    session_date: date
    
    # Related data
    price_levels: List[PriceLevel]
    market_session: MarketSession | None
    weekly_session: WeeklySession | None
    
    # Structured data (JSON) for:
    # 1. Weekly recaps to pull from daily post data
    # 2. Frontend to render tables/charts consistently
    # 3. Regeneration with same data
    structured_data: Dict
    
    # Status
    status: TradingPostStatus
    
    # SEO
    meta_description: str | None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    scheduled_for: datetime | None
    
    def __init__(
        self,
        instrument: Instrument,
        post_type: PostType,
        title: str,
        content: str,
        session_date: date,
        price_levels: List[PriceLevel] | None = None,
        market_session: MarketSession | None = None,
        weekly_session: WeeklySession | None = None,
        structured_data: Dict | None = None,
        slug: TradingSlug | None = None,
        status: TradingPostStatus = TradingPostStatus.DRAFT,
        meta_description: str | None = None,
        id: UUID | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        published_at: datetime | None = None,
        scheduled_for: datetime | None = None,
    ) -> None:
        self.id = id or uuid4()
        self.instrument = instrument
        self.post_type = post_type
        self.title = self._validate_title(title)
        self.slug = slug or TradingSlug.create(
            instrument=instrument,
            post_type=post_type,
            date_str=session_date.isoformat(),
        )
        self.content = self._validate_content(content)
        self.session_date = session_date
        self.price_levels = price_levels or []
        self.market_session = market_session
        self.weekly_session = weekly_session
        self.structured_data = structured_data or {}
        self.status = status
        self.meta_description = meta_description
        self.created_at = created_at or timezone.now()
        self.updated_at = updated_at or timezone.now()
        self.published_at = published_at
        self.scheduled_for = scheduled_for
    
    @staticmethod
    def _validate_title(title: str) -> str:
        """Validate post title."""
        title = title.strip()
        if len(title) < 10:
            raise ValueError("Title must be at least 10 characters")
        if len(title) > 200:
            raise ValueError("Title must not exceed 200 characters")
        return title
    
    @staticmethod
    def _validate_content(content: str) -> str:
        """Validate post content."""
        content = content.strip()
        if len(content) < 100:
            raise ValueError("Content must be at least 100 characters")
        if len(content) > 50000:
            raise ValueError("Content must not exceed 50,000 characters")
        return content
    
    def publish(self) -> None:
        """Publish the post immediately."""
        if self.status == TradingPostStatus.PUBLISHED:
            raise ValueError("Post is already published")
        
        self.status = TradingPostStatus.PUBLISHED
        self.published_at = timezone.now()
        self.updated_at = timezone.now()
        self.scheduled_for = None
    
    def schedule(self, publish_at: datetime) -> None:
        """Schedule the post for future publication."""
        if self.status == TradingPostStatus.PUBLISHED:
            raise ValueError("Cannot schedule already published post")
        
        if publish_at <= timezone.now():
            raise ValueError("Scheduled time must be in the future")
        
        self.status = TradingPostStatus.SCHEDULED
        self.scheduled_for = publish_at
        self.updated_at = timezone.now()
    
    def unpublish(self) -> None:
        """Move post back to draft."""
        if self.status != TradingPostStatus.PUBLISHED:
            raise ValueError("Post is not published")
        
        self.status = TradingPostStatus.DRAFT
        self.updated_at = timezone.now()
    
    def archive(self) -> None:
        """Archive the post."""
        self.status = TradingPostStatus.ARCHIVED
        self.updated_at = timezone.now()
    
    def update_content(self, title: str, content: str) -> None:
        """Update post content."""
        self.title = self._validate_title(title)
        self.content = self._validate_content(content)
        self.updated_at = timezone.now()
    
    @property
    def is_published(self) -> bool:
        """Check if post is publicly visible."""
        return self.status == TradingPostStatus.PUBLISHED
    
    @property
    def is_scheduled(self) -> bool:
        """Check if post is scheduled for future publication."""
        return self.status == TradingPostStatus.SCHEDULED
    
    @property
    def reading_time(self) -> int:
        """Estimate reading time in minutes."""
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))
    
    @property
    def excerpt(self) -> str:
        """Generate a short excerpt from content."""
        # Remove markdown syntax for excerpt
        import re
        plain = self.content[:300]
        plain = re.sub(r'[#*`\[\]()]', '', plain)
        plain = re.sub(r'\|.*?\|', '', plain)  # Remove table rows
        return plain.strip() + '...' if len(self.content) > 300 else plain.strip()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TradingPost):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
