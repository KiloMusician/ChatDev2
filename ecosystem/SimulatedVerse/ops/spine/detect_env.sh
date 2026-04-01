#!/usr/bin/env bash
set -euo pipefail

BASE=$(bash ops/spine/detect_spine.sh)
if [[ "$BASE" == "VACUUM" ]]; then
  export OPENAI_BASE_URL=""
  export OPENAI_API_KEY=""
  echo "⚠️  VACUUM mode: non-LLM tools only"
else
  export OPENAI_BASE_URL="$BASE"
  export OPENAI_API_KEY="sk-local"
  echo "✅  LLM spine at $OPENAI_BASE_URL"
fi