#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Preparing environment…"
python -m pip install -q aider-chat open-interpreter smolagents litellm semgrep comby ruff black isort mypy bandit gdtoolkit sentence-transformers
npm -s i -D eslint prettier typescript @types/node jscodeshift ts-morph

echo "🧠 Detecting LLM spine…"
chmod +x ops/spine/detect_spine.sh ops/spine/detect_env.sh ops/llm/serve_llama.sh
BASE=$(bash ops/spine/detect_spine.sh)
if [[ "$BASE" == "VACUUM" ]]; then
  echo "➡️  VACUUM mode enabled"
else
  export OPENAI_BASE_URL="$BASE"
  export OPENAI_API_KEY="sk-local"
  echo "➡️  LLM at $OPENAI_BASE_URL"
fi

echo "🧹 Running mechanical fixes…"
just -f ops/tasks/justfile fix 2>/dev/null || make -f ops/tasks/pipelines.mk fix

echo "📚 Seeding local index…"
python - <<'PY'
import os, subprocess
os.makedirs("ops/receipts", exist_ok=True)
print("✅ Ready.")
PY