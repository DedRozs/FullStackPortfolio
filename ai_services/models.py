from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AIService(models.Model):
    """
    Model representing an AI-powered service.
    Each AI service is created and owned by an authenticated user.
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(default="None")
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="ai_services"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
