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


class BlogIdeaModel(models.Model):
    """Django ORM model for BlogIdea entity - tracks content ideas."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        REJECTED = 'rejected', 'Rejected'
        FAILED = 'failed', 'Failed'
    
    class Source(models.TextChoices):
        TRENDS = 'trends', 'Google Trends'
        MANUAL = 'manual', 'Manual Entry'
        AI_SUGGESTED = 'ai_suggested', 'AI Suggested'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.CharField(max_length=300)
    keywords = models.JSONField(default=list)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.AI_SUGGESTED)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    expertise_area = models.CharField(max_length=100)  # AI, Full-Stack, Cloud, etc.
    trend_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    blog_post = models.ForeignKey(
        BlogPostModel, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='source_idea'
    )
    rejection_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        app_label = 'blog'
        db_table = 'blog_ideas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['expertise_area']),
        ]
    
    def __str__(self) -> str:
        return f"{self.topic} ({self.status})"


class ContentGenerationLogModel(models.Model):
    """Audit log for content generation pipeline stages."""
    
    class Stage(models.TextChoices):
        IDEA_GENERATION = 'idea_generation', 'Idea Generation'
        CONTENT_CREATION = 'content_creation', 'Content Creation'
        PROOFREADING = 'proofreading', 'Proofreading'
        PUBLISHING = 'publishing', 'Publishing'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idea = models.ForeignKey(
        BlogIdeaModel,
        on_delete=models.CASCADE,
        related_name='generation_logs'
    )
    stage = models.CharField(max_length=30, choices=Stage.choices)
    model_used = models.CharField(max_length=50)  # e.g., 'gpt-4', 'gpt-4o', 'claude-3'
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    duration_seconds = models.FloatField(default=0.0)
    success = models.BooleanField(default=True)
    output_preview = models.TextField(null=True, blank=True)  # First 500 chars
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'blog'
        db_table = 'content_generation_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['idea', 'stage']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"{status} {self.stage} - {self.model_used}"
