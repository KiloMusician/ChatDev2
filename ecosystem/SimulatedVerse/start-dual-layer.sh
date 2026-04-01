#!/bin/bash
# CoreLink Foundation Dual-Layer System Launcher
# This script bypasses tsx dependency issues and starts the working dual-layer server

echo "🚀 Starting CoreLink Foundation Dual-Layer System"
echo "=================================================="

# Kill any existing node processes
pkill -f node 2>/dev/null || true
sleep 1

# Set environment
export NODE_ENV=development
export PORT=5000

echo "✅ Environment configured:"
echo "   NODE_ENV: $NODE_ENV"
echo "   PORT: $PORT"

# Start the bootstrap server (bypasses tsx issues)
echo ""
echo "🔧 Launching dual-layer server..."
echo "   - Casual interface: http://localhost:5000/casual"
echo "   - Developer console: http://localhost:5000/developer"
echo "   - API endpoints: http://localhost:5000/api/*"
echo ""

# Start server in foreground with proper error handling
node bootstrap-server.js 2>&1 | while IFS= read -r line; do
    echo "$(date '+%H:%M:%S') | $line"
done