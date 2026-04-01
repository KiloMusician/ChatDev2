#!/bin/bash
# Make ecoscan runnable from any terminal in this project
chmod +x ecoscan 2>/dev/null || true

# ── Terminal Depths universal launcher wiring ────────────────────────────────
export TD_SERVER_URL=http://localhost:8008
export NUSYQ_HUB_URL=http://localhost:3003
# Make `td` available in PATH for this shell and child processes
TD_BIN="/home/runner/workspace/ecosystem/Dev-Mentor"
if [[ ":$PATH:" != *":$TD_BIN:"* ]]; then
  export PATH="$TD_BIN:$PATH"
fi
# Also wire into ~/.local/bin for persistent sessions
mkdir -p ~/.local/bin
ln -sf "$TD_BIN/td" ~/.local/bin/td 2>/dev/null || true

# Start backend in background on port 6400
python server_main.py --host localhost --port 6400 &
BACKEND_PID=$!

# Wait for backend to be ready before starting frontend
echo "Waiting for backend to start..."
for i in $(seq 1 30); do
  if curl -s http://localhost:6400/health > /dev/null 2>&1; then
    echo "Backend ready."
    break
  fi
  sleep 1
done

# ── NuSyQ Ecosystem Services ──────────────────────────────────────────────
if [ -d "ecosystem" ]; then
  echo "Starting NuSyQ ecosystem services..."
  bash ecosystem/start_services.sh &
  ECOSYSTEM_PID=$!
fi

# Start frontend on port 5000 (Vite proxies /api and /ws to backend)
cd frontend && npm run dev

# Cleanup on exit
kill $BACKEND_PID 2>/dev/null
kill $ECOSYSTEM_PID 2>/dev/null
