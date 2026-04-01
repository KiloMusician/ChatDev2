#!/usr/bin/env bash
set -euo pipefail
cmd="${1:-help}"; shift || true
case "$cmd" in
  gates)         bash scripts/gates.sh "$@";;
  ingest)        bash scripts/ingest_tasks.sh "$@";;
  council)       bash scripts/council_turn.sh "$@";;
  audit)         bash scripts/structural_audit.sh "$@";;
  theater)       bash scripts/theater_guard.sh "$@";;
  godot)         bash scripts/godot_smoke.sh "$@";;
  spine)         bash scripts/spine_restore.sh "$@";;
  proxy)         bash scripts/proxy_sidecar.sh "$@";;
  receipts)      bash scripts/receipts_index.sh "$@";;
  daemon)        bash scripts/daemon_loop.sh "$@";;
  help|*)        echo "Usage: ./run.sh [gates|ingest|council|audit|theater|godot|spine|proxy|receipts|daemon]";;
esac