from __future__ import annotations

import logging

from django.contrib.auth import get_user_model

from ..domain.exceptions import PostNotFoundError
from ..domain.repositories import IPostRepository, ITagRepository
from ..domain.services import RelatedPostFinder
from ..domain.value_objects import PostStatus, Slug
from .dtos import PostDetailDTO, PostFeedItemDTO, PostListItemDTO, TagDTO

logger = logging.getLogger(__name__)


def _resolve_author_names(author_ids: list) -> dict:
    """Returns {author_id: display_name} for all given IDs in one query."""
    User = get_user_model()
    users = User.objects.filter(pk__in=set(author_ids))
    return {u.pk: (u.get_full_name() or u.username) for u in users}


def _build_tag_dto_map(tag_repo: ITagRepository, all_tag_ids: list) -> dict:
    """Returns {tag_id: TagDTO} for all given IDs in one query."""
    if not all_tag_ids:
        return {}
    tags = tag_repo.find_by_ids(list(set(all_tag_ids)))
    return {t.id: TagDTO(id=t.id, name=t.name, slug=str(t.slug)) for t in tags}


def _post_to_list_dto(post, author_name: str, tag_dto_map: dict) -> PostListItemDTO:
    image_url = str(post.featured_image_path) if post.featured_image_path else None
    return PostListItemDTO(
        id=post.id,
        title=post.title,
        slug=str(post.slug),
        excerpt=post.excerpt.text,
        reading_time_minutes=post.reading_time.minutes,
        published_at=post.published_at,
        author_display_name=author_name,
        featured_image_url=image_url,
        tags=tuple(tag_dto_map[tid] for tid in post.tag_ids if tid in tag_dto_map),
    )


class ListPublishedPosts:
    def __init__(self, post_repo: IPostRepository, tag_repo: ITagRepository) -> None:
        self._posts = post_repo
        self._tags = tag_repo

    def execute(self, page: int, page_size: int) -> list:
        posts = self._posts.find_published(page=page, page_size=page_size)
        if not posts:
            return []
        author_name_map = _resolve_author_names([p.author_id for p in posts])
        tag_dto_map = _build_tag_dto_map(self._tags, [tid for p in posts for tid in p.tag_ids])
        return [
            _post_to_list_dto(p, author_name_map.get(p.author_id, 'Unknown Author'), tag_dto_map)
            for p in posts
        ]


class GetPostBySlug:
    def __init__(self, post_repo: IPostRepository, tag_repo: ITagRepository) -> None:
        self._posts = post_repo
        self._tags = tag_repo
        self._related_finder = RelatedPostFinder(post_repo)

    def execute(self, slug: str, request_user_is_staff: bool) -> PostDetailDTO:
        post = self._posts.find_by_slug(Slug(slug))
        if post is None:
            raise PostNotFoundError(f'No post found for slug: {slug!r}')
        if post.status != PostStatus.PUBLISHED and not request_user_is_staff:
            raise PostNotFoundError(f'Post {slug!r} is not published.')
        related = self._related_finder.find_related(post, limit=3)
        all_posts = [post, *related]
        author_name_map = _resolve_author_names([p.author_id for p in all_posts])
        all_tag_ids = [tid for p in all_posts for tid in p.tag_ids]
        tag_dto_map = _build_tag_dto_map(self._tags, all_tag_ids)
        related_dtos = tuple(
            _post_to_list_dto(r, author_name_map.get(r.author_id, 'Unknown Author'), tag_dto_map)
            for r in related
        )
        image_url = str(post.featured_image_path) if post.featured_image_path else None
        return PostDetailDTO(
            id=post.id,
            title=post.title,
            slug=str(post.slug),
            excerpt=post.excerpt.text,
            body=post.body,
            reading_time_minutes=post.reading_time.minutes,
            published_at=post.published_at,
            author_display_name=author_name_map.get(post.author_id, 'Unknown Author'),
            featured_image_url=image_url,
            tags=tuple(tag_dto_map[tid] for tid in post.tag_ids if tid in tag_dto_map),
            related_posts=related_dtos,
        )


class ListTags:
    def __init__(self, tag_repo: ITagRepository) -> None:
        self._tags = tag_repo

    def execute(self) -> list:
        tags = self._tags.find_all()
        return [TagDTO(id=t.id, name=t.name, slug=str(t.slug)) for t in tags]


class GetAllPublishedPostsForFeed:
    def __init__(self, post_repo: IPostRepository) -> None:
        self._posts = post_repo

    def execute(self) -> list:
        posts = self._posts.find_all_published()
        return [
            PostFeedItemDTO(
                title=p.title,
                slug=str(p.slug),
                excerpt=p.excerpt.text,
                published_at=p.published_at,
            )
            for p in posts
        ]
