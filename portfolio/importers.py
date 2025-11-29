"""
Portfolio import utilities for auto-retrieving user holdings
"""
import csv
import io
import json
import re
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class PortfolioImporter:
    """Import portfolio holdings from various sources"""
    
    # Supported brokers and their CSV formats
    BROKER_FORMATS = {
        'zerodha': {
            'required_columns': ['tradingsymbol', 'quantity', 'average_price'],
            'column_mapping': {
                'tradingsymbol': 'symbol',
                'quantity': 'quantity',
                'average_price': 'avg_price',
                'buy_date': 'purchase_date'
            }
        },
        'groww': {
            'required_columns': ['stock_symbol', 'qty', 'avg_buy_price'],
            'column_mapping': {
                'stock_symbol': 'symbol',
                'qty': 'quantity',
                'avg_buy_price': 'avg_price',
                'purchase_date': 'purchase_date'
            }
        },
        'upstox': {
            'required_columns': ['symbol', 'quantity', 'buy_avg_price'],
            'column_mapping': {
                'symbol': 'symbol',
                'quantity': 'quantity',
                'buy_avg_price': 'avg_price',
                'buy_date': 'purchase_date'
            }
        },
        'angelone': {
            'required_columns': ['scripname', 'netqty', 'avgprice'],
            'column_mapping': {
                'scripname': 'symbol',
                'netqty': 'quantity',
                'avgprice': 'avg_price',
                'buydate': 'purchase_date'
            }
        },
        'generic': {
            'required_columns': ['symbol', 'quantity', 'price'],
            'column_mapping': {
                'symbol': 'symbol',
                'quantity': 'quantity',
                'price': 'avg_price',
                'avg_price': 'avg_price',
                'average_price': 'avg_price',
                'date': 'purchase_date',
                'purchase_date': 'purchase_date'
            }
        }
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.skip_count = 0
    
    def detect_broker_format(self, csv_content: str) -> str:
        """Detect broker format from CSV headers"""
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            headers = [h.lower().strip() for h in reader.fieldnames]
            
            # Check for each broker format
            for broker, format_info in self.BROKER_FORMATS.items():
                required_cols = [col.lower() for col in format_info['required_columns']]
                if all(col in headers for col in required_cols):
                    return broker
            
            return 'generic'
        except Exception as e:
            logger.error(f"Error detecting broker format: {str(e)}")
            return 'generic'
    
    def parse_csv(self, csv_content: str, broker: str = None) -> List[Dict]:
        """Parse CSV content and extract holdings data"""
        holdings = []
        
        try:
            # Detect broker if not specified
            if not broker:
                broker = self.detect_broker_format(csv_content)
            
            format_info = self.BROKER_FORMATS.get(broker, self.BROKER_FORMATS['generic'])
            column_mapping = format_info['column_mapping']
            
            reader = csv.DictReader(io.StringIO(csv_content))
            
            for row_num, row in enumerate(reader, start=2):  # Start from 2 (1 is header)
                try:
                    # Convert keys to lowercase for case-insensitive matching
                    row_lower = {k.lower().strip(): v.strip() for k, v in row.items() if v}
                    
                    # Extract data using column mapping
                    holding_data = self._extract_holding_data(row_lower, column_mapping, broker)
                    
                    if holding_data:
                        holding_data['row_number'] = row_num
                        holdings.append(holding_data)
                    else:
                        self.skip_count += 1
                        self.warnings.append(f"Row {row_num}: Skipped - missing required data")
                        
                except Exception as e:
                    self.errors.append(f"Row {row_num}: {str(e)}")
                    continue
            
            logger.info(f"Parsed {len(holdings)} holdings from CSV ({broker} format)")
            
        except Exception as e:
            self.errors.append(f"CSV parsing error: {str(e)}")
            logger.error(f"Error parsing CSV: {str(e)}")
        
        return holdings
    
    def _extract_holding_data(self, row: Dict, column_mapping: Dict, broker: str) -> Dict:
        """Extract holding data from a CSV row"""
        holding = {}
        
        # Extract symbol
        symbol = None
        for source_col in ['tradingsymbol', 'symbol', 'stock_symbol', 'scripname', 'scrip']:
            if source_col in row:
                symbol = self._clean_symbol(row[source_col])
                break
        
        if not symbol:
            return None
        
        # Extract quantity
        quantity = None
        for qty_col in ['quantity', 'qty', 'netqty', 'net_qty']:
            if qty_col in row:
                try:
                    quantity = int(float(row[qty_col]))
                    break
                except (ValueError, TypeError):
                    continue
        
        if not quantity or quantity <= 0:
            return None
        
        # Extract average price
        avg_price = None
        for price_col in ['average_price', 'avg_price', 'avgprice', 'buy_avg_price', 'price']:
            if price_col in row:
                try:
                    avg_price = Decimal(str(row[price_col]).replace(',', ''))
                    break
                except (ValueError, TypeError, Decimal.InvalidOperation):
                    continue
        
        if not avg_price or avg_price <= 0:
            return None
        
        # Extract purchase date (optional)
        purchase_date = None
        for date_col in ['purchase_date', 'buy_date', 'buydate', 'date']:
            if date_col in row and row[date_col]:
                purchase_date = self._parse_date(row[date_col])
                break
        
        if not purchase_date:
            purchase_date = date.today()
        
        holding = {
            'symbol': symbol,
            'quantity': quantity,
            'avg_price': avg_price,
            'purchase_date': purchase_date,
            'broker': broker
        }
        
        return holding
    
    def _clean_symbol(self, symbol: str) -> str:
        """Clean and normalize stock symbol"""
        # Remove common suffixes
        symbol = symbol.upper().strip()
        symbol = re.sub(r'[-_\s]EQ$', '', symbol)  # Remove -EQ suffix
        symbol = re.sub(r'\.NS$|\.BO$', '', symbol)  # Remove NSE/BSE suffixes
        return symbol
    
    def _parse_date(self, date_string: str) -> date:
        """Parse date from various formats"""
        date_formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%d-%b-%Y',
            '%d %b %Y',
            '%Y%m%d'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string.strip(), fmt).date()
            except (ValueError, AttributeError):
                continue
        
        # If no format matches, return today
        return date.today()
    
    def parse_json(self, json_content: str) -> List[Dict]:
        """Parse JSON format portfolio data"""
        holdings = []
        
        try:
            data = json.loads(json_content)
            
            # Handle different JSON structures
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # Try common keys
                items = data.get('holdings', data.get('positions', data.get('data', [])))
            else:
                self.errors.append("Invalid JSON structure")
                return []
            
            for idx, item in enumerate(items, start=1):
                try:
                    holding = {
                        'symbol': self._clean_symbol(item.get('symbol', item.get('tradingsymbol', ''))),
                        'quantity': int(item.get('quantity', item.get('qty', 0))),
                        'avg_price': Decimal(str(item.get('average_price', item.get('avg_price', 0)))),
                        'purchase_date': self._parse_date(item.get('purchase_date', item.get('date', str(date.today())))),
                        'broker': item.get('broker', 'imported')
                    }
                    
                    if holding['symbol'] and holding['quantity'] > 0 and holding['avg_price'] > 0:
                        holdings.append(holding)
                        self.success_count += 1
                    else:
                        self.skip_count += 1
                        
                except Exception as e:
                    self.errors.append(f"Item {idx}: {str(e)}")
                    continue
            
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            self.errors.append(f"JSON parsing error: {str(e)}")
        
        return holdings
    
    def get_import_summary(self) -> Dict:
        """Get summary of import operation"""
        return {
            'success_count': self.success_count,
            'skip_count': self.skip_count,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings
        }


class BrokerAPIConnector:
    """Connect to broker APIs to fetch portfolio (future implementation)"""
    
    SUPPORTED_BROKERS = ['zerodha', 'groww', 'upstox', 'angelone']
    
    def __init__(self, broker: str, api_key: str = None, access_token: str = None):
        self.broker = broker.lower()
        self.api_key = api_key
        self.access_token = access_token
        
        if self.broker not in self.SUPPORTED_BROKERS:
            raise ValueError(f"Unsupported broker: {broker}")
    
    def fetch_holdings(self) -> List[Dict]:
        """Fetch holdings from broker API"""
        # This would be implemented for each broker's API
        # For now, return placeholder
        raise NotImplementedError(f"API integration for {self.broker} coming soon")
    
    def get_authorization_url(self) -> str:
        """Get OAuth authorization URL for broker"""
        # Implementation depends on broker's OAuth flow
        raise NotImplementedError(f"OAuth for {self.broker} coming soon")