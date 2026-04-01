#!/usr/bin/env bash
set -euo pipefail

echo "▶ Preflight: verifying toolchain & repo shape"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing $1"; exit 1; }; }

for bin in node npm python3 pip git jq curl; do need "$bin"; done

# Detect package managers / lockfiles
[ -f package.json ] && echo "✓ Node project detected"
[ -f pnpm-lock.yaml ] && PM="pnpm" || PM="npm"

# Python venv (for ML bits)
if [ -d ml ] || [ -f requirements.txt ] || [ -f pyproject.toml ]; then
  echo "✓ Python/ML layer detected"
fi

# Core folders expected (best-effort)
expect_dirs=( "src" "server" "client" "agents" "modules" )
for d in "${expect_dirs[@]}"; do
  [ -d "$d" ] && echo "✓ $d present" || echo "⚠ $d missing (will continue)"
done

# Check for CognitoWeave specific components
[ -d "modules/culture_ship" ] && echo "✓ Culture Ship detected"
[ -d "agents" ] && echo "✓ Agent system detected"
[ -f "server/index.ts" ] && echo "✓ Server index detected"

echo "▶ Preflight passed"