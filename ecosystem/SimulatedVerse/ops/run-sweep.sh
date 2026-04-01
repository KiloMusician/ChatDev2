#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-5000}"
echo "[1/4] Repo scan…"
tsx tools/repo-scan.ts
echo "[2/4] Enqueue offenders…"
curl -sS -X POST "http://localhost:${PORT}/api/ops/queue" \
  -H "Content-Type: application/x-ndjson" \
  --data-binary @data/_scan/refactor_sweep.ndjson | jq '.'
echo "[3/4] System status…"
curl -sS "http://localhost:${PORT}/api/ops/status" | jq '.'
echo "[4/4] Complete - fake work converted to real tasks!"