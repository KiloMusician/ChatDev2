#!/usr/bin/env bash
set -euo pipefail

SIMVERSE_DIR="${SIMVERSE_DIR:-/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse}"
PORT="${SIMULATEDVERSE_PORT:-5002}"
HOST="${SIMULATEDVERSE_HOST:-127.0.0.1}"
LOG_FILE="${SIMVERSE_LOG_FILE:-${SIMVERSE_DIR}/simv_daemon.log}"
PID_FILE="${SIMVERSE_PID_FILE:-/tmp/simv_daemon.pid}"
HEALTH_URL="http://${HOST}:${PORT}/api/health"

if [ ! -d "$SIMVERSE_DIR" ]; then
    echo "SimulatedVerse path not found: $SIMVERSE_DIR" >&2
    exit 1
fi

if [ -f "$PID_FILE" ]; then
    existing_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [ -n "${existing_pid:-}" ] && kill -0 "$existing_pid" 2>/dev/null; then
        if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
            echo "SimulatedVerse daemon already running (PID $existing_pid)"
            exit 0
        fi
    fi
fi

if ! curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
    stale_pid="$(ss -ltnp 2>/dev/null | awk -v port=":${PORT}" '$4 ~ port { if (match($0, /pid=[0-9]+/)) { print substr($0, RSTART + 4, RLENGTH - 4); exit } }')"
    if [ -n "${stale_pid:-}" ] && kill -0 "$stale_pid" 2>/dev/null; then
        echo "Clearing stale SimulatedVerse listener on :$PORT (PID $stale_pid)"
        kill "$stale_pid" 2>/dev/null || true
        sleep 2
    fi
fi

cd "$SIMVERSE_DIR"

export PORT="$PORT"
export SIMULATEDVERSE_PORT="$PORT"
export SIMULATEDVERSE_HOST="$HOST"
export NODE_ENV="${NODE_ENV:-development}"
export TMPDIR="${TMPDIR:-/tmp}"
export SIMULATEDVERSE_FULL_STARTUP_TIMEOUT_MS="${SIMULATEDVERSE_FULL_STARTUP_TIMEOUT_MS:-10000}"
export SIMULATEDVERSE_DEGRADED_STARTUP_TIMEOUT_MS="${SIMULATEDVERSE_DEGRADED_STARTUP_TIMEOUT_MS:-20000}"

nohup setsid node --env-file=.env --import tsx/esm server/startup_fallback.ts >>"$LOG_FILE" 2>&1 &
daemon_pid=$!
echo "$daemon_pid" >"$PID_FILE"
echo "SimulatedVerse daemon started (PID $daemon_pid)"
