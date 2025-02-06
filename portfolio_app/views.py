from rest_framework import viewsets
from .models import Project
from .serializers import ProjectSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

from django.shortcuts import render

def home_view(request):
    return render(request, "portfolio_app/index.html")
