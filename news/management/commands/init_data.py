from django.core.management.base import BaseCommand
from django.utils import timezone
from news.models import Stock, Category, NewsSource


class Command(BaseCommand):
    help = 'Initialize database with default stocks, categories, and news sources'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing database with default data...')
        
        # Create categories
        categories_data = [
            ('MARKET_OPEN', 'Market Opening News', '#17a2b8'),
            ('EARNINGS', 'Earnings Reports', '#28a745'),
            ('POLICY', 'Government Policy', '#ffc107'),
            ('GLOBAL', 'Global Market Impact', '#fd7e14'),
            ('SECTOR', 'Sector-specific News', '#6f42c1'),
            ('IPO', 'IPO and Listings', '#e83e8c'),
            ('MERGER', 'Mergers & Acquisitions', '#20c997'),
            ('COMMODITY', 'Commodity News', '#6c757d'),
            ('CURRENCY', 'Currency and Forex', '#007bff'),
            ('REGULATORY', 'Regulatory Changes', '#dc3545'),
            ('OTHER', 'Other News', '#495057'),
        ]
        
        for name, description, color in categories_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'color_code': color
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.get_name_display()}')
        
        # Create major Indian stocks
        stocks_data = [
            # Nifty 50 major stocks
            ('RELIANCE', 'Reliance Industries Limited', 'Energy', True, True),
            ('TCS', 'Tata Consultancy Services', 'Information Technology', True, True),
            ('HDFCBANK', 'HDFC Bank Limited', 'Banking', True, True),
            ('INFY', 'Infosys Limited', 'Information Technology', True, True),
            ('ITC', 'ITC Limited', 'FMCG', True, True),
            ('SBIN', 'State Bank of India', 'Banking', True, True),
            ('BHARTIARTL', 'Bharti Airtel Limited', 'Telecommunications', True, False),
            ('KOTAKBANK', 'Kotak Mahindra Bank', 'Banking', True, False),
            ('LT', 'Larsen & Toubro Limited', 'Engineering', True, True),
            ('WIPRO', 'Wipro Limited', 'Information Technology', True, False),
            ('MARUTI', 'Maruti Suzuki India Limited', 'Automotive', True, True),
            ('TATAMOTORS', 'Tata Motors Limited', 'Automotive', True, True),
            ('TATASTEEL', 'Tata Steel Limited', 'Metals', True, True),
            ('BAJFINANCE', 'Bajaj Finance Limited', 'Financial Services', True, False),
            ('HCLTECH', 'HCL Technologies Limited', 'Information Technology', True, False),
            ('ASIANPAINT', 'Asian Paints Limited', 'Consumer Goods', True, True),
            ('NESTLEIND', 'Nestle India Limited', 'FMCG', True, False),
            ('ULTRACEMCO', 'UltraTech Cement Limited', 'Cement', True, True),
            ('TITAN', 'Titan Company Limited', 'Consumer Goods', True, False),
            ('AXISBANK', 'Axis Bank Limited', 'Banking', True, True),
            ('ICICIBANK', 'ICICI Bank Limited', 'Banking', True, True),
            ('HINDUNILVR', 'Hindustan Unilever Limited', 'FMCG', True, True),
            ('SUNPHARMA', 'Sun Pharmaceutical Industries', 'Pharmaceuticals', True, True),
            ('POWERGRID', 'Power Grid Corporation of India', 'Utilities', True, True),
            ('NTPC', 'NTPC Limited', 'Utilities', True, True),
            ('ONGC', 'Oil and Natural Gas Corporation', 'Energy', True, True),
            ('TECHM', 'Tech Mahindra Limited', 'Information Technology', True, False),
            ('DRREDDY', 'Dr. Reddys Laboratories', 'Pharmaceuticals', True, False),
            ('CIPLA', 'Cipla Limited', 'Pharmaceuticals', True, False),
            ('ADANIPORTS', 'Adani Ports and SEZ', 'Infrastructure', True, False),
        ]
        
        for symbol, name, sector, is_nifty50, is_sensex in stocks_data:
            stock, created = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'company_name': name,
                    'sector': sector,
                    'is_nifty50': is_nifty50,
                    'is_sensex': is_sensex
                }
            )
            if created:
                self.stdout.write(f'Created stock: {stock.symbol} - {stock.company_name}')
        
        # Create news sources
        sources_data = [
            ('Economic Times', 'https://economictimes.indiatimes.com', 
             'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms'),
            ('Business Standard', 'https://www.business-standard.com', 
             'https://www.business-standard.com/rss/markets-106.rss'),
            ('LiveMint', 'https://www.livemint.com', 
             'https://www.livemint.com/rss/market'),
            ('MoneyControl', 'https://www.moneycontrol.com', 
             'https://www.moneycontrol.com/rss/results.xml'),
            ('Financial Express', 'https://www.financialexpress.com', 
             'https://www.financialexpress.com/market/rss/'),
            ('The Hindu BusinessLine', 'https://www.thehindubusinessline.com', 
             'https://www.thehindubusinessline.com/markets/?service=rss'),
        ]
        
        for name, url, rss_feed in sources_data:
            source, created = NewsSource.objects.get_or_create(
                name=name,
                defaults={
                    'url': url,
                    'rss_feed': rss_feed,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created news source: {source.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully initialized database with default data!')
        )
        self.stdout.write(
            f'Created {Category.objects.count()} categories, '
            f'{Stock.objects.count()} stocks, '
            f'and {NewsSource.objects.count()} news sources.'
        )