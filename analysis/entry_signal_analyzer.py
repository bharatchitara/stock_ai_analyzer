"""
Entry signal analyzer for detecting buy opportunities
"""
from django.utils import timezone
from django.db.models import Q, Avg
from datetime import timedelta, date
from decimal import Decimal
import logging

from news.models import Stock, NewsArticle
from portfolio.models import PromoterHolding, CorporateAction, EntryOpportunity

logger = logging.getLogger(__name__)


class EntrySignalAnalyzer:
    """Analyzes entry signals for stock buying opportunities"""
    
    def __init__(self):
        self.today = timezone.now().date()
    
    def detect_price_dips(self, dip_threshold=5.0, days_lookback=7):
        """
        Detect stocks with significant price dips in recent trading days
        
        Args:
            dip_threshold: Minimum percentage dip (default 5%)
            days_lookback: Days to look back (default 7)
        
        Returns:
            List of EntryOpportunity objects
        """
        opportunities = []
        cutoff_date = self.today - timedelta(days=days_lookback)
        
        # Get stocks with recent price data
        stocks = Stock.objects.filter(
            current_price__isnull=False,
            price_updated_at__gte=cutoff_date
        )
        
        for stock in stocks:
            # For now, we'll check if there's negative news or if we can calculate from historical data
            # This is a placeholder - in production you'd fetch historical prices from an API
            
            # Check if there's recent negative news indicating a dip
            negative_news = NewsArticle.objects.filter(
                mentioned_stocks=stock,
                sentiment='NEGATIVE',
                published_at__gte=timezone.now() - timedelta(days=days_lookback)
            ).count()
            
            if negative_news >= 2:  # At least 2 negative news articles
                # Calculate approximate dip (placeholder logic)
                estimated_dip = min(negative_news * 2.5, 10)  # Max 10%
                
                if estimated_dip >= dip_threshold:
                    signal_strength = 'STRONG' if estimated_dip >= 7 else 'MODERATE'
                    
                    opportunity = EntryOpportunity(
                        stock=stock,
                        opportunity_type='PRICE_DIP',
                        signal_date=self.today,
                        signal_strength=signal_strength,
                        price_at_signal=stock.current_price,
                        percentage_change=Decimal(str(-estimated_dip)),
                        description=f"Stock dipped approximately {estimated_dip:.1f}% in last {days_lookback} days due to negative news. Good entry opportunity for long-term investors.",
                        expires_at=self.today + timedelta(days=7)
                    )
                    opportunities.append(opportunity)
        
        return opportunities
    
    def detect_new_orders(self, days_lookback=30):
        """
        Detect stocks with new order wins or contract announcements
        
        Args:
            days_lookback: Days to look back (default 30)
        
        Returns:
            List of EntryOpportunity objects
        """
        opportunities = []
        cutoff_date = timezone.now() - timedelta(days=days_lookback)
        
        # Search for news mentioning orders, contracts, wins
        order_keywords = ['order', 'contract', 'won', 'awarded', 'bagged', 'deal']
        
        news_articles = NewsArticle.objects.filter(
            published_at__gte=cutoff_date,
            sentiment__in=['POSITIVE', 'NEUTRAL']
        )
        
        for article in news_articles:
            title_lower = article.title.lower()
            content_lower = article.content.lower()
            
            # Check if article mentions orders/contracts
            if any(keyword in title_lower or keyword in content_lower for keyword in order_keywords):
                for stock in article.mentioned_stocks.all():
                    # Check if we already have this signal
                    existing = EntryOpportunity.objects.filter(
                        stock=stock,
                        opportunity_type='ORDER_WIN',
                        signal_date__gte=self.today - timedelta(days=7)
                    ).exists()
                    
                    if not existing:
                        signal_strength = 'STRONG' if 'major' in title_lower or 'significant' in title_lower else 'MODERATE'
                        
                        opportunity = EntryOpportunity(
                            stock=stock,
                            opportunity_type='ORDER_WIN',
                            signal_date=article.published_at.date(),
                            signal_strength=signal_strength,
                            price_at_signal=stock.current_price,
                            description=f"New order/contract win: {article.title[:200]}",
                            expires_at=self.today + timedelta(days=14)
                        )
                        opportunities.append(opportunity)
        
        return opportunities
    
    def detect_dividend_announcements(self, days_lookback=30):
        """
        Detect stocks with high dividend announcements
        
        Args:
            days_lookback: Days to look back (default 30)
        
        Returns:
            List of EntryOpportunity objects
        """
        opportunities = []
        cutoff_date = self.today - timedelta(days=days_lookback)
        
        # Get dividend corporate actions
        dividend_actions = CorporateAction.objects.filter(
            action_type='DIVIDEND',
            announcement_date__gte=cutoff_date
        ).select_related('stock')
        
        for action in dividend_actions:
            # Check if we already have this signal
            existing = EntryOpportunity.objects.filter(
                stock=action.stock,
                opportunity_type='DIVIDEND',
                signal_date=action.announcement_date
            ).exists()
            
            if not existing:
                # Determine strength based on dividend amount
                dividend_amount = action.dividend_amount or 0
                signal_strength = 'STRONG' if dividend_amount > 10 else 'MODERATE' if dividend_amount > 5 else 'WEAK'
                
                opportunity = EntryOpportunity(
                    stock=action.stock,
                    opportunity_type='DIVIDEND',
                    signal_date=action.announcement_date,
                    signal_strength=signal_strength,
                    price_at_signal=action.stock.current_price,
                    description=f"Dividend announced: ₹{dividend_amount}/share. Ex-date: {action.ex_date}",
                    expires_at=action.ex_date if action.ex_date else self.today + timedelta(days=30)
                )
                opportunities.append(opportunity)
        
        return opportunities
    
    def detect_expansion_news(self, days_lookback=30):
        """
        Detect stocks with expansion or acquisition news
        
        Args:
            days_lookback: Days to look back (default 30)
        
        Returns:
            List of EntryOpportunity objects
        """
        opportunities = []
        cutoff_date = timezone.now() - timedelta(days=days_lookback)
        
        # Search for expansion/acquisition news
        expansion_keywords = ['expansion', 'acquisition', 'merger', 'takeover', 'plant', 'facility', 'capacity', 'subsidiary']
        
        news_articles = NewsArticle.objects.filter(
            published_at__gte=cutoff_date,
            sentiment='POSITIVE',
            category__name__in=['MERGER', 'SECTOR', 'EARNINGS']
        )
        
        for article in news_articles:
            title_lower = article.title.lower()
            content_lower = article.content.lower()
            
            # Check if article mentions expansion/acquisition
            if any(keyword in title_lower or keyword in content_lower for keyword in expansion_keywords):
                for stock in article.mentioned_stocks.all():
                    # Check if we already have this signal
                    existing = EntryOpportunity.objects.filter(
                        stock=stock,
                        opportunity_type='EXPANSION',
                        signal_date__gte=self.today - timedelta(days=7)
                    ).exists()
                    
                    if not existing:
                        signal_strength = 'STRONG' if any(word in title_lower for word in ['major', 'significant', 'massive']) else 'MODERATE'
                        
                        opportunity = EntryOpportunity(
                            stock=stock,
                            opportunity_type='EXPANSION',
                            signal_date=article.published_at.date(),
                            signal_strength=signal_strength,
                            price_at_signal=stock.current_price,
                            description=f"Expansion/Acquisition: {article.title[:200]}",
                            expires_at=self.today + timedelta(days=30)
                        )
                        opportunities.append(opportunity)
        
        return opportunities
    
    def detect_stock_splits(self, days_lookback=60):
        """
        Detect stock split announcements
        
        Args:
            days_lookback: Days to look back (default 60)
        
        Returns:
            List of EntryOpportunity objects
        """
        opportunities = []
        cutoff_date = self.today - timedelta(days=days_lookback)
        
        # Get stock split corporate actions
        split_actions = CorporateAction.objects.filter(
            action_type='SPLIT',
            announcement_date__gte=cutoff_date
        ).select_related('stock')
        
        for action in split_actions:
            # Check if we already have this signal
            existing = EntryOpportunity.objects.filter(
                stock=action.stock,
                opportunity_type='SPLIT',
                signal_date=action.announcement_date
            ).exists()
            
            if not existing:
                opportunity = EntryOpportunity(
                    stock=action.stock,
                    opportunity_type='SPLIT',
                    signal_date=action.announcement_date,
                    signal_strength='STRONG',
                    price_at_signal=action.stock.current_price,
                    description=f"Stock split announced: {action.split_ratio}. Record date: {action.record_date}",
                    expires_at=action.record_date if action.record_date else self.today + timedelta(days=45)
                )
                opportunities.append(opportunity)
        
        return opportunities
    
    def detect_bonus_issues(self, days_lookback=60):
        """
        Detect bonus share announcements
        
        Args:
            days_lookback: Days to look back (default 60)
        
        Returns:
            List of EntryOpportunity objects
        """
        opportunities = []
        cutoff_date = self.today - timedelta(days=days_lookback)
        
        # Get bonus issue corporate actions
        bonus_actions = CorporateAction.objects.filter(
            action_type='BONUS',
            announcement_date__gte=cutoff_date
        ).select_related('stock')
        
        for action in bonus_actions:
            # Check if we already have this signal
            existing = EntryOpportunity.objects.filter(
                stock=action.stock,
                opportunity_type='BONUS',
                signal_date=action.announcement_date
            ).exists()
            
            if not existing:
                opportunity = EntryOpportunity(
                    stock=action.stock,
                    opportunity_type='BONUS',
                    signal_date=action.announcement_date,
                    signal_strength='STRONG',
                    price_at_signal=action.stock.current_price,
                    description=f"Bonus shares announced: {action.bonus_ratio}. Record date: {action.record_date}",
                    expires_at=action.record_date if action.record_date else self.today + timedelta(days=45)
                )
                opportunities.append(opportunity)
        
        return opportunities
    
    def generate_all_entry_signals(self):
        """
        Generate all types of entry signals
        
        Returns:
            Dict with counts of each signal type created
        """
        logger.info("Starting entry signal generation...")
        
        results = {
            'price_dips': 0,
            'order_wins': 0,
            'dividends': 0,
            'expansions': 0,
            'splits': 0,
            'bonuses': 0,
            'total': 0
        }
        
        # Detect all signal types
        all_opportunities = []
        
        all_opportunities.extend(self.detect_price_dips())
        all_opportunities.extend(self.detect_new_orders())
        all_opportunities.extend(self.detect_dividend_announcements())
        all_opportunities.extend(self.detect_expansion_news())
        all_opportunities.extend(self.detect_stock_splits())
        all_opportunities.extend(self.detect_bonus_issues())
        
        # Save all opportunities
        for opp in all_opportunities:
            try:
                opp.save()
                results[self._get_result_key(opp.opportunity_type)] += 1
                results['total'] += 1
            except Exception as e:
                logger.error(f"Error saving entry opportunity: {e}")
        
        # Deactivate expired signals
        expired_count = EntryOpportunity.objects.filter(
            expires_at__lt=self.today,
            is_active=True
        ).update(is_active=False)
        
        logger.info(f"Entry signals generated: {results['total']} new, {expired_count} expired")
        return results
    
    def _get_result_key(self, opportunity_type):
        """Map opportunity type to result key"""
        mapping = {
            'PRICE_DIP': 'price_dips',
            'ORDER_WIN': 'order_wins',
            'DIVIDEND': 'dividends',
            'EXPANSION': 'expansions',
            'SPLIT': 'splits',
            'BONUS': 'bonuses',
        }
        return mapping.get(opportunity_type, 'total')
    
    def get_active_opportunities(self, stock=None, opportunity_type=None):
        """
        Get active entry opportunities
        
        Args:
            stock: Filter by stock (optional)
            opportunity_type: Filter by type (optional)
        
        Returns:
            QuerySet of active EntryOpportunity objects
        """
        queryset = EntryOpportunity.objects.filter(
            is_active=True,
            expires_at__gte=self.today
        ).select_related('stock').order_by('-signal_strength', '-signal_date')
        
        if stock:
            queryset = queryset.filter(stock=stock)
        
        if opportunity_type:
            queryset = queryset.filter(opportunity_type=opportunity_type)
        
        return queryset
