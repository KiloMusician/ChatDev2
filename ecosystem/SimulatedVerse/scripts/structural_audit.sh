#!/usr/bin/env bash
set -euo pipefail
mkdir -p reports
todos=$(rg -n --no-heading 'TODO|FIXME' --glob '!node_modules' --glob '!.git' | wc -l | tr -d ' ')
logs=$(rg -n --no-heading 'console\.log|print\(' --glob '!node_modules' --glob '!.git' | wc -l | tr -d ' ')
big=$(find . -type f -size +25M -not -path "./node_modules/*" -not -path "./.git/*" | wc -l | tr -d ' ')
jq -n --arg ts "$(date -Iseconds)" --argjson todos "$todos" --argjson logs "$logs" --argjson big "$big" \
'{"timestamp":$ts,"audit":{"todos":$todos,"logs":$logs,"oversized":$big}}' > reports/repo_audit.json
echo "AUDIT: $(cat reports/repo_audit.json)"