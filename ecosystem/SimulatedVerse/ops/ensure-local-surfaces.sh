#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . "${ROOT_DIR}/.env"
  set +a
fi

SIM_PORT="${SIMULATEDVERSE_PORT:-${PORT:-5002}}"
CHATDEV_PORT="${CHATDEV_PORT:-4466}"
SIM_LOG="${TMPDIR:-/tmp}/simulatedverse-minimal.log"
CHATDEV_LOG="${TMPDIR:-/tmp}/chatdev-adapter.log"

check_url() {
  local url="$1"
  curl --silent --fail --max-time 2 "$url" >/dev/null
}

start_detached() {
  local workdir="$1"
  local command="$2"
  local log_file="$3"
  (
    cd "$workdir"
    setsid -f bash -lc "exec ${command} </dev/null >>'${log_file}' 2>&1"
  )
}

wait_for_url() {
  local url="$1"
  local label="$2"
  local attempts="${3:-20}"
  local delay="${4:-1}"
  local i
  for ((i=1; i<=attempts; i++)); do
    if check_url "$url"; then
      printf '[ok] %s -> %s\n' "$label" "$url"
      return 0
    fi
    sleep "$delay"
  done
  printf '[error] %s did not become healthy: %s\n' "$label" "$url" >&2
  return 1
}

ensure_surface() {
  local url="$1"
  local label="$2"
  local workdir="$3"
  local command="$4"
  local log_file="$5"

  if check_url "$url"; then
    printf '[skip] %s already healthy -> %s\n' "$label" "$url"
    return 0
  fi

  printf '[start] %s\n' "$label"
  start_detached "$workdir" "$command" "$log_file"
  wait_for_url "$url" "$label"
}

ensure_surface \
  "http://127.0.0.1:${SIM_PORT}/api/health" \
  "SimulatedVerse minimal" \
  "$ROOT_DIR" \
  "npm run dev:minimal" \
  "$SIM_LOG"

ensure_surface \
  "http://127.0.0.1:${CHATDEV_PORT}/chatdev/agents" \
  "ChatDev adapter" \
  "$ROOT_DIR/packages/chatdev-adapter" \
  "npm run start" \
  "$CHATDEV_LOG"

printf '[done] local surfaces ready\n'
