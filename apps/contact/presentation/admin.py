from django.contrib import admin

from apps.contact.infrastructure.models import ContactMessageModel


@admin.register(ContactMessageModel)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
