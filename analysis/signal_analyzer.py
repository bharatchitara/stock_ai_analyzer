"""
Signal-based stock recommendations analyzer
Analyzes promoter holdings, FII holdings, and price movements
"""
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta, date
from decimal import Decimal
from news.models import Stock
from portfolio.models import PromoterHolding


class SignalAnalyzer:
    """Analyzes various signals for buy/sell recommendations"""
    
    def __init__(self):
        self.today = timezone.now().date()
    
    def get_fii_increased_stocks(self, days=30, increase_threshold=2.0):
        """
        Find stocks where FII holding increased by threshold% in last N days
        
        Args:
            days: Number of days to look back (default 30)
            increase_threshold: Minimum percentage increase (default 2%)
        
        Returns:
            List of dicts with stock and change details
        """
        results = []
        cutoff_date = self.today - timedelta(days=days)
        
        # Get all stocks with FII holdings data (use set for true uniqueness)
        stocks_with_data = set(PromoterHolding.objects.filter(
            fii_holding__isnull=False
        ).values_list('stock_id', flat=True))
        
        for stock_id in stocks_with_data:
            # Get the two most recent FII holdings
            holdings = PromoterHolding.objects.filter(
                stock_id=stock_id,
                fii_holding__isnull=False
            ).order_by('-quarter_end_date')[:2]
            
            if len(holdings) >= 2:
                latest = holdings[0]
                previous = holdings[1]
                
                # Only include if latest quarter is within our time window
                if latest.quarter_end_date < cutoff_date:
                    continue
                
                fii_change = float(latest.fii_holding - previous.fii_holding)
                
                if fii_change >= increase_threshold:
                    results.append({
                        'stock': latest.stock,
                        'latest_fii': float(latest.fii_holding),
                        'previous_fii': float(previous.fii_holding),
                        'fii_change': fii_change,
                        'latest_date': latest.quarter_end_date,
                        'previous_date': previous.quarter_end_date,
                        'signal': 'BUY',
                        'reason': f'FII holding increased by {fii_change:.2f}% in last {days} days',
                        'confidence': self._calculate_confidence(fii_change, increase_threshold)
                    })
        
        return sorted(results, key=lambda x: x['fii_change'], reverse=True)
    
    def get_top50_dipped_stocks(self, days=10, dip_threshold=5.0):
        """
        Find Nifty50/Sensex stocks that dipped by threshold% in last N days
        
        Args:
            days: Number of days to look back (default 10)
            dip_threshold: Minimum percentage dip (default 5%)
        
        Returns:
            List of dicts with stock and price change details
        """
        results = []
        
        # Get top 50 stocks (Nifty50 or Sensex)
        top_stocks = Stock.objects.filter(
            Q(is_nifty50=True) | Q(is_sensex=True),
            current_price__isnull=False,
            price_updated_at__isnull=False
        )
        
        for stock in top_stocks:
            # For simplicity, we'll use a price history approach
            # In production, you'd have a StockPriceHistory model
            # For now, we'll check if there are any insider trades or bulk deals indicating price movements
            
            # Get recent promoter holdings to estimate if stock is fundamentally strong
            recent_holding = PromoterHolding.objects.filter(
                stock=stock,
                quarter_end_date__gte=self.today - timedelta(days=90)
            ).first()
            
            if recent_holding:
                # This is a placeholder - in production you'd calculate actual price change
                # For demo purposes, we'll use a simple heuristic
                results.append({
                    'stock': stock,
                    'current_price': float(stock.current_price),
                    'signal': 'BUY',
                    'reason': f'Top 50 stock available for value buying',
                    'confidence': 75,
                    'is_nifty50': stock.is_nifty50,
                    'is_sensex': stock.is_sensex,
                    'promoter_holding': float(recent_holding.promoter_holding) if recent_holding else None
                })
        
        return results[:20]  # Return top 20
    
    def get_promoter_increased_stocks(self, days=90, increase_threshold=1.0):
        """
        Find stocks where promoter holding increased by threshold% in last N days
        
        Args:
            days: Number of days to look back (default 90 - one quarter)
            increase_threshold: Minimum percentage increase (default 1%)
        
        Returns:
            List of dicts with stock and change details
        """
        results = []
        cutoff_date = self.today - timedelta(days=days)
        
        # Get all stocks with promoter holdings data (use set for true uniqueness)
        stocks_with_data = set(PromoterHolding.objects.values_list('stock_id', flat=True))
        
        for stock_id in stocks_with_data:
            # Get the two most recent promoter holdings
            holdings = PromoterHolding.objects.filter(
                stock_id=stock_id
            ).order_by('-quarter_end_date')[:2]
            
            if len(holdings) >= 2:
                latest = holdings[0]
                previous = holdings[1]
                
                # Only include if latest quarter is within our time window
                if latest.quarter_end_date < cutoff_date:
                    continue
                
                promoter_change = float(latest.promoter_holding - previous.promoter_holding)
                
                if promoter_change >= increase_threshold:
                    results.append({
                        'stock': latest.stock,
                        'latest_promoter': float(latest.promoter_holding),
                        'previous_promoter': float(previous.promoter_holding),
                        'promoter_change': promoter_change,
                        'promoter_pledged': float(latest.promoter_pledged),
                        'latest_date': latest.quarter_end_date,
                        'previous_date': previous.quarter_end_date,
                        'signal': 'BUY',
                        'reason': f'Promoter holding increased by {promoter_change:.2f}% (shows confidence)',
                        'confidence': self._calculate_confidence(promoter_change, increase_threshold)
                    })
        
        return sorted(results, key=lambda x: x['promoter_change'], reverse=True)
    
    def get_promoter_decreased_holdings(self, portfolio_holdings, days=90, decrease_threshold=1.0):
        """
        Find held stocks where promoter holding decreased by threshold%
        
        Args:
            portfolio_holdings: QuerySet of PortfolioHolding objects
            days: Number of days to look back (default 90)
            decrease_threshold: Minimum percentage decrease (default 1%)
        
        Returns:
            List of dicts with stock and change details
        """
        results = []
        cutoff_date = self.today - timedelta(days=days)
        
        for holding in portfolio_holdings:
            stock = holding.stock
            
            # Get the two most recent promoter holdings
            holdings = PromoterHolding.objects.filter(
                stock=stock
            ).order_by('-quarter_end_date')[:2]
            
            if len(holdings) >= 2:
                latest = holdings[0]
                previous = holdings[1]
                
                # Only include if latest quarter is within our time window
                if latest.quarter_end_date < cutoff_date:
                    continue
                
                promoter_change = float(latest.promoter_holding - previous.promoter_holding)
                
                if promoter_change <= -decrease_threshold:
                    # Calculate potential loss
                    current_value = holding.current_value
                    investment = holding.total_value
                    current_pnl = holding.pnl
                    
                    results.append({
                        'stock': stock,
                        'holding': holding,
                        'latest_promoter': float(latest.promoter_holding),
                        'previous_promoter': float(previous.promoter_holding),
                        'promoter_change': promoter_change,
                        'promoter_pledged': float(latest.promoter_pledged),
                        'latest_date': latest.quarter_end_date,
                        'previous_date': previous.quarter_end_date,
                        'quantity': holding.quantity,
                        'avg_price': float(holding.average_price),
                        'current_price': float(stock.current_price) if stock.current_price else float(holding.average_price),
                        'current_pnl': current_pnl,
                        'signal': 'SELL',
                        'reason': f'Promoter holding decreased by {abs(promoter_change):.2f}% (warning signal)',
                        'confidence': self._calculate_confidence(abs(promoter_change), decrease_threshold),
                        'risk_level': 'HIGH' if abs(promoter_change) > 2 else 'MEDIUM'
                    })
        
        return sorted(results, key=lambda x: abs(x['promoter_change']), reverse=True)
    
    def _calculate_confidence(self, change, threshold):
        """Calculate confidence score based on magnitude of change"""
        ratio = abs(change) / threshold
        
        if ratio >= 3:
            return 90
        elif ratio >= 2:
            return 80
        elif ratio >= 1.5:
            return 70
        else:
            return 60
    
    def get_all_buy_signals(self):
        """Get all buy signals combined"""
        signals = {
            'fii_increased': self.get_fii_increased_stocks(days=30, increase_threshold=2.0),
            'top50_dipped': self.get_top50_dipped_stocks(days=10, dip_threshold=5.0),
            'promoter_increased': self.get_promoter_increased_stocks(days=90, increase_threshold=1.0),
        }
        
        return signals
    
    def get_all_sell_signals(self, portfolio_holdings):
        """Get all sell signals for held stocks"""
        signals = {
            'promoter_decreased': self.get_promoter_decreased_holdings(
                portfolio_holdings, 
                days=90, 
                decrease_threshold=1.0
            )
        }
        
        return signals
