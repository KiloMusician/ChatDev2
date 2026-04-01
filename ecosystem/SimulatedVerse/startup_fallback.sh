#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export TMPDIR="${TMPDIR:-/tmp}"
export PORT="${PORT:-5002}"
export SIMULATEDVERSE_PORT="${SIMULATEDVERSE_PORT:-$PORT}"

exec node --env-file=.env --import tsx/esm server/startup_fallback.ts
