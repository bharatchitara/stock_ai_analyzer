# Run Analysis Script - Usage Guide

## Overview
The `run_analysis.sh` script performs comprehensive stock market analysis on-demand, including:
- News collection from multiple sources
- AI-powered sentiment analysis
- Stock recommendations generation
- Portfolio analysis with AI insights
- Stock price updates

## Quick Start

### Run Complete Analysis
```bash
./run_analysis.sh
```

This will execute all 5 steps automatically:
1. **News Collection** - Scrapes latest news from configured sources
2. **Sentiment Analysis** - Analyzes news sentiment using AI
3. **Recommendations** - Generates BUY/SELL/HOLD recommendations
4. **Price Updates** - Fetches current stock prices
5. **Portfolio Analysis** - Analyzes your holdings with AI

## When to Use

### Daily Analysis
- Run before market hours (before 9:15 AM IST)
- Run after market close (after 3:30 PM IST)
- Run anytime for updated insights

### Event-Driven
- After major market news
- Before making investment decisions
- When reviewing portfolio performance

## Output

The script provides colored output:
- 🔵 **Blue** - Section headers and info
- 🟢 **Green** - Success messages
- 🟡 **Yellow** - Progress indicators
- 🔴 **Red** - Errors (script continues despite errors)

## What Each Step Does

### Step 1: News Collection
- Scrapes news from Economic Times, Moneycontrol, Business Standard, etc.
- Extracts stock mentions
- Saves articles to database
- Skips duplicates automatically

### Step 2: Sentiment Analysis
- Analyzes last 7 days of pending articles
- Uses AI to determine POSITIVE/NEGATIVE/NEUTRAL sentiment
- Limits to 50 most recent articles per run
- Updates article records in database

### Step 3: Generate Recommendations
- Analyzes stocks with recent news
- Generates BUY/SELL/HOLD recommendations
- Considers sentiment, price trends, and news impact
- Limits to top 20 stocks per run

### Step 4: Update Stock Prices
- Fetches current prices from Yahoo Finance/NSE
- Updates all stocks in portfolio
- Timeout: 10 seconds per stock
- Continues on individual failures

### Step 5: Portfolio Analysis
- Runs AI analysis on all portfolio holdings
- Calculates risk levels
- Provides confidence scores
- Generates target prices and stop losses

## View Results

After running the script:

1. **Portfolio Dashboard**: http://localhost:9150/portfolio/
   - Click "AI Analysis" button for detailed insights
   - View comprehensive analysis with tabs

2. **News Page**: http://localhost:9150/news/
   - Browse collected news articles
   - Filter by sentiment, stock, category

3. **Analytics**: http://localhost:9150/portfolio/analytics/
   - View sector allocation
   - Check top gainers/losers
   - See P&L distribution

## Requirements

- Django server must be running (`python manage.py runserver 9150`)
- Virtual environment must be activated (script does this automatically)
- Internet connection for news scraping and price fetching
- API keys configured in `.env`:
  - `GEMINI_API_KEY` (for AI analysis)
  - `OPENAI_API_KEY` (optional, fallback)

## Troubleshooting

### Script Won't Run
```bash
# Make sure it's executable
chmod +x run_analysis.sh

# Run with bash explicitly
bash run_analysis.sh
```

### Django Not Found
```bash
# Install requirements
source .venv/bin/activate
pip install -r requirements.txt
```

### News Collection Fails
- Check internet connection
- Verify news source websites are accessible
- Some sources may be temporarily down (script continues)

### API Rate Limits
- Google Gemini: 15 requests/minute free tier
- If hit, analysis continues with available data
- Wait a minute and run again

### No Portfolio Found
- Import your portfolio first via Dashboard
- Use CSV import, JSON import, or image import
- Add stocks manually if needed

## Advanced Usage

### Run Only Specific Steps

You can modify the script to run only certain steps by commenting out sections:

```bash
# Edit run_analysis.sh and comment out unwanted steps
nano run_analysis.sh
```

### Schedule Automatic Runs

Add to crontab for automatic daily analysis:
```bash
# Edit crontab
crontab -e

# Add line for 6:00 AM daily (replace /path/to with your actual path)
0 6 * * * /path/to/projectBuff/run_analysis.sh >> /path/to/projectBuff/analysis.log 2>&1
```

### Integration with start_system.sh

The `start_system.sh` already runs scheduled tasks. Use `run_analysis.sh` for:
- Manual on-demand analysis
- Testing before automation
- Quick updates between scheduled runs

## Performance

Typical execution time (depends on portfolio size and internet speed):
- News Collection: 1-2 minutes
- Sentiment Analysis: 30-60 seconds (50 articles)
- Recommendations: 30-45 seconds (20 stocks)
- Price Updates: 15-30 seconds (all portfolio stocks)
- Portfolio Analysis: 20-40 seconds (per 10 holdings)

**Total**: ~3-5 minutes for complete analysis

## Tips

1. **Run during market hours** for real-time price updates
2. **Run before market** (7-9 AM) for morning insights
3. **Run after market** (4-6 PM) for day review
4. **Keep Django server running** in separate terminal
5. **Check logs** if any step fails repeatedly

## Comparison with start_system.sh

| Feature | run_analysis.sh | start_system.sh |
|---------|----------------|-----------------|
| Purpose | On-demand analysis | Full system startup |
| Duration | 3-5 minutes | Runs continuously |
| Celery | Not required | Required |
| Redis | Not required | Required |
| Scheduling | Manual only | Automated (6 AM, 7:30 AM, 8:30 AM) |
| Use Case | Quick updates | Daily automation |

## Support

For issues or questions:
1. Check Django logs: Server terminal output
2. Check script output for specific errors
3. Verify all requirements are installed
4. Ensure API keys are configured

## Version
v1.0.0 - Initial release
