#!/usr/bin/env bash
set -euo pipefail
PROMPT="${1:-"ping"}"
OLLAMA="${OLLAMA_HOST:-http://127.0.0.1:11434}"
GATE="${LLM_GATEWAY_URL:-http://127.0.0.1:4455}"
USE_OPENAI="${OPENAI_API_KEY:-}"
fail() { echo "$1"; return 1; }

probe_ollama(){ curl -fsS --max-time 2 "$OLLAMA/api/version" >/dev/null; }
probe_gate(){ curl -fsS --max-time 2 "$GATE/health" >/dev/null; }

# Try Ollama
if probe_ollama; then
  curl -fsS "$OLLAMA/api/generate" -H 'Content-Type: application/json' \
    -d "{\"model\":\"qwen2.5:7b-instruct\",\"prompt\":\"$PROMPT\",\"stream\":false}" \
    || true
  exit 0
fi

# Try Gateway
if probe_gate; then
  curl -fsS "$GATE/llm/chat" -H 'Content-Type: application/json' \
    -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$PROMPT\"}],\"stream\":false}" \
    || true
  exit 0
fi

# Try OpenAI once
if [ -n "$USE_OPENAI" ]; then
  curl -fsS https://api.openai.com/v1/chat/completions \
    -H "Authorization: Bearer $USE_OPENAI" -H "Content-Type: application/json" \
    -d "{\"model\":\"${OPENAI_MODEL:-gpt-4o-mini}\",\"messages\":[{\"role\":\"user\",\"content\":\"$PROMPT\"}],\"temperature\":0.2}" \
    || true
  exit 0
fi

# Vacuum mode: no-op that returns empty JSON; caller must be robust to this.
echo '{"mode":"vacuum","ok":true,"note":"LLM backends unavailable"}'
