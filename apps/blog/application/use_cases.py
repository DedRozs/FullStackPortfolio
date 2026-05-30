from __future__ import annotations

import logging

from django.contrib.auth import get_user_model

from ..domain.exceptions import PostNotFoundError
from ..domain.repositories import IPostRepository, ITagRepository
from ..domain.services import RelatedPostFinder
from ..domain.value_objects import PostStatus, Slug
from .dtos import PostDetailDTO, PostFeedItemDTO, PostListItemDTO, TagDTO

logger = logging.getLogger(__name__)


def _build_tag_dtos(tag_repo: ITagRepository, tag_ids: list) -> tuple:
    if not tag_ids:
        return ()
    tags = tag_repo.find_by_ids(tag_ids)
    return tuple(TagDTO(id=t.id, name=t.name, slug=str(t.slug)) for t in tags)


def _resolve_author_name(author_id: int) -> str:
    User = get_user_model()
    try:
        user = User.objects.get(pk=author_id)
        return user.get_full_name() or user.username
    except User.DoesNotExist:
        return 'Unknown Author'


def _post_to_list_dto(post, tag_repo: ITagRepository) -> PostListItemDTO:
    image_url = str(post.featured_image_path) if post.featured_image_path else None
    return PostListItemDTO(
        id=post.id,
        title=post.title,
        slug=str(post.slug),
        excerpt=post.excerpt.text,
        reading_time_minutes=post.reading_time.minutes,
        published_at=post.published_at,
        author_display_name=_resolve_author_name(post.author_id),
        featured_image_url=image_url,
        tags=_build_tag_dtos(tag_repo, post.tag_ids),
    )


class ListPublishedPosts:
    def __init__(self, post_repo: IPostRepository, tag_repo: ITagRepository) -> None:
        self._posts = post_repo
        self._tags = tag_repo

    def execute(self, page: int, page_size: int) -> list:
        posts = self._posts.find_published(page=page, page_size=page_size)
        return [_post_to_list_dto(p, self._tags) for p in posts]


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
        related_dtos = tuple(_post_to_list_dto(r, self._tags) for r in related)
        image_url = str(post.featured_image_path) if post.featured_image_path else None
        return PostDetailDTO(
            id=post.id,
            title=post.title,
            slug=str(post.slug),
            excerpt=post.excerpt.text,
            body=post.body,
            reading_time_minutes=post.reading_time.minutes,
            published_at=post.published_at,
            author_display_name=_resolve_author_name(post.author_id),
            featured_image_url=image_url,
            tags=_build_tag_dtos(self._tags, post.tag_ids),
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
