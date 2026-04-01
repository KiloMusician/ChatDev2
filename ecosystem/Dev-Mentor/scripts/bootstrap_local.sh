#!/usr/bin/env bash
# =============================================================================
#  bootstrap_local.sh — Universal bootstrap for Linux / macOS / WSL / Git Bash
#  Detects surface, shows ecosystem status, starts the game server.
# =============================================================================
set -euo pipefail

RESET='\033[0m'; BOLD='\033[1m'; RED='\033[0;31m'; GREEN='\033[0;32m'
YELLOW='\033[1;33m'; CYAN='\033[0;36m'; DIM='\033[2m'

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ─── Banner ──────────────────────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}"
cat <<'BANNER'
╔══════════════════════════════════════════════════════════╗
║   TERMINAL DEPTHS · DEVMENTOR ECOSYSTEM                  ║
║   Offline-First · AI-Optional · Self-Aware              ║
╚══════════════════════════════════════════════════════════╝
BANNER
echo -e "${RESET}"

# ─── Surface detection ────────────────────────────────────────────────────────
SURFACE="local"
if [[ -n "${REPL_ID:-}" || -n "${REPLIT_DEV_DOMAIN:-}" ]]; then
    SURFACE="replit"
elif [[ -f "/.dockerenv" ]]; then
    SURFACE="docker"
elif [[ -n "${TERM_PROGRAM:-}" && "$TERM_PROGRAM" == "vscode" ]] || [[ -n "${VSCODE_PID:-}" ]]; then
    SURFACE="vscode"
elif grep -qi microsoft /proc/version 2>/dev/null; then
    SURFACE="wsl"
fi

echo -e "  ${DIM}Surface  :${RESET} ${BOLD}${SURFACE^^}${RESET}"
echo -e "  ${DIM}Python   :${RESET} $(python3 --version 2>/dev/null || echo 'not found')"
echo -e "  ${DIM}Host     :${RESET} $(hostname)"
echo ""

# ─── Python environment check ─────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}✗ python3 not found. Install Python 3.10+.${RESET}"
    exit 1
fi

# ─── Sibling repo scan ────────────────────────────────────────────────────────
echo -e "${CYAN}  Sibling Repositories:${RESET}"
PARENT="$(dirname "$ROOT")"
for REPO in NuSyQ-Hub SimulatedVerse CyberTerminal NuSyQ; do
    if [[ -d "$PARENT/$REPO" ]]; then
        echo -e "    ${GREEN}✓${RESET} $REPO"
    else
        echo -e "    ${DIM}·${RESET} $REPO (not found at $PARENT/$REPO)"
    fi
done
echo ""

# ─── Port watcher ─────────────────────────────────────────────────────────────
echo -e "${CYAN}  Service Status:${RESET}"
if python3 scripts/port_watcher.py --json 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
ports = d.get('ports', {})
alive = sum(1 for p in ports.values() if p.get('alive'))
dark  = sum(1 for p in ports.values() if not p.get('alive'))
print(f'    Alive: {alive}  Dark: {dark}')
for ext, info in sorted(ports.items(), key=lambda x: int(x[0])):
    icon = '✓' if info.get('alive') else '✗'
    tier = info.get('tier','opt')[:4].upper()
    name = info.get('name','')[:42]
    print(f'    {icon} [{tier}] :{info[\"local_port\"]:<5} {name}')
" 2>/dev/null; then
    :
else
    echo -e "    ${DIM}(port scanner not available — run scripts/port_watcher.py manually)${RESET}"
fi
echo ""

# ─── Surface-specific quickstart ──────────────────────────────────────────────
case "$SURFACE" in
    replit)
        echo -e "${CYAN}  REPLIT QUICKSTART:${RESET}"
        echo -e "    • Game auto-starts via the DevMentor Console workflow"
        echo -e "    • Open the Webview tab to see the game"
        echo -e "    • Type ${BOLD}help${RESET} in the terminal to begin"
        ;;
    docker)
        echo -e "${CYAN}  DOCKER QUICKSTART:${RESET}"
        echo -e "    • Singleton infra: ${BOLD}make docker-core${RESET}"
        echo -e "    • Shared ops:      ${BOLD}make docker-up${RESET}"
        echo -e "    • App containers:  ${BOLD}make docker-apps${RESET}"
        echo -e "    • Full showcase:   ${BOLD}make docker-full${RESET}"
        echo -e "    • Port check:  ${BOLD}python scripts/port_watcher.py --fix${RESET}"
        echo -e "    • CLI client:  ${BOLD}python scripts/td.py${RESET}"
        ;;
    vscode)
        echo -e "${CYAN}  VS CODE QUICKSTART:${RESET}"
        echo -e "    • Ctrl+Shift+B — DevMentor task panel"
        echo -e "    • Open: DevMentorWorkspace.workspace.json"
        echo -e "    • Start Task: ${BOLD}Start DevMentor Server${RESET}"
        ;;
    wsl)
        echo -e "${CYAN}  WSL QUICKSTART:${RESET}"
        echo -e "    • Start server: ${BOLD}python -m cli.devmentor serve${RESET}"
        echo -e "    • Docker:       ${BOLD}docker compose up -d${RESET} (via Docker Desktop)"
        echo -e "    • VS Code:      ${BOLD}code .${RESET} (opens in Remote-WSL)"
        ;;
    *)
        echo -e "${CYAN}  LOCAL QUICKSTART:${RESET}"
        echo -e "    • Start server: ${BOLD}python -m cli.devmentor serve --host 0.0.0.0 --port 5000${RESET}"
        echo -e "    • CLI client:   ${BOLD}python scripts/td.py${RESET}"
        echo -e "    • Set GAME_API_URL if connecting to Replit"
        ;;
esac
echo ""

# ─── Auto-start game server (if not running) ─────────────────────────────────
if [[ "${AUTO_START:-0}" == "1" ]] || [[ "$SURFACE" == "local" || "$SURFACE" == "wsl" ]]; then
    PORT="${GAME_PORT:-5000}"
    if ! python3 -c "import socket; s=socket.create_connection(('localhost',$PORT),1)" 2>/dev/null; then
        echo -e "${YELLOW}  Starting game server on :$PORT ...${RESET}"
        python3 -m cli.devmentor serve --host 0.0.0.0 --port "$PORT" &
        SERVER_PID=$!
        sleep 2
        if python3 -c "import socket; s=socket.create_connection(('localhost',$PORT),1)" 2>/dev/null; then
            echo -e "${GREEN}  ✓ Server running (PID $SERVER_PID)${RESET}"
        else
            echo -e "${RED}  ✗ Server failed to start${RESET}"
        fi
    else
        echo -e "${GREEN}  ✓ Game server already running on :$PORT${RESET}"
    fi
fi

echo ""
echo -e "${DIM}  Environment report: ${BOLD}python core/environment.py${RESET}"
echo -e "${DIM}  Activation plan:    ${BOLD}python core/environment.py --plan${RESET}"
echo -e "${DIM}  Port watcher:       ${BOLD}python scripts/port_watcher.py${RESET}"
echo -e "${DIM}  In-game:            ${BOLD}context · plan · surface${RESET}"
echo ""
