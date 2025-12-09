"""
Management command to generate entry signals for stocks
"""
from django.core.management.base import BaseCommand
from analysis.entry_signal_analyzer import EntrySignalAnalyzer
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate entry signals for buying opportunities'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Analyzing stocks for entry opportunities...\n')
        
        analyzer = EntrySignalAnalyzer()
        results = analyzer.generate_all_entry_signals()
        
        self.stdout.write(f'\n📊 Entry Signals Generated:')
        self.stdout.write(f'  💰 Price Dips (5-7%): {results["price_dips"]}')
        self.stdout.write(f'  📦 New Orders: {results["order_wins"]}')
        self.stdout.write(f'  💵 Dividend Announcements: {results["dividends"]}')
        self.stdout.write(f'  🏭 Expansion/Acquisition: {results["expansions"]}')
        self.stdout.write(f'  ✂️  Stock Splits: {results["splits"]}')
        self.stdout.write(f'  🎁 Bonus Issues: {results["bonuses"]}')
        self.stdout.write(f'\n  ✅ Total: {results["total"]} new entry signals')
        
        self.stdout.write(self.style.SUCCESS('\n✨ Entry signal generation completed!'))
