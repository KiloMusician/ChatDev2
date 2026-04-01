#!/usr/bin/env bash
set -euo pipefail
ts="$(date -u +%Y%m%d-%H%M%S)"
out=".snapshot/$ts"
mkdir -p "$out"
cp -a NEXUS/maps "$out/maps"
cp -a NEXUS/datasets "$out/datasets"
echo "{\"created\":\"$ts\"}" > "$out/meta.json"
echo "Snapshot at $out"