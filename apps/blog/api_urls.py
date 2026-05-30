from django.urls import path

from . import api_views

app_name = 'blog_api'

urlpatterns = [
    path('posts/', api_views.post_list, name='post_list'),
    path('posts/<slug:slug>/', api_views.post_detail, name='post_detail'),
]
