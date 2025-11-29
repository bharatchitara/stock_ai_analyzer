"""
AI-powered news analysis and categorization module
"""

# Optional imports - system works without these
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

import json
import re
from typing import Dict, List, Tuple, Optional
from django.conf import settings
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    """AI-powered news analysis for sentiment, categorization, and impact assessment"""
    
    def __init__(self):
        self.openai_client = None
        self.sentiment_analyzer = None
        self.setup_ai_models()
    
    def setup_ai_models(self):
        """Initialize AI models"""
        try:
            # Setup OpenAI
            if OPENAI_AVAILABLE and hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                openai.api_key = settings.OPENAI_API_KEY
                self.openai_client = openai
                logger.info("OpenAI client initialized")
            
            # Setup local sentiment analysis model (optional)
            if TRANSFORMERS_AVAILABLE:
                try:
                    self.sentiment_analyzer = pipeline(
                        "sentiment-analysis",
                        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                        tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest"
                    )
                    logger.info("Sentiment analysis model initialized")
                except Exception as e:
                    logger.warning(f"Could not load transformers model: {e}")
                    self.sentiment_analyzer = None
            
        except Exception as e:
            logger.error(f"Error setting up AI models: {str(e)}")
            logger.info("System will use rule-based analysis as fallback")
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment of news text
        Returns: (sentiment, confidence_score)
        """
        try:
            if self.sentiment_analyzer:
                # Use local model
                result = self.sentiment_analyzer(text[:512])  # Limit text length
                
                # Convert to our format
                label = result[0]['label']
                score = result[0]['score']
                
                # Map to our sentiment categories
                if 'POSITIVE' in label.upper() or label in ['4', '5'] or 'LABEL_2' in label:
                    sentiment = 'POSITIVE'
                elif 'NEGATIVE' in label.upper() or label in ['1', '2'] or 'LABEL_0' in label:
                    sentiment = 'NEGATIVE'
                else:
                    sentiment = 'NEUTRAL'
                
                return sentiment, score
            
            elif self.openai_client:
                # Use OpenAI as fallback
                return self._analyze_sentiment_openai(text)
            
            else:
                # Use rule-based analysis as final fallback
                return self._analyze_sentiment_rules(text)
                
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return self._analyze_sentiment_rules(text)
    
    def _analyze_sentiment_rules(self, text: str) -> Tuple[str, float]:
        """Rule-based sentiment analysis fallback"""
        text_lower = text.lower()
        
        # Positive keywords for financial news
        positive_words = [
            'profit', 'growth', 'gain', 'rise', 'up', 'increase', 'bullish', 'positive',
            'strong', 'beat', 'exceed', 'outperform', 'surge', 'rally', 'boom', 'recovery',
            'dividend', 'bonus', 'expansion', 'merger', 'acquisition', 'success', 'achieve'
        ]
        
        # Negative keywords for financial news
        negative_words = [
            'loss', 'decline', 'fall', 'down', 'decrease', 'bearish', 'negative', 'weak',
            'miss', 'fail', 'underperform', 'crash', 'drop', 'plunge', 'concern', 'worry',
            'debt', 'liability', 'penalty', 'investigation', 'fraud', 'scandal', 'crisis'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            confidence = min(positive_count / (positive_count + negative_count + 1), 0.8)
            return 'POSITIVE', confidence
        elif negative_count > positive_count:
            confidence = min(negative_count / (positive_count + negative_count + 1), 0.8)
            return 'NEGATIVE', confidence
        else:
            return 'NEUTRAL', 0.5

    def _analyze_sentiment_openai(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment using OpenAI"""
        try:
            prompt = f"""
            Analyze the sentiment of this Indian stock market news article:
            
            "{text[:1000]}"
            
            Respond with only a JSON object:
            {{"sentiment": "POSITIVE/NEGATIVE/NEUTRAL", "confidence": 0.0-1.0}}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            return result['sentiment'], result['confidence']
            
        except Exception as e:
            logger.error(f"Error in OpenAI sentiment analysis: {str(e)}")
            return 'NEUTRAL', 0.5
    
    def categorize_news(self, title: str, content: str) -> Tuple[str, float]:
        """
        Categorize news article based on content
        Returns: (category, confidence_score)
        """
        try:
            # Rule-based categorization with keywords
            text = f"{title} {content}".lower()
            
            category_keywords = {
                'EARNINGS': ['earnings', 'quarterly', 'profit', 'revenue', 'q1', 'q2', 'q3', 'q4', 'results'],
                'POLICY': ['policy', 'government', 'rbi', 'sebi', 'ministry', 'budget', 'tax', 'regulation'],
                'IPO': ['ipo', 'listing', 'debut', 'public issue', 'share sale', 'allotment'],
                'MERGER': ['merger', 'acquisition', 'takeover', 'deal', 'buyout', 'consolidation'],
                'GLOBAL': ['global', 'international', 'us', 'china', 'fed', 'dollar', 'crude oil'],
                'COMMODITY': ['gold', 'silver', 'crude', 'oil', 'commodity', 'metal'],
                'CURRENCY': ['rupee', 'dollar', 'currency', 'forex', 'exchange rate'],
                'REGULATORY': ['sebi', 'rbi', 'compliance', 'penalty', 'investigation', 'regulatory'],
                'MARKET_OPEN': ['pre-market', 'opening', 'early trade', 'morning trade'],
                'SECTOR': ['sector', 'industry', 'banking', 'pharma', 'it', 'auto', 'fmcg']
            }
            
            # Score each category
            category_scores = {}
            for category, keywords in category_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text)
                if score > 0:
                    category_scores[category] = score / len(keywords)
            
            if category_scores:
                best_category = max(category_scores.items(), key=lambda x: x[1])
                return best_category[0], min(best_category[1] * 2, 1.0)  # Scale confidence
            
            # Use OpenAI for complex categorization
            if self.openai_client:
                return self._categorize_news_openai(title, content)
            
            return 'OTHER', 0.5
            
        except Exception as e:
            logger.error(f"Error in news categorization: {str(e)}")
            return 'OTHER', 0.5
    
    def _categorize_news_openai(self, title: str, content: str) -> Tuple[str, float]:
        """Categorize news using OpenAI"""
        try:
            categories = [
                'MARKET_OPEN', 'EARNINGS', 'POLICY', 'GLOBAL', 'SECTOR', 
                'IPO', 'MERGER', 'COMMODITY', 'CURRENCY', 'REGULATORY', 'OTHER'
            ]
            
            prompt = f"""
            Categorize this Indian stock market news article into one of these categories:
            {', '.join(categories)}
            
            Title: "{title}"
            Content: "{content[:500]}"
            
            Respond with only a JSON object:
            {{"category": "CATEGORY_NAME", "confidence": 0.0-1.0}}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            return result['category'], result['confidence']
            
        except Exception as e:
            logger.error(f"Error in OpenAI categorization: {str(e)}")
            return 'OTHER', 0.5
    
    def assess_impact_level(self, title: str, content: str, mentioned_stocks: List[str]) -> Tuple[str, float]:
        """
        Assess the potential market impact of the news
        Returns: (impact_level, confidence_score)
        """
        try:
            text = f"{title} {content}".lower()
            impact_score = 0
            
            # High impact keywords
            high_impact_keywords = [
                'breaking', 'major', 'significant', 'massive', 'huge', 'unprecedented',
                'crisis', 'emergency', 'investigation', 'fraud', 'scandal', 'crash',
                'merger', 'acquisition', 'deal', 'ipo', 'listing'
            ]
            
            # Medium impact keywords
            medium_impact_keywords = [
                'growth', 'decline', 'increase', 'decrease', 'profit', 'loss',
                'quarterly', 'results', 'earnings', 'guidance', 'outlook'
            ]
            
            # Calculate impact score
            for keyword in high_impact_keywords:
                if keyword in text:
                    impact_score += 3
            
            for keyword in medium_impact_keywords:
                if keyword in text:
                    impact_score += 1
            
            # Bonus for major stocks
            major_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ITC']
            if any(stock in mentioned_stocks for stock in major_stocks):
                impact_score += 2
            
            # Multiple stock mentions
            if len(mentioned_stocks) > 3:
                impact_score += 1
            
            # Determine impact level
            if impact_score >= 5:
                return 'HIGH', min(impact_score / 10, 1.0)
            elif impact_score >= 2:
                return 'MEDIUM', min(impact_score / 7, 1.0)
            else:
                return 'LOW', max(impact_score / 5, 0.2)
                
        except Exception as e:
            logger.error(f"Error in impact assessment: {str(e)}")
            return 'LOW', 0.5
    
    def generate_summary(self, content: str) -> str:
        """Generate a concise summary of the news article"""
        try:
            if self.openai_client and len(content) > 200:
                prompt = f"""
                Summarize this Indian stock market news article in 2-3 sentences:
                
                "{content[:1000]}"
                
                Focus on the key financial implications and market impact.
                """
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.3
                )
                
                return response.choices[0].message.content.strip()
            
            else:
                # Simple extractive summary - first two sentences
                sentences = content.split('. ')
                if len(sentences) >= 2:
                    return '. '.join(sentences[:2]) + '.'
                else:
                    return content[:200] + '...'
                    
        except Exception as e:
            logger.error(f"Error in summary generation: {str(e)}")
            return content[:200] + '...' if len(content) > 200 else content
    
    def analyze_article(self, title: str, content: str, mentioned_stocks: List[str]) -> Dict:
        """
        Complete analysis of a news article
        Returns dictionary with all analysis results
        """
        logger.info(f"Analyzing article: {title[:50]}...")
        
        try:
            # Sentiment analysis
            sentiment, sentiment_score = self.analyze_sentiment(f"{title} {content}")
            
            # Categorization
            category, category_confidence = self.categorize_news(title, content)
            
            # Impact assessment
            impact_level, impact_confidence = self.assess_impact_level(title, content, mentioned_stocks)
            
            # Generate summary
            summary = self.generate_summary(content)
            
            analysis_result = {
                'sentiment': sentiment,
                'sentiment_score': sentiment_score,
                'category': category,
                'category_confidence': category_confidence,
                'impact_level': impact_level,
                'impact_confidence': impact_confidence,
                'summary': summary,
                'confidence_score': (sentiment_score + category_confidence + impact_confidence) / 3,
                'analyzed_at': datetime.now()
            }
            
            logger.info(f"Analysis completed: {sentiment} sentiment, {category} category, {impact_level} impact")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in article analysis: {str(e)}")
            return {
                'sentiment': 'NEUTRAL',
                'sentiment_score': 0.5,
                'category': 'OTHER',
                'category_confidence': 0.5,
                'impact_level': 'LOW',
                'impact_confidence': 0.5,
                'summary': content[:200] + '...' if len(content) > 200 else content,
                'confidence_score': 0.5,
                'analyzed_at': datetime.now()
            }


class RecommendationEngine:
    """Generate stock recommendations based on news analysis"""
    
    def __init__(self):
        self.news_analyzer = NewsAnalyzer()
    
    def generate_stock_recommendations(self, analyzed_articles: List[Dict]) -> List[Dict]:
        """
        Generate stock recommendations based on analyzed news articles
        """
        logger.info("Generating stock recommendations...")
        
        # Group articles by mentioned stocks
        stock_news = {}
        for article in analyzed_articles:
            for stock in article.get('mentioned_stocks', []):
                if stock not in stock_news:
                    stock_news[stock] = []
                stock_news[stock].append(article)
        
        recommendations = []
        
        for stock_symbol, articles in stock_news.items():
            try:
                recommendation = self._analyze_stock_sentiment(stock_symbol, articles)
                if recommendation:
                    recommendations.append(recommendation)
            except Exception as e:
                logger.error(f"Error generating recommendation for {stock_symbol}: {str(e)}")
                continue
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    
    def _analyze_stock_sentiment(self, stock_symbol: str, articles: List[Dict]) -> Optional[Dict]:
        """Analyze overall sentiment for a specific stock"""
        if not articles:
            return None
        
        # Calculate weighted sentiment scores
        positive_weight = 0
        negative_weight = 0
        total_impact_weight = 0
        
        high_impact_articles = []
        key_factors = []
        
        for article in articles:
            sentiment = article.get('sentiment', 'NEUTRAL')
            sentiment_score = article.get('sentiment_score', 0.5)
            impact_level = article.get('impact_level', 'LOW')
            
            # Weight based on impact level
            weight = 1
            if impact_level == 'HIGH':
                weight = 3
                high_impact_articles.append(article)
            elif impact_level == 'MEDIUM':
                weight = 2
            
            total_impact_weight += weight
            
            if sentiment == 'POSITIVE':
                positive_weight += weight * sentiment_score
            elif sentiment == 'NEGATIVE':
                negative_weight += weight * sentiment_score
            
            # Extract key factors
            category = article.get('category', 'OTHER')
            if category not in ['OTHER']:
                key_factors.append(category)
        
        if total_impact_weight == 0:
            return None
        
        # Calculate overall sentiment score
        net_sentiment = (positive_weight - negative_weight) / total_impact_weight
        
        # Determine recommendation
        recommendation_type = 'HOLD'  # Default
        risk_level = 'MEDIUM'
        confidence = 50
        
        if net_sentiment > 0.3:
            recommendation_type = 'BUY' if net_sentiment > 0.6 else 'WATCH'
            risk_level = 'LOW' if net_sentiment > 0.7 else 'MEDIUM'
            confidence = min(80 + net_sentiment * 20, 95)
        elif net_sentiment < -0.3:
            recommendation_type = 'SELL'
            risk_level = 'HIGH'
            confidence = min(70 + abs(net_sentiment) * 20, 90)
        else:
            confidence = 40 + abs(net_sentiment) * 20
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            stock_symbol, recommendation_type, articles, net_sentiment
        )
        
        return {
            'stock_symbol': stock_symbol,
            'recommendation': recommendation_type,
            'risk_level': risk_level,
            'confidence_level': confidence,
            'reasoning': reasoning,
            'key_factors': list(set(key_factors)),
            'related_articles': [article.get('id') for article in articles if article.get('id')],
            'net_sentiment_score': net_sentiment,
            'total_articles': len(articles),
            'high_impact_articles': len(high_impact_articles)
        }
    
    def _generate_reasoning(self, stock_symbol: str, recommendation: str, articles: List[Dict], net_sentiment: float) -> str:
        """Generate human-readable reasoning for the recommendation"""
        article_count = len(articles)
        positive_count = sum(1 for a in articles if a.get('sentiment') == 'POSITIVE')
        negative_count = sum(1 for a in articles if a.get('sentiment') == 'NEGATIVE')
        
        sentiment_desc = "positive" if net_sentiment > 0 else "negative" if net_sentiment < 0 else "mixed"
        
        reasoning_parts = [
            f"Based on analysis of {article_count} news articles about {stock_symbol}.",
            f"Overall sentiment is {sentiment_desc} with {positive_count} positive and {negative_count} negative articles.",
        ]
        
        if recommendation == 'BUY':
            reasoning_parts.append("Strong positive news flow suggests potential upward movement.")
        elif recommendation == 'SELL':
            reasoning_parts.append("Negative news sentiment indicates potential downside risk.")
        elif recommendation == 'WATCH':
            reasoning_parts.append("Moderate positive sentiment warrants close monitoring.")
        else:  # HOLD
            reasoning_parts.append("Mixed sentiment suggests maintaining current position.")
        
        # Add category-specific insights
        categories = [a.get('category') for a in articles if a.get('category')]
        if 'EARNINGS' in categories:
            reasoning_parts.append("Earnings-related news is a key factor.")
        if 'POLICY' in categories:
            reasoning_parts.append("Policy developments may impact the stock.")
        
        return " ".join(reasoning_parts)