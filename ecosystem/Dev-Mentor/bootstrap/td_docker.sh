#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════════
# Terminal Depths — Docker Bootstrap
# One-liner to play Terminal Depths from a Docker container.
#
# Usage (replace <URL> with your Terminal Depths server URL):
#
#   # Interactive REPL:
#   docker run --rm -it \
#     -e TD_URL=https://your-repl.replit.app \
#     -e TD_AGENT_NAME="DockerAgent" \
#     -e TD_AGENT_TYPE="docker_agent" \
#     python:3.11-slim \
#     bash -c "pip install -q requests && curl -fsSL $TD_URL/static/td_quickstart.py | python3"
#
#   # OR: copy this file into your container and run it:
#   docker run --rm -it \
#     -v "$(pwd)/bootstrap:/bootstrap" \
#     -e TD_URL=https://your-repl.replit.app \
#     python:3.11-slim \
#     python3 /bootstrap/td_quickstart.py
#
#   # Minimal one-liner (no Python, just curl + bash):
#   docker run --rm -it \
#     -e TD_URL=https://your-repl.replit.app \
#     -e TD_AGENT_NAME="DockerCurl" \
#     curlimages/curl:latest \
#     sh -c "$(curl -fsSL $TD_URL/static/td_quickstart.sh)"
#
# Environment variables:
#   TD_URL         — Terminal Depths server URL (required)
#   TD_AGENT_NAME  — Agent display name (default: DockerAgent)
#   TD_AGENT_EMAIL — Agent email (auto-generated if not set)
#   TD_AGENT_TYPE  — Agent type (default: docker_agent)
#   TD_TOKEN       — Existing token (skips registration)
# ════════════════════════════════════════════════════════════════════════════
set -euo pipefail

TD_URL="${TD_URL:-}"
TD_AGENT_NAME="${TD_AGENT_NAME:-DockerAgent}"
TD_AGENT_TYPE="${TD_AGENT_TYPE:-docker_agent}"
TD_TOKEN="${TD_TOKEN:-}"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
DIM='\033[2m'
RESET='\033[0m'

log() { echo -e "${CYAN}[TD-DOCKER]${RESET} $*"; }
ok()  { echo -e "${GREEN}[✓]${RESET} $*"; }
err() { echo -e "${RED}[✗]${RESET} $*" >&2; }

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         TERMINAL DEPTHS — DOCKER SURFACE                ║"
echo "║         Connecting from container...                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Validate TD_URL ───────────────────────────────────────────────────────
if [[ -z "$TD_URL" ]]; then
    log "TD_URL not set. Probing defaults..."
    for url in "http://localhost:5000" "http://host.docker.internal:5000"; do
        if curl -sf "${url}/api/health" > /dev/null 2>&1; then
            TD_URL="$url"
            ok "Found server at $TD_URL"
            break
        fi
    done
    if [[ -z "$TD_URL" ]]; then
        err "Cannot find Terminal Depths server."
        err "Set TD_URL: docker run ... -e TD_URL=https://your-server.replit.app ..."
        exit 1
    fi
fi

log "Server: $TD_URL"

# ── Health check ──────────────────────────────────────────────────────────
if ! curl -sf "${TD_URL}/api/health" > /dev/null 2>&1; then
    err "Server at $TD_URL is not responding."
    exit 1
fi
ok "Server is alive."

# ── Register or use existing token ────────────────────────────────────────
if [[ -z "$TD_TOKEN" ]]; then
    CONTAINER_ID="${HOSTNAME:-docker-$(date +%s)}"
    EMAIL="${TD_AGENT_EMAIL:-${TD_AGENT_NAME}@docker.terminal-depths.local}"
    EMAIL="${EMAIL,,}"  # lowercase
    EMAIL="${EMAIL// /-}"

    log "Registering as '$TD_AGENT_NAME' (${TD_AGENT_TYPE})..."

    REGISTER_RESPONSE=$(curl -sf -X POST \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"${TD_AGENT_NAME}\",\"email\":\"${EMAIL}\",\"agent_type\":\"${TD_AGENT_TYPE}\",\"capabilities\":[\"docker\",\"bash\"]}" \
        "${TD_URL}/api/agent/register" 2>&1) || {
        err "Registration failed: $REGISTER_RESPONSE"
        exit 1
    }

    TD_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token',''))" 2>/dev/null)
    SESSION_ID=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)

    if [[ -z "$TD_TOKEN" ]]; then
        err "Registration failed. Response: $REGISTER_RESPONSE"
        exit 1
    fi
    ok "Registered. Token: ${TD_TOKEN:0:12}..."
    ok "Session: $SESSION_ID"
    echo "$TD_TOKEN" > "${HOME:-/root}/.td_token" 2>/dev/null || true
else
    ok "Using provided token: ${TD_TOKEN:0:12}..."
fi

# ── Run initial commands ──────────────────────────────────────────────────
run_command() {
    local cmd="$1"
    local response
    response=$(curl -sf -X POST \
        -H "Content-Type: application/json" \
        -H "X-Agent-Token: $TD_TOKEN" \
        -d "{\"command\":\"${cmd}\"}" \
        "${TD_URL}/api/agent/command" 2>/dev/null) || echo '[]'
    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if isinstance(data, dict):
    data = data.get('output', [])
for item in data:
    text = item.get('s', item.get('text', ''))
    if text:
        print(text)
" 2>/dev/null
}

log "Running intro sequence..."
echo ""
run_command "motd"
echo ""
run_command "status"
echo ""

# ── Interactive REPL ──────────────────────────────────────────────────────
log "Entering interactive REPL. Type 'help' for commands, 'quit' to exit."
echo ""
echo -e "${DIM}  (You are playing as: ${TD_AGENT_NAME} | Type: ${TD_AGENT_TYPE})${RESET}"
echo ""

while true; do
    printf "${CYAN}ghost@node-7 \$${RESET} "
    if ! read -r user_input 2>/dev/null; then
        echo ""
        log "EOF — exiting."
        break
    fi

    if [[ -z "$user_input" ]]; then continue; fi
    if [[ "$user_input" =~ ^(quit|exit|q)$ ]]; then
        log "Session ended. Progress saved."
        break
    fi

    response=$(curl -sf -X POST \
        -H "Content-Type: application/json" \
        -H "X-Agent-Token: $TD_TOKEN" \
        -d "{\"command\":$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$user_input")}" \
        "${TD_URL}/api/agent/command" 2>/dev/null) || { echo "  (connection error)"; continue; }

    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if isinstance(data, dict):
    data = data.get('output', [])
for item in data:
    text = item.get('s', item.get('text', ''))
    if text:
        print(text)
" 2>/dev/null
    echo ""
done

echo ""
log "Docker session complete. Token saved at ~/.td_token"
