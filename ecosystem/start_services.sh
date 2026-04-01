#!/bin/bash
# NuSyQ Ecosystem Service Launcher
# Starts all ecosystem repos that can run in this environment

ECOSYSTEM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[ecosystem] Starting NuSyQ ecosystem services..."

# ── Dev-Mentor: Terminal Depths FastAPI backend ──────────────────────────
echo "[ecosystem] Starting Dev-Mentor (Terminal Depths) on port 8008..."
cd "$ECOSYSTEM_DIR/Dev-Mentor"
python -m uvicorn app.backend.main:app \
  --host localhost \
  --port 8008 \
  --log-level warning \
  2>&1 | sed 's/^/[dev-mentor] /' &
DEV_MENTOR_PID=$!

# ── CONCEPT_SAMURAI: Static concept docs ────────────────────────────────
echo "[ecosystem] Starting CONCEPT_SAMURAI (static docs) on port 3002..."
cd "$ECOSYSTEM_DIR/CONCEPT_SAMURAI"
python -c "
import http.server, socketserver, os
os.chdir('$ECOSYSTEM_DIR/CONCEPT_SAMURAI')
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, f, *a): pass
with socketserver.TCPServer(('localhost', 3002), H) as s:
    s.serve_forever()
" 2>&1 | sed 's/^/[concept-samurai] /' &
CONCEPT_PID=$!

# ── NuSyQ-Hub: Full FastAPI service on port 3003 ────────────────────────
echo "[ecosystem] Starting NuSyQ-Hub Reactive API on port 3003..."
cd "$ECOSYSTEM_DIR/NuSyQ-Hub"
python -m uvicorn src.api.main:app \
  --host localhost \
  --port 3003 \
  --log-level warning \
  2>&1 | sed 's/^/[nusyq-hub] /' &
HUB_PID=$!

# ── Wait for services to start ───────────────────────────────────────────
sleep 3
echo "[ecosystem] Services started:"
echo "  Dev-Mentor      → http://localhost:8008/api/manifest"
echo "  CONCEPT_SAMURAI → http://localhost:3002"
echo "  NuSyQ-Hub       → http://localhost:3003/api/status"

# Keep running until killed
wait $DEV_MENTOR_PID $CONCEPT_PID $HUB_PID
