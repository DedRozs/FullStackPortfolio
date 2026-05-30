"""
Django Q2 async tasks for blog post vectorization.

These functions are enqueued by the post_save signal in signals.py and
executed by the Q cluster worker defined in Dockerfile.worker.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def vectorize_post(post_id: int) -> None:
    """
    Compute and upsert the embedding for a published Post.

    Called asynchronously by Django Q2 after a Post is published or updated.
    Failures are logged; the task is not automatically retried in this version.
    """
    from django.apps import apps

    PostModel = apps.get_model('blog', 'Post')
    try:
        post = PostModel.objects.get(pk=post_id)
    except PostModel.DoesNotExist:
        logger.error('vectorize_post: Post %d not found; skipping.', post_id)
        return

    from ..services.embedding_service import PostEmbeddingService

    service = PostEmbeddingService()
    text = f'{post.title}\n\n{post.excerpt}\n\n{post.body}'
    try:
        service.upsert(post_id=post_id, text=text)
        logger.info('vectorize_post: upserted embedding for post %d.', post_id)
    except Exception:
        logger.exception('vectorize_post: failed to upsert embedding for post %d.', post_id)
        raise


def delete_post_vector(post_id: int) -> None:
    """
    Remove the Supabase embedding for an unpublished or deleted Post.

    Called asynchronously by Django Q2 after a Post is unpublished.
    """
    from ..services.embedding_service import PostEmbeddingService

    service = PostEmbeddingService()
    try:
        service.delete(post_id=post_id)
        logger.info('delete_post_vector: deleted embedding for post %d.', post_id)
    except Exception:
        logger.exception(
            'delete_post_vector: failed to delete embedding for post %d.', post_id
        )
