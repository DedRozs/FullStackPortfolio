from django.urls import path
from .views import *

urlpatterns = [
    # Project API Endpoints
    path('api/projects/', ProjectListCreateView.as_view(), name='project-list'),
    path('api/projects/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),

    # Skill API Endpoints
    path('api/skills/', SkillListCreateView.as_view(), name='skill-list'),
    path('api/skills/<int:pk>/', SkillDetailView.as_view(), name='skill-detail'),

    # Experience API Endpoints
    path('api/experiences/', ExperienceListCreateView.as_view(), name='experience-list'),
    path('api/experiences/<int:pk>/', ExperienceDetailView.as_view(), name='experience-detail'),

    # Blog API Endpoints
    path("api/blog/", BlogPostListCreateView.as_view(), name="blog-list"),
    path("api/blog/<int:pk>/", BlogPostDetailView.as_view(), name="blog-detail"),

    path("", home_view, name="home"),
    path("about/", about_view, name="about"),
    path("projects/", projects_view, name="projects"),
    path("projects/<int:project_id>/", project_detail_view, name="project-detail"),
    path("blog/", blog_view, name="blog"),
    path("blog/<int:post_id>/", blog_post_view, name="blog-post"),
    path("contact/", contact_view, name="contact"),
    path("login/", login_view, name="login"),
    path("admin/dashboard/", admin_dashboard_view, name="admin-dashboard"),

]
