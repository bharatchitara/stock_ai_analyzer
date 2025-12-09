# Stock Events Tracker - User Guide

## Overview
This module tracks important stock events for your portfolio holdings including:
- **Insider Trades**: Directors and promoters buying/selling shares
- **Bulk Deals**: Large transactions (>0.5% of equity)
- **Block Deals**: Institutional transactions (>10,000 shares or >Rs 10 crore)
- **Corporate Actions**: Dividends, bonuses, splits, rights issues, buybacks
- **Promoter Holdings**: Quarterly shareholding pattern changes

## Features

### 1. Automated Data Fetching
Automatically fetch stock events from NSE/BSE and other sources.

### 2. Event Tracking
- Real-time updates on insider trading activity
- Track bulk and block deal transactions
- Monitor corporate actions (dividends, bonuses, etc.)
- Analyze promoter holding trends

### 3. Portfolio Integration
- View events for all your held stocks
- Filter events by stock or holding
- Get alerts on significant events

## Quick Start

### Step 1: Set Up Your Portfolio
Add stocks to your portfolio through the dashboard:
```
http://localhost:8000/portfolio/
```

### Step 2: Fetch Stock Events
Run the management command to fetch events for your holdings:

```bash
# Fetch all events for portfolio holdings
python manage.py fetch_stock_events --holdings-only

# Fetch specific event type
python manage.py fetch_stock_events --event-type insider --holdings-only

# Fetch for specific stock
python manage.py fetch_stock_events --symbol RELIANCE

# Fetch for all stocks (first 50)
python manage.py fetch_stock_events
```

### Step 3: View Stock Events
Navigate to a stock's event page:
```
http://localhost:8000/portfolio/stock/RELIANCE/events/
```

Or view events directly from holding detail page.

## Management Commands

### `fetch_stock_events`
Fetch stock events from various sources.

**Options:**
- `--symbol SYMBOL`: Fetch for specific stock symbol
- `--event-type {insider,bulk,block,corporate,promoter,all}`: Event type to fetch (default: all)
- `--holdings-only`: Fetch only for stocks in portfolio holdings
- `--days DAYS`: Number of days to look back for trades (default: 90)

**Examples:**

```bash
# Fetch insider trades for last 30 days for holdings
python manage.py fetch_stock_events --event-type insider --days 30 --holdings-only

# Fetch all events for TCS
python manage.py fetch_stock_events --symbol TCS --event-type all

# Fetch only promoter holdings for all stocks
python manage.py fetch_stock_events --event-type promoter
```

## API Endpoints

### Fetch Events via AJAX
```javascript
POST /portfolio/api/fetch-events/

Request:
{
    "symbol": "RELIANCE",
    "event_type": "all"  // or "insider", "bulk", "block", "corporate", "promoter"
}

Response:
{
    "success": true,
    "fetched": {
        "insider_trades": 5,
        "bulk_deals": 2,
        "corporate_actions": 1,
        "promoter_holdings": 4
    }
}
```

## Data Models

### InsiderTrade
- `insider_name`: Name of the insider (director/promoter)
- `insider_designation`: Role (Director, Promoter, etc.)
- `transaction_type`: BUY, SELL, PLEDGE, REVOKE
- `quantity`: Number of shares traded
- `price_per_share`: Transaction price
- `transaction_date`: Date of transaction
- `intimation_date`: Date disclosed to exchange

### BulkDeal
- `client_name`: Name of the entity
- `deal_type`: BUY or SELL
- `quantity`: Shares traded
- `price_per_share`: Deal price
- `deal_date`: Transaction date
- `exchange`: NSE or BSE

### BlockDeal
Similar to BulkDeal but for larger institutional transactions.

### CorporateAction
- `action_type`: DIVIDEND, BONUS, SPLIT, RIGHTS, BUYBACK, etc.
- `description`: Full description
- `ex_date`: Ex-date for the action
- `record_date`: Record date
- `payment_date`: Payment/distribution date
- `dividend_amount`: Amount per share (for dividends)
- `bonus_ratio`: Ratio (for bonus issues)
- `split_ratio`: Ratio (for stock splits)

### PromoterHolding
- `quarter_end_date`: Quarter ending date
- `promoter_holding`: Promoter holding percentage
- `promoter_pledged`: Pledged shares percentage
- `public_holding`: Public holding percentage
- `fii_holding`: Foreign institutional investor holding
- `dii_holding`: Domestic institutional investor holding

## Data Sources

### Primary Sources
1. **NSE (National Stock Exchange)** - Official API
   - Insider trading data
   - Bulk/block deals
   - Corporate announcements
   - Shareholding patterns

2. **BSE (Bombay Stock Exchange)** - Official website
   - Alternative source for all event types

### Fallback Sources
- Screener.in
- Investing.com
- Money Control

## Automation

### Celery Tasks (Future Enhancement)
Add to `celery.py` for automated fetching:

```python
@app.task
def fetch_daily_stock_events():
    """Fetch stock events daily for all holdings"""
    from portfolio.models import Holding
    from portfolio.stock_events_fetcher import StockEventFetcher
    
    fetcher = StockEventFetcher()
    holdings = Holding.objects.select_related('stock').all()
    
    for holding in holdings:
        events = fetcher.fetch_all_events_for_stock(holding.stock.symbol)
        # Save to database
        ...
```

### Schedule in Celery Beat
```python
app.conf.beat_schedule = {
    'fetch-stock-events-daily': {
        'task': 'portfolio.tasks.fetch_daily_stock_events',
        'schedule': crontab(hour=18, minute=0),  # 6 PM IST daily
    },
}
```

## Admin Interface

Access admin panel to manage events:
```
http://localhost:8000/admin/portfolio/
```

Available models:
- Portfolio
- Holding
- InsiderTrade
- BulkDeal
- BlockDeal
- CorporateAction
- PromoterHolding
- ShareholdingPattern

## Event Analysis

### Insider Trading Signals
- **Buying by promoters/directors**: Generally positive signal
- **Heavy selling**: May indicate concerns
- **Pledging of shares**: Risk indicator

### Bulk/Block Deals
- **Institutional buying**: Positive sentiment
- **FII accumulation**: Long-term bullish
- **Promoter selling**: Requires attention

### Corporate Actions
- **Regular dividends**: Sign of profitability
- **Bonus issues**: Often precedes price adjustment
- **Stock splits**: Makes shares more accessible
- **Buybacks**: Company confidence in own stock

### Promoter Holdings
- **Increasing**: Strong confidence
- **Decreasing**: May indicate concerns or fund raising
- **High pledging**: Risk factor
- **Decreasing pledge**: Improving financial health

## Troubleshooting

### No Data Fetched
1. Check internet connection
2. Verify NSE website is accessible
3. Check Django logs for API errors
4. Try alternative date ranges

### Rate Limiting
NSE may rate limit requests. Recommended:
- Add delays between requests
- Fetch during non-market hours
- Use caching for frequent queries

### Missing Events
- Some stocks may not have recent events
- Check if stock symbol is correct
- Verify stock is actively traded

## Best Practices

1. **Regular Fetching**: Run fetch command daily after market hours
2. **Monitor Holdings**: Focus on events for your portfolio stocks
3. **Set Alerts**: Configure notifications for critical events
4. **Historical Analysis**: Track trends over quarters
5. **Combine with News**: Correlate events with news articles

## Example Workflow

```bash
# Morning: Add new stocks to portfolio
python manage.py shell
>>> from portfolio.models import Portfolio, Holding
>>> from news.models import Stock
>>> portfolio = Portfolio.objects.first()
>>> reliance = Stock.objects.get(symbol='RELIANCE')
>>> Holding.objects.create(portfolio=portfolio, stock=reliance, quantity=100, avg_price=2450.00)

# Evening: Fetch events
python manage.py fetch_stock_events --holdings-only

# View events in browser
# http://localhost:8000/portfolio/stock/RELIANCE/events/

# Check insider trades
python manage.py shell
>>> from portfolio.models import InsiderTrade
>>> InsiderTrade.objects.filter(stock__symbol='RELIANCE').count()
>>> latest = InsiderTrade.objects.filter(stock__symbol='RELIANCE').first()
>>> print(f"{latest.insider_name} {latest.transaction_type} {latest.quantity} shares")
```

## Future Enhancements

- [ ] Real-time event notifications
- [ ] Email/SMS alerts for significant events
- [ ] Event-based recommendation engine
- [ ] Historical event impact analysis
- [ ] Integration with technical analysis
- [ ] Custom event filters and queries
- [ ] Export events to CSV/Excel
- [ ] Mobile app integration

## Support

For issues or questions:
1. Check Django logs: `tail -f logs/django.log`
2. Review NSE API documentation
3. Check GitHub issues
4. Contact support team

## Data Refresh Schedule

- **Insider Trades**: Daily at 6 PM
- **Bulk/Block Deals**: Daily at 6 PM
- **Corporate Actions**: Weekly
- **Promoter Holdings**: Quarterly + on-demand

## Performance Tips

1. Use `--holdings-only` to limit API calls
2. Fetch specific event types when needed
3. Use database indexing for faster queries
4. Cache frequently accessed data
5. Run during non-peak hours

---

**Last Updated**: November 30, 2025
**Version**: 1.0.0
