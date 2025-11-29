# Stock Market News AI Dashboard

An AI-powered Django application for tracking Indian stock market news before 9:10 AM market opening with intelligent categorization and stock recommendations.

## ⚡ Quick Commands

```bash
# Start Django server
python manage.py runserver 9150

# Quick portfolio analysis (30 sec)
./quick_analysis.sh

# Full analysis with news collection (3-5 min)  
./run_analysis.sh
```

📖 **See [docs/ANALYSIS_SCRIPTS.md](docs/ANALYSIS_SCRIPTS.md) for detailed usage**

## 🚀 Features

- **📰 Automated News Collection**: Scrapes major Indian financial news sources before market hours
- **🤖 AI-Powered Analysis**: Uses OpenAI/Transformers for sentiment analysis and categorization
- **📊 Smart Recommendations**: Generates BUY/SELL/HOLD recommendations based on news sentiment
- **📈 Interactive Dashboard**: Bootstrap-based responsive UI with charts and analytics
- **⏰ Scheduled Tasks**: Celery-powered background jobs for automated data collection
- **🎯 Pre-Market Focus**: Specifically designed for news analysis before 9:10 AM market opening

## 🛠️ Technology Stack

- **Backend**: Django 5.2, Django REST Framework
- **Frontend**: Bootstrap 5, Chart.js, Vanilla JavaScript
- **Database**: PostgreSQL (production), SQLite (development)
- **AI/ML**: OpenAI API, Hugging Face Transformers
- **Background Tasks**: Celery, Redis
- **News Sources**: Economic Times, Business Standard, LiveMint, MoneyControl

## 📋 Prerequisites

- Python 3.8+
- Redis server
- OpenAI API key (optional, for enhanced AI features)

## 🚦 Quick Start

### 1. Clone and Setup Environment

```bash
cd projectBuff
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env file with your configuration
```

Required environment variables:
- `SECRET_KEY`: Django secret key
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `REDIS_URL`: Redis connection URL
- `DEBUG`: Set to True for development

### 4. Initialize Database

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py init_data  # Load default stocks and categories
python manage.py createsuperuser
```

### 5. Start Redis Server

```bash
# On macOS with Homebrew
brew services start redis

# On Ubuntu
sudo systemctl start redis-server

# Or run Redis directly
redis-server
```

### 6. Start Celery Worker (in separate terminal)

```bash
source venv/bin/activate
celery -A stock_news_ai worker --loglevel=info
```

### 7. Start Celery Beat (in separate terminal)

```bash
source venv/bin/activate
celery -A stock_news_ai beat --loglevel=info
```

### 8. Run Django Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the dashboard.

## 📅 Automated Schedule

The system automatically runs the following tasks:

- **6:00 AM IST**: Collect news from all sources
- **7:30 AM IST**: Analyze collected news with AI
- **8:30 AM IST**: Generate stock recommendations
- **9:00 AM IST**: Send notifications (if configured)

## 🎯 Key Models

### NewsArticle
- Title, content, URL, source
- AI analysis: sentiment, category, impact level
- Related stocks and recommendations
- Pre-market timing detection

### Recommendation
- Stock symbol, recommendation type (BUY/SELL/HOLD/WATCH)
- Confidence level, risk assessment
- AI-generated reasoning and key factors
- Validity period and related articles

### Stock
- Major Indian stocks (Nifty 50, Sensex)
- Company details, sector classification
- Market cap and index membership

## 🔧 Management Commands

```bash
# Initialize default data
python manage.py init_data

# Manually collect news
python manage.py shell
>>> from news.tasks import collect_morning_news
>>> collect_morning_news.delay()

# Manually analyze news
>>> from news.tasks import analyze_news_batch
>>> analyze_news_batch.delay()

# Generate recommendations
>>> from news.tasks import generate_daily_recommendations
>>> generate_daily_recommendations.delay()
```

## 📊 Dashboard Features

### Home Dashboard
- Real-time sentiment distribution charts
- Pre-market news timeline
- Active recommendations summary
- Market session status

### News Section
- Filterable news list by sentiment, category, source
- Detailed article view with AI analysis
- Related stock recommendations
- Pre-market badge for timing

### Recommendations
- Stock recommendations with confidence levels
- Risk assessment and reasoning
- Related news articles
- Performance tracking

### Watchlist (User Feature)
- Personal stock watchlist
- Custom alerts and notifications
- Filtered news and recommendations

## 🔌 API Endpoints

```bash
# Sentiment chart data
GET /api/sentiment-chart/

# Recommendation distribution
GET /api/recommendation-chart/

# News timeline
GET /api/news-timeline/?days=7
```

## 🚀 Production Deployment

### Environment Setup
1. Set `DEBUG=False` in environment
2. Configure PostgreSQL database
3. Set up Redis for production
4. Configure proper `SECRET_KEY`
5. Add domain to `ALLOWED_HOSTS`

### Using Docker (Recommended)
```bash
# Create Dockerfile and docker-compose.yml
docker-compose up -d
```

### Manual Deployment
1. Install dependencies on server
2. Configure Nginx/Apache
3. Set up Gunicorn
4. Configure Celery with supervisor
5. Set up SSL certificate

## 📈 News Sources Configured

- **Economic Times**: Market and economy news
- **Business Standard**: Financial markets coverage
- **LiveMint**: Real-time market updates
- **MoneyControl**: Stock analysis and reports
- **Financial Express**: Business news
- **Hindu BusinessLine**: Corporate coverage

## 🤖 AI Features

### Sentiment Analysis
- Positive, Negative, Neutral classification
- Confidence scoring (0-1 scale)
- Context-aware analysis for financial news

### News Categorization
- Market Opening, Earnings, Policy, Global
- Sector-specific, IPO, M&A, Regulatory
- Color-coded for easy identification

### Impact Assessment
- High, Medium, Low impact levels
- Based on stock mentions and keywords
- Influences recommendation generation

### Recommendation Engine
- Multi-factor analysis combining:
  - News sentiment scores
  - Impact assessment
  - Historical patterns
  - Stock-specific factors

## 🔧 Customization

### Adding News Sources
1. Update `news/scraper.py` with new source config
2. Add RSS feeds and selectors
3. Test scraping functionality

### Custom AI Models
1. Replace OpenAI with local models
2. Implement custom analysis logic
3. Update `analysis/ai_analyzer.py`

### UI Customization
1. Modify Bootstrap themes
2. Update dashboard templates
3. Add custom charts and widgets

## 📝 Logging

Logs are configured for:
- News scraping activities
- AI analysis results
- Recommendation generation
- Error tracking and debugging

Check `logs/` directory for detailed logs.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting guide
2. Review logs for error details
3. Create issue with detailed description

## ⚠️ Disclaimer

This tool is for educational and research purposes. Stock recommendations generated are based on news sentiment analysis and should not be considered as financial advice. Always consult with qualified financial advisors before making investment decisions.

---

Built with ❤️ for the Indian stock market community.