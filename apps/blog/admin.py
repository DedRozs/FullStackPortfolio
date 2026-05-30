from django.contrib import admin

from .models import Post, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'status',
        'author',
        'reading_time_minutes',
        'published_at',
        'created_at',
    )
    list_filter = ('status', 'tags')
    search_fields = ('title', 'excerpt', 'body')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'reading_time_minutes')
    date_hierarchy = 'published_at'
    filter_horizontal = ('tags',)
    fieldsets = (
        (
            'Content',
            {
                'fields': ('title', 'slug', 'excerpt', 'body', 'featured_image'),
            },
        ),
        (
            'Publication',
            {
                'fields': ('status', 'author', 'tags', 'published_at'),
            },
        ),
        (
            'Metadata',
            {
                'fields': ('reading_time_minutes', 'created_at', 'updated_at'),
                'classes': ('collapse',),
            },
        ),
    )
