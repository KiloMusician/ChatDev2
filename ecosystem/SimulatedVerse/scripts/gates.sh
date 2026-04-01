#!/usr/bin/env bash
set -euo pipefail
ts=$(date -Iseconds)
mkdir -p reports public
# G1: LLM Spine (Ollama/Gateway/OpenAI env presence checks only; no calls)
ollama="${OLLAMA_HOST:-http://127.0.0.1:11434}"
gateway="${LLM_GATEWAY_URL:-http://127.0.0.1:4455}"
model="${OPENAI_MODEL:-gpt-4o-mini}"

g1="DOWN"
if curl -s --max-time 2 "$ollama/api/version" >/dev/null 2>&1; then g1="OLLAMA_OK"; else
  if curl -s --max-time 2 "$gateway/health" >/dev/null 2>&1; then g1="GATEWAY_OK"; else
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then g1="OPENAI_KEY_PRESENT"; fi
  fi
fi

# G2: Queue Live (≥1 backlog item exists?)
backlog=$(ls backlog/next_up/*.json 2>/dev/null | wc -l | tr -d ' ')
g2=$([ "$backlog" -ge 1 ] && echo "LIVE" || echo "EMPTY")

# G3: UI Fresh (system-status.json mtime Δ<=60s?)
ui="STALE"
if [[ -f public/system-status.json ]]; then
  delta=$(( $(date +%s) - $(stat -c %Y public/system-status.json) ))
  [[ $delta -le 60 ]] && ui="FRESH"
else ui="MISSING"; fi
g3="$ui"

# G4: Disk/Noise (growth < 50 files/min. We measure current file count only)
files=$(find . -type f -not -path "./.git/*" -not -path "./node_modules/*" | wc -l | tr -d ' ')
g4="MEASURED"

jq -n --arg ts "$ts" --arg g1 "$g1" --arg g2 "$g2" --arg g3 "$g3" --arg g4 "$g4" \
--argjson backlog "$backlog" --argjson files "$files" '
{timestamp:$ts, gates:{llm_spine:$g1, queue:$g2, ui:$g3, disk:$g4}, counts:{backlog:$backlog, files:$files}}' \
> reports/gates_status.json

cp reports/gates_status.json public/system-status.json
echo "GATES: $(cat reports/gates_status.json)"