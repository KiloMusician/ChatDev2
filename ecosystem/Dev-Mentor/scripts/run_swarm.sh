#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════════
# Terminal Depths — Swarm Launcher
# Starts the autonomous development organism in multiple modes.
#
# Usage:
#   ./scripts/run_swarm.sh               # Full swarm (all roles)
#   ./scripts/run_swarm.sh --init        # Phase 0 init only
#   ./scripts/run_swarm.sh --scout       # Run scouts only
#   ./scripts/run_swarm.sh --lore        # Run lorekeepers only
#   ./scripts/run_swarm.sh --test        # Run testers only
#   ./scripts/run_swarm.sh --status      # Show swarm status
# ════════════════════════════════════════════════════════════════════════════
set -euo pipefail

TD_URL="${TD_URL:-http://localhost:5000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
DIM='\033[2m'
RESET='\033[0m'

log()  { echo -e "${CYAN}[SWARM]${RESET} $*"; }
ok()   { echo -e "${GREEN}[✓]${RESET} $*"; }
err()  { echo -e "${RED}[✗]${RESET} $*" >&2; }
dim()  { echo -e "${DIM}$*${RESET}"; }

# ── Health check ──────────────────────────────────────────────────────────
health_check() {
    if curl -sf "${TD_URL}/api/health" > /dev/null 2>&1; then
        ok "Game API at ${TD_URL} is alive"
        return 0
    else
        err "Game API is down. Start with: python -m cli.devmentor serve"
        return 1
    fi
}

# ── Status ────────────────────────────────────────────────────────────────
show_status() {
    echo ""
    log "Swarm Status:"
    curl -sf "${TD_URL}/api/swarm/status" 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
if not data.get('ok'):
    print('  Swarm offline.')
    sys.exit(0)
print(f'  Phase:   {data[\"phase\"]}')
print(f'  DP:      {data[\"dp_balance\"]} pts')
print(f'  Agents:  {data[\"agents\"][\"total\"]}')
tasks = data.get('tasks', {})
print(f'  Tasks:   {tasks.get(\"open\",0)} open / {tasks.get(\"done\",0)} done')
" || dim "  (swarm controller unavailable)"
    echo ""
}

# ── Init ─────────────────────────────────────────────────────────────────
run_init() {
    log "Running Phase 0 initialization..."
    python3 "$SCRIPT_DIR/swarm_init.py" "$@"
}

# ── Run scouts ───────────────────────────────────────────────────────────
run_scouts() {
    log "Launching 3 scouts..."
    for i in 1 2 3; do
        log "Scout-$i starting..."
        python3 "$SCRIPT_DIR/swarm_agent.py" \
            --role scout \
            --name "AutoScout-$i" \
            --loops 2 &
        sleep 0.5
    done
    wait
    ok "All scouts complete."
}

# ── Run lorekeepers ──────────────────────────────────────────────────────
run_lorekeepers() {
    log "Launching 2 lorekeepers..."
    for i in 1 2; do
        python3 "$SCRIPT_DIR/swarm_agent.py" \
            --role lorekeeper \
            --name "AutoLore-$i" \
            --loops 2 &
        sleep 0.5
    done
    wait
    ok "All lorekeepers complete."
}

# ── Run testers ──────────────────────────────────────────────────────────
run_testers() {
    log "Launching 2 testers..."
    for i in 1 2; do
        python3 "$SCRIPT_DIR/swarm_agent.py" \
            --role tester \
            --name "AutoTest-$i" \
            --loops 2 &
        sleep 0.5
    done
    wait
    ok "All testers complete."
}

# ── Full swarm ───────────────────────────────────────────────────────────
run_full() {
    log "Launching full swarm (scouts + lorekeepers + testers)..."
    run_scouts &
    sleep 1
    run_lorekeepers &
    sleep 1
    run_testers &
    wait
    ok "Full swarm cycle complete."
    show_status
}

# ── Main ─────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         TERMINAL DEPTHS — SWARM LAUNCHER                ║"
echo "║         The development organism activates.             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

health_check || exit 1

case "${1:-full}" in
    --init)   run_init "${@:2}" ;;
    --scout)  run_scouts ;;
    --lore)   run_lorekeepers ;;
    --test)   run_testers ;;
    --status) show_status ;;
    --full|full|*) run_full ;;
esac

echo ""
log "Swarm session complete. Check /api/swarm/status for DP balance."
