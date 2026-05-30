from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class PostPublished:
    post_id: Optional[int]
    slug: str
    title: str
    published_at: datetime
    author_id: int


@dataclass(frozen=True)
class PostUnpublished:
    post_id: int
    slug: str


@dataclass(frozen=True)
class PostUpdated:
    post_id: int
    slug: str
    updated_at: datetime
    content_changed: bool


@dataclass(frozen=True)
class PostVectorized:
    post_id: int
    slug: str
    dimensions: int
    vectorized_at: datetime


@dataclass(frozen=True)
class PostVectorizationFailed:
    post_id: int
    slug: str
    error_message: str
    failed_at: datetime
