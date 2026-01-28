"""Repository implementations for the Blog bounded context."""
from typing import List
from uuid import UUID

from apps.blog.domain.entities import (
    BlogPost, PostStatus, BlogIdea, IdeaStatus, 
    ContentGenerationLog, GenerationStage
)
from apps.blog.domain.repositories import BlogPostRepository
from apps.blog.domain.value_objects import Slug, Tag, PostContent
from apps.blog.infrastructure.models import (
    BlogPostModel, BlogIdeaModel, ContentGenerationLogModel
)


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
    
    def search(
        self, 
        search_term: str, 
        tag: Tag | None = None,
        limit: int = 10, 
        offset: int = 0
    ) -> List[BlogPost]:
        """Search published posts by title and content."""
        from django.db.models import Q
        
        queryset = BlogPostModel.objects.filter(
            status=BlogPostModel.Status.PUBLISHED
        ).filter(
            Q(title__icontains=search_term) | Q(content__icontains=search_term)
        )
        
        if tag:
            queryset = queryset.filter(tags__contains=[str(tag)])
        
        queryset = queryset.order_by('-published_at')[offset:offset + limit]
        return [self._to_entity(model) for model in queryset]
    
    def count_search_results(self, search_term: str, tag: Tag | None = None) -> int:
        """Count total search results."""
        from django.db.models import Q
        
        queryset = BlogPostModel.objects.filter(
            status=BlogPostModel.Status.PUBLISHED
        ).filter(
            Q(title__icontains=search_term) | Q(content__icontains=search_term)
        )
        
        if tag:
            queryset = queryset.filter(tags__contains=[str(tag)])
        
        return queryset.count()
    
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


class DjangoBlogIdeaRepository:
    """Django ORM implementation for BlogIdea persistence."""
    
    def save(self, idea: BlogIdea) -> None:
        """Persist a blog idea."""
        BlogIdeaModel.objects.update_or_create(
            id=idea.id,
            defaults={
                'topic': idea.topic,
                'keywords': idea.keywords,
                'source': idea.source,
                'status': idea.status.value,
                'expertise_area': idea.expertise_area,
                'trend_score': idea.trend_score,
                'processed_at': idea.processed_at,
                'blog_post_id': idea.blog_post_id,
                'rejection_reason': idea.rejection_reason,
            }
        )
    
    def find_by_id(self, idea_id: UUID) -> BlogIdea | None:
        """Find an idea by its ID."""
        try:
            model = BlogIdeaModel.objects.get(id=idea_id)
            return self._to_entity(model)
        except BlogIdeaModel.DoesNotExist:
            return None
    
    def find_by_status(self, status: IdeaStatus) -> List[BlogIdea]:
        """Find all ideas with a specific status."""
        queryset = BlogIdeaModel.objects.filter(
            status=status.value
        ).order_by('-created_at')
        return [self._to_entity(m) for m in queryset]
    
    def find_recent(self, limit: int = 20) -> List[BlogIdea]:
        """Find recent ideas."""
        queryset = BlogIdeaModel.objects.all().order_by('-created_at')[:limit]
        return [self._to_entity(m) for m in queryset]
    
    def delete(self, idea: BlogIdea) -> None:
        """Delete an idea."""
        BlogIdeaModel.objects.filter(id=idea.id).delete()
    
    @staticmethod
    def _to_entity(model: BlogIdeaModel) -> BlogIdea:
        """Map ORM model to domain entity."""
        return BlogIdea(
            id=model.id,
            topic=model.topic,
            keywords=model.keywords,
            source=model.source,
            status=IdeaStatus(model.status),
            expertise_area=model.expertise_area,
            trend_score=model.trend_score,
            created_at=model.created_at,
            processed_at=model.processed_at,
            blog_post_id=model.blog_post_id,
            rejection_reason=model.rejection_reason,
        )


class DjangoContentGenerationLogRepository:
    """Django ORM implementation for ContentGenerationLog persistence."""
    
    def save(self, log: ContentGenerationLog) -> None:
        """Persist a generation log entry."""
        ContentGenerationLogModel.objects.update_or_create(
            id=log.id,
            defaults={
                'idea_id': log.idea_id,
                'stage': log.stage.value,
                'model_used': log.model_used,
                'input_tokens': log.input_tokens,
                'output_tokens': log.output_tokens,
                'duration_seconds': log.duration_seconds,
                'success': log.success,
                'output_preview': log.output_preview,
                'error_message': log.error_message,
            }
        )
    
    def find_by_idea(self, idea_id: UUID) -> List[ContentGenerationLog]:
        """Find all logs for a specific idea."""
        queryset = ContentGenerationLogModel.objects.filter(
            idea_id=idea_id
        ).order_by('created_at')
        return [self._to_entity(m) for m in queryset]
    
    def find_recent(self, limit: int = 50) -> List[ContentGenerationLog]:
        """Find recent log entries."""
        queryset = ContentGenerationLogModel.objects.all().order_by('-created_at')[:limit]
        return [self._to_entity(m) for m in queryset]
    
    @staticmethod
    def _to_entity(model: ContentGenerationLogModel) -> ContentGenerationLog:
        """Map ORM model to domain entity."""
        return ContentGenerationLog(
            id=model.id,
            idea_id=model.idea_id,
            stage=GenerationStage(model.stage),
            model_used=model.model_used,
            input_tokens=model.input_tokens,
            output_tokens=model.output_tokens,
            duration_seconds=model.duration_seconds,
            success=model.success,
            output_preview=model.output_preview,
            error_message=model.error_message,
            created_at=model.created_at,
        )
