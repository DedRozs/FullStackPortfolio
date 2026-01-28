"""Queries for the Blog bounded context."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetPostByIdQuery:
    """Query to get a specific post by ID."""
    post_id: UUID


@dataclass(frozen=True)
class GetPostBySlugQuery:
    """Query to get a specific post by slug."""
    slug: str


@dataclass(frozen=True)
class GetPublishedPostsQuery:
    """Query to get published posts with pagination."""
    limit: int = 10
    offset: int = 0


@dataclass(frozen=True)
class GetPostsByTagQuery:
    """Query to get posts by tag."""
    tag: str
    limit: int = 10
    offset: int = 0


@dataclass(frozen=True)
class GetAllPostsQuery:
    """Query to get all posts (admin use)."""
    status: str | None = None  # "draft", "published", "archived"


@dataclass(frozen=True)
class GetAllTagsQuery:
    """Query to get all unique tags."""
    pass


@dataclass(frozen=True)
class SearchPostsQuery:
    """Query to search posts by title and content."""
    search_term: str
    tag: str | None = None
    limit: int = 10
    offset: int = 0
