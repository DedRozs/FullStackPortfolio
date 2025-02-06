from rest_framework import viewsets
from .models import AIService
from .serializers import AIServiceSerializer
from rest_framework.permissions import IsAuthenticated

class AIServiceViewSet(viewsets.ModelViewSet):
    queryset = AIService.objects.all()
    serializer_class = AIServiceSerializer
    permission_classes = [IsAuthenticated]
