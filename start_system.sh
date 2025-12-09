#!/bin/bash
# Stock Market News AI - Startup Script
# Run this script to start all services

echo "🚀 Starting Stock Market News AI System..."

# Change to project directory (script's directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source .venv/bin/activate

# Function to check and kill Django server
kill_django_server() {
    echo "🔍 Checking for existing Django server..."
    DJANGO_PIDS=$(lsof -ti:9000 2>/dev/null)
    if [ ! -z "$DJANGO_PIDS" ]; then
        echo "🛑 Found Django server running on port 9000. Stopping..."
        kill -9 $DJANGO_PIDS 2>/dev/null
        sleep 2
        echo "✅ Previous server stopped"
    fi
}

# Kill existing Django server
kill_django_server

echo "📊 Starting Redis server..."
brew services start redis
sleep 2

echo "🐍 Starting Django server..."
python manage.py runserver 9000 &
DJANGO_PID=$!
sleep 3

echo "⚡ Starting Celery worker..."
celery -A stock_news_ai worker --loglevel=info &
CELERY_WORKER_PID=$!
sleep 2

echo "⏰ Starting Celery scheduler..."
celery -A stock_news_ai beat --loglevel=info &
CELERY_BEAT_PID=$!
sleep 2

echo "📰 Running on-demand news collection, analysis, and recommendations..."
python manage.py scrape_news
echo "🤖 Running AI analysis on collected news..."
python manage.py shell -c "from news.tasks import analyze_news_batch; analyze_news_batch()"
echo "💡 Generating stock recommendations..."
python manage.py shell -c "from news.tasks import generate_daily_recommendations; generate_daily_recommendations()"
echo "📊 Fetching promoter holdings for top stocks..."
python manage.py fetch_stock_events --event-type promoter --holdings-only --days 90 2>/dev/null || echo "⚠️  Note: Promoter data fetch skipped (may hit rate limits)"
echo "🎯 Generating entry signals (price dips, dividends, orders, etc.)..."
python manage.py generate_entry_signals
echo "✅ Initial news pipeline completed"

echo "💤 Preventing system sleep for 12 hours..."
caffeinate -u -t 43200 &
CAFFEINATE_PID=$!

echo ""
echo "✅ All services started successfully!"
echo "📱 Dashboard: http://localhost:8000"
echo "🔧 Admin Panel: http://localhost:8000/admin (admin/admin)"
echo ""
echo "⏰ Automated schedule:"
echo "   - 6:00 AM IST: News Collection"
echo "   - 7:30 AM IST: AI Analysis"
echo "   - 8:30 AM IST: Generate Recommendations"
echo ""
echo "📊 Service PIDs:"
echo "   - Django: $DJANGO_PID"
echo "   - Celery Worker: $CELERY_WORKER_PID"
echo "   - Celery Beat: $CELERY_BEAT_PID"
echo "   - Caffeinate: $CAFFEINATE_PID"
echo ""
echo "⚠️  Keep this terminal open to maintain services"
echo "🛑 Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $DJANGO_PID $CELERY_WORKER_PID $CELERY_BEAT_PID $CAFFEINATE_PID 2>/dev/null
    brew services stop redis
    echo "✅ All services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT

# Wait for user input
echo "💡 System is running... Press Ctrl+C to stop"
wait