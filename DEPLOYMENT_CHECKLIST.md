# Deployment Checklist ✅

## Pre-Deployment

- [ ] All code committed to Git
- [ ] `.env` file is in `.gitignore` (never commit secrets!)
- [ ] `requirements.txt` is up to date
- [ ] `Procfile` exists
- [ ] `runtime.txt` specifies Python version
- [ ] Database migrations are up to date
- [ ] Static files configured correctly

## Files Created for Deployment

- [x] `Procfile` - Tells platform how to run app
- [x] `runtime.txt` - Specifies Python 3.11.9
- [x] Updated `requirements.txt` - Added deployment packages
- [x] Updated `settings.py` - Production settings
- [x] `DEPLOYMENT_GUIDE.md` - Complete guide
- [x] `QUICK_DEPLOY_RENDER.md` - 5-minute Render guide

## Environment Variables to Set

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False  
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgres://...
REDIS_URL=redis://...
GEMINI_API_KEY=your-key (optional)
```

## Platform Choice

Choose one:

1. ✅ **Render.com** (RECOMMENDED)
   - Free PostgreSQL + Redis
   - Easy setup
   - Auto-deploy on push
   - Follow: `QUICK_DEPLOY_RENDER.md`

2. **Railway.app**
   - $5 free credit/month
   - Always-on
   - Follow: `DEPLOYMENT_GUIDE.md` → Railway section

3. **PythonAnywhere**
   - Always-on
   - No Celery support
   - Follow: `DEPLOYMENT_GUIDE.md` → PythonAnywhere section

4. **Fly.io**
   - Requires credit card
   - Global CDN
   - Follow: `DEPLOYMENT_GUIDE.md` → Fly.io section

## After Deployment

- [ ] App loads without errors
- [ ] Admin panel accessible
- [ ] Create superuser
- [ ] Run `python manage.py generate_entry_signals`
- [ ] Run `python manage.py scrape_news`
- [ ] Test all major features
- [ ] Set up monitoring (UptimeRobot)
- [ ] Configure custom domain (optional)

## Testing Locally with Production Settings

```bash
# Test with DEBUG=False
export DEBUG=False
export ALLOWED_HOSTS=localhost,127.0.0.1
export SECRET_KEY=test-secret-key

# Collect static files
python manage.py collectstatic --noinput

# Run with gunicorn
gunicorn stock_news_ai.wsgi:application

# Visit http://localhost:8000
```

## Quick Deploy Steps (Render.com)

1. Push to GitHub
2. Create Render account
3. Create PostgreSQL database
4. Create Redis instance
5. Create web service (connect GitHub repo)
6. Add environment variables
7. Deploy automatically
8. Create superuser via Shell
9. Done! 🎉

**Time**: 5-10 minutes
**Cost**: $0

## Support

- Render Docs: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/5.0/howto/deployment/
- GitHub Issues: Create issue if stuck

---

Ready to deploy? Start with: `QUICK_DEPLOY_RENDER.md`
