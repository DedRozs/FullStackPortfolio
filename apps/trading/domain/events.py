"""Domain events for the Trading bounded context."""
from dataclasses import dataclass, field
from datetime import date
from typing import Any, List
from uuid import UUID

from apps.shared.domain.events import DomainEvent
from apps.trading.domain.value_objects import Instrument, PostType


@dataclass(frozen=True)
class MarketDataFetched(DomainEvent):
    """Event raised when market data is successfully retrieved from yfinance."""
    instrument: Instrument = field(default=None)  # type: ignore
    session_date: date = field(default=None)  # type: ignore
    session_id: UUID = field(default=None)  # type: ignore
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'instrument': self.instrument.short_name if self.instrument else None,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'session_id': str(self.session_id) if self.session_id else None,
        }


@dataclass(frozen=True)
class PriceLevelsCalculated(DomainEvent):
    """Event raised when price levels are computed from session data."""
    instrument: Instrument = field(default=None)  # type: ignore
    session_date: date = field(default=None)  # type: ignore
    level_count: int = 0
    level_types: List[str] = field(default_factory=list)
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'instrument': self.instrument.short_name if self.instrument else None,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'level_count': self.level_count,
            'level_types': self.level_types,
        }


@dataclass(frozen=True)
class TradingPostGenerated(DomainEvent):
    """Event raised when AI content is created for a trading post."""
    post_id: UUID = field(default=None)  # type: ignore
    instrument: Instrument = field(default=None)  # type: ignore
    post_type: PostType = field(default=None)  # type: ignore
    session_date: date = field(default=None)  # type: ignore
    title: str = ""
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'post_id': str(self.post_id) if self.post_id else None,
            'instrument': self.instrument.short_name if self.instrument else None,
            'post_type': self.post_type.value if self.post_type else None,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'title': self.title,
        }


@dataclass(frozen=True)
class TradingPostPublished(DomainEvent):
    """Event raised when a trading post is published."""
    post_id: UUID = field(default=None)  # type: ignore
    instrument: Instrument = field(default=None)  # type: ignore
    post_type: PostType = field(default=None)  # type: ignore
    title: str = ""
    slug: str = ""
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'post_id': str(self.post_id) if self.post_id else None,
            'instrument': self.instrument.short_name if self.instrument else None,
            'post_type': self.post_type.value if self.post_type else None,
            'title': self.title,
            'slug': self.slug,
        }


@dataclass(frozen=True)
class TradingPostScheduled(DomainEvent):
    """Event raised when a trading post is scheduled for future publication."""
    post_id: UUID = field(default=None)  # type: ignore
    instrument: Instrument = field(default=None)  # type: ignore
    post_type: PostType = field(default=None)  # type: ignore
    scheduled_for: str = ""  # ISO format datetime
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'post_id': str(self.post_id) if self.post_id else None,
            'instrument': self.instrument.short_name if self.instrument else None,
            'post_type': self.post_type.value if self.post_type else None,
            'scheduled_for': self.scheduled_for,
        }


@dataclass(frozen=True)
class WeeklyDataAggregated(DomainEvent):
    """Event raised when weekly session data is aggregated."""
    instrument: Instrument = field(default=None)  # type: ignore
    week_start_date: date = field(default=None)  # type: ignore
    week_end_date: date = field(default=None)  # type: ignore
    trading_days: int = 0
    weekly_session_id: UUID = field(default=None)  # type: ignore
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'instrument': self.instrument.short_name if self.instrument else None,
            'week_start_date': self.week_start_date.isoformat() if self.week_start_date else None,
            'week_end_date': self.week_end_date.isoformat() if self.week_end_date else None,
            'trading_days': self.trading_days,
            'weekly_session_id': str(self.weekly_session_id) if self.weekly_session_id else None,
        }
