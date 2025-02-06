from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, generics, permissions

from .models import AIService
from .serializers import AIServiceSerializer

class AIServiceCreateView(generics.CreateAPIView):
    queryset = AIService.objects.all()
    serializer_class = AIServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class AIServiceListView(generics.ListAPIView):
    queryset = AIService.objects.all()
    serializer_class = AIServiceSerializer
    permission_classes = [permissions.AllowAny]

from rest_framework.exceptions import PermissionDenied

class AIServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting an AI service.
    Only the owner can update or delete.
    """
    queryset = AIService.objects.all()
    serializer_class = AIServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self):
        """
        Override get_object to return 403 Forbidden instead of 404 when unauthorized users attempt to update.
        """
        obj = super().get_object()

        # Ensure only the owner can modify the object
        if self.request.method in ["PUT", "PATCH", "DELETE"] and obj.owner != self.request.user:
            raise PermissionDenied("You do not have permission to edit this AI service.")

        return obj
