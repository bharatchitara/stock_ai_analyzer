from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.core.management import call_command
from datetime import datetime, timedelta
import pytz
import threading
import logging

from news.models import (
    NewsArticle, Recommendation, Category, Stock, MarketSession,
    UserPortfolio
)

logger = logging.getLogger(__name__)


def dashboard_home(request):
    """Main dashboard view"""
    # Get today's date in IST
    ist = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist).date()
    
    # Get today's pre-market news (before 9:10 AM)
    pre_market_news = NewsArticle.objects.filter(
        published_at__date=today,
        is_pre_market=True
    ).select_related('source', 'category').order_by('-published_at')[:10]
    
    # Get latest recommendations
    latest_recommendations = Recommendation.objects.filter(
        is_active=True,
        valid_until__gt=timezone.now()
    ).select_related('stock').order_by('-created_at')[:8]
    
    # Get sentiment distribution for today
    sentiment_stats = NewsArticle.objects.filter(
        published_at__date=today,
        is_pre_market=True
    ).values('sentiment').annotate(count=Count('sentiment'))
    
    # Get category distribution
    category_stats = NewsArticle.objects.filter(
        published_at__date=today,
        is_pre_market=True
    ).values('category__name').annotate(count=Count('category')).exclude(category=None)
    
    # Get market session info
    market_session, created = MarketSession.objects.get_or_create(date=today)
    
    # Get portfolio data (for default user or first available)
    portfolio_data = None
    try:
        user_portfolio = UserPortfolio.objects.first()
        if user_portfolio:
            portfolio_data = {
                'total_investment': user_portfolio.total_investment_value,
                'current_value': user_portfolio.total_current_value,
                'total_pnl': user_portfolio.total_pnl,
                'total_pnl_percent': user_portfolio.total_pnl_percentage,
                'holdings_count': user_portfolio.holdings.count(),
            }
    except:
        pass
    
    if not portfolio_data:
        portfolio_data = {
            'total_investment': 0,
            'current_value': 0,
            'total_pnl': 0,
            'total_pnl_percent': 0,
            'holdings_count': 0,
        }
    
    context = {
        'pre_market_news': pre_market_news,
        'latest_recommendations': latest_recommendations,
        'sentiment_stats': sentiment_stats,
        'category_stats': category_stats,
        'market_session': market_session,
        'today': today,
        'portfolio': portfolio_data,
    }
    
    return render(request, 'dashboard/home.html', context)


def news_list(request):
    """News listing page with filters"""
    # Get filter parameters
    category = request.GET.get('category')
    sentiment = request.GET.get('sentiment')
    source = request.GET.get('source')
    date_filter = request.GET.get('date', 'today')
    
    # Base queryset
    news_queryset = NewsArticle.objects.select_related('source', 'category').order_by('-published_at')
    
    # Apply filters
    ist = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist).date()
    
    if date_filter == 'today':
        news_queryset = news_queryset.filter(published_at__date=today)
    elif date_filter == 'yesterday':
        yesterday = today - timedelta(days=1)
        news_queryset = news_queryset.filter(published_at__date=yesterday)
    elif date_filter == 'week':
        week_ago = today - timedelta(days=7)
        news_queryset = news_queryset.filter(published_at__date__gte=week_ago)
    
    if category:
        news_queryset = news_queryset.filter(category__name=category.upper())
    
    if sentiment:
        news_queryset = news_queryset.filter(sentiment=sentiment.upper())
    
    if source:
        news_queryset = news_queryset.filter(source__name=source)
    
    # Pagination
    paginator = Paginator(news_queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = Category.objects.all()
    sources = NewsArticle.objects.values_list('source__name', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'sources': sources,
        'current_filters': {
            'category': category,
            'sentiment': sentiment,
            'source': source,
            'date': date_filter,
        }
    }
    
    return render(request, 'dashboard/news_list.html', context)


def news_detail(request, news_id):
    """Individual news article view"""
    article = get_object_or_404(NewsArticle, id=news_id)
    
    # Increment view count
    article.view_count += 1
    article.save(update_fields=['view_count'])
    
    # Get related recommendations for mentioned stocks
    related_recommendations = Recommendation.objects.filter(
        stock__in=article.mentioned_stocks.all(),
        is_active=True,
        valid_until__gt=timezone.now()
    ).select_related('stock')
    
    context = {
        'article': article,
        'related_recommendations': related_recommendations,
    }
    
    return render(request, 'dashboard/news_detail.html', context)


def recommendations_list(request):
    """Stock recommendations listing"""
    # Get filter parameters
    recommendation_type = request.GET.get('type')
    risk_level = request.GET.get('risk')
    stock_search = request.GET.get('stock')
    
    # Base queryset
    recommendations_queryset = Recommendation.objects.filter(
        is_active=True,
        valid_until__gt=timezone.now()
    ).select_related('stock').order_by('-confidence_level', '-created_at')
    
    # Apply filters
    if recommendation_type:
        recommendations_queryset = recommendations_queryset.filter(recommendation=recommendation_type.upper())
    
    if risk_level:
        recommendations_queryset = recommendations_queryset.filter(risk_level=risk_level.upper())
    
    if stock_search:
        recommendations_queryset = recommendations_queryset.filter(
            Q(stock__symbol__icontains=stock_search) |
            Q(stock__company_name__icontains=stock_search)
        )
    
    # Pagination
    paginator = Paginator(recommendations_queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get recommendation stats
    rec_stats = Recommendation.objects.filter(
        is_active=True,
        valid_until__gt=timezone.now()
    ).values('recommendation').annotate(count=Count('recommendation'))
    
    context = {
        'page_obj': page_obj,
        'rec_stats': rec_stats,
        'current_filters': {
            'type': recommendation_type,
            'risk': risk_level,
            'stock': stock_search,
        }
    }
    
    return render(request, 'dashboard/recommendations.html', context)


def watchlist(request):
    """User's personal watchlist"""
    # Get watchlist for first user or empty
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        first_user = User.objects.first()
        if first_user:
            user_watchlist = first_user.userwatchlist_set.filter(
                is_active=True
            ).select_related('stock')
        else:
            user_watchlist = []
    except:
        user_watchlist = []
    
    # Get latest recommendations for watchlist stocks
    watchlist_stocks = [item.stock for item in user_watchlist]
    watchlist_recommendations = Recommendation.objects.filter(
        stock__in=watchlist_stocks,
        is_active=True,
        valid_until__gt=timezone.now()
    ).select_related('stock')
    
    # Get recent news for watchlist stocks
    watchlist_news = NewsArticle.objects.filter(
        mentioned_stocks__in=watchlist_stocks,
        published_at__gte=timezone.now() - timedelta(days=7)
    ).distinct().select_related('source', 'category').order_by('-published_at')[:20]
    
    context = {
        'watchlist': user_watchlist,
        'recommendations': watchlist_recommendations,
        'recent_news': watchlist_news,
    }
    
    return render(request, 'dashboard/watchlist.html', context)


# API views for AJAX calls and charts

def sentiment_chart_data(request):
    """API endpoint for sentiment distribution chart"""
    date_filter = request.GET.get('date', 'today')
    
    ist = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist).date()
    
    if date_filter == 'today':
        date_range = [today]
    elif date_filter == 'week':
        date_range = [today - timedelta(days=i) for i in range(7)]
    else:
        date_range = [today]
    
    data = []
    for date in date_range:
        sentiment_counts = NewsArticle.objects.filter(
            published_at__date=date,
            is_pre_market=True
        ).values('sentiment').annotate(count=Count('sentiment'))
        
        daily_data = {
            'date': date.strftime('%Y-%m-%d'),
            'positive': 0,
            'negative': 0,
            'neutral': 0
        }
        
        for item in sentiment_counts:
            sentiment = item['sentiment'].lower()
            if sentiment in daily_data:
                daily_data[sentiment] = item['count']
        
        data.append(daily_data)
    
    return JsonResponse({'data': data})


def recommendation_chart_data(request):
    """API endpoint for recommendation distribution chart"""
    rec_counts = Recommendation.objects.filter(
        is_active=True,
        valid_until__gt=timezone.now()
    ).values('recommendation').annotate(count=Count('recommendation'))
    
    data = {item['recommendation']: item['count'] for item in rec_counts}
    
    return JsonResponse({'data': data})


def news_timeline_data(request):
    """API endpoint for news timeline chart"""
    days = int(request.GET.get('days', 7))
    
    ist = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist).date()
    
    timeline_data = []
    for i in range(days):
        date = today - timedelta(days=i)
        
        daily_count = NewsArticle.objects.filter(
            published_at__date=date,
            is_pre_market=True
        ).count()
        
        timeline_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': daily_count
        })
    
    timeline_data.reverse()
    return JsonResponse({'data': timeline_data})


def run_news_collection(request):
    """Trigger news collection in background (non-blocking)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    def background_task():
        """Run news scraping, analysis, and recommendations in background thread"""
        try:
            logger.info("Starting background news collection...")
            call_command('scrape_news')
            logger.info("Background news collection completed")
            
            # Run AI analysis on collected news
            logger.info("Starting AI analysis of collected news...")
            from news.tasks import analyze_news_batch
            analyze_result = analyze_news_batch()
            logger.info(f"AI analysis completed: {analyze_result}")
            
            # Generate recommendations based on analysis
            logger.info("Generating stock recommendations...")
            from news.tasks import generate_daily_recommendations
            rec_result = generate_daily_recommendations()
            logger.info(f"Recommendations generated: {rec_result}")
            
        except Exception as e:
            logger.error(f"Error in background news collection pipeline: {str(e)}")
    
    # Start background thread
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()
    
    return JsonResponse({
        'status': 'started',
        'message': 'News collection, analysis, and recommendations started in background. This may take 3-5 minutes.'
    })


def check_collection_status(request):
    """Check status of news collection"""
    ist = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist).date()
    
    # Get latest articles count
    recent_articles = NewsArticle.objects.filter(
        scraped_at__gte=timezone.now() - timedelta(minutes=10)
    ).count()
    
    recommendation_articles = NewsArticle.objects.filter(
        scraped_at__gte=timezone.now() - timedelta(minutes=10),
        is_recommendation=True
    ).count()
    
    total_today = NewsArticle.objects.filter(
        published_at__date=today
    ).count()
    
    return JsonResponse({
        'recent_articles': recent_articles,
        'recommendation_articles': recommendation_articles,
        'total_today': total_today
    })
    
    timeline_data.reverse()  # Show oldest to newest
    
    return JsonResponse({'data': timeline_data})


def trading_signals(request):
    """View for trading signals based on holdings changes and price movements"""
    from analysis.signal_analyzer import SignalAnalyzer
    from news.models import UserPortfolio, Stock
    from django.contrib.auth import get_user_model
    from portfolio.models import PromoterHolding
    from datetime import timedelta
    
    # Auto-fetch promoter holdings in background (non-blocking)
    from portfolio.stock_events_fetcher import StockEventFetcher
    
    def fetch_holdings_background():
        """Background task to fetch promoter holdings"""
        try:
            fetcher = StockEventFetcher()
            top_stocks = Stock.objects.filter(Q(is_nifty50=True) | Q(is_sensex=True))[:5]  # Reduced to 5 stocks
            
            fetch_count = 0
            saved_count = 0
            
            for stock in top_stocks:
                try:
                    # Fetch holdings data
                    holdings = fetcher.fetch_promoter_holding(stock.symbol)
                    
                    if holdings:
                        # Save to database
                        for holding_data in holdings:
                            try:
                                obj, created = PromoterHolding.objects.update_or_create(
                                    stock=stock,
                                    quarter_end_date=holding_data['quarter_end_date'],
                                    defaults=holding_data
                                )
                                if created:
                                    saved_count += 1
                            except Exception as e:
                                logger.warning(f"Error saving promoter holding: {e}")
                                continue
                        
                        fetch_count += 1
                    
                    # Add delay to avoid rate limiting
                    import time
                    time.sleep(5)  # Increased to 5 seconds
                except Exception as e:
                    logger.warning(f"Failed to fetch promoter holding for {stock.symbol}: {str(e)[:100]}")
                    continue
            
            logger.info(f"Background fetch completed: {fetch_count}/{len(top_stocks)} stocks fetched, {saved_count} new records saved")
        except Exception as e:
            logger.error(f"Background fetch error: {e}")
    
    # Only fetch if data is missing or old (don't fetch every time to avoid rate limits)
    latest_holding = PromoterHolding.objects.order_by('-quarter_end_date').first()
    should_fetch = False
    
    if not latest_holding:
        should_fetch = True
        logger.info("No promoter holdings data. Starting background fetch...")
    elif latest_holding.quarter_end_date < (timezone.now().date() - timedelta(days=7)):
        should_fetch = True
        logger.info("Promoter holdings data older than 7 days. Starting background fetch...")
    
    if should_fetch:
        # Start background thread (non-blocking)
        import threading
        fetch_thread = threading.Thread(target=fetch_holdings_background)
        fetch_thread.daemon = True
        fetch_thread.start()
    
    # Get user portfolio
    User = get_user_model()
    first_user = User.objects.first()
    portfolio_holdings = []
    
    if first_user:
        user_portfolio = UserPortfolio.objects.filter(user=first_user).first()
        if user_portfolio:
            portfolio_holdings = user_portfolio.holdings.select_related('stock').all()
    
    # Initialize analyzers
    analyzer = SignalAnalyzer()
    from analysis.entry_signal_analyzer import EntrySignalAnalyzer
    entry_analyzer = EntrySignalAnalyzer()
    
    # Get buy signals
    buy_signals = analyzer.get_all_buy_signals()
    
    # Get sell signals for held stocks
    sell_signals = analyzer.get_all_sell_signals(portfolio_holdings) if portfolio_holdings else {'promoter_decreased': []}
    
    # Get entry opportunities
    entry_opportunities = entry_analyzer.get_active_opportunities()
    
    # Group entry opportunities by type
    entry_by_type = {
        'PRICE_DIP': [],
        'ORDER_WIN': [],
        'DIVIDEND': [],
        'EXPANSION': [],
        'SPLIT': [],
        'BONUS': [],
    }
    
    for opp in entry_opportunities:
        if opp.opportunity_type in entry_by_type:
            entry_by_type[opp.opportunity_type].append(opp)
    
    context = {
        'fii_increased': buy_signals['fii_increased'],
        'top50_dipped': buy_signals['top50_dipped'],
        'promoter_increased': buy_signals['promoter_increased'],
        'promoter_decreased': sell_signals['promoter_decreased'],
        'has_portfolio': len(portfolio_holdings) > 0,
        'entry_opportunities': entry_opportunities,
        'entry_by_type': entry_by_type,
    }
    
    return render(request, 'dashboard/trading_signals.html', context)
