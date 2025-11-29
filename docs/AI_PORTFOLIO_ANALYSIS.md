# AI Portfolio Analysis Feature

## Overview
Comprehensive AI-powered portfolio analysis that provides buy/sell/hold recommendations based on multiple factors including sentiment analysis, technical indicators, news monitoring, and valuation metrics.

## Features

### 1. **Sentiment Analysis**
- Analyzes recent news articles (last 30 days) for each stock
- Calculates sentiment score from -1 (very negative) to +1 (very positive)
- Categorizes articles by sentiment: POSITIVE, NEGATIVE, NEUTRAL
- Shows sentiment distribution and summary

### 2. **Technical Analysis**
- **Trend Detection**: Identifies UPTREND, DOWNTREND, or SIDEWAYS movement
- **Moving Averages**: Calculates 20-day and 50-day moving averages
- **Support & Resistance**: Identifies key price levels
- **Momentum Indicators**: Tracks 5-day and 20-day price changes
- **Pattern Recognition**: Detects bullish/bearish momentum, golden/death cross patterns
- **Volatility Analysis**: Measures price range and volatility

### 3. **Valuation Assessment**
- Compares current price to 3-month average
- Identifies OVERVALUED, UNDERVALUED, or FAIR_VALUE status
- Calculates percentage deviation from average
- Helps identify buying/selling opportunities

### 4. **News Monitoring**
- Tracks recent news articles mentioning each stock
- Displays impact level (HIGH, MEDIUM, LOW)
- Shows article categories (EARNINGS, POLICY, MARKET, etc.)
- Links to full articles for detailed reading

### 5. **Corporate Actions Tracking**
- Monitors bulk deals
- Tracks insider trading activity
- Lists corporate actions (dividends, splits, etc.)
- Shows upcoming events

### 6. **AI Recommendations**
- **BUY**: Strong buy signals based on positive sentiment, uptrend, and undervaluation
- **SELL**: Strong sell signals based on negative sentiment, downtrend, or overvaluation
- **HOLD**: Mixed signals or neutral market conditions

Each recommendation includes:
- Confidence score (0-100%)
- Risk level (HIGH, MEDIUM, LOW)
- Target price (for buy/hold recommendations)
- Stop loss price
- Detailed reasoning

## How to Use

### From Portfolio Dashboard
1. Click the **"AI Analysis"** button
2. Wait for analysis to complete (may take 10-30 seconds)
3. Review comprehensive analysis for each holding

### Understanding Recommendations

#### BUY Signals
Generated when:
- Positive news sentiment (> 0.3)
- Stock in uptrend
- Price below 3-month average (undervalued)
- Bullish momentum detected
- Support level holding

#### SELL Signals
Generated when:
- Negative news sentiment (< -0.3)
- Stock in downtrend
- Price above 3-month average (overvalued)
- Bearish momentum detected
- Large gains (>20%) - book profits

#### HOLD Signals
Generated when:
- Mixed sentiment
- Sideways trend
- Fair valuation
- No clear momentum

### Risk Levels

- **HIGH RISK**: Downtrend + negative sentiment
- **MEDIUM RISK**: Mixed signals or neutral conditions
- **LOW RISK**: Uptrend + positive sentiment

## Analysis Components

### Portfolio Summary Dashboard
Shows at-a-glance metrics:
- Total buy recommendations
- Total sell recommendations
- Total hold recommendations
- High-risk holdings count
- Positive sentiment count
- Negative sentiment count

### Per-Stock Analysis
Each holding displays:

#### 1. Header Section
- Stock symbol and name
- Quantity, average price, current price
- P&L (absolute and percentage)
- Recommendation badge (BUY/SELL/HOLD)
- Risk level badge
- Confidence score
- Target price and stop loss

#### 2. AI Reasoning
Detailed explanation of why the recommendation was made, including:
- News sentiment factors
- Valuation assessment
- Technical signals
- P&L considerations

#### 3. News & Sentiment Tab
- Sentiment score visualization
- News summary
- List of recent articles with sentiment badges
- Publication dates

#### 4. Technical Analysis Tab
- Current trend (UPTREND/DOWNTREND)
- Moving averages (20-day, 50-day)
- Support and resistance levels
- Technical signal badges
- 5-day and 20-day price changes

#### 5. Valuation Tab
- Valuation status (OVERVALUED/UNDERVALUED/FAIR_VALUE)
- Current price
- 3-month average price
- Deviation percentage
- Interpretation and guidance

## Scoring System

The AI uses a multi-factor scoring system:

### Buy Score Factors (+points)
- Positive sentiment (> 0.3): +2
- Uptrend: +2
- Bullish momentum: +1
- Undervalued: +2
- Loss position with positive outlook: +1

### Sell Score Factors (+points)
- Negative sentiment (< -0.3): +2
- Downtrend: +2
- Bearish momentum: +1
- Overvalued: +2
- Large gains (>20%): +1
- Significant loss (<-10%) with negative outlook: +1

### Decision Thresholds
- BUY: Buy score > Sell score AND Buy score >= 4
- SELL: Sell score > Buy score AND Sell score >= 4
- HOLD: All other cases

## Data Sources

- **Stock Prices**: Yahoo Finance (3 months historical data)
- **News Articles**: Internal database (last 30 days)
- **Sentiment**: Pre-calculated sentiment from news analysis
- **Technical Indicators**: Calculated from price data

## Best Practices

1. **Run Analysis Regularly**: Weekly or after major market events
2. **Consider Multiple Factors**: Don't rely on a single metric
3. **Use Stop Losses**: Always set stop losses to manage risk
4. **Review News**: Read the actual news articles before acting
5. **Monitor Trends**: Watch for trend changes and pattern shifts
6. **Portfolio Balance**: Don't act on all recommendations at once
7. **Risk Management**: Pay attention to risk levels

## Limitations

- Analysis is based on historical data and news
- Cannot predict unexpected events or black swan events
- Market conditions can change rapidly
- Recommendations are suggestions, not financial advice
- Always do your own research before investing

## Future Enhancements

Potential improvements:
- Integration with live NSE/BSE data for corporate actions
- Real-time news scraping
- More advanced chart patterns (head & shoulders, triangles, etc.)
- Machine learning models for price prediction
- Sector-wide analysis and comparison
- Portfolio optimization suggestions
- Risk-adjusted return calculations
- Backtesting of recommendations
