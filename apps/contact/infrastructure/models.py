"""Django ORM models for the Contact bounded context.

These are infrastructure concerns - they map domain entities to database tables.
They should not contain business logic.
"""
from django.db import models
import uuid


class ContactMessageModel(models.Model):
    """Django ORM model for ContactMessage entity.
    
    This is a persistence model, not a domain model.
    It's used only for database operations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'contact'
        db_table = 'contact_messages'
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"Message from {self.name} ({self.email})"
