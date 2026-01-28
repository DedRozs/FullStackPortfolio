"""Application services for the Trading bounded context.

Application services orchestrate use cases by coordinating domain objects,
repositories, and publishing events. They do not contain business logic.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List
from uuid import UUID

from django.utils import timezone

from apps.trading.domain.entities import (
    TradingPost,
    TradingPostStatus,
    MarketSession,
    WeeklySession,
    PriceLevel,
)
from apps.trading.domain.events import (
    MarketDataFetched,
    PriceLevelsCalculated,
    TradingPostGenerated,
    TradingPostPublished,
    TradingPostScheduled,
    WeeklyDataAggregated,
)
from apps.trading.domain.repositories import (
    TradingPostRepository,
    MarketSessionRepository,
    WeeklySessionRepository,
    PriceLevelRepository,
)
from apps.trading.domain.value_objects import (
    Instrument,
    PostType,
    TradingSlug,
    LevelType,
)
from apps.trading.application.commands import (
    FetchMarketDataCommand,
    FetchMarketDataBatchCommand,
    CalculatePriceLevelsCommand,
    GenerateTradingPostCommand,
    GenerateTradingPostBatchCommand,
    CreateTradingPostCommand,
    UpdateTradingPostCommand,
    PublishTradingPostCommand,
    ScheduleTradingPostCommand,
    UnpublishTradingPostCommand,
    ArchiveTradingPostCommand,
    DeleteTradingPostCommand,
    AggregateWeeklyDataCommand,
    PublishScheduledPostsCommand,
)
from apps.trading.application.queries import (
    GetTradingPostByIdQuery,
    GetTradingPostBySlugQuery,
    GetPublishedTradingPostsQuery,
    GetPostsByInstrumentQuery,
    GetPostsByTypeQuery,
    GetPostsByInstrumentAndTypeQuery,
    GetPostsBySessionDateQuery,
    GetLatestPostsByInstrumentQuery,
    GetAllTradingPostsQuery,
    GetMarketSessionQuery,
    GetLatestMarketSessionsQuery,
    GetMarketSessionsRangeQuery,
    GetWeeklySessionQuery,
    GetPriceLevelsQuery,
    GetCurrentPriceLevelsQuery,
    GetPostCountQuery,
    CheckPostExistsQuery,
    GetAllInstrumentsQuery,
    GetScheduledPostsQuery,
)
from apps.shared.infrastructure.event_bus import EventBus


class TradingApplicationService:
    """Application service for Trading blog use cases.
    
    Coordinates between repositories, domain entities, and external services.
    Publishes domain events after successful operations.
    """
    
    def __init__(
        self,
        post_repository: TradingPostRepository,
        session_repository: MarketSessionRepository,
        weekly_repository: WeeklySessionRepository,
        level_repository: PriceLevelRepository,
        event_bus: EventBus,
    ) -> None:
        self._post_repo = post_repository
        self._session_repo = session_repository
        self._weekly_repo = weekly_repository
        self._level_repo = level_repository
        self._event_bus = event_bus
    
    # ---------------------
    # Command Handlers
    # ---------------------
    
    def create_post(self, command: CreateTradingPostCommand) -> UUID:
        """Create a new trading post manually."""
        # Get related market session if available
        market_session = self._session_repo.find_by_instrument_and_date(
            command.instrument,
            command.session_date,
        )
        
        # Get price levels for the session
        price_levels = self._level_repo.find_by_instrument_and_date(
            command.instrument,
            command.session_date,
        )
        
        post = TradingPost(
            instrument=command.instrument,
            post_type=command.post_type,
            title=command.title,
            content=command.content,
            session_date=command.session_date,
            meta_description=command.meta_description,
            market_session=market_session,
            price_levels=price_levels,
        )
        
        self._post_repo.save(post)
        
        event = TradingPostGenerated(
            post_id=post.id,
            instrument=post.instrument,
            post_type=post.post_type,
            session_date=post.session_date,
            title=post.title,
        )
        self._event_bus.publish(event)
        
        return post.id
    
    def update_post(self, command: UpdateTradingPostCommand) -> None:
        """Update an existing trading post."""
        post = self._post_repo.find_by_id(command.post_id)
        if post is None:
            raise ValueError(f"Trading post not found: {command.post_id}")
        
        post.update_content(command.title, command.content)
        post.meta_description = command.meta_description
        
        self._post_repo.save(post)
    
    def publish_post(self, command: PublishTradingPostCommand) -> None:
        """Publish a trading post immediately."""
        post = self._post_repo.find_by_id(command.post_id)
        if post is None:
            raise ValueError(f"Trading post not found: {command.post_id}")
        
        post.publish()
        self._post_repo.save(post)
        
        event = TradingPostPublished(
            post_id=post.id,
            instrument=post.instrument,
            post_type=post.post_type,
            title=post.title,
            slug=str(post.slug),
        )
        self._event_bus.publish(event)
    
    def schedule_post(self, command: ScheduleTradingPostCommand) -> None:
        """Schedule a trading post for future publication."""
        post = self._post_repo.find_by_id(command.post_id)
        if post is None:
            raise ValueError(f"Trading post not found: {command.post_id}")
        
        post.schedule(command.publish_at)
        self._post_repo.save(post)
        
        event = TradingPostScheduled(
            post_id=post.id,
            instrument=post.instrument,
            post_type=post.post_type,
            scheduled_for=command.publish_at.isoformat(),
        )
        self._event_bus.publish(event)
    
    def unpublish_post(self, command: UnpublishTradingPostCommand) -> None:
        """Unpublish a trading post."""
        post = self._post_repo.find_by_id(command.post_id)
        if post is None:
            raise ValueError(f"Trading post not found: {command.post_id}")
        
        post.unpublish()
        self._post_repo.save(post)
    
    def archive_post(self, command: ArchiveTradingPostCommand) -> None:
        """Archive a trading post."""
        post = self._post_repo.find_by_id(command.post_id)
        if post is None:
            raise ValueError(f"Trading post not found: {command.post_id}")
        
        post.archive()
        self._post_repo.save(post)
    
    def delete_post(self, command: DeleteTradingPostCommand) -> None:
        """Delete a trading post."""
        post = self._post_repo.find_by_id(command.post_id)
        if post is None:
            raise ValueError(f"Trading post not found: {command.post_id}")
        
        self._post_repo.delete(post)
    
    def aggregate_weekly_data(self, command: AggregateWeeklyDataCommand) -> UUID | None:
        """Aggregate daily sessions into a weekly session.
        
        Returns the weekly session ID if successful, None if insufficient data.
        """
        # Calculate week end date (Friday)
        week_end_date = command.week_start_date + timedelta(days=4)
        
        # Get all daily sessions for the week
        daily_sessions = self._session_repo.find_by_date_range(
            command.instrument,
            command.week_start_date,
            week_end_date,
        )
        
        if not daily_sessions:
            return None
        
        # Check if weekly session already exists
        existing = self._weekly_repo.find_by_instrument_and_week(
            command.instrument,
            command.week_start_date,
        )
        
        if existing:
            # Update existing weekly session
            existing.daily_sessions = daily_sessions
            existing._calculate_aggregates()
            existing.updated_at = timezone.now()
            self._weekly_repo.save(existing)
            session_id = existing.id
        else:
            # Create new weekly session
            weekly_session = WeeklySession(
                instrument=command.instrument,
                week_start_date=command.week_start_date,
                week_end_date=week_end_date,
                daily_sessions=daily_sessions,
            )
            self._weekly_repo.save(weekly_session)
            session_id = weekly_session.id
        
        event = WeeklyDataAggregated(
            instrument=command.instrument,
            week_start_date=command.week_start_date,
            week_end_date=week_end_date,
            weekly_session_id=session_id,
            trading_days=len(daily_sessions),
        )
        self._event_bus.publish(event)
        
        return session_id
    
    def publish_scheduled_posts(self, command: PublishScheduledPostsCommand) -> int:
        """Publish all scheduled posts that are due.
        
        Returns the number of posts published.
        """
        posts = self._post_repo.find_scheduled_ready_to_publish()
        count = 0
        
        for post in posts:
            post.publish()
            self._post_repo.save(post)
            
            event = TradingPostPublished(
                post_id=post.id,
                instrument=post.instrument,
                post_type=post.post_type,
                title=post.title,
                slug=str(post.slug),
            )
            self._event_bus.publish(event)
            count += 1
        
        return count
    
    # ---------------------
    # Query Handlers
    # ---------------------
    
    def get_post_by_id(self, query: GetTradingPostByIdQuery) -> TradingPost | None:
        """Get a trading post by ID."""
        return self._post_repo.find_by_id(query.post_id)
    
    def get_post_by_slug(self, query: GetTradingPostBySlugQuery) -> TradingPost | None:
        """Get a trading post by slug."""
        try:
            slug = TradingSlug(query.slug)
            return self._post_repo.find_by_slug(slug)
        except ValueError:
            return None
    
    def get_published_posts(self, query: GetPublishedTradingPostsQuery) -> List[TradingPost]:
        """Get published trading posts with pagination."""
        return self._post_repo.find_all_published(
            limit=query.limit,
            offset=query.offset,
        )
    
    def get_posts_by_instrument(self, query: GetPostsByInstrumentQuery) -> List[TradingPost]:
        """Get published posts for a specific instrument."""
        try:
            instrument = Instrument.from_short_name(query.instrument)
            return self._post_repo.find_by_instrument(
                instrument,
                limit=query.limit,
                offset=query.offset,
            )
        except ValueError:
            return []
    
    def get_posts_by_type(self, query: GetPostsByTypeQuery) -> List[TradingPost]:
        """Get published posts of a specific type."""
        try:
            post_type = PostType(query.post_type)
            return self._post_repo.find_by_post_type(
                post_type,
                limit=query.limit,
                offset=query.offset,
            )
        except ValueError:
            return []
    
    def get_posts_by_instrument_and_type(
        self,
        query: GetPostsByInstrumentAndTypeQuery,
    ) -> List[TradingPost]:
        """Get published posts for specific instrument and type."""
        try:
            instrument = Instrument.from_short_name(query.instrument)
            post_type = PostType(query.post_type)
            return self._post_repo.find_by_instrument_and_type(
                instrument,
                post_type,
                limit=query.limit,
                offset=query.offset,
            )
        except ValueError:
            return []
    
    def get_posts_by_session_date(
        self,
        query: GetPostsBySessionDateQuery,
    ) -> List[TradingPost]:
        """Get posts for a specific session date."""
        instrument = None
        if query.instrument:
            try:
                instrument = Instrument.from_short_name(query.instrument)
            except ValueError:
                return []
        
        return self._post_repo.find_by_session_date(
            query.session_date,
            instrument,
        )
    
    def get_all_posts(self, query: GetAllTradingPostsQuery) -> List[TradingPost]:
        """Get all trading posts (admin use)."""
        status = None
        if query.status:
            try:
                status = TradingPostStatus(query.status)
            except ValueError:
                pass
        return self._post_repo.find_all(status)
    
    def get_market_session(self, query: GetMarketSessionQuery) -> MarketSession | None:
        """Get market session data for an instrument and date."""
        try:
            instrument = Instrument.from_short_name(query.instrument)
            return self._session_repo.find_by_instrument_and_date(
                instrument,
                query.session_date,
            )
        except ValueError:
            return None
    
    def get_latest_market_sessions(
        self,
        query: GetLatestMarketSessionsQuery,
    ) -> List[MarketSession]:
        """Get recent market sessions for an instrument."""
        try:
            instrument = Instrument.from_short_name(query.instrument)
            return self._session_repo.find_latest_by_instrument(
                instrument,
                limit=query.limit,
            )
        except ValueError:
            return []
    
    def get_market_sessions_range(
        self,
        query: GetMarketSessionsRangeQuery,
    ) -> List[MarketSession]:
        """Get market sessions within a date range."""
        try:
            instrument = Instrument.from_short_name(query.instrument)
            return self._session_repo.find_by_date_range(
                instrument,
                query.start_date,
                query.end_date,
            )
        except ValueError:
            return []
    
    def get_weekly_session(self, query: GetWeeklySessionQuery) -> WeeklySession | None:
        """Get weekly session data for an instrument and week."""
        try:
            instrument = Instrument.from_short_name(query.instrument)
            return self._weekly_repo.find_by_instrument_and_week(
                instrument,
                query.week_start_date,
            )
        except ValueError:
            return None
    
    def get_price_levels(self, query: GetPriceLevelsQuery) -> List[PriceLevel]:
        """Get price levels for an instrument and date."""
        try:
            instrument = Instrument.from_short_name(query.instrument)
            return self._level_repo.find_by_instrument_and_date(
                instrument,
                query.session_date,
            )
        except ValueError:
            return []
    
    def get_current_price_levels(
        self,
        query: GetCurrentPriceLevelsQuery,
    ) -> List[PriceLevel]:
        """Get the most current price levels for an instrument."""
        try:
            instrument = Instrument.from_short_name(query.instrument)
            return self._level_repo.find_current_levels(instrument)
        except ValueError:
            return []
    
    def get_post_count(self, query: GetPostCountQuery) -> int:
        """Get count of published posts."""
        instrument = None
        if query.instrument:
            try:
                instrument = Instrument.from_short_name(query.instrument)
            except ValueError:
                return 0
        return self._post_repo.count_published(instrument)
    
    def check_post_exists(self, query: CheckPostExistsQuery) -> bool:
        """Check if a post already exists for given criteria."""
        try:
            instrument = Instrument.from_short_name(query.instrument)
            post_type = PostType(query.post_type)
            return self._post_repo.exists_for_date_and_type(
                instrument,
                post_type,
                query.session_date,
            )
        except ValueError:
            return False
    
    def get_all_instruments(self, query: GetAllInstrumentsQuery) -> List[Instrument]:
        """Get all available instruments."""
        return list(Instrument)
    
    def get_scheduled_posts(self, query: GetScheduledPostsQuery) -> List[TradingPost]:
        """Get posts scheduled for publication."""
        return self._post_repo.find_scheduled_ready_to_publish()


# Factory function for dependency injection
def get_trading_service() -> TradingApplicationService:
    """Create a TradingApplicationService with all dependencies.
    
    This factory function wires up all the required repositories
    and the event bus for the application service.
    """
    from apps.trading.infrastructure.repositories import (
        DjangoTradingPostRepository,
        DjangoMarketSessionRepository,
        DjangoWeeklySessionRepository,
        DjangoPriceLevelRepository,
    )
    from apps.shared.infrastructure.event_bus import get_event_bus
    
    return TradingApplicationService(
        post_repository=DjangoTradingPostRepository(),
        session_repository=DjangoMarketSessionRepository(),
        weekly_repository=DjangoWeeklySessionRepository(),
        level_repository=DjangoPriceLevelRepository(),
        event_bus=get_event_bus(),
    )
