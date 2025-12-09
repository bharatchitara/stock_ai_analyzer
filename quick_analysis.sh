#!/bin/bash
# Quick Portfolio Analysis Script
# Runs AI analysis on your portfolio with existing news data

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Quick Portfolio AI Analysis${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source .venv/bin/activate

# Function to check and kill Django server
kill_django_server() {
    echo -e "${BLUE}🔍 Checking for existing Django server...${NC}"
    for port in 8000 9000 9150; do
        PIDS=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$PIDS" ]; then
            echo -e "${BLUE}🛑 Found Django server on port $port. Stopping...${NC}"
            kill -9 $PIDS 2>/dev/null
        fi
    done
    sleep 1
}

# Kill existing Django server if running
kill_django_server

echo -e "${YELLOW}Step 1/3: Updating Stock Prices...${NC}"
python manage.py update_prices --all 2>&1 | tail -5
echo -e "${GREEN}✓ Prices updated${NC}"
echo ""

echo -e "${YELLOW}Step 2/3: Analyzing News Sentiment...${NC}"
python manage.py shell << 'PYEOF'
from news.models import NewsArticle
from django.utils import timezone
from datetime import timedelta

try:
    from google import genai
    from django.conf import settings
    
    cutoff = timezone.now() - timedelta(days=30)
    pending = NewsArticle.objects.filter(
        sentiment='PENDING',
        published_at__gte=cutoff
    )[:20]
    
    if pending.count() > 0:
        from news.models import AIConfig
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        config = AIConfig.get_active_config()
        model_name = config.gemini_model
        
        for article in pending:
            try:
                prompt = f"Analyze sentiment of this news title: '{article.title}'\nRespond with only: POSITIVE, NEGATIVE, or NEUTRAL"
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                sentiment = response.text.strip().upper()
                
                if sentiment in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
                    article.sentiment = sentiment
                    article.save()
            except:
                continue
        
        print(f"✓ Analyzed {pending.count()} articles")
    else:
        print("  No pending articles")
except Exception as e:
    print(f"⚠ Sentiment analysis skipped: {str(e)}")
PYEOF
echo ""

echo -e "${YELLOW}Step 3/3: Running Portfolio AI Analysis...${NC}"
python manage.py shell << 'PYEOF'
from news.models import UserPortfolio
from portfolio.portfolio_analyzer import PortfolioAnalyzer
from django.contrib.auth.models import User
import sys

try:
    user = User.objects.first()
    if not user:
        print("  ⚠ No user found")
        sys.exit(0)
    
    portfolio = UserPortfolio.objects.filter(user=user).first()
    if not portfolio:
        print("  ⚠ No portfolio found")
        sys.exit(0)
    
    holdings = portfolio.holdings.all()
    if not holdings.exists():
        print("  ⚠ No holdings in portfolio")
        sys.exit(0)
    
    print(f"  Analyzing {holdings.count()} holdings...\n")
    
    analyzer = PortfolioAnalyzer()
    result = analyzer.analyze_portfolio(holdings)
    
    summary = result['portfolio_summary']
    print(f"✓ Analysis Complete!")
    print(f"  • BUY: {summary['buy_recommendations']} stocks")
    print(f"  • HOLD: {summary['hold_recommendations']} stocks")
    print(f"  • SELL: {summary['sell_recommendations']} stocks")
    print(f"  • High Risk: {summary['high_risk_count']} stocks")
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

echo ""
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Analysis Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""
echo -e "View results at: ${YELLOW}http://localhost:9150/portfolio/${NC}"
echo -e "Click '${YELLOW}AI Analysis${NC}' button for detailed insights"
echo ""
