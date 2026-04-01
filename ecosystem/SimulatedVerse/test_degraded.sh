#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:5002}"

echo "[1/3] /healthz"
curl -fsS "${BASE_URL}/healthz" | rg '"ok":true'

echo "[2/3] /readyz"
curl -fsS "${BASE_URL}/readyz" | rg '"ok":true'

echo "[3/3] /"
curl -fsS "${BASE_URL}/" | rg '<!DOCTYPE html>|<html'

echo "degraded-mode checks passed"
