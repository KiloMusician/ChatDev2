#!/usr/bin/env bash
set -euo pipefail
echo "==> Linters (local only, no tokens)"
[ -f package.json ] && npx -y eslint . || true
[ -f package.json ] && npx -y prettier -c . || true
command -v ruff >/dev/null && ruff check . || true
command -v black >/dev/null && black --check . || true
command -v mypy >/dev/null && mypy || true
command -v shellcheck >/dev/null && shellcheck -x ops/**/*.sh || true