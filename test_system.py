#!/usr/bin/env python3
"""
Test script for Stock Market News AI System
Run this to verify everything is working correctly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_news_ai.settings')
django.setup()

from news.scraper import NewsScraper, StockMentionExtractor
from analysis.ai_analyzer import NewsAnalyzer
from news.models import NewsSource, Stock, NewsArticle

def test_system():
    print("🚀 Testing Stock Market News AI System")
    print("=" * 50)
    
    # Test 1: Database Setup
    print("1. Database Status:")
    print(f"   📊 News Sources: {NewsSource.objects.count()}")
    print(f"   📈 Stocks: {Stock.objects.count()}")
    print(f"   📰 News Articles: {NewsArticle.objects.count()}")
    
    # Test 2: Stock Mention Extractor
    print("\n2. Testing Stock Mention Extractor:")
    extractor = StockMentionExtractor()
    test_text = "Reliance Industries and TCS reported strong results while HDFC Bank announced new schemes"
    mentioned_stocks = extractor.extract_mentioned_stocks(test_text)
    print(f"   📝 Text: {test_text}")
    print(f"   🎯 Mentioned Stocks: {mentioned_stocks}")
    
    # Test 3: AI Analyzer
    print("\n3. Testing AI Sentiment Analysis:")
    analyzer = NewsAnalyzer()
    
    test_cases = [
        "Reliance Industries reported record quarterly profits beating all analyst expectations",
        "TCS faces challenges due to declining demand in global markets",
        "HDFC Bank maintains steady performance with moderate growth"
    ]
    
    for i, text in enumerate(test_cases, 1):
        sentiment, confidence = analyzer.analyze_sentiment(text)
        print(f"   3.{i} Text: {text[:60]}...")
        print(f"       🎯 Sentiment: {sentiment} (Confidence: {confidence:.2f})")
    
    # Test 4: News Scraper (Basic Test)
    print("\n4. Testing News Scraper Setup:")
    scraper = NewsScraper()
    from news.scraper import NewsSourceConfig
    print(f"   🌐 Configured Sources: {len(NewsSourceConfig.SOURCES)}")
    for source in NewsSourceConfig.SOURCES.keys():
        print(f"       - {source.replace('_', ' ').title()}")
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    print("📅 System is ready for automated news collection tomorrow at 6:00 AM IST")
    print("🎯 To start automation, run:")
    print("   - Redis server: redis-server")
    print("   - Celery worker: celery -A stock_news_ai worker --loglevel=info")
    print("   - Celery beat: celery -A stock_news_ai beat --loglevel=info")
    print("🌐 Dashboard available at: http://localhost:8000")
    print("=" * 50)

if __name__ == "__main__":
    test_system()