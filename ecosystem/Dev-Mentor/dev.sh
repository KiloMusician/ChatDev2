#!/usr/bin/env bash
# dev.sh — Terminal Depths development server with auto-reload
# Usage: ./dev.sh [--test] [--play] [--agents]

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

GREEN='\033[0;32m' CYAN='\033[0;36m' YELLOW='\033[1;33m' NC='\033[0m'

log() { echo -e "${CYAN}[dev]${NC} $*"; }
ok()  { echo -e "${GREEN}[ok]${NC}  $*"; }
warn(){ echo -e "${YELLOW}[warn]${NC} $*"; }

log "Terminal Depths Development Server"
log "=================================="

# Parse flags
RUN_TESTS=0 RUN_PLAY=0 RUN_AGENTS=0
for arg in "$@"; do
  case "$arg" in
    --test)   RUN_TESTS=1 ;;
    --play)   RUN_PLAY=1 ;;
    --agents) RUN_AGENTS=1 ;;
  esac
done

# Zero-token ops: check before starting
log "Running pre-flight checks..."
python3 -c "
import sys, pathlib
files = ['app/backend/main.py', 'app/game_engine/commands.py', 'app/game_engine/scripting.py']
ok = True
for f in files:
    if not pathlib.Path(f).exists():
        print(f'MISSING: {f}')
        ok = False
    else:
        sz = pathlib.Path(f).stat().st_size
        print(f'  ok  {f} ({sz} bytes)')
if ok:
    print('Pre-flight: all engine files present.')
"

# Ensure sessions dir
mkdir -p sessions

# Optional: run tests first
if [ "$RUN_TESTS" -eq 1 ]; then
  log "Running test suite..."
  python3 playtest.py --quick 2>&1 | tail -20
fi

# Optional: start agents
if [ "$RUN_AGENTS" -eq 1 ]; then
  log "Starting orchestrator agent in background..."
  python3 agents/orchestrator.py &
  ORCH_PID=$!
  log "Orchestrator PID: $ORCH_PID"
fi

# Start server with auto-reload
log "Starting API server with auto-reload..."
ok "Server: http://localhost:7337"
ok "Game JS:  http://localhost:7337/game/"
ok "Game CLI: http://localhost:7337/game-cli/"
ok "API docs: http://localhost:7337/api/docs"
ok "Agent:    http://localhost:7337/api/agent/info"
echo ""

exec uvicorn app.backend.main:app \
  --host 0.0.0.0 \
  --port 7337 \
  --reload \
  --reload-dir app \
  --log-level info
