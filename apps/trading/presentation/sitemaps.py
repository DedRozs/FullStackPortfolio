"""
Sitemap configuration for Trading Blog SEO.

Generates XML sitemaps for search engines to index trading posts and instrument pages.
"""
from django.contrib.sitemaps import Sitemap

from apps.trading.infrastructure.models import TradingPostModel
from apps.trading.domain.value_objects import Instrument


class TradingBlogStaticSitemap(Sitemap):
    """Sitemap for static trading blog pages (SPA routes)."""
    
    priority = 0.7
    changefreq = 'daily'
    protocol = 'https'
    
    def items(self):
        """Return static trading blog routes."""
        routes = [
            'trading-blog',  # Main trading blog page
        ]
        # Add instrument-specific pages
        for instrument in Instrument:
            routes.append(f'trading-blog/{instrument.short_name.lower()}')
        return routes
    
    def location(self, item):
        """Return the URL for each item."""
        return f'/{item}'


class TradingPostSitemap(Sitemap):
    """Sitemap for individual trading posts."""
    
    changefreq = 'weekly'
    protocol = 'https'
    
    def items(self):
        """Return all published trading posts."""
        return TradingPostModel.objects.filter(
            status=TradingPostModel.Status.PUBLISHED
        ).order_by('-published_at')
    
    def lastmod(self, obj):
        """Return last modification date."""
        return obj.updated_at
    
    def location(self, obj):
        """Return the URL for the post."""
        return f'/trading-blog/{obj.slug}'
    
    def priority(self, obj):
        """Calculate priority based on post type and recency.
        
        Pre-market and post-market posts get slightly higher priority
        as they are more time-sensitive.
        """
        base_priority = 0.7
        
        # Boost for pre-market and post-market posts
        if obj.post_type in ['pre_market', 'post_market']:
            base_priority = 0.8
        
        return base_priority


class InstrumentSitemap(Sitemap):
    """Sitemap for instrument-specific pages."""
    
    priority = 0.7
    changefreq = 'daily'
    protocol = 'https'
    
    def items(self):
        """Return all instruments."""
        return list(Instrument)
    
    def location(self, instrument: Instrument):
        """Return the URL for the instrument page."""
        return f'/trading-blog/{instrument.short_name.lower()}'


# Sitemap registry for trading blog
trading_sitemaps = {
    'trading-static': TradingBlogStaticSitemap,
    'trading-posts': TradingPostSitemap,
    'trading-instruments': InstrumentSitemap,
}
