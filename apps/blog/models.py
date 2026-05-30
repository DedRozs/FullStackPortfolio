from django.db import models
from django.utils.text import slugify


class Post(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    summary = models.TextField(
        help_text='Short excerpt used in AI context injection and post listings.',
    )
    body = models.TextField()
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
