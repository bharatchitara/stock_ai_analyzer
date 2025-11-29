# Stock Price Fetching System

## Overview
The system automatically fetches current stock prices from NSE India and Yahoo Finance when you import holdings or manually via the dashboard.

## Features

### 1. Automatic Price Updates
Stock prices are automatically fetched when:
- Adding a new holding manually
- Importing holdings from CSV/JSON files
- Importing holdings from images (screenshots)

### 2. Manual Price Refresh
Click the **"Refresh Prices"** button on the portfolio dashboard to update all stock prices in your portfolio.

### 3. Management Command
Update prices via command line:

```bash
# Update prices for all stocks in portfolios
python manage.py update_prices

# Update all stocks in database
python manage.py update_prices --all

# Update specific stocks
python manage.py update_prices --symbols RELIANCE TCS HDFCBANK
```

## Data Sources

### Primary: NSE India
- Most reliable for Indian stocks
- Real-time market data
- Directly from National Stock Exchange

### Fallback: Yahoo Finance
- Used when NSE fails
- Uses `.NS` suffix for NSE-listed stocks
- Global coverage

## How It Works

1. **Try NSE First**: Fetches from NSE India API
2. **Fallback to Yahoo**: If NSE fails, tries Yahoo Finance
3. **Store Results**: Updates `Stock.current_price` and `Stock.price_updated_at`
4. **Error Handling**: Gracefully handles API failures, rate limits, and network issues

## Stock Price Fields

Each Stock model has:
- `current_price`: Latest market price (Decimal)
- `price_updated_at`: Timestamp of last successful price fetch (DateTime)

## Example Usage

### In Views
```python
from portfolio.stock_fetcher import StockPriceFetcher

# Fetch single stock price
fetcher = StockPriceFetcher()
result = fetcher.fetch_price('RELIANCE')

if result['success']:
    print(f"Price: ₹{result['current_price']}")
    print(f"Source: {result['source']}")
else:
    print(f"Error: {result['error']}")

# Update multiple stocks
stocks = Stock.objects.filter(symbol__in=['TCS', 'INFY', 'WIPRO'])
price_result = fetcher.update_stock_prices(stocks)

print(f"Updated: {price_result['updated']}")
print(f"Failed: {price_result['failed']}")
```

## Import Flow

### CSV/JSON Import
1. Parse holdings from file
2. Create/update portfolio holdings
3. **Fetch current prices for all imported stocks**
4. Show success message with price update count

### Image Import
1. Extract holdings using OCR/AI
2. Create/update portfolio holdings
3. **Fetch current prices for all imported stocks**
4. Show success message with price update count

## Error Handling

The system handles:
- **Network timeouts**: 10-second timeout per request
- **API rate limits**: Graceful failure with warning messages
- **Invalid symbols**: Logs warning and continues
- **Server errors**: Falls back to alternate source

## User Feedback

Users receive clear messages:
- ✅ "Updated prices for 5 stocks"
- ⚠️ "Could not fetch prices for 2 stocks"
- ℹ️ "Current price updated: ₹2,450.50"

## Future Enhancements

Potential improvements:
- Scheduled price updates (using Celery)
- Caching to reduce API calls
- Real-time WebSocket price updates
- Support for more exchanges (BSE, etc.)
- Historical price tracking
- Price alerts and notifications
