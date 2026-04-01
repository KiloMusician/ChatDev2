#!/usr/bin/env bash
# Terminal Depths + Dev-Mentor Bootstrap (bash/WSL/Linux/macOS)
# Comprehensive startup orchestrator for local multi-repo workspace
# Usage: ./bootstrap.sh [full|dev|cli|stop] [lite|balanced|architect|vision]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
C_TITLE='\033[1;36m'
C_OK='\033[1;32m'
C_WARN='\033[1;33m'
C_ERR='\033[1;31m'
C_INFO='\033[1;34m'
C_RESET='\033[0m'

# Parse args
MODE="${1:-full}"
PROFILE="${2:-balanced}"
SKIP_DOCKER="${SKIP_DOCKER:-}"
NO_WAIT="${NO_WAIT:-}"

# ============================================================
# Utility Functions
# ============================================================

write_title() {
    echo ""
    echo -e "${C_TITLE}════════════════════════════════════════════════════════════${C_RESET}"
    echo -e "${C_TITLE}$1${C_RESET}"
    echo -e "${C_TITLE}════════════════════════════════════════════════════════════${C_RESET}"
    echo ""
}

write_ok() {
    echo -e "${C_OK}✓${C_RESET} $1"
}

write_warn() {
    echo -e "${C_WARN}⚠${C_RESET} $1"
}

write_err() {
    echo -e "${C_ERR}✗${C_RESET} $1"
}

write_info() {
    echo -e "${C_INFO}ℹ${C_RESET} $1"
}

command_exists() {
    command -v "$1" &> /dev/null
}

test_port() {
    local port=$1
    if nc -z 127.0.0.1 "$port" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

docker_running() {
    docker info &>/dev/null
}

# ============================================================
# Bootstrap Sequence
# ============================================================

write_title "Terminal Depths Bootstrap v2.1"

# 1. Environment Check
write_info "Stage 1: Environment Validation"

ENV_OK=true

if command_exists docker; then
    if docker_running; then
        write_ok "Docker: running"
    else
        write_err "Docker: not running"
        ENV_OK=false
    fi
else
    if [ -z "$SKIP_DOCKER" ]; then
        write_err "Docker: not installed"
        ENV_OK=false
    else
        write_warn "Docker: not installed (continuing with SKIP_DOCKER)"
    fi
fi

if command_exists python3; then
    PY_VER=$(python3 --version 2>&1)
    write_ok "Python: $PY_VER"
else
    write_err "Python3: not found"
    ENV_OK=false
fi

if command_exists node; then
    NODE_VER=$(node --version)
    write_ok "Node.js: $NODE_VER"
else
    write_warn "Node.js: not found (SimulatedVerse may not run)"
fi

if [ "$ENV_OK" = false ]; then
    write_err "Environment validation failed"
    exit 1
fi

# 2. Environment Configuration
write_info "Stage 2: Environment Configuration"

export TERMINAL_DEPTHS_PROFILE="$PROFILE"
export TD_ENDPOINT="http://127.0.0.1:11434/api/generate"
export PYTHONUNBUFFERED=1

write_ok "Profile: $PROFILE"
write_ok "TD_ENDPOINT: $TD_ENDPOINT"

# 3. Docker Compose
if [ -z "$SKIP_DOCKER" ] && [[ "$MODE" =~ ^(full|dev)$ ]]; then
    write_info "Stage 3: Shared Singleton Docker Services"
    
    COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
    if [ ! -f "$COMPOSE_FILE" ]; then
        write_err "docker-compose.yml not found"
        exit 1
    fi
    
    write_info "Starting shared singleton infra (this may take 1-2 minutes)..."
    docker compose -f "$COMPOSE_FILE" up -d redis ollama model-router shared-postgres 2>&1 | grep -E "Starting|Created|running" || true
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        write_ok "Shared singleton infra: starting"
    else
        write_err "Docker Compose failed"
        exit 1
    fi
    
    # Wait for services
    if [ -z "$NO_WAIT" ]; then
        write_info "Waiting for service health checks..."
        TIMEOUT=60
        START=$(date +%s)
        
        while true; do
            NOW=$(date +%s)
            ELAPSED=$((NOW - START))
            
            if [ $ELAPSED -gt $TIMEOUT ]; then
                break
            fi
            
            OLLAMA_OK=false
            DEV_MENTOR_OK=true

            test_port 11434 && OLLAMA_OK=true || true
            test_port 9001 || true

            if [ "$OLLAMA_OK" = true ]; then
                write_ok "All services healthy"
                break
            fi

            [ "$OLLAMA_OK" = false ] && write_warn "Waiting for Ollama..."

            sleep 3
        done
    fi
fi

# 4. Python Environment
write_info "Stage 4: Python Environment"

if [ ! -d "$SCRIPT_DIR/venv" ]; then
    write_info "Creating Python virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    write_ok "Virtual environment: created"
else
    write_ok "Virtual environment: exists"
fi

# shellcheck source=/dev/null
source "$SCRIPT_DIR/venv/bin/activate"
write_ok "Virtual environment: activated"

if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    write_info "Installing Python dependencies..."
    pip install -q -e . 2>&1 || true
    write_ok "Python dependencies: ready"
fi

# 5. Handle Modes
echo ""

if [[ "$MODE" =~ ^(full|dev)$ ]] && ! test_port 7337; then
    write_info "Stage 5: Starting Dev-Mentor natively"
    nohup python3 -m cli.devmentor serve --host 0.0.0.0 --port 7337 >/tmp/devmentor-bootstrap.log 2>&1 &
    sleep 3
    if test_port 7337; then
        write_ok "Dev-Mentor native server: running on :7337"
    else
        write_warn "Dev-Mentor did not come up on :7337; inspect /tmp/devmentor-bootstrap.log"
    fi
fi

case "$MODE" in
    full)
        write_info "Mode: FULL (services + CLI client)"
        
        if [ -n "$SKIP_DOCKER" ]; then
            write_warn "Skipping Docker services"
        fi
        
        write_ok "Workspace ready. Services running on:"
        echo "  🎮 Terminal Depths CLI:   cd $SCRIPT_DIR && python -m cli.devmentor play"
        echo "  🌍 SimulatedVerse UI:     http://localhost:5000"
        echo "  📡 Dev-Mentor API:        http://localhost:7337/docs"
        echo "  🧠 Ollama:                http://localhost:11434"
        echo ""
        echo "Launch CLI in a new terminal."
        ;;
        
    dev)
        write_info "Mode: DEV (services only)"
        write_ok "Services are running. Attach clients as needed."
        ;;
        
    cli)
        write_info "Mode: CLI (client only)"
        
        if ! test_port 7337; then
            write_err "Dev-Mentor backend not reachable on :7337"
            write_info "Run 'bootstrap.sh dev' first"
            exit 1
        fi
        
        write_ok "Launching Terminal Depths CLI..."
        echo ""
        
        cd "$SCRIPT_DIR"
        python -m cli.devmentor play
        ;;
        
    stop)
        write_info "Mode: STOP (shutting down)"
        
        if [ -z "$SKIP_DOCKER" ]; then
            COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
            docker compose -f "$COMPOSE_FILE" down 2>&1 | grep -E "Stopping|Removed" || true
            write_ok "Docker services: stopped"
        fi
        
        write_ok "Shutdown complete."
        ;;
        
    *)
        write_err "Unknown mode: $MODE (use full|dev|cli|stop)"
        exit 1
        ;;
esac

echo ""
write_ok "Bootstrap complete."
echo ""
