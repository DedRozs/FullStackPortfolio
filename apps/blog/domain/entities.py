from __future__ import annotations

from datetime import datetime
from typing import Optional

from .events import PostPublished, PostUnpublished, PostUpdated
from .exceptions import PublishInvariantError
from .value_objects import Excerpt, FeaturedImagePath, PostStatus, ReadingTime, Slug


class Tag:
    def __init__(
        self,
        name: str,
        slug: Slug,
        id: Optional[int] = None,
    ) -> None:
        if not name or len(name) > 100:
            raise ValueError('Tag.name must be non-empty and <= 100 characters.')
        self.id = id
        self.name = name
        self.slug = slug

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tag):
            return NotImplemented
        if self.id is not None and other.id is not None:
            return self.id == other.id
        return self.slug == other.slug

    def __hash__(self) -> int:
        if self.id is not None:
            return hash(self.id)
        return hash(self.slug)

    def __repr__(self) -> str:
        return f'Tag(id={self.id!r}, name={self.name!r})'


class Post:
    def __init__(
        self,
        title: str,
        slug: Slug,
        excerpt: Excerpt,
        body: str,
        author_id: int,
        reading_time: ReadingTime,
        status: PostStatus = PostStatus.DRAFT,
        published_at: Optional[datetime] = None,
        featured_image_path: Optional[FeaturedImagePath] = None,
        tag_ids: Optional[list] = None,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if not title or len(title) > 300:
            raise ValueError('Post.title must be non-empty and <= 300 characters.')
        self.id = id
        self.title = title
        self.slug = slug
        self.excerpt = excerpt
        self.body = body
        self.author_id = author_id
        self.reading_time = reading_time
        self.status = status
        self.published_at = published_at
        self.featured_image_path = featured_image_path
        self.tag_ids: list = list(tag_ids) if tag_ids else []
        self.created_at = created_at
        self.updated_at = updated_at
        self._pending_events: list = []

    # ------------------------------------------------------------------ #
    # State transitions
    # ------------------------------------------------------------------ #

    def publish(self, published_at: datetime) -> None:
        if not self.body:
            raise PublishInvariantError('Cannot publish a Post with an empty body.')
        if not self.title:
            raise PublishInvariantError('Cannot publish a Post with an empty title.')
        if not self.excerpt.text:
            raise PublishInvariantError('Cannot publish a Post with an empty excerpt.')
        self.status = PostStatus.PUBLISHED
        self.published_at = published_at
        self._pending_events.append(
            PostPublished(
                post_id=self.id,
                slug=str(self.slug),
                title=self.title,
                published_at=published_at,
                author_id=self.author_id,
            )
        )

    def unpublish(self) -> None:
        self.status = PostStatus.DRAFT
        self.published_at = None
        if self.id is not None:
            self._pending_events.append(
                PostUnpublished(post_id=self.id, slug=str(self.slug))
            )

    # ------------------------------------------------------------------ #
    # Tag management
    # ------------------------------------------------------------------ #

    def add_tag(self, tag_id: int) -> None:
        if tag_id not in self.tag_ids:
            self.tag_ids.append(tag_id)

    def remove_tag(self, tag_id: int) -> None:
        self.tag_ids = [t for t in self.tag_ids if t != tag_id]

    # ------------------------------------------------------------------ #
    # Event helpers
    # ------------------------------------------------------------------ #

    def mark_updated(self, updated_at: datetime, content_changed: bool) -> None:
        if self.status == PostStatus.PUBLISHED and self.id is not None:
            self._pending_events.append(
                PostUpdated(
                    post_id=self.id,
                    slug=str(self.slug),
                    updated_at=updated_at,
                    content_changed=content_changed,
                )
            )

    def collect_events(self) -> list:
        events = list(self._pending_events)
        self._pending_events.clear()
        return events

    # ------------------------------------------------------------------ #
    # Identity
    # ------------------------------------------------------------------ #

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Post):
            return NotImplemented
        if self.id is not None and other.id is not None:
            return self.id == other.id
        return self.slug == other.slug

    def __hash__(self) -> int:
        if self.id is not None:
            return hash(self.id)
        return hash(self.slug)

    def __repr__(self) -> str:
        return f'Post(id={self.id!r}, slug={self.slug!r}, status={self.status!r})'
