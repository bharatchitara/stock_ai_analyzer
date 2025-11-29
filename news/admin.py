from django.contrib import admin
from .models import (
    NewsSource, Category, Stock, NewsArticle, 
    Recommendation, UserWatchlist, MarketSession,
    UserPortfolio, PortfolioHolding, PersonalizedRecommendation
)


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = ['created_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color_code']
    list_filter = ['name']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'company_name', 'sector', 'is_nifty50', 'is_sensex']
    list_filter = ['sector', 'is_nifty50', 'is_sensex']
    search_fields = ['symbol', 'company_name', 'sector']
    list_editable = ['is_nifty50', 'is_sensex']


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = [
        'title_short', 'source', 'category', 'sentiment', 
        'impact_level', 'is_pre_market', 'published_at'
    ]
    list_filter = [
        'source', 'category', 'sentiment', 'impact_level', 
        'is_pre_market', 'is_analyzed', 'published_at'
    ]
    search_fields = ['title', 'content', 'summary']
    readonly_fields = ['scraped_at', 'analyzed_at', 'view_count']
    filter_horizontal = ['mentioned_stocks']
    date_hierarchy = 'published_at'
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'summary', 'url', 'source', 'category')
        }),
        ('AI Analysis', {
            'fields': ('sentiment', 'sentiment_score', 'impact_level', 'confidence_score', 'is_analyzed')
        }),
        ('Related Data', {
            'fields': ('mentioned_stocks',)
        }),
        ('Timestamps', {
            'fields': ('published_at', 'scraped_at', 'analyzed_at', 'is_pre_market'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('view_count',),
            'classes': ('collapse',)
        })
    )


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'stock', 'recommendation', 'risk_level', 
        'confidence_level', 'target_price', 'is_active', 'created_at'
    ]
    list_filter = [
        'recommendation', 'risk_level', 'is_active', 
        'created_at', 'valid_until'
    ]
    search_fields = ['stock__symbol', 'stock__company_name', 'reasoning']
    readonly_fields = ['created_at']
    filter_horizontal = ['related_articles']
    date_hierarchy = 'created_at'


@admin.register(UserWatchlist)
class UserWatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'added_at', 'is_active']
    list_filter = ['is_active', 'added_at']
    search_fields = ['user__username', 'stock__symbol', 'stock__company_name']


@admin.register(MarketSession)
class MarketSessionAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_news_collected', 'total_recommendations',
        'news_collection_completed', 'analysis_completed'
    ]
    list_filter = ['date']
    readonly_fields = [
        'news_collection_started', 'news_collection_completed',
        'analysis_completed', 'recommendations_generated'
    ]


@admin.register(UserPortfolio)
class UserPortfolioAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_holdings_count', 'created_at', 'updated_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


class PersonalizedRecommendationInline(admin.TabularInline):
    model = PersonalizedRecommendation
    extra = 0
    readonly_fields = ['created_at']
    fields = ['recommendation', 'priority', 'confidence_score', 'reasoning', 'is_active']


@admin.register(PortfolioHolding)
class PortfolioHoldingAdmin(admin.ModelAdmin):
    list_display = [
        'portfolio_user', 'stock', 'quantity', 'average_price',
        'current_value_display', 'pnl_display', 'purchase_date'
    ]
    list_filter = ['portfolio__user', 'stock__sector', 'purchase_date']
    search_fields = ['portfolio__user__username', 'stock__symbol', 'stock__company_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PersonalizedRecommendationInline]
    
    def portfolio_user(self, obj):
        return obj.portfolio.user.username
    portfolio_user.short_description = 'User'
    
    def current_value_display(self, obj):
        return f"₹{obj.current_value:,.2f}"
    current_value_display.short_description = 'Current Value'
    
    def pnl_display(self, obj):
        pnl = obj.pnl
        pnl_pct = obj.pnl_percentage
        color = 'green' if pnl >= 0 else 'red'
        return f'<span style="color: {color};">₹{pnl:,.2f} ({pnl_pct:+.2f}%)</span>'
    pnl_display.short_description = 'P&L'
    pnl_display.allow_tags = True


@admin.register(PersonalizedRecommendation)
class PersonalizedRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'holding_stock', 'recommendation', 'priority', 
        'confidence_score', 'is_active', 'created_at'
    ]
    list_filter = ['recommendation', 'priority', 'is_active', 'created_at']
    search_fields = ['holding__stock__symbol', 'reasoning']
    readonly_fields = ['created_at']
    filter_horizontal = ['related_articles']
    
    def holding_stock(self, obj):
        return f"{obj.holding.portfolio.user.username} - {obj.holding.stock.symbol}"
    holding_stock.short_description = 'Holding'
