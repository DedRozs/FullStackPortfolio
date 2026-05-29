from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at', 'email_sent', 'sms_sent')
    list_filter = ('email_sent', 'sms_sent')
    readonly_fields = ('submitted_at', 'email_sent', 'sms_sent')
    search_fields = ('name', 'email', 'message')
