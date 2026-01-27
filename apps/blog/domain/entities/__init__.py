"""Blog post entity - the aggregate root for this context."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID, uuid4

from apps.blog.domain.value_objects import Slug, Tag, PostContent


class PostStatus(Enum):
    """Publication status of a blog post."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class BlogPost:
    """Aggregate root for blog posts.
    
    Represents a blog article with all its business rules.
    """
    id: UUID
    title: str
    slug: Slug
    content: PostContent
    tags: List[Tag]
    status: PostStatus
    author_name: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    featured_image_url: str | None = None
    meta_description: str | None = None
    
    def __init__(
        self,
        title: str,
        content: PostContent,
        author_name: str,
        tags: List[Tag] | None = None,
        slug: Slug | None = None,
        id: UUID | None = None,
        status: PostStatus = PostStatus.DRAFT,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        published_at: datetime | None = None,
        featured_image_url: str | None = None,
        meta_description: str | None = None,
    ) -> None:
        self.id = id or uuid4()
        self.title = self._validate_title(title)
        self.slug = slug or Slug.from_title(title)
        self.content = content
        self.tags = tags or []
        self.status = status
        self.author_name = author_name
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.published_at = published_at
        self.featured_image_url = featured_image_url
        self.meta_description = meta_description
    
    @staticmethod
    def _validate_title(title: str) -> str:
        """Validate post title."""
        title = title.strip()
        if len(title) < 5:
            raise ValueError("Title must be at least 5 characters")
        if len(title) > 200:
            raise ValueError("Title must not exceed 200 characters")
        return title
    
    def publish(self) -> None:
        """Publish the post."""
        if self.status == PostStatus.PUBLISHED:
            raise ValueError("Post is already published")
        
        self.status = PostStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def unpublish(self) -> None:
        """Move post back to draft."""
        if self.status != PostStatus.PUBLISHED:
            raise ValueError("Post is not published")
        
        self.status = PostStatus.DRAFT
        self.updated_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archive the post."""
        self.status = PostStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
    
    def update_content(self, title: str, content: PostContent, tags: List[Tag]) -> None:
        """Update post content."""
        self.title = self._validate_title(title)
        self.content = content
        self.tags = tags
        self.updated_at = datetime.utcnow()
        
        # Regenerate slug if title changed and not published
        if self.status == PostStatus.DRAFT:
            self.slug = Slug.from_title(title)
    
    def add_tag(self, tag: Tag) -> None:
        """Add a tag to the post."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: Tag) -> None:
        """Remove a tag from the post."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    @property
    def is_published(self) -> bool:
        """Check if post is publicly visible."""
        return self.status == PostStatus.PUBLISHED
    
    @property
    def reading_time(self) -> int:
        """Get estimated reading time in minutes."""
        return self.content.reading_time_minutes
    
    @property
    def excerpt(self) -> str:
        """Get post excerpt."""
        return self.content.excerpt
