"""
RSS Feed for Blog Posts.

Provides RSS 2.0 feed for blog content syndication, improving SEO discoverability.
"""
from django.contrib.syndication.views import Feed
from django.urls import reverse

from apps.blog.infrastructure.models import BlogPostModel


class BlogPostFeed(Feed):
    """RSS feed for published blog posts."""
    
    title = "Joseph Prince | Software Engineering Blog"
    link = "https://www.thejosephprince.com/blog"
    description = (
        "Technical articles on software engineering, Clean Architecture, "
        "Domain-Driven Design, Python, TypeScript, React, and Django by "
        "Joseph Prince, CTO at Sports Thread."
    )
    language = "en-us"
    author_name = "Joseph Prince"
    author_email = "joseph@thejosephprince.com"
    author_link = "https://www.thejosephprince.com/about"
    feed_copyright = "Copyright © 2024-2026 Joseph Prince. All rights reserved."
    categories = (
        "Software Engineering",
        "Clean Architecture", 
        "Domain-Driven Design",
        "Python",
        "TypeScript",
        "React",
        "Django",
    )
    
    def items(self):
        """Return the 20 most recent published posts."""
        return BlogPostModel.objects.filter(
            status='published'
        ).order_by('-published_at')[:20]
    
    def item_title(self, item: BlogPostModel) -> str:
        """Return the post title."""
        return item.title
    
    def item_description(self, item: BlogPostModel) -> str:
        """Return the post excerpt."""
        return item.excerpt or item.content[:300]
    
    def item_link(self, item: BlogPostModel) -> str:
        """Return the full URL to the blog post."""
        return f"https://www.thejosephprince.com/blog/{item.slug}"
    
    def item_pubdate(self, item: BlogPostModel):
        """Return the publication date."""
        return item.published_at
    
    def item_updateddate(self, item: BlogPostModel):
        """Return the last updated date."""
        return item.updated_at
    
    def item_author_name(self, item: BlogPostModel) -> str:
        """Return author name."""
        return "Joseph Prince"
    
    def item_categories(self, item: BlogPostModel):
        """Return tags as categories."""
        return item.tags or []
