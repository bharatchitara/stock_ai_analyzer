from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import pytz
import logging

from .models import NewsArticle, NewsSource, Category, Stock, Recommendation, MarketSession, PortfolioHolding
from .scraper import NewsScraper, StockMentionExtractor, NewsSourceConfig
from analysis.ai_analyzer import NewsAnalyzer, RecommendationEngine

logger = logging.getLogger(__name__)

@shared_task
def collect_morning_news():
    """
    Celery task to collect morning news before market opening
    Runs at 6:00 AM IST daily
    """
    logger.info("Starting morning news collection task...")
    
    ist = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist).date()
    
    # Get or create today's market session
    market_session, created = MarketSession.objects.get_or_create(date=today)
    market_session.news_collection_started = timezone.now()
    market_session.save()
    
    try:
        # Initialize scraper and extractor
        scraper = NewsScraper()
        stock_extractor = StockMentionExtractor()
        
        # Scrape all news sources
        all_articles = scraper.scrape_all_sources()
        
        total_saved = 0
        
        for source_key, articles in all_articles.items():
            # Get or create news source
            source_config = NewsSourceConfig.SOURCES.get(source_key, {})
            source_name = source_config.get('name', source_key)
            
            news_source, created = NewsSource.objects.get_or_create(
                name=source_name,
                defaults={
                    'url': source_config.get('base_url', ''),
                    'is_active': True
                }
            )
            
            for article_data in articles:
                try:
                    # Check if article already exists
                    if NewsArticle.objects.filter(url=article_data['url']).exists():
                        continue
                    
                    # Extract mentioned stocks
                    full_text = f"{article_data.get('title', '')} {article_data.get('content', '')}"
                    mentioned_stock_symbols = stock_extractor.extract_mentioned_stocks(full_text)
                    
                    # Create news article
                    article = NewsArticle.objects.create(
                        title=article_data.get('title', ''),
                        content=article_data.get('content', ''),
                        summary=article_data.get('summary', ''),
                        url=article_data['url'],
                        source=news_source,
                        published_at=article_data['published_at'],
                    )
                    
                    # Add mentioned stocks
                    if mentioned_stock_symbols:
                        stocks = Stock.objects.filter(symbol__in=mentioned_stock_symbols)
                        article.mentioned_stocks.set(stocks)
                    
                    total_saved += 1
                    logger.info(f"Saved article: {article.title[:50]}...")
                    
                except Exception as e:
                    logger.error(f"Error saving article: {str(e)}")
                    continue
        
        # Update market session
        market_session.news_collection_completed = timezone.now()
        market_session.total_news_collected = total_saved
        market_session.save()
        
        logger.info(f"Morning news collection completed. Saved {total_saved} articles.")
        return {'status': 'success', 'articles_saved': total_saved}
        
    except Exception as e:
        logger.error(f"Error in morning news collection: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def analyze_news_batch():
    """
    Celery task to analyze collected news using AI
    Runs at 7:30 AM IST daily
    """
    logger.info("Starting news analysis task...")
    
    ist = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist).date()
    
    try:
        # Get today's unanalyzed articles
        unanalyzed_articles = NewsArticle.objects.filter(
            published_at__date=today,
            is_analyzed=False
        ).select_related('source', 'category').prefetch_related('mentioned_stocks')
        
        if not unanalyzed_articles.exists():
            logger.info("No unanalyzed articles found for today.")
            return {'status': 'success', 'articles_analyzed': 0}
        
        analyzer = NewsAnalyzer()
        analyzed_count = 0
        
        for article in unanalyzed_articles:
            try:
                # Get mentioned stock symbols
                mentioned_stocks = list(article.mentioned_stocks.values_list('symbol', flat=True))
                
                # Analyze article
                analysis_result = analyzer.analyze_article(
                    title=article.title,
                    content=article.content,
                    mentioned_stocks=mentioned_stocks
                )
                
                # Update article with analysis results
                article.sentiment = analysis_result['sentiment']
                article.sentiment_score = analysis_result['sentiment_score']
                article.impact_level = analysis_result['impact_level']
                article.confidence_score = analysis_result['confidence_score']
                
                # Update summary if generated
                if analysis_result.get('summary') and not article.summary:
                    article.summary = analysis_result['summary']
                
                # Set category if determined
                if analysis_result.get('category'):
                    try:
                        category = Category.objects.get(name=analysis_result['category'])
                        article.category = category
                    except Category.DoesNotExist:
                        pass
                
                article.is_analyzed = True
                article.analyzed_at = timezone.now()
                article.save()
                
                analyzed_count += 1
                logger.info(f"Analyzed: {article.title[:50]}... - {analysis_result['sentiment']}")
                
            except Exception as e:
                logger.error(f"Error analyzing article {article.id}: {str(e)}")
                continue
        
        # Update market session
        market_session = MarketSession.objects.get(date=today)
        market_session.analysis_completed = timezone.now()
        market_session.save()
        
        logger.info(f"News analysis completed. Analyzed {analyzed_count} articles.")
        return {'status': 'success', 'articles_analyzed': analyzed_count}
        
    except Exception as e:
        logger.error(f"Error in news analysis: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def generate_daily_recommendations():
    """
    Celery task to generate stock recommendations based on analyzed news
    Runs at 8:30 AM IST daily
    """
    logger.info("Starting recommendation generation task...")
    
    ist = pytz.timezone('Asia/Kolkata')
    today = timezone.now().astimezone(ist).date()
    
    try:
        # Get today's analyzed articles
        analyzed_articles = NewsArticle.objects.filter(
            published_at__date=today,
            is_analyzed=True
        ).select_related('source', 'category').prefetch_related('mentioned_stocks')
        
        if not analyzed_articles.exists():
            logger.info("No analyzed articles found for recommendation generation.")
            return {'status': 'success', 'recommendations_generated': 0}
        
        # Prepare article data for recommendation engine
        article_data = []
        for article in analyzed_articles:
            article_info = {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'sentiment': article.sentiment,
                'sentiment_score': article.sentiment_score,
                'impact_level': article.impact_level,
                'category': article.category.name if article.category else 'OTHER',
                'mentioned_stocks': list(article.mentioned_stocks.values_list('symbol', flat=True))
            }
            article_data.append(article_info)
        
        # Generate recommendations
        recommendation_engine = RecommendationEngine()
        recommendations = recommendation_engine.generate_stock_recommendations(article_data)
        
        generated_count = 0
        
        for rec_data in recommendations:
            try:
                # Get stock object
                stock = Stock.objects.get(symbol=rec_data['stock_symbol'])
                
                # Deactivate old recommendations for this stock
                Recommendation.objects.filter(
                    stock=stock,
                    is_active=True
                ).update(is_active=False)
                
                # Create new recommendation
                valid_until = timezone.now() + timedelta(days=1)  # Valid for 24 hours
                
                recommendation = Recommendation.objects.create(
                    stock=stock,
                    recommendation=rec_data['recommendation'],
                    risk_level=rec_data['risk_level'],
                    confidence_level=rec_data['confidence_level'],
                    reasoning=rec_data['reasoning'],
                    key_factors=rec_data['key_factors'],
                    valid_until=valid_until,
                    is_active=True
                )
                
                # Link related articles
                if rec_data.get('related_articles'):
                    related_articles = NewsArticle.objects.filter(
                        id__in=rec_data['related_articles']
                    )
                    recommendation.related_articles.set(related_articles)
                
                generated_count += 1
                logger.info(f"Generated recommendation: {rec_data['recommendation']} {stock.symbol}")
                
            except Stock.DoesNotExist:
                logger.warning(f"Stock not found: {rec_data['stock_symbol']}")
                continue
            except Exception as e:
                logger.error(f"Error creating recommendation: {str(e)}")
                continue
        
        # Update market session
        market_session = MarketSession.objects.get(date=today)
        market_session.recommendations_generated = timezone.now()
        market_session.total_recommendations = generated_count
        market_session.save()
        
        logger.info(f"Recommendation generation completed. Generated {generated_count} recommendations.")
        return {'status': 'success', 'recommendations_generated': generated_count}
        
    except Exception as e:
        logger.error(f"Error in recommendation generation: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_data():
    """
    Cleanup old news articles and recommendations
    Run this weekly to keep database size manageable
    """
    logger.info("Starting data cleanup task...")
    
    try:
        # Delete news articles older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        old_articles = NewsArticle.objects.filter(published_at__lt=cutoff_date)
        deleted_articles = old_articles.count()
        old_articles.delete()
        
        # Delete inactive recommendations older than 7 days
        old_recommendations = Recommendation.objects.filter(
            is_active=False,
            created_at__lt=timezone.now() - timedelta(days=7)
        )
        deleted_recommendations = old_recommendations.count()
        old_recommendations.delete()
        
        # Delete old market sessions (keep last 30 days)
        old_sessions = MarketSession.objects.filter(
            date__lt=timezone.now().date() - timedelta(days=30)
        )
        deleted_sessions = old_sessions.count()
        old_sessions.delete()
        
        logger.info(f"Cleanup completed: {deleted_articles} articles, {deleted_recommendations} recommendations, {deleted_sessions} sessions deleted")
        
        return {
            'status': 'success',
            'deleted_articles': deleted_articles,
            'deleted_recommendations': deleted_recommendations,
            'deleted_sessions': deleted_sessions
        }
        
    except Exception as e:
        logger.error(f"Error in data cleanup: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def fetch_holdings_news():
    """
    Celery task to fetch latest news for portfolio holdings
    Runs every 6 hours
    """
    logger.info("Starting holdings news fetch task...")
    
    try:
        from news.scraper import NewsScraper, StockMentionExtractor
        
        # Get all unique stocks from holdings
        stock_ids = PortfolioHolding.objects.values_list('stock_id', flat=True).distinct()
        stocks = Stock.objects.filter(id__in=stock_ids)
        
        if not stocks.exists():
            logger.warning("No holdings found in portfolio")
            return {'status': 'success', 'message': 'No holdings to fetch news for'}
        
        scraper = NewsScraper()
        extractor = StockMentionExtractor()
        
        total_new = 0
        total_skipped = 0
        cutoff_time = timezone.now() - timedelta(hours=6)  # Only fetch news from last 6 hours
        
        for stock in stocks:
            logger.info(f"Fetching news for {stock.symbol}...")
            
            try:
                # Fetch news articles for this stock
                articles = []
                search_queries = [
                    f"{stock.symbol} stock",
                    f"{stock.company_name} share price"
                ]
                
                for query in search_queries:
                    try:
                        results = scraper.scrape_google_news(query, max_results=5)
                        articles.extend(results)
                    except Exception as e:
                        logger.warning(f"Error fetching Google News for {query}: {e}")
                        continue
                
                # Remove duplicates
                seen_urls = set()
                unique_articles = []
                for article in articles:
                    if article['url'] not in seen_urls:
                        seen_urls.add(article['url'])
                        unique_articles.append(article)
                
                # Process articles
                for article_data in unique_articles[:10]:
                    try:
                        # Check if article already exists
                        if NewsArticle.objects.filter(url=article_data['url']).exists():
                            total_skipped += 1
                            continue
                        
                        # Skip old articles
                        if article_data.get('published_at') and article_data['published_at'] < cutoff_time:
                            total_skipped += 1
                            continue
                        
                        # Generate AI summary
                        ai_summary = scraper.generate_brief_summary(
                            article_data['title'],
                            article_data.get('content', article_data.get('summary', ''))
                        )
                        
                        # Skip if not relevant
                        if not ai_summary.get('is_relevant', True):
                            total_skipped += 1
                            continue
                        
                        # Get or create news source
                        news_source, _ = NewsSource.objects.get_or_create(
                            name=article_data['source_name'],
                            defaults={
                                'url': article_data.get('source_url', ''),
                                'is_active': True
                            }
                        )
                        
                        # Create news article
                        article = NewsArticle.objects.create(
                            title=article_data['title'],
                            url=article_data['url'],
                            content=article_data.get('content', ''),
                            summary=article_data.get('summary', ''),
                            ai_summary=ai_summary.get('brief_summary', ''),
                            source=news_source,
                            published_at=article_data.get('published_at', timezone.now()),
                            sentiment_score=ai_summary.get('sentiment_score', 0),
                            is_recommendation=extractor.is_recommendation_article(
                                article_data['title'] + ' ' + article_data.get('content', '')
                            )
                        )
                        
                        # Link to stock
                        article.mentioned_stocks.add(stock)
                        
                        total_new += 1
                        logger.info(f"Saved article: {article.title[:50]}...")
                        
                    except Exception as e:
                        logger.error(f"Error saving article: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error fetching news for {stock.symbol}: {e}")
                continue
        
        logger.info(f"Holdings news fetch completed. New: {total_new}, Skipped: {total_skipped}")
        
        return {
            'status': 'success',
            'new_articles': total_new,
            'skipped_articles': total_skipped,
            'stocks_processed': stocks.count()
        }
        
    except Exception as e:
        logger.error(f"Error in holdings news fetch: {str(e)}")
        return {'status': 'error', 'message': str(e)}