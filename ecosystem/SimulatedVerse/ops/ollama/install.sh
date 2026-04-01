#!/usr/bin/env bash
set -euo pipefail

# 1) Detect existing
if command -v ollama >/dev/null 2>&1; then
    echo "[ollama] already installed: $(ollama --version 2>/dev/null || true)"
    exit 0
fi

# 2) Try official install (Linux x86-64). Replit usually allows curl.
echo "[ollama] installing..."
curl -fsSL https://ollama.com/install.sh | sh

# 3) Verify
if ! command -v ollama >/dev/null 2>&1; then
    echo "[ollama] install failed. Keep scripts, the cascade will fall back to cloud LLMs if configured."
    exit 1
fi
echo "[ollama] OK: $(ollama --version)"