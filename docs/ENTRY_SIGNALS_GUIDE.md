# Entry Signals Guide

## Overview
The Entry Signals feature helps identify ideal entry points for buying stocks based on various market events and opportunities.

## Signal Types

### 1. Price Dips (5-7%)
**When to use**: Good entry opportunity after recent price corrections
- Detects stocks that have dipped 5-7% in the last 7 days
- Based on negative news sentiment analysis
- **Signal Strength**: 
  - STRONG: 7%+ dip
  - MODERATE: 5-7% dip

### 2. New Orders/Contracts
**When to use**: Revenue growth catalyst
- Detects major order wins and contract awards
- Scans news for keywords: order, contract, won, awarded, bagged, deal
- **Signal Strength**:
  - STRONG: Major/significant orders mentioned
  - MODERATE: Regular order wins

### 3. Dividend Announcements
**When to use**: Income + capital appreciation opportunity
- Tracks corporate dividend announcements
- Best to enter before ex-dividend date
- **Signal Strength**:
  - STRONG: Dividend > ₹10/share
  - MODERATE: Dividend ₹5-10/share
  - WEAK: Dividend < ₹5/share

### 4. Expansion/Acquisition News
**When to use**: Long-term growth potential
- Detects expansion plans, new facilities, acquisitions, mergers
- Scans for keywords: expansion, acquisition, merger, plant, capacity
- **Signal Strength**:
  - STRONG: Major/massive expansions
  - MODERATE: Regular expansions

### 5. Stock Splits
**When to use**: Increased liquidity and accessibility
- Tracks stock split announcements
- Enter before record date for split eligibility
- **Signal Strength**: Always STRONG

### 6. Bonus Issues
**When to use**: Free shares opportunity
- Tracks bonus share announcements
- Enter before record date to receive bonus shares
- **Signal Strength**: Always STRONG

## Usage

### Generate Signals Manually
```bash
python manage.py generate_entry_signals
```

### Auto-Generated on Startup
Entry signals are automatically generated when you run:
```bash
./start_system.sh
```

### View Signals
1. Navigate to Trading Signals page: `/trading-signals/`
2. Scroll to "Entry Opportunities" section
3. Signals are grouped by type with cards showing:
   - Stock symbol
   - Signal strength badge
   - Description
   - Price at signal (if available)
   - Expiry date

### Admin Panel
View and manage all entry opportunities in Django admin:
```
http://localhost:9000/admin/portfolio/entryopportunity/
```

## Signal Expiry
- **Price Dips**: 7 days validity
- **Order Wins**: 14 days validity
- **Dividends**: Until ex-date
- **Expansions**: 30 days validity
- **Splits/Bonus**: Until record date (typically 45 days)

Expired signals are automatically deactivated during signal generation.

## Database Schema

### EntryOpportunity Model
```python
- stock: ForeignKey to Stock
- opportunity_type: PRICE_DIP, ORDER_WIN, DIVIDEND, EXPANSION, SPLIT, BONUS
- signal_date: Date when signal was generated
- signal_strength: STRONG, MODERATE, WEAK
- price_at_signal: Price when signal was detected
- percentage_change: For price dips (-5% to -10%)
- description: Human-readable explanation
- is_active: Boolean flag
- expires_at: When signal expires
```

## Integration with Trading Signals

Entry Signals complement the existing trading signals:

1. **Trading Signals** (holdings-based):
   - FII holding increased
   - Promoter holding increased
   - Top 50 stocks dipped
   - Promoter holding decreased (sell)

2. **Entry Signals** (event-based):
   - Price dips
   - Corporate actions
   - Major announcements
   - Market events

Together they provide comprehensive buy/sell guidance.

## Best Practices

1. **Combine Multiple Signals**: Look for stocks with multiple positive entry signals
2. **Check Fundamentals**: Verify company fundamentals before entry
3. **Risk Management**: Use appropriate position sizing
4. **Expiry Awareness**: Act before signals expire
5. **Cross-Reference**: Compare with promoter/FII holdings data

## Disclaimer

Entry signals are automated based on historical data and news analysis. Always:
- Do your own research
- Consult with a financial advisor
- Consider your risk appetite
- Diversify your portfolio
- Never invest based solely on automated signals
