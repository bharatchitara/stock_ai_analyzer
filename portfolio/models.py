"""
Portfolio models for tracking holdings and related stock events
"""
from django.db import models
from django.utils import timezone


class Portfolio(models.Model):
    """User's portfolio containing multiple holdings"""
    name = models.CharField(max_length=200, default="My Portfolio")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def total_value(self):
        """Calculate total portfolio value"""
        return sum(holding.current_value() for holding in self.holdings.all())
    
    def total_investment(self):
        """Calculate total investment"""
        return sum(holding.total_investment() for holding in self.holdings.all())
    
    def total_pnl(self):
        """Calculate total profit/loss"""
        return self.total_value() - self.total_investment()


class Holding(models.Model):
    """Individual stock holding in a portfolio"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey('news.Stock', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['portfolio', 'stock']
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.quantity} shares"
    
    def total_investment(self):
        """Calculate total investment amount"""
        return float(self.quantity * self.avg_price)
    
    def current_value(self):
        """Calculate current market value"""
        if self.stock.current_price:
            return float(self.quantity * self.stock.current_price)
        return self.total_investment()
    
    def pnl(self):
        """Calculate profit/loss"""
        return self.current_value() - self.total_investment()
    
    def pnl_percentage(self):
        """Calculate profit/loss percentage"""
        investment = self.total_investment()
        if investment > 0:
            return (self.pnl() / investment) * 100
        return 0


class InsiderTrade(models.Model):
    """Insider trading information"""
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('PLEDGE', 'Pledge'),
        ('REVOKE', 'Revoke Pledge'),
    ]
    
    stock = models.ForeignKey('news.Stock', on_delete=models.CASCADE, related_name='insider_trades')
    insider_name = models.CharField(max_length=200)
    insider_designation = models.CharField(max_length=200)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.BigIntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    transaction_date = models.DateField()
    intimation_date = models.DateField()
    exchange = models.CharField(max_length=10, default='NSE')  # NSE/BSE
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date', '-intimation_date']
        indexes = [
            models.Index(fields=['stock', '-transaction_date']),
            models.Index(fields=['-transaction_date']),
        ]
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.insider_name} {self.transaction_type} {self.quantity}"


class BulkDeal(models.Model):
    """Bulk deal transactions (>0.5% of equity)"""
    DEAL_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    stock = models.ForeignKey('news.Stock', on_delete=models.CASCADE, related_name='bulk_deals')
    client_name = models.CharField(max_length=200)
    deal_type = models.CharField(max_length=10, choices=DEAL_TYPES)
    quantity = models.BigIntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    deal_date = models.DateField()
    exchange = models.CharField(max_length=10, default='NSE')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-deal_date']
        indexes = [
            models.Index(fields=['stock', '-deal_date']),
            models.Index(fields=['-deal_date']),
        ]
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.client_name} {self.deal_type} {self.quantity}"


class BlockDeal(models.Model):
    """Block deal transactions (>10,000 shares or >Rs 10 crore)"""
    DEAL_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    stock = models.ForeignKey('news.Stock', on_delete=models.CASCADE, related_name='block_deals')
    client_name = models.CharField(max_length=200)
    deal_type = models.CharField(max_length=10, choices=DEAL_TYPES)
    quantity = models.BigIntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    deal_date = models.DateField()
    exchange = models.CharField(max_length=10, default='NSE')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-deal_date']
        indexes = [
            models.Index(fields=['stock', '-deal_date']),
            models.Index(fields=['-deal_date']),
        ]
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.client_name} {self.deal_type} {self.quantity}"


class CorporateAction(models.Model):
    """Corporate actions like dividends, bonuses, splits, etc."""
    ACTION_TYPES = [
        ('DIVIDEND', 'Dividend'),
        ('BONUS', 'Bonus Issue'),
        ('SPLIT', 'Stock Split'),
        ('RIGHTS', 'Rights Issue'),
        ('BUYBACK', 'Buyback'),
        ('MERGER', 'Merger/Amalgamation'),
        ('DELISTING', 'Delisting'),
        ('AGM', 'Annual General Meeting'),
        ('EGM', 'Extraordinary General Meeting'),
    ]
    
    stock = models.ForeignKey('news.Stock', on_delete=models.CASCADE, related_name='corporate_actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    ex_date = models.DateField(null=True, blank=True)
    record_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    announcement_date = models.DateField()
    
    # Specific fields for different action types
    dividend_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bonus_ratio = models.CharField(max_length=20, blank=True)  # e.g., "1:2" means 1 bonus for 2 held
    split_ratio = models.CharField(max_length=20, blank=True)  # e.g., "1:10" means 1 split into 10
    rights_ratio = models.CharField(max_length=20, blank=True)
    rights_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-ex_date', '-announcement_date']
        indexes = [
            models.Index(fields=['stock', '-ex_date']),
            models.Index(fields=['-ex_date']),
            models.Index(fields=['action_type']),
        ]
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.get_action_type_display()} - {self.ex_date or self.announcement_date}"


class PromoterHolding(models.Model):
    """Promoter shareholding pattern over time"""
    stock = models.ForeignKey('news.Stock', on_delete=models.CASCADE, related_name='promoter_holdings')
    quarter_end_date = models.DateField()
    
    # Promoter holding percentages
    promoter_holding = models.DecimalField(max_digits=5, decimal_places=2)
    promoter_pledged = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Public holding
    public_holding = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Institutional holdings
    fii_holding = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dii_holding = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Number of shareholders
    total_shareholders = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-quarter_end_date']
        unique_together = ['stock', 'quarter_end_date']
        indexes = [
            models.Index(fields=['stock', '-quarter_end_date']),
            models.Index(fields=['-quarter_end_date']),
        ]
    
    def __str__(self):
        return f"{self.stock.symbol} - Q{self.quarter_end_date} - Promoter: {self.promoter_holding}%"
    
    def promoter_change(self):
        """Calculate change from previous quarter"""
        previous = PromoterHolding.objects.filter(
            stock=self.stock,
            quarter_end_date__lt=self.quarter_end_date
        ).first()
        
        if previous:
            return float(self.promoter_holding - previous.promoter_holding)
        return 0


class ShareholdingPattern(models.Model):
    """Detailed shareholding pattern by category"""
    stock = models.ForeignKey('news.Stock', on_delete=models.CASCADE, related_name='shareholding_patterns')
    quarter_end_date = models.DateField()
    
    # Promoter categories
    indian_promoters = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    foreign_promoters = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Public categories
    retail_investors = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    others = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Institutional
    mutual_funds = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    banks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    insurance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fii = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    dii = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-quarter_end_date']
        unique_together = ['stock', 'quarter_end_date']
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.quarter_end_date} - Shareholding Pattern"


class EntryOpportunity(models.Model):
    """Entry signals for buying stocks"""
    OPPORTUNITY_TYPES = [
        ('PRICE_DIP', 'Price Dip'),
        ('ORDER_WIN', 'New Order'),
        ('DIVIDEND', 'Dividend Announcement'),
        ('EXPANSION', 'Expansion/Acquisition'),
        ('SPLIT', 'Stock Split'),
        ('BONUS', 'Bonus Issue'),
    ]
    
    SIGNAL_STRENGTH = [
        ('STRONG', 'Strong'),
        ('MODERATE', 'Moderate'),
        ('WEAK', 'Weak'),
    ]
    
    stock = models.ForeignKey('news.Stock', on_delete=models.CASCADE, related_name='entry_opportunities')
    opportunity_type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPES)
    signal_date = models.DateField()
    signal_strength = models.CharField(max_length=10, choices=SIGNAL_STRENGTH, default='MODERATE')
    price_at_signal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percentage_change = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    expires_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-signal_date', '-signal_strength']
        verbose_name_plural = 'Entry Opportunities'
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.get_opportunity_type_display()} ({self.signal_strength})"
