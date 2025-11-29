#!/usr/bin/env python
"""Portfolio AI Analysis Helper Script"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_news_ai.settings')
django.setup()

from news.models import UserPortfolio
from portfolio.portfolio_analyzer import PortfolioAnalyzer
from django.contrib.auth.models import User

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
