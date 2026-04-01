#!/usr/bin/env bash
set -euo pipefail
ENGINE="${ENGINE:-ollama}"     # local first; fallback: OPENAI=false
MODEL="${MODEL:-qwen2.5:1.5b}" # tiny local model by default
MAXTOK="${MAXTOK:-128}"
TEMP="${TEMP:-0}"
PROMPT_FILE="${1:?prompt file}"; shift
FILEPATH="${1:?target file}"; shift

if command -v ollama >/dev/null; then
  printf "### FILE: %s\n\n" "$FILEPATH"
  {
    echo "SYSTEM: You are a static analyzer. Be terse. Output a bullet list of defects only."
    echo "CONSTRAINTS: max ${MAXTOK} tokens, no code rewriting."
    echo "PROMPT:"
    cat "$PROMPT_FILE"
    echo
    echo "=== FILE CONTENT START (first 300 lines) ==="
    sed -n '1,300p' "$FILEPATH"
    echo "=== FILE CONTENT END ==="
  } | ollama run "$MODEL" -p -
else
  echo "[skip] ollama not found; no token spend."
fi