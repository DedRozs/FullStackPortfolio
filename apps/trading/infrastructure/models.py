"""Django ORM models for the Trading bounded context."""
from django.db import models
import uuid


class TradingPostModel(models.Model):
    """Django ORM model for TradingPost aggregate."""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
    
    class InstrumentChoices(models.TextChoices):
        NQ = 'NQ=F', 'E-mini Nasdaq-100'
        ES = 'ES=F', 'E-mini S&P 500'
        RTY = 'RTY=F', 'E-mini Russell 2000'
        YM = 'YM=F', 'E-mini Dow Jones'
    
    class PostTypeChoices(models.TextChoices):
        PRE_MARKET = 'pre_market', 'Pre-Market Analysis'
        POST_MARKET = 'post_market', 'Session Recap'
        WEEKLY_RECAP = 'weekly_recap', 'Weekly Recap'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument = models.CharField(max_length=10, choices=InstrumentChoices.choices)
    post_type = models.CharField(max_length=20, choices=PostTypeChoices.choices)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()  # Markdown content
    session_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    meta_description = models.CharField(max_length=300, blank=True, null=True)
    
    # Structured data for the post (JSON schema based on post_type)
    # Stores raw market data used to generate the content for:
    # 1. Weekly recaps to pull from daily post data
    # 2. Frontend to render structured tables/charts
    # 3. Consistency across regenerations
    structured_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    scheduled_for = models.DateTimeField(blank=True, null=True)
    
    # Related session data (optional FK, sessions can exist without posts)
    market_session = models.ForeignKey(
        'MarketSessionModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trading_posts',
    )
    weekly_session = models.ForeignKey(
        'WeeklySessionModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trading_posts',
    )
    
    class Meta:
        app_label = 'trading'
        db_table = 'trading_posts'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['instrument', 'post_type']),
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['session_date']),
            models.Index(fields=['scheduled_for']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['instrument', 'post_type', 'session_date'],
                name='unique_trading_post_per_session',
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.get_instrument_display()} - {self.title}"


class MarketSessionModel(models.Model):
    """Django ORM model for MarketSession entity.
    
    Stores daily trading session data for each instrument.
    """
    
    class InstrumentChoices(models.TextChoices):
        NQ = 'NQ=F', 'E-mini Nasdaq-100'
        ES = 'ES=F', 'E-mini S&P 500'
        RTY = 'RTY=F', 'E-mini Russell 2000'
        YM = 'YM=F', 'E-mini Dow Jones'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument = models.CharField(max_length=10, choices=InstrumentChoices.choices)
    session_date = models.DateField()
    
    # Session OHLC (stored as decimals for precision)
    open_price = models.DecimalField(max_digits=12, decimal_places=2)
    high_price = models.DecimalField(max_digits=12, decimal_places=2)
    low_price = models.DecimalField(max_digits=12, decimal_places=2)
    close_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Overnight session (Globex)
    overnight_high = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    overnight_low = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    
    # Volume
    volume = models.BigIntegerField(default=0)
    
    # Prior session reference
    prior_close = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    
    # Calculated change metrics
    change_points = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    change_percent = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'trading'
        db_table = 'trading_market_sessions'
        ordering = ['-session_date']
        indexes = [
            models.Index(fields=['instrument', '-session_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['instrument', 'session_date'],
                name='unique_session_per_day',
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.get_instrument_display()} - {self.session_date}"


class WeeklySessionModel(models.Model):
    """Django ORM model for WeeklySession entity.
    
    Stores aggregated weekly data for each instrument.
    """
    
    class InstrumentChoices(models.TextChoices):
        NQ = 'NQ=F', 'E-mini Nasdaq-100'
        ES = 'ES=F', 'E-mini S&P 500'
        RTY = 'RTY=F', 'E-mini Russell 2000'
        YM = 'YM=F', 'E-mini Dow Jones'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument = models.CharField(max_length=10, choices=InstrumentChoices.choices)
    week_start_date = models.DateField()  # Monday of the week
    week_end_date = models.DateField()    # Friday of the week
    
    # Weekly OHLC
    open_price = models.DecimalField(max_digits=12, decimal_places=2)
    high_price = models.DecimalField(max_digits=12, decimal_places=2)
    low_price = models.DecimalField(max_digits=12, decimal_places=2)
    close_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Weekly performance
    change_points = models.DecimalField(max_digits=12, decimal_places=2)
    change_percent = models.DecimalField(max_digits=8, decimal_places=4)
    
    # Total volume for the week
    total_volume = models.BigIntegerField(default=0)
    
    # Number of trading days
    trading_days = models.PositiveSmallIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'trading'
        db_table = 'trading_weekly_sessions'
        ordering = ['-week_start_date']
        indexes = [
            models.Index(fields=['instrument', '-week_start_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['instrument', 'week_start_date'],
                name='unique_weekly_session_per_week',
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.get_instrument_display()} - Week of {self.week_start_date}"


class PriceLevelModel(models.Model):
    """Django ORM model for PriceLevel entity.
    
    Stores individual price levels for support/resistance analysis.
    """
    
    class InstrumentChoices(models.TextChoices):
        NQ = 'NQ=F', 'E-mini Nasdaq-100'
        ES = 'ES=F', 'E-mini S&P 500'
        RTY = 'RTY=F', 'E-mini Russell 2000'
        YM = 'YM=F', 'E-mini Dow Jones'
    
    class LevelTypeChoices(models.TextChoices):
        PRIOR_HIGH = 'prior_high', 'Prior Day High'
        PRIOR_LOW = 'prior_low', 'Prior Day Low'
        PRIOR_CLOSE = 'prior_close', 'Prior Day Close'
        OVERNIGHT_HIGH = 'overnight_high', 'Overnight High'
        OVERNIGHT_LOW = 'overnight_low', 'Overnight Low'
        WEEKLY_OPEN = 'weekly_open', 'Weekly Open'
        WEEKLY_HIGH = 'weekly_high', 'Weekly High'
        WEEKLY_LOW = 'weekly_low', 'Weekly Low'
        MONTHLY_HIGH = 'monthly_high', 'Monthly High'
        MONTHLY_LOW = 'monthly_low', 'Monthly Low'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument = models.CharField(max_length=10, choices=InstrumentChoices.choices)
    level_type = models.CharField(max_length=20, choices=LevelTypeChoices.choices)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    session_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'trading'
        db_table = 'trading_price_levels'
        ordering = ['-session_date', 'level_type']
        indexes = [
            models.Index(fields=['instrument', '-session_date']),
            models.Index(fields=['instrument', 'level_type']),
        ]
    
    def __str__(self) -> str:
        return f"{self.get_instrument_display()} {self.get_level_type_display()}: {self.price}"


class TradingPostPriceLevelModel(models.Model):
    """Join table for TradingPost to PriceLevel many-to-many relationship."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trading_post = models.ForeignKey(
        TradingPostModel,
        on_delete=models.CASCADE,
        related_name='post_price_levels',
    )
    price_level = models.ForeignKey(
        PriceLevelModel,
        on_delete=models.CASCADE,
        related_name='level_trading_posts',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'trading'
        db_table = 'trading_post_price_levels'
        constraints = [
            models.UniqueConstraint(
                fields=['trading_post', 'price_level'],
                name='unique_post_level_relationship',
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.trading_post_id} - {self.price_level_id}"


class IntradayBarModel(models.Model):
    """Stores 1-minute OHLCV bars for intraday analysis.
    
    Data is fetched daily from Databento and stored locally to:
    1. Reduce ongoing API costs (fetch once, query forever)
    2. Provide intraday context for AI content generation
    3. Enable session progression analysis (high/low timing, volume distribution)
    """
    
    class InstrumentChoices(models.TextChoices):
        NQ = 'NQ=F', 'E-mini Nasdaq-100'
        ES = 'ES=F', 'E-mini S&P 500'
        RTY = 'RTY=F', 'E-mini Russell 2000'
        YM = 'YM=F', 'E-mini Dow Jones'
    
    class SessionChoices(models.TextChoices):
        OVERNIGHT = 'overnight', 'Overnight Session (6PM-9:30AM ET)'
        RTH = 'rth', 'Regular Trading Hours (9:30AM-5PM ET)'
    
    # Composite primary key fields
    instrument = models.CharField(max_length=10, choices=InstrumentChoices.choices)
    timestamp = models.DateTimeField()  # Bar start time in UTC
    
    # OHLCV data
    open_price = models.DecimalField(max_digits=12, decimal_places=2)
    high_price = models.DecimalField(max_digits=12, decimal_places=2)
    low_price = models.DecimalField(max_digits=12, decimal_places=2)
    close_price = models.DecimalField(max_digits=12, decimal_places=2)
    volume = models.BigIntegerField()
    
    # Derived fields for efficient querying
    session_date = models.DateField()  # Trading date this bar belongs to
    session_type = models.CharField(
        max_length=20,
        choices=SessionChoices.choices,
        default=SessionChoices.RTH,
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'trading'
        db_table = 'trading_intraday_bars'
        ordering = ['instrument', 'timestamp']
        indexes = [
            models.Index(fields=['instrument', 'session_date']),
            models.Index(fields=['instrument', 'session_date', 'session_type']),
            models.Index(fields=['instrument', 'timestamp']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['instrument', 'timestamp'],
                name='unique_bar_per_instrument_timestamp',
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.instrument} {self.timestamp}: O={self.open_price} H={self.high_price} L={self.low_price} C={self.close_price}"
