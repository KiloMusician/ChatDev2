#!/usr/bin/env bash
set -euo pipefail
. scripts/engines.sh
mkdir -p backlog/next_up reports
out="backlog/ingested_user_work.json"
scan_tasks > reports/_raw_task_hits.ndjson || true
hits=$(wc -l < reports/_raw_task_hits.ndjson 2>/dev/null || echo 0)
> "$out"
echo "[" >> "$out"
i=0
if [[ -s reports/_raw_task_hits.ndjson ]]; then
  while IFS= read -r line; do
    norm=$(printf "%s" "$line" | normalize_task)
    id=$(printf "%s" "$norm" | jq -r .id)
    file="backlog/next_up/${id}.json"
    printf "%s" "$norm" > "$file"
    [[ $i -gt 0 ]] && echo "," >> "$out"
    printf "%s" "$norm" >> "$out"
    i=$((i+1))
  done < reports/_raw_task_hits.ndjson
fi
echo "]" >> "$out"
jq -n --arg ts "$(date -Iseconds)" --argjson found "$hits" \
'{"timestamp":$ts,"ingest":{"hits":$found,"outputs":"backlog/next_up/*"}}' \
> reports/ingest_receipt.json
echo "INGEST: found=$hits → backlog/next_up/, receipt=reports/ingest_receipt.json"