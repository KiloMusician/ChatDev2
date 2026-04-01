#!/usr/bin/env bash
# Load environment variables for NuSyQ-Hub.
# Usage: source scripts/setup_env.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -f "$REPO_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$REPO_ROOT/.env"
  set +a
else
  echo "Warning: $REPO_ROOT/.env not found. Create it from .env.example."
fi

export CHATDEV_PATH="${CHATDEV_PATH:-}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export OLLAMA_API_KEY="${OLLAMA_API_KEY:-}"
export SECRET_KEY="${SECRET_KEY:-}"
export DATABASE_URL="${DATABASE_URL:-}"
