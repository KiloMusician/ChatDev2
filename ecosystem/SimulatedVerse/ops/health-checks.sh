#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . "${ROOT_DIR}/.env"
  set +a
fi

# LSP + route health (fast checks you can run anytime)
echo "🔍 Running health checks..."

PORT="${SIMULATEDVERSE_PORT:-${PORT:-5002}}"
CHATDEV_PORT="${CHATDEV_PORT:-4466}"

# Quick typecheck + route smoke in CI or pre-commit
echo "📝 TypeScript check..."
npm run -s check || { echo "❌ TS errors"; exit 1; }

echo "🌐 Server health check..."
curl -sf "http://127.0.0.1:${PORT}/api/health" || echo "⚠️ /api/health not responding on :${PORT}"

echo "🎮 Game API check..."
curl -sf "http://127.0.0.1:${PORT}/api/game/demo-user" | grep -q "tick\|energy" || echo "⚠️ API shape mismatch on :${PORT}"

echo "🤖 ChatDev adapter check..."
curl -sf "http://127.0.0.1:${CHATDEV_PORT}/chatdev/agents" >/dev/null || echo "⚠️ ChatDev adapter not responding on :${CHATDEV_PORT}"

echo "✅ Health checks complete!"
