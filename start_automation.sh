#!/bin/bash
# Auto-start script for Stock Market News AI
# Runs daily at 5:55 AM to prepare for 6:00 AM collection

# Navigate to project directory (script's directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Start Redis (if not running)
if ! pgrep -x "redis-server" > /dev/null; then
    redis-server &
fi

# Start Django server
python manage.py runserver &
DJANGO_PID=$!

# Start Celery worker
celery -A stock_news_ai worker --loglevel=info &
WORKER_PID=$!

# Start Celery beat (scheduler)
celery -A stock_news_ai beat --loglevel=info &
BEAT_PID=$!

echo "Stock Market News AI started successfully!"
echo "Django PID: $DJANGO_PID"
echo "Worker PID: $WORKER_PID" 
echo "Beat PID: $BEAT_PID"

# Keep running until 10 AM (4 hours)
sleep 14400

# Cleanup
kill $DJANGO_PID $WORKER_PID $BEAT_PID
echo "Stock Market News AI stopped."