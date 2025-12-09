# Quick Deploy to Render.com

Follow these steps to deploy in **5 minutes**:

## 1. Push to GitHub

```bash
git init
git add .
git commit -m "Ready for deployment"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

## 2. Create Render Account

- Go to https://render.com
- Click "Get Started" → Sign up with GitHub
- Authorize Render to access your repositories

## 3. Create PostgreSQL Database

1. Click "New +" → "PostgreSQL"
2. Settings:
   - **Name**: `stock-news-ai-db`
   - **Database**: `stocknews`
   - **User**: `stocknews`
   - **Region**: Choose closest to you
   - **Instance Type**: **Free**
3. Click "Create Database"
4. **Copy** the "Internal Database URL" (starts with `postgres://`)

## 4. Create Redis Instance

1. Click "New +" → "Redis"
2. Settings:
   - **Name**: `stock-news-ai-redis`
   - **Region**: Same as database
   - **Instance Type**: **Free**
3. Click "Create Redis"
4. **Copy** the "Internal Redis URL" (starts with `redis://`)

## 5. Create Web Service

1. Click "New +" → "Web Service"
2. Click "Connect Repository" → Select your GitHub repo
3. Settings:
   - **Name**: `stock-news-ai` (or any name)
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: **Python 3**
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command**:
     ```bash
     gunicorn stock_news_ai.wsgi:application --bind 0.0.0.0:$PORT
     ```
   - **Instance Type**: **Free**

4. Click "Advanced" → Add Environment Variables:
   ```
   SECRET_KEY = django-insecure-CHANGE-THIS-TO-RANDOM-STRING-xyz123
   DEBUG = False
   ALLOWED_HOSTS = .onrender.com
   DATABASE_URL = (paste PostgreSQL Internal URL from step 3)
   REDIS_URL = (paste Redis Internal URL from step 4)
   GEMINI_API_KEY = your-gemini-key-if-you-have-one
   PYTHON_VERSION = 3.11.0
   ```

5. Click "Create Web Service"

## 6. Wait for Deployment

- First deployment takes **5-10 minutes**
- Watch the logs in real-time
- When you see "Build successful" and "Deploy live", it's ready!

## 7. Create Superuser

After successful deployment:

1. Go to your Render dashboard
2. Click on your web service → "Shell" tab
3. Run these commands:
   ```bash
   python manage.py createsuperuser
   ```
4. Enter username, email, password

## 8. (Optional) Add Celery Worker

For background tasks:

1. Click "New +" → "Background Worker"
2. Connect same repository
3. Settings:
   - **Name**: `stock-news-ai-worker`
   - **Region**: Same as others
   - **Runtime**: **Python 3**
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     celery -A stock_news_ai worker --loglevel=info
     ```
4. Add same environment variables as web service
5. Click "Create Background Worker"

## 9. Access Your App

Your app will be available at:
```
https://stock-news-ai.onrender.com
```
(or whatever name you chose)

Admin panel:
```
https://stock-news-ai.onrender.com/admin
```

## 10. Keep App Awake (Optional)

Free tier apps sleep after 15 minutes of inactivity.

To keep it awake:
1. Go to https://uptimerobot.com (free)
2. Add Monitor → HTTP(s)
3. URL: Your Render app URL
4. Monitoring interval: 5 minutes

---

## 🎉 Done!

Your app is now live and accessible worldwide!

### Next Steps:
- [ ] Generate entry signals: Shell → `python manage.py generate_entry_signals`
- [ ] Scrape news: Shell → `python manage.py scrape_news`
- [ ] Set up custom domain (Render supports this)
- [ ] Configure scheduled tasks (Render Cron Jobs - free)

---

## 📱 Quick Commands via Render Shell

```bash
# Create admin user
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Generate entry signals
python manage.py generate_entry_signals

# Fetch stock events
python manage.py fetch_stock_events --event-type promoter --symbol RELIANCE

# Scrape news
python manage.py scrape_news
```

---

## 🐛 Troubleshooting

### App not loading?
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure DATABASE_URL and REDIS_URL are correct

### Static files missing?
- Re-run build command
- Check STATIC_ROOT in settings.py

### Database errors?
- Verify DATABASE_URL is the **Internal** URL (not External)
- Check database is in same region as web service

---

**Total Time**: ~5-10 minutes ⚡
**Cost**: $0 💰
**Result**: Live production app! 🚀
