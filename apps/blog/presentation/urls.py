from django.urls import path

from apps.blog.presentation.views import (
    BlogPostListView,
    BlogPostDetailView,
    BlogTagListView,
    AdminBlogPostView,
    AdminBlogPostDetailView,
    AdminPublishPostView,
)
from apps.blog.presentation.task_views import (
    GenerateIdeasTaskView,
    PublishBlogTaskView,
    CleanupIdeasTaskView,
    HealthCheckTaskView,
)
from apps.blog.presentation.feeds import BlogPostFeed

app_name = 'blog'

urlpatterns = [
    # Public endpoints
    path('posts/', BlogPostListView.as_view(), name='post-list'),
    path('posts/<slug:slug>/', BlogPostDetailView.as_view(), name='post-detail'),
    path('tags/', BlogTagListView.as_view(), name='tag-list'),
    path('rss/', BlogPostFeed(), name='rss-feed'),
    
    # Task endpoints (triggered by GAE Cron)
    path('tasks/generate-ideas/', GenerateIdeasTaskView.as_view(), name='task-generate-ideas'),
    path('tasks/publish-blog/', PublishBlogTaskView.as_view(), name='task-publish-blog'),
    path('tasks/cleanup-ideas/', CleanupIdeasTaskView.as_view(), name='task-cleanup-ideas'),
    path('tasks/health-check/', HealthCheckTaskView.as_view(), name='task-health-check'),
    
    # Admin endpoints (TODO: add authentication)
    path('admin/posts/', AdminBlogPostView.as_view(), name='admin-post-create'),
    path('admin/posts/<str:post_id>/', AdminBlogPostDetailView.as_view(), name='admin-post-detail'),
    path('admin/posts/<str:post_id>/publish/', AdminPublishPostView.as_view(), name='admin-post-publish'),
]
