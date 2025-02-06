from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import *

urlpatterns = [
    path("create/", BlogCreateView.as_view(), name="blog_create"),
    path("", BlogListView.as_view(), name="blog_list"),
    path("<int:pk>/", BlogDetailView.as_view(), name="blog_detail"),
]
