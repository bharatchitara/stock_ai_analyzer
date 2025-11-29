"""
Management command to update stock prices
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import Stock
from portfolio.stock_fetcher import StockPriceFetcher


class Command(BaseCommand):
    help = 'Update current prices for all stocks in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            nargs='+',
            type=str,
            help='Specific stock symbols to update (space-separated)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Update all stocks in database',
        )

    def handle(self, *args, **options):
        fetcher = StockPriceFetcher()
        
        # Determine which stocks to update
        if options['symbols']:
            stocks = Stock.objects.filter(symbol__in=options['symbols'])
            self.stdout.write(f"Updating prices for {len(options['symbols'])} specified stocks...")
        elif options['all']:
            stocks = Stock.objects.all()
            self.stdout.write(f"Updating prices for all {stocks.count()} stocks...")
        else:
            # Default: update only stocks in portfolios
            from news.models import PortfolioHolding
            stock_ids = PortfolioHolding.objects.values_list('stock_id', flat=True).distinct()
            stocks = Stock.objects.filter(id__in=stock_ids)
            self.stdout.write(f"Updating prices for {stocks.count()} stocks in portfolios...")
        
        if not stocks.exists():
            self.stdout.write(self.style.WARNING('No stocks found to update'))
            return
        
        # Update prices
        result = fetcher.update_stock_prices(stocks)
        
        # Display results
        self.stdout.write(self.style.SUCCESS(f"\nPrice Update Summary:"))
        self.stdout.write(f"  ✓ Successfully updated: {result['updated']} stocks")
        self.stdout.write(f"  ✗ Failed to fetch: {result['failed']} stocks")
        self.stdout.write(f"  Total processed: {result['total']} stocks")
        
        # Show updated stocks with prices
        if result['updated'] > 0:
            self.stdout.write(self.style.SUCCESS(f"\nUpdated Stock Prices:"))
            for stock in stocks.filter(current_price__isnull=False).order_by('symbol'):
                self.stdout.write(
                    f"  {stock.symbol:15} → ₹{stock.current_price:>10.2f} "
                    f"(updated: {stock.price_updated_at.strftime('%Y-%m-%d %H:%M:%S')})"
                )
