# Quick Start Guide

## 🚀 Project Successfully Created!

Your **Stock Market News AI Dashboard** is now ready and running at `http://localhost:8000`

### ✅ What's Been Set Up:

1. **Complete Django Project Structure**
   - News collection and storage app
   - AI analysis engine  
   - Interactive dashboard with Bootstrap UI
   - Background task processing with Celery

2. **Database Models**
   - NewsArticle, Stock, Category, Recommendation
   - User watchlist and market session tracking
   - 30+ major Indian stocks pre-loaded
   - 6 major financial news sources configured

3. **AI-Powered Features**
   - Sentiment analysis (Positive/Negative/Neutral)
   - News categorization (Earnings, Policy, IPO, etc.)
   - Impact level assessment (High/Medium/Low)
   - Stock recommendation generation

4. **Automated Scheduling**
   - 6:00 AM IST: Collect pre-market news
   - 7:30 AM IST: AI analysis of articles
   - 8:30 AM IST: Generate recommendations

## 🎯 Next Steps to Get Started:

### 1. Access the Dashboard
- Visit: `http://localhost:8000`
- Admin panel: `http://localhost:8000/admin` (admin/admin)

### 2. Configure API Keys (Optional but Recommended)

Edit `.env` file:
```bash
cp .env.example .env
```

Add your OpenAI API key for enhanced AI features:
```
OPENAI_API_KEY=your-api-key-here
```

### 3. Start Background Workers (For Automation)

**Terminal 1: Celery Worker**
```bash
source venv/bin/activate
celery -A stock_news_ai worker --loglevel=info
```

**Terminal 2: Celery Beat (Scheduler)**
```bash
source venv/bin/activate  
celery -A stock_news_ai beat --loglevel=info
```

**Terminal 3: Redis (Required for Celery)**
```bash
# Install Redis if not installed
brew install redis  # macOS
# OR
sudo apt-get install redis-server  # Ubuntu

# Start Redis
redis-server
```

### 4. Test News Collection Manually

```python
# In Django shell
python manage.py shell

>>> from news.tasks import collect_morning_news
>>> result = collect_morning_news()
>>> print(result)
```

## 📊 Dashboard Features:

### Home Dashboard
- Real-time sentiment analysis charts
- Pre-market news feed (before 9:10 AM)
- Active stock recommendations
- Market session status

### News Section
- Filter by source, sentiment, category, date
- AI-analyzed articles with impact levels
- Stock mentions and recommendations

### Recommendations
- BUY/SELL/HOLD/WATCH recommendations  
- Confidence levels and risk assessment
- AI-generated reasoning

## 🛠️ Development Commands:

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Collect static files for production
python manage.py collectstatic

# Create admin user
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Django shell for testing
python manage.py shell
```

## 🎨 Customization Options:

### Add New News Sources
1. Update `news/scraper.py` with RSS feeds
2. Configure selectors for content extraction
3. Test scraping functionality

### Modify AI Analysis
1. Update `analysis/ai_analyzer.py`
2. Customize sentiment analysis logic
3. Add new categorization rules

### UI/UX Changes
1. Edit templates in `dashboard/templates/`
2. Modify Bootstrap themes and colors
3. Add new chart types with Chart.js

## 🚀 Production Deployment:

### Environment Setup
```bash
# Set production settings
DEBUG=False
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=yourdomain.com
```

### Docker Deployment (Recommended)
```dockerfile
# Dockerfile example
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "stock_news_ai.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Manual Server Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure Nginx/Apache reverse proxy
3. Set up Gunicorn WSGI server
4. Configure Celery with supervisor/systemd
5. Set up PostgreSQL database
6. Configure SSL certificate

## 📈 Sample Data & Testing:

The system comes pre-loaded with:
- **30 major Indian stocks** (Nifty 50, Sensex)
- **11 news categories** (Earnings, Policy, IPO, etc.)  
- **6 financial news sources** (ET, BS, Mint, etc.)

Test the complete workflow:
1. Run news collection task
2. Analyze collected articles with AI
3. Generate stock recommendations
4. View results in dashboard

## 🔧 Troubleshooting:

### Common Issues:
1. **Celery not working**: Ensure Redis is running
2. **News scraping fails**: Check RSS feed URLs
3. **AI analysis errors**: Verify OpenAI API key
4. **Dashboard not loading**: Check Django URL configuration

### Logs:
- Django: Check console output
- Celery: Check worker logs
- News scraping: Check Django logs

## 🆘 Support:

- Check the comprehensive `README.md` for detailed documentation
- Review error logs for debugging
- Test individual components using Django shell
- Verify all dependencies are properly installed

---

**🎉 Congratulations! Your Indian Stock Market News AI Dashboard is ready for use!**

Start by visiting `http://localhost:8000` to explore the interface and begin collecting pre-market news insights.