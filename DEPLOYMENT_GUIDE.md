# Free Deployment Guide - Stock Market News AI

## 📋 Overview

This guide covers multiple **FREE** deployment options for the Stock Market News AI application.

---

## 🚀 Option 1: Render.com (RECOMMENDED - Easiest)

**Pros**: Free tier, PostgreSQL included, automatic deployments, easy setup
**Cons**: Apps sleep after 15 min inactivity (free tier)

### Steps:

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Push Code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

3. **Create Web Service**
   - Dashboard → New → Web Service
   - Connect your GitHub repository
   - Settings:
     - **Name**: stock-news-ai
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
     - **Start Command**: `gunicorn stock_news_ai.wsgi:application`
     - **Instance Type**: Free

4. **Add Environment Variables**
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=your-app-name.onrender.com
   DATABASE_URL=(auto-populated by Render)
   REDIS_URL=(will add after creating Redis)
   GEMINI_API_KEY=your-gemini-key
   ```

5. **Create PostgreSQL Database**
   - Dashboard → New → PostgreSQL
   - **Name**: stock-news-ai-db
   - **Instance Type**: Free
   - Copy the Internal Database URL

6. **Create Redis Instance**
   - Dashboard → New → Redis
   - **Name**: stock-news-ai-redis
   - **Instance Type**: Free
   - Copy the Redis URL
   - Add to environment variables

7. **Add Background Workers** (Optional - Celery)
   - Dashboard → New → Background Worker
   - **Build Command**: Same as web service
   - **Start Command**: `celery -A stock_news_ai worker --loglevel=info`
   - Add same environment variables

8. **Deploy**
   - Render will auto-deploy on git push
   - First deployment takes 5-10 minutes

**Access**: `https://your-app-name.onrender.com`

---

## 🌐 Option 2: Railway.app

**Pros**: $5 free credit/month, PostgreSQL + Redis included, no sleep
**Cons**: Credit runs out if you use too many resources

### Steps:

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy from GitHub**
   - New Project → Deploy from GitHub
   - Select your repository
   - Railway auto-detects Django

3. **Add Services**
   - Add PostgreSQL: New → Database → PostgreSQL
   - Add Redis: New → Database → Redis

4. **Configure Environment Variables**
   ```
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}
   DATABASE_URL=${{DATABASE_URL}}
   REDIS_URL=${{REDIS_URL}}
   GEMINI_API_KEY=your-key
   ```

5. **Add Build/Deploy Commands**
   - Build: `pip install -r requirements.txt`
   - Deploy: `python manage.py collectstatic --noinput && python manage.py migrate && gunicorn stock_news_ai.wsgi`

6. **Generate Domain**
   - Settings → Generate Domain

**Access**: `https://your-app.up.railway.app`

---

## ☁️ Option 3: PythonAnywhere (Limited Free)

**Pros**: Always on, no credit card needed
**Cons**: Limited to 1 web app, no background tasks on free tier, manual setup

### Steps:

1. **Create Account**
   - Go to [pythonanywhere.com](https://www.pythonanywhere.com)
   - Sign up for Beginner account (Free)

2. **Upload Code**
   ```bash
   # From Bash console on PythonAnywhere
   git clone YOUR_GITHUB_REPO_URL
   cd projectBuff
   ```

3. **Create Virtual Environment**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 stocknews
   pip install -r requirements.txt
   ```

4. **Configure Web App**
   - Web tab → Add new web app
   - Select Manual configuration (Python 3.10)
   - Source code: `/home/yourusername/projectBuff`
   - Working directory: `/home/yourusername/projectBuff`
   - Virtualenv: `/home/yourusername/.virtualenvs/stocknews`

5. **Edit WSGI File**
   ```python
   import os
   import sys
   
   path = '/home/yourusername/projectBuff'
   if path not in sys.path:
       sys.path.insert(0, path)
   
   os.environ['DJANGO_SETTINGS_MODULE'] = 'stock_news_ai.settings'
   
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

6. **Configure Static Files**
   - Web tab → Static files
   - URL: `/static/`
   - Directory: `/home/yourusername/projectBuff/staticfiles/`

7. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```

**Access**: `https://yourusername.pythonanywhere.com`

---

## 🔥 Option 4: Fly.io

**Pros**: Global edge network, PostgreSQL included
**Cons**: Requires credit card (but free tier doesn't charge)

### Steps:

1. **Install Fly CLI**
   ```bash
   brew install flyctl
   # or
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**
   ```bash
   flyctl auth login
   ```

3. **Create fly.toml**
   ```toml
   app = "stock-news-ai"
   primary_region = "sin"  # Singapore
   
   [build]
   
   [env]
     PORT = "8000"
   
   [[services]]
     http_checks = []
     internal_port = 8000
     processes = ["app"]
     protocol = "tcp"
   
     [[services.ports]]
       force_https = true
       handlers = ["http"]
       port = 80
   
     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   
   [processes]
     app = "gunicorn stock_news_ai.wsgi"
   ```

4. **Create PostgreSQL**
   ```bash
   flyctl postgres create
   flyctl postgres attach --app stock-news-ai
   ```

5. **Set Secrets**
   ```bash
   flyctl secrets set SECRET_KEY=your-secret-key
   flyctl secrets set DEBUG=False
   flyctl secrets set GEMINI_API_KEY=your-key
   ```

6. **Deploy**
   ```bash
   flyctl deploy
   ```

**Access**: `https://stock-news-ai.fly.dev`

---

## 🆓 Option 5: Heroku (Free tier removed, but GitHub Students get credits)

If you're a student, get [GitHub Student Pack](https://education.github.com/pack) for Heroku credits.

---

## 📝 Pre-Deployment Checklist

- [ ] Create `.env` file with production secrets
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up PostgreSQL database
- [ ] Set up Redis (for Celery)
- [ ] Configure `SECRET_KEY`
- [ ] Add `GEMINI_API_KEY` if using AI features
- [ ] Run `python manage.py collectstatic`
- [ ] Run `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`

---

## 🔒 Environment Variables Needed

```bash
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgres://user:pass@host:5432/dbname
REDIS_URL=redis://default:password@host:6379
GEMINI_API_KEY=your-gemini-api-key
```

---

## 🎯 Recommended: Render.com

For this application, **Render.com** is the best free option because:
- ✅ Easy setup (5 minutes)
- ✅ Free PostgreSQL + Redis
- ✅ Auto-deploy on git push
- ✅ HTTPS included
- ✅ Background workers supported
- ✅ No credit card required

---

## 🚨 Important Notes

### Free Tier Limitations:
- **Render**: Apps sleep after 15 min inactivity (30-60s wake-up time)
- **Railway**: $5 credit/month (~500 hours)
- **PythonAnywhere**: No background tasks (Celery won't work)
- **Fly.io**: Requires credit card (but won't charge on free tier)

### Solutions for "Sleeping" Apps:
1. Use **UptimeRobot** (free) to ping your app every 5 minutes
2. Upgrade to paid tier ($7-10/month for always-on)
3. Use Railway (always-on with free credits)

---

## 📊 Cost Comparison

| Platform | Free Tier | Always On? | PostgreSQL | Redis | Background Jobs |
|----------|-----------|------------|------------|-------|-----------------|
| **Render** | ✅ Yes | ❌ Sleeps | ✅ Yes | ✅ Yes | ✅ Yes |
| **Railway** | 💰 $5 credit | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **PythonAnywhere** | ✅ Yes | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Fly.io** | ✅ Yes* | ✅ Yes | ✅ Yes | ⚠️ Paid | ✅ Yes |

*Requires credit card

---

## 🎓 Next Steps

1. Choose your platform (Render recommended)
2. Push code to GitHub
3. Follow platform-specific steps above
4. Configure environment variables
5. Deploy!
6. Visit your app: `https://your-app.platform.com`

---

## 🆘 Troubleshooting

### "DisallowedHost" Error
Add your domain to `ALLOWED_HOSTS` in environment variables

### Static files not loading
Run `python manage.py collectstatic --noinput`

### Database connection errors
Check `DATABASE_URL` environment variable

### Celery not working
Ensure Redis is configured and worker process is running

---

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Render Django Guide](https://render.com/docs/deploy-django)
- [Railway Django Guide](https://docs.railway.app/guides/django)

---

## 💡 Pro Tips

1. **Use environment variables** for all secrets
2. **Never commit** `.env` file or `db.sqlite3`
3. **Test locally** with `DEBUG=False` before deploying
4. **Monitor logs** after deployment
5. **Set up error tracking** (Sentry has free tier)
6. **Use CDN** for static files (Cloudflare free tier)
7. **Backup database** regularly

---

**Need help?** Check the platform-specific documentation or create an issue on GitHub.
