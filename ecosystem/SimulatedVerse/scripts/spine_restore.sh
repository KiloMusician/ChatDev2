#!/usr/bin/env bash
set -euo pipefail
mkdir -p reports .prox
ts=$(date -Iseconds)
ollama="${OLLAMA_HOST:-http://127.0.0.1:11434}"
gateway="${LLM_GATEWAY_URL:-http://127.0.0.1:4455}"
status="FAILED"
plan=""

# A) Native launch (if binary present)
if command -v ollama >/dev/null 2>&1; then
  (OLLAMA_HOST="$ollama" nohup ollama serve >/dev/null 2>&1 & echo $! > .prox/ollama.pid) || true
  sleep 0.2
  curl -s --max-time 2 "$ollama/api/version" >/dev/null 2>&1 && { status="OLLAMA_LOCAL_UP"; plan="A"; }
fi

# B) Llama.cpp micro-server fallback (HTTP relay)
if [[ "$status" = "FAILED" ]] && command -v server >/dev/null 2>&1; then
  # assumes compiled llama.cpp `server` is present & a GGUF at models/tiny.gguf
  (nohup server -m models/tiny.gguf -c 2048 -ngl 0 --port 8089 >/dev/null 2>&1 & echo $! > .prox/llamacpp.pid) || true
  sleep 0.2
  nc -z localhost 8089 >/dev/null 2>&1 && { status="LLAMACPP_UP"; plan="B"; }
fi

# C) Cloud gateway via cloudflared/ngrok (Quantum tunnel)
if [[ "$status" = "FAILED" ]] && command -v cloudflared >/dev/null 2>&1; then
  (nohup cloudflared tunnel --url http://127.0.0.1:11434 > .prox/cloudflared.log 2>&1 & echo $! > .prox/cloudflared.pid) || true
  sleep 0.2
  grep -m1 -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' .prox/cloudflared.log > .prox/ollama_url.txt || true
  if [[ -s .prox/ollama_url.txt ]]; then export OLLAMA_HOST="$(cat .prox/ollama_url.txt)"; status="OLLAMA_VIA_TUNNEL"; plan="C"; fi
fi

# D) Remote sidecar (Tailscale/SSH reverse); requires env TS_IP/SSH_URI
if [[ "$status" = "FAILED" && -n "${OLLAMA_REMOTE_URL:-}" ]]; then
  export OLLAMA_HOST="$OLLAMA_REMOTE_URL"
  curl -s --max-time 2 "$OLLAMA_HOST/api/version" >/dev/null 2>&1 && { status="OLLAMA_REMOTE_OK"; plan="D"; }
fi

jq -n --arg ts "$ts" --arg status "$status" --arg plan "$plan" \
'{"timestamp":$ts,"spine_restore":{"status":$status,"plan":$plan}}' > reports/spine_restore.json
echo "SPINE: $(cat reports/spine_restore.json)"