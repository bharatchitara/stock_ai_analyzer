#!/bin/bash
# Stock Market News AI - On-Demand Analysis Script
# Run news collection + AI analysis + recommendations generation anytime

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Stock Market News AI - Analysis Runner${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""

# Change to project directory (script's directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"
cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please create it first: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source .venv/bin/activate

# Check if Django is accessible
if ! python -c "import django" 2>/dev/null; then
    echo -e "${RED}❌ Django not found in virtual environment!${NC}"
    echo "Please install requirements: pip install -r requirements.txt"
    exit 1
fi

echo -e "${GREEN}✓ Environment ready${NC}"
echo ""

# Function to show progress
show_progress() {
    local message=$1
    echo -e "${BLUE}➜${NC} ${message}"
}

# Function to show success
show_success() {
    local message=$1
    echo -e "${GREEN}✓${NC} ${message}"
}

# Function to show error
show_error() {
    local message=$1
    echo -e "${RED}✗${NC} ${message}"
}

# Step 1: News Collection
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 1: Collecting Latest News${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
show_progress "Scraping news from sources..."

python manage.py shell << 'PYEOF'
print("\n🔍 Starting news collection...")
try:
    # Try to import required modules
    try:
        from news.scraper import scrape_morning_news
        from django.utils import timezone
        
        # Run the news scraper
        result = scrape_morning_news()
        print(f"✓ Collected {result.get('total_articles', 0)} articles")
        print(f"  - Saved: {result.get('articles_saved', 0)}")
        print(f"  - Duplicates: {result.get('duplicates_skipped', 0)}")
    except ImportError as ie:
        print(f"⚠ News scraper not available: {str(ie)}")
        print("  Install missing dependencies: pip install feedparser beautifulsoup4 requests")
        print("  Skipping news collection...")
except Exception as e:
    print(f"✗ Error during news collection: {str(e)}")
PYEOF

if [ $? -eq 0 ]; then
    show_success "News collection step completed"
else
    show_error "News collection failed (continuing anyway...)"
fi
echo ""

# Step 2: Sentiment Analysis
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 2: Analyzing News Sentiment${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
show_progress "Running sentiment analysis on articles..."

python manage.py shell << 'PYEOF'
from news.models import NewsArticle
from analysis.ai_analyzer import NewsAnalyzer
from django.utils import timezone
from datetime import timedelta

print("\n🤖 Starting sentiment analysis...")
try:
    # Get pending articles from last 7 days
    cutoff = timezone.now() - timedelta(days=7)
    pending_articles = NewsArticle.objects.filter(
        sentiment='PENDING',
        published_at__gte=cutoff
    ).order_by('-published_at')[:50]  # Limit to 50 most recent
    
    total = pending_articles.count()
    print(f"Found {total} articles pending analysis")
    
    if total > 0:
        analyzer = NewsAnalyzer()
        analyzed_count = 0
        
        for article in pending_articles:
            try:
                sentiment = analyzer.analyze_sentiment(article.title, article.content or '')
                article.sentiment = sentiment['sentiment']
                article.save()
                analyzed_count += 1
                
                if analyzed_count % 10 == 0:
                    print(f"  Analyzed {analyzed_count}/{total} articles...")
            except Exception as e:
                print(f"  ⚠ Error analyzing article {article.id}: {str(e)}")
                continue
        
        print(f"✓ Analyzed {analyzed_count} articles")
    else:
        print("  No pending articles found")
except Exception as e:
    print(f"✗ Error during sentiment analysis: {str(e)}")
    import traceback
    traceback.print_exc()
PYEOF

if [ $? -eq 0 ]; then
    show_success "Sentiment analysis completed"
else
    show_error "Sentiment analysis failed (continuing anyway...)"
fi
echo ""

# Step 3: Generate Recommendations
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 3: Generating Stock Recommendations${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
show_progress "Analyzing stocks and generating recommendations..."

python manage.py shell << 'PYEOF'
from news.models import Stock, Recommendation
from analysis.ai_analyzer import RecommendationEngine
from django.utils import timezone

print("\n💡 Generating recommendations...")
try:
    engine = RecommendationEngine()
    
    # Get stocks with recent news
    stocks_with_news = Stock.objects.filter(
        news_articles__published_at__gte=timezone.now() - timedelta(days=7)
    ).distinct()[:20]  # Limit to top 20 stocks
    
    total = stocks_with_news.count()
    print(f"Generating recommendations for {total} stocks...")
    
    if total > 0:
        generated_count = 0
        
        for stock in stocks_with_news:
            try:
                recommendation = engine.generate_recommendation(stock)
                if recommendation:
                    generated_count += 1
                    print(f"  ✓ {stock.symbol}: {recommendation.get('action', 'N/A')}")
            except Exception as e:
                print(f"  ⚠ Error for {stock.symbol}: {str(e)}")
                continue
        
        print(f"✓ Generated {generated_count} recommendations")
    else:
        print("  No stocks with recent news found")
except Exception as e:
    print(f"✗ Error generating recommendations: {str(e)}")
    import traceback
    traceback.print_exc()
PYEOF

if [ $? -eq 0 ]; then
    show_success "Recommendations generated"
else
    show_error "Recommendation generation failed (continuing anyway...)"
fi
echo ""

# Step 4: Update Stock Prices
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 4: Updating Stock Prices${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
show_progress "Fetching latest stock prices..."

python manage.py update_prices --all 2>&1 | grep -v "^System check identified"

if [ $? -eq 0 ]; then
    show_success "Stock prices updated"
else
    show_error "Stock price update failed (continuing anyway...)"
fi
echo ""

# Step 5: Portfolio Analysis (if portfolio exists)
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 5: Portfolio AI Analysis${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
show_progress "Running AI analysis on portfolio holdings..."

python manage.py shell << 'PYEOF'
from news.models import UserPortfolio, PortfolioHolding
from portfolio.portfolio_analyzer import PortfolioAnalyzer
from django.contrib.auth.models import User
from datetime import timedelta

print("\n📊 Running portfolio analysis...")
try:
    # Get user's portfolio
    user = User.objects.first()
    if not user:
        print("  ⚠ No user found, skipping portfolio analysis")
    else:
        portfolio = UserPortfolio.objects.filter(user=user).first()
        if not portfolio:
            print("  ⚠ No portfolio found, skipping analysis")
        else:
            holdings = portfolio.holdings.all()
            if holdings.count() == 0:
                print("  ⚠ No holdings in portfolio")
            else:
                print(f"  Analyzing {holdings.count()} holdings...")
                
                analyzer = PortfolioAnalyzer()
                result = analyzer.analyze_portfolio(holdings)
                
                print(f"✓ Analysis complete for {len(result['holdings_analysis'])} stocks")
                print(f"  - BUY recommendations: {result['portfolio_summary']['buy_recommendations']}")
                print(f"  - SELL recommendations: {result['portfolio_summary']['sell_recommendations']}")
                print(f"  - HOLD recommendations: {result['portfolio_summary']['hold_recommendations']}")
                print(f"  - High risk stocks: {result['portfolio_summary']['high_risk_count']}")
except Exception as e:
    print(f"✗ Error during portfolio analysis: {str(e)}")
    import traceback
    traceback.print_exc()
PYEOF

if [ $? -eq 0 ]; then
    show_success "Portfolio analysis completed"
else
    show_error "Portfolio analysis failed"
fi
echo ""

# Summary
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Analysis Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Visit http://localhost:9150/portfolio/ to view results"
echo "  2. Click 'AI Analysis' button for detailed insights"
echo "  3. Check news at http://localhost:9150/news/"
echo ""
echo -e "${BLUE}💡 Tip:${NC} Run this script anytime to get latest analysis"
echo -e "${BLUE}    Usage: ./run_analysis.sh${NC}"
echo ""
