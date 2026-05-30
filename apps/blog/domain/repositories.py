from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .entities import Post, Tag
from .value_objects import Slug


class IPostRepository(ABC):
    @abstractmethod
    def save(self, post: Post) -> None:
        """Persist a new or updated Post. Raises SlugConflictError on slug collision."""

    @abstractmethod
    def find_by_id(self, post_id: int) -> Optional[Post]:
        """Return the Post with the given ID, or None."""

    @abstractmethod
    def find_by_slug(self, slug: Slug) -> Optional[Post]:
        """Return the Post whose slug matches, or None."""

    @abstractmethod
    def find_published(self, page: int, page_size: int) -> list:
        """Return a paginated list of PUBLISHED Posts ordered by published_at desc."""

    @abstractmethod
    def find_by_tag(self, tag_id: int, page: int, page_size: int) -> list:
        """Return a paginated list of PUBLISHED Posts for the given tag_id."""

    @abstractmethod
    def find_published_by_tag_ids(
        self, tag_ids: list, exclude_post_id: int, limit: int
    ) -> list:
        """Return up to limit PUBLISHED Posts matching any tag_id, excluding exclude_post_id."""

    @abstractmethod
    def find_all_published(self) -> list:
        """Return all PUBLISHED Posts ordered by published_at desc (for RSS)."""

    @abstractmethod
    def delete(self, post_id: int) -> None:
        """Delete the Post. Raises PostNotFoundError if not found."""

    @abstractmethod
    def count_published(self) -> int:
        """Return the total count of PUBLISHED Posts."""


class ITagRepository(ABC):
    @abstractmethod
    def save(self, tag: Tag) -> None:
        """Persist a new or updated Tag. Raises TagNameConflictError on name collision."""

    @abstractmethod
    def find_by_id(self, tag_id: int) -> Optional[Tag]:
        """Return the Tag with the given ID, or None."""

    @abstractmethod
    def find_by_slug(self, slug: Slug) -> Optional[Tag]:
        """Return the Tag whose slug matches, or None."""

    @abstractmethod
    def find_all(self) -> list:
        """Return all Tags ordered by name ascending."""

    @abstractmethod
    def find_by_ids(self, tag_ids: list) -> list:
        """Return Tags matching the given IDs."""
