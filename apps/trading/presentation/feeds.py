"""
RSS Feeds for Trading Blog Posts.

Provides RSS 2.0 feeds for trading content syndication, improving SEO discoverability.
Supports both all-instruments feed and per-instrument feeds.
"""
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed

from apps.trading.infrastructure.models import TradingPostModel
from apps.trading.domain.value_objects import Instrument


class TradingPostFeed(Feed):
    """RSS feed for all published trading posts."""
    
    title = "Joseph Prince | Trading Analysis Blog"
    link = "https://www.thejosephprince.com/trading-blog"
    description = (
        "Daily pre-market analysis and session recaps for index futures: "
        "NQ (E-mini Nasdaq-100), ES (E-mini S&P 500), RTY (E-mini Russell 2000), "
        "and YM (E-mini Dow Jones). Technical levels and key zones for active traders."
    )
    language = "en-us"
    author_name = "Joseph Prince"
    author_email = "joseph@thejosephprince.com"
    author_link = "https://www.thejosephprince.com/about"
    feed_copyright = "Copyright © 2024-2026 Joseph Prince. All rights reserved."
    categories = (
        "Trading",
        "Futures",
        "Technical Analysis",
        "E-mini Nasdaq",
        "E-mini S&P 500",
        "Market Analysis",
    )
    
    def items(self):
        """Return the 20 most recent published posts."""
        return TradingPostModel.objects.filter(
            status='published'
        ).order_by('-published_at')[:20]
    
    def item_title(self, item: TradingPostModel) -> str:
        """Return the post title."""
        return item.title
    
    def item_description(self, item: TradingPostModel) -> str:
        """Return the post meta description or excerpt."""
        if item.meta_description:
            return item.meta_description
        # Generate excerpt from content
        content = item.content[:300]
        return content.strip() + '...' if len(item.content) > 300 else content
    
    def item_link(self, item: TradingPostModel) -> str:
        """Return the full URL to the trading post."""
        return f"https://www.thejosephprince.com/trading-blog/{item.slug}"
    
    def item_pubdate(self, item: TradingPostModel):
        """Return the publication date."""
        return item.published_at
    
    def item_updateddate(self, item: TradingPostModel):
        """Return the last updated date."""
        return item.updated_at
    
    def item_author_name(self, item: TradingPostModel) -> str:
        """Return author name."""
        return "Joseph Prince"
    
    def item_categories(self, item: TradingPostModel):
        """Return categories based on instrument and post type."""
        categories = ['Futures', 'Trading']
        
        # Add instrument category
        instrument_categories = {
            'NQ=F': 'E-mini Nasdaq-100',
            'ES=F': 'E-mini S&P 500',
            'RTY=F': 'E-mini Russell 2000',
            'YM=F': 'E-mini Dow Jones',
        }
        if item.instrument in instrument_categories:
            categories.append(instrument_categories[item.instrument])
        
        # Add post type category
        type_categories = {
            'pre_market': 'Pre-Market Analysis',
            'post_market': 'Session Recap',
            'weekly_recap': 'Weekly Recap',
        }
        if item.post_type in type_categories:
            categories.append(type_categories[item.post_type])
        
        return categories


class InstrumentPostFeed(Feed):
    """RSS feed for a specific instrument's posts."""
    
    def get_object(self, request, instrument: str):
        """Get the instrument from the URL."""
        # Validate and normalize instrument
        try:
            return Instrument.from_short_name(instrument.upper())
        except ValueError:
            return None
    
    def title(self, instrument: Instrument | None):
        """Return feed title for the instrument."""
        if instrument is None:
            return "Joseph Prince | Trading Analysis"
        return f"{instrument.display_name} Analysis | Joseph Prince Trading Blog"
    
    def link(self, instrument: Instrument | None):
        """Return feed link."""
        if instrument is None:
            return "https://www.thejosephprince.com/trading-blog"
        return f"https://www.thejosephprince.com/trading-blog/{instrument.short_name.lower()}"
    
    def description(self, instrument: Instrument | None):
        """Return feed description for the instrument."""
        if instrument is None:
            return "Trading analysis and market insights."
        return (
            f"Daily pre-market analysis and session recaps for {instrument.display_name} "
            f"({instrument.short_name}) futures. Technical levels, key zones, and trading "
            f"insights for active futures traders."
        )
    
    def items(self, instrument: Instrument | None):
        """Return the 20 most recent published posts for this instrument."""
        if instrument is None:
            return TradingPostModel.objects.none()
        
        return TradingPostModel.objects.filter(
            status='published',
            instrument=instrument.value,
        ).order_by('-published_at')[:20]
    
    def item_title(self, item: TradingPostModel) -> str:
        """Return the post title."""
        return item.title
    
    def item_description(self, item: TradingPostModel) -> str:
        """Return the post meta description or excerpt."""
        if item.meta_description:
            return item.meta_description
        content = item.content[:300]
        return content.strip() + '...' if len(item.content) > 300 else content
    
    def item_link(self, item: TradingPostModel) -> str:
        """Return the full URL to the trading post."""
        return f"https://www.thejosephprince.com/trading-blog/{item.slug}"
    
    def item_pubdate(self, item: TradingPostModel):
        """Return the publication date."""
        return item.published_at
    
    def item_author_name(self, item: TradingPostModel) -> str:
        """Return author name."""
        return "Joseph Prince"
