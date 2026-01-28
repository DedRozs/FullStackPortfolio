"""URL configuration for the Trading bounded context."""
from django.urls import path

from apps.trading.presentation.views import (
    TradingPostListView,
    TradingPostDetailView,
    InstrumentListView,
    InstrumentPostsView,
    PostTypeListView,
    AdminTradingPostView,
    AdminTradingPostDetailView,
    AdminPublishPostView,
    AdminUnpublishPostView,
    AdminSchedulePostView,
    AdminArchivePostView,
)
from apps.trading.presentation.feeds import (
    TradingPostFeed,
    InstrumentPostFeed,
)

app_name = 'trading'

urlpatterns = [
    # Public endpoints
    path('posts/', TradingPostListView.as_view(), name='post-list'),
    path('posts/<slug:slug>/', TradingPostDetailView.as_view(), name='post-detail'),
    path('instruments/', InstrumentListView.as_view(), name='instrument-list'),
    path('instruments/<str:instrument>/', InstrumentPostsView.as_view(), name='instrument-posts'),
    path('types/', PostTypeListView.as_view(), name='type-list'),
    
    # RSS feeds
    path('rss/', TradingPostFeed(), name='rss-feed'),
    path('rss/<str:instrument>/', InstrumentPostFeed(), name='instrument-rss-feed'),
    
    # Admin endpoints (TODO: add authentication)
    path('admin/posts/', AdminTradingPostView.as_view(), name='admin-post-create'),
    path('admin/posts/<str:post_id>/', AdminTradingPostDetailView.as_view(), name='admin-post-detail'),
    path('admin/posts/<str:post_id>/publish/', AdminPublishPostView.as_view(), name='admin-post-publish'),
    path('admin/posts/<str:post_id>/unpublish/', AdminUnpublishPostView.as_view(), name='admin-post-unpublish'),
    path('admin/posts/<str:post_id>/schedule/', AdminSchedulePostView.as_view(), name='admin-post-schedule'),
    path('admin/posts/<str:post_id>/archive/', AdminArchivePostView.as_view(), name='admin-post-archive'),
]
