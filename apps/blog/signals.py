import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Post

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Post)
def sync_embedding(sender, instance: Post, **kwargs) -> None:
    """Keep the Supabase embedding in sync whenever a post is saved."""
    from .services.embedding_service import PostEmbeddingService

    service = PostEmbeddingService()
    if instance.published:
        try:
            service.upsert(
                post_id=instance.pk,
                text=f"{instance.title}\n\n{instance.summary}\n\n{instance.body}",
            )
        except Exception:
            logger.exception('Failed to upsert embedding for post %d', instance.pk)
    else:
        try:
            service.delete(instance.pk)
        except Exception:
            logger.exception('Failed to delete embedding for post %d', instance.pk)
