#!/usr/bin/env bash
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  DevMentor / Terminal Depths — Universal Launcher (bash/Linux/macOS)    │
# │  Works: standalone shell, Docker, VS Code terminal, GitHub Codespaces   │
# └─────────────────────────────────────────────────────────────────────────┘
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Prevent stale .pyc bytecode from masking code changes
export PYTHONDONTWRITEBYTECODE=1

PORT="${TD_PORT:-7337}"
HOST="${TD_HOST:-0.0.0.0}"
MODE="${1:-serve}"

_banner() {
  printf '\033[1;36m'
  echo "╔══════════════════════════════════════════════╗"
  echo "║   Terminal Depths — DevMentor Launcher       ║"
  echo "║   Mode: %-36s║" "$MODE"
  echo "╚══════════════════════════════════════════════╝"
  printf '\033[0m'
}

_require() { command -v "$1" &>/dev/null || { echo "Required: $1"; exit 1; }; }

case "$MODE" in
  serve|s)
    _banner
    _require python3
    echo "→ Starting API server on http://$HOST:$PORT"
    echo "→ Browser: http://localhost:$PORT/game/"
    exec python3 -m cli.devmentor serve --host "$HOST" --port "$PORT"
    ;;
  play|p)
    _banner
    _require python3
    SESSION="${2:-player-$(whoami)}"
    echo "→ Interactive terminal REPL (session: $SESSION)"
    exec python3 -m cli.devmentor play --session-id "$SESSION"
    ;;
  docker|d)
    _banner
    _require docker
    echo "→ Launching via Docker Compose"
    docker compose -f docker-compose.yml up -d
    echo "→ API: http://localhost:7337  |  Game: http://localhost:7337/game/"
    ;;
  docker-full|df)
    _banner
    _require docker
    echo "→ Full stack (cascade, redis, ollama, openwebui)"
    docker compose -f docker-compose.full.yml up -d
    ;;
  docker-rimworld|rw)
    _banner
    _require docker
    echo "→ RimWorld + VNC stack"
    docker compose -f docker-compose.full.yml --profile rimworld up -d
    echo "→ VNC: localhost:5900  |  RimAPI: localhost:8765"
    ;;
  stop)
    echo "Stopping all DevMentor containers..."
    docker compose -f docker-compose.yml down 2>/dev/null || true
    docker compose -f docker-compose.full.yml down 2>/dev/null || true
    ;;
  status|st)
    python3 -m cli.devmentor status
    ;;
  mcp)
    _banner
    _require python3
    echo "→ MCP server on stdio (for Claude / Copilot)"
    exec python3 mcp/server.py
    ;;
  agent|a)
    SESSION="${2:-agent-$(hostname)}"
    _banner
    python3 -m cli.devmentor agent --session-id "$SESSION" "${@:3}"
    ;;
  help|h|--help|-h)
    echo ""
    echo "Usage: ./devmentor.sh [mode] [args]"
    echo ""
    echo "Modes:"
    echo "  serve (s)          Start API server  (default, port \$TD_PORT or 7337)"
    echo "  play  (p) [name]   Interactive REPL"
    echo "  docker (d)         Docker Compose (base stack)"
    echo "  docker-full (df)   Full stack with Redis/Ollama"
    echo "  docker-rimworld    RimWorld + VNC stack"
    echo "  stop               Stop all containers"
    echo "  status (st)        System status"
    echo "  mcp                MCP stdio server (for Claude Desktop / Copilot)"
    echo "  agent (a) [id]     Run as named agent"
    echo ""
    echo "Environment:"
    echo "  TD_PORT=7337       Server port"
    echo "  TD_HOST=0.0.0.0    Bind address"
    echo "  OPENAI_API_KEY     Optional — for OpenAI LLM backend"
    echo "  NUSYQ_PASSKEY      NuSyQ hub passkey"
    ;;
  *)
    echo "Unknown mode: $MODE. Try: ./devmentor.sh help"
    exit 1
    ;;
esac
