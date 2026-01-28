"""
Django-Q2 scheduled tasks for automated content generation.

These tasks run on a schedule to:
1. Generate new blog post ideas based on trends
2. Process pending ideas through the content pipeline
3. Clean up old/failed ideas
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings

from apps.blog.application.content_generation.pipeline import ContentPipeline
from apps.blog.infrastructure.repositories import (
    DjangoBlogPostRepository,
    DjangoBlogIdeaRepository,
    DjangoContentGenerationLogRepository,
)

if TYPE_CHECKING:
    from apps.blog.domain.entities import BlogPost

logger = logging.getLogger(__name__)


def _get_pipeline() -> ContentPipeline:
    """Factory function to create a configured ContentPipeline."""
    return ContentPipeline(
        idea_repository=DjangoBlogIdeaRepository(),
        post_repository=DjangoBlogPostRepository(),
        log_repository=DjangoContentGenerationLogRepository(),
        openai_api_key=settings.OPENAI_API_KEY,
    )


def generate_daily_ideas() -> dict:
    """
    Generate new blog post ideas based on trending topics.
    
    This task should run once daily (e.g., 6:00 AM).
    It generates ideas and stores them for later processing.
    
    Returns:
        dict: Summary of generated ideas
    """
    logger.info("Starting daily idea generation task")
    
    try:
        pipeline = _get_pipeline()
        ideas = pipeline.generate_ideas_only(num_ideas=3)
        
        result = {
            'success': True,
            'ideas_generated': len(ideas),
            'topics': [idea.topic for idea in ideas],
        }
        logger.info(f"Generated {len(ideas)} new ideas: {result['topics']}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate ideas: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


def process_pending_idea() -> dict:
    """
    Process a single pending idea through the full content pipeline.
    
    This task should run periodically (e.g., every 2 hours).
    It takes one pending idea and processes it through content creation and proofreading.
    
    Returns:
        dict: Summary of processing result
    """
    logger.info("Starting content pipeline task")
    
    try:
        pipeline = _get_pipeline()
        post_ids = pipeline.run_full_pipeline(num_posts=1)
        
        if not post_ids:
            logger.info("No posts created (may need more ideas or quality issues)")
            return {
                'success': True,
                'processed': False,
                'message': 'No posts created - check pending ideas or quality logs',
            }
        
        post_id = post_ids[0]
        logger.info(f"Successfully published post: {post_id}")
        return {
            'success': True,
            'processed': True,
            'published': True,
            'post_id': str(post_id),
        }
            
    except Exception as e:
        logger.error(f"Failed to process idea: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


def cleanup_old_ideas(days_old: int = 30) -> dict:
    """
    Clean up old failed or rejected ideas.
    
    This task should run weekly to prevent database bloat.
    
    Args:
        days_old: Delete ideas older than this many days
        
    Returns:
        dict: Summary of cleanup
    """
    from datetime import timedelta
    from django.utils import timezone
    from apps.blog.infrastructure.models import BlogIdeaModel
    from apps.blog.domain.entities import IdeaStatus
    
    logger.info(f"Starting cleanup of ideas older than {days_old} days")
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Only delete failed or rejected ideas
        queryset = BlogIdeaModel.objects.filter(
            created_at__lt=cutoff_date,
            status__in=[IdeaStatus.FAILED.value, IdeaStatus.REJECTED.value],
        )
        
        count = queryset.count()
        queryset.delete()
        
        logger.info(f"Cleaned up {count} old ideas")
        return {
            'success': True,
            'deleted_count': count,
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup ideas: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
        }


def health_check() -> dict:
    """
    Simple health check task to verify the task system is working.
    
    Returns:
        dict: Health status
    """
    from django.utils import timezone
    
    return {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'openai_configured': bool(settings.OPENAI_API_KEY),
    }
