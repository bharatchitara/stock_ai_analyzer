# Analysis Scripts - Summary

## ✅ Created Files

### 1. Scripts
- **`quick_analysis.sh`** - Fast daily portfolio analysis (~30 sec)
- **`run_analysis.sh`** - Complete analysis with news collection (~3-5 min)

### 2. Documentation  
- **`docs/ANALYSIS_SCRIPTS.md`** - Main guide comparing both scripts
- **`docs/RUN_ANALYSIS_GUIDE.md`** - Detailed guide for run_analysis.sh
- **`README.md`** - Updated with quick commands

## 🎯 Usage

### For Daily Use (Recommended)
```bash
./quick_analysis.sh
```

This runs:
1. Stock price updates
2. News sentiment analysis (pending articles)
3. Portfolio AI analysis with BUY/SELL/HOLD recommendations

**Perfect for:** Daily morning checks, quick updates before trading

### For Weekly Deep Analysis
```bash
./run_analysis.sh
```

This runs:
1. News collection from sources (scraping)
2. Sentiment analysis on all new articles
3. Stock recommendations generation
4. Stock price updates
5. Portfolio AI analysis

**Perfect for:** Weekly reviews, getting fresh news data

## 📊 What You Get

Both scripts provide:
- ✅ Updated stock prices from Yahoo Finance/NSE
- ✅ AI-powered news sentiment analysis
- ✅ BUY/SELL/HOLD recommendations with confidence scores
- ✅ Risk level assessment (HIGH/MEDIUM/LOW)
- ✅ Target prices and stop losses
- ✅ Technical analysis (trends, support/resistance)
- ✅ News summary per stock

## 🔗 View Results

After running either script, visit:
- http://localhost:9150/portfolio/ - Click "AI Analysis" button
- http://localhost:9150/portfolio/analytics/ - Charts and metrics
- http://localhost:9150/news/ - News articles

## 💡 Key Differences

| Feature | quick_analysis.sh | run_analysis.sh |
|---------|-------------------|-----------------|
| Speed | ⚡ 30-60 sec | 🔄 3-5 min |
| News Scraping | ❌ No | ✅ Yes |
| Dependencies | Minimal | Full (feedparser, etc.) |
| Use Case | Daily | Weekly |

## 🚀 Getting Started

1. **Make sure Django server is running:**
   ```bash
   python manage.py runserver 9150
   ```

2. **Run quick analysis:**
   ```bash
   ./quick_analysis.sh
   ```

3. **View results in browser:**
   - Open http://localhost:9150/portfolio/
   - Click "AI Analysis" button

## 📝 Notes

- Both scripts automatically activate the virtual environment
- Errors in one step don't stop subsequent steps
- Full colored output shows progress and results
- All analysis is based on existing news + live price data
- AI uses Google Gemini (configured in your .env)

## 🔧 Troubleshooting

If you get errors:
1. Make sure Django server is running
2. Check that .env has GEMINI_API_KEY
3. Install missing packages: `pip install -r requirements.txt`
4. For run_analysis.sh: `pip install feedparser beautifulsoup4`

## 📚 More Information

- Detailed usage: [docs/ANALYSIS_SCRIPTS.md](./ANALYSIS_SCRIPTS.md)
- Full guide: [docs/RUN_ANALYSIS_GUIDE.md](./RUN_ANALYSIS_GUIDE.md)
