# Enhanced News Scraping Guide

## Overview
The enhanced news scraper now collects targeted stock recommendations and insights from multiple sources including Google News search.

## New Features

### 1. Google News Stock Recommendations
Automatically searches Google News for:
- "indian stocks to buy today"
- "best stocks to buy now india"
- "top stock picks india"
- "stock recommendations india"
- "analyst stock recommendations india"
- "nifty stocks to buy"
- "bse stocks recommendation"
- "stocks to buy before market opens"
- "pre market stock picks india"

### 2. Expanded Stock Coverage
Now tracks **70+ stocks** including:
- All Nifty 50 stocks
- Popular midcap stocks (Zomato, Paytm, Nykaa, Policybazaar)
- Key sectoral leaders
- Multiple company name variations for better matching

### 3. Smart Stock Detection
Recognizes stocks by:
- Stock symbols (e.g., "TCS", "INFY")
- Company names (e.g., "Tata Consultancy Services")
- Abbreviations (e.g., "HUL" for Hindustan Unilever)
- Alternate names (e.g., "RIL" for Reliance Industries)

### 4. Recommendation Detection
Automatically identifies articles containing:
- Buy/Sell/Hold recommendations
- Target prices
- Analyst ratings
- Upgrades/downgrades
- Stock picks and ideas

## Usage

### Quick Scrape (Current Portfolio Stocks Only)
```bash
python manage.py scrape_news --no-recommendations
```

### Full Scrape (All Sources + Google News Recommendations)
```bash
python manage.py scrape_news
```

### Recommendations Only (Fast)
```bash
python manage.py scrape_news --recommendations-only
```

### Specific Source
```bash
python manage.py scrape_news --source economic_times
python manage.py scrape_news --source moneycontrol
```

## Available Sources

### Indian Financial News Sites
1. **Economic Times** - Market news and analysis
2. **Business Standard** - Business and finance news
3. **LiveMint** - Market and money news
4. **MoneyControl** - Stock market reports
5. **Financial Express** - Market and economy news
6. **The Hindu Business** - Business and economy news

### Investment Platform Blogs
7. **Groww** - Investment insights and market analysis
8. **Zerodha (Z-Connect)** - Trading and investment insights
9. **Upstox** - Market analysis and trading tips
10. **Angel One** - Stock recommendations and market news
11. **Ticker Tape (Smallcase)** - Stock research and analysis
12. **Investing.com India** - Global and Indian market news

### Google News (Recommendation Search)
Searches for targeted stock recommendation articles from all news sources

## Script Integration

### Update `run_analysis.sh`
The full analysis script now includes:
```bash
# Step 1: Enhanced news collection with recommendations
python manage.py scrape_news

# Step 2: Sentiment analysis (existing)
python manage.py analyze_sentiment

# Step 3: Generate recommendations (existing)
# ... rest of the analysis
```

### Update `quick_analysis.sh`
For daily quick checks (without scraping):
```bash
# Uses existing news data
# Just updates sentiment and generates recommendations
```

## Database Fields

### NewsArticle Model - New Field
- `is_recommendation` (Boolean) - True if article contains stock recommendations

### Query Examples
```python
# Get all recommendation articles
recommendations = NewsArticle.objects.filter(is_recommendation=True)

# Get recommendation articles for a specific stock
infy_recommendations = NewsArticle.objects.filter(
    is_recommendation=True,
    related_stocks__symbol='INFY'
)

# Get today's pre-market recommendations
from django.utils import timezone
today = timezone.now().date()

morning_recommendations = NewsArticle.objects.filter(
    is_recommendation=True,
    is_pre_market=True,
    published_at__date=today
)
```

## Performance

### Scraping Time Estimates
- **RSS Feeds Only**: 2-3 minutes (12 sources)
- **Google News Recommendations**: 1-2 minutes (9 search queries)
- **Full Scrape**: 3-5 minutes (all sources + recommendations)
- **Recommendations Only**: 1-2 minutes (fastest)

### Rate Limiting
- 1 second between articles from same source
- 2 seconds between different sources
- 2 seconds between Google News queries

## Best Practices

### Morning Routine (Before 9:10 AM)
```bash
# 1. Full scrape with recommendations
python manage.py scrape_news

# 2. Analyze sentiment
python manage.py analyze_sentiment

# 3. Generate portfolio recommendations
python manage.py analyze_portfolio
```

### Throughout the Day
```bash
# Quick recommendation updates
python manage.py scrape_news --recommendations-only
```

### Weekly Deep Dive
```bash
# Full scrape + analysis
./run_analysis.sh
```

## Monitoring

### Check Scraping Statistics
```python
from news.models import NewsArticle
from django.utils import timezone
from datetime import timedelta

# Last 24 hours
yesterday = timezone.now() - timedelta(days=1)
stats = {
    'total': NewsArticle.objects.filter(scraped_at__gte=yesterday).count(),
    'recommendations': NewsArticle.objects.filter(
        scraped_at__gte=yesterday,
        is_recommendation=True
    ).count(),
    'pre_market': NewsArticle.objects.filter(
        scraped_at__gte=yesterday,
        is_pre_market=True
    ).count(),
}
print(f"Last 24h: {stats['total']} articles ({stats['recommendations']} recommendations)")
```

## Troubleshooting

### No Articles Found
```bash
# Check internet connection
curl -I https://economictimes.indiatimes.com

# Check RSS feed accessibility
python -c "import feedparser; print(feedparser.parse('https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms').entries[:1])"
```

### Stocks Not Detected
```python
# Test stock extraction
from news.scraper import StockMentionExtractor

extractor = StockMentionExtractor()
text = "Infosys and TCS showing strong growth"
stocks = extractor.extract_mentioned_stocks(text)
print(f"Found stocks: {stocks}")  # Should output: ['INFY', 'TCS']
```

### Google News Blocked
If Google News scraping is blocked:
1. Check rate limits (2 seconds between queries)
2. Verify User-Agent header is set
3. Try using `--no-recommendations` flag
4. Use VPN if geo-blocked

## Future Enhancements

### Planned Features
- [ ] Twitter/X integration for real-time news
- [ ] Telegram channel scraping
- [ ] WhatsApp group message parsing
- [ ] Broker research report PDFs
- [ ] Earnings call transcripts
- [ ] NSE/BSE official announcements
- [ ] SEBI filings and circulars

### Configuration Options
Add to `settings.py`:
```python
NEWS_SCRAPER_CONFIG = {
    'MAX_ARTICLES_PER_SOURCE': 20,
    'SCRAPE_INTERVAL_SECONDS': 1,
    'ENABLE_GOOGLE_NEWS': True,
    'GOOGLE_NEWS_MAX_RESULTS': 10,
    'USER_AGENT': 'Custom User Agent String',
}
```

## API Endpoints (Future)

### RESTful API for News
```
GET /api/news/recommendations/
GET /api/news/recommendations/?stock=INFY
GET /api/news/latest/?is_pre_market=true
GET /api/news/search/?q=earnings
```

## Contributing

To add a new news source:

1. Add to `news/scraper.py`:
```python
'source_key': {
    'name': 'Source Name',
    'base_url': 'https://example.com',
    'rss_feeds': [
        'https://example.com/feed.rss',
    ],
    'selectors': {
        'title': 'h1',
        'content': '.article-content',
        'published_time': '.publish-date',
    }
}
```

2. Test the source:
```bash
python manage.py scrape_news --source source_key
```

3. Add documentation and submit PR

---

## Support

For issues or questions:
- Check logs: `tail -f logs/news_scraper.log`
- Run in debug mode: `python manage.py scrape_news --verbosity 2`
- Open GitHub issue with error details
