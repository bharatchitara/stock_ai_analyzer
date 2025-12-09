# Automatic News Fetching - Quick Start

## 🎯 What's New?

Your portfolio now automatically fetches the latest news for all your holdings every 6 hours! You can also fetch news on-demand with a single click.

## 🚀 Quick Start

### Option 1: Use the Startup Script (Easiest)
```bash
./start_with_automation.sh
```
This starts everything you need: Django, Celery Worker, Celery Beat, and Redis.

### Option 2: Manual Start
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
source .venv/bin/activate
celery -A stock_news_ai worker --loglevel=info

# Terminal 3: Start Celery Beat
source .venv/bin/activate
celery -A stock_news_ai beat --loglevel=info

# Terminal 4: Start Django
source .venv/bin/activate
python manage.py runserver 9150
```

## 📰 How to Fetch News

### From the Dashboard (On-Demand)
1. Go to http://localhost:9150/portfolio/
2. Click the **"Fetch News"** button (📰)
3. Wait for the success message
4. View news on stock detail pages

### Via Command Line
```bash
# Fetch news for all holdings
python manage.py fetch_holdings_news

# Fetch for specific stock
python manage.py fetch_holdings_news --symbol TRENT

# Fetch only last 6 hours
python manage.py fetch_holdings_news --hours 6
```

## ⏰ Automatic Schedule

| Task | Frequency | Time (IST) |
|------|-----------|------------|
| **Holdings News** | Every 6 hours | 12AM, 6AM, 12PM, 6PM |
| Morning Market News | Daily | 6:00 AM |
| News Analysis | Daily | 7:30 AM |
| Recommendations | Daily | 8:30 AM |

## 📊 What It Does

1. **Identifies** all stocks in your portfolio
2. **Searches** Google News for latest articles
3. **Filters** using AI to keep only relevant news
4. **Summarizes** each article with sentiment analysis
5. **Links** news to your stocks automatically

## 🎯 Features

✅ Automatic fetching every 6 hours  
✅ On-demand fetch with one click  
✅ AI-powered relevance filtering  
✅ Sentiment analysis  
✅ Duplicate detection  
✅ Links news to multiple stocks  

## 📖 Full Documentation

See `docs/NEWS_FETCH_GUIDE.md` for complete details.

## 🔧 Troubleshooting

**No news appearing?**
- Ensure you have holdings in your portfolio
- Run manual fetch first: `python manage.py fetch_holdings_news`

**Celery not working?**
- Check Redis is running: `redis-cli ping`
- Check logs in `logs/` directory

**Need help?**
- Check `logs/celery_worker.log` for errors
- Run with `--hours 24` to get more articles

## 💡 Pro Tips

1. **First time?** Run manual fetch: `python manage.py fetch_holdings_news`
2. **Want more news?** Use `--max-articles 10`
3. **Monitor logs** during first few runs
4. **Keep Redis running** for background tasks
