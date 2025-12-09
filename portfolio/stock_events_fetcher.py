"""
Data fetcher for stock events: insider trades, bulk deals, corporate actions, promoter holdings
"""
import logging
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)


class StockEventFetcher:
    """Fetch stock events from various sources (NSE, BSE, screener.in, etc.)"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nseindia.com/',
        })
        self.nse_base_url = 'https://www.nseindia.com'
        self.bse_base_url = 'https://www.bseindia.com'
        self.screener_base_url = 'https://www.screener.in'
    
    def _get_nse_cookies(self):
        """Get NSE cookies for API access"""
        try:
            self.session.get(self.nse_base_url, timeout=10)
        except Exception as e:
            logger.error(f"Error getting NSE cookies: {e}")
    
    def fetch_insider_trades(self, symbol: str, days: int = 90) -> List[Dict]:
        """
        Fetch insider trading data for a stock
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            days: Number of days to look back
            
        Returns:
            List of insider trade dictionaries
        """
        trades = []
        
        # Try NSE first
        try:
            self._get_nse_cookies()
            
            # NSE insider trading URL
            url = f"{self.nse_base_url}/api/corporates-pit?symbol={symbol}&index=equities"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    for item in data['data']:
                        try:
                            trade = {
                                'insider_name': item.get('personName', ''),
                                'insider_designation': item.get('personCategory', ''),
                                'transaction_type': self._parse_transaction_type(item.get('typeOfSecurity', '')),
                                'quantity': int(item.get('secAcq', 0) or item.get('secDisp', 0) or 0),
                                'transaction_date': self._parse_date(item.get('acqfromDt', '')),
                                'intimation_date': self._parse_date(item.get('intimDt', '')),
                                'exchange': 'NSE',
                                'remarks': item.get('remarks', ''),
                            }
                            
                            # Calculate transaction value if price available
                            if 'price' in item and item['price']:
                                trade['price_per_share'] = float(item['price'])
                                trade['total_value'] = trade['price_per_share'] * trade['quantity']
                            
                            trades.append(trade)
                        except Exception as e:
                            logger.warning(f"Error parsing insider trade: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error fetching NSE insider trades for {symbol}: {e}")
        
        # Try alternative source: screener.in or investing.com
        if not trades:
            trades = self._fetch_insider_trades_alternative(symbol, days)
        
        return trades
    
    def fetch_bulk_deals(self, symbol: str = None, date: str = None) -> List[Dict]:
        """
        Fetch bulk deals (>0.5% equity transactions)
        
        Args:
            symbol: Stock symbol (optional, if None fetches all)
            date: Date in YYYY-MM-DD format (optional, defaults to today)
            
        Returns:
            List of bulk deal dictionaries
        """
        deals = []
        
        if not date:
            date = datetime.now().strftime('%d-%m-%Y')
        else:
            # Convert YYYY-MM-DD to DD-MM-YYYY for NSE
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date = date_obj.strftime('%d-%m-%Y')
        
        try:
            self._get_nse_cookies()
            
            # NSE bulk deals URL
            url = f"{self.nse_base_url}/api/live-analysis-bulk-deals?date={date}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    for item in data['data']:
                        try:
                            deal_symbol = item.get('symbol', '')
                            
                            # Filter by symbol if provided
                            if symbol and deal_symbol != symbol:
                                continue
                            
                            deal = {
                                'symbol': deal_symbol,
                                'client_name': item.get('clientName', ''),
                                'deal_type': 'BUY' if 'buy' in item.get('dealType', '').lower() else 'SELL',
                                'quantity': int(item.get('quantity', 0)),
                                'price_per_share': float(item.get('tradePrice', 0)),
                                'total_value': float(item.get('quantity', 0)) * float(item.get('tradePrice', 0)),
                                'deal_date': self._parse_date(date),
                                'exchange': 'NSE',
                                'remarks': item.get('remarks', ''),
                            }
                            
                            deals.append(deal)
                        except Exception as e:
                            logger.warning(f"Error parsing bulk deal: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error fetching NSE bulk deals: {e}")
        
        return deals
    
    def fetch_block_deals(self, symbol: str = None, date: str = None) -> List[Dict]:
        """
        Fetch block deals (>10,000 shares or >Rs 10 crore)
        
        Args:
            symbol: Stock symbol (optional)
            date: Date in YYYY-MM-DD format (optional)
            
        Returns:
            List of block deal dictionaries
        """
        deals = []
        
        if not date:
            date = datetime.now().strftime('%d-%m-%Y')
        else:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date = date_obj.strftime('%d-%m-%Y')
        
        try:
            self._get_nse_cookies()
            
            # NSE block deals URL
            url = f"{self.nse_base_url}/api/live-analysis-block-deals?date={date}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    for item in data['data']:
                        try:
                            deal_symbol = item.get('symbol', '')
                            
                            if symbol and deal_symbol != symbol:
                                continue
                            
                            deal = {
                                'symbol': deal_symbol,
                                'client_name': item.get('clientName', ''),
                                'deal_type': 'BUY' if 'buy' in item.get('dealType', '').lower() else 'SELL',
                                'quantity': int(item.get('quantity', 0)),
                                'price_per_share': float(item.get('tradePrice', 0)),
                                'total_value': float(item.get('quantity', 0)) * float(item.get('tradePrice', 0)),
                                'deal_date': self._parse_date(date),
                                'exchange': 'NSE',
                                'remarks': item.get('remarks', ''),
                            }
                            
                            deals.append(deal)
                        except Exception as e:
                            logger.warning(f"Error parsing block deal: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error fetching NSE block deals: {e}")
        
        return deals
    
    def fetch_corporate_actions(self, symbol: str, months: int = 12) -> List[Dict]:
        """
        Fetch corporate actions (dividends, bonuses, splits, etc.)
        
        Args:
            symbol: Stock symbol
            months: Number of months to look back
            
        Returns:
            List of corporate action dictionaries
        """
        actions = []
        
        try:
            self._get_nse_cookies()
            
            # NSE corporate actions URL
            url = f"{self.nse_base_url}/api/corporate-announcements?index=equities&symbol={symbol}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    for item in data:
                        try:
                            subject = item.get('subject', '').lower()
                            
                            # Determine action type
                            action_type = self._determine_action_type(subject)
                            
                            if not action_type:
                                continue
                            
                            action = {
                                'action_type': action_type,
                                'description': item.get('subject', ''),
                                'announcement_date': self._parse_date(item.get('an_dt', '')),
                                'ex_date': self._parse_date(item.get('ex_dt', '')),
                                'record_date': self._parse_date(item.get('rec_dt', '')),
                                'remarks': item.get('attchmntText', ''),
                            }
                            
                            # Extract specific details based on type
                            if action_type == 'DIVIDEND':
                                action['dividend_amount'] = self._extract_dividend_amount(subject)
                            elif action_type == 'BONUS':
                                action['bonus_ratio'] = self._extract_ratio(subject)
                            elif action_type == 'SPLIT':
                                action['split_ratio'] = self._extract_ratio(subject)
                            elif action_type == 'RIGHTS':
                                action['rights_ratio'] = self._extract_ratio(subject)
                            
                            actions.append(action)
                        except Exception as e:
                            logger.warning(f"Error parsing corporate action: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error fetching corporate actions for {symbol}: {e}")
        
        return actions
    
    def fetch_promoter_holding(self, symbol: str, days: int = 90) -> List[Dict]:
        """
        Fetch promoter shareholding pattern
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back (unused, kept for API compatibility)
            
        Returns:
            List of promoter holding dictionaries by quarter
        """
        holdings = []
        
        # Try NSE API first with correct endpoint
        try:
            self._get_nse_cookies()
            
            # Get stock details from database to get company name
            from news.models import Stock
            try:
                stock = Stock.objects.get(symbol=symbol)
                company_name = stock.company_name
            except:
                company_name = symbol
            
            # NSE shareholding pattern URL with required parameters
            import urllib.parse
            encoded_name = urllib.parse.quote(company_name)
            url = f"{self.nse_base_url}/api/corporate-share-holdings-master?index=equities&symbol={symbol}&issuer={encoded_name}"
            
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if 'data' in data and isinstance(data['data'], list):
                        for item in data['data']:
                            try:
                                holding = {
                                    'quarter_end_date': self._parse_date(item.get('date', '')),
                                    'promoter_holding': float(item.get('promoterPercentage', 0) or 0),
                                    'promoter_pledged': float(item.get('pledgedPercentage', 0) or 0),
                                    'public_holding': float(item.get('publicPercentage', 0) or 0),
                                    'fii_holding': float(item.get('fiiPercentage', 0) or 0),
                                    'dii_holding': float(item.get('diiPercentage', 0) or 0),
                                }
                                
                                if holding['quarter_end_date']:
                                    holdings.append(holding)
                            except Exception as e:
                                logger.debug(f"Error parsing NSE holding: {e}")
                                continue
                        
                        if holdings:
                            logger.info(f"Successfully fetched {len(holdings)} quarters from NSE for {symbol}")
                            return holdings
                            
                except ValueError as json_error:
                    logger.warning(f"NSE returned invalid JSON for {symbol}: {json_error}")
            else:
                logger.warning(f"NSE API returned status {response.status_code} for {symbol}")
                
        except Exception as e:
            logger.error(f"Error fetching from NSE for {symbol}: {e}")
        
        # Fallback to screener.in if NSE fails
        holdings = self._fetch_promoter_holding_screener(symbol)
        
        if holdings:
            logger.info(f"Successfully fetched {len(holdings)} quarters from screener.in for {symbol}")
        else:
            logger.warning(f"No promoter holdings data found for {symbol}")
        
        return holdings
    
    def fetch_all_events_for_stock(self, symbol: str) -> Dict:
        """
        Fetch all events for a stock in one call
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with all event types
        """
        return {
            'insider_trades': self.fetch_insider_trades(symbol),
            'bulk_deals': self.fetch_bulk_deals(symbol),
            'block_deals': self.fetch_block_deals(symbol),
            'corporate_actions': self.fetch_corporate_actions(symbol),
            'promoter_holdings': self.fetch_promoter_holding(symbol),
        }
    
    # Helper methods
    
    def _parse_transaction_type(self, text: str) -> str:
        """Parse transaction type from text"""
        text = text.lower()
        if 'buy' in text or 'acquisition' in text or 'acquired' in text:
            return 'BUY'
        elif 'sell' in text or 'disposal' in text or 'sold' in text:
            return 'SELL'
        elif 'pledge' in text:
            return 'PLEDGE'
        elif 'revoke' in text or 'unpledge' in text:
            return 'REVOKE'
        return 'BUY'
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return None
        
        try:
            # Try various date formats
            for fmt in ['%d-%b-%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    date_obj = datetime.strptime(str(date_str), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    continue
            
            # If all formats fail, return None
            return None
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {e}")
            return None
    
    def _determine_action_type(self, subject: str) -> Optional[str]:
        """Determine corporate action type from subject"""
        subject = subject.lower()
        
        if 'dividend' in subject:
            return 'DIVIDEND'
        elif 'bonus' in subject:
            return 'BONUS'
        elif 'split' in subject or 'sub-division' in subject:
            return 'SPLIT'
        elif 'rights' in subject:
            return 'RIGHTS'
        elif 'buyback' in subject or 'buy back' in subject:
            return 'BUYBACK'
        elif 'merger' in subject or 'amalgamation' in subject:
            return 'MERGER'
        elif 'delisting' in subject:
            return 'DELISTING'
        elif 'agm' in subject or 'annual general meeting' in subject:
            return 'AGM'
        elif 'egm' in subject or 'extraordinary general meeting' in subject:
            return 'EGM'
        
        return None
    
    def _extract_dividend_amount(self, text: str) -> Optional[float]:
        """Extract dividend amount from text"""
        try:
            # Look for patterns like "Rs 10", "₹5.50", "Re 1"
            match = re.search(r'(?:rs\.?|₹|re\.?)\s*(\d+\.?\d*)', text.lower())
            if match:
                return float(match.group(1))
        except:
            pass
        return None
    
    def _extract_ratio(self, text: str) -> Optional[str]:
        """Extract ratio from text (e.g., '1:2' or '2 for 1')"""
        try:
            # Look for patterns like "1:2", "1 for 2", "2-for-1"
            match = re.search(r'(\d+)\s*(?::|for|-)\s*(\d+)', text.lower())
            if match:
                return f"{match.group(1)}:{match.group(2)}"
        except:
            pass
        return None
    
    def _fetch_insider_trades_alternative(self, symbol: str, days: int) -> List[Dict]:
        """Fetch from alternative sources when NSE fails"""
        # Implementation for alternative sources (screener.in, investing.com, etc.)
        # This is a placeholder - implement based on available APIs
        return []
    
    def _fetch_promoter_holding_screener(self, symbol: str) -> List[Dict]:
        """Fetch promoter holdings from screener.in"""
        holdings = []
        
        try:
            # Screener.in stock page
            url = f"{self.screener_base_url}/company/{symbol}/"
            logger.info(f"Attempting to fetch from screener.in: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            logger.info(f"Screener.in response status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find shareholding pattern section
                shareholding_section = soup.find('section', {'id': 'shareholding'})
                
                if shareholding_section:
                    # Look for the first table with shareholding data (recent quarters)
                    table = shareholding_section.find('table')
                    
                    if table:
                        rows = table.find_all('tr')
                        
                        if len(rows) >= 4:  # Need at least header + 3 rows (Promoters, FII, DII)
                            try:
                                # First row is header with quarters
                                header_row = rows[0]
                                quarter_cells = header_row.find_all(['th', 'td'])[1:]  # Skip first column
                                quarters = [cell.text.strip() for cell in quarter_cells]
                                
                                # Find Promoters, FII, and DII rows
                                promoter_row = None
                                fii_row = None
                                dii_row = None
                                
                                for row in rows[1:]:
                                    label = row.find(['th', 'td']).text.strip().lower()
                                    if 'promoter' in label:
                                        promoter_row = row
                                    elif 'fii' in label or 'foreign' in label:
                                        fii_row = row
                                    elif 'dii' in label or 'domestic' in label:
                                        dii_row = row
                                
                                if promoter_row:
                                    promoter_cells = promoter_row.find_all('td')
                                    fii_cells = fii_row.find_all('td') if fii_row else []
                                    dii_cells = dii_row.find_all('td') if dii_row else []
                                    
                                    # Process each quarter
                                    for i, quarter_text in enumerate(quarters):
                                        if i < len(promoter_cells):
                                            try:
                                                promoter_pct = float(promoter_cells[i].text.strip().replace('%', ''))
                                                fii_pct = float(fii_cells[i].text.strip().replace('%', '')) if i < len(fii_cells) else 0.0
                                                dii_pct = float(dii_cells[i].text.strip().replace('%', '')) if i < len(dii_cells) else 0.0
                                                
                                                # Parse quarter date (e.g., "Sep 2024")
                                                quarter_date = self._parse_quarter_date(quarter_text)
                                                
                                                if quarter_date:
                                                    holding = {
                                                        'quarter_end_date': quarter_date,
                                                        'promoter_holding': promoter_pct,
                                                        'promoter_pledged': 0.0,  # Not available on screener
                                                        'public_holding': 100.0 - promoter_pct - fii_pct - dii_pct,
                                                        'fii_holding': fii_pct,
                                                        'dii_holding': dii_pct,
                                                    }
                                                    holdings.append(holding)
                                            except Exception as e:
                                                logger.debug(f"Error parsing quarter {quarter_text}: {e}")
                                                continue
                                
                                logger.info(f"Fetched {len(holdings)} quarters from screener.in for {symbol}")
                            except Exception as e:
                                logger.error(f"Error parsing screener table: {e}")
                    else:
                        logger.warning(f"No table found in shareholding section for {symbol}")
            else:
                logger.warning(f"Screener.in returned status {response.status_code} for {symbol}")
                
        except Exception as e:
            logger.error(f"Error fetching from screener.in for {symbol}: {e}")
        
        return holdings
    
    def _parse_quarter_date(self, quarter_text: str) -> Optional[str]:
        """Parse quarter text like 'Sep 2024' to last day of quarter"""
        try:
            # Map month to quarter end date
            quarter_map = {
                'mar': '-03-31',
                'jun': '-06-30',
                'sep': '-09-30',
                'dec': '-12-31',
            }
            
            quarter_text = quarter_text.lower()
            
            for month, suffix in quarter_map.items():
                if month in quarter_text:
                    # Extract year
                    year_match = re.search(r'\d{4}', quarter_text)
                    if year_match:
                        year = year_match.group(0)
                        return f"{year}{suffix}"
            
            return None
        except Exception as e:
            logger.debug(f"Error parsing quarter date {quarter_text}: {e}")
            return None
    
    def _fetch_promoter_holding_alternative(self, symbol: str) -> List[Dict]:
        """Fetch from alternative sources when NSE fails"""
        # Try screener.in
        return self._fetch_promoter_holding_screener(symbol)
