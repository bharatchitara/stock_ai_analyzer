# Keep Render App Always-On Guide 🚀

Render free tier apps sleep after 15 minutes of inactivity. Here are proven methods to keep your app awake 24/7.

## Method 1: UptimeRobot (RECOMMENDED) ⭐

**Cost**: FREE  
**Setup Time**: 2 minutes  
**Effectiveness**: 99.9%

### Steps:

1. **Sign Up**
   - Go to https://uptimerobot.com
   - Create free account (50 monitors included)

2. **Create Monitor**
   - Click "Add New Monitor"
   - Monitor Type: HTTP(s)
   - Friendly Name: `Stock News AI`
   - URL: `https://your-app-name.onrender.com/health/`
   - Monitoring Interval: **5 minutes** (prevents 15-min sleep)

3. **Configure Alerts** (Optional)
   - Email: Your email
   - Get notified if app goes down

4. **Done!**
   - Your app will be pinged every 5 minutes
   - Render won't put it to sleep

### Health Check Endpoint

Already added to your app: `/health/`

Test it locally:
```bash
curl http://localhost:8000/health/
# Response: {"status": "ok", "service": "stock-news-ai"}
```

After deployment:
```bash
curl https://your-app-name.onrender.com/health/
```

---

## Method 2: Cron-job.org

**Cost**: FREE  
**Setup Time**: 2 minutes

1. Sign up at https://cron-job.org
2. Create new cronjob
3. URL: `https://your-app-name.onrender.com/health/`
4. Schedule: Every 5 minutes (`*/5 * * * *`)
5. Save

---

## Method 3: GitHub Actions (Free Alternative)

Create `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Alive

on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
  workflow_dispatch:

jobs:
  keep-alive:
    runs-on: ubuntu-latest
    steps:
      - name: Ping App
        run: |
          curl -f https://your-app-name.onrender.com/health/ || exit 1
```

**Note**: GitHub Actions cron jobs can be unreliable. Use UptimeRobot instead.

---

## Method 4: Koyeb (Alternative Free Hosting)

If you need true always-on:

1. Deploy to **Koyeb** instead (no sleep)
2. Free tier: 512MB RAM, always-on
3. Sign up at https://www.koyeb.com

---

## Method 5: Paid Render Plan

**Cost**: $7/month  
**Benefits**:
- No sleep
- More resources
- Priority support
- Background workers included

Upgrade at: https://dashboard.render.com/billing

---

## Comparison Table

| Method | Cost | Always-On | Setup Time | Reliability |
|--------|------|-----------|------------|-------------|
| **UptimeRobot** ⭐ | Free | Yes | 2 min | 99.9% |
| Cron-job.org | Free | Yes | 2 min | 99% |
| GitHub Actions | Free | Yes | 5 min | 95% |
| Koyeb Hosting | Free | Yes | 10 min | 99.9% |
| Render Paid | $7/mo | Yes | 0 min | 99.99% |

---

## Testing Your Setup

### 1. Check Health Endpoint
```bash
curl https://your-app-name.onrender.com/health/
```

Expected response:
```json
{"status": "ok", "service": "stock-news-ai"}
```

### 2. Monitor Render Logs
```bash
# In Render dashboard
Logs → Filter by "health"
```

You should see requests every 5 minutes:
```
GET /health/ HTTP/1.1" 200
```

### 3. Check Uptime
After 24 hours, your UptimeRobot dashboard will show:
- Uptime: 100%
- Response time: < 500ms

---

## Advanced: Multiple Endpoints

Ping different endpoints to keep background workers active:

```python
# In stock_news_ai/urls.py

def worker_health(request):
    """Check if Celery is running"""
    from django_celery_beat.models import PeriodicTask
    tasks = PeriodicTask.objects.filter(enabled=True).count()
    return JsonResponse({'status': 'ok', 'active_tasks': tasks})

urlpatterns = [
    # ... existing patterns
    path('health/', health_check),
    path('health/worker/', worker_health),
]
```

Then create 2 monitors in UptimeRobot:
1. `/health/` - Every 5 minutes
2. `/health/worker/` - Every 10 minutes

---

## Troubleshooting

### App Still Sleeping?

1. **Check interval**: Must be < 15 minutes
2. **Verify URL**: Test manually in browser
3. **Check Render logs**: See if pings are arriving
4. **DNS issues**: Use IP address instead of domain

### High Response Times?

Your app may still "cold start" occasionally:
- First request after deployment: 5-10 seconds
- Normal requests: < 500ms

This is normal behavior.

### Rate Limiting?

Render free tier has limits:
- 400 hours/month (16.6 days)
- With UptimeRobot: You'll use ~720 hours/month

**Solution**: The app will sleep for a few days at month-end. Acceptable for free tier.

---

## Recommended Setup (Best Practice)

1. ✅ Deploy to Render
2. ✅ Add UptimeRobot monitor (5-min interval)
3. ✅ Add Cron-job.org backup (10-min interval)
4. ✅ Set up email alerts
5. ✅ Monitor first 24 hours

**Total Cost**: $0  
**Total Time**: 5 minutes  
**Uptime**: 99%+ (free tier limitations apply)

---

## Next Steps

1. Deploy your app to Render (follow `QUICK_DEPLOY_RENDER.md`)
2. Get your app URL: `https://your-app-name.onrender.com`
3. Set up UptimeRobot with `/health/` endpoint
4. Wait 24 hours and verify uptime

**Your app will stay awake! 🎉**

---

## Resources

- UptimeRobot Docs: https://uptimerobot.com/help/
- Render Free Tier: https://render.com/docs/free
- Health Check Best Practices: https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

---

**Pro Tip**: If you need 100% uptime for a portfolio project, spend the $7/month for Render's paid tier. It's worth it for peace of mind and faster response times.
