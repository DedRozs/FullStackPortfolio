from django.urls import path
from .views import (
    ProjectListCreateView, ProjectDetailView,
    SkillListCreateView, SkillDetailView,
    ExperienceListCreateView, ExperienceDetailView
)

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
]
