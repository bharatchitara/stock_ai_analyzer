"""
Management command to fetch news for portfolio holdings
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from news.models import NewsArticle, Stock, NewsSource, PortfolioHolding
from news.scraper import NewsScraper, StockMentionExtractor
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch latest news for stocks in portfolio holdings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Fetch news for specific stock symbol'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Fetch news from last N hours (default: 24)'
        )
        parser.add_argument(
            '--max-articles',
            type=int,
            default=10,
            help='Maximum articles per stock (default: 10)'
        )

    def handle(self, *args, **options):
        symbol = options['symbol']
        hours = options['hours']
        max_articles = options['max_articles']
        
        scraper = NewsScraper()
        extractor = StockMentionExtractor()
        
        # Determine which stocks to process
        if symbol:
            stocks = Stock.objects.filter(symbol=symbol)
            if not stocks.exists():
                self.stdout.write(self.style.ERROR(f'Stock {symbol} not found'))
                return
        else:
            # Get all unique stocks from holdings
            stock_ids = PortfolioHolding.objects.values_list('stock_id', flat=True).distinct()
            stocks = Stock.objects.filter(id__in=stock_ids)
        
        if not stocks.exists():
            self.stdout.write(self.style.WARNING('No holdings found in portfolio'))
            return
        
        self.stdout.write(f'Fetching news for {stocks.count()} stocks from holdings...\n')
        
        total_new = 0
        total_existing = 0
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        for stock in stocks:
            self.stdout.write(f'📰 Fetching news for {stock.symbol} ({stock.company_name})...')
            
            try:
                # Fetch news articles for this stock
                articles = self._fetch_stock_news(scraper, stock, max_articles)
                
                if not articles:
                    self.stdout.write(f'  ℹ️  No news found')
                    continue
                
                self.stdout.write(f'  📥 Retrieved {len(articles)} articles')
                
                saved_count = 0
                skipped_count = 0
                
                for article_data in articles:
                    try:
                        # Check if article already exists
                        if NewsArticle.objects.filter(url=article_data['url']).exists():
                            skipped_count += 1
                            continue
                        
                        # Skip old articles
                        if article_data.get('published_at') and article_data['published_at'] < cutoff_time:
                            skipped_count += 1
                            continue
                        
                        # Generate AI summary
                        ai_summary = scraper.generate_brief_summary(
                            article_data['title'],
                            article_data.get('content', article_data.get('summary', ''))
                        )
                        
                        # Skip if not relevant
                        if not ai_summary.get('is_relevant', True):
                            skipped_count += 1
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
                        
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error saving article: {e}")
                        continue
                
                if saved_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Saved {saved_count} new articles'))
                    total_new += saved_count
                if skipped_count > 0:
                    self.stdout.write(f'  ℹ️  Skipped {skipped_count} existing/old articles')
                    total_existing += skipped_count
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
                logger.error(f'Error fetching news for {stock.symbol}: {str(e)}')
                continue
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ News fetch completed!'))
        self.stdout.write(f'   New articles: {total_new}')
        self.stdout.write(f'   Skipped: {total_existing}')
    
    def _fetch_stock_news(self, scraper, stock, max_articles):
        """Fetch news for a specific stock"""
        articles = []
        
        # Try Google News search for the stock
        search_queries = [
            f"{stock.symbol} stock",
            f"{stock.company_name} share price",
            f"{stock.symbol} news today"
        ]
        
        for query in search_queries:
            try:
                results = scraper.scrape_google_news(query, max_results=max_articles)
                articles.extend(results)
                if len(articles) >= max_articles:
                    break
            except Exception as e:
                logger.warning(f"Error fetching Google News for {query}: {e}")
                continue
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        return unique_articles[:max_articles]
