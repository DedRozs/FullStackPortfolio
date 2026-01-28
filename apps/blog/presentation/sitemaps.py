"""
Sitemap configuration for SEO.

Generates XML sitemaps for search engines to index blog posts and static pages.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.blog.infrastructure.models import BlogPostModel


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages (SPA routes)."""
    
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'
    
    def items(self):
        return ['home', 'about', 'blog', 'contact']
    
    def location(self, item):
        # Map internal names to SPA routes
        routes = {
            'home': '/',
            'about': '/about',
            'blog': '/blog',
            'contact': '/contact',
        }
        return routes.get(item, '/')


class BlogPostSitemap(Sitemap):
    """Sitemap for blog posts."""
    
    changefreq = 'weekly'
    protocol = 'https'
    
    def items(self):
        return BlogPostModel.objects.filter(
            status=BlogPostModel.Status.PUBLISHED
        ).order_by('-published_at')
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f'/blog/{obj.slug}'
    
    def priority(self, obj):
        # Newer posts get higher priority
        return 0.9


# Sitemap registry
sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogPostSitemap,
}
