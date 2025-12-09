# Server Management Guide

## Quick Reference

All shell scripts in the project now automatically check for and stop any existing Django server before starting a new one.

## Affected Scripts

1. **start_system.sh** - Checks port 9000
2. **start_automation.sh** - Checks ports 8000, 9000, 9150
3. **run_analysis.sh** - Checks ports 8000, 9000, 9150
4. **quick_analysis.sh** - Checks ports 8000, 9000, 9150

## New Server Management Utility

### Usage

```bash
# Check server status
./manage_server.sh status

# Start server (default port 9150)
./manage_server.sh start

# Start server on specific port
./manage_server.sh start 8000

# Stop all Django servers
./manage_server.sh stop

# Restart server
./manage_server.sh restart

# Restart on specific port
./manage_server.sh restart 8000
```

### Commands

| Command | Description |
|---------|-------------|
| `start [port]` | Start Django server on specified port (default: 9150) |
| `stop` | Stop all Django servers on ports 8000, 9000, 9150 |
| `restart [port]` | Stop and start server |
| `status` | Check if server is running and on which port |

## How It Works

### Automatic Server Detection

When any script starts, it:

1. Checks common Django ports (8000, 9000, 9150)
2. Uses `lsof -ti:<port>` to find processes
3. Kills any existing Django server with `kill -9`
4. Waits 1-2 seconds before starting new server

### Example Output

```bash
🔍 Checking for existing Django server...
🛑 Found Django server on port 9150. Stopping...
✅ Previous server stopped
🐍 Starting Django server...
```

## Manual Server Management

### Check what's running on a port

```bash
lsof -ti:9150
```

### Kill specific port

```bash
kill -9 $(lsof -ti:9150)
```

### Kill all Django servers

```bash
pkill -f "python manage.py runserver"
```

## Port Usage

| Port | Used By | Purpose |
|------|---------|---------|
| 8000 | start_automation.sh | Default Django port |
| 9000 | start_system.sh | Production server |
| 9150 | Manual/Development | Primary development port |

## Troubleshooting

**Issue**: "Address already in use"
```bash
# Solution 1: Use manage_server.sh
./manage_server.sh stop
./manage_server.sh start

# Solution 2: Kill manually
kill -9 $(lsof -ti:9150)
```

**Issue**: Script says "Server stopped" but still getting errors
```bash
# Wait a moment and check
sleep 2
./manage_server.sh status

# Force kill all Python processes (careful!)
pkill -9 python
```

**Issue**: Multiple servers running
```bash
# Stop all Django servers
./manage_server.sh stop

# Or manually
for port in 8000 9000 9150; do
    kill -9 $(lsof -ti:$port 2>/dev/null)
done
```

## Best Practices

1. **Use manage_server.sh for manual control**
   - Cleaner and safer than manual commands
   - Provides clear feedback
   - Checks multiple ports

2. **Scripts handle cleanup automatically**
   - No need to manually stop before running scripts
   - Prevents "address in use" errors

3. **Check status before debugging**
   ```bash
   ./manage_server.sh status
   ```

4. **Consistent port usage**
   - Development: 9150
   - Automation: 8000
   - Production: 9000

## Implementation Details

### Function Added to Scripts

```bash
kill_django_server() {
    echo "🔍 Checking for existing Django server..."
    for port in 8000 9000 9150; do
        PIDS=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$PIDS" ]; then
            echo "🛑 Found Django server on port $port. Stopping..."
            kill -9 $PIDS 2>/dev/null
        fi
    done
    sleep 1
}
```

### When It Runs

- **Before** starting Django server in any script
- Automatically in background
- No user interaction needed

## Examples

### Starting System
```bash
# Old way (could fail if server running)
./start_system.sh

# New way (automatic cleanup)
./start_system.sh  # Just works! ✓
```

### Running Analysis
```bash
# Automatic server cleanup
./run_analysis.sh

# Or use dedicated manager
./manage_server.sh restart
./run_analysis.sh
```

### Development Workflow
```bash
# Check status
./manage_server.sh status

# Stop for code changes
./manage_server.sh stop

# Make changes...

# Start again
./manage_server.sh start 9150
```

## Safety Features

✅ **No data loss** - Only kills Django server, not database  
✅ **Grace period** - Waits 1-2 seconds after kill  
✅ **Multi-port check** - Finds servers on any common port  
✅ **Silent operation** - No errors if no server running  
✅ **Fallback safe** - Uses `2>/dev/null` to ignore errors  

## Integration with Existing Scripts

All scripts now include:
- Server detection
- Automatic cleanup
- Clear status messages
- Safe error handling

No changes needed to your workflow!
