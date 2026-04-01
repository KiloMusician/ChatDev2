#!/usr/bin/env bash
set -euo pipefail
mkdir -p reports
delta_files=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
delta_receipts=$(ls reports/*receipt*.json 2>/dev/null | wc -l | tr -d ' ')
delta_ui=$([ -f public/system-status.json ] && echo 1 || echo 0)
total=$((delta_files + delta_receipts + delta_ui))
k=12
theta=$(awk -v t=$total -v k=$k 'BEGIN{print (t>=k)?0: (k-t)/k}')
jq -n --arg ts "$(date -Iseconds)" --argjson theta "$theta" \
'{"timestamp":$ts,"theater":{"theta":$theta,"k_norm":12}}' > reports/theater_status.json
echo "THEATER θ=$theta"
if awk -v th="$theta" 'BEGIN{exit !(th>0.2)}'; then
  echo "CASCADE: forcing receipts via ingest+council"
  ./run.sh ingest
  ./run.sh council
fi