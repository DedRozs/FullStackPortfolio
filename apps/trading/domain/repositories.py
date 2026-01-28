"""Repository interfaces for the Trading bounded context."""
from abc import ABC, abstractmethod
from datetime import date
from typing import List
from uuid import UUID

from apps.trading.domain.entities import (
    TradingPost,
    TradingPostStatus,
    MarketSession,
    WeeklySession,
    PriceLevel,
)
from apps.trading.domain.value_objects import (
    Instrument,
    PostType,
    TradingSlug,
    LevelType,
)


class TradingPostRepository(ABC):
    """Abstract repository for TradingPost aggregate.
    
    Provides collection-like interface for trading posts.
    """
    
    @abstractmethod
    def save(self, post: TradingPost) -> None:
        """Persist a trading post."""
        pass
    
    @abstractmethod
    def find_by_id(self, post_id: UUID) -> TradingPost | None:
        """Find a post by its ID."""
        pass
    
    @abstractmethod
    def find_by_slug(self, slug: TradingSlug) -> TradingPost | None:
        """Find a post by its slug."""
        pass
    
    @abstractmethod
    def find_all_published(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> List[TradingPost]:
        """Find all published posts, ordered by publish date descending."""
        pass
    
    @abstractmethod
    def find_by_instrument(
        self,
        instrument: Instrument,
        limit: int = 10,
        offset: int = 0,
    ) -> List[TradingPost]:
        """Find published posts for a specific instrument."""
        pass
    
    @abstractmethod
    def find_by_post_type(
        self,
        post_type: PostType,
        limit: int = 10,
        offset: int = 0,
    ) -> List[TradingPost]:
        """Find published posts of a specific type."""
        pass
    
    @abstractmethod
    def find_by_instrument_and_type(
        self,
        instrument: Instrument,
        post_type: PostType,
        limit: int = 10,
        offset: int = 0,
    ) -> List[TradingPost]:
        """Find published posts for specific instrument and type."""
        pass
    
    @abstractmethod
    def find_by_session_date(
        self,
        session_date: date,
        instrument: Instrument | None = None,
    ) -> List[TradingPost]:
        """Find posts for a specific session date."""
        pass
    
    @abstractmethod
    def find_scheduled_ready_to_publish(self) -> List[TradingPost]:
        """Find scheduled posts that are ready to be published."""
        pass
    
    @abstractmethod
    def find_all(
        self,
        status: TradingPostStatus | None = None,
    ) -> List[TradingPost]:
        """Find all posts, optionally filtered by status."""
        pass
    
    @abstractmethod
    def delete(self, post: TradingPost) -> None:
        """Delete a trading post."""
        pass
    
    @abstractmethod
    def count_published(
        self,
        instrument: Instrument | None = None,
    ) -> int:
        """Count total published posts, optionally for an instrument."""
        pass
    
    @abstractmethod
    def exists_for_date_and_type(
        self,
        instrument: Instrument,
        post_type: PostType,
        session_date: date,
    ) -> bool:
        """Check if a post already exists for the given criteria."""
        pass


class MarketSessionRepository(ABC):
    """Abstract repository for MarketSession entity.
    
    Provides persistence for daily market session data.
    """
    
    @abstractmethod
    def save(self, session: MarketSession) -> None:
        """Persist a market session."""
        pass
    
    @abstractmethod
    def find_by_id(self, session_id: UUID) -> MarketSession | None:
        """Find a session by its ID."""
        pass
    
    @abstractmethod
    def find_by_instrument_and_date(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> MarketSession | None:
        """Find a session for specific instrument and date."""
        pass
    
    @abstractmethod
    def find_latest_by_instrument(
        self,
        instrument: Instrument,
        limit: int = 5,
    ) -> List[MarketSession]:
        """Find most recent sessions for an instrument."""
        pass
    
    @abstractmethod
    def find_by_date_range(
        self,
        instrument: Instrument,
        start_date: date,
        end_date: date,
    ) -> List[MarketSession]:
        """Find sessions within a date range."""
        pass
    
    @abstractmethod
    def find_prior_session(
        self,
        instrument: Instrument,
        before_date: date,
    ) -> MarketSession | None:
        """Find the session immediately before the given date."""
        pass
    
    @abstractmethod
    def delete(self, session: MarketSession) -> None:
        """Delete a market session."""
        pass


class WeeklySessionRepository(ABC):
    """Abstract repository for WeeklySession entity.
    
    Provides persistence for weekly aggregated data.
    """
    
    @abstractmethod
    def save(self, session: WeeklySession) -> None:
        """Persist a weekly session."""
        pass
    
    @abstractmethod
    def find_by_id(self, session_id: UUID) -> WeeklySession | None:
        """Find a weekly session by its ID."""
        pass
    
    @abstractmethod
    def find_by_instrument_and_week(
        self,
        instrument: Instrument,
        week_start_date: date,
    ) -> WeeklySession | None:
        """Find a weekly session for specific instrument and week."""
        pass
    
    @abstractmethod
    def find_latest_by_instrument(
        self,
        instrument: Instrument,
        limit: int = 4,
    ) -> List[WeeklySession]:
        """Find most recent weekly sessions for an instrument."""
        pass
    
    @abstractmethod
    def delete(self, session: WeeklySession) -> None:
        """Delete a weekly session."""
        pass


class PriceLevelRepository(ABC):
    """Abstract repository for PriceLevel entity.
    
    Provides persistence for calculated price levels.
    """
    
    @abstractmethod
    def save(self, level: PriceLevel) -> None:
        """Persist a price level."""
        pass
    
    @abstractmethod
    def save_many(self, levels: List[PriceLevel]) -> None:
        """Persist multiple price levels."""
        pass
    
    @abstractmethod
    def find_by_id(self, level_id: UUID) -> PriceLevel | None:
        """Find a price level by its ID."""
        pass
    
    @abstractmethod
    def find_by_instrument_and_date(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> List[PriceLevel]:
        """Find all levels for an instrument on a specific date."""
        pass
    
    @abstractmethod
    def find_by_level_type(
        self,
        instrument: Instrument,
        level_type: LevelType,
        limit: int = 10,
    ) -> List[PriceLevel]:
        """Find recent levels of a specific type."""
        pass
    
    @abstractmethod
    def find_current_levels(
        self,
        instrument: Instrument,
    ) -> List[PriceLevel]:
        """Find the most current levels for an instrument.
        
        Returns the latest levels for each level type.
        """
        pass
    
    @abstractmethod
    def delete_by_session_date(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> None:
        """Delete all levels for an instrument on a specific date."""
        pass
