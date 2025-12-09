import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_news_ai.settings')

app = Celery('stock_news_ai')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Celery Beat Schedule for automated tasks
app.conf.beat_schedule = {
    'collect-morning-news': {
        'task': 'news.tasks.collect_morning_news',
        'schedule': crontab(hour=6, minute=0),  # Run at 6:00 AM IST daily
    },
    'analyze-collected-news': {
        'task': 'news.tasks.analyze_news_batch',
        'schedule': crontab(hour=7, minute=30),  # Run at 7:30 AM IST daily
    },
    'generate-recommendations': {
        'task': 'news.tasks.generate_daily_recommendations',
        'schedule': crontab(hour=8, minute=30),  # Run at 8:30 AM IST daily
    },
    'fetch-holdings-news-every-6-hours': {
        'task': 'news.tasks.fetch_holdings_news',
        'schedule': crontab(minute=0, hour='*/6'),  # Run every 6 hours
    },
    'cleanup-old-data': {
        'task': 'news.tasks.cleanup_old_data',
        'schedule': crontab(hour=23, minute=0),  # Run at 11:00 PM IST daily
    },
}

app.conf.timezone = 'Asia/Kolkata'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')