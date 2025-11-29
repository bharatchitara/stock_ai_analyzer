# Analysis Scripts - Quick Reference

## Available Scripts

### 1. `quick_analysis.sh` ⚡ (Recommended)
**Fast portfolio analysis with existing news data**

```bash
./quick_analysis.sh
```

**What it does:**
- ✅ Updates stock prices (Yahoo Finance/NSE)
- ✅ Analyzes pending news sentiment (AI)
- ✅ Runs portfolio AI analysis
- ✅ Shows BUY/SELL/HOLD recommendations

**Duration:** ~30-60 seconds  
**Requirements:** Django server running, API keys configured

**Best for:**
- Quick daily analysis
- Before making investment decisions
- Checking portfolio performance
- Getting updated recommendations

---

### 2. `run_analysis.sh` 🔄 (Full Analysis)
**Complete analysis including news collection**

```bash
./run_analysis.sh
```

**What it does:**
- 📰 Scrapes news from multiple sources
- 🤖 AI sentiment analysis
- 💡 Stock recommendations generation
- 💰 Stock price updates  
- 📊 Portfolio AI analysis

**Duration:** ~3-5 minutes  
**Requirements:** All dependencies installed (feedparser, beautifulsoup4, etc.)

**Best for:**
- Weekly comprehensive updates
- When you need fresh news
- Complete market analysis
- Initial setup and testing

---

## Quick Start

### Daily Workflow (Recommended)

```bash
# Morning (before market hours)
./quick_analysis.sh

# View results
# Open: http://localhost:9150/portfolio/
# Click "AI Analysis" button
```

### Weekly Deep Analysis

```bash
# Install missing dependencies first (if any)
pip install feedparser beautifulsoup4 requests lxml

# Run full analysis
./run_analysis.sh
```

---

## Comparison

| Feature | quick_analysis.sh | run_analysis.sh |
|---------|-------------------|-----------------|
| **Speed** | 30-60 sec | 3-5 min |
| **News Collection** | ❌ Uses existing | ✅ Scrapes fresh |
| **Sentiment Analysis** | ✅ Yes | ✅ Yes |
| **Price Updates** | ✅ Yes | ✅ Yes |
| **Portfolio Analysis** | ✅ Yes | ✅ Yes |
| **Recommendations** | ✅ Via Portfolio | ✅ Direct + Portfolio |
| **Dependencies** | Minimal | Full (feedparser, etc.) |
| **Best For** | Daily use | Weekly/initial |

---

## View Results

After running either script:

### 1. Portfolio Dashboard
```
http://localhost:9150/portfolio/
```
- Click "AI Analysis" button for detailed insights
- View BUY/SELL/HOLD recommendations
- Check risk levels and confidence scores

### 2. Analytics Page
```
http://localhost:9150/portfolio/analytics/
```
- Sector allocation charts
- Top gainers/losers
- P&L distribution

### 3. News Page
```
http://localhost:9150/news/
```
- Browse news articles
- Filter by stock, sentiment, category

---

## Prerequisites

### Required (for both scripts)
```bash
# 1. Django server must be running
python manage.py runserver 9150

# 2. Virtual environment activated (scripts do this automatically)
source .venv/bin/activate

# 3. API keys in .env file
GEMINI_API_KEY=your_key_here
```

### Optional (for run_analysis.sh)
```bash
# Install news scraping dependencies
pip install feedparser beautifulsoup4 requests lxml
```

---

## Troubleshooting

### "Virtual environment not found"
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### "Django server not responding"
```bash
# Start server in another terminal
python manage.py runserver 9150
```

### "Module not found" errors
```bash
# Install missing packages
pip install feedparser beautifulsoup4 requests lxml google-generativeai
```

### "No portfolio found"
1. Go to http://localhost:9150/portfolio/
2. Click "Import Portfolio"
3. Upload CSV/JSON or use image import
4. Run script again

### API Rate Limits
- Gemini API: 15 requests/minute (free tier)
- If hit, wait 60 seconds and try again
- Or use smaller batches in script

---

## Automation

### Daily Auto-Run (macOS/Linux)

Add to crontab:
```bash
crontab -e
```

Add line:
```
# Run at 6 AM daily (replace /path/to with your actual path)
0 6 * * * /path/to/projectBuff/quick_analysis.sh >> /path/to/projectBuff/analysis.log 2>&1
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily 6:00 AM)
4. Action: Run `bash quick_analysis.sh`
5. Set working directory to project folder

---

## Tips

1. **Run quick_analysis.sh daily** for fast updates
2. **Run run_analysis.sh weekly** for fresh news
3. **Check during market hours** for real-time prices
4. **Review before trading** to get latest insights
5. **Keep server running** in separate terminal

---

## Examples

### Quick Morning Check
```bash
# Takes ~30 seconds
./quick_analysis.sh

# Output shows:
# ✓ Prices updated
# ✓ Analyzed 5 articles  
# ✓ Analysis Complete!
#   • BUY: 3 stocks
#   • HOLD: 8 stocks
#   • SELL: 1 stock
```

### Weekly Deep Dive
```bash
# Takes ~3-5 minutes
./run_analysis.sh

# Output shows all 5 steps:
# Step 1: Collecting Latest News (scraped 50 articles)
# Step 2: Sentiment Analysis (analyzed 30 articles)
# Step 3: Recommendations (generated 15)
# Step 4: Price Updates (updated 12 stocks)
# Step 5: Portfolio Analysis (analyzed 12 holdings)
```

---

## Support

For detailed documentation:
- `quick_analysis.sh` - Just works, no docs needed!
- `run_analysis.sh` - See [RUN_ANALYSIS_GUIDE.md](./RUN_ANALYSIS_GUIDE.md)

---

## Version History

- **v1.1** - Added quick_analysis.sh for daily use
- **v1.0** - Initial run_analysis.sh release
