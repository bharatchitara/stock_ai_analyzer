"""
Image processing utilities for extracting stock holding information from screenshots
"""
import re
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)


class PortfolioImageProcessor:
    """Extract stock holding information from broker app screenshots using OCR"""
    
    def __init__(self):
        self.ocr_available = self._check_ocr_availability()
    
    def _check_ocr_availability(self) -> bool:
        """Check if OCR libraries are available"""
        try:
            import pytesseract
            from PIL import Image
            return True
        except ImportError:
            logger.warning("OCR libraries not available. Install: pip install pytesseract pillow")
            return False
    
    def extract_holdings_from_image(self, image_path: str) -> Dict:
        """
        Extract stock holdings from portfolio screenshot
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict with extracted holdings data and metadata
        """
        if not self.ocr_available:
            return {
                'success': False,
                'error': 'OCR libraries not installed. Install pytesseract and pillow.',
                'holdings': []
            }
        
        try:
            import pytesseract
            from PIL import Image
            
            # Open and preprocess image
            image = Image.open(image_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            # Extract holdings from text
            holdings = self._parse_holdings_from_text(text)
            
            return {
                'success': True,
                'holdings': holdings,
                'raw_text': text,
                'detected_broker': self._detect_broker_from_text(text)
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'holdings': []
            }
    
    def _detect_broker_from_text(self, text: str) -> Optional[str]:
        """Detect broker from screenshot text"""
        text_lower = text.lower()
        
        broker_keywords = {
            'zerodha': ['zerodha', 'kite'],
            'groww': ['groww'],
            'upstox': ['upstox'],
            'angelone': ['angel one', 'angelone', 'angel broking'],
            'hdfc': ['hdfc securities'],
            'icici': ['icici direct'],
        }
        
        for broker, keywords in broker_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return broker
        
        return None
    
    def _parse_holdings_from_text(self, text: str) -> List[Dict]:
        """
        Parse stock holdings from OCR text
        
        Common patterns in broker apps:
        - Stock symbol/name
        - Quantity (Qty)
        - Average price (Avg. price, Buy price)
        - Current price (LTP, CMP)
        - P&L
        """
        holdings = []
        lines = text.split('\n')
        
        # Pattern for stock symbols (e.g., RELIANCE, TCS, HDFCBANK)
        symbol_pattern = r'\b[A-Z]{2,12}\b'
        
        # Pattern for numbers with optional commas and decimals
        number_pattern = r'[\d,]+\.?\d*'
        
        # Pattern for price (with rupee symbol or without)
        price_pattern = r'[₹₨]?\s*' + number_pattern
        
        current_holding = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Look for stock symbols
            symbols = re.findall(symbol_pattern, line)
            
            # Common stock symbols in NSE
            if symbols:
                for symbol in symbols:
                    # Skip common words that match pattern
                    if symbol in ['QTY', 'LTP', 'CMP', 'AVG', 'PRICE', 'BUY', 'SELL', 'PNL']:
                        continue
                    
                    # Start new holding
                    if 'symbol' in current_holding:
                        holdings.append(current_holding)
                    
                    current_holding = {'symbol': symbol}
            
            # Look for quantity
            if any(keyword in line.upper() for keyword in ['QTY', 'QUANTITY', 'SHARES']):
                numbers = re.findall(number_pattern, line)
                if numbers and 'symbol' in current_holding:
                    # Find quantity (usually first number after Qty keyword)
                    qty_index = max([line.upper().find(kw) for kw in ['QTY', 'QUANTITY', 'SHARES']])
                    remaining_text = line[qty_index:]
                    qty_numbers = re.findall(number_pattern, remaining_text)
                    if qty_numbers:
                        current_holding['quantity'] = self._clean_number(qty_numbers[0])
            
            # Look for average/buy price
            if any(keyword in line.upper() for keyword in ['AVG', 'AVERAGE', 'BUY PRICE']):
                prices = re.findall(price_pattern, line)
                if prices and 'symbol' in current_holding:
                    current_holding['avg_price'] = self._clean_price(prices[0])
            
            # Look for current price
            if any(keyword in line.upper() for keyword in ['LTP', 'CMP', 'CURRENT']):
                prices = re.findall(price_pattern, line)
                if prices and 'symbol' in current_holding:
                    current_holding['current_price'] = self._clean_price(prices[0])
            
            # Alternative: Parse table-like structure (symbol qty price)
            if 'symbol' not in current_holding:
                parts = line.split()
                if len(parts) >= 3:
                    # Check if first part is a stock symbol
                    potential_symbol = parts[0].upper()
                    if re.match(r'^[A-Z]{2,12}$', potential_symbol):
                        # Try to extract quantity and price
                        numbers = [self._clean_number(p) for p in parts[1:] if re.match(number_pattern, p)]
                        if len(numbers) >= 2:
                            holdings.append({
                                'symbol': potential_symbol,
                                'quantity': numbers[0],
                                'avg_price': numbers[1]
                            })
        
        # Add last holding if exists
        if current_holding and 'symbol' in current_holding:
            holdings.append(current_holding)
        
        # Clean up holdings
        cleaned_holdings = []
        for holding in holdings:
            if 'symbol' in holding and ('quantity' in holding or 'avg_price' in holding):
                cleaned_holdings.append(holding)
        
        return cleaned_holdings
    
    def _clean_number(self, text: str) -> int:
        """Clean and convert text to integer (for quantity)"""
        try:
            # Remove commas and convert
            cleaned = re.sub(r'[,\s₹₨]', '', text)
            return int(float(cleaned))
        except (ValueError, AttributeError):
            return 0
    
    def _clean_price(self, text: str) -> float:
        """Clean and convert text to float (for prices)"""
        try:
            # Remove currency symbols, commas
            cleaned = re.sub(r'[,\s₹₨]', '', text)
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0
    
    def extract_with_gemini(self, image_path: str, gemini_api_key: str) -> Dict:
        """
        Use Google Gemini Vision API to extract holdings from image
        """
        try:
            from google import genai
            from PIL import Image
            
            # Configure Gemini
            client = genai.Client(api_key=gemini_api_key)
            
            # Open and upload image
            img = Image.open(image_path)
            
            # Create prompt
            prompt = """Extract stock holdings information from this portfolio screenshot.
Return a JSON array with objects containing:
- symbol: stock symbol (e.g., RELIANCE, TCS)
- quantity: number of shares
- avg_price: average buy price per share
- current_price: current market price (if visible)

Only return valid stock holdings. Return empty array if no holdings found.
Format: [{"symbol": "RELIANCE", "quantity": 10, "avg_price": 2450.50, "current_price": 2500.00}]
Return ONLY the JSON array, no other text."""
            
            # Get model from config
            try:
                from news.models import AIConfig
                config = AIConfig.get_active_config()
                model_name = config.gemini_model
            except:
                model_name = 'gemini-2.5-flash'
            
            # Generate response
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt, img]
            )
            content = response.text
            
            # Extract JSON from response
            import json
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                holdings = json.loads(json_match.group())
                return {
                    'success': True,
                    'holdings': holdings,
                    'method': 'gemini_vision'
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not parse Gemini response',
                    'holdings': []
                }
                
        except Exception as e:
            logger.error(f"Error with Gemini extraction: {str(e)}")
            return {
                'success': False,
                'error': f"Gemini extraction failed: {str(e)}",
                'holdings': []
            }
    
    def extract_with_ai(self, image_path: str, openai_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None) -> Dict:
        """
        Use Gemini AI Vision API to extract holdings from image
        Falls back to OCR if Gemini fails
        """
        if not gemini_api_key:
            logger.info("No Gemini API key provided, using OCR extraction")
            return self.extract_holdings_from_image(image_path)
        
        try:
            return self.extract_with_gemini(image_path, gemini_api_key)
        except Exception as e:
            logger.error(f"Error with Gemini extraction: {str(e)}")
            logger.info("Falling back to OCR extraction")
            return self.extract_holdings_from_image(image_path)
