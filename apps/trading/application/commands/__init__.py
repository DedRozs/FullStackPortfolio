"""Commands for the Trading bounded context.

Commands are frozen dataclasses representing write operations.
They are named imperatively (e.g., FetchMarketData, not MarketDataFetched).
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List
from uuid import UUID

from apps.trading.domain.value_objects import Instrument, PostType


@dataclass(frozen=True)
class FetchMarketDataCommand:
    """Command to fetch market data from yfinance for an instrument.
    
    Triggers retrieval of OHLC data for the specified instrument and date.
    """
    instrument: Instrument
    session_date: date


@dataclass(frozen=True)
class FetchMarketDataBatchCommand:
    """Command to fetch market data for all instruments on a date.
    
    Convenience command for daily batch operations.
    """
    session_date: date
    instruments: List[Instrument] = field(default_factory=lambda: list(Instrument))


@dataclass(frozen=True)
class CalculatePriceLevelsCommand:
    """Command to calculate price levels from session data.
    
    Computes support/resistance levels based on prior session,
    overnight data, and weekly/monthly context.
    """
    instrument: Instrument
    session_date: date
    include_weekly: bool = True
    include_monthly: bool = True


@dataclass(frozen=True)
class GenerateTradingPostCommand:
    """Command to generate a trading blog post.
    
    Creates AI-generated content based on market data and price levels.
    """
    instrument: Instrument
    post_type: PostType
    session_date: date


@dataclass(frozen=True)
class GenerateTradingPostBatchCommand:
    """Command to generate posts for all instruments.
    
    Used for scheduled generation of pre-market, post-market, or weekly posts.
    """
    post_type: PostType
    session_date: date
    instruments: List[Instrument] = field(default_factory=lambda: list(Instrument))


@dataclass(frozen=True)
class CreateTradingPostCommand:
    """Command to create a trading post manually.
    
    Used for manual post creation with provided content.
    """
    instrument: Instrument
    post_type: PostType
    title: str
    content: str
    session_date: date
    meta_description: str | None = None


@dataclass(frozen=True)
class UpdateTradingPostCommand:
    """Command to update an existing trading post."""
    post_id: UUID
    title: str
    content: str
    meta_description: str | None = None


@dataclass(frozen=True)
class PublishTradingPostCommand:
    """Command to publish a trading post immediately."""
    post_id: UUID


@dataclass(frozen=True)
class ScheduleTradingPostCommand:
    """Command to schedule a trading post for future publication."""
    post_id: UUID
    publish_at: datetime


@dataclass(frozen=True)
class UnpublishTradingPostCommand:
    """Command to unpublish a trading post."""
    post_id: UUID


@dataclass(frozen=True)
class ArchiveTradingPostCommand:
    """Command to archive a trading post."""
    post_id: UUID


@dataclass(frozen=True)
class DeleteTradingPostCommand:
    """Command to delete a trading post."""
    post_id: UUID


@dataclass(frozen=True)
class AggregateWeeklyDataCommand:
    """Command to aggregate weekly session data.
    
    Combines daily sessions into a weekly summary for recap posts.
    """
    instrument: Instrument
    week_start_date: date  # Monday of the week


@dataclass(frozen=True)
class PublishScheduledPostsCommand:
    """Command to publish all posts that are scheduled and due.
    
    Called by the scheduler to process scheduled posts.
    """
    pass
