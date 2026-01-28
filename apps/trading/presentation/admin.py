"""Django Admin configuration for the Trading bounded context."""
from django.contrib import admin
from django.utils.html import format_html

from apps.trading.infrastructure.models import (
    TradingPostModel,
    MarketSessionModel,
    WeeklySessionModel,
    PriceLevelModel,
)


@admin.register(TradingPostModel)
class TradingPostAdmin(admin.ModelAdmin):
    """Admin for managing trading posts."""
    
    list_display = [
        'title',
        'instrument_display',
        'post_type_display',
        'session_date',
        'status',
        'published_at',
        'created_at',
    ]
    list_filter = [
        'status',
        'instrument',
        'post_type',
        'session_date',
        'created_at',
        'published_at',
    ]
    search_fields = ['title', 'content', 'slug']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-session_date', '-created_at']
    date_hierarchy = 'session_date'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content')
        }),
        ('Classification', {
            'fields': ('instrument', 'post_type', 'session_date')
        }),
        ('SEO', {
            'fields': ('meta_description',),
            'classes': ('collapse',)
        }),
        ('Status & Scheduling', {
            'fields': ('status', 'scheduled_for', 'published_at')
        }),
        ('Related Data', {
            'fields': ('market_session', 'weekly_session'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_posts', 'unpublish_posts', 'archive_posts']
    
    @admin.display(description='Instrument', ordering='instrument')
    def instrument_display(self, obj):
        """Display instrument with short name."""
        instrument_names = {
            'NQ=F': 'NQ',
            'ES=F': 'ES',
            'RTY=F': 'RTY',
            'YM=F': 'YM',
        }
        return instrument_names.get(obj.instrument, obj.instrument)
    
    @admin.display(description='Type', ordering='post_type')
    def post_type_display(self, obj):
        """Display post type with readable name."""
        type_names = {
            'pre_market': 'Pre-Market',
            'post_market': 'Recap',
            'weekly_recap': 'Weekly',
        }
        return type_names.get(obj.post_type, obj.post_type)
    
    @admin.action(description='Publish selected posts')
    def publish_posts(self, request, queryset):
        """Publish selected posts."""
        from django.utils import timezone
        count = queryset.exclude(status='published').update(
            status='published',
            published_at=timezone.now(),
        )
        self.message_user(request, f'{count} posts published.')
    
    @admin.action(description='Unpublish selected posts')
    def unpublish_posts(self, request, queryset):
        """Unpublish selected posts."""
        count = queryset.filter(status='published').update(status='draft')
        self.message_user(request, f'{count} posts unpublished.')
    
    @admin.action(description='Archive selected posts')
    def archive_posts(self, request, queryset):
        """Archive selected posts."""
        count = queryset.update(status='archived')
        self.message_user(request, f'{count} posts archived.')


@admin.register(MarketSessionModel)
class MarketSessionAdmin(admin.ModelAdmin):
    """Admin for viewing market session data."""
    
    list_display = [
        'instrument_display',
        'session_date',
        'open_price',
        'high_price',
        'low_price',
        'close_price',
        'change_display',
        'volume',
        'created_at',
    ]
    list_filter = [
        'instrument',
        'session_date',
        'created_at',
    ]
    search_fields = ['instrument']
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'change_points',
        'change_percent',
    ]
    ordering = ['-session_date']
    date_hierarchy = 'session_date'
    
    fieldsets = (
        (None, {
            'fields': ('instrument', 'session_date')
        }),
        ('Session OHLC', {
            'fields': ('open_price', 'high_price', 'low_price', 'close_price')
        }),
        ('Overnight Session', {
            'fields': ('overnight_high', 'overnight_low'),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('prior_close', 'change_points', 'change_percent', 'volume')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Instrument', ordering='instrument')
    def instrument_display(self, obj):
        """Display instrument with short name."""
        instrument_names = {
            'NQ=F': 'NQ',
            'ES=F': 'ES',
            'RTY=F': 'RTY',
            'YM=F': 'YM',
        }
        return instrument_names.get(obj.instrument, obj.instrument)
    
    @admin.display(description='Change')
    def change_display(self, obj):
        """Display change with color coding."""
        if obj.change_percent is None:
            return '-'
        
        pct = float(obj.change_percent)
        color = 'green' if pct >= 0 else 'red'
        sign = '+' if pct >= 0 else ''
        return format_html(
            '<span style="color: {};">{}{:.2f}%</span>',
            color,
            sign,
            pct,
        )
    
    def has_add_permission(self, request):
        """Sessions are created by the data pipeline only."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Sessions are read-only in admin."""
        return False


@admin.register(WeeklySessionModel)
class WeeklySessionAdmin(admin.ModelAdmin):
    """Admin for viewing weekly session data."""
    
    list_display = [
        'instrument_display',
        'week_start_date',
        'week_end_date',
        'open_price',
        'high_price',
        'low_price',
        'close_price',
        'change_display',
        'trading_days',
        'created_at',
    ]
    list_filter = [
        'instrument',
        'week_start_date',
        'created_at',
    ]
    search_fields = ['instrument']
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'change_points',
        'change_percent',
        'trading_days',
    ]
    ordering = ['-week_start_date']
    
    fieldsets = (
        (None, {
            'fields': ('instrument', 'week_start_date', 'week_end_date')
        }),
        ('Weekly OHLC', {
            'fields': ('open_price', 'high_price', 'low_price', 'close_price')
        }),
        ('Performance', {
            'fields': ('change_points', 'change_percent', 'trading_days')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Instrument', ordering='instrument')
    def instrument_display(self, obj):
        """Display instrument with short name."""
        instrument_names = {
            'NQ=F': 'NQ',
            'ES=F': 'ES',
            'RTY=F': 'RTY',
            'YM=F': 'YM',
        }
        return instrument_names.get(obj.instrument, obj.instrument)
    
    @admin.display(description='Change')
    def change_display(self, obj):
        """Display change with color coding."""
        if obj.change_percent is None:
            return '-'
        
        pct = float(obj.change_percent)
        color = 'green' if pct >= 0 else 'red'
        sign = '+' if pct >= 0 else ''
        return format_html(
            '<span style="color: {};">{}{:.2f}%</span>',
            color,
            sign,
            pct,
        )
    
    def has_add_permission(self, request):
        """Weekly sessions are created by the data pipeline only."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Weekly sessions are read-only in admin."""
        return False


@admin.register(PriceLevelModel)
class PriceLevelAdmin(admin.ModelAdmin):
    """Admin for viewing price levels."""
    
    list_display = [
        'instrument_display',
        'level_type_display',
        'price',
        'session_date',
        'created_at',
    ]
    list_filter = [
        'instrument',
        'level_type',
        'session_date',
        'created_at',
    ]
    search_fields = ['instrument', 'level_type']
    readonly_fields = ['id', 'created_at']
    ordering = ['-session_date', 'instrument', 'level_type']
    date_hierarchy = 'session_date'
    
    fieldsets = (
        (None, {
            'fields': ('instrument', 'level_type', 'price', 'session_date')
        }),
        ('System', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Instrument', ordering='instrument')
    def instrument_display(self, obj):
        """Display instrument with short name."""
        instrument_names = {
            'NQ=F': 'NQ',
            'ES=F': 'ES',
            'RTY=F': 'RTY',
            'YM=F': 'YM',
        }
        return instrument_names.get(obj.instrument, obj.instrument)
    
    @admin.display(description='Level Type', ordering='level_type')
    def level_type_display(self, obj):
        """Display level type with readable name."""
        type_names = {
            'prior_high': 'Prior High',
            'prior_low': 'Prior Low',
            'prior_close': 'Prior Close',
            'overnight_high': 'ON High',
            'overnight_low': 'ON Low',
            'weekly_open': 'Wkly Open',
            'weekly_high': 'Wkly High',
            'weekly_low': 'Wkly Low',
            'monthly_high': 'Mo High',
            'monthly_low': 'Mo Low',
        }
        return type_names.get(obj.level_type, obj.level_type)
    
    def has_add_permission(self, request):
        """Price levels are created by the data pipeline only."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Price levels are read-only in admin."""
        return False
