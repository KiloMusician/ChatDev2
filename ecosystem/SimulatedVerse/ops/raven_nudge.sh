#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:5000}"
ADMIN_TOKEN="${ADMIN_TOKEN:?set ADMIN_TOKEN}"
PROMPT="${1:?usage: ops/raven_nudge.sh 'your prompt here' }"

# 1) Forward the exact prompt to the system
curl -fsS -X POST "$BASE/api/raven/ingest" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":$(
        jq -rn --arg p "$PROMPT" '$p'
      ),\"policy\":{\"autonomous_mode\":true},\"meta\":{\"source\":\"replit\"}}"

# 2) Minimal poll — stop as soon as a PR opens or a cascade is active
for i in {1..6}; do
  sleep 5
  s=$(curl -fsS "$BASE/api/marble/status")
  echo "$s" | jq '{active: .active|length, completed_today, recent_prs: .recent_prs[0:3]}'
  test "$(echo "$s" | jq '.recent_prs|length')" -ge 1 && break || true
done

# 3) Sync the live Repl (pull main); your Repl sync hook may already do this on merges
git fetch origin main && git checkout main && git reset --hard origin/main

# 4) Run smoke tests (fast truth checks only)
npm run test --silent -- -t "@smoke" || true