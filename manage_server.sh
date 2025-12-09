#!/bin/bash
# Django Server Management Utility
# Provides commands to start, stop, restart, and check Django server status

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default port
DEFAULT_PORT=9150

# Function to check if server is running on a port
check_server() {
    local port=${1:-$DEFAULT_PORT}
    PIDS=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PIDS" ]; then
        return 0  # Server is running
    else
        return 1  # Server is not running
    fi
}

# Function to get server status
status() {
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}   Django Server Status Check${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""
    
    local found=0
    for port in 8000 9000 9150; do
        if check_server $port; then
            PIDS=$(lsof -ti:$port 2>/dev/null)
            echo -e "${GREEN}✓ Server running on port $port${NC}"
            echo -e "  PIDs: $PIDS"
            found=1
        fi
    done
    
    if [ $found -eq 0 ]; then
        echo -e "${YELLOW}⊗ No Django server running${NC}"
    fi
    echo ""
}

# Function to stop server
stop() {
    local port=${1:-$DEFAULT_PORT}
    echo -e "${YELLOW}🛑 Stopping Django server...${NC}"
    
    local found=0
    for p in 8000 9000 9150; do
        if check_server $p; then
            PIDS=$(lsof -ti:$p 2>/dev/null)
            echo -e "${BLUE}  Found server on port $p (PIDs: $PIDS)${NC}"
            kill -9 $PIDS 2>/dev/null
            found=1
        fi
    done
    
    if [ $found -eq 0 ]; then
        echo -e "${YELLOW}⊗ No server to stop${NC}"
    else
        sleep 2
        echo -e "${GREEN}✓ Server stopped${NC}"
    fi
    echo ""
}

# Function to start server
start() {
    local port=${1:-$DEFAULT_PORT}
    
    echo -e "${BLUE}🚀 Starting Django server on port $port...${NC}"
    
    # Check if already running
    if check_server $port; then
        echo -e "${YELLOW}⚠️  Server already running on port $port${NC}"
        echo -e "${YELLOW}   Use 'restart' to restart the server${NC}"
        echo ""
        return 1
    fi
    
    # Change to script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"
    
    # Activate virtual environment
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}❌ Virtual environment not found!${NC}"
        return 1
    fi
    
    # Start server in background
    python manage.py runserver $port > /dev/null 2>&1 &
    SERVER_PID=$!
    
    # Wait a moment and check if it started
    sleep 3
    
    if check_server $port; then
        echo -e "${GREEN}✓ Server started successfully${NC}"
        echo -e "  PID: $SERVER_PID"
        echo -e "  URL: ${BLUE}http://localhost:$port${NC}"
        echo -e "  Admin: ${BLUE}http://localhost:$port/admin${NC}"
    else
        echo -e "${RED}❌ Server failed to start${NC}"
        echo -e "${YELLOW}Check logs for errors${NC}"
    fi
    echo ""
}

# Function to restart server
restart() {
    local port=${1:-$DEFAULT_PORT}
    echo -e "${YELLOW}🔄 Restarting Django server...${NC}"
    echo ""
    stop
    sleep 1
    start $port
}

# Function to show usage
usage() {
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}   Django Server Manager${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""
    echo "Usage: ./manage_server.sh [command] [port]"
    echo ""
    echo "Commands:"
    echo -e "  ${GREEN}start [port]${NC}    - Start Django server (default port: 9150)"
    echo -e "  ${GREEN}stop${NC}            - Stop all Django servers"
    echo -e "  ${GREEN}restart [port]${NC}  - Restart Django server"
    echo -e "  ${GREEN}status${NC}          - Check server status"
    echo ""
    echo "Examples:"
    echo "  ./manage_server.sh start        # Start on port 9150"
    echo "  ./manage_server.sh start 8000   # Start on port 8000"
    echo "  ./manage_server.sh stop         # Stop all servers"
    echo "  ./manage_server.sh restart      # Restart on port 9150"
    echo "  ./manage_server.sh status       # Check status"
    echo ""
}

# Main logic
case "$1" in
    start)
        start ${2:-$DEFAULT_PORT}
        ;;
    stop)
        stop
        ;;
    restart)
        restart ${2:-$DEFAULT_PORT}
        ;;
    status)
        status
        ;;
    *)
        usage
        ;;
esac
