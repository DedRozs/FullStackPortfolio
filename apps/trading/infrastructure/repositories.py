"""Repository implementations for the Trading bounded context."""
from datetime import date
from decimal import Decimal
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
    Price,
    PercentageChange,
)
from apps.trading.infrastructure.models import (
    TradingPostModel,
    MarketSessionModel,
    WeeklySessionModel,
    PriceLevelModel,
    TradingPostPriceLevelModel,
)


class DjangoTradingPostRepository(TradingPostRepository):
    """Django ORM implementation of TradingPostRepository."""
    
    def save(self, post: TradingPost) -> None:
        """Persist a trading post."""
        # Get related session IDs if available
        market_session_id = None
        weekly_session_id = None
        
        if post.market_session:
            market_session_id = post.market_session.id
        if post.weekly_session:
            weekly_session_id = post.weekly_session.id
        
        model, _ = TradingPostModel.objects.update_or_create(
            id=post.id,
            defaults={
                'instrument': post.instrument.value,
                'post_type': post.post_type.value,
                'title': post.title,
                'slug': str(post.slug),
                'content': post.content,
                'session_date': post.session_date,
                'status': post.status.value,
                'meta_description': post.meta_description,
                'structured_data': post.structured_data,
                'published_at': post.published_at,
                'scheduled_for': post.scheduled_for,
                'market_session_id': market_session_id,
                'weekly_session_id': weekly_session_id,
            }
        )
        
        # Handle price levels relationship
        if post.price_levels:
            # Clear existing relationships
            TradingPostPriceLevelModel.objects.filter(trading_post=model).delete()
            
            # Create new relationships
            for level in post.price_levels:
                # Ensure level exists in database
                level_model, _ = PriceLevelModel.objects.get_or_create(
                    id=level.id,
                    defaults={
                        'instrument': level.instrument.value,
                        'level_type': level.level_type.value,
                        'price': level.price.value,
                        'session_date': level.session_date,
                    }
                )
                TradingPostPriceLevelModel.objects.create(
                    trading_post=model,
                    price_level=level_model,
                )
    
    def find_by_id(self, post_id: UUID) -> TradingPost | None:
        """Find a post by its ID."""
        try:
            model = TradingPostModel.objects.select_related(
                'market_session', 'weekly_session'
            ).prefetch_related(
                'post_price_levels__price_level'
            ).get(id=post_id)
            return self._to_entity(model)
        except TradingPostModel.DoesNotExist:
            return None
    
    def find_by_slug(self, slug: TradingSlug) -> TradingPost | None:
        """Find a post by its slug."""
        try:
            model = TradingPostModel.objects.select_related(
                'market_session', 'weekly_session'
            ).prefetch_related(
                'post_price_levels__price_level'
            ).get(
                slug=str(slug),
                status=TradingPostModel.Status.PUBLISHED,
            )
            return self._to_entity(model)
        except TradingPostModel.DoesNotExist:
            return None
    
    def find_all_published(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> List[TradingPost]:
        """Find all published posts, ordered by publish date descending."""
        queryset = TradingPostModel.objects.filter(
            status=TradingPostModel.Status.PUBLISHED
        ).select_related(
            'market_session', 'weekly_session'
        ).prefetch_related(
            'post_price_levels__price_level'
        ).order_by('-published_at')[offset:offset + limit]
        
        return [self._to_entity(model) for model in queryset]
    
    def find_by_instrument(
        self,
        instrument: Instrument,
        limit: int = 10,
        offset: int = 0,
    ) -> List[TradingPost]:
        """Find published posts for a specific instrument."""
        queryset = TradingPostModel.objects.filter(
            instrument=instrument.value,
            status=TradingPostModel.Status.PUBLISHED,
        ).select_related(
            'market_session', 'weekly_session'
        ).prefetch_related(
            'post_price_levels__price_level'
        ).order_by('-published_at')[offset:offset + limit]
        
        return [self._to_entity(model) for model in queryset]
    
    def find_by_post_type(
        self,
        post_type: PostType,
        limit: int = 10,
        offset: int = 0,
    ) -> List[TradingPost]:
        """Find published posts of a specific type."""
        queryset = TradingPostModel.objects.filter(
            post_type=post_type.value,
            status=TradingPostModel.Status.PUBLISHED,
        ).select_related(
            'market_session', 'weekly_session'
        ).prefetch_related(
            'post_price_levels__price_level'
        ).order_by('-published_at')[offset:offset + limit]
        
        return [self._to_entity(model) for model in queryset]
    
    def find_by_instrument_and_type(
        self,
        instrument: Instrument,
        post_type: PostType,
        limit: int = 10,
        offset: int = 0,
    ) -> List[TradingPost]:
        """Find published posts for specific instrument and type."""
        queryset = TradingPostModel.objects.filter(
            instrument=instrument.value,
            post_type=post_type.value,
            status=TradingPostModel.Status.PUBLISHED,
        ).select_related(
            'market_session', 'weekly_session'
        ).prefetch_related(
            'post_price_levels__price_level'
        ).order_by('-published_at')[offset:offset + limit]
        
        return [self._to_entity(model) for model in queryset]
    
    def find_by_session_date(
        self,
        session_date: date,
        instrument: Instrument | None = None,
    ) -> List[TradingPost]:
        """Find posts for a specific session date."""
        queryset = TradingPostModel.objects.filter(
            session_date=session_date,
            status=TradingPostModel.Status.PUBLISHED,
        )
        
        if instrument:
            queryset = queryset.filter(instrument=instrument.value)
        
        queryset = queryset.select_related(
            'market_session', 'weekly_session'
        ).prefetch_related(
            'post_price_levels__price_level'
        ).order_by('-published_at')
        
        return [self._to_entity(model) for model in queryset]
    
    def find_scheduled_ready_to_publish(self) -> List[TradingPost]:
        """Find scheduled posts that are ready to be published."""
        now = timezone.now()
        queryset = TradingPostModel.objects.filter(
            status=TradingPostModel.Status.SCHEDULED,
            scheduled_for__lte=now,
        ).select_related(
            'market_session', 'weekly_session'
        ).prefetch_related(
            'post_price_levels__price_level'
        ).order_by('scheduled_for')
        
        return [self._to_entity(model) for model in queryset]
    
    def find_all(
        self,
        status: TradingPostStatus | None = None,
    ) -> List[TradingPost]:
        """Find all posts, optionally filtered by status."""
        queryset = TradingPostModel.objects.all()
        
        if status:
            queryset = queryset.filter(status=status.value)
        
        queryset = queryset.select_related(
            'market_session', 'weekly_session'
        ).prefetch_related(
            'post_price_levels__price_level'
        ).order_by('-created_at')
        
        return [self._to_entity(model) for model in queryset]
    
    def delete(self, post: TradingPost) -> None:
        """Delete a trading post."""
        TradingPostModel.objects.filter(id=post.id).delete()
    
    def count_published(
        self,
        instrument: Instrument | None = None,
    ) -> int:
        """Count total published posts, optionally for an instrument."""
        queryset = TradingPostModel.objects.filter(
            status=TradingPostModel.Status.PUBLISHED
        )
        
        if instrument:
            queryset = queryset.filter(instrument=instrument.value)
        
        return queryset.count()
    
    def exists_for_date_and_type(
        self,
        instrument: Instrument,
        post_type: PostType,
        session_date: date,
    ) -> bool:
        """Check if a post already exists for the given criteria."""
        return TradingPostModel.objects.filter(
            instrument=instrument.value,
            post_type=post_type.value,
            session_date=session_date,
        ).exists()
    
    def _to_entity(self, model: TradingPostModel) -> TradingPost:
        """Map ORM model to domain entity."""
        # Get price levels from relationship
        price_levels = []
        for rel in model.post_price_levels.all():
            level_model = rel.price_level
            price_levels.append(
                PriceLevel(
                    id=level_model.id,
                    level_type=LevelType(level_model.level_type),
                    price=Price(level_model.price),
                    session_date=level_model.session_date,
                    instrument=Instrument(level_model.instrument),
                    created_at=level_model.created_at,
                )
            )
        
        # Map market session if present
        market_session = None
        if model.market_session:
            market_session = DjangoMarketSessionRepository._to_entity(
                model.market_session
            )
        
        # Map weekly session if present
        weekly_session = None
        if model.weekly_session:
            weekly_session = DjangoWeeklySessionRepository._to_entity_without_sessions(
                model.weekly_session
            )
        
        return TradingPost(
            id=model.id,
            instrument=Instrument(model.instrument),
            post_type=PostType(model.post_type),
            title=model.title,
            slug=TradingSlug(model.slug),
            content=model.content,
            session_date=model.session_date,
            price_levels=price_levels,
            market_session=market_session,
            weekly_session=weekly_session,
            structured_data=model.structured_data or {},
            status=TradingPostStatus(model.status),
            meta_description=model.meta_description,
            created_at=model.created_at,
            updated_at=model.updated_at,
            published_at=model.published_at,
            scheduled_for=model.scheduled_for,
        )


class DjangoMarketSessionRepository(MarketSessionRepository):
    """Django ORM implementation of MarketSessionRepository."""
    
    def save(self, session: MarketSession) -> None:
        """Persist a market session.
        
        Uses instrument + session_date as lookup to match unique constraint.
        Syncs the entity's id with the database record's id after save.
        """
        model, _ = MarketSessionModel.objects.update_or_create(
            instrument=session.instrument.value,
            session_date=session.session_date,
            defaults={
                'open_price': session.open_price.value,
                'high_price': session.high_price.value,
                'low_price': session.low_price.value,
                'close_price': session.close_price.value,
                'overnight_high': session.overnight_high.value if session.overnight_high else None,
                'overnight_low': session.overnight_low.value if session.overnight_low else None,
                'volume': session.volume,
                'prior_close': session.prior_close.value if session.prior_close else None,
                'change_points': session.change_points,
                'change_percent': session.change_percent.value if session.change_percent else None,
            }
        )
        # Sync the entity's id with the database record's id
        # This ensures foreign key references work correctly
        session.id = model.id
    
    def find_by_id(self, session_id: UUID) -> MarketSession | None:
        """Find a session by its ID."""
        try:
            model = MarketSessionModel.objects.get(id=session_id)
            return self._to_entity(model)
        except MarketSessionModel.DoesNotExist:
            return None
    
    def find_by_instrument_and_date(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> MarketSession | None:
        """Find a session for specific instrument and date."""
        try:
            model = MarketSessionModel.objects.get(
                instrument=instrument.value,
                session_date=session_date,
            )
            return self._to_entity(model)
        except MarketSessionModel.DoesNotExist:
            return None
    
    def find_latest_by_instrument(
        self,
        instrument: Instrument,
        limit: int = 5,
    ) -> List[MarketSession]:
        """Find most recent sessions for an instrument."""
        queryset = MarketSessionModel.objects.filter(
            instrument=instrument.value
        ).order_by('-session_date')[:limit]
        
        return [self._to_entity(model) for model in queryset]
    
    def find_by_date_range(
        self,
        instrument: Instrument,
        start_date: date,
        end_date: date,
    ) -> List[MarketSession]:
        """Find sessions within a date range."""
        queryset = MarketSessionModel.objects.filter(
            instrument=instrument.value,
            session_date__gte=start_date,
            session_date__lte=end_date,
        ).order_by('session_date')
        
        return [self._to_entity(model) for model in queryset]
    
    def find_prior_session(
        self,
        instrument: Instrument,
        before_date: date,
    ) -> MarketSession | None:
        """Find the session immediately before the given date."""
        try:
            model = MarketSessionModel.objects.filter(
                instrument=instrument.value,
                session_date__lt=before_date,
            ).order_by('-session_date').first()
            
            if model:
                return self._to_entity(model)
            return None
        except MarketSessionModel.DoesNotExist:
            return None
    
    def delete(self, session: MarketSession) -> None:
        """Delete a market session."""
        MarketSessionModel.objects.filter(id=session.id).delete()
    
    @staticmethod
    def _to_entity(model: MarketSessionModel) -> MarketSession:
        """Map ORM model to domain entity."""
        return MarketSession(
            id=model.id,
            instrument=Instrument(model.instrument),
            session_date=model.session_date,
            open_price=Price(model.open_price),
            high_price=Price(model.high_price),
            low_price=Price(model.low_price),
            close_price=Price(model.close_price),
            overnight_high=Price(model.overnight_high) if model.overnight_high else None,
            overnight_low=Price(model.overnight_low) if model.overnight_low else None,
            volume=model.volume,
            prior_close=Price(model.prior_close) if model.prior_close else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class DjangoWeeklySessionRepository(WeeklySessionRepository):
    """Django ORM implementation of WeeklySessionRepository."""
    
    def __init__(self, market_session_repo: MarketSessionRepository | None = None):
        """Initialize with optional market session repository."""
        self._market_session_repo = market_session_repo or DjangoMarketSessionRepository()
    
    def save(self, session: WeeklySession) -> None:
        """Persist a weekly session."""
        WeeklySessionModel.objects.update_or_create(
            id=session.id,
            defaults={
                'instrument': session.instrument.value,
                'week_start_date': session.week_start_date,
                'week_end_date': session.week_end_date,
                'open_price': session.open_price.value,
                'high_price': session.high_price.value,
                'low_price': session.low_price.value,
                'close_price': session.close_price.value,
                'change_points': session.change_points,
                'change_percent': session.change_percent.value,
                'total_volume': session.total_volume,
                'trading_days': session.trading_days,
            }
        )
    
    def find_by_id(self, session_id: UUID) -> WeeklySession | None:
        """Find a weekly session by its ID."""
        try:
            model = WeeklySessionModel.objects.get(id=session_id)
            return self._to_entity(model)
        except WeeklySessionModel.DoesNotExist:
            return None
    
    def find_by_instrument_and_week(
        self,
        instrument: Instrument,
        week_start_date: date,
    ) -> WeeklySession | None:
        """Find a weekly session for specific instrument and week."""
        try:
            model = WeeklySessionModel.objects.get(
                instrument=instrument.value,
                week_start_date=week_start_date,
            )
            return self._to_entity(model)
        except WeeklySessionModel.DoesNotExist:
            return None
    
    def find_latest_by_instrument(
        self,
        instrument: Instrument,
        limit: int = 4,
    ) -> List[WeeklySession]:
        """Find most recent weekly sessions for an instrument."""
        queryset = WeeklySessionModel.objects.filter(
            instrument=instrument.value
        ).order_by('-week_start_date')[:limit]
        
        return [self._to_entity(model) for model in queryset]
    
    def delete(self, session: WeeklySession) -> None:
        """Delete a weekly session."""
        WeeklySessionModel.objects.filter(id=session.id).delete()
    
    def _to_entity(self, model: WeeklySessionModel) -> WeeklySession:
        """Map ORM model to domain entity with daily sessions."""
        # Fetch daily sessions for the week
        daily_sessions = self._market_session_repo.find_by_date_range(
            instrument=Instrument(model.instrument),
            start_date=model.week_start_date,
            end_date=model.week_end_date,
        )
        
        # If no daily sessions found, we can't fully reconstruct
        # Return a minimal entity with stored aggregates
        if not daily_sessions:
            return self._to_entity_without_sessions(model)
        
        return WeeklySession(
            id=model.id,
            instrument=Instrument(model.instrument),
            week_start_date=model.week_start_date,
            week_end_date=model.week_end_date,
            daily_sessions=daily_sessions,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    @staticmethod
    def _to_entity_without_sessions(model: WeeklySessionModel) -> WeeklySession:
        """Map ORM model without loading daily sessions.
        
        Creates a minimal placeholder session when daily sessions aren't needed.
        """
        # Create a minimal placeholder session for the entity constructor
        placeholder_session = MarketSession(
            instrument=Instrument(model.instrument),
            session_date=model.week_start_date,
            open_price=Price(model.open_price),
            high_price=Price(model.high_price),
            low_price=Price(model.low_price),
            close_price=Price(model.close_price),
            volume=model.total_volume,
        )
        
        weekly = WeeklySession(
            id=model.id,
            instrument=Instrument(model.instrument),
            week_start_date=model.week_start_date,
            week_end_date=model.week_end_date,
            daily_sessions=[placeholder_session],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
        
        # Override calculated values with stored values
        weekly.open_price = Price(model.open_price)
        weekly.high_price = Price(model.high_price)
        weekly.low_price = Price(model.low_price)
        weekly.close_price = Price(model.close_price)
        weekly.change_points = model.change_points
        weekly.change_percent = PercentageChange(model.change_percent)
        
        return weekly


class DjangoPriceLevelRepository(PriceLevelRepository):
    """Django ORM implementation of PriceLevelRepository."""
    
    def save(self, level: PriceLevel) -> None:
        """Persist a price level."""
        PriceLevelModel.objects.update_or_create(
            id=level.id,
            defaults={
                'instrument': level.instrument.value,
                'level_type': level.level_type.value,
                'price': level.price.value,
                'session_date': level.session_date,
            }
        )
    
    def save_many(self, levels: List[PriceLevel]) -> None:
        """Persist multiple price levels."""
        for level in levels:
            self.save(level)
    
    def find_by_id(self, level_id: UUID) -> PriceLevel | None:
        """Find a price level by its ID."""
        try:
            model = PriceLevelModel.objects.get(id=level_id)
            return self._to_entity(model)
        except PriceLevelModel.DoesNotExist:
            return None
    
    def find_by_instrument_and_date(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> List[PriceLevel]:
        """Find all levels for an instrument on a specific date."""
        queryset = PriceLevelModel.objects.filter(
            instrument=instrument.value,
            session_date=session_date,
        ).order_by('level_type')
        
        return [self._to_entity(model) for model in queryset]
    
    def find_by_level_type(
        self,
        instrument: Instrument,
        level_type: LevelType,
        limit: int = 10,
    ) -> List[PriceLevel]:
        """Find recent levels of a specific type."""
        queryset = PriceLevelModel.objects.filter(
            instrument=instrument.value,
            level_type=level_type.value,
        ).order_by('-session_date')[:limit]
        
        return [self._to_entity(model) for model in queryset]
    
    def find_current_levels(
        self,
        instrument: Instrument,
    ) -> List[PriceLevel]:
        """Find the most current levels for an instrument.
        
        Returns the latest levels for each level type.
        """
        from django.db.models import Max
        
        # Get the latest session date for this instrument
        latest_date = PriceLevelModel.objects.filter(
            instrument=instrument.value
        ).aggregate(Max('session_date'))['session_date__max']
        
        if not latest_date:
            return []
        
        queryset = PriceLevelModel.objects.filter(
            instrument=instrument.value,
            session_date=latest_date,
        ).order_by('level_type')
        
        return [self._to_entity(model) for model in queryset]
    
    def delete_by_session_date(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> None:
        """Delete all levels for an instrument on a specific date."""
        PriceLevelModel.objects.filter(
            instrument=instrument.value,
            session_date=session_date,
        ).delete()
    
    @staticmethod
    def _to_entity(model: PriceLevelModel) -> PriceLevel:
        """Map ORM model to domain entity."""
        return PriceLevel(
            id=model.id,
            level_type=LevelType(model.level_type),
            price=Price(model.price),
            session_date=model.session_date,
            instrument=Instrument(model.instrument),
            created_at=model.created_at,
        )
