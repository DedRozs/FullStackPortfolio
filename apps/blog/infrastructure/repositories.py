"""Repository implementations for the Blog bounded context."""
from typing import List
from uuid import UUID

from apps.blog.domain.entities import BlogPost, PostStatus
from apps.blog.domain.repositories import BlogPostRepository
from apps.blog.domain.value_objects import Slug, Tag, PostContent
from apps.blog.infrastructure.models import BlogPostModel


class DjangoBlogPostRepository(BlogPostRepository):
    """Django ORM implementation of BlogPostRepository."""
    
    def save(self, post: BlogPost) -> None:
        """Persist a blog post."""
        BlogPostModel.objects.update_or_create(
            id=post.id,
            defaults={
                'title': post.title,
                'slug': str(post.slug),
                'content': post.content.markdown,
                'tags': [str(t) for t in post.tags],
                'status': post.status.value,
                'author_name': post.author_name,
                'featured_image_url': post.featured_image_url,
                'meta_description': post.meta_description,
                'published_at': post.published_at,
            }
        )
    
    def find_by_id(self, post_id: UUID) -> BlogPost | None:
        """Find a post by its ID."""
        try:
            model = BlogPostModel.objects.get(id=post_id)
            return self._to_entity(model)
        except BlogPostModel.DoesNotExist:
            return None
    
    def find_by_slug(self, slug: Slug) -> BlogPost | None:
        """Find a post by its slug."""
        try:
            model = BlogPostModel.objects.get(
                slug=str(slug),
                status=BlogPostModel.Status.PUBLISHED,
            )
            return self._to_entity(model)
        except BlogPostModel.DoesNotExist:
            return None
    
    def find_all_published(self, limit: int = 10, offset: int = 0) -> List[BlogPost]:
        """Find all published posts."""
        queryset = BlogPostModel.objects.filter(
            status=BlogPostModel.Status.PUBLISHED
        ).order_by('-published_at')[offset:offset + limit]
        return [self._to_entity(model) for model in queryset]
    
    def find_by_tag(self, tag: Tag, limit: int = 10, offset: int = 0) -> List[BlogPost]:
        """Find published posts with a specific tag."""
        queryset = BlogPostModel.objects.filter(
            status=BlogPostModel.Status.PUBLISHED,
            tags__contains=[str(tag)],
        ).order_by('-published_at')[offset:offset + limit]
        return [self._to_entity(model) for model in queryset]
    
    def find_all(self, status: PostStatus | None = None) -> List[BlogPost]:
        """Find all posts, optionally filtered by status."""
        queryset = BlogPostModel.objects.all()
        if status:
            queryset = queryset.filter(status=status.value)
        return [self._to_entity(model) for model in queryset]
    
    def delete(self, post: BlogPost) -> None:
        """Delete a blog post."""
        BlogPostModel.objects.filter(id=post.id).delete()
    
    def count_published(self) -> int:
        """Count total published posts."""
        return BlogPostModel.objects.filter(
            status=BlogPostModel.Status.PUBLISHED
        ).count()
    
    def get_all_tags(self) -> List[Tag]:
        """Get all unique tags from published posts."""
        posts = BlogPostModel.objects.filter(
            status=BlogPostModel.Status.PUBLISHED
        ).values_list('tags', flat=True)
        
        unique_tags = set()
        for tag_list in posts:
            unique_tags.update(tag_list)
        
        return [Tag(t) for t in sorted(unique_tags)]
    
    @staticmethod
    def _to_entity(model: BlogPostModel) -> BlogPost:
        """Map ORM model to domain entity."""
        return BlogPost(
            id=model.id,
            title=model.title,
            slug=Slug(model.slug),
            content=PostContent(model.content),
            tags=[Tag(t) for t in model.tags],
            status=PostStatus(model.status),
            author_name=model.author_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
            published_at=model.published_at,
            featured_image_url=model.featured_image_url,
            meta_description=model.meta_description,
        )
