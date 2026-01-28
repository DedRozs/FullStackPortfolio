"""Application services for the Blog bounded context."""
from dataclasses import dataclass
from typing import List
from uuid import UUID

from apps.blog.domain.entities import BlogPost, PostStatus
from apps.blog.domain.events import BlogPostCreated, BlogPostPublished, BlogPostUpdated
from apps.blog.domain.repositories import BlogPostRepository
from apps.blog.domain.value_objects import Slug, Tag, PostContent
from apps.blog.application.commands import (
    CreateBlogPostCommand,
    UpdateBlogPostCommand,
    PublishBlogPostCommand,
    UnpublishBlogPostCommand,
    DeleteBlogPostCommand,
)
from apps.blog.application.queries import (
    GetPostByIdQuery,
    GetPostBySlugQuery,
    GetPublishedPostsQuery,
    GetPostsByTagQuery,
    GetAllPostsQuery,
    GetAllTagsQuery,
    SearchPostsQuery,
)
from apps.shared.infrastructure.event_bus import EventBus


class BlogApplicationService:
    """Application service for Blog use cases."""
    
    def __init__(
        self,
        repository: BlogPostRepository,
        event_bus: EventBus,
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus
    
    # Command handlers
    
    def create_post(self, command: CreateBlogPostCommand) -> UUID:
        """Create a new blog post."""
        content = PostContent(command.content)
        tags = [Tag(t) for t in command.tags]
        
        post = BlogPost(
            title=command.title,
            content=content,
            author_name=command.author_name,
            tags=tags,
            featured_image_url=command.featured_image_url,
            meta_description=command.meta_description,
        )
        
        self._repository.save(post)
        
        event = BlogPostCreated(
            post_id=post.id,
            title=post.title,
            author_name=post.author_name,
        )
        self._event_bus.publish(event)
        
        return post.id
    
    def update_post(self, command: UpdateBlogPostCommand) -> None:
        """Update an existing blog post."""
        post = self._repository.find_by_id(command.post_id)
        if post is None:
            raise ValueError(f"Post not found: {command.post_id}")
        
        content = PostContent(command.content)
        tags = [Tag(t) for t in command.tags]
        
        post.update_content(command.title, content, tags)
        post.featured_image_url = command.featured_image_url
        post.meta_description = command.meta_description
        
        self._repository.save(post)
        
        event = BlogPostUpdated(post_id=post.id, title=post.title)
        self._event_bus.publish(event)
    
    def publish_post(self, command: PublishBlogPostCommand) -> None:
        """Publish a blog post."""
        post = self._repository.find_by_id(command.post_id)
        if post is None:
            raise ValueError(f"Post not found: {command.post_id}")
        
        post.publish()
        self._repository.save(post)
        
        event = BlogPostPublished(
            post_id=post.id,
            title=post.title,
            slug=str(post.slug),
        )
        self._event_bus.publish(event)
    
    def unpublish_post(self, command: UnpublishBlogPostCommand) -> None:
        """Unpublish a blog post."""
        post = self._repository.find_by_id(command.post_id)
        if post is None:
            raise ValueError(f"Post not found: {command.post_id}")
        
        post.unpublish()
        self._repository.save(post)
    
    def delete_post(self, command: DeleteBlogPostCommand) -> None:
        """Delete a blog post."""
        post = self._repository.find_by_id(command.post_id)
        if post is None:
            raise ValueError(f"Post not found: {command.post_id}")
        
        self._repository.delete(post)
    
    # Query handlers
    
    def get_post_by_id(self, query: GetPostByIdQuery) -> BlogPost | None:
        """Get a post by ID."""
        return self._repository.find_by_id(query.post_id)
    
    def get_post_by_slug(self, query: GetPostBySlugQuery) -> BlogPost | None:
        """Get a post by slug."""
        try:
            slug = Slug(query.slug)
            return self._repository.find_by_slug(slug)
        except ValueError:
            return None
    
    def get_published_posts(self, query: GetPublishedPostsQuery) -> List[BlogPost]:
        """Get published posts with pagination."""
        return self._repository.find_all_published(
            limit=query.limit,
            offset=query.offset,
        )
    
    def get_posts_by_tag(self, query: GetPostsByTagQuery) -> List[BlogPost]:
        """Get posts by tag."""
        try:
            tag = Tag(query.tag)
            return self._repository.find_by_tag(tag, query.limit, query.offset)
        except ValueError:
            return []
    
    def get_all_posts(self, query: GetAllPostsQuery) -> List[BlogPost]:
        """Get all posts (admin use)."""
        status = None
        if query.status:
            status = PostStatus(query.status)
        return self._repository.find_all(status)
    
    def get_all_tags(self, query: GetAllTagsQuery) -> List[Tag]:
        """Get all unique tags."""
        return self._repository.get_all_tags()
    
    def get_total_published_count(self) -> int:
        """Get count of published posts."""
        return self._repository.count_published()
    
    def search_posts(self, query: SearchPostsQuery) -> List[BlogPost]:
        """Search posts by title and content."""
        tag = None
        if query.tag:
            try:
                tag = Tag(query.tag)
            except ValueError:
                pass
        return self._repository.search(
            search_term=query.search_term,
            tag=tag,
            limit=query.limit,
            offset=query.offset,
        )
    
    def count_search_results(self, search_term: str, tag: str | None = None) -> int:
        """Count search results."""
        tag_obj = None
        if tag:
            try:
                tag_obj = Tag(tag)
            except ValueError:
                pass
        return self._repository.count_search_results(search_term, tag_obj)


@dataclass
class BlogPostDTO:
    """Data Transfer Object for BlogPost."""
    id: str
    title: str
    slug: str
    excerpt: str
    content: str
    tags: List[str]
    status: str
    author_name: str
    reading_time: int
    created_at: str
    updated_at: str
    published_at: str | None
    featured_image_url: str | None
    meta_description: str | None
    
    @classmethod
    def from_entity(cls, entity: BlogPost) -> 'BlogPostDTO':
        """Create DTO from domain entity."""
        return cls(
            id=str(entity.id),
            title=entity.title,
            slug=str(entity.slug),
            excerpt=entity.excerpt,
            content=entity.content.markdown,
            tags=[str(t) for t in entity.tags],
            status=entity.status.value,
            author_name=entity.author_name,
            reading_time=entity.reading_time,
            created_at=entity.created_at.isoformat(),
            updated_at=entity.updated_at.isoformat(),
            published_at=entity.published_at.isoformat() if entity.published_at else None,
            featured_image_url=entity.featured_image_url,
            meta_description=entity.meta_description,
        )


@dataclass
class BlogPostSummaryDTO:
    """Lightweight DTO for post listings."""
    id: str
    title: str
    slug: str
    excerpt: str
    tags: List[str]
    author_name: str
    reading_time: int
    published_at: str | None
    featured_image_url: str | None
    
    @classmethod
    def from_entity(cls, entity: BlogPost) -> 'BlogPostSummaryDTO':
        """Create summary DTO from domain entity."""
        return cls(
            id=str(entity.id),
            title=entity.title,
            slug=str(entity.slug),
            excerpt=entity.excerpt,
            tags=[str(t) for t in entity.tags],
            author_name=entity.author_name,
            reading_time=entity.reading_time,
            published_at=entity.published_at.isoformat() if entity.published_at else None,
            featured_image_url=entity.featured_image_url,
        )
