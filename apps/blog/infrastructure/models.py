"""Django ORM models for the Blog bounded context."""
from django.db import models
import uuid


class BlogPostModel(models.Model):
    """Django ORM model for BlogPost entity."""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()  # Markdown content
    tags = models.JSONField(default=list)  # Store tags as JSON array
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    author_name = models.CharField(max_length=100)
    featured_image_url = models.URLField(max_length=500, blank=True, null=True)
    meta_description = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        app_label = 'blog'
        db_table = 'blog_posts'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', '-published_at']),
        ]
    
    def __str__(self) -> str:
        return self.title
