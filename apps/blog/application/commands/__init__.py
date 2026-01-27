"""Commands for the Blog bounded context."""
from dataclasses import dataclass
from typing import List
from uuid import UUID


@dataclass(frozen=True)
class CreateBlogPostCommand:
    """Command to create a new blog post."""
    title: str
    content: str  # Markdown content
    author_name: str
    tags: List[str] = None  # type: ignore
    featured_image_url: str | None = None
    meta_description: str | None = None
    
    def __post_init__(self):
        # Handle mutable default
        object.__setattr__(self, 'tags', self.tags or [])


@dataclass(frozen=True)
class UpdateBlogPostCommand:
    """Command to update an existing blog post."""
    post_id: UUID
    title: str
    content: str
    tags: List[str] = None  # type: ignore
    featured_image_url: str | None = None
    meta_description: str | None = None
    
    def __post_init__(self):
        object.__setattr__(self, 'tags', self.tags or [])


@dataclass(frozen=True)
class PublishBlogPostCommand:
    """Command to publish a blog post."""
    post_id: UUID


@dataclass(frozen=True)
class UnpublishBlogPostCommand:
    """Command to unpublish a blog post."""
    post_id: UUID


@dataclass(frozen=True)
class DeleteBlogPostCommand:
    """Command to delete a blog post."""
    post_id: UUID
