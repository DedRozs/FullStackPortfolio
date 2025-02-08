from django.urls import path
from .views import (
    home_view, projects_view, project_detail_view,
    blog_view, blog_detail_view, contact_view, about_view
)

urlpatterns = [
    path("", home_view, name="home"),
    path("about/", about_view, name="about"),  # ✅ Fix: Ensure 'about' exists
    path("projects/", projects_view, name="projects"),
    path("projects/<int:project_id>/", project_detail_view, name="project_detail"),
    path("blog/", blog_view, name="blog"),
    path("blog/<int:blog_id>/", blog_detail_view, name="blog_detail"),
    path("contact/", contact_view, name="contact"),
]
