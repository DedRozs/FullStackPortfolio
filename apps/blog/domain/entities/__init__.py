"""Blog post entity - the aggregate root for this context."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID, uuid4
from django.utils import timezone
from apps.blog.domain.value_objects import Slug, Tag, PostContent


class PostStatus(Enum):
    """Publication status of a blog post."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class IdeaStatus(Enum):
    """Status of a blog idea in the generation pipeline."""
    PENDING = "pending"          # Idea generated, waiting to be processed
    PROCESSING = "processing"    # Currently being processed
    COMPLETED = "completed"      # Successfully turned into a blog post
    REJECTED = "rejected"        # Rejected (duplicate, off-topic, etc.)
    FAILED = "failed"            # Processing failed


class GenerationStage(Enum):
    """Stages in the content generation pipeline."""
    IDEA_GENERATION = "idea_generation"
    CONTENT_CREATION = "content_creation"
    PROOFREADING = "proofreading"
    PUBLISHING = "publishing"


@dataclass
class BlogIdea:
    """Represents a blog post idea for the content generation pipeline.
    
    Tracks ideas from generation through execution to prevent duplicates.
    """
    id: UUID
    topic: str
    keywords: List[str]
    source: str  # 'trends', 'manual', 'ai_suggested'
    status: IdeaStatus
    expertise_area: str  # AI, Full-Stack, Cloud, etc.
    trend_score: float | None  # Popularity score from trends API
    created_at: datetime
    processed_at: datetime | None = None
    blog_post_id: UUID | None = None  # Reference to created post
    rejection_reason: str | None = None
    
    def __init__(
        self,
        topic: str,
        keywords: List[str],
        expertise_area: str,
        source: str = "ai_suggested",
        trend_score: float | None = None,
        id: UUID | None = None,
        status: IdeaStatus = IdeaStatus.PENDING,
        created_at: datetime | None = None,
        processed_at: datetime | None = None,
        blog_post_id: UUID | None = None,
        rejection_reason: str | None = None,
    ) -> None:
        self.id = id or uuid4()
        self.topic = topic
        self.keywords = keywords
        self.expertise_area = expertise_area
        self.source = source
        self.trend_score = trend_score
        self.status = status
        self.created_at = created_at or timezone.now()
        self.processed_at = processed_at
        self.blog_post_id = blog_post_id
        self.rejection_reason = rejection_reason
    
    def start_processing(self) -> None:
        """Mark idea as being processed."""
        if self.status != IdeaStatus.PENDING:
            raise ValueError(f"Cannot process idea in {self.status.value} status")
        self.status = IdeaStatus.PROCESSING
    
    def complete(self, blog_post_id: UUID) -> None:
        """Mark idea as successfully processed."""
        self.status = IdeaStatus.COMPLETED
        self.blog_post_id = blog_post_id
        self.processed_at = timezone.now()
    
    def reject(self, reason: str) -> None:
        """Reject the idea."""
        self.status = IdeaStatus.REJECTED
        self.rejection_reason = reason
        self.processed_at = timezone.now()
    
    def fail(self, reason: str) -> None:
        """Mark processing as failed."""
        self.status = IdeaStatus.FAILED
        self.rejection_reason = reason
        self.processed_at = datetime.utcnow()


@dataclass
class ContentGenerationLog:
    """Audit log for content generation pipeline stages.
    
    Tracks each step in the multi-model generation process.
    """
    id: UUID
    idea_id: UUID
    stage: GenerationStage
    model_used: str  # e.g., 'gpt-4', 'claude-3', etc.
    input_tokens: int
    output_tokens: int
    duration_seconds: float
    success: bool
    output_preview: str | None  # First 500 chars of output
    error_message: str | None
    created_at: datetime
    
    def __init__(
        self,
        idea_id: UUID,
        stage: GenerationStage,
        model_used: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_seconds: float = 0.0,
        success: bool = True,
        output_preview: str | None = None,
        error_message: str | None = None,
        id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id or uuid4()
        self.idea_id = idea_id
        self.stage = stage
        self.model_used = model_used
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.duration_seconds = duration_seconds
        self.success = success
        self.output_preview = output_preview[:500] if output_preview else None
        self.error_message = error_message
        self.created_at = created_at or datetime.utcnow()


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
        self.created_at = created_at or timezone.now()
        self.updated_at = updated_at or timezone.now()
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
        self.published_at = timezone.now()
        self.updated_at = timezone.now()
    
    def unpublish(self) -> None:
        """Move post back to draft."""
        if self.status != PostStatus.PUBLISHED:
            raise ValueError("Post is not published")
        
        self.status = PostStatus.DRAFT
        self.updated_at = timezone.now()
    
    def archive(self) -> None:
        """Archive the post."""
        self.status = PostStatus.ARCHIVED
        self.updated_at = timezone.now()
    
    def update_content(self, title: str, content: PostContent, tags: List[Tag]) -> None:
        """Update post content."""
        self.title = self._validate_title(title)
        self.content = content
        self.tags = tags
        self.updated_at = timezone.now()
        
        # Regenerate slug if title changed and not published
        if self.status == PostStatus.DRAFT:
            self.slug = Slug.from_title(title)
    
    def add_tag(self, tag: Tag) -> None:
        """Add a tag to the post."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = timezone.now()
    
    def remove_tag(self, tag: Tag) -> None:
        """Remove a tag from the post."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = timezone.now()
    
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
