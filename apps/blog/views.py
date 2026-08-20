from __future__ import annotations

from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render
from django.utils.feedgenerator import Rss201rev2Feed

from .application.use_cases import GetAllPublishedPostsForFeed, GetPostBySlug, ListPublishedPosts
from .domain.exceptions import PostNotFoundError
from .infrastructure.repositories import DjangoPostRepository, DjangoTagRepository

_PAGE_SIZE = 10


def _make_repos():
    return DjangoPostRepository(), DjangoTagRepository()


def post_list(request):
    post_repo, tag_repo = _make_repos()
    use_case = ListPublishedPosts(post_repo, tag_repo)
    try:
        page_number = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page_number = 1
    total = post_repo.count_published()
    posts_on_page = use_case.execute(page=page_number, page_size=_PAGE_SIZE)
    paginator = Paginator(range(total), _PAGE_SIZE)
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'blog/post_list.html',
        {'posts': posts_on_page, 'page_obj': page_obj},
    )


def post_detail(request, slug: str):
    post_repo, tag_repo = _make_repos()
    use_case = GetPostBySlug(post_repo, tag_repo)
    try:
        post_dto = use_case.execute(
            slug=slug,
            request_user_is_staff=request.user.is_staff,
        )
    except PostNotFoundError:
        raise Http404
    return render(request, 'blog/post_detail.html', {'post': post_dto})


class LatestPostsFeed(Feed):
    feed_type = Rss201rev2Feed
    title = 'Joseph Prince - Engineering Blog'
    link = '/blog/'
    description = 'Notes on backend architecture, Django, and running systems in production.'

    def items(self):
        post_repo = DjangoPostRepository()
        use_case = GetAllPublishedPostsForFeed(post_repo)
        return use_case.execute()

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_link(self, item):
        return f'/blog/{item.slug}/'

    def item_pubdate(self, item):
        return item.published_at
