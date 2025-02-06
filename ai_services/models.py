from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AIService(models.Model):
    SERVICE_CHOICES = [
        ("chatbot", "Chatbot Assistant"),
        ("recommendation", "AI-Powered Blog Recommendations"),
        ("search", "AI-Powered Search Engine"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_type} for {self.user.username}"
