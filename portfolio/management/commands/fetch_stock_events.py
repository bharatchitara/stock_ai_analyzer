"""
Management command to fetch stock events for portfolio holdings
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from portfolio.models import Holding, InsiderTrade, BulkDeal, BlockDeal, CorporateAction, PromoterHolding
from portfolio.stock_events_fetcher import StockEventFetcher
from news.models import Stock
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch stock events (insider trades, bulk deals, corporate actions, promoter holdings) for portfolio stocks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Fetch for specific stock symbol'
        )
        parser.add_argument(
            '--event-type',
            type=str,
            choices=['insider', 'bulk', 'block', 'corporate', 'promoter', 'all'],
            default='all',
            help='Type of event to fetch'
        )
        parser.add_argument(
            '--holdings-only',
            action='store_true',
            help='Fetch only for stocks in portfolio holdings'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to look back for trades'
        )

    def handle(self, *args, **options):
        symbol = options['symbol']
        event_type = options['event_type']
        holdings_only = options['holdings_only']
        days = options['days']
        
        fetcher = StockEventFetcher()
        
        # Determine which stocks to process
        if symbol:
            stocks = Stock.objects.filter(symbol=symbol)
            if not stocks.exists():
                self.stdout.write(self.style.ERROR(f'Stock {symbol} not found'))
                return
        elif holdings_only:
            # Get all unique stocks from holdings
            stock_ids = Holding.objects.values_list('stock_id', flat=True).distinct()
            stocks = Stock.objects.filter(id__in=stock_ids)
        else:
            # Get all active stocks
            stocks = Stock.objects.all()[:50]  # Limit to avoid rate limiting
        
        self.stdout.write(f'Processing {stocks.count()} stocks...')
        
        for stock in stocks:
            self.stdout.write(f'\nFetching events for {stock.symbol}...')
            
            try:
                # Fetch insider trades
                if event_type in ['insider', 'all']:
                    self._fetch_insider_trades(fetcher, stock, days)
                
                # Fetch bulk deals (last 7 days)
                if event_type in ['bulk', 'all']:
                    self._fetch_bulk_deals(fetcher, stock)
                
                # Fetch block deals (last 7 days)
                if event_type in ['block', 'all']:
                    self._fetch_block_deals(fetcher, stock)
                
                # Fetch corporate actions
                if event_type in ['corporate', 'all']:
                    self._fetch_corporate_actions(fetcher, stock)
                
                # Fetch promoter holdings
                if event_type in ['promoter', 'all']:
                    self._fetch_promoter_holdings(fetcher, stock)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {stock.symbol}: {str(e)}'))
                logger.error(f'Error processing {stock.symbol}: {str(e)}')
                continue
        
        self.stdout.write(self.style.SUCCESS('\n✅ Stock events fetch completed!'))
    
    def _fetch_insider_trades(self, fetcher, stock, days):
        """Fetch and save insider trades"""
        self.stdout.write(f'  📡 Fetching insider trades from NSE API...')
        trades = fetcher.fetch_insider_trades(stock.symbol, days)
        
        if not trades:
            self.stdout.write(f'  ℹ️  No insider trades found (or NSE API error)')
            return
        
        self.stdout.write(f'  📥 Retrieved {len(trades)} insider trades from NSE')
        
        saved_count = 0
        for trade_data in trades:
            try:
                # Check if trade already exists
                existing = InsiderTrade.objects.filter(
                    stock=stock,
                    insider_name=trade_data['insider_name'],
                    transaction_date=trade_data['transaction_date'],
                    quantity=trade_data['quantity']
                ).exists()
                
                if not existing:
                    InsiderTrade.objects.create(
                        stock=stock,
                        **trade_data
                    )
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error saving insider trade: {e}")
                continue
        
        if saved_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Saved {saved_count} new insider trades'))
        else:
            self.stdout.write(f'  ℹ️  All insider trades already in database')
    
    def _fetch_bulk_deals(self, fetcher, stock):
        """Fetch and save bulk deals for last 7 days"""
        self.stdout.write(f'  📡 Fetching bulk deals from NSE API (last 7 days)...')
        saved_count = 0
        found_count = 0
        
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            deals = fetcher.fetch_bulk_deals(stock.symbol, date)
            found_count += len(deals)
            
            for deal_data in deals:
                try:
                    existing = BulkDeal.objects.filter(
                        stock=stock,
                        client_name=deal_data['client_name'],
                        deal_date=deal_data['deal_date'],
                        quantity=deal_data['quantity']
                    ).exists()
                    
                    if not existing:
                        # Remove symbol from deal_data as it's not a field
                        deal_data.pop('symbol', None)
                        BulkDeal.objects.create(
                            stock=stock,
                            **deal_data
                        )
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving bulk deal: {e}")
                    continue
        
        if found_count > 0:
            self.stdout.write(f'  📥 Retrieved {found_count} bulk deals from NSE')
            if saved_count > 0:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Saved {saved_count} new bulk deals'))
            else:
                self.stdout.write(f'  ℹ️  All bulk deals already in database')
        else:
            self.stdout.write(f'  ℹ️  No bulk deals found in last 7 days (normal if no large trades)')
    
    def _fetch_block_deals(self, fetcher, stock):
        """Fetch and save block deals for last 7 days"""
        saved_count = 0
        
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            deals = fetcher.fetch_block_deals(stock.symbol, date)
            
            for deal_data in deals:
                try:
                    existing = BlockDeal.objects.filter(
                        stock=stock,
                        client_name=deal_data['client_name'],
                        deal_date=deal_data['deal_date'],
                        quantity=deal_data['quantity']
                    ).exists()
                    
                    if not existing:
                        deal_data.pop('symbol', None)
                        BlockDeal.objects.create(
                            stock=stock,
                            **deal_data
                        )
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving block deal: {e}")
                    continue
        
        if saved_count > 0:
            self.stdout.write(f'  ✅ Saved {saved_count} block deals')
    
    def _fetch_corporate_actions(self, fetcher, stock):
        """Fetch and save corporate actions"""
        self.stdout.write(f'  📡 Fetching corporate actions from NSE API...')
        actions = fetcher.fetch_corporate_actions(stock.symbol)
        
        if not actions:
            self.stdout.write(f'  ℹ️  No corporate actions found')
            return
        
        self.stdout.write(f'  📥 Retrieved {len(actions)} corporate actions from NSE')
        
        saved_count = 0
        for action_data in actions:
            try:
                existing = CorporateAction.objects.filter(
                    stock=stock,
                    action_type=action_data['action_type'],
                    announcement_date=action_data['announcement_date']
                ).exists()
                
                if not existing:
                    CorporateAction.objects.create(
                        stock=stock,
                        **action_data
                    )
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error saving corporate action: {e}")
                continue
        
        if saved_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Saved {saved_count} new corporate actions'))
        else:
            self.stdout.write(f'  ℹ️  All corporate actions already in database')
    
    def _fetch_promoter_holdings(self, fetcher, stock):
        """Fetch and save promoter holdings"""
        self.stdout.write(f'  📡 Fetching promoter holdings from NSE API...')
        
        try:
            holdings = fetcher.fetch_promoter_holding(stock.symbol)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠️  NSE API error: {str(e)}'))
            return
        
        if not holdings:
            self.stdout.write(f'  ℹ️  No promoter holdings data available (NSE API may be down or rate-limiting)')
            return
        
        self.stdout.write(f'  📥 Retrieved {len(holdings)} quarters of holding data')
        
        saved_count = 0
        for holding_data in holdings:
            try:
                # Update or create
                obj, created = PromoterHolding.objects.update_or_create(
                    stock=stock,
                    quarter_end_date=holding_data['quarter_end_date'],
                    defaults=holding_data
                )
                if created:
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error saving promoter holding: {e}")
                continue
        
        if saved_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Saved {saved_count} new promoter holding records'))
        else:
            self.stdout.write(f'  ℹ️  All promoter holdings already in database')
