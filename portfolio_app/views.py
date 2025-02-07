from rest_framework import viewsets
from .serializers import ProjectSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import render
from .models import *


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


def home_view(request):
    return render(request, "portfolio_app/index.html")


def projects_view(request):
    projects = Project.objects.all()
    return render(request, "portfolio_app/projects.html", {"projects": projects})


def contact_view(request):
    return render(request, "portfolio_app/contact.html")


def about_view(request):
    return render(request, "portfolio_app/about.html")
