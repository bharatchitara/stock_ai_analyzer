"""
Admin interface for portfolio models
"""
from django.contrib import admin
from .models import (
    Portfolio, Holding, InsiderTrade, BulkDeal, BlockDeal,
    CorporateAction, PromoterHolding, ShareholdingPattern, EntryOpportunity
)


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'is_active', 'total_value', 'total_pnl']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    
    def total_value(self, obj):
        return f"₹{obj.total_value():,.2f}"
    total_value.short_description = 'Total Value'
    
    def total_pnl(self, obj):
        pnl = obj.total_pnl()
        color = 'green' if pnl >= 0 else 'red'
        return f'<span style="color: {color}">₹{pnl:,.2f}</span>'
    total_pnl.short_description = 'P&L'
    total_pnl.allow_tags = True


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ['stock', 'portfolio', 'quantity', 'avg_price', 'current_value', 'pnl_display', 'updated_at']
    list_filter = ['portfolio', 'stock__sector', 'purchase_date']
    search_fields = ['stock__symbol', 'stock__company_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def current_value(self, obj):
        return f"₹{obj.current_value():,.2f}"
    current_value.short_description = 'Current Value'
    
    def pnl_display(self, obj):
        pnl = obj.pnl()
        pnl_pct = obj.pnl_percentage()
        color = 'green' if pnl >= 0 else 'red'
        return f'<span style="color: {color}">₹{pnl:,.2f} ({pnl_pct:.2f}%)</span>'
    pnl_display.short_description = 'P&L'
    pnl_display.allow_tags = True


@admin.register(InsiderTrade)
class InsiderTradeAdmin(admin.ModelAdmin):
    list_display = ['stock', 'insider_name', 'transaction_type', 'quantity', 'transaction_date', 'exchange']
    list_filter = ['transaction_type', 'exchange', 'transaction_date', 'stock__sector']
    search_fields = ['stock__symbol', 'insider_name', 'insider_designation']
    date_hierarchy = 'transaction_date'
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Stock Information', {
            'fields': ('stock', 'exchange')
        }),
        ('Insider Details', {
            'fields': ('insider_name', 'insider_designation')
        }),
        ('Transaction Details', {
            'fields': ('transaction_type', 'quantity', 'price_per_share', 'total_value')
        }),
        ('Dates', {
            'fields': ('transaction_date', 'intimation_date')
        }),
        ('Additional Info', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )


@admin.register(BulkDeal)
class BulkDealAdmin(admin.ModelAdmin):
    list_display = ['stock', 'client_name', 'deal_type', 'quantity', 'price_per_share', 'total_value', 'deal_date']
    list_filter = ['deal_type', 'exchange', 'deal_date', 'stock__sector']
    search_fields = ['stock__symbol', 'client_name']
    date_hierarchy = 'deal_date'
    readonly_fields = ['created_at']


@admin.register(BlockDeal)
class BlockDealAdmin(admin.ModelAdmin):
    list_display = ['stock', 'client_name', 'deal_type', 'quantity', 'price_per_share', 'total_value', 'deal_date']
    list_filter = ['deal_type', 'exchange', 'deal_date', 'stock__sector']
    search_fields = ['stock__symbol', 'client_name']
    date_hierarchy = 'deal_date'
    readonly_fields = ['created_at']


@admin.register(CorporateAction)
class CorporateActionAdmin(admin.ModelAdmin):
    list_display = ['stock', 'action_type', 'ex_date', 'announcement_date', 'get_details']
    list_filter = ['action_type', 'ex_date', 'stock__sector']
    search_fields = ['stock__symbol', 'description']
    date_hierarchy = 'ex_date'
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('stock', 'action_type', 'description')
        }),
        ('Important Dates', {
            'fields': ('ex_date', 'record_date', 'payment_date', 'announcement_date')
        }),
        ('Action Details', {
            'fields': ('dividend_amount', 'bonus_ratio', 'split_ratio', 'rights_ratio', 'rights_price')
        }),
        ('Additional Info', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )
    
    def get_details(self, obj):
        if obj.action_type == 'DIVIDEND' and obj.dividend_amount:
            return f"₹{obj.dividend_amount}"
        elif obj.action_type == 'BONUS' and obj.bonus_ratio:
            return obj.bonus_ratio
        elif obj.action_type == 'SPLIT' and obj.split_ratio:
            return obj.split_ratio
        return "-"
    get_details.short_description = 'Details'


@admin.register(PromoterHolding)
class PromoterHoldingAdmin(admin.ModelAdmin):
    list_display = ['stock', 'quarter_end_date', 'promoter_holding', 'promoter_pledged', 'public_holding', 'get_change']
    list_filter = ['quarter_end_date', 'stock__sector']
    search_fields = ['stock__symbol']
    date_hierarchy = 'quarter_end_date'
    readonly_fields = ['created_at', 'updated_at']
    
    def get_change(self, obj):
        change = obj.promoter_change()
        if change > 0:
            return f'<span style="color: green">+{change:.2f}%</span>'
        elif change < 0:
            return f'<span style="color: red">{change:.2f}%</span>'
        return "0.00%"
    get_change.short_description = 'QoQ Change'
    get_change.allow_tags = True


@admin.register(ShareholdingPattern)
class ShareholdingPatternAdmin(admin.ModelAdmin):
    list_display = ['stock', 'quarter_end_date', 'indian_promoters', 'foreign_promoters', 'fii', 'dii', 'retail_investors']
    list_filter = ['quarter_end_date', 'stock__sector']
    search_fields = ['stock__symbol']
    date_hierarchy = 'quarter_end_date'
    readonly_fields = ['created_at']


@admin.register(EntryOpportunity)
class EntryOpportunityAdmin(admin.ModelAdmin):
    list_display = ['stock', 'opportunity_type', 'signal_strength', 'signal_date', 'price_at_signal', 'percentage_change', 'is_active', 'expires_at']
    list_filter = ['opportunity_type', 'signal_strength', 'is_active', 'signal_date']
    search_fields = ['stock__symbol', 'stock__company_name', 'description']
    date_hierarchy = 'signal_date'
    readonly_fields = ['created_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Stock Information', {
            'fields': ('stock', 'opportunity_type', 'signal_strength')
        }),
        ('Signal Details', {
            'fields': ('signal_date', 'price_at_signal', 'percentage_change', 'description')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at', 'created_at')
        }),
    )
