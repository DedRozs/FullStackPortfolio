from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TagDTO:
    id: int
    name: str
    slug: str


@dataclass(frozen=True)
class PostListItemDTO:
    id: int
    title: str
    slug: str
    excerpt: str
    reading_time_minutes: int
    published_at: datetime
    author_display_name: str
    featured_image_url: Optional[str]
    tags: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class PostDetailDTO:
    id: int
    title: str
    slug: str
    excerpt: str
    body: str
    reading_time_minutes: int
    published_at: datetime
    author_display_name: str
    featured_image_url: Optional[str]
    tags: tuple = field(default_factory=tuple)
    related_posts: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class PostFeedItemDTO:
    title: str
    slug: str
    excerpt: str
    published_at: datetime
