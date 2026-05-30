import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .domain.services import ReadingTimeCalculator
from .models import Post

logger = logging.getLogger(__name__)

_reading_time_calculator = ReadingTimeCalculator()


@receiver(pre_save, sender=Post)
def compute_reading_time(sender, instance: Post, **kwargs) -> None:
    """Recompute reading time whenever the Post body changes before save."""
    if instance.body:
        rt = _reading_time_calculator.calculate(instance.body)
        instance.reading_time_minutes = rt.minutes


@receiver(post_save, sender=Post)
def schedule_vectorization(sender, instance: Post, **kwargs) -> None:
    """Enqueue a Django Q2 task to sync the Supabase embedding after every save."""
    try:
        from django_q.tasks import async_task

        from .application.vectorization_task import delete_post_vector, vectorize_post

        if instance.status == Post.PUBLISHED:
            async_task(
                vectorize_post,
                instance.pk,
                task_name=f'vectorize-post-{instance.pk}',
            )
        else:
            async_task(
                delete_post_vector,
                instance.pk,
                task_name=f'delete-vector-post-{instance.pk}',
            )
    except Exception:
        logger.exception(
            'schedule_vectorization: failed to enqueue task for post %d', instance.pk
        )
