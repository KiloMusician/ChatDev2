#!/usr/bin/env bash
set -euo pipefail
mkdir -p reports
has_gd=$(rg -n --no-heading --glob '!node_modules' --glob '!.git' 'extends Node|extends Spatial|class_name' 2>/dev/null | wc -l | tr -d ' ')
jq -n --arg ts "$(date -Iseconds)" --argjson files "$has_gd" \
'{"timestamp":$ts,"godot":{"gdscript_hits":$files,"hud":"unknown","input_loop":"unknown"}}' \
> reports/sim_proof.json
echo "GODOT PROOF: $(cat reports/sim_proof.json)"