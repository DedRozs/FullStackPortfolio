"""API views for the Blog bounded context."""
import json
from uuid import UUID
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.blog.application.commands import (
    CreateBlogPostCommand,
    UpdateBlogPostCommand,
    PublishBlogPostCommand,
    DeleteBlogPostCommand,
)
from apps.blog.application.queries import (
    GetPostBySlugQuery,
    GetPublishedPostsQuery,
    GetPostsByTagQuery,
    GetAllTagsQuery,
)
from apps.blog.application.services import (
    BlogApplicationService,
    BlogPostDTO,
    BlogPostSummaryDTO,
)
from apps.blog.infrastructure.repositories import DjangoBlogPostRepository
from apps.shared.infrastructure.event_bus import get_event_bus


def get_blog_service() -> BlogApplicationService:
    """Factory function for dependency injection."""
    return BlogApplicationService(
        repository=DjangoBlogPostRepository(),
        event_bus=get_event_bus(),
    )


class BlogPostListView(View):
    """API endpoint for listing blog posts."""
    
    def get(self, request) -> JsonResponse:
        """Get published posts with pagination."""
        service = get_blog_service()
        
        # Parse query params
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))
        tag = request.GET.get('tag')
        
        if tag:
            query = GetPostsByTagQuery(tag=tag, limit=limit, offset=offset)
            posts = service.get_posts_by_tag(query)
        else:
            query = GetPublishedPostsQuery(limit=limit, offset=offset)
            posts = service.get_published_posts(query)
        
        return JsonResponse({
            'posts': [BlogPostSummaryDTO.from_entity(p).__dict__ for p in posts],
            'total': service.get_total_published_count(),
        })


class BlogPostDetailView(View):
    """API endpoint for a single blog post."""
    
    def get(self, request, slug: str) -> JsonResponse:
        """Get a single post by slug."""
        service = get_blog_service()
        query = GetPostBySlugQuery(slug=slug)
        post = service.get_post_by_slug(query)
        
        if post is None:
            return JsonResponse({
                'error': 'Post not found',
            }, status=404)
        
        return JsonResponse({
            'post': BlogPostDTO.from_entity(post).__dict__,
        })


class BlogTagListView(View):
    """API endpoint for listing all tags."""
    
    def get(self, request) -> JsonResponse:
        """Get all unique tags."""
        service = get_blog_service()
        query = GetAllTagsQuery()
        tags = service.get_all_tags(query)
        
        return JsonResponse({
            'tags': [{'name': str(t), 'slug': t.slug} for t in tags],
        })


# Admin endpoints (would need authentication in production)

@method_decorator(csrf_exempt, name='dispatch')
class AdminBlogPostView(View):
    """Admin API for managing blog posts."""
    
    def post(self, request) -> JsonResponse:
        """Create a new blog post."""
        try:
            data = json.loads(request.body)
            
            command = CreateBlogPostCommand(
                title=data.get('title', ''),
                content=data.get('content', ''),
                author_name=data.get('author_name', 'Joseph Prince'),
                tags=data.get('tags', []),
                featured_image_url=data.get('featured_image_url'),
                meta_description=data.get('meta_description'),
            )
            
            service = get_blog_service()
            post_id = service.create_post(command)
            
            return JsonResponse({
                'success': True,
                'post_id': str(post_id),
            }, status=201)
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON',
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AdminBlogPostDetailView(View):
    """Admin API for managing a single blog post."""
    
    def put(self, request, post_id: str) -> JsonResponse:
        """Update a blog post."""
        try:
            data = json.loads(request.body)
            
            command = UpdateBlogPostCommand(
                post_id=UUID(post_id),
                title=data.get('title', ''),
                content=data.get('content', ''),
                tags=data.get('tags', []),
                featured_image_url=data.get('featured_image_url'),
                meta_description=data.get('meta_description'),
            )
            
            service = get_blog_service()
            service.update_post(command)
            
            return JsonResponse({'success': True})
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)
    
    def delete(self, request, post_id: str) -> JsonResponse:
        """Delete a blog post."""
        try:
            command = DeleteBlogPostCommand(post_id=UUID(post_id))
            service = get_blog_service()
            service.delete_post(command)
            
            return JsonResponse({'success': True})
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AdminPublishPostView(View):
    """Admin API for publishing a blog post."""
    
    def post(self, request, post_id: str) -> JsonResponse:
        """Publish a blog post."""
        try:
            command = PublishBlogPostCommand(post_id=UUID(post_id))
            service = get_blog_service()
            service.publish_post(command)
            
            return JsonResponse({'success': True})
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)
