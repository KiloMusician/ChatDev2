#!/usr/bin/env bash
set -euo pipefail
jq -n --arg ts "$(date -Iseconds)" \
--argjson receipts "$(ls reports/*.json 2>/dev/null | sort | jq -R -s -c 'split("\n")|map(select(length>0))')" \
'{"timestamp":$ts,"receipts":$receipts}' > reports/_index.json
echo "RECEIPTS: reports/_index.json"