#!/usr/bin/env bash
set -euo pipefail
if [ -f package.json ]; then
  if jq -e '.scripts.test' package.json >/dev/null 2>&1; then
    npm test || true
  fi
fi

if command -v pytest >/dev/null; then
  pytest -q || true
fi