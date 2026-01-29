"""
Django-Q2 scheduled tasks for automated trading content generation.

These tasks run on a schedule to:
1. Fetch daily intraday bar data after market close (PREVIOUS DAY due to data delay)
2. Generate pre-market briefings before RTH opens
3. Generate post-market recaps after settlement (PREVIOUS DAY due to data delay)
4. Generate weekly recaps on Saturdays

IMPORTANT: Databento subscription has ~24-hour data delay for CME data.
- Data for Monday becomes available Tuesday evening
- Post-market recaps are generated for YESTERDAY (the day we just got data for)
- Pre-market briefings use prior day data (always available)

Schedule (all times Eastern):
- 5:30 PM ET: Fetch intraday bars for YESTERDAY
- 6:00 PM ET: Generate post-market recaps for YESTERDAY
- 6:30 AM ET: Generate pre-market briefings for TODAY
- 9:00 AM ET Saturday: Generate weekly recaps
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List

from django.conf import settings

from apps.trading.application.content_generation.pipeline import (
    TradingContentPipeline,
    PipelineResult,
)
from apps.trading.infrastructure.repositories import (
    DjangoTradingPostRepository,
    DjangoMarketSessionRepository,
    DjangoWeeklySessionRepository,
    DjangoPriceLevelRepository,
)
from apps.shared.infrastructure.event_bus import get_event_bus
from apps.trading.domain.value_objects import Instrument, PostType

logger = logging.getLogger(__name__)

# All four index futures
ALL_INSTRUMENTS = [Instrument.ES, Instrument.NQ, Instrument.RTY, Instrument.YM]


def _get_pipeline(skip_review: bool = False) -> TradingContentPipeline:
    """Factory function to create a configured TradingContentPipeline."""
    return TradingContentPipeline(
        post_repository=DjangoTradingPostRepository(),
        session_repository=DjangoMarketSessionRepository(),
        weekly_repository=DjangoWeeklySessionRepository(),
        level_repository=DjangoPriceLevelRepository(),
        event_bus=get_event_bus(),
        openai_api_key=getattr(settings, 'OPENAI_API_KEY', ''),
        skip_review=skip_review,
    )


def fetch_daily_intraday_bars() -> dict:
    """
    Fetch intraday bar data for all instruments for YESTERDAY's session.
    
    This task should run after market settlement (5:30 PM ET).
    Due to ~24-hour Databento data delay, we fetch YESTERDAY's data.
    It fetches 1-minute bars from Databento for ES, NQ, RTY, and YM.
    
    Returns:
        dict: Summary of fetched data
    """
    from apps.trading.infrastructure.market_data.databento_client import DatabentoClient
    
    logger.info("Starting daily intraday bar fetch task")
    
    try:
        client = DatabentoClient()
        # Fetch YESTERDAY's data due to ~24-hour delay
        yesterday = date.today() - timedelta(days=1)
        
        # Skip weekends
        if yesterday.weekday() >= 5:
            logger.info(f"Skipping {yesterday} - weekend")
            return {
                'success': True,
                'date': str(yesterday),
                'skipped': True,
                'reason': 'weekend',
            }
        
        results = {}
        total_bars = 0
        
        for instrument in ALL_INSTRUMENTS:
            try:
                bars_stored = client.fetch_and_store_bars(
                    instrument=instrument.value,
                    session_date=yesterday,
                    include_overnight=True,
                )
                results[instrument.short_name] = {
                    'success': True,
                    'bars': bars_stored,
                }
                total_bars += bars_stored
                logger.info(f"Fetched {bars_stored} bars for {instrument.short_name}")
            except Exception as e:
                results[instrument.short_name] = {
                    'success': False,
                    'error': str(e),
                }
                logger.error(f"Failed to fetch bars for {instrument.short_name}: {e}")
        
        return {
            'success': all(r['success'] for r in results.values()),
            'date': str(yesterday),
            'total_bars': total_bars,
            'instruments': results,
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch intraday bars: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


def generate_premarket_posts() -> dict:
    """
    Generate pre-market briefings for all instruments for TODAY.
    
    This task should run before RTH opens (6:30 AM ET).
    Pre-market uses prior day data (which is available due to 24-hour delay).
    It generates and auto-publishes pre-market analysis for ES, NQ, RTY, YM.
    
    Returns:
        dict: Summary of generated posts
    """
    logger.info("Starting pre-market post generation task")
    
    try:
        pipeline = _get_pipeline()
        today = date.today()
        
        # Skip weekends
        if today.weekday() >= 5:
            logger.info(f"Skipping {today} - weekend")
            return {
                'success': True,
                'date': str(today),
                'skipped': True,
                'reason': 'weekend',
            }
        
        results: List[PipelineResult] = pipeline.generate_premarket_posts(
            session_date=today,
            instruments=ALL_INSTRUMENTS,
            auto_publish=True,
        )
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        result = {
            'success': len(failed) == 0,
            'date': str(today),
            'post_type': 'pre_market',
            'generated': len(successful),
            'failed': len(failed),
            'posts': [
                {
                    'instrument': r.instrument.short_name,
                    'post_id': str(r.post_id) if r.post_id else None,
                    'success': r.success,
                    'error': r.error_message if not r.success else None,
                }
                for r in results
            ],
        }
        
        logger.info(
            f"Pre-market generation complete: {len(successful)} success, {len(failed)} failed"
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate pre-market posts: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


def generate_postmarket_posts() -> dict:
    """
    Generate post-market recaps for all instruments for YESTERDAY's session.
    
    This task should run after settlement (6:00 PM ET).
    Due to ~24-hour Databento data delay, we generate recaps for YESTERDAY.
    It generates and auto-publishes post-market recaps for ES, NQ, RTY, YM.
    
    Returns:
        dict: Summary of generated posts
    """
    logger.info("Starting post-market post generation task")
    
    try:
        pipeline = _get_pipeline()
        # Generate for YESTERDAY due to data delay
        yesterday = date.today() - timedelta(days=1)
        
        # Skip weekends
        if yesterday.weekday() >= 5:
            logger.info(f"Skipping {yesterday} - weekend")
            return {
                'success': True,
                'date': str(yesterday),
                'skipped': True,
                'reason': 'weekend',
            }
        
        results: List[PipelineResult] = pipeline.generate_postmarket_posts(
            session_date=yesterday,
            instruments=ALL_INSTRUMENTS,
            auto_publish=True,
        )
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        result = {
            'success': len(failed) == 0,
            'date': str(yesterday),
            'post_type': 'post_market',
            'generated': len(successful),
            'failed': len(failed),
            'posts': [
                {
                    'instrument': r.instrument.short_name,
                    'post_id': str(r.post_id) if r.post_id else None,
                    'success': r.success,
                    'error': r.error_message if not r.success else None,
                }
                for r in results
            ],
        }
        
        logger.info(
            f"Post-market generation complete: {len(successful)} success, {len(failed)} failed"
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate post-market posts: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


def generate_weekly_recaps() -> dict:
    """
    Generate weekly recap posts for all instruments.
    
    This task should run on Saturday morning (9:00 AM ET).
    It generates and auto-publishes weekly recaps for ES, NQ, RTY, YM.
    
    Returns:
        dict: Summary of generated posts
    """
    logger.info("Starting weekly recap generation task")
    
    try:
        pipeline = _get_pipeline()
        
        # Find the Monday of this past week
        today = date.today()
        days_since_monday = today.weekday()
        if days_since_monday == 5:  # Saturday
            week_start = today - timedelta(days=5)  # Previous Monday
        elif days_since_monday == 6:  # Sunday
            week_start = today - timedelta(days=6)  # Previous Monday
        else:
            # Running on a weekday - use the current week's Monday
            week_start = today - timedelta(days=days_since_monday)
        
        results: List[PipelineResult] = pipeline.generate_weekly_recap_posts(
            week_start=week_start,
            instruments=ALL_INSTRUMENTS,
            auto_publish=True,
        )
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        result = {
            'success': len(failed) == 0,
            'week_start': str(week_start),
            'post_type': 'weekly_recap',
            'generated': len(successful),
            'failed': len(failed),
            'posts': [
                {
                    'instrument': r.instrument.short_name,
                    'post_id': str(r.post_id) if r.post_id else None,
                    'success': r.success,
                    'error': r.error_message if not r.success else None,
                }
                for r in results
            ],
        }
        
        logger.info(
            f"Weekly recap generation complete: {len(successful)} success, {len(failed)} failed"
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate weekly recaps: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


def trading_health_check() -> dict:
    """
    Simple health check task to verify the trading task system is working.
    
    Returns:
        dict: Health check status
    """
    from apps.trading.infrastructure.models import TradingPostModel, MarketSessionModel
    
    try:
        post_count = TradingPostModel.objects.count()
        session_count = MarketSessionModel.objects.count()
        
        return {
            'success': True,
            'trading_posts': post_count,
            'market_sessions': session_count,
            'message': 'Trading task system is operational',
        }
    except Exception as e:
        logger.error(f"Trading health check failed: {e}")
        return {
            'success': False,
            'error': str(e),
        }
