from __future__ import annotations

import logging
from typing import Optional

from django.db.models import Count

from ..domain.entities import Post as PostEntity
from ..domain.entities import Tag as TagEntity
from ..domain.exceptions import PostNotFoundError, SlugConflictError, TagNameConflictError
from ..domain.repositories import IPostRepository, ITagRepository
from ..domain.value_objects import (
    Excerpt,
    FeaturedImagePath,
    PostStatus,
    ReadingTime,
    Slug,
)
from ..models import Post as PostModel
from ..models import Tag as TagModel

logger = logging.getLogger(__name__)


def _model_to_post_entity(post: PostModel) -> PostEntity:
    featured = None
    if post.featured_image:
        featured = FeaturedImagePath(str(post.featured_image))
    return PostEntity(
        id=post.pk,
        title=post.title,
        slug=Slug(post.slug),
        excerpt=Excerpt(post.excerpt),
        body=post.body,
        author_id=post.author_id,
        reading_time=ReadingTime(minutes=post.reading_time_minutes or 1),
        status=PostStatus(post.status),
        published_at=post.published_at,
        featured_image_path=featured,
        tag_ids=list(post.tags.values_list('id', flat=True)),
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


def _model_to_tag_entity(tag: TagModel) -> TagEntity:
    return TagEntity(id=tag.pk, name=tag.name, slug=Slug(tag.slug))


class DjangoPostRepository(IPostRepository):
    def _qs(self):
        return PostModel.objects.select_related('author').prefetch_related('tags')

    def save(self, post: PostEntity) -> None:
        try:
            if post.id is None:
                obj = PostModel(
                    title=post.title,
                    slug=str(post.slug),
                    excerpt=post.excerpt.text,
                    body=post.body,
                    author_id=post.author_id,
                    reading_time_minutes=post.reading_time.minutes,
                    status=post.status.value,
                    published_at=post.published_at,
                    featured_image=(
                        str(post.featured_image_path) if post.featured_image_path else None
                    ),
                )
                obj.save()
                post.id = obj.pk
            else:
                PostModel.objects.filter(pk=post.id).update(
                    title=post.title,
                    slug=str(post.slug),
                    excerpt=post.excerpt.text,
                    body=post.body,
                    author_id=post.author_id,
                    reading_time_minutes=post.reading_time.minutes,
                    status=post.status.value,
                    published_at=post.published_at,
                )
            obj = PostModel.objects.get(pk=post.id)
            obj.tags.set(post.tag_ids)
        except Exception as exc:
            msg = str(exc).lower()
            if 'unique' in msg and 'slug' in msg:
                raise SlugConflictError(str(post.slug)) from exc
            raise

    def find_by_id(self, post_id: int) -> Optional[PostEntity]:
        try:
            return _model_to_post_entity(self._qs().get(pk=post_id))
        except PostModel.DoesNotExist:
            return None

    def find_by_slug(self, slug: Slug) -> Optional[PostEntity]:
        try:
            return _model_to_post_entity(self._qs().get(slug=str(slug)))
        except PostModel.DoesNotExist:
            return None

    def find_published(self, page: int, page_size: int) -> list:
        offset = (page - 1) * page_size
        qs = self._qs().filter(status=PostModel.PUBLISHED).order_by('-published_at')
        return [_model_to_post_entity(p) for p in qs[offset : offset + page_size]]

    def find_by_tag(self, tag_id: int, page: int, page_size: int) -> list:
        offset = (page - 1) * page_size
        qs = (
            self._qs()
            .filter(status=PostModel.PUBLISHED, tags__id=tag_id)
            .order_by('-published_at')
        )
        return [_model_to_post_entity(p) for p in qs[offset : offset + page_size]]

    def find_published_by_tag_ids(
        self, tag_ids: list, exclude_post_id: int, limit: int
    ) -> list:
        qs = (
            self._qs()
            .filter(status=PostModel.PUBLISHED, tags__id__in=tag_ids)
            .exclude(pk=exclude_post_id)
            .annotate(shared_count=Count('tags'))
            .order_by('-shared_count', '-published_at')
            .distinct()[:limit]
        )
        return [_model_to_post_entity(p) for p in qs]

    def find_all_published(self) -> list:
        qs = self._qs().filter(status=PostModel.PUBLISHED).order_by('-published_at')
        return [_model_to_post_entity(p) for p in qs]

    def delete(self, post_id: int) -> None:
        deleted, _ = PostModel.objects.filter(pk=post_id).delete()
        if deleted == 0:
            raise PostNotFoundError(post_id)

    def count_published(self) -> int:
        return PostModel.objects.filter(status=PostModel.PUBLISHED).count()


class DjangoTagRepository(ITagRepository):
    def save(self, tag: TagEntity) -> None:
        try:
            if tag.id is None:
                obj = TagModel(name=tag.name, slug=str(tag.slug))
                obj.save()
                tag.id = obj.pk
            else:
                TagModel.objects.filter(pk=tag.id).update(
                    name=tag.name, slug=str(tag.slug)
                )
        except Exception as exc:
            if 'unique' in str(exc).lower():
                raise TagNameConflictError(tag.name) from exc
            raise

    def find_by_id(self, tag_id: int) -> Optional[TagEntity]:
        try:
            return _model_to_tag_entity(TagModel.objects.get(pk=tag_id))
        except TagModel.DoesNotExist:
            return None

    def find_by_slug(self, slug: Slug) -> Optional[TagEntity]:
        try:
            return _model_to_tag_entity(TagModel.objects.get(slug=str(slug)))
        except TagModel.DoesNotExist:
            return None

    def find_all(self) -> list:
        return [_model_to_tag_entity(t) for t in TagModel.objects.order_by('name')]

    def find_by_ids(self, tag_ids: list) -> list:
        return [
            _model_to_tag_entity(t)
            for t in TagModel.objects.filter(pk__in=tag_ids)
        ]
