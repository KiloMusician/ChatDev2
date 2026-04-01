#!/bin/bash
# Start backend in background on port 6400
python server_main.py --host localhost --port 6400 &
BACKEND_PID=$!

# Start frontend on port 5000 (Vite proxies /api and /ws to backend)
cd frontend && npm run dev

# If frontend exits, kill backend
kill $BACKEND_PID 2>/dev/null
