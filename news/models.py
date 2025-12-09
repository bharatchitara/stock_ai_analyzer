from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class AIConfig(models.Model):
    """Configuration for AI models used in the application"""
    name = models.CharField(max_length=100, unique=True, help_text="Configuration name (e.g., 'default', 'production')")
    gemini_model = models.CharField(max_length=100, default='gemini-2.5-flash', help_text="Gemini model name")
    openai_model = models.CharField(max_length=100, default='gpt-3.5-turbo', help_text="OpenAI model name")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - Gemini: {self.gemini_model}"
    
    @classmethod
    def get_active_config(cls):
        """Get the active AI configuration"""
        config = cls.objects.filter(is_active=True).first()
        if not config:
            # Create default config if none exists
            config = cls.objects.create(
                name='default',
                gemini_model='gemini-2.5-flash',
                openai_model='gpt-3.5-turbo',
                is_active=True
            )
        return config
    
    class Meta:
        verbose_name = 'AI Configuration'
        verbose_name_plural = 'AI Configurations'
        ordering = ['-is_active', '-updated_at']


class NewsSource(models.Model):
    """Model for news sources like Economic Times, Business Standard, etc."""
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField()
    rss_feed = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Category(models.Model):
    """Categories for news articles"""
    CATEGORY_CHOICES = [
        ('MARKET_OPEN', 'Market Opening'),
        ('EARNINGS', 'Earnings Report'),
        ('POLICY', 'Government Policy'),
        ('GLOBAL', 'Global Impact'),
        ('SECTOR', 'Sector News'),
        ('IPO', 'IPO/Listings'),
        ('MERGER', 'Mergers & Acquisitions'),
        ('COMMODITY', 'Commodity News'),
        ('CURRENCY', 'Currency/Forex'),
        ('REGULATORY', 'Regulatory Changes'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=7, default='#007bff')  # Hex color
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']


class Stock(models.Model):
    """Model for stock information"""
    symbol = models.CharField(max_length=20, unique=True)  # e.g., RELIANCE, TCS
    company_name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100)
    market_cap = models.BigIntegerField(null=True, blank=True)
    is_nifty50 = models.BooleanField(default=False)
    is_sensex = models.BooleanField(default=False)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_updated_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.symbol} - {self.company_name}"
    
    class Meta:
        ordering = ['symbol']


class NewsArticle(models.Model):
    """Main model for news articles"""
    SENTIMENT_CHOICES = [
        ('POSITIVE', 'Positive'),
        ('NEGATIVE', 'Negative'),
        ('NEUTRAL', 'Neutral'),
        ('PENDING', 'Pending Analysis'),
    ]
    
    IMPACT_CHOICES = [
        ('HIGH', 'High Impact'),
        ('MEDIUM', 'Medium Impact'),
        ('LOW', 'Low Impact'),
        ('PENDING', 'Pending Analysis'),
    ]
    
    title = models.CharField(max_length=500)
    content = models.TextField()
    summary = models.TextField(blank=True)
    url = models.URLField(unique=True)
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    # AI Analysis fields
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES, default='PENDING')
    sentiment_score = models.FloatField(null=True, blank=True)  # -1 to 1 scale
    impact_level = models.CharField(max_length=10, choices=IMPACT_CHOICES, default='PENDING')
    confidence_score = models.FloatField(null=True, blank=True)  # 0 to 1 scale
    
    # AI-generated visual summary fields
    ai_summary = models.JSONField(null=True, blank=True)  # Stores key_points, impact, emoji
    key_points = models.TextField(blank=True)  # Brief bullet points
    impact_summary = models.CharField(max_length=200, blank=True)  # One-line impact
    article_emoji = models.CharField(max_length=10, blank=True)  # Visual indicator
    
    # Related stocks mentioned in the news
    mentioned_stocks = models.ManyToManyField(Stock, blank=True)
    
    # Timestamps
    published_at = models.DateTimeField()
    scraped_at = models.DateTimeField(auto_now_add=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    is_analyzed = models.BooleanField(default=False)
    is_pre_market = models.BooleanField(default=False)  # Published before 9:10 AM
    is_recommendation = models.BooleanField(default=False)  # Contains stock recommendations
    view_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.title[:100]}..."
    
    def save(self, *args, **kwargs):
        # Check if article is published before market opening (9:10 AM IST)
        if self.published_at:
            market_open_time = self.published_at.replace(hour=9, minute=10, second=0, microsecond=0)
            self.is_pre_market = self.published_at < market_open_time
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['published_at']),
            models.Index(fields=['sentiment']),
            models.Index(fields=['is_pre_market']),
            models.Index(fields=['source', 'published_at']),
        ]


class Recommendation(models.Model):
    """AI-generated stock recommendations based on news analysis"""
    RECOMMENDATION_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('HOLD', 'Hold'),
        ('WATCH', 'Watch'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
    ]
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    recommendation = models.CharField(max_length=10, choices=RECOMMENDATION_CHOICES)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    
    # Price targets and analysis
    target_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stop_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confidence_level = models.FloatField()  # 0 to 100 percentage
    
    # Related news articles that influenced this recommendation
    related_articles = models.ManyToManyField(NewsArticle, blank=True)
    
    # AI analysis
    reasoning = models.TextField()
    key_factors = models.JSONField(default=list)  # List of key factors
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()  # Recommendation expiry
    
    # Status
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.recommendation} {self.stock.symbol} - {self.confidence_level}%"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stock', 'created_at']),
            models.Index(fields=['recommendation']),
            models.Index(fields=['is_active', 'valid_until']),
        ]


class UserWatchlist(models.Model):
    """User's personalized stock watchlist"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'stock']
        ordering = ['added_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol}"


class MarketSession(models.Model):
    """Track daily market sessions and news collection status"""
    date = models.DateField(unique=True)
    news_collection_started = models.DateTimeField(null=True, blank=True)
    news_collection_completed = models.DateTimeField(null=True, blank=True)
    analysis_completed = models.DateTimeField(null=True, blank=True)
    recommendations_generated = models.DateTimeField(null=True, blank=True)
    
    total_news_collected = models.PositiveIntegerField(default=0)
    total_recommendations = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Market Session - {self.date}"
    
    class Meta:
        ordering = ['-date']


class UserPortfolio(models.Model):
    """Model for user's stock portfolio"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Portfolio"
    
    @property
    def total_holdings_count(self):
        return self.holdings.count()
    
    @property
    def total_investment_value(self):
        return sum(holding.total_value for holding in self.holdings.all())
    
    @property
    def total_current_value(self):
        return sum(holding.current_value for holding in self.holdings.all())
    
    @property
    def total_pnl(self):
        return self.total_current_value - self.total_investment_value
    
    @property
    def total_pnl_percentage(self):
        if self.total_investment_value > 0:
            return (self.total_pnl / self.total_investment_value) * 100
        return 0


class PortfolioHolding(models.Model):
    """Model for individual stock holdings in user portfolio"""
    portfolio = models.ForeignKey(UserPortfolio, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField()
    notes = models.TextField(blank=True, help_text="Personal notes about this holding")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['portfolio', 'stock']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.portfolio.user.username} - {self.stock.symbol} ({self.quantity} shares)"
    
    @property
    def total_value(self):
        """Total investment value (quantity * average_price)"""
        return float(self.quantity) * float(self.average_price)
    
    @property
    def current_value(self):
        """Current market value"""
        if self.stock.current_price:
            return float(self.quantity) * float(self.stock.current_price)
        return self.total_value
    
    @property
    def pnl(self):
        """Profit/Loss amount"""
        return self.current_value - self.total_value
    
    @property
    def pnl_percentage(self):
        """Profit/Loss percentage"""
        if self.total_value > 0:
            return (self.pnl / self.total_value) * 100
        return 0
    
    @property
    def is_profitable(self):
        """Whether this holding is in profit"""
        return self.pnl > 0


class PersonalizedRecommendation(models.Model):
    """Personalized recommendations for user's portfolio holdings"""
    RECOMMENDATION_CHOICES = [
        ('HOLD', 'Hold'),
        ('BUY_MORE', 'Buy More'),
        ('SELL_PARTIAL', 'Sell Partial'),
        ('SELL_ALL', 'Sell All'),
        ('WATCH', 'Watch Closely'),
    ]
    
    PRIORITY_CHOICES = [
        ('HIGH', 'High Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('LOW', 'Low Priority'),
    ]
    
    holding = models.ForeignKey(PortfolioHolding, on_delete=models.CASCADE, related_name='recommendations')
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    confidence_score = models.FloatField()  # 0 to 1
    reasoning = models.TextField()
    key_factors = models.JSONField(default=list)  # List of key factors
    target_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stop_loss_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Related news articles that influenced this recommendation
    related_articles = models.ManyToManyField('NewsArticle', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at', '-priority']
    
    def __str__(self):
        return f"{self.holding.stock.symbol} - {self.recommendation} ({self.priority} Priority)"
