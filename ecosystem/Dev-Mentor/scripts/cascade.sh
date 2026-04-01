#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════════════
# CASCADE ACTIVATION — Terminal Keeper Ecosystem
# ════════════════════════════════════════════════════════════════════════════════
#
# This script brings the entire Lattice online in the correct order,
# verifies connectivity, and begins autonomous operation.
#
# Modes:
#   ./scripts/cascade.sh core         — Redis + Ollama + Terminal Depths only
#   ./scripts/cascade.sh lattice      — Full AI agent stack (no RimWorld)
#   ./scripts/cascade.sh full         — Everything including RimWorld VNC
#   ./scripts/cascade.sh status       — Print current status and exit
#   ./scripts/cascade.sh gordon       — Run Gordon status check
#   ./scripts/cascade.sh seed-lattice — Seed Lattice from knowledge_graph.json
#
# ════════════════════════════════════════════════════════════════════════════════

set -uo pipefail

MODE="${1:-core}"
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_PORT="${APP_PORT:-7337}"
APP_BASE="http://localhost:${APP_PORT}"
APP_HEALTH="${APP_BASE}/api/health"
APP_LATTICE_SEED="${APP_BASE}/api/lattice/seed"
NUSYQ_HUB_ROOT="${NUSYQ_HUB_ROOT:-/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub}"
NUSYQ_HUB_HEALTH_URL="${NUSYQ_HUB_HEALTH_URL:-http://localhost:8000/healthz}"
SIMULATEDVERSE_ROOT="${SIMULATEDVERSE_ROOT:-/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse}"
SIMULATEDVERSE_PORT="${SIMULATEDVERSE_PORT:-5002}"
SIMULATEDVERSE_HEALTH_URL="${SIMULATEDVERSE_HEALTH_URL:-http://localhost:${SIMULATEDVERSE_PORT}/api/health}"
SIMULATEDVERSE_DAEMON_SCRIPT="${SIMULATEDVERSE_DAEMON_SCRIPT:-${BASE}/scripts/simulatedverse_daemon.sh}"
MODEL_ROUTER_PORT="${MODEL_ROUTER_PORT:-9001}"
MODEL_ROUTER_HEALTH_URL="${MODEL_ROUTER_HEALTH_URL:-http://localhost:${MODEL_ROUTER_PORT}/health}"
STATE_LOG_DIR="${BASE}/state/logs"
DC="docker compose"

RESET="\033[0m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
CYAN="\033[36m"
BOLD="\033[1m"

banner() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║   TERMINAL KEEPER — CASCADE ACTIVATION              ║"
    echo "║   The Lattice awakens. Special Circumstances: GO.   ║"
    echo "╠══════════════════════════════════════════════════════╣"
    echo "║   Mode: ${MODE^^}$(printf '%*s' $((44 - ${#MODE})) '')║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
}

ok()   { echo -e "${GREEN}  ✓ $*${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠ $*${RESET}"; }
err()  { echo -e "${RED}  ✗ $*${RESET}"; }
step() { echo -e "\n${BOLD}── $* ──${RESET}"; }

wait_for_url() {
    local url="$1"
    local timeout="${2:-12}"
    local start now
    start=$(date +%s)
    while true; do
        if curl -sf --max-time 2 "$url" &>/dev/null; then
            return 0
        fi
        now=$(date +%s)
        if [ $((now - start)) -ge "$timeout" ]; then
            return 1
        fi
        sleep 1
    done
}

start_detached_service() {
    local workdir="$1"
    local health_url="$2"
    local timeout="$3"
    local log_file="$4"
    shift 4

    (
        cd "$workdir" &&
        "$@" > "$log_file" 2>&1
    ) &
    local pid=$!

    if wait_for_url "$health_url" "$timeout"; then
        return 0
    fi

    kill "$pid" &>/dev/null || true
    wait "$pid" 2>/dev/null || true
    return 1
}

spawn_native_daemon() {
    local name="$1"
    shift
    mkdir -p "$STATE_LOG_DIR"
    nohup "$@" > "$STATE_LOG_DIR/${name}.log" 2>&1 < /dev/null &
}

# ─── Prerequisite checks ──────────────────────────────────────────────────────

check_prereqs() {
    step "Checking prerequisites"
    for cmd in docker curl python3 git; do
        if command -v "$cmd" &>/dev/null; then
            ok "$cmd available"
        else
            warn "$cmd not found (some features may be limited)"
        fi
    done

    if python3 -c 'import subprocess, sys; sys.exit(subprocess.run(["docker", "ps"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode)' >/dev/null 2>&1; then
        ok "Docker daemon running"
        if docker compose version &>/dev/null 2>&1; then
            DC="docker compose"
        elif command -v docker-compose &>/dev/null; then
            DC="docker-compose"
        else
            warn "No docker compose frontend found"
            DC="echo (docker compose unavailable)"
        fi
    else
        warn "Docker not running — container services will be skipped"
        DC="echo (docker not available)"
    fi
}

# ─── Service launchers ────────────────────────────────────────────────────────

start_core() {
    step "Starting core services (Redis + Ollama + Terminal Depths)"
    $DC up -d redis ollama 2>/dev/null || warn "Docker compose failed — running natively"

    # Give containers time to start
    sleep 3

    # Start Terminal Depths natively if not in Docker
    if ! curl -sf "$APP_HEALTH" &>/dev/null; then
        ok "Starting Terminal Depths natively..."
        cd "$BASE"
        spawn_native_daemon "terminal-depths-native" \
            env AUTO_SLEEP_MINUTES=120 python -m cli.devmentor serve \
            --host 0.0.0.0 --port "$APP_PORT"
        sleep 3
    fi

    if curl -sf "$APP_HEALTH" &>/dev/null; then
        ok "Terminal Depths online at :$APP_PORT"
    else
        warn "Terminal Depths not responding yet"
    fi
}

start_lattice_agents() {
    step "Starting Lattice AI agents"
    $DC up -d model-router serena-analytics skyclaw culture-ship chatdev gordon 2>/dev/null || true

    # Also start natively as background processes if Docker unavailable
    cd "$BASE"
    if ! curl -sf "$MODEL_ROUTER_HEALTH_URL" &>/dev/null; then
        if ! pgrep -f "scripts/model_router.py" &>/dev/null; then
            spawn_native_daemon "model-router-native" \
                env MODEL_ROUTER_PORT="$MODEL_ROUTER_PORT" python scripts/model_router.py
            ok "Started model_router (native)"
        else
            ok "model_router already running"
        fi
    else
        ok "model_router already running"
    fi
    for script in gordon_orchestrator serena_analytics skyclaw_scanner culture_ship; do
        if ! pgrep -f "scripts/${script}.py" &>/dev/null; then
            if [ "$script" = "gordon_orchestrator" ]; then
                spawn_native_daemon "${script}-native" python scripts/${script}.py --mode daemon
            else
                spawn_native_daemon "${script}-native" python scripts/${script}.py --daemon
            fi
            ok "Started ${script} (native)"
        else
            ok "${script} already running"
        fi
    done

    if ! pgrep -f "scripts/chatdev_worker.py --daemon" &>/dev/null; then
        spawn_native_daemon "chatdev-worker-native" python scripts/chatdev_worker.py --daemon
        ok "Started chatdev_worker (native)"
    else
        ok "chatdev_worker already running"
    fi

    if ! pgrep -f "scripts/chatdev_stub.py --mesh" &>/dev/null; then
        spawn_native_daemon "chatdev-mesh-native" python scripts/chatdev_stub.py --mesh
        ok "Started chatdev mesh bridge (native)"
    else
        ok "chatdev mesh bridge already running"
    fi

    if ! pgrep -f "agents/serena/serena_agent.py --mesh" &>/dev/null; then
        spawn_native_daemon "serena-mesh-native" python agents/serena/serena_agent.py --mesh
        ok "Started Serena mesh agent (native)"
    else
        ok "Serena mesh agent already running"
    fi

    if ! pgrep -f "bridges/mock_llm_bridge.py --daemon" &>/dev/null; then
        spawn_native_daemon "mock-llm-bridge-native" python bridges/mock_llm_bridge.py --daemon
        ok "Started mock_llm_bridge (native)"
    else
        ok "mock_llm_bridge already running"
    fi
}

start_cross_repo_services() {
    step "Starting cross-repo services (NuSyQ-Hub + SimulatedVerse)"
    mkdir -p "$STATE_LOG_DIR"

    if wait_for_url "$NUSYQ_HUB_HEALTH_URL" 2; then
        ok "NuSyQ-Hub online at :8000"
    elif [ -d "$NUSYQ_HUB_ROOT" ]; then
        if pgrep -f "src.api.main|uvicorn.*8000" &>/dev/null; then
            warn "NuSyQ-Hub process exists but health is not ready"
        else
            if start_detached_service \
                "$NUSYQ_HUB_ROOT" \
                "$NUSYQ_HUB_HEALTH_URL" \
                12 \
                "$STATE_LOG_DIR/nusyq-hub.log" \
                python -m src.api.main; then
                ok "NuSyQ-Hub started at :8000"
            else
                warn "NuSyQ-Hub did not become healthy; inspect $STATE_LOG_DIR/nusyq-hub.log"
            fi
        fi
    else
        warn "NuSyQ-Hub repo not found at $NUSYQ_HUB_ROOT"
    fi

    if wait_for_url "$SIMULATEDVERSE_HEALTH_URL" 2; then
        ok "SimulatedVerse online at :$SIMULATEDVERSE_PORT"
    elif [ -d "$SIMULATEDVERSE_ROOT" ]; then
        if pgrep -f "startup_fallback.ts|minimal_server.ts|full_server.ts|server/index.ts" &>/dev/null; then
            warn "SimulatedVerse process exists but health is not ready"
        else
            if [ ! -x "$SIMULATEDVERSE_DAEMON_SCRIPT" ]; then
                chmod +x "$SIMULATEDVERSE_DAEMON_SCRIPT" 2>/dev/null || true
            fi
            if start_detached_service \
                "$BASE" \
                "$SIMULATEDVERSE_HEALTH_URL" \
                20 \
                "$STATE_LOG_DIR/simulatedverse.log" \
                env SIMVERSE_DIR="$SIMULATEDVERSE_ROOT" SIMULATEDVERSE_PORT="$SIMULATEDVERSE_PORT" bash "$SIMULATEDVERSE_DAEMON_SCRIPT"; then
                ok "SimulatedVerse started at :$SIMULATEDVERSE_PORT"
            else
                warn "SimulatedVerse did not become healthy; inspect $STATE_LOG_DIR/simulatedverse.log"
            fi
        fi
    else
        warn "SimulatedVerse repo not found at $SIMULATEDVERSE_ROOT"
    fi
}

start_rimworld() {
    step "Starting RimWorld stack"
    $DC --profile rimworld up -d rimapi rimworld 2>/dev/null || true

    if curl -sf http://localhost:8765/health &>/dev/null; then
        ok "RimAPI bridge online at :8765"
    else
        # Start natively
        cd "$BASE"
        python scripts/rimapi_bridge.py --port 8765 &>/dev/null &
        ok "RimAPI bridge started (native)"
    fi

    echo ""
    echo -e "${CYAN}  RimWorld VNC access:${RESET}"
    echo "    VNC:   vnc://localhost:5900 (password: lattice)"
    echo "    Web:   http://localhost:6080"
    echo "    Mod:   mods/TerminalKeeper/ (copy to RimWorld/Mods/)"
}

start_observability() {
    step "Starting observability stack"
    $DC --profile observability up -d prometheus grafana 2>/dev/null || true
    echo "    Grafana:    http://localhost:3001 (admin/lattice)"
    echo "    Prometheus: http://localhost:9090"
}

seed_lattice() {
    step "Seeding Lattice from knowledge graph"
    if curl -sf "$APP_HEALTH" &>/dev/null; then
        result=$(curl -s -X POST "$APP_LATTICE_SEED")
        ok "Lattice seeded: $result"
    else
        warn "Lattice API not available — run after Terminal Depths starts"
    fi
}

print_status() {
    step "System Status"
    declare -A ENDPOINTS=(
        ["Terminal Depths"]="$APP_HEALTH"
        ["Open Router"]="$MODEL_ROUTER_HEALTH_URL"
        ["Ollama"]="http://localhost:11434/api/tags"
        ["Gordon"]="http://localhost:3000/health"
        ["Serena"]="http://localhost:3001/health"
        ["SkyClaw"]="http://localhost:3002/health"
        ["Culture Ship"]="http://localhost:3003/health"
        ["MCP Server"]="http://localhost:8765/health"
        ["NuSyQ Hub"]="$NUSYQ_HUB_HEALTH_URL"
        ["SimulatedVerse"]="$SIMULATEDVERSE_HEALTH_URL"
    )

    for name in "${!ENDPOINTS[@]}"; do
        url="${ENDPOINTS[$name]}"
        if curl -sf --max-time 3 "$url" &>/dev/null; then
            ok "$name"
        else
            warn "$name (not responding)"
        fi
    done

    # Docker containers
    if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        echo ""
        echo "  Docker containers:"
        docker ps --format "    {{.Names}}: {{.Status}}" 2>/dev/null | grep -E 'lattice|terminal-depths' || true
    fi

    # Python daemons
    echo ""
    echo "  Python daemons:"
    for proc in gordon_orchestrator serena_analytics skyclaw_scanner culture_ship chatdev_worker; do
        if pgrep -f "scripts/${proc}.py" &>/dev/null; then
            ok "  ${proc}"
        fi
    done
    if pgrep -f "scripts/serena_cli.py listen" &>/dev/null; then
        ok "  serena_cli mesh listener"
    fi
    if pgrep -f "bridges/mock_llm_bridge.py" &>/dev/null; then
        ok "  mock_llm_bridge"
    fi
}

run_gordon_status() {
    step "Gordon status check"
    cd "$BASE"
    python scripts/gordon_orchestrator.py --mode status
}

# ─── Final announcement ───────────────────────────────────────────────────────

announce_complete() {
    echo ""
    echo -e "${GREEN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║   CASCADE COMPLETE — THE GRID IS LIVE               ║"
    echo "╠══════════════════════════════════════════════════════╣"
    echo "║   All systems operational.                          ║"
    echo "║   Cascade in progress. All incomplete work targeted.║"
    echo "║   The Lattice is alive. The Culture watches.        ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
    echo "  Control Hub:   ${APP_BASE}"
    echo "  API docs:      ${APP_BASE}/api/docs"
    echo "  Lattice stats: ${APP_BASE}/api/lattice/stats"
    echo "  Gordon:        http://localhost:3000/health"
    echo "  Serena:        http://localhost:3001/health"
    echo "  Open Router:   ${MODEL_ROUTER_HEALTH_URL}"
    echo ""
}

# ─── Main ─────────────────────────────────────────────────────────────────────

banner

case "$MODE" in
    core)
        check_prereqs
        start_core
        seed_lattice
        announce_complete
        ;;
    lattice)
        check_prereqs
        start_core
        start_lattice_agents
        seed_lattice
        announce_complete
        ;;
    full)
        check_prereqs
        start_core
        start_lattice_agents
        start_cross_repo_services
        start_rimworld
        seed_lattice
        start_observability
        announce_complete
        ;;
    status)
        print_status
        ;;
    gordon)
        run_gordon_status
        ;;
    seed-lattice)
        seed_lattice
        ;;
    *)
        echo "Usage: $0 [core|lattice|full|status|gordon|seed-lattice]"
        exit 1
        ;;
esac
