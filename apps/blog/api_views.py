from __future__ import annotations

import logging

from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .application.dtos import PostDetailDTO, PostListItemDTO, TagDTO
from .application.use_cases import GetPostBySlug, ListPublishedPosts
from .domain.exceptions import PostNotFoundError
from .infrastructure.repositories import DjangoPostRepository, DjangoTagRepository

logger = logging.getLogger(__name__)

_PAGE_SIZE = 10


def _make_repos():
    return DjangoPostRepository(), DjangoTagRepository()


def _resolve_image_url(path: str | None) -> str | None:
    """Convert a raw storage path to a full URL using the configured backend."""
    if not path:
        return None
    try:
        return default_storage.url(path)
    except Exception:
        logger.warning('Could not resolve image URL for path: %s', path)
        return None


def _serialize_tag(tag: TagDTO) -> dict:
    return {'id': tag.id, 'name': tag.name, 'slug': tag.slug}


def _serialize_list_item(dto: PostListItemDTO) -> dict:
    return {
        'id': dto.id,
        'title': dto.title,
        'slug': dto.slug,
        'excerpt': dto.excerpt,
        'reading_time_minutes': dto.reading_time_minutes,
        'published_at': dto.published_at.isoformat() if dto.published_at else None,
        'author_display_name': dto.author_display_name,
        'featured_image_url': _resolve_image_url(dto.featured_image_url),
        'tags': [_serialize_tag(t) for t in dto.tags],
    }


def _serialize_detail(dto: PostDetailDTO) -> dict:
    return {
        'id': dto.id,
        'title': dto.title,
        'slug': dto.slug,
        'excerpt': dto.excerpt,
        'body': dto.body,
        'reading_time_minutes': dto.reading_time_minutes,
        'published_at': dto.published_at.isoformat() if dto.published_at else None,
        'author_display_name': dto.author_display_name,
        'featured_image_url': _resolve_image_url(dto.featured_image_url),
        'tags': [_serialize_tag(t) for t in dto.tags],
        'related_posts': [_serialize_list_item(r) for r in dto.related_posts],
    }


@require_GET
def post_list(request):
    post_repo, tag_repo = _make_repos()
    try:
        page_number = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page_number = 1
    use_case = ListPublishedPosts(post_repo, tag_repo)
    total = post_repo.count_published()
    posts_on_page = use_case.execute(page=page_number, page_size=_PAGE_SIZE)
    paginator = Paginator(range(total), _PAGE_SIZE)
    page_obj = paginator.get_page(page_number)
    return JsonResponse({
        'posts': [_serialize_list_item(p) for p in posts_on_page],
        'total': total,
        'page': page_obj.number,
        'num_pages': paginator.num_pages,
        'page_size': _PAGE_SIZE,
    })


@require_GET
def post_detail(request, slug: str):
    post_repo, tag_repo = _make_repos()
    use_case = GetPostBySlug(post_repo, tag_repo)
    try:
        dto = use_case.execute(
            slug=slug,
            request_user_is_staff=request.user.is_staff,
        )
    except PostNotFoundError:
        return JsonResponse({'error': 'Post not found.'}, status=404)
    return JsonResponse(_serialize_detail(dto))
