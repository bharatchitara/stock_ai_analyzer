# News Fetching for Portfolio Holdings - User Guide

## Overview
The system automatically fetches the latest news for all stocks in your portfolio holdings every 6 hours. You can also fetch news on-demand anytime.

## Automatic News Fetching (Every 6 Hours)

The system runs a scheduled task that fetches news every 6 hours (12 AM, 6 AM, 12 PM, 6 PM IST).

### To Enable Automatic Fetching:

1. **Start Redis** (required for Celery):
```bash
redis-server
```

2. **Start Celery Worker** (in a new terminal):
```bash
cd /Users/bchita076/projectBuff
source .venv/bin/activate
celery -A stock_news_ai worker --loglevel=info
```

3. **Start Celery Beat** (scheduler, in another terminal):
```bash
cd /Users/bchita076/projectBuff
source .venv/bin/activate
celery -A stock_news_ai beat --loglevel=info
```

The system will now automatically fetch news every 6 hours for all stocks in your holdings.

## On-Demand News Fetching

### Method 1: Via Dashboard UI (Easiest)

1. Go to your Portfolio Dashboard: `http://localhost:9150/portfolio/`
2. Click the **"Fetch News"** button (📰) in the top-right corner
3. Wait for the success message
4. View the latest news in the News section or on stock detail pages

### Method 2: Via Management Command

Fetch news for all holdings (last 24 hours):
```bash
python manage.py fetch_holdings_news
```

Fetch news for specific stock:
```bash
python manage.py fetch_holdings_news --symbol TRENT
```

Fetch news from last 6 hours only:
```bash
python manage.py fetch_holdings_news --hours 6
```

Limit articles per stock:
```bash
python manage.py fetch_holdings_news --max-articles 5
```

## How It Works

1. **Stock Selection**: The system identifies all unique stocks in your portfolio holdings
2. **News Search**: For each stock, it searches Google News using:
   - `{SYMBOL} stock` (e.g., "TRENT stock")
   - `{Company Name} share price` (e.g., "Trent Limited share price")
3. **Filtering**: 
   - Removes duplicate articles
   - Skips articles older than specified hours
   - Uses AI to filter out non-relevant articles
4. **AI Processing**:
   - Generates brief summaries using Gemini AI
   - Analyzes sentiment (positive/negative/neutral)
   - Identifies if article contains recommendations
5. **Storage**: Saves articles with links to relevant stocks

## What News Gets Fetched?

- Latest financial news mentioning your stocks
- Company announcements and updates
- Market analysis and expert opinions
- Dividend/bonus announcements
- Quarterly results coverage
- Broker recommendations
- Sectoral news affecting your stocks

## Scheduled Tasks Summary

| Task | Frequency | Time (IST) | Description |
|------|-----------|------------|-------------|
| Morning News Collection | Daily | 6:00 AM | Collects general market news |
| Holdings News Fetch | Every 6 hours | 12AM, 6AM, 12PM, 6PM | Fetches news for your holdings |
| News Analysis | Daily | 7:30 AM | AI analysis of collected news |
| Generate Recommendations | Daily | 8:30 AM | Creates AI recommendations |
| Cleanup Old Data | Daily | 11:00 PM | Removes old articles (30+ days) |

## Viewing Fetched News

1. **Portfolio Dashboard**: View recent news for each stock
2. **Stock Detail Page**: See all news for a specific stock
3. **Holding Detail Page**: View news and events for your holdings
4. **Stock Events Page**: Click calendar icon (📅) to see events and related news

## Troubleshooting

### No News Appearing?
1. Check if you have holdings in your portfolio
2. Verify the stocks have valid symbols
3. Check Django logs for API errors
4. Try fetching manually first to test

### Celery Not Working?
1. Ensure Redis is running: `redis-cli ping` should return `PONG`
2. Check Celery worker logs for errors
3. Verify `CELERY_BROKER_URL` in settings.py

### Too Many API Requests?
- Reduce `--max-articles` parameter
- Increase time between manual fetches
- The 6-hour automatic schedule is already optimized

## Best Practices

1. **Run manual fetch** after importing new holdings
2. **Monitor first few runs** to ensure everything works
3. **Check logs regularly** for any API rate limiting
4. **Keep Redis running** for background tasks
5. **Restart Celery** after code changes to tasks

## Example Workflow

```bash
# Initial setup (one time)
redis-server &  # Start Redis in background

# Start workers (keep running in separate terminals)
celery -A stock_news_ai worker --loglevel=info
celery -A stock_news_ai beat --loglevel=info

# Manual fetch when needed
python manage.py fetch_holdings_news --hours 6 --max-articles 5

# View in browser
# Go to http://localhost:9150/portfolio/
# Click "Fetch News" button or view existing news
```

## Related Commands

- `python manage.py scrape_news` - Fetch general market news
- `python manage.py fetch_stock_events --holdings-only` - Fetch stock events
- `python manage.py init_data` - Initialize sample data

## Support

For issues or questions, check:
- Django logs: Look for errors in console
- Celery logs: Check worker output
- Redis logs: Verify Redis is running
- News scraper logs: Check for API rate limiting
