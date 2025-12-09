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
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Indian timezone
IST = pytz.timezone('Asia/Kolkata')

# Configure Gemini AI
try:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
except:
    logger.warning("Gemini API key not configured")
    client = None

def get_gemini_model():
    """Get Gemini model name from database configuration"""
    try:
        from news.models import AIConfig
        config = AIConfig.get_active_config()
        return config.gemini_model
    except Exception as e:
        logger.warning(f"Could not fetch AI config from database: {e}. Using default.")
        return 'gemini-2.5-flash'

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
        },
        'investing_com': {
            'name': 'Investing.com India',
            'base_url': 'https://in.investing.com',
            'rss_feeds': [
                'https://in.investing.com/rss/news_285.rss',  # India news
            ],
            'selectors': {
                'title': 'h1',
                'content': '.articlePage, .WYSIWYG',
                'published_time': '.contentSectionDetails span',
            }
        },
        'ticker_tape': {
            'name': 'Ticker Tape (Smallcase)',
            'base_url': 'https://www.tickertape.in',
            'rss_feeds': [
                'https://www.tickertape.in/blog/feed/',
            ],
            'selectors': {
                'title': 'h1, .entry-title',
                'content': '.entry-content, .post-content',
                'published_time': '.entry-date, .post-date',
            }
        }
    }
    
    # Google News search queries for targeted stock recommendations
    RECOMMENDATION_QUERIES = [
        'indian stocks to buy today',
        'best stocks to buy now india',
        'top stock picks india',
        'stock recommendations india',
        'analyst stock recommendations india',
        'nifty stocks to buy',
        'bse stocks recommendation',
        'stocks to buy before market opens',
        'pre market stock picks india',
    ]


class NewsScraper:
    """Main news scraper class"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_google_news(self, query: str, max_results: int = 10) -> List[Dict]:
        """Scrape Google News search results for a specific query"""
        articles = []
        
        try:
            # Use Google News RSS feed for the search query
            search_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
            
            logger.info(f"Searching Google News for: {query}")
            feed = feedparser.parse(search_url)
            
            for entry in feed.entries[:max_results]:
                try:
                    # Extract published date
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime.fromtimestamp(
                            time.mktime(entry.published_parsed),
                            tz=IST
                        )
                    
                    if not published_at:
                        published_at = datetime.now(IST)
                    
                    # Extract source from the title (Google News format)
                    title = entry.title.strip()
                    source_name = 'Google News'
                    if ' - ' in title:
                        title_parts = title.rsplit(' - ', 1)
                        title = title_parts[0]
                        source_name = title_parts[1] if len(title_parts) > 1 else source_name
                    
                    article_data = {
                        'title': title,
                        'url': entry.link,
                        'published_at': published_at,
                        'summary': getattr(entry, 'summary', ''),
                        'source_name': source_name,
                        'search_query': query,
                        'content': getattr(entry, 'summary', '')  # Use summary as content for Google News
                    }
                    
                    articles.append(article_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing Google News entry: {str(e)}")
                    continue
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            logger.error(f"Error scraping Google News for query '{query}': {str(e)}")
        
        return articles
    
    def scrape_recommendation_news(self) -> List[Dict]:
        """Scrape news specifically about stock recommendations"""
        all_recommendation_articles = []
        
        logger.info("Starting stock recommendation news scraping...")
        
        for query in NewsSourceConfig.RECOMMENDATION_QUERIES:
            articles = self.scrape_google_news(query, max_results=5)
            all_recommendation_articles.extend(articles)
            logger.info(f"Found {len(articles)} articles for query: {query}")
            time.sleep(2)  # Rate limiting between queries
        
        logger.info(f"Total recommendation articles found: {len(all_recommendation_articles)}")
        return all_recommendation_articles
    
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
            
            # If normal extraction failed, try AI extraction
            if not content or len(content) < 100:
                logger.info(f"Traditional extraction failed, trying AI extraction for {url}")
                content = self._ai_extract_content(response.text, title)
            
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
    
    def _ai_extract_content(self, html_text: str, title: str) -> str:
        """Use AI to extract main content from HTML when traditional methods fail"""
        try:
            # Remove scripts and styles
            soup = BeautifulSoup(html_text, 'html.parser')
            for script in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                script.decompose()
            
            # Get visible text
            text = soup.get_text(separator='\n', strip=True)
            
            # Limit text length for AI processing
            text = text[:5000]
            
            prompt = f"""Extract the main article content from this text. Title: {title}
            
Remove all navigation, ads, sidebars, and other non-article content.
Return only the main article text, keeping it concise and readable.

Text:
{text}

Main Article:"""
            
            response = client.models.generate_content(
                model=get_gemini_model(),
                contents=prompt
            )
            extracted_content = response.text.strip()
            
            return extracted_content if len(extracted_content) > 50 else ""
            
        except Exception as e:
            logger.error(f"AI extraction error: {str(e)}")
            return ""
    
    def is_relevant_to_finance(self, title: str, content: str) -> bool:
        """Check if article is relevant to stocks/finance using AI"""
        try:
            prompt = f"""Is this article about stocks, finance, markets, economy, or business?

Title: {title}
Content: {content[:500]}

Answer ONLY with: YES or NO

If the article is about:
- Stock markets, stock recommendations, company earnings
- Banking, finance, economy, GDP, inflation
- Business news, mergers, acquisitions
- Corporate results, IPOs, market trends
Answer: YES

If the article is about:
- Sports, entertainment, politics (not economy related)
- Weather, crime, accidents
- General news not related to finance
Answer: NO

Answer:"""
            
            response = client.models.generate_content(
                model=get_gemini_model(),
                contents=prompt
            )
            answer = response.text.strip().upper()
            
            return 'YES' in answer
            
        except Exception as e:
            logger.error(f"Error checking relevance: {str(e)}")
            # Default to True to avoid filtering out articles on error
            return True
    
    def generate_brief_summary(self, title: str, content: str) -> Dict[str, str]:
        """Generate a brief, visual summary of the article using AI"""
        try:
            prompt = f"""Analyze this financial news article and create a brief visual summary.

Title: {title}
Content: {content[:2000]}

Provide:
1. KEY_POINTS: 3-4 bullet points (each under 15 words) of the most important information
2. IMPACT: One sentence about market/stock impact
3. EMOJI: One relevant emoji that represents the article
4. SENTIMENT: POSITIVE, NEGATIVE, or NEUTRAL (based on market/stock impact)
5. SENTIMENT_SCORE: A number from -1.0 (very negative) to +1.0 (very positive)
6. IS_RELEVANT: YES if related to stocks/finance/business, NO otherwise

Guidelines for sentiment:
- POSITIVE: Good news for stocks/market (earnings beat, policy support, growth, upgrades, buy recommendations)
- NEGATIVE: Bad news (earnings miss, regulatory issues, downgrades, sell-offs, scandals)
- NEUTRAL: Informational without clear positive/negative impact

Format as:
KEY_POINTS:
• [point 1]
• [point 2]
• [point 3]

IMPACT: [impact sentence]

EMOJI: [emoji]

SENTIMENT: [POSITIVE/NEGATIVE/NEUTRAL]

SENTIMENT_SCORE: [number between -1.0 and 1.0]

IS_RELEVANT: [YES or NO]"""
            
            response = client.models.generate_content(
                model=get_gemini_model(),
                contents=prompt
            )
            summary_text = response.text.strip()
            
            # Parse the response
            summary_parts = {}
            current_section = None
            key_points = []
            
            for line in summary_text.split('\n'):
                line = line.strip()
                if line.startswith('KEY_POINTS:'):
                    current_section = 'KEY_POINTS'
                elif line.startswith('IMPACT:'):
                    summary_parts['impact'] = line.replace('IMPACT:', '').strip()
                    current_section = None
                elif line.startswith('EMOJI:'):
                    summary_parts['emoji'] = line.replace('EMOJI:', '').strip()
                    current_section = None
                elif line.startswith('SENTIMENT:'):
                    sentiment_text = line.replace('SENTIMENT:', '').strip().upper()
                    # Extract just the sentiment word (POSITIVE/NEGATIVE/NEUTRAL)
                    if 'POSITIVE' in sentiment_text:
                        summary_parts['sentiment'] = 'POSITIVE'
                    elif 'NEGATIVE' in sentiment_text:
                        summary_parts['sentiment'] = 'NEGATIVE'
                    else:
                        summary_parts['sentiment'] = 'NEUTRAL'
                    current_section = None
                elif line.startswith('SENTIMENT_SCORE:'):
                    try:
                        score_text = line.replace('SENTIMENT_SCORE:', '').strip()
                        # Extract number from text
                        import re
                        score_match = re.search(r'-?\d+\.?\d*', score_text)
                        if score_match:
                            score = float(score_match.group())
                            # Clamp between -1 and 1
                            summary_parts['sentiment_score'] = max(-1.0, min(1.0, score))
                    except (ValueError, AttributeError):
                        summary_parts['sentiment_score'] = 0.0
                    current_section = None
                elif line.startswith('IS_RELEVANT:'):
                    relevance = line.replace('IS_RELEVANT:', '').strip().upper()
                    summary_parts['is_relevant'] = 'YES' in relevance
                    current_section = None
                elif current_section == 'KEY_POINTS' and line.startswith('•'):
                    key_points.append(line.replace('•', '').strip())
            
            summary_parts['key_points'] = key_points
            
            # Defaults
            if 'is_relevant' not in summary_parts:
                summary_parts['is_relevant'] = True
            if 'sentiment' not in summary_parts:
                summary_parts['sentiment'] = 'NEUTRAL'
            if 'sentiment_score' not in summary_parts:
                # Auto-calculate from sentiment if not provided
                if summary_parts.get('sentiment') == 'POSITIVE':
                    summary_parts['sentiment_score'] = 0.5
                elif summary_parts.get('sentiment') == 'NEGATIVE':
                    summary_parts['sentiment_score'] = -0.5
                else:
                    summary_parts['sentiment_score'] = 0.0
            
            return summary_parts
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return {
                'key_points': [],
                'impact': '',
                'emoji': '📰',
                'sentiment': 'NEUTRAL'
            }
    
    def scrape_all_sources(self, include_recommendations: bool = True) -> Dict[str, List[Dict]]:
        """Scrape all configured news sources"""
        all_articles = {}
        
        # Scrape regular RSS feeds
        for source_key in NewsSourceConfig.SOURCES.keys():
            logger.info(f"Scraping source: {source_key}")
            articles = self.scrape_rss_feeds(source_key)
            all_articles[source_key] = articles
            logger.info(f"Scraped {len(articles)} articles from {source_key}")
            
            # Rate limiting between sources
            time.sleep(2)
        
        # Scrape Google News for stock recommendations
        if include_recommendations:
            logger.info("Scraping Google News for stock recommendations...")
            recommendation_articles = self.scrape_recommendation_news()
            all_articles['google_news_recommendations'] = recommendation_articles
        
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
    
    # Expanded Indian stock symbols and company mappings (Top 100 NSE stocks)
    STOCK_MAPPINGS = {
        'RELIANCE': ['Reliance Industries', 'RIL'],
        'TCS': ['Tata Consultancy Services', 'Tata Consultancy', 'TCS'],
        'HDFCBANK': ['HDFC Bank', 'HDFC'],
        'INFY': ['Infosys', 'Infosys Technologies'],
        'ITC': ['ITC Limited', 'ITC'],
        'SBIN': ['State Bank of India', 'State Bank', 'SBI'],
        'BHARTIARTL': ['Bharti Airtel', 'Airtel'],
        'KOTAKBANK': ['Kotak Mahindra Bank', 'Kotak Bank', 'Kotak'],
        'LT': ['Larsen & Toubro', 'Larsen and Toubro', 'L&T'],
        'WIPRO': ['Wipro', 'Wipro Technologies'],
        'MARUTI': ['Maruti Suzuki', 'Maruti', 'Maruti Suzuki India'],
        'TATAMOTORS': ['Tata Motors', 'Tata Motor'],
        'TATASTEEL': ['Tata Steel', 'Tata Steel'],
        'BAJFINANCE': ['Bajaj Finance', 'Bajaj Fin'],
        'HCLTECH': ['HCL Technologies', 'HCL Tech', 'HCL'],
        'ASIANPAINT': ['Asian Paints', 'Asian Paint'],
        'NESTLEIND': ['Nestle India', 'Nestle'],
        'ULTRACEMCO': ['UltraTech Cement', 'UltraTech'],
        'TITAN': ['Titan Company', 'Titan'],
        'AXISBANK': ['Axis Bank', 'Axis'],
        'SUNPHARMA': ['Sun Pharmaceutical', 'Sun Pharma'],
        'ADANIENT': ['Adani Enterprises', 'Adani Enterprise'],
        'ADANIPORTS': ['Adani Ports', 'Adani Port'],
        'HINDALCO': ['Hindalco Industries', 'Hindalco'],
        'INDUSINDBK': ['IndusInd Bank', 'IndusInd'],
        'ICICIBANK': ['ICICI Bank', 'ICICI'],
        'ONGC': ['Oil and Natural Gas', 'ONGC'],
        'NTPC': ['NTPC', 'National Thermal Power'],
        'POWERGRID': ['Power Grid', 'PowerGrid'],
        'COALINDIA': ['Coal India', 'Coal India Limited'],
        'JSWSTEEL': ['JSW Steel', 'JSW'],
        'TECHM': ['Tech Mahindra', 'TechM'],
        'BAJAJFINSV': ['Bajaj Finserv', 'Bajaj Financial Services'],
        'DIVISLAB': ['Divis Laboratories', 'Divis Lab'],
        'DMART': ['DMart', 'Avenue Supermarts'],
        'DRREDDY': ['Dr Reddy', 'Dr Reddys Laboratories'],
        'EICHERMOT': ['Eicher Motors', 'Eicher'],
        'GRASIM': ['Grasim Industries', 'Grasim'],
        'HEROMOTOCO': ['Hero MotoCorp', 'Hero Moto'],
        'HINDZINC': ['Hindustan Zinc', 'Hind Zinc'],
        'HINDUNILVR': ['Hindustan Unilever', 'HUL'],
        'IOC': ['Indian Oil', 'Indian Oil Corporation', 'IOC'],
        'JINDALSTEL': ['Jindal Steel', 'JSL'],
        'M&M': ['Mahindra & Mahindra', 'Mahindra and Mahindra', 'M&M'],
        'ONGC': ['ONGC', 'Oil & Natural Gas'],
        'SBILIFE': ['SBI Life', 'SBI Life Insurance'],
        'SHREECEM': ['Shree Cement', 'Shree Cements'],
        'TATACONSUM': ['Tata Consumer', 'Tata Consumer Products'],
        'VEDL': ['Vedanta', 'Vedanta Limited'],
        'ZOMATO': ['Zomato', 'Zomato Limited'],
        'PAYTM': ['Paytm', 'One97 Communications'],
        'NYKAA': ['Nykaa', 'FSN E-Commerce'],
        'POLICYBZR': ['Policybazaar', 'PB Fintech'],
        'ADANIGREEN': ['Adani Green', 'Adani Green Energy'],
        'BAJAJ-AUTO': ['Bajaj Auto', 'Bajaj'],
        'BRITANNIA': ['Britannia Industries', 'Britannia'],
        'CIPLA': ['Cipla', 'Cipla Limited'],
        'GODREJCP': ['Godrej Consumer', 'Godrej'],
        'GAIL': ['GAIL', 'Gas Authority of India'],
        'HAL': ['HAL', 'Hindustan Aeronautics'],
        'HDFCLIFE': ['HDFC Life', 'HDFC Life Insurance'],
        'IRCTC': ['IRCTC', 'Indian Railway Catering'],
        'LTI': ['LTI', 'LTIMindtree'],
        'PIDILITIND': ['Pidilite Industries', 'Pidilite'],
        'PNB': ['Punjab National Bank', 'PNB'],
        'SIEMENS': ['Siemens', 'Siemens India'],
        'TRENT': ['Trent', 'Trent Limited'],
        'UPL': ['UPL', 'United Phosphorus'],
    }
    
    def extract_mentioned_stocks(self, text: str) -> List[str]:
        """Extract stock symbols mentioned in the text"""
        mentioned_stocks = []
        text_upper = text.upper()
        
        for symbol, company_names in self.STOCK_MAPPINGS.items():
            # Check if symbol is mentioned
            if symbol in text_upper:
                mentioned_stocks.append(symbol)
                continue
            
            # Check all company name variations
            for company_name in company_names:
                if (company_name.upper() in text_upper or
                    company_name.upper().replace(' ', '') in text_upper or
                    company_name.upper().replace('&', 'AND') in text_upper):
                    mentioned_stocks.append(symbol)
                    break
        
        return list(set(mentioned_stocks))  # Remove duplicates
    
    def is_recommendation_article(self, text: str) -> bool:
        """Check if article contains stock recommendation keywords"""
        recommendation_keywords = [
            'buy', 'sell', 'hold', 'target price', 'stock pick',
            'recommendation', 'analyst', 'rating', 'upgrade', 'downgrade',
            'bullish', 'bearish', 'long term', 'short term', 'invest',
            'accumulate', 'book profit', 'stop loss', 'top pick',
            'stocks to buy', 'stocks to watch', 'stock ideas'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in recommendation_keywords)


# Example usage functions for Django management commands

def scrape_morning_news(include_recommendations: bool = True):
    """Function to scrape morning news before market opening"""
    scraper = NewsScraper()
    extractor = StockMentionExtractor()
    
    logger.info("Starting morning news scraping...")
    
    # Scrape all sources (including Google News recommendations)
    all_articles = scraper.scrape_all_sources(include_recommendations=include_recommendations)
    
    # Process and save articles to database
    total_saved = 0
    recommendation_count = 0
    
    for source_key, articles in all_articles.items():
        # Filter for pre-market news (skip for Google News recommendations)
        if source_key == 'google_news_recommendations':
            articles_to_process = articles
        else:
            articles_to_process = scraper.filter_pre_market_news(articles)
        
        logger.info(f"Found {len(articles_to_process)} articles from {source_key}")
        
        for article_data in articles_to_process:
            try:
                # Extract mentioned stocks
                full_text = f"{article_data.get('title', '')} {article_data.get('content', '')} {article_data.get('summary', '')}"
                mentioned_stocks = extractor.extract_mentioned_stocks(full_text)
                article_data['mentioned_stocks'] = mentioned_stocks
                
                # Check if it's a recommendation article
                is_recommendation = extractor.is_recommendation_article(full_text)
                article_data['is_recommendation'] = is_recommendation
                
                if is_recommendation:
                    recommendation_count += 1
                    logger.info(f"Recommendation article found: {article_data.get('title', '')[:50]}...")
                
                # Save to database (this would be implemented in Django management command)
                # save_article_to_db(article_data, source_key)
                total_saved += 1
                
            except Exception as e:
                logger.error(f"Error processing article: {str(e)}")
                continue
    
    logger.info(f"Morning news scraping completed. Saved {total_saved} articles ({recommendation_count} recommendations).")
    return {'total': total_saved, 'recommendations': recommendation_count}