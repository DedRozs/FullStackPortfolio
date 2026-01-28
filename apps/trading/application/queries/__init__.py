"""Queries for the Trading bounded context.

Queries are frozen dataclasses representing read operations.
They specify what data to retrieve and any filters/pagination.
"""
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from apps.trading.domain.value_objects import Instrument, PostType


@dataclass(frozen=True)
class GetTradingPostByIdQuery:
    """Query to get a specific trading post by ID."""
    post_id: UUID


@dataclass(frozen=True)
class GetTradingPostBySlugQuery:
    """Query to get a specific trading post by slug."""
    slug: str


@dataclass(frozen=True)
class GetPublishedTradingPostsQuery:
    """Query to get published trading posts with pagination."""
    limit: int = 10
    offset: int = 0


@dataclass(frozen=True)
class GetPostsByInstrumentQuery:
    """Query to get trading posts for a specific instrument."""
    instrument: str  # Short name: NQ, ES, RTY, YM
    limit: int = 10
    offset: int = 0


@dataclass(frozen=True)
class GetPostsByTypeQuery:
    """Query to get trading posts of a specific type."""
    post_type: str  # pre_market, post_market, weekly_recap
    limit: int = 10
    offset: int = 0


@dataclass(frozen=True)
class GetPostsByInstrumentAndTypeQuery:
    """Query to get trading posts for specific instrument and type."""
    instrument: str
    post_type: str
    limit: int = 10
    offset: int = 0


@dataclass(frozen=True)
class GetPostsBySessionDateQuery:
    """Query to get trading posts for a specific session date."""
    session_date: date
    instrument: str | None = None


@dataclass(frozen=True)
class GetLatestPostsByInstrumentQuery:
    """Query to get latest posts for each instrument.
    
    Returns the most recent post of each type for a given instrument.
    """
    instrument: str


@dataclass(frozen=True)
class GetAllTradingPostsQuery:
    """Query to get all trading posts (admin use)."""
    status: str | None = None  # draft, scheduled, published, archived


@dataclass(frozen=True)
class GetMarketSessionQuery:
    """Query to get market session data for an instrument and date."""
    instrument: str
    session_date: date


@dataclass(frozen=True)
class GetLatestMarketSessionsQuery:
    """Query to get recent market sessions for an instrument."""
    instrument: str
    limit: int = 5


@dataclass(frozen=True)
class GetMarketSessionsRangeQuery:
    """Query to get market sessions within a date range."""
    instrument: str
    start_date: date
    end_date: date


@dataclass(frozen=True)
class GetWeeklySessionQuery:
    """Query to get weekly session data for an instrument and week."""
    instrument: str
    week_start_date: date  # Monday of the week


@dataclass(frozen=True)
class GetPriceLevelsQuery:
    """Query to get price levels for an instrument and date."""
    instrument: str
    session_date: date


@dataclass(frozen=True)
class GetCurrentPriceLevelsQuery:
    """Query to get the most current price levels for an instrument.
    
    Returns latest levels for each level type.
    """
    instrument: str


@dataclass(frozen=True)
class GetPostCountQuery:
    """Query to get count of published posts."""
    instrument: str | None = None


@dataclass(frozen=True)
class CheckPostExistsQuery:
    """Query to check if a post already exists for given criteria."""
    instrument: str
    post_type: str
    session_date: date


@dataclass(frozen=True)
class GetAllInstrumentsQuery:
    """Query to get all available instruments."""
    pass


@dataclass(frozen=True)
class GetScheduledPostsQuery:
    """Query to get posts scheduled for publication.
    
    Used by scheduler to find posts due for publishing.
    """
    pass
