#!/usr/bin/env bash
set -euo pipefail
passes="${1:-12}"
for i in $(seq 1 "$passes"); do
  echo "=== PASS $i ==="
  ./run.sh gates
  ./run.sh ingest
  ./run.sh council
  ./run.sh theater
  ./run.sh receipts
  # Adaptive pause only if queue empty AND no file deltas
  q=$(ls backlog/next_up/*.json 2>/dev/null | wc -l | tr -d ' ')
  d=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  [[ $q -eq 0 && $d -eq 0 ]] && sleep 1 || true
done