#!/bin/bash
# Start all services for Stock Market News AI with automated news fetching

echo "🚀 Starting Stock Market News AI System..."
echo "=========================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis is not running. Starting Redis..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis started successfully"
    else
        echo "❌ Failed to start Redis. Please start it manually: redis-server"
        exit 1
    fi
else
    echo "✅ Redis is already running"
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $CELERY_WORKER_PID 2>/dev/null
    kill $CELERY_BEAT_PID 2>/dev/null
    kill $DJANGO_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Celery Worker in background
echo "📦 Starting Celery Worker..."
celery -A stock_news_ai worker --loglevel=info > logs/celery_worker.log 2>&1 &
CELERY_WORKER_PID=$!
sleep 3

if ps -p $CELERY_WORKER_PID > /dev/null; then
    echo "✅ Celery Worker started (PID: $CELERY_WORKER_PID)"
else
    echo "❌ Failed to start Celery Worker"
    exit 1
fi

# Start Celery Beat in background
echo "⏰ Starting Celery Beat (Scheduler)..."
celery -A stock_news_ai beat --loglevel=info > logs/celery_beat.log 2>&1 &
CELERY_BEAT_PID=$!
sleep 2

if ps -p $CELERY_BEAT_PID > /dev/null; then
    echo "✅ Celery Beat started (PID: $CELERY_BEAT_PID)"
else
    echo "❌ Failed to start Celery Beat"
    kill $CELERY_WORKER_PID
    exit 1
fi

# Start Django development server
echo "🌐 Starting Django Server..."
python manage.py runserver 9150 > logs/django.log 2>&1 &
DJANGO_PID=$!
sleep 3

if ps -p $DJANGO_PID > /dev/null; then
    echo "✅ Django Server started (PID: $DJANGO_PID)"
else
    echo "❌ Failed to start Django Server"
    kill $CELERY_WORKER_PID
    kill $CELERY_BEAT_PID
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ All services running successfully!"
echo "=========================================="
echo ""
echo "📊 Access your application:"
echo "   Portfolio Dashboard: http://localhost:9150/portfolio/"
echo "   News Dashboard: http://localhost:9150/"
echo ""
echo "📝 Logs are being written to:"
echo "   Celery Worker: logs/celery_worker.log"
echo "   Celery Beat: logs/celery_beat.log"
echo "   Django: logs/django.log"
echo ""
echo "🔄 Automated tasks schedule:"
echo "   - Morning news: Daily at 6:00 AM"
echo "   - Holdings news: Every 6 hours (12AM, 6AM, 12PM, 6PM)"
echo "   - News analysis: Daily at 7:30 AM"
echo "   - Recommendations: Daily at 8:30 AM"
echo ""
echo "💡 Manual commands:"
echo "   - Fetch holdings news: python manage.py fetch_holdings_news"
echo "   - Fetch stock events: python manage.py fetch_stock_events --holdings-only"
echo "   - Scrape general news: python manage.py scrape_news"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="

# Wait for user interrupt
wait
