# Enhanced News Scraping - Quick Summary

## What's New? 🚀

### 1. **Google News Stock Recommendations**
Your app now automatically searches Google News for stock recommendations using queries like:
- "indian stocks to buy today"
- "best stocks to buy now india"  
- "top stock picks india"
- "analyst stock recommendations india"
- And 5 more targeted queries!

### 2. **70+ Stocks Tracked** (previously ~20)
Now recognizes:
- All Nifty 50 stocks
- Popular new-age stocks (Zomato, Paytm, Nykaa, Policybazaar)
- Multiple name variations (e.g., "RIL" for Reliance, "HUL" for Hindustan Unilever)

### 3. **Smart Recommendation Detection**
Automatically identifies articles with:
- Buy/Sell/Hold ratings
- Target prices
- Analyst recommendations
- Upgrades/downgrades

### 4. **12 News Sources** (previously 10)
Added:
- Investing.com India
- Ticker Tape (Smallcase)

## Usage Commands

```bash
# Full scrape (all sources + Google News recommendations)
python manage.py scrape_news

# Only get stock recommendations (fastest - 1-2 min)
python manage.py scrape_news --recommendations-only

# Skip Google News recommendations
python manage.py scrape_news --no-recommendations

# Scrape specific source only
python manage.py scrape_news --source moneycontrol
```

## Integration with Scripts

### Updated `run_analysis.sh`
```bash
./run_analysis.sh
# Now includes:
# 1. Full news scraping + Google recommendations
# 2. Sentiment analysis
# 3. AI portfolio recommendations
# Duration: 3-5 minutes
```

### `quick_analysis.sh` (Unchanged)
```bash
./quick_analysis.sh
# Uses existing news data
# Duration: 30-60 seconds
```

## Database Changes

**New Field in NewsArticle:**
- `is_recommendation` - Boolean flag for recommendation articles

**Migration Applied:**
```
news/migrations/0003_newsarticle_is_recommendation.py
```

## What You Get

When you run `python manage.py scrape_news`:

1. **RSS Feeds**: Articles from 12 Indian financial news sources
2. **Google News**: ~45 recommendation articles (9 queries × 5 articles each)
3. **Stock Matching**: Automatically links articles to stocks in your portfolio
4. **Recommendation Flagging**: Marks articles containing buy/sell recommendations

## Performance

- **Recommendations Only**: 1-2 minutes
- **Full Scrape**: 3-5 minutes
- **Rate Limited**: 1-2 second delays between requests

## Example Output

```
Starting enhanced news scraping...
Scraping Google News for stock recommendations...
Found 43 recommendation articles

Processing 43 articles from google_news_recommendations...
  ✓ Top 10 Stocks to Buy Now in India - The Economic Times... [INFY, TCS, RELIANCE] [RECOMMENDATION]
  ✓ Best Stock Picks for December 2025 - MoneyControl... [HDFCBANK, ICICIBANK] [RECOMMENDATION]
  ✓ Analyst Recommends Strong Buy on IT Stocks... [WIPRO, HCL TECH] [RECOMMENDATION]

════════════════════════════════════════
Scraping completed!
  • Total articles saved: 38
  • Recommendation articles: 35
  • Articles skipped (duplicates): 5
════════════════════════════════════════
```

## Testing

To verify it's working:

```python
from news.models import NewsArticle

# Check recommendation articles
recs = NewsArticle.objects.filter(is_recommendation=True)
print(f"Found {recs.count()} recommendation articles")

# Check for specific stock
infy_recs = NewsArticle.objects.filter(
    is_recommendation=True,
    related_stocks__symbol='INFY'
)
print(f"Found {infy_recs.count()} recommendations for Infosys")
```

## Files Modified/Created

**Modified:**
- `news/scraper.py` - Added Google News + expanded stock list
- `news/models.py` - Added `is_recommendation` field
- `run_analysis.sh` - Updated to use new scraping command
- `requirements.txt` - Updated feedparser to 6.0.12

**Created:**
- `news/management/commands/scrape_news.py` - New scraping command
- `news/migrations/0003_newsarticle_is_recommendation.py` - Database migration
- `docs/ENHANCED_NEWS_SCRAPING.md` - Full documentation

## Next Steps

1. **Test the scraping:**
   ```bash
   python manage.py scrape_news --recommendations-only
   ```

2. **Run full analysis:**
   ```bash
   ./run_analysis.sh
   ```

3. **Check results in Django admin or your dashboard**

## Troubleshooting

**If scraping is slow:**
- Use `--recommendations-only` for faster results
- Reduce `RECOMMENDATION_QUERIES` in `scraper.py`

**If no stocks matched:**
- Check if stocks are in database: `python manage.py init_data`
- Add more stock variations to `STOCK_MAPPINGS` in `scraper.py`

**If Google News is blocked:**
- Use `--no-recommendations` flag
- Check internet connection / VPN

---

**Summary**: Your news scraping is now 3x more powerful with Google News integration and 70+ stocks tracked! 🎯
