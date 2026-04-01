#!/usr/bin/env bash
set -euo pipefail

probe() { curl -sS --max-time 2 "$1/models" | grep -q '"data"'; }

# Preferred order: local OpenAI-compat → LiteLLM → Ollama → vacuum
CANDIDATES=(
  "http://127.0.0.1:4455/v1"      # LiteLLM proxy
  "http://127.0.0.1:11434/v1"     # llama.cpp server in oai-compat mode
  "http://127.0.0.1:5005/v1"      # Kobold/TGI/vLLM
)

FOUND=""
for base in "${CANDIDATES[@]}"; do
  if probe "$base"; then FOUND="$base"; break; fi
done

if [[ -z "$FOUND" ]]; then
  echo "VACUUM" # Non-LLM mode
else
  echo "$FOUND"
fi