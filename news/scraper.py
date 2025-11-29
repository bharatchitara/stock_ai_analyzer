"""
News scraping utilities for Indian financial news sources
"""

import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timezone
import pytz
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import List, Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Indian timezone
IST = pytz.timezone('Asia/Kolkata')

class NewsSourceConfig:
    """Configuration for different news sources"""
    
    SOURCES = {
        'economic_times': {
            'name': 'Economic Times',
            'base_url': 'https://economictimes.indiatimes.com',
            'rss_feeds': [
                'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
                'https://economictimes.indiatimes.com/news/economy/rssfeeds/1715249553.cms',
            ],
            'selectors': {
                'title': 'h1',
                'content': '.artText, .Normal',
                'published_time': '.publish_on',
            }
        },
        'business_standard': {
            'name': 'Business Standard',
            'base_url': 'https://www.business-standard.com',
            'rss_feeds': [
                'https://www.business-standard.com/rss/markets-106.rss',
                'https://www.business-standard.com/rss/finance-103.rss',
            ],
            'selectors': {
                'title': 'h1',
                'content': '.story-text, .article-content',
                'published_time': '.story-date',
            }
        },
        'livemint': {
            'name': 'LiveMint',
            'base_url': 'https://www.livemint.com',
            'rss_feeds': [
                'https://www.livemint.com/rss/market',
                'https://www.livemint.com/rss/money',
            ],
            'selectors': {
                'title': 'h1',
                'content': '.mainSectionDiv, .articleBody',
                'published_time': '.publishedDetails',
            }
        },
        'moneycontrol': {
            'name': 'MoneyControl',
            'base_url': 'https://www.moneycontrol.com',
            'rss_feeds': [
                'https://www.moneycontrol.com/rss/results.xml',
                'https://www.moneycontrol.com/rss/marketreports.xml',
            ],
            'selectors': {
                'title': 'h1',
                'content': '.arti-content, .content_wrapper',
                'published_time': '.article_schedule',
            }
        },
        'groww': {
            'name': 'Groww',
            'base_url': 'https://groww.in',
            'rss_feeds': [
                'https://groww.in/blog/feed',
            ],
            'selectors': {
                'title': 'h1, .entry-title',
                'content': '.entry-content, .post-content, .blog-content',
                'published_time': '.published, .post-date',
            }
        },
        'zerodha': {
            'name': 'Zerodha',
            'base_url': 'https://zerodha.com',
            'rss_feeds': [
                'https://zerodha.com/z-connect/feed',
            ],
            'selectors': {
                'title': 'h1, .post-title',
                'content': '.post-content, .entry-content',
                'published_time': '.post-meta, .published',
            }
        },
        'upstox': {
            'name': 'Upstox',
            'base_url': 'https://upstox.com',
            'rss_feeds': [
                'https://upstox.com/blog/feed/',
            ],
            'selectors': {
                'title': 'h1, .entry-title',
                'content': '.entry-content, .post-content',
                'published_time': '.entry-date, .post-date',
            }
        },
        'angelone': {
            'name': 'Angel One',
            'base_url': 'https://www.angelone.in',
            'rss_feeds': [
                'https://www.angelone.in/blog/feed/',
            ],
            'selectors': {
                'title': 'h1, .entry-title',
                'content': '.entry-content, .post-content, .blog-content',
                'published_time': '.entry-date, .post-date',
            }
        },
        'financial_express': {
            'name': 'Financial Express',
            'base_url': 'https://www.financialexpress.com',
            'rss_feeds': [
                'https://www.financialexpress.com/market/rss/',
                'https://www.financialexpress.com/economy/rss/',
            ],
            'selectors': {
                'title': 'h1, .main-story-heading',
                'content': '.main-story-content, .story-content, .article-content',
                'published_time': '.story-date, .article-date',
            }
        },
        'the_hindu': {
            'name': 'The Hindu Business',
            'base_url': 'https://www.thehindu.com',
            'rss_feeds': [
                'https://www.thehindu.com/business/Economy/feeder/default.rss',
                'https://www.thehindu.com/business/Markets/feeder/default.rss',
            ],
            'selectors': {
                'title': 'h1, .title',
                'content': '.articlebodycontent, .story-content',
                'published_time': '.publish-time, .article-date',
            }
        }
    }


class NewsScraper:
    """Main news scraper class"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_rss_feeds(self, source_key: str) -> List[Dict]:
        """Scrape articles from RSS feeds of a news source"""
        source_config = NewsSourceConfig.SOURCES.get(source_key)
        if not source_config:
            logger.error(f"Source {source_key} not found in configuration")
            return []
        
        articles = []
        
        for rss_url in source_config['rss_feeds']:
            try:
                logger.info(f"Scraping RSS feed: {rss_url}")
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries:
                    article_data = self._parse_rss_entry(entry, source_config)
                    if article_data:
                        # Get full article content
                        full_content = self._extract_article_content(
                            article_data['url'], 
                            source_config['selectors']
                        )
                        if full_content:
                            article_data.update(full_content)
                        
                        articles.append(article_data)
                        
                        # Rate limiting
                        time.sleep(1)
                        
            except Exception as e:
                logger.error(f"Error scraping RSS feed {rss_url}: {str(e)}")
                continue
        
        return articles
    
    def _parse_rss_entry(self, entry, source_config: Dict) -> Optional[Dict]:
        """Parse individual RSS entry"""
        try:
            # Extract published date
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime.fromtimestamp(
                    time.mktime(entry.published_parsed),
                    tz=IST
                )
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_at = datetime.fromtimestamp(
                    time.mktime(entry.updated_parsed),
                    tz=IST
                )
            
            if not published_at:
                published_at = datetime.now(IST)
            
            # Only process articles from today or yesterday (for pre-market news)
            today = datetime.now(IST).date()
            article_date = published_at.date()
            
            if (today - article_date).days > 1:
                return None
            
            article_data = {
                'title': entry.title.strip(),
                'url': entry.link,
                'published_at': published_at,
                'summary': getattr(entry, 'summary', ''),
                'source_name': source_config['name']
            }
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry: {str(e)}")
            return None
    
    def _extract_article_content(self, url: str, selectors: Dict) -> Optional[Dict]:
        """Extract full article content from URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.select_one(selectors['title'])
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Extract content
            content_elems = soup.select(selectors['content'])
            content_parts = []
            for elem in content_elems:
                text = elem.get_text(strip=True)
                if text:
                    content_parts.append(text)
            
            content = '\n\n'.join(content_parts)
            
            if not content:
                logger.warning(f"No content extracted from {url}")
                return None
            
            return {
                'content': content,
                'title': title if title else None
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return None
    
    def scrape_all_sources(self) -> Dict[str, List[Dict]]:
        """Scrape all configured news sources"""
        all_articles = {}
        
        for source_key in NewsSourceConfig.SOURCES.keys():
            logger.info(f"Scraping source: {source_key}")
            articles = self.scrape_rss_feeds(source_key)
            all_articles[source_key] = articles
            logger.info(f"Scraped {len(articles)} articles from {source_key}")
            
            # Rate limiting between sources
            time.sleep(2)
        
        return all_articles
    
    def filter_pre_market_news(self, articles: List[Dict]) -> List[Dict]:
        """Filter articles published before 9:10 AM IST"""
        pre_market_articles = []
        
        for article in articles:
            published_at = article.get('published_at')
            if published_at:
                # Check if published before 9:10 AM IST
                market_open_time = published_at.replace(hour=9, minute=10, second=0, microsecond=0)
                if published_at < market_open_time:
                    pre_market_articles.append(article)
        
        return pre_market_articles


class StockMentionExtractor:
    """Extract stock symbols and company names mentioned in news articles"""
    
    # Common Indian stock symbols and company mappings
    STOCK_MAPPINGS = {
        'RELIANCE': 'Reliance Industries',
        'TCS': 'Tata Consultancy Services',
        'HDFCBANK': 'HDFC Bank',
        'INFY': 'Infosys',
        'ITC': 'ITC Limited',
        'SBIN': 'State Bank of India',
        'BHARTIARTL': 'Bharti Airtel',
        'KOTAKBANK': 'Kotak Mahindra Bank',
        'LT': 'Larsen & Toubro',
        'WIPRO': 'Wipro',
        'MARUTI': 'Maruti Suzuki',
        'TATAMOTORS': 'Tata Motors',
        'TATASTEEL': 'Tata Steel',
        'BAJFINANCE': 'Bajaj Finance',
        'HCLTECH': 'HCL Technologies',
        'ASIANPAINT': 'Asian Paints',
        'NESTLEIND': 'Nestle India',
        'ULTRACEMCO': 'UltraTech Cement',
        'TITAN': 'Titan Company',
        'AXISBANK': 'Axis Bank',
    }
    
    def extract_mentioned_stocks(self, text: str) -> List[str]:
        """Extract stock symbols mentioned in the text"""
        mentioned_stocks = []
        text_upper = text.upper()
        
        for symbol, company in self.STOCK_MAPPINGS.items():
            if (symbol in text_upper or 
                company.upper() in text_upper or
                company.upper().replace(' ', '') in text_upper):
                mentioned_stocks.append(symbol)
        
        return list(set(mentioned_stocks))  # Remove duplicates


# Example usage functions for Django management commands

def scrape_morning_news():
    """Function to scrape morning news before market opening"""
    scraper = NewsScraper()
    extractor = StockMentionExtractor()
    
    logger.info("Starting morning news scraping...")
    
    # Scrape all sources
    all_articles = scraper.scrape_all_sources()
    
    # Process and save articles to database
    total_saved = 0
    
    for source_key, articles in all_articles.items():
        # Filter for pre-market news
        pre_market_articles = scraper.filter_pre_market_news(articles)
        
        logger.info(f"Found {len(pre_market_articles)} pre-market articles from {source_key}")
        
        for article_data in pre_market_articles:
            try:
                # Extract mentioned stocks
                full_text = f"{article_data.get('title', '')} {article_data.get('content', '')}"
                mentioned_stocks = extractor.extract_mentioned_stocks(full_text)
                article_data['mentioned_stocks'] = mentioned_stocks
                
                # Save to database (this would be implemented in Django management command)
                # save_article_to_db(article_data, source_key)
                total_saved += 1
                
            except Exception as e:
                logger.error(f"Error processing article: {str(e)}")
                continue
    
    logger.info(f"Morning news scraping completed. Saved {total_saved} articles.")
    return total_saved