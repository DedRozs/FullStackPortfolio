"""Trading post generator service.

Orchestrates the content generation pipeline for trading blog posts.
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional, TYPE_CHECKING
from uuid import UUID

from django.conf import settings
from django.utils import timezone

from apps.trading.domain.entities import (
    TradingPost,
    TradingPostStatus,
    MarketSession,
    WeeklySession,
    PriceLevel,
)
from apps.trading.domain.value_objects import Instrument, PostType, Price, LevelType
from apps.trading.application.content_generation.prompts.premarket_prompt import (
    PreMarketPromptBuilder,
    PreMarketContext,
)
from apps.trading.application.content_generation.prompts.postmarket_prompt import (
    PostMarketPromptBuilder,
    PostMarketContext,
)

if TYPE_CHECKING:
    from apps.trading.application.intraday_analysis import SessionProgression
from apps.trading.application.content_generation.prompts.weekly_recap_prompt import (
    WeeklyRecapPromptBuilder,
    WeeklyRecapContext,
)


logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of trading post content generation."""
    success: bool
    title: str = ""
    content: str = ""
    meta_description: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    duration_seconds: float = 0.0
    error_message: str = ""


@dataclass
class GenerationLog:
    """Log entry for content generation attempts."""
    post_type: PostType
    instrument: Instrument
    session_date: date
    model_used: str
    input_tokens: int
    output_tokens: int
    duration_seconds: float
    success: bool
    error_message: str = ""
    created_at: datetime = field(default_factory=timezone.now)


class TradingPostGeneratorService:
    """Service for generating trading blog post content using AI.
    
    Handles the generation of pre-market analysis, post-market recaps,
    and weekly recap content using OpenAI models.
    
    Uses different models optimized for each post type:
    - Post-market: o3 (200K context, deep reasoning for 1m bar analysis)
    - Pre-market: o3-mini (lighter context, faster generation)
    - Weekly recap: o3 (processes 5 days of intraday data)
    
    Models are configurable via settings:
    - TRADING_MODEL_POSTMARKET
    - TRADING_MODEL_PREMARKET
    - TRADING_MODEL_WEEKLY
    """
    
    # Default models for each post type
    DEFAULT_MODEL_POSTMARKET = "o3"      # Deep reasoning, large context
    DEFAULT_MODEL_PREMARKET = "o3-mini"  # Lighter, faster
    DEFAULT_MODEL_WEEKLY = "o3"          # Deep reasoning for weekly analysis
    
    def __init__(
        self,
        openai_api_key: str | None = None,
        model_postmarket: str | None = None,
        model_premarket: str | None = None,
        model_weekly: str | None = None,
    ) -> None:
        """Initialize the generator service.
        
        Args:
            openai_api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            model_postmarket: Model for post-market recaps (default: o3)
            model_premarket: Model for pre-market posts (default: o3-mini)
            model_weekly: Model for weekly recaps (default: o3)
        """
        self.openai_api_key = openai_api_key or getattr(settings, 'OPENAI_API_KEY', '')
        
        # Load models from settings with fallback to defaults
        self.model_postmarket = (
            model_postmarket 
            or getattr(settings, 'TRADING_MODEL_POSTMARKET', None)
            or self.DEFAULT_MODEL_POSTMARKET
        )
        self.model_premarket = (
            model_premarket
            or getattr(settings, 'TRADING_MODEL_PREMARKET', None)
            or self.DEFAULT_MODEL_PREMARKET
        )
        self.model_weekly = (
            model_weekly
            or getattr(settings, 'TRADING_MODEL_WEEKLY', None)
            or self.DEFAULT_MODEL_WEEKLY
        )
        
        self._client = None
        
        # Initialize prompt builders
        self._premarket_builder = PreMarketPromptBuilder()
        self._postmarket_builder = PostMarketPromptBuilder()
        self._weekly_builder = WeeklyRecapPromptBuilder()
    
    @property
    def client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.openai_api_key)
        return self._client
    
    def generate_premarket_post(
        self,
        instrument: Instrument,
        session_date: date,
        prior_session: MarketSession | None,
        overnight_high: Price | None = None,
        overnight_low: Price | None = None,
        weekly_open: Price | None = None,
        weekly_high: Price | None = None,
        weekly_low: Price | None = None,
        monthly_high: Price | None = None,
        monthly_low: Price | None = None,
        price_levels: List[PriceLevel] | None = None,
        prior_day_progression: Optional["SessionProgression"] = None,
        overnight_bars: Optional[List] = None,
    ) -> Tuple[GenerationResult, GenerationLog]:
        """Generate pre-market analysis content.
        
        Args:
            instrument: Futures instrument to analyze
            session_date: Trading date for the analysis
            prior_session: Previous trading session data
            overnight_high: Overnight session high price
            overnight_low: Overnight session low price
            weekly_open: Monday's opening price
            weekly_high: Running weekly high
            weekly_low: Running weekly low
            monthly_high: Monthly high
            monthly_low: Monthly low
            price_levels: List of calculated price levels
            prior_day_progression: Full prior day's 1m bar analysis
            overnight_bars: Raw overnight session bars for current day
            
        Returns:
            Tuple of (GenerationResult, GenerationLog)
        """
        context = PreMarketContext(
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
            price_levels=price_levels or [],
            prior_day_progression=prior_day_progression,
            overnight_bars=overnight_bars or [],
        )
        
        prompt = self._premarket_builder.build_prompt(context)
        system_prompt = self._premarket_builder.get_system_prompt()
        
        return self._generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            post_type=PostType.PRE_MARKET,
            instrument=instrument,
            session_date=session_date,
        )
    
    def generate_postmarket_post(
        self,
        instrument: Instrument,
        session_date: date,
        current_session: MarketSession,
        prior_levels: List[PriceLevel] | None = None,
        weekly_high: Price | None = None,
        weekly_low: Price | None = None,
        monthly_high: Price | None = None,
        monthly_low: Price | None = None,
        intraday_progression: Optional["SessionProgression"] = None,
    ) -> Tuple[GenerationResult, GenerationLog]:
        """Generate post-market recap content.
        
        Args:
            instrument: Futures instrument to analyze
            session_date: Trading date for the recap
            current_session: The completed trading session
            prior_levels: Pre-market levels to compare against
            weekly_high: Running weekly high
            weekly_low: Running weekly low
            monthly_high: Monthly high
            monthly_low: Monthly low
            intraday_progression: Optional session progression from 1m bar analysis
            
        Returns:
            Tuple of (GenerationResult, GenerationLog)
        """
        context = PostMarketContext(
            instrument=instrument,
            session_date=session_date,
            current_session=current_session,
            prior_levels=prior_levels or [],
            weekly_high=weekly_high,
            weekly_low=weekly_low,
            monthly_high=monthly_high,
            monthly_low=monthly_low,
            intraday_progression=intraday_progression,
        )
        
        prompt = self._postmarket_builder.build_prompt(context)
        system_prompt = self._postmarket_builder.get_system_prompt()
        
        return self._generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            post_type=PostType.POST_MARKET,
            instrument=instrument,
            session_date=session_date,
        )
    
    def generate_weekly_recap_post(
        self,
        instrument: Instrument,
        weekly_session: WeeklySession,
        prior_week_close: Price | None = None,
        monthly_high: Price | None = None,
        monthly_low: Price | None = None,
    ) -> Tuple[GenerationResult, GenerationLog]:
        """Generate weekly recap content.
        
        Args:
            instrument: Futures instrument to analyze
            weekly_session: Aggregated weekly session data
            prior_week_close: Prior week's closing price
            monthly_high: Monthly high
            monthly_low: Monthly low
            
        Returns:
            Tuple of (GenerationResult, GenerationLog)
        """
        context = WeeklyRecapContext(
            instrument=instrument,
            week_start_date=weekly_session.week_start_date,
            week_end_date=weekly_session.week_end_date,
            weekly_session=weekly_session,
            prior_week_close=prior_week_close,
            monthly_high=monthly_high,
            monthly_low=monthly_low,
        )
        
        prompt = self._weekly_builder.build_prompt(context)
        system_prompt = self._weekly_builder.get_system_prompt()
        
        return self._generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            post_type=PostType.WEEKLY_RECAP,
            instrument=instrument,
            session_date=weekly_session.week_start_date,
        )
    
    def _generate_content(
        self,
        prompt: str,
        system_prompt: str,
        post_type: PostType,
        instrument: Instrument,
        session_date: date,
        model: str | None = None,
    ) -> Tuple[GenerationResult, GenerationLog]:
        """Execute the AI content generation.
        
        Args:
            prompt: User prompt with market data
            system_prompt: System prompt with style guidelines
            post_type: Type of post being generated
            instrument: Instrument being analyzed
            session_date: Session date for the post
            model: Specific model to use (defaults to post-type appropriate model)
            
        Returns:
            Tuple of (GenerationResult, GenerationLog)
        """
        # Select model based on post type if not explicitly provided
        if model is None:
            model = {
                PostType.PRE_MARKET: self.model_premarket,
                PostType.POST_MARKET: self.model_postmarket,
                PostType.WEEKLY_RECAP: self.model_weekly,
            }.get(post_type, self.model_postmarket)
        
        start_time = time.time()
        
        try:
            # Build API call parameters
            # Note: o3/o3-mini are reasoning models and don't use temperature
            api_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "max_completion_tokens": 4000,  # Trading analysis needs detail
            }
            
            # Only add temperature for non-reasoning models
            if not model.startswith("o"):
                api_params["temperature"] = 0.7
            
            response = self.client.chat.completions.create(**api_params)
            
            duration = time.time() - start_time
            raw_content = response.choices[0].message.content or ""
            
            # Parse the response
            parsed = self._parse_response(raw_content)
            
            # Extract token usage with safety checks
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0
            
            result = GenerationResult(
                success=True,
                title=parsed['title'],
                content=parsed['content'],
                meta_description=parsed['meta_description'],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_seconds=duration,
            )
            
            log = GenerationLog(
                post_type=post_type,
                instrument=instrument,
                session_date=session_date,
                model_used=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_seconds=duration,
                success=True,
            )
            
            logger.info(
                f"Generated {post_type.value} post for {instrument.short_name} "
                f"using {model} ({total_tokens} tokens, {duration:.2f}s)"
            )
            
            return result, log
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            logger.error(
                f"Failed to generate {post_type.value} post for "
                f"{instrument.short_name}: {error_msg}"
            )
            
            result = GenerationResult(
                success=False,
                error_message=error_msg,
                duration_seconds=duration,
            )
            
            log = GenerationLog(
                post_type=post_type,
                instrument=instrument,
                session_date=session_date,
                model_used=model,
                input_tokens=0,
                output_tokens=0,
                duration_seconds=duration,
                success=False,
                error_message=error_msg,
            )
            
            return result, log
    
    def _parse_response(self, raw_content: str) -> dict:
        """Parse the AI response into structured content.
        
        Args:
            raw_content: Raw response from AI model
            
        Returns:
            Dictionary with 'title', 'content', and 'meta_description'
        """
        title = ""
        content = ""
        meta_description = ""
        
        # Split by markers
        if "---TITLE---" in raw_content:
            parts = raw_content.split("---TITLE---")
            if len(parts) > 1:
                remaining = parts[1]
                
                if "---CONTENT---" in remaining:
                    title_parts = remaining.split("---CONTENT---")
                    title = title_parts[0].strip()
                    
                    if len(title_parts) > 1:
                        content_remaining = title_parts[1]
                        
                        if "---META_DESCRIPTION---" in content_remaining:
                            content_parts = content_remaining.split("---META_DESCRIPTION---")
                            content = content_parts[0].strip()
                            
                            if len(content_parts) > 1:
                                meta_description = content_parts[1].strip()
                        else:
                            content = content_remaining.strip()
                else:
                    # No content marker, treat rest as content
                    content = remaining.strip()
        else:
            # Fallback: treat entire response as content
            content = raw_content.strip()
            # Try to extract title from first line if it looks like a header
            lines = content.split('\n')
            if lines and lines[0].startswith('#'):
                title = lines[0].lstrip('#').strip()
        
        # Generate defaults if missing
        if not title:
            title = "Trading Analysis"
        
        if not meta_description and content:
            # Use first 160 chars of content
            clean_content = content.replace('#', '').replace('*', '').strip()
            meta_description = clean_content[:157] + "..." if len(clean_content) > 160 else clean_content
        
        return {
            'title': title[:200],  # Max title length
            'content': content,
            'meta_description': meta_description[:300],  # Max meta length
        }


def get_trading_post_generator() -> TradingPostGeneratorService:
    """Factory function for TradingPostGeneratorService.
    
    Returns:
        Configured TradingPostGeneratorService instance
    """
    return TradingPostGeneratorService()
