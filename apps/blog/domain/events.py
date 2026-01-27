"""Domain events for the Blog bounded context."""
from dataclasses import dataclass, field
from typing import Any, List
from uuid import UUID

from apps.shared.domain.events import DomainEvent


@dataclass(frozen=True)
class BlogPostCreated(DomainEvent):
    """Event raised when a new blog post is created."""
    post_id: UUID = field(default_factory=lambda: None)  # type: ignore
    title: str = ""
    author_name: str = ""
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'post_id': str(self.post_id),
            'title': self.title,
            'author_name': self.author_name,
        }


@dataclass(frozen=True)
class BlogPostPublished(DomainEvent):
    """Event raised when a blog post is published."""
    post_id: UUID = field(default_factory=lambda: None)  # type: ignore
    title: str = ""
    slug: str = ""
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'post_id': str(self.post_id),
            'title': self.title,
            'slug': self.slug,
        }


@dataclass(frozen=True)
class BlogPostUpdated(DomainEvent):
    """Event raised when a blog post is updated."""
    post_id: UUID = field(default_factory=lambda: None)  # type: ignore
    title: str = ""
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'post_id': str(self.post_id),
            'title': self.title,
        }
