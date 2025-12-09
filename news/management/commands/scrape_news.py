from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import NewsArticle, Stock, NewsSource
from news.scraper import NewsScraper, StockMentionExtractor
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape news articles from various sources including Google News recommendations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--recommendations-only',
            action='store_true',
            help='Only scrape Google News for stock recommendations',
        )
        parser.add_argument(
            '--no-recommendations',
            action='store_true',
            help='Skip Google News recommendations scraping',
        )
        parser.add_argument(
            '--source',
            type=str,
            help='Scrape specific source only (e.g., economic_times, moneycontrol)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting enhanced news scraping...'))
        
        scraper = NewsScraper()
        extractor = StockMentionExtractor()
        
        recommendations_only = options.get('recommendations_only', False)
        no_recommendations = options.get('no_recommendations', False)
        specific_source = options.get('source')
        
        all_articles = {}
        
        # Scrape Google News recommendations if requested
        if recommendations_only or not no_recommendations:
            self.stdout.write('Scraping Google News for stock recommendations...')
            recommendation_articles = scraper.scrape_recommendation_news()
            all_articles['google_news_recommendations'] = recommendation_articles
            self.stdout.write(self.style.SUCCESS(
                f'Found {len(recommendation_articles)} recommendation articles'
            ))
        
        # Scrape RSS feeds if not recommendations-only
        if not recommendations_only:
            if specific_source:
                self.stdout.write(f'Scraping specific source: {specific_source}')
                articles = scraper.scrape_rss_feeds(specific_source)
                all_articles[specific_source] = articles
            else:
                self.stdout.write('Scraping all RSS feed sources...')
                all_articles = scraper.scrape_all_sources(
                    include_recommendations=not no_recommendations
                )
        
        # Process and save articles
        total_saved = 0
        total_skipped = 0
        recommendation_count = 0
        
        for source_key, articles in all_articles.items():
            self.stdout.write(f'\nProcessing {len(articles)} articles from {source_key}...')
            
            for article_data in articles:
                try:
                    # Check if article already exists
                    if NewsArticle.objects.filter(url=article_data['url']).exists():
                        total_skipped += 1
                        continue
                    
                    # Extract mentioned stocks
                    full_text = f"{article_data.get('title', '')} {article_data.get('content', '')} {article_data.get('summary', '')}"
                    mentioned_stocks = extractor.extract_mentioned_stocks(full_text)
                    is_recommendation = extractor.is_recommendation_article(full_text)
                    
                    # Generate AI summary
                    ai_summary = scraper.generate_brief_summary(
                        article_data['title'],
                        article_data.get('content', article_data.get('summary', ''))
                    )
                    
                    # Skip if not relevant to finance/stocks
                    if not ai_summary.get('is_relevant', True):
                        self.stdout.write(
                            self.style.WARNING(f'  ⊗ Skipped (not finance-related): {article_data["title"][:50]}...')
                        )
                        total_skipped += 1
                        continue
                    
                    # Get or create news source
                    news_source, _ = NewsSource.objects.get_or_create(
                        name=article_data['source_name'],
                        defaults={
                            'url': article_data.get('url', '').split('/')[0] + '//' + article_data.get('url', '').split('/')[2] if '/' in article_data.get('url', '') else '',
                            'is_active': True
                        }
                    )
                    
                    # Prepare key points as text
                    key_points_text = '\n'.join([f"• {point}" for point in ai_summary.get('key_points', [])])
                    
                    # Create article
                    article = NewsArticle.objects.create(
                        title=article_data['title'],
                        url=article_data['url'],
                        content=article_data.get('content', article_data.get('summary', '')),
                        published_at=article_data['published_at'],
                        source=news_source,
                        sentiment=ai_summary.get('sentiment', 'PENDING'),
                        sentiment_score=ai_summary.get('sentiment_score', 0.0),
                        is_pre_market=article_data['published_at'].hour < 9 or 
                                     (article_data['published_at'].hour == 9 and 
                                      article_data['published_at'].minute < 10),
                        is_recommendation=is_recommendation,
                        ai_summary=ai_summary,
                        key_points=key_points_text,
                        impact_summary=ai_summary.get('impact', ''),
                        article_emoji=ai_summary.get('emoji', '📰')
                    )
                    
                    # Link to mentioned stocks
                    if mentioned_stocks:
                        stocks = Stock.objects.filter(symbol__in=mentioned_stocks)
                        article.mentioned_stocks.set(stocks)
                        
                        self.stdout.write(
                            f'  ✓ {article.title[:60]}... '
                            f'[{", ".join(mentioned_stocks)}]'
                            f'{" [RECOMMENDATION]" if is_recommendation else ""}'
                        )
                    else:
                        self.stdout.write(f'  ✓ {article.title[:60]}... [No stocks matched]')
                    
                    total_saved += 1
                    if is_recommendation:
                        recommendation_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error saving article: {str(e)}')
                    )
                    logger.error(f"Error saving article: {str(e)}", exc_info=True)
                    continue
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Scraping completed!'))
        self.stdout.write(f'  • Total articles saved: {total_saved}')
        self.stdout.write(f'  • Recommendation articles: {recommendation_count}')
        self.stdout.write(f'  • Articles skipped (duplicates): {total_skipped}')
        self.stdout.write('='*60)
