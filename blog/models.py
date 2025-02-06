from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    published_at = models.DateTimeField(auto_now_add=True)
    tags = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title
