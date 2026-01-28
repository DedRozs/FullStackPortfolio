"""Trading content generation pipeline.

Orchestrates the full workflow for generating trading blog posts:
1. Fetch market data for the instrument/date
2. Calculate price levels
3. Generate content using AI
4. Create and optionally publish the trading post
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Tuple, Dict, Any, Optional
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
    Price,
    LevelType,
    SessionOHLC,
    DailySessionData,
    PriceLevelData,
    PostMarketStructuredData,
    PreMarketStructuredData,
    WeeklyRecapStructuredData,
)
from apps.trading.domain.events import (
    TradingPostGenerated,
    TradingPostPublished,
)
from apps.trading.application.content_generation.trading_post_generator import (
    TradingPostGeneratorService,
    GenerationResult,
    GenerationLog,
)
from apps.trading.application.content_generation.reviewer import (
    TradingPostReviewerService,
    ReviewResult,
    ReviewLog,
)
from apps.trading.application.intraday_analysis import (
    IntradayAnalysisService,
    SessionProgression,
)
from apps.trading.infrastructure.market_data.local_market_data import (
    LocalMarketDataService,
    SessionData,
    DataNotAvailableError,
)
from apps.trading.infrastructure.market_data.sync_service import (
    MarketDataSyncService,
    DataFetchError,
)
from apps.shared.infrastructure.event_bus import EventBus


logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of running the content generation pipeline."""
    success: bool
    post_id: UUID | None = None
    post_type: PostType | None = None
    instrument: Instrument | None = None
    title: str = ""
    published: bool = False
    error_message: str = ""
    tokens_used: int = 0
    duration_seconds: float = 0.0
    # Review metrics
    reviewed: bool = False
    review_approved: bool = False
    review_quality_score: float = 0.0
    review_issues: int = 0


class TradingContentPipeline:
    """Orchestrates the trading content generation pipeline.
    
    Coordinates between market data fetching, price level calculation,
    AI content generation, and post publication.
    """
    
    def __init__(
        self,
        post_repository: TradingPostRepository,
        session_repository: MarketSessionRepository,
        weekly_repository: WeeklySessionRepository,
        level_repository: PriceLevelRepository,
        event_bus: EventBus,
        market_data_service: LocalMarketDataService | None = None,
        sync_service: MarketDataSyncService | None = None,
        generator: TradingPostGeneratorService | None = None,
        reviewer: TradingPostReviewerService | None = None,
        intraday_analyzer: IntradayAnalysisService | None = None,
        skip_review: bool = False,
        auto_fetch_data: bool = True,
    ) -> None:
        """Initialize the pipeline with all dependencies.
        
        Args:
            post_repository: Repository for trading posts
            session_repository: Repository for market sessions
            weekly_repository: Repository for weekly sessions
            level_repository: Repository for price levels
            event_bus: Event bus for publishing domain events
            market_data_service: Service for reading market data from local DB
            sync_service: Service for fetching missing data from Databento
            generator: Content generator service (o3-mini for reasoning)
            reviewer: Content reviewer service (gpt-5-mini for validation)
            intraday_analyzer: Service for analyzing intraday bar data
            skip_review: If True, bypass review step (for testing only)
            auto_fetch_data: If True, automatically fetch missing data before generation
        """
        self._post_repo = post_repository
        self._session_repo = session_repository
        self._weekly_repo = weekly_repository
        self._level_repo = level_repository
        self._event_bus = event_bus
        self._market_data = market_data_service or LocalMarketDataService()
        self._sync_service = sync_service or MarketDataSyncService()
        self._generator = generator or TradingPostGeneratorService()
        self._reviewer = reviewer or TradingPostReviewerService()
        self._intraday_analyzer = intraday_analyzer or IntradayAnalysisService()
        self._skip_review = skip_review
        self._auto_fetch = auto_fetch_data
    
    # =========================================================================
    # Data Availability Checks
    # =========================================================================
    
    def check_data_availability(
        self,
        instrument: Instrument,
        session_date: date,
    ) -> dict:
        """Check if all required data is available for content generation.
        
        Use this before generation to ensure data has been fetched.
        
        Args:
            instrument: The instrument to check
            session_date: The trading date
            
        Returns:
            Dict with availability status and missing data details
        """
        bar_counts = self._market_data.get_bar_count(instrument, session_date)
        has_rth = bar_counts['rth'] > 0
        has_overnight = bar_counts['overnight'] > 0
        
        # Check prior session for pre-market
        prior_date = self._get_prior_trading_day(session_date)
        prior_counts = self._market_data.get_bar_count(instrument, prior_date)
        has_prior = prior_counts['rth'] > 0
        
        # Validate data integrity if RTH exists
        validation = None
        if has_rth:
            validation = self._market_data.validate_data_integrity(instrument, session_date)
        
        return {
            'ready_for_postmarket': has_rth,
            'ready_for_premarket': has_prior,  # Need prior session for pre-market
            'session_date': session_date.isoformat(),
            'rth_bars': bar_counts['rth'],
            'overnight_bars': bar_counts['overnight'],
            'prior_date': prior_date.isoformat(),
            'prior_rth_bars': prior_counts['rth'],
            'validation': validation,
            'fetch_command': (
                f"python manage.py fetch_intraday_bars "
                f"--date {session_date} --instruments {instrument.value.replace('=F', '')}"
            ) if not has_rth else None,
        }
    
    # =========================================================================
    # Structured Data Builders
    # =========================================================================
    
    def _build_session_data(self, session: MarketSession) -> Dict[str, Any]:
        """Build structured session data for JSON storage."""
        return DailySessionData(
            date=session.session_date.isoformat(),
            day_name=session.session_date.strftime('%A'),
            ohlc=SessionOHLC(
                open=float(session.open_price.value),
                high=float(session.high_price.value),
                low=float(session.low_price.value),
                close=float(session.close_price.value),
                volume=session.volume,
            ),
            change_points=float(session.change_points) if session.change_points else None,
            change_percent=float(session.change_percent.value) if session.change_percent else None,
            prior_close=float(session.prior_close.value) if session.prior_close else None,
        ).to_dict()
    
    def _build_level_data(self, level: PriceLevel) -> Dict[str, Any]:
        """Build structured price level data."""
        return PriceLevelData(
            level_type=level.level_type.value,
            price=float(level.price.value),
            label=level.level_type.display_name,
        ).to_dict()
    
    def _build_postmarket_structured_data(
        self,
        instrument: Instrument,
        session_date: date,
        current_session: MarketSession,
        levels: List[PriceLevel],
        weekly_high: Price | None,
        weekly_low: Price | None,
        monthly_high: Price | None,
        monthly_low: Price | None,
    ) -> Dict[str, Any]:
        """Build structured data for post-market posts."""
        return PostMarketStructuredData(
            instrument=instrument.value,
            session_date=session_date.isoformat(),
            session=self._build_session_data(current_session),
            levels=[self._build_level_data(lvl) for lvl in levels],
            weekly_high=float(weekly_high.value) if weekly_high else None,
            weekly_low=float(weekly_low.value) if weekly_low else None,
            monthly_high=float(monthly_high.value) if monthly_high else None,
            monthly_low=float(monthly_low.value) if monthly_low else None,
        ).to_dict()
    
    def _build_premarket_structured_data(
        self,
        instrument: Instrument,
        session_date: date,
        prior_session: MarketSession | None,
        levels: List[PriceLevel],
        overnight_high: Price | None,
        overnight_low: Price | None,
        weekly_open: Price | None,
        weekly_high: Price | None,
        weekly_low: Price | None,
        monthly_high: Price | None,
        monthly_low: Price | None,
    ) -> Dict[str, Any]:
        """Build structured data for pre-market posts."""
        return PreMarketStructuredData(
            instrument=instrument.value,
            session_date=session_date.isoformat(),
            prior_session=self._build_session_data(prior_session) if prior_session else None,
            levels=[self._build_level_data(lvl) for lvl in levels],
            overnight_high=float(overnight_high.value) if overnight_high else None,
            overnight_low=float(overnight_low.value) if overnight_low else None,
            weekly_open=float(weekly_open.value) if weekly_open else None,
            weekly_high=float(weekly_high.value) if weekly_high else None,
            weekly_low=float(weekly_low.value) if weekly_low else None,
            monthly_high=float(monthly_high.value) if monthly_high else None,
            monthly_low=float(monthly_low.value) if monthly_low else None,
        ).to_dict()
    
    def _build_weekly_structured_data(
        self,
        instrument: Instrument,
        weekly_session: WeeklySession,
        monthly_high: Price | None,
        monthly_low: Price | None,
        prior_week_close: Price | None,
    ) -> Dict[str, Any]:
        """Build structured data for weekly recap posts."""
        daily_sessions = [
            self._build_session_data(session)
            for session in weekly_session.daily_sessions
        ]
        
        levels = [
            PriceLevelData("weekly_open", float(weekly_session.open_price.value), "Weekly Open").to_dict(),
            PriceLevelData("weekly_high", float(weekly_session.high_price.value), "Weekly High").to_dict(),
            PriceLevelData("weekly_low", float(weekly_session.low_price.value), "Weekly Low").to_dict(),
            PriceLevelData("weekly_close", float(weekly_session.close_price.value), "Weekly Close").to_dict(),
        ]
        
        return WeeklyRecapStructuredData(
            instrument=instrument.value,
            week_start_date=weekly_session.week_start_date.isoformat(),
            week_end_date=weekly_session.week_end_date.isoformat(),
            weekly_ohlc=SessionOHLC(
                open=float(weekly_session.open_price.value),
                high=float(weekly_session.high_price.value),
                low=float(weekly_session.low_price.value),
                close=float(weekly_session.close_price.value),
                volume=weekly_session.total_volume,
            ).to_dict(),
            change_points=float(weekly_session.change_points),
            change_percent=float(weekly_session.change_percent.value),
            daily_sessions=daily_sessions,
            levels=levels,
            monthly_high=float(monthly_high.value) if monthly_high else None,
            monthly_low=float(monthly_low.value) if monthly_low else None,
            prior_week_close=float(prior_week_close.value) if prior_week_close else None,
        ).to_dict()
    
    # =========================================================================
    # Post Generation Methods
    # =========================================================================
    
    def generate_premarket_posts(
        self,
        session_date: date,
        instruments: List[Instrument] | None = None,
        auto_publish: bool = False,
    ) -> List[PipelineResult]:
        """Generate pre-market posts for all or specified instruments.
        
        Args:
            session_date: Trading date for analysis
            instruments: Specific instruments to generate (defaults to all)
            auto_publish: Whether to publish immediately
            
        Returns:
            List of PipelineResult for each instrument
        """
        instruments = instruments or list(Instrument)
        results = []
        
        for instrument in instruments:
            logger.info(f"Generating pre-market post for {instrument.short_name}")
            
            try:
                result = self._generate_premarket_post(
                    instrument=instrument,
                    session_date=session_date,
                    auto_publish=auto_publish,
                )
                results.append(result)
                
            except Exception as e:
                logger.error(
                    f"Pipeline failed for {instrument.short_name}: {e}"
                )
                results.append(PipelineResult(
                    success=False,
                    instrument=instrument,
                    post_type=PostType.PRE_MARKET,
                    error_message=str(e),
                ))
        
        return results
    
    def generate_postmarket_posts(
        self,
        session_date: date,
        instruments: List[Instrument] | None = None,
        auto_publish: bool = False,
    ) -> List[PipelineResult]:
        """Generate post-market recap posts for all or specified instruments.
        
        Args:
            session_date: Trading date for recap
            instruments: Specific instruments to generate (defaults to all)
            auto_publish: Whether to publish immediately
            
        Returns:
            List of PipelineResult for each instrument
        """
        instruments = instruments or list(Instrument)
        results = []
        
        for instrument in instruments:
            logger.info(f"Generating post-market post for {instrument.short_name}")
            
            try:
                result = self._generate_postmarket_post(
                    instrument=instrument,
                    session_date=session_date,
                    auto_publish=auto_publish,
                )
                results.append(result)
                
            except Exception as e:
                logger.error(
                    f"Pipeline failed for {instrument.short_name}: {e}"
                )
                results.append(PipelineResult(
                    success=False,
                    instrument=instrument,
                    post_type=PostType.POST_MARKET,
                    error_message=str(e),
                ))
        
        return results
    
    def generate_weekly_recaps(
        self,
        week_start_date: date,
        instruments: List[Instrument] | None = None,
        auto_publish: bool = False,
    ) -> List[PipelineResult]:
        """Generate weekly recap posts for all or specified instruments.
        
        Args:
            week_start_date: Monday of the week to recap
            instruments: Specific instruments to generate (defaults to all)
            auto_publish: Whether to publish immediately
            
        Returns:
            List of PipelineResult for each instrument
        """
        instruments = instruments or list(Instrument)
        results = []
        
        for instrument in instruments:
            logger.info(f"Generating weekly recap for {instrument.short_name}")
            
            try:
                result = self._generate_weekly_recap(
                    instrument=instrument,
                    week_start_date=week_start_date,
                    auto_publish=auto_publish,
                )
                results.append(result)
                
            except Exception as e:
                logger.error(
                    f"Pipeline failed for {instrument.short_name}: {e}"
                )
                results.append(PipelineResult(
                    success=False,
                    instrument=instrument,
                    post_type=PostType.WEEKLY_RECAP,
                    error_message=str(e),
                ))
        
        return results
    
    def _generate_premarket_post(
        self,
        instrument: Instrument,
        session_date: date,
        auto_publish: bool,
    ) -> PipelineResult:
        """Generate a single pre-market post.
        
        Args:
            instrument: Futures instrument
            session_date: Trading date
            auto_publish: Whether to publish immediately
            
        Returns:
            PipelineResult with outcome
        """
        # Check if post already exists
        if self._post_repo.exists_for_date_and_type(
            instrument, PostType.PRE_MARKET, session_date
        ):
            return PipelineResult(
                success=False,
                instrument=instrument,
                post_type=PostType.PRE_MARKET,
                error_message="Pre-market post already exists for this date",
            )
        
        # Get prior trading day
        prior_date = self._get_prior_trading_day(session_date)
        
        # Auto-fetch prior session data from Databento if enabled and needed
        if self._auto_fetch and self._sync_service:
            try:
                self._sync_service.ensure_prior_session(instrument, session_date)
            except DataFetchError as e:
                return PipelineResult(
                    success=False,
                    instrument=instrument,
                    post_type=PostType.PRE_MARKET,
                    error_message=f"Failed to fetch prior session data: {e}",
                )
        
        # Fetch prior session data from local storage
        prior_session = self._session_repo.find_by_instrument_and_date(
            instrument, prior_date
        )
        
        # Fetch or create prior session from market data
        if not prior_session:
            prior_data = self._market_data.fetch_session_data(instrument, prior_date)
            if prior_data:
                prior_session = self._create_session_from_data(prior_data)
                self._session_repo.save(prior_session)
        
        # Fetch overnight data
        overnight_data = self._market_data.fetch_overnight_data(instrument, session_date)
        overnight_high = Price(overnight_data.overnight_high) if overnight_data else None
        overnight_low = Price(overnight_data.overnight_low) if overnight_data else None
        
        # Get prior day's session progression (raw bars for AI context)
        prior_day_progression = None
        if self._intraday_analyzer:
            try:
                prior_day_progression = self._intraday_analyzer.analyze_session(
                    instrument=instrument.short_name,
                    session_date=prior_date,
                    include_raw_bars=True,
                )
            except Exception as e:
                logger.warning(f"Could not get prior day progression: {e}")
        
        # Get overnight session raw bars for current date
        overnight_bars = []
        if self._intraday_analyzer:
            try:
                overnight_bars = self._intraday_analyzer.get_overnight_bars(
                    instrument=instrument.short_name,
                    session_date=session_date,
                )
            except Exception as e:
                logger.warning(f"Could not get overnight bars: {e}")
        
        # Get weekly context
        week_start = self._get_week_start(session_date)
        weekly_open, weekly_high, weekly_low = self._get_weekly_context(
            instrument, week_start, session_date
        )
        
        # Get monthly context
        monthly_high, monthly_low = self._get_monthly_context(instrument, session_date)
        
        # Get existing price levels
        price_levels = self._level_repo.find_by_instrument_and_date(
            instrument, prior_date
        )
        
        # Generate content
        gen_result, gen_log = self._generator.generate_premarket_post(
            instrument=instrument,
            session_date=session_date,
            prior_session=prior_session,
            overnight_high=overnight_high,
            overnight_low=overnight_low,
            weekly_open=weekly_open,
            weekly_high=weekly_high,
            weekly_low=weekly_low,
            monthly_high=monthly_high,
            monthly_low=monthly_low,
            price_levels=price_levels,
            prior_day_progression=prior_day_progression,
            overnight_bars=overnight_bars,
        )
        
        if not gen_result.success:
            return PipelineResult(
                success=False,
                instrument=instrument,
                post_type=PostType.PRE_MARKET,
                error_message=gen_result.error_message,
                duration_seconds=gen_result.duration_seconds,
            )
        
        # Review step (multi-model validation)
        reviewed = False
        review_approved = False
        review_quality_score = 0.0
        review_issues = 0
        final_title = gen_result.title
        final_content = gen_result.content
        final_meta = gen_result.meta_description
        total_tokens = gen_result.input_tokens + gen_result.output_tokens
        total_duration = gen_result.duration_seconds
        
        if not self._skip_review:
            # Build price level references for accuracy check
            level_refs = [
                f"{level.level_type.value}: {level.price.value}"
                for level in price_levels
            ] if price_levels else None
            
            review_result, review_log = self._reviewer.review_content(
                title=gen_result.title,
                content=gen_result.content,
                meta_description=gen_result.meta_description,
                instrument=instrument,
                post_type=PostType.PRE_MARKET,
                price_levels_mentioned=level_refs,
            )
            
            reviewed = True
            review_approved = review_result.approved
            review_quality_score = review_result.quality_score
            review_issues = len(review_result.issues)
            total_tokens += review_result.input_tokens + review_result.output_tokens
            total_duration += review_result.duration_seconds
            
            if not review_result.approved and review_result.issues:
                # Critical issues found - don't save
                logger.warning(
                    f"Content rejected by reviewer for {instrument.short_name}: "
                    f"{review_result.issues}"
                )
                issue_descriptions = [
                    i.get('text', i.get('description', str(i))) if isinstance(i, dict) else str(i)
                    for i in review_result.issues
                ]
                return PipelineResult(
                    success=False,
                    instrument=instrument,
                    post_type=PostType.PRE_MARKET,
                    error_message=f"Review failed: {'; '.join(issue_descriptions)}",
                    tokens_used=total_tokens,
                    duration_seconds=total_duration,
                    reviewed=True,
                    review_approved=False,
                    review_quality_score=review_quality_score,
                    review_issues=review_issues,
                )
            
            # Use revised content from reviewer
            final_title = review_result.revised_title
            final_content = review_result.revised_content
            final_meta = review_result.revised_meta_description
            
            logger.info(
                f"Content approved by reviewer for {instrument.short_name}: "
                f"score={review_quality_score:.1f}"
            )
        
        # Build structured data for JSON storage
        structured_data = self._build_premarket_structured_data(
            instrument=instrument,
            session_date=session_date,
            prior_session=prior_session,
            overnight_high=overnight_high,
            overnight_low=overnight_low,
            levels=price_levels,
            weekly_open=weekly_open,
            weekly_high=weekly_high,
            weekly_low=weekly_low,
            monthly_high=monthly_high,
            monthly_low=monthly_low,
        )
        
        # Create and save the post
        post = TradingPost(
            instrument=instrument,
            post_type=PostType.PRE_MARKET,
            title=final_title,
            content=final_content,
            session_date=session_date,
            meta_description=final_meta,
            market_session=prior_session,
            price_levels=price_levels,
            structured_data=structured_data,
        )
        
        if auto_publish:
            post.publish()
        
        self._post_repo.save(post)
        
        # Publish domain event
        self._event_bus.publish(TradingPostGenerated(
            post_id=post.id,
            instrument=instrument,
            post_type=PostType.PRE_MARKET,
            session_date=session_date,
            title=post.title,
        ))
        
        if auto_publish:
            self._event_bus.publish(TradingPostPublished(
                post_id=post.id,
                instrument=instrument,
                post_type=PostType.PRE_MARKET,
                title=post.title,
                slug=str(post.slug),
            ))
        
        return PipelineResult(
            success=True,
            post_id=post.id,
            post_type=PostType.PRE_MARKET,
            instrument=instrument,
            title=post.title,
            published=auto_publish,
            tokens_used=total_tokens,
            duration_seconds=total_duration,
            reviewed=reviewed,
            review_approved=review_approved,
            review_quality_score=review_quality_score,
            review_issues=review_issues,
        )
    
    def _generate_postmarket_post(
        self,
        instrument: Instrument,
        session_date: date,
        auto_publish: bool,
    ) -> PipelineResult:
        """Generate a single post-market recap post.
        
        Args:
            instrument: Futures instrument
            session_date: Trading date
            auto_publish: Whether to publish immediately
            
        Returns:
            PipelineResult with outcome
        """
        # Check if post already exists
        if self._post_repo.exists_for_date_and_type(
            instrument, PostType.POST_MARKET, session_date
        ):
            return PipelineResult(
                success=False,
                instrument=instrument,
                post_type=PostType.POST_MARKET,
                error_message="Post-market recap already exists for this date",
            )
        
        # Auto-fetch data from Databento if enabled and needed
        if self._auto_fetch and self._sync_service:
            try:
                self._sync_service.ensure_session_data(instrument, session_date)
            except DataFetchError as e:
                return PipelineResult(
                    success=False,
                    instrument=instrument,
                    post_type=PostType.POST_MARKET,
                    error_message=f"Failed to fetch market data: {e}",
                )
        
        # Fetch current session data from local storage
        session_data = self._market_data.fetch_session_data(instrument, session_date)
        if not session_data:
            short_symbol = instrument.value.replace('=F', '')
            return PipelineResult(
                success=False,
                instrument=instrument,
                post_type=PostType.POST_MARKET,
                error_message=(
                    f"No intraday data available for {instrument.value} on {session_date}. "
                    f"Run: python manage.py fetch_intraday_bars --date {session_date} "
                    f"--instruments {short_symbol}"
                ),
            )
        
        current_session = self._create_session_from_data(session_data)
        self._session_repo.save(current_session)
        
        # Save price levels for this session
        session_levels = current_session.get_price_levels()
        for level in session_levels:
            self._level_repo.save(level)
        
        # Get pre-market levels (from morning's analysis)
        prior_levels = self._level_repo.find_by_instrument_and_date(
            instrument, self._get_prior_trading_day(session_date)
        )
        
        # Get weekly context
        week_start = self._get_week_start(session_date)
        _, weekly_high, weekly_low = self._get_weekly_context(
            instrument, week_start, session_date
        )
        
        # Get monthly context
        monthly_high, monthly_low = self._get_monthly_context(instrument, session_date)
        
        # Get intraday progression analysis if we have 1m bar data
        intraday_progression: Optional[SessionProgression] = None
        if self._intraday_analyzer.has_data_for_session(instrument.value, session_date):
            prior_close: Optional[Decimal] = None
            if current_session.prior_close:
                prior_close = Decimal(str(current_session.prior_close.value))
            intraday_progression = self._intraday_analyzer.analyze_session(
                instrument=instrument.value,
                session_date=session_date,
                prior_close=prior_close,
            )
            if intraday_progression:
                logger.info(f"Using intraday progression for {instrument.value} on {session_date}")
        
        # Generate content
        gen_result, gen_log = self._generator.generate_postmarket_post(
            instrument=instrument,
            session_date=session_date,
            current_session=current_session,
            prior_levels=prior_levels,
            weekly_high=weekly_high,
            weekly_low=weekly_low,
            monthly_high=monthly_high,
            monthly_low=monthly_low,
            intraday_progression=intraday_progression,
        )
        
        if not gen_result.success:
            return PipelineResult(
                success=False,
                instrument=instrument,
                post_type=PostType.POST_MARKET,
                error_message=gen_result.error_message,
                duration_seconds=gen_result.duration_seconds,
            )
        
        # Review step (multi-model validation)
        reviewed = False
        review_approved = False
        review_quality_score = 0.0
        review_issues = 0
        final_title = gen_result.title
        final_content = gen_result.content
        final_meta = gen_result.meta_description
        total_tokens = gen_result.input_tokens + gen_result.output_tokens
        total_duration = gen_result.duration_seconds
        
        if not self._skip_review:
            # Build price level references for accuracy check
            level_refs = [
                f"{level.level_type.value}: {level.price.value}"
                for level in session_levels
            ] if session_levels else None
            
            # Build intraday summary for reviewer verification
            intraday_summary: Optional[str] = None
            if intraday_progression:
                high_info = intraday_progression.session_high_info
                low_info = intraday_progression.session_low_info
                high_str = f"{high_info.price} at {high_info.time_et}" if high_info else "N/A"
                low_str = f"{low_info.price} at {low_info.time_et}" if low_info else "N/A"
                intraday_summary = (
                    f"Session High: {high_str}\n"
                    f"Session Low: {low_str}\n"
                    f"AM Volume: {intraday_progression.am_volume_pct:.1f}%, PM Volume: {intraday_progression.pm_volume_pct:.1f}%\n"
                    f"Total 1m bars: {len(intraday_progression.rth_bars)}"
                )
            
            review_result, review_log = self._reviewer.review_content(
                title=gen_result.title,
                content=gen_result.content,
                meta_description=gen_result.meta_description,
                instrument=instrument,
                post_type=PostType.POST_MARKET,
                price_levels_mentioned=level_refs,
                intraday_data_provided=intraday_progression is not None,
                intraday_summary=intraday_summary,
            )
            
            reviewed = True
            review_approved = review_result.approved
            review_quality_score = review_result.quality_score
            review_issues = len(review_result.issues)
            total_tokens += review_result.input_tokens + review_result.output_tokens
            total_duration += review_result.duration_seconds
            
            if not review_result.approved and review_result.issues:
                issue_descriptions = [
                    i.get('text', i.get('description', str(i))) if isinstance(i, dict) else str(i)
                    for i in review_result.issues
                ]
                logger.warning(
                    f"Content rejected by reviewer for {instrument.short_name}: "
                    f"{issue_descriptions}"
                )
                return PipelineResult(
                    success=False,
                    instrument=instrument,
                    post_type=PostType.POST_MARKET,
                    error_message=f"Review failed: {'; '.join(issue_descriptions)}",
                    tokens_used=total_tokens,
                    duration_seconds=total_duration,
                    reviewed=True,
                    review_approved=False,
                    review_quality_score=review_quality_score,
                    review_issues=review_issues,
                )
            
            final_title = review_result.revised_title
            final_content = review_result.revised_content
            final_meta = review_result.revised_meta_description
            
            logger.info(
                f"Content approved by reviewer for {instrument.short_name}: "
                f"score={review_quality_score:.1f}"
            )
        
        # Build structured data for JSON storage
        structured_data = self._build_postmarket_structured_data(
            instrument=instrument,
            session_date=session_date,
            current_session=current_session,
            levels=session_levels,
            weekly_high=weekly_high,
            weekly_low=weekly_low,
            monthly_high=monthly_high,
            monthly_low=monthly_low,
        )
        
        # Create and save the post
        post = TradingPost(
            instrument=instrument,
            post_type=PostType.POST_MARKET,
            title=final_title,
            content=final_content,
            session_date=session_date,
            meta_description=final_meta,
            market_session=current_session,
            price_levels=session_levels,
            structured_data=structured_data,
        )
        
        if auto_publish:
            post.publish()
        
        self._post_repo.save(post)
        
        # Publish domain events
        self._event_bus.publish(TradingPostGenerated(
            post_id=post.id,
            instrument=instrument,
            post_type=PostType.POST_MARKET,
            session_date=session_date,
            title=post.title,
        ))
        
        if auto_publish:
            self._event_bus.publish(TradingPostPublished(
                post_id=post.id,
                instrument=instrument,
                post_type=PostType.POST_MARKET,
                title=post.title,
                slug=str(post.slug),
            ))
        
        return PipelineResult(
            success=True,
            post_id=post.id,
            post_type=PostType.POST_MARKET,
            instrument=instrument,
            title=post.title,
            published=auto_publish,
            tokens_used=total_tokens,
            duration_seconds=total_duration,
            reviewed=reviewed,
            review_approved=review_approved,
            review_quality_score=review_quality_score,
            review_issues=review_issues,
        )
    
    def _generate_weekly_recap(
        self,
        instrument: Instrument,
        week_start_date: date,
        auto_publish: bool,
    ) -> PipelineResult:
        """Generate a single weekly recap post.
        
        Args:
            instrument: Futures instrument
            week_start_date: Monday of the week
            auto_publish: Whether to publish immediately
            
        Returns:
            PipelineResult with outcome
        """
        # Check if post already exists
        if self._post_repo.exists_for_date_and_type(
            instrument, PostType.WEEKLY_RECAP, week_start_date
        ):
            return PipelineResult(
                success=False,
                instrument=instrument,
                post_type=PostType.WEEKLY_RECAP,
                error_message="Weekly recap already exists for this week",
            )
        
        week_end_date = week_start_date + timedelta(days=4)
        
        # Auto-fetch week data from Databento if enabled and needed
        if self._auto_fetch and self._sync_service:
            try:
                self._sync_service.ensure_week_data(instrument, week_start_date)
            except DataFetchError as e:
                return PipelineResult(
                    success=False,
                    instrument=instrument,
                    post_type=PostType.WEEKLY_RECAP,
                    error_message=f"Failed to fetch weekly data: {e}",
                )
        
        # Get or create weekly session from local storage
        weekly_session = self._weekly_repo.find_by_instrument_and_week(
            instrument, week_start_date
        )
        
        if not weekly_session:
            # Fetch weekly data and create session
            weekly_data = self._market_data.fetch_weekly_data(
                instrument, week_start_date
            )
            
            if not weekly_data:
                return PipelineResult(
                    success=False,
                    instrument=instrument,
                    post_type=PostType.WEEKLY_RECAP,
                    error_message="Could not fetch weekly data",
                )
            
            # Create daily sessions
            daily_sessions = []
            for session_data in weekly_data:
                session = self._create_session_from_data(session_data)
                self._session_repo.save(session)
                daily_sessions.append(session)
            
            # Create weekly session
            weekly_session = WeeklySession(
                instrument=instrument,
                week_start_date=week_start_date,
                week_end_date=week_end_date,
                daily_sessions=daily_sessions,
            )
            self._weekly_repo.save(weekly_session)
        
        # Get prior week close
        prior_week_start = week_start_date - timedelta(days=7)
        prior_weekly = self._weekly_repo.find_by_instrument_and_week(
            instrument, prior_week_start
        )
        prior_week_close = prior_weekly.close_price if prior_weekly else None
        
        # Get monthly context
        monthly_high, monthly_low = self._get_monthly_context(
            instrument, week_start_date
        )
        
        # Generate content
        gen_result, gen_log = self._generator.generate_weekly_recap_post(
            instrument=instrument,
            weekly_session=weekly_session,
            prior_week_close=prior_week_close,
            monthly_high=monthly_high,
            monthly_low=monthly_low,
        )
        
        if not gen_result.success:
            return PipelineResult(
                success=False,
                instrument=instrument,
                post_type=PostType.WEEKLY_RECAP,
                error_message=gen_result.error_message,
                duration_seconds=gen_result.duration_seconds,
            )
        
        # Review step (multi-model validation)
        reviewed = False
        review_approved = False
        review_quality_score = 0.0
        review_issues = 0
        final_title = gen_result.title
        final_content = gen_result.content
        final_meta = gen_result.meta_description
        total_tokens = gen_result.input_tokens + gen_result.output_tokens
        total_duration = gen_result.duration_seconds
        weekly_levels = weekly_session.get_price_levels()
        
        if not self._skip_review:
            # Build price level references for accuracy check
            level_refs = [
                f"{level.level_type.value}: {level.price.value}"
                for level in weekly_levels
            ] if weekly_levels else None
            
            review_result, review_log = self._reviewer.review_content(
                title=gen_result.title,
                content=gen_result.content,
                meta_description=gen_result.meta_description,
                instrument=instrument,
                post_type=PostType.WEEKLY_RECAP,
                price_levels_mentioned=level_refs,
            )
            
            reviewed = True
            review_approved = review_result.approved
            review_quality_score = review_result.quality_score
            review_issues = len(review_result.issues)
            total_tokens += review_result.input_tokens + review_result.output_tokens
            total_duration += review_result.duration_seconds
            
            if not review_result.approved and review_result.issues:
                issue_descriptions = [
                    i.get('text', i.get('description', str(i))) if isinstance(i, dict) else str(i)
                    for i in review_result.issues
                ]
                logger.warning(
                    f"Content rejected by reviewer for {instrument.short_name}: "
                    f"{issue_descriptions}"
                )
                return PipelineResult(
                    success=False,
                    instrument=instrument,
                    post_type=PostType.WEEKLY_RECAP,
                    error_message=f"Review failed: {'; '.join(issue_descriptions)}",
                    tokens_used=total_tokens,
                    duration_seconds=total_duration,
                    reviewed=True,
                    review_approved=False,
                    review_quality_score=review_quality_score,
                    review_issues=review_issues,
                )
            
            final_title = review_result.revised_title
            final_content = review_result.revised_content
            final_meta = review_result.revised_meta_description
            
            logger.info(
                f"Content approved by reviewer for {instrument.short_name}: "
                f"score={review_quality_score:.1f}"
            )
        
        # Build structured data for JSON storage
        structured_data = self._build_weekly_structured_data(
            instrument=instrument,
            weekly_session=weekly_session,
            monthly_high=monthly_high,
            monthly_low=monthly_low,
            prior_week_close=prior_week_close,
        )
        
        # Create and save the post
        post = TradingPost(
            instrument=instrument,
            post_type=PostType.WEEKLY_RECAP,
            title=final_title,
            content=final_content,
            session_date=week_start_date,
            meta_description=final_meta,
            weekly_session=weekly_session,
            price_levels=weekly_levels,
            structured_data=structured_data,
        )
        
        if auto_publish:
            post.publish()
        
        self._post_repo.save(post)
        
        # Publish domain events
        self._event_bus.publish(TradingPostGenerated(
            post_id=post.id,
            instrument=instrument,
            post_type=PostType.WEEKLY_RECAP,
            session_date=week_start_date,
            title=post.title,
        ))
        
        if auto_publish:
            self._event_bus.publish(TradingPostPublished(
                post_id=post.id,
                instrument=instrument,
                post_type=PostType.WEEKLY_RECAP,
                title=post.title,
                slug=str(post.slug),
            ))
        
        return PipelineResult(
            success=True,
            post_id=post.id,
            post_type=PostType.WEEKLY_RECAP,
            instrument=instrument,
            title=post.title,
            published=auto_publish,
            tokens_used=total_tokens,
            duration_seconds=total_duration,
            reviewed=reviewed,
            review_approved=review_approved,
            review_quality_score=review_quality_score,
            review_issues=review_issues,
        )
    
    def _create_session_from_data(self, data: SessionData) -> MarketSession:
        """Create a MarketSession entity from raw session data.
        
        Args:
            data: Raw session data from yfinance
            
        Returns:
            MarketSession entity
        """
        return MarketSession(
            instrument=data.instrument,
            session_date=data.session_date,
            open_price=Price(data.open_price),
            high_price=Price(data.high_price),
            low_price=Price(data.low_price),
            close_price=Price(data.close_price),
            volume=data.volume,
            prior_close=Price(data.prior_close) if data.prior_close else None,
        )
    
    def _get_prior_trading_day(self, session_date: date) -> date:
        """Get the prior trading day (skip weekends).
        
        Args:
            session_date: Reference date
            
        Returns:
            Prior trading day date
        """
        prior = session_date - timedelta(days=1)
        
        # Skip weekends (0=Monday, 6=Sunday)
        while prior.weekday() >= 5:
            prior = prior - timedelta(days=1)
        
        return prior
    
    def _get_week_start(self, session_date: date) -> date:
        """Get the Monday of the week containing session_date.
        
        Args:
            session_date: Any date in the week
            
        Returns:
            Monday of that week
        """
        days_since_monday = session_date.weekday()
        return session_date - timedelta(days=days_since_monday)
    
    def _get_weekly_context(
        self,
        instrument: Instrument,
        week_start: date,
        up_to_date: date,
    ) -> Tuple[Price | None, Price | None, Price | None]:
        """Get weekly open, high, low up to the specified date.
        
        Args:
            instrument: Futures instrument
            week_start: Monday of the week
            up_to_date: Date to calculate context up to
            
        Returns:
            Tuple of (weekly_open, weekly_high, weekly_low)
        """
        sessions = self._session_repo.find_by_date_range(
            instrument, week_start, up_to_date
        )
        
        if not sessions:
            # Try to fetch from market data
            weekly_data = self._market_data.fetch_weekly_data(instrument, week_start)
            if weekly_data:
                # Filter to up_to_date
                weekly_data = [d for d in weekly_data if d.session_date <= up_to_date]
                if weekly_data:
                    weekly_open = Price(weekly_data[0].open_price)
                    weekly_high = Price(max(d.high_price for d in weekly_data))
                    weekly_low = Price(min(d.low_price for d in weekly_data))
                    return weekly_open, weekly_high, weekly_low
            return None, None, None
        
        sessions = sorted(sessions, key=lambda s: s.session_date)
        weekly_open = sessions[0].open_price
        weekly_high = Price(max(s.high_price.value for s in sessions))
        weekly_low = Price(min(s.low_price.value for s in sessions))
        
        return weekly_open, weekly_high, weekly_low
    
    def _get_monthly_context(
        self,
        instrument: Instrument,
        reference_date: date,
    ) -> Tuple[Price | None, Price | None]:
        """Get monthly high and low for the month containing reference_date.
        
        Args:
            instrument: Futures instrument
            reference_date: Any date in the month
            
        Returns:
            Tuple of (monthly_high, monthly_low)
        """
        result = self._market_data.fetch_monthly_high_low(instrument, reference_date)
        
        if result:
            monthly_high, monthly_low = result
            return Price(monthly_high), Price(monthly_low)
        
        return None, None


def get_trading_content_pipeline(auto_fetch_data: bool = True) -> TradingContentPipeline:
    """Factory function for TradingContentPipeline.
    
    Wires up all dependencies and returns a configured pipeline instance.
    Uses LocalMarketDataService to read from stored intraday bars.
    When auto_fetch_data is True, missing data is automatically fetched
    from Databento before generation.
    
    Args:
        auto_fetch_data: Whether to automatically fetch missing data
            from Databento. Defaults to True for convenience.
    
    Returns:
        Configured TradingContentPipeline instance
    """
    from apps.trading.infrastructure.repositories import (
        DjangoTradingPostRepository,
        DjangoMarketSessionRepository,
        DjangoWeeklySessionRepository,
        DjangoPriceLevelRepository,
    )
    from apps.trading.infrastructure.market_data.local_market_data import LocalMarketDataService
    from apps.trading.infrastructure.market_data.sync_service import MarketDataSyncService
    from apps.shared.infrastructure.event_bus import get_event_bus
    
    # Create sync service for auto-fetching (only if enabled)
    sync_service = MarketDataSyncService() if auto_fetch_data else None
    
    return TradingContentPipeline(
        post_repository=DjangoTradingPostRepository(),
        session_repository=DjangoMarketSessionRepository(),
        weekly_repository=DjangoWeeklySessionRepository(),
        level_repository=DjangoPriceLevelRepository(),
        event_bus=get_event_bus(),
        market_data_service=LocalMarketDataService(),
        generator=TradingPostGeneratorService(),
        sync_service=sync_service,
        auto_fetch_data=auto_fetch_data,
    )
