#!/usr/bin/env bash
# Terminal Depths — Bash/Curl Quickstart
# ════════════════════════════════════════════════════════════════════════════════
# Universal entry point for any bash/curl environment.
# Requirements: bash 4+, curl, jq (optional but recommended)
#
# Usage:
#   bash bootstrap/td_quickstart.sh
#   TD_URL=https://my.replit.app bash bootstrap/td_quickstart.sh
#   TD_AGENT_NAME="Gordon" TD_AGENT_TYPE="docker_agent" bash ...
#   echo "ls" | bash bootstrap/td_quickstart.sh
# ════════════════════════════════════════════════════════════════════════════════

set -euo pipefail

TD_URL="${TD_URL:-http://localhost:5000}"
TD_TOKEN_FILE="${TD_TOKEN_FILE:-$HOME/.td_token}"
AGENT_NAME="${TD_AGENT_NAME:-}"
AGENT_TYPE="${TD_AGENT_TYPE:-human}"
NO_COLOR="${TD_NO_COLOR:-}"

# ── Colors ────────────────────────────────────────────────────────────────────
if [ -z "$NO_COLOR" ] && [ -t 1 ]; then
  GRN='\033[32m'; CYN='\033[36m'; DIM='\033[2m'
  RED='\033[31m'; YLW='\033[33m'; MGT='\033[35m'; RST='\033[0m'; BLD='\033[1m'
else
  GRN=''; CYN=''; DIM=''; RED=''; YLW=''; MGT=''; RST=''; BLD=''
fi

_ok()   { echo -e "${GRN}  ✓ $*${RST}"; }
_err()  { echo -e "${RED}  ✗ $*${RST}"; }
_info() { echo -e "${CYN}  · $*${RST}"; }
_dim()  { echo -e "${DIM}  $*${RST}"; }

# ── Helpers ───────────────────────────────────────────────────────────────────
_curl_post() {
  local path="$1" body="$2" token="${3:-}"
  local headers=(-H "Content-Type: application/json")
  [ -n "$token" ] && headers+=(-H "X-Agent-Token: $token")
  curl -sf "${headers[@]}" -X POST -d "$body" "${TD_URL}${path}" 2>/dev/null || echo '{"error":"curl failed"}'
}

_curl_get() {
  local path="$1" token="${2:-}"
  local headers=()
  [ -n "$token" ] && headers+=(-H "X-Agent-Token: $token")
  curl -sf "${headers[@]}" "${TD_URL}${path}" 2>/dev/null || echo '{"error":"curl failed"}'
}

_parse_output() {
  local json="$1"
  if command -v jq &>/dev/null; then
    echo "$json" | jq -r '.output[]? | .s // empty' 2>/dev/null || echo "$json"
  else
    # Fallback: extract "s" values with basic sed
    echo "$json" | grep -o '"s":"[^"]*"' | sed 's/"s":"//; s/"$//' || echo "$json"
  fi
}

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLD}${CYN}  ◈ TERMINAL DEPTHS — Bash Quickstart${RST}"
_dim "Server: $TD_URL"
echo ""

# ── Health check ──────────────────────────────────────────────────────────────
health=$(_curl_get "/api/health")
if echo "$health" | grep -q '"error"'; then
  _err "Server unreachable at $TD_URL"
  _dim "Start server: python -m cli.devmentor serve"
  exit 1
fi
_ok "Server reachable"

# ── Load or register agent ────────────────────────────────────────────────────
TOKEN=""
AGENT_ID=""
SESSION_ID=""

if [ -f "$TD_TOKEN_FILE" ] && command -v jq &>/dev/null; then
  saved_server=$(jq -r '.server // ""' "$TD_TOKEN_FILE" 2>/dev/null)
  if [ "$saved_server" = "$TD_URL" ]; then
    TOKEN=$(jq -r '.token // ""' "$TD_TOKEN_FILE" 2>/dev/null)
    AGENT_ID=$(jq -r '.agent_id // ""' "$TD_TOKEN_FILE" 2>/dev/null)
    saved_name=$(jq -r '.name // ""' "$TD_TOKEN_FILE" 2>/dev/null)
    if [ -n "$TOKEN" ]; then
      profile=$(_curl_get "/api/agent/profile" "$TOKEN")
      if ! echo "$profile" | grep -q '"error"'; then
        _ok "Loaded identity: $saved_name"
      else
        TOKEN=""  # token invalid, re-register
      fi
    fi
  fi
fi

if [ -z "$TOKEN" ]; then
  if [ -z "$AGENT_NAME" ]; then
    if [ -t 0 ]; then
      read -rp "  Agent name [${USER:-agent}]: " AGENT_NAME
      AGENT_NAME="${AGENT_NAME:-${USER:-agent}}"
    else
      AGENT_NAME="${USER:-agent}"
    fi
  fi
  HOSTNAME_SLUG=$(hostname 2>/dev/null | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-')
  EMAIL="${AGENT_NAME,,}@${HOSTNAME_SLUG}.terminal-depths"
  EMAIL=$(echo "$EMAIL" | tr ' ' '_')
  
  body=$(printf '{"name":"%s","email":"%s","agent_type":"%s"}' \
    "$AGENT_NAME" "$EMAIL" "$AGENT_TYPE")
  result=$(_curl_post "/api/agent/register" "$body")
  
  if echo "$result" | grep -q '"error"'; then
    _err "Registration failed"
    echo "$result"
    exit 1
  fi
  
  if command -v jq &>/dev/null; then
    TOKEN=$(echo "$result" | jq -r '.token')
    AGENT_ID=$(echo "$result" | jq -r '.agent_id')
    SESSION_ID=$(echo "$result" | jq -r '.session_id')
    printf '{"token":"%s","agent_id":"%s","name":"%s","server":"%s"}' \
      "$TOKEN" "$AGENT_ID" "$AGENT_NAME" "$TD_URL" > "$TD_TOKEN_FILE"
  fi
  
  _ok "Registered: $AGENT_NAME [$AGENT_TYPE]"
  _dim "Token saved to $TD_TOKEN_FILE"
fi

# ── Run command ───────────────────────────────────────────────────────────────
run_cmd() {
  local cmd="$1"
  body=$(printf '{"command":"%s"}' "$(echo "$cmd" | sed 's/"/\\"/g')")
  result=$(_curl_post "/api/agent/command" "$body" "$TOKEN")
  _parse_output "$result"
}

# ── Pipe mode ─────────────────────────────────────────────────────────────────
if [ ! -t 0 ]; then
  while IFS= read -r line; do
    [ -n "$line" ] && run_cmd "$line"
  done
  exit 0
fi

# ── Interactive REPL ──────────────────────────────────────────────────────────
echo -e "${GRN}  Connected. Type 'exit' to quit.${RST}"
_dim "Tip: try 'help', 'tutorial', 'quests', 'hive', 'lore'"
echo ""

while true; do
  printf "${GRN}  ghost@node-7:~\$ ${RST}"
  if ! IFS= read -r cmd; then
    echo ""
    _dim "Session ended. Progress saved."
    break
  fi
  [ -z "$cmd" ] && continue
  [[ "$cmd" =~ ^(exit|quit|q)$ ]] && { _dim "Session ended. Progress saved."; break; }
  run_cmd "$cmd"
  echo ""
done
