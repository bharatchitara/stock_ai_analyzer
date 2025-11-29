"""
AI-powered portfolio analysis with sentiment, recommendations, and technical analysis
"""
import logging
import requests
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
import json

logger = logging.getLogger(__name__)


class PortfolioAnalyzer:
    """Comprehensive portfolio analysis using AI and market data"""
    
    def __init__(self):
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
    
    def analyze_portfolio(self, holdings_queryset) -> Dict:
        """
        Perform comprehensive analysis on all portfolio holdings
        Returns analysis for each stock with recommendations
        """
        results = {
            'analyzed_at': timezone.now(),
            'holdings_analysis': [],
            'portfolio_summary': {
                'total_holdings': holdings_queryset.count(),
                'buy_recommendations': 0,
                'sell_recommendations': 0,
                'hold_recommendations': 0,
                'high_risk_count': 0,
                'positive_sentiment': 0,
                'negative_sentiment': 0,
            }
        }
        
        for holding in holdings_queryset:
            try:
                analysis = self.analyze_single_holding(holding)
                results['holdings_analysis'].append(analysis)
                
                # Update summary counts
                if analysis['recommendation'] == 'BUY':
                    results['portfolio_summary']['buy_recommendations'] += 1
                elif analysis['recommendation'] == 'SELL':
                    results['portfolio_summary']['sell_recommendations'] += 1
                else:
                    results['portfolio_summary']['hold_recommendations'] += 1
                
                if analysis.get('risk_level') == 'HIGH':
                    results['portfolio_summary']['high_risk_count'] += 1
                
                if analysis.get('sentiment', 0) > 0:
                    results['portfolio_summary']['positive_sentiment'] += 1
                elif analysis.get('sentiment', 0) < 0:
                    results['portfolio_summary']['negative_sentiment'] += 1
                    
            except Exception as e:
                logger.error(f"Error analyzing {holding.stock.symbol}: {str(e)}")
                continue
        
        return results
    
    def analyze_single_holding(self, holding) -> Dict:
        """Analyze a single stock holding"""
        stock = holding.stock
        
        # Get market data
        price_data = self._get_price_data(stock.symbol)
        
        # Get news sentiment
        news_analysis = self._analyze_news(stock.symbol)
        
        # Technical analysis
        technical_analysis = self._technical_analysis(stock.symbol, price_data)
        
        # Corporate actions and insider trading
        corporate_info = self._get_corporate_actions(stock.symbol)
        
        # Valuation assessment
        valuation = self._assess_valuation(stock, price_data)
        
        # Generate AI recommendation
        ai_recommendation = self._generate_ai_recommendation(
            stock=stock,
            holding=holding,
            price_data=price_data,
            news_analysis=news_analysis,
            technical_analysis=technical_analysis,
            corporate_info=corporate_info,
            valuation=valuation
        )
        
        return {
            'stock_symbol': stock.symbol,
            'stock_name': stock.company_name,
            'holding_quantity': holding.quantity,
            'average_price': float(holding.average_price),
            'current_price': float(stock.current_price or holding.average_price),
            'pnl': float(holding.pnl),
            'pnl_percentage': float(holding.pnl_percentage),
            'recommendation': ai_recommendation['action'],
            'confidence': ai_recommendation['confidence'],
            'reasoning': ai_recommendation['reasoning'],
            'risk_level': ai_recommendation['risk_level'],
            'target_price': ai_recommendation.get('target_price'),
            'stop_loss': ai_recommendation.get('stop_loss'),
            'sentiment': news_analysis['overall_sentiment'],
            'sentiment_score': news_analysis['sentiment_score'],
            'news_summary': news_analysis['summary'],
            'recent_news': news_analysis['articles'][:5],
            'technical_signals': technical_analysis,
            'corporate_actions': corporate_info,
            'valuation_status': valuation['status'],
            'valuation_metrics': valuation['metrics'],
        }
    
    def _get_price_data(self, symbol: str) -> Dict:
        """Fetch historical price data for technical analysis"""
        try:
            # Using Yahoo Finance for historical data
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS"
            params = {
                'interval': '1d',
                'range': '3mo'  # 3 months of data
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    
                    timestamps = result.get('timestamp', [])
                    quotes = result.get('indicators', {}).get('quote', [{}])[0]
                    
                    return {
                        'timestamps': timestamps,
                        'open': quotes.get('open', []),
                        'high': quotes.get('high', []),
                        'low': quotes.get('low', []),
                        'close': quotes.get('close', []),
                        'volume': quotes.get('volume', []),
                    }
            
            return {}
            
        except Exception as e:
            logger.debug(f"Error fetching price data for {symbol}: {str(e)}")
            return {}
    
    def _analyze_news(self, symbol: str) -> Dict:
        """Analyze recent news sentiment for the stock"""
        from news.models import NewsArticle
        
        # Get recent news articles (last 30 days)
        cutoff_date = timezone.now() - timedelta(days=30)
        articles_qs = NewsArticle.objects.filter(
            mentioned_stocks__symbol=symbol,
            published_at__gte=cutoff_date
        ).order_by('-published_at')
        
        # Get total count first
        total_articles = articles_qs.count()
        
        if total_articles == 0:
            return {
                'overall_sentiment': 0,
                'sentiment_score': 0,
                'summary': f'No recent news available for {symbol}',
                'articles': []
            }
        
        # Get counts by sentiment (may include PENDING)
        positive_count = articles_qs.filter(sentiment='POSITIVE').count()
        negative_count = articles_qs.filter(sentiment='NEGATIVE').count()
        neutral_count = articles_qs.filter(sentiment='NEUTRAL').count()
        pending_count = articles_qs.filter(sentiment='PENDING').count()
        
        # Now slice to get articles for list
        articles = list(articles_qs[:20])
        
        # Calculate sentiment score only from analyzed articles (not PENDING)
        analyzed_count = positive_count + negative_count + neutral_count
        if analyzed_count > 0:
            sentiment_score = (positive_count - negative_count) / analyzed_count
        else:
            # All articles are PENDING, treat as neutral
            sentiment_score = 0
        
        # Categorize articles
        article_list = []
        for article in articles[:10]:
            # For display, show PENDING as NEUTRAL
            display_sentiment = article.sentiment if article.sentiment != 'PENDING' else 'NEUTRAL'
            article_list.append({
                'title': article.title,
                'sentiment': display_sentiment,
                'impact_level': article.impact_level,
                'category': article.category.name if article.category else 'OTHER',
                'published_at': article.published_at.strftime('%Y-%m-%d'),
                'url': article.url
            })
        
        # Generate summary
        if analyzed_count == 0:
            summary = f"Found {total_articles} recent articles (sentiment analysis pending)"
        elif sentiment_score > 0.3:
            summary = f"Predominantly positive news ({positive_count} positive, {negative_count} negative)"
        elif sentiment_score < -0.3:
            summary = f"Predominantly negative news ({positive_count} positive, {negative_count} negative)"
        else:
            summary = f"Mixed sentiment ({positive_count} positive, {negative_count} negative, {neutral_count} neutral)"
            if pending_count > 0:
                summary += f", {pending_count} pending analysis"
        
        return {
            'overall_sentiment': sentiment_score,
            'sentiment_score': sentiment_score,
            'summary': summary,
            'articles': article_list,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
        }
    
    def _technical_analysis(self, symbol: str, price_data: Dict) -> Dict:
        """Perform technical analysis on price data"""
        if not price_data or not price_data.get('close'):
            return {
                'trend': 'UNKNOWN',
                'signals': [],
                'patterns': []
            }
        
        closes = [p for p in price_data['close'] if p is not None]
        highs = [p for p in price_data['high'] if p is not None]
        lows = [p for p in price_data['low'] if p is not None]
        
        if len(closes) < 20:
            return {
                'trend': 'INSUFFICIENT_DATA',
                'signals': [],
                'patterns': []
            }
        
        signals = []
        patterns = []
        
        # Moving averages
        ma_20 = sum(closes[-20:]) / 20
        ma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
        current_price = closes[-1]
        
        # Trend analysis
        if current_price > ma_20:
            trend = 'UPTREND'
            signals.append('Price above 20-day MA')
        else:
            trend = 'DOWNTREND'
            signals.append('Price below 20-day MA')
        
        if ma_50:
            if ma_20 > ma_50:
                signals.append('Golden cross pattern (bullish)')
            else:
                signals.append('Death cross pattern (bearish)')
        
        # Support and resistance
        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        
        if current_price >= recent_high * 0.98:
            signals.append('Near resistance level')
            patterns.append('RESISTANCE')
        
        if current_price <= recent_low * 1.02:
            signals.append('Near support level')
            patterns.append('SUPPORT')
        
        # Momentum
        price_change_5d = ((closes[-1] / closes[-5]) - 1) * 100 if len(closes) >= 5 else 0
        price_change_20d = ((closes[-1] / closes[-20]) - 1) * 100
        
        if price_change_5d > 5:
            signals.append('Strong upward momentum')
            patterns.append('BULLISH_MOMENTUM')
        elif price_change_5d < -5:
            signals.append('Strong downward momentum')
            patterns.append('BEARISH_MOMENTUM')
        
        # Volatility
        price_range = (recent_high - recent_low) / recent_low * 100
        if price_range > 20:
            signals.append('High volatility detected')
        
        return {
            'trend': trend,
            'signals': signals,
            'patterns': patterns,
            'ma_20': round(ma_20, 2),
            'ma_50': round(ma_50, 2) if ma_50 else None,
            'support': round(recent_low, 2),
            'resistance': round(recent_high, 2),
            'price_change_5d': round(price_change_5d, 2),
            'price_change_20d': round(price_change_20d, 2),
        }
    
    def _get_corporate_actions(self, symbol: str) -> Dict:
        """Get information about corporate actions, bulk deals, insider trading"""
        # This would typically call NSE/BSE APIs or scrape their websites
        # For now, returning a placeholder structure
        
        return {
            'bulk_deals': [],
            'insider_trades': [],
            'corporate_actions': [],
            'upcoming_events': []
        }
    
    def _assess_valuation(self, stock, price_data: Dict) -> Dict:
        """Assess if stock is overpriced or underpriced"""
        current_price = float(stock.current_price or 0)
        
        if not current_price or not price_data.get('close'):
            return {
                'status': 'UNKNOWN',
                'metrics': {}
            }
        
        closes = [p for p in price_data['close'] if p is not None]
        
        # Calculate average price over period
        avg_price_3mo = sum(closes) / len(closes)
        
        # Simple valuation based on price relative to average
        deviation = ((current_price / avg_price_3mo) - 1) * 100
        
        if deviation > 15:
            status = 'OVERVALUED'
        elif deviation < -15:
            status = 'UNDERVALUED'
        else:
            status = 'FAIR_VALUE'
        
        return {
            'status': status,
            'metrics': {
                'current_price': current_price,
                '3mo_avg_price': round(avg_price_3mo, 2),
                'deviation_percent': round(deviation, 2)
            }
        }
    
    def _generate_ai_recommendation(self, stock, holding, price_data, news_analysis, 
                                   technical_analysis, corporate_info, valuation) -> Dict:
        """Generate AI-powered recommendation using all available data"""
        
        # Scoring system
        buy_score = 0
        sell_score = 0
        
        # News sentiment impact
        sentiment = news_analysis['sentiment_score']
        if sentiment > 0.3:
            buy_score += 2
        elif sentiment < -0.3:
            sell_score += 2
        
        # Technical analysis impact
        if technical_analysis.get('trend') == 'UPTREND':
            buy_score += 2
        elif technical_analysis.get('trend') == 'DOWNTREND':
            sell_score += 2
        
        if 'BULLISH_MOMENTUM' in technical_analysis.get('patterns', []):
            buy_score += 1
        if 'BEARISH_MOMENTUM' in technical_analysis.get('patterns', []):
            sell_score += 1
        
        # Valuation impact
        if valuation['status'] == 'UNDERVALUED':
            buy_score += 2
        elif valuation['status'] == 'OVERVALUED':
            sell_score += 2
        
        # P&L consideration
        pnl_percent = holding.pnl_percentage
        if pnl_percent > 20:
            # Consider booking profits
            sell_score += 1
        elif pnl_percent < -10:
            # Consider averaging or cutting losses
            if buy_score > sell_score:
                buy_score += 1  # Good opportunity to average
            else:
                sell_score += 1  # Cut losses
        
        # Determine action
        if buy_score > sell_score and buy_score >= 4:
            action = 'BUY'
            confidence = min(buy_score * 15, 90)
        elif sell_score > buy_score and sell_score >= 4:
            action = 'SELL'
            confidence = min(sell_score * 15, 90)
        else:
            action = 'HOLD'
            confidence = 60
        
        # Risk level
        if technical_analysis.get('trend') == 'DOWNTREND' and sentiment < 0:
            risk_level = 'HIGH'
        elif technical_analysis.get('trend') == 'UPTREND' and sentiment > 0:
            risk_level = 'LOW'
        else:
            risk_level = 'MEDIUM'
        
        # Generate reasoning
        reasoning_parts = []
        
        if sentiment > 0.3:
            reasoning_parts.append(f"Positive news sentiment ({news_analysis['positive_count']} positive articles)")
        elif sentiment < -0.3:
            reasoning_parts.append(f"Negative news sentiment ({news_analysis['negative_count']} negative articles)")
        
        if valuation['status'] == 'UNDERVALUED':
            reasoning_parts.append("Stock appears undervalued compared to 3-month average")
        elif valuation['status'] == 'OVERVALUED':
            reasoning_parts.append("Stock appears overvalued compared to 3-month average")
        
        reasoning_parts.extend(technical_analysis.get('signals', [])[:2])
        
        if pnl_percent > 20:
            reasoning_parts.append(f"Strong gains ({pnl_percent:.1f}%) - consider booking partial profits")
        elif pnl_percent < -10:
            reasoning_parts.append(f"Current loss ({pnl_percent:.1f}%) - reassess position")
        
        reasoning = ". ".join(reasoning_parts) if reasoning_parts else "Based on current market conditions"
        
        # Calculate target and stop loss
        current_price = float(stock.current_price or holding.average_price)
        
        if action == 'BUY':
            target_price = current_price * 1.15  # 15% upside
            stop_loss = current_price * 0.92     # 8% stop loss
        elif action == 'SELL':
            target_price = None
            stop_loss = current_price * 0.95     # 5% stop loss
        else:
            target_price = current_price * 1.10  # 10% upside
            stop_loss = current_price * 0.95     # 5% stop loss
        
        return {
            'action': action,
            'confidence': confidence,
            'reasoning': reasoning,
            'risk_level': risk_level,
            'target_price': round(target_price, 2) if target_price else None,
            'stop_loss': round(stop_loss, 2),
            'buy_score': buy_score,
            'sell_score': sell_score,
        }
