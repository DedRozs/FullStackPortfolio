from rest_framework import generics, permissions
from .models import Project, Skill, Experience
from .serializers import ProjectSerializer, SkillSerializer, ExperienceSerializer
from drf_spectacular.utils import extend_schema
from apps.auth_app.permissions import IsAdminUser
from rest_framework.throttling import ScopedRateThrottle

# List all projects (GET) & Create new project (POST)
class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsAdminUser()]  # Restrict modifications to admins
        return [permissions.AllowAny()]

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'project'

# Retrieve, Update, or Delete a specific project (GET, PUT, DELETE)
class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

# Skill API
class SkillListCreateView(generics.ListCreateAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  

class SkillDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

# Experience API
class ExperienceListCreateView(generics.ListCreateAPIView):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  

class ExperienceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer

from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required

# Serve Portfolio Homepage
def home_view(request):
    return render(request, "portfolio/home.html")

# Serve Login Page
def login_view(request):
    return render(request, "auth_app/login.html")

# Serve Admin Dashboard (Only for Authenticated Admins)
@login_required
def admin_dashboard_view(request):
    print(request.user.is_superuser)
    if request.user.role == "user":  # Ensure only admins can access
        return render(request, "403.html")  # Redirect unauthorized users
    return render(request, "admin/dashboard.html")
