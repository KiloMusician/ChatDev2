#!/usr/bin/env bash
set -euo pipefail

ts="$(date -u +%Y%m%d_%H%M%S)"
out="reports/colony_audit_${ts}.json"

# cheap scans (no network)
files_total="$(find . -type f \( -name "*.ts" -o -name "*.js" -o -name "*.json" -o -name "*.md" -o -name "*.rtf" \) -not -path "./node_modules/*" | wc -l | tr -d ' ')"
todos="$(grep -RniI --exclude-dir=node_modules -E "TODO|FIXME" || true)"
todos_count="$(printf "%s" "$todos" | grep -c . || true)"
consoles_count="$(find src -type f \( -name "*.ts" -o -name "*.js" \) -not -path "*/node_modules/*" -print0 2>/dev/null | xargs -0 grep -c "console\." 2>/dev/null | awk -F: '{s+=$2} END{print s+0}' || echo "0")"

# agent map (active/dormant/locked heuristics)
map=$(cat <<'MAP'
{
  "agents": {
    "replit": "active",
    "sage_pilot": "active",
    "copilot": "dormant",
    "vscode": "dormant",
    "culture_ship": "active",
    "rossetta_core": "active",
    "msgX": "active",
    "ui_preview": "active",
    "idle_engine": "dormant",
    "guardian": "dormant",
    "git_steward": "active"
  }
}
MAP
)

# Create JSON output using printf and basic shell tools
cat > "$out" <<JSON
{
  "stage": "colony_audit",
  "timestamp": "${ts}",
  "counts": {
    "files_total": ${files_total},
    "todos": ${todos_count},
    "consoles": ${consoles_count}
  },
  "agents": $(printf '%s' "$map" | grep -A 20 '"agents"'),
  "rosetta_files": $(ls knowledge/rosetta 2>/dev/null | wc -l | tr -d ' '),
  "next_hint": "run rosetta_ingest.sh then ui_deepmerge.sh"
}
JSON

echo "OK: $out"