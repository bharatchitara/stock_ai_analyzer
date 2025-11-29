"""
Stock price fetching utilities for Indian stocks
"""
import logging
import requests
from decimal import Decimal
from typing import Dict, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


class StockPriceFetcher:
    """Fetch current stock prices from various sources"""
    
    def __init__(self):
        self.base_urls = {
            'nse': 'https://www.nseindia.com/api/quote-equity?symbol=',
            'yahoo': 'https://query1.finance.yahoo.com/v8/finance/chart/',
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        # Create session for NSE with cookies
        self.nse_session = requests.Session()
        self.nse_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        })
    
    def fetch_price(self, symbol: str) -> Dict:
        """
        Fetch current price for a stock symbol
        Tries multiple sources in order of reliability
        """
        # Try Yahoo Finance first (more reliable API)
        price = self._fetch_from_yahoo(symbol)
        if price:
            return {
                'success': True,
                'symbol': symbol,
                'current_price': price,
                'source': 'Yahoo Finance',
                'timestamp': timezone.now()
            }
        
        # Fall back to NSE
        price = self._fetch_from_nse(symbol)
        if price:
            return {
                'success': True,
                'symbol': symbol,
                'current_price': price,
                'source': 'NSE',
                'timestamp': timezone.now()
            }
        
        return {
            'success': False,
            'symbol': symbol,
            'error': 'Could not fetch price from any source'
        }
    
    def _fetch_from_nse(self, symbol: str) -> Optional[Decimal]:
        """Fetch price from NSE India"""
        try:
            # First, get cookies by visiting the homepage
            try:
                self.nse_session.get('https://www.nseindia.com', timeout=5)
            except:
                pass  # Ignore if homepage fails
            
            url = f"{self.base_urls['nse']}{symbol}"
            response = self.nse_session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # NSE returns price in 'priceInfo' -> 'lastPrice'
                    if 'priceInfo' in data and 'lastPrice' in data['priceInfo']:
                        price = data['priceInfo']['lastPrice']
                        return Decimal(str(price))
                except ValueError as ve:
                    # JSON decode error - likely HTML response
                    logger.debug(f"NSE returned non-JSON response for {symbol}")
                    return None
            
            return None
            
        except Exception as e:
            logger.debug(f"NSE fetch failed for {symbol}: {str(e)}")
            return None
    
    def _fetch_from_yahoo(self, symbol: str) -> Optional[Decimal]:
        """Fetch price from Yahoo Finance"""
        try:
            # Yahoo Finance uses .NS suffix for NSE stocks
            yahoo_symbol = f"{symbol}.NS"
            url = f"{self.base_urls['yahoo']}{yahoo_symbol}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Navigate to current price in Yahoo's response
                if 'chart' in data and 'result' in data['chart']:
                    results = data['chart']['result']
                    if results and len(results) > 0:
                        result = results[0]
                        if 'meta' in result and 'regularMarketPrice' in result['meta']:
                            price = result['meta']['regularMarketPrice']
                            return Decimal(str(price))
            
            return None
            
        except Exception as e:
            logger.debug(f"Yahoo Finance fetch failed for {symbol}: {str(e)}")
            return None
    
    def fetch_multiple_prices(self, symbols: list) -> Dict[str, Dict]:
        """Fetch prices for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            result = self.fetch_price(symbol)
            results[symbol] = result
        
        return results
    
    def update_stock_prices(self, stocks_queryset):
        """Update prices for a queryset of Stock objects"""
        updated_count = 0
        failed_count = 0
        
        for stock in stocks_queryset:
            result = self.fetch_price(stock.symbol)
            
            if result['success']:
                stock.current_price = result['current_price']
                stock.price_updated_at = result['timestamp']
                stock.save(update_fields=['current_price', 'price_updated_at'])
                updated_count += 1
                logger.info(f"Updated price for {stock.symbol}: ₹{result['current_price']} (from {result['source']})")
            else:
                failed_count += 1
                logger.debug(f"Failed to update price for {stock.symbol}")
        
        return {
            'updated': updated_count,
            'failed': failed_count,
            'total': stocks_queryset.count()
        }
