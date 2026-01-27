from django.urls import path

from apps.blog.presentation.views import (
    BlogPostListView,
    BlogPostDetailView,
    BlogTagListView,
    AdminBlogPostView,
    AdminBlogPostDetailView,
    AdminPublishPostView,
)

app_name = 'blog'

urlpatterns = [
    # Public endpoints
    path('posts/', BlogPostListView.as_view(), name='post-list'),
    path('posts/<slug:slug>/', BlogPostDetailView.as_view(), name='post-detail'),
    path('tags/', BlogTagListView.as_view(), name='tag-list'),
    
    # Admin endpoints (TODO: add authentication)
    path('admin/posts/', AdminBlogPostView.as_view(), name='admin-post-create'),
    path('admin/posts/<str:post_id>/', AdminBlogPostDetailView.as_view(), name='admin-post-detail'),
    path('admin/posts/<str:post_id>/publish/', AdminPublishPostView.as_view(), name='admin-post-publish'),
]
