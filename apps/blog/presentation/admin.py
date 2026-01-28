from django.contrib import admin

from apps.blog.infrastructure.models import (
    BlogPostModel,
    BlogIdeaModel,
    ContentGenerationLogModel,
)


@admin.register(BlogPostModel)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'author_name', 'published_at', 'created_at']
    list_filter = ['status', 'created_at', 'published_at']
    search_fields = ['title', 'content', 'tags']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'author_name')
        }),
        ('Metadata', {
            'fields': ('tags', 'featured_image_url', 'meta_description')
        }),
        ('Status', {
            'fields': ('status', 'published_at')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BlogIdeaModel)
class BlogIdeaAdmin(admin.ModelAdmin):
    """Admin for managing AI-generated blog ideas."""
    list_display = ['topic', 'status', 'expertise_area', 'trend_score', 'created_at', 'processed_at']
    list_filter = ['status', 'expertise_area', 'source', 'created_at']
    search_fields = ['topic', 'keywords']
    readonly_fields = ['id', 'created_at', 'processed_at', 'blog_post']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('topic', 'keywords', 'expertise_area')
        }),
        ('Source & Scoring', {
            'fields': ('source', 'trend_score')
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason', 'processed_at')
        }),
        ('Related Content', {
            'fields': ('blog_post',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_pending', 'mark_as_rejected']
    
    @admin.action(description='Mark selected ideas as pending')
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
    
    @admin.action(description='Mark selected ideas as rejected')
    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejected', rejection_reason='Rejected by admin')


@admin.register(ContentGenerationLogModel)
class ContentGenerationLogAdmin(admin.ModelAdmin):
    """Admin for viewing content generation logs."""
    list_display = ['idea', 'stage', 'model_used', 'success', 'duration_seconds', 'created_at']
    list_filter = ['stage', 'success', 'model_used', 'created_at']
    search_fields = ['idea__topic', 'output_preview', 'error_message']
    readonly_fields = ['id', 'idea', 'stage', 'model_used', 'input_tokens', 
                       'output_tokens', 'duration_seconds', 'success', 
                       'output_preview', 'error_message', 'created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        """Logs are created by the system only."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Logs are read-only."""
        return False

