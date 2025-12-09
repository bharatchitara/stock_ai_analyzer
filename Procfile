web: gunicorn stock_news_ai.wsgi --log-file -
worker: celery -A stock_news_ai worker --loglevel=info
beat: celery -A stock_news_ai beat --loglevel=info
