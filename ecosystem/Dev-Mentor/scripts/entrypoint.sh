#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# Terminal Depths / DevMentor — Docker Entrypoint
# ═══════════════════════════════════════════════════════════════════════════
# Pre-cascade step: clone / update all ecosystem repositories so the game,
# agents, and gateway have access to the full NuSyQ ecosystem.
#
# Repos are written to /workspace/repos/ (or /app/state/repos/ as fallback).
# Each repo is dependency-installed with uv if pyproject.toml is present.
# Environment variables are exported pointing to each repo path.
#
# Usage (Docker CMD override):
#   ENTRYPOINT ["scripts/entrypoint.sh"]
#
# Environment variables read:
#   GITHUB_TOKEN   — GitHub PAT with repo:read scope (required for private repos)
#   SKIP_HARVEST   — set to "1" to skip repo cloning and start immediately
#   REPOS_DIR      — override clone destination (default: /workspace/repos)
#   PORT           — server port (default: 7337 for Docker)
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Colour helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; DIM='\033[2m'; RESET='\033[0m'
info()    { echo -e "${CYAN}[HARVEST]${RESET} $*"; }
ok()      { echo -e "${GREEN}[✓]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[⚠]${RESET} $*"; }
fail()    { echo -e "${RED}[✗]${RESET} $*"; }
section() { echo -e "\n${CYAN}╔══ $* ══╗${RESET}"; }

# ── Configuration ───────────────────────────────────────────────────────────
REPOS_DIR="${REPOS_DIR:-/workspace/repos}"
# If /workspace doesn't exist (Replit / non-Docker), fall back to state/repos
if [ ! -d "/workspace" ]; then
    REPOS_DIR="${REPOS_DIR:-state/repos}"
fi
SKIP_HARVEST="${SKIP_HARVEST:-0}"
PORT="${PORT:-7337}"

# ── Ecosystem repository list ───────────────────────────────────────────────
# Format: "name|https_url"
REPOS=(
    "NuSyQ-Hub|https://github.com/KiloMusician/NuSyQ-Hub.git"
    "SimulatedVerse|https://github.com/KiloMusician/SimulatedVerse.git"
    "NuSyQ-Ultimate|https://github.com/KiloMusician/-NuSyQ_Ultimate_Repo.git"
    "Dev-Mentor|https://github.com/KiloMusician/Dev-Mentor.git"
)

# ── Repository Harvest ──────────────────────────────────────────────────────
if [ "${SKIP_HARVEST}" != "1" ]; then
    section "REPOSITORY HARVEST — Msg⛛{harvest.begin}"
    info "Target directory: ${REPOS_DIR}"
    mkdir -p "${REPOS_DIR}"

    for entry in "${REPOS[@]}"; do
        NAME="${entry%%|*}"
        URL="${entry##*|}"
        TARGET="${REPOS_DIR}/${NAME}"

        # Inject token into HTTPS URL if available
        AUTH_URL="${URL}"
        if [ -n "${GITHUB_TOKEN:-}" ] && [[ "${URL}" == https://github.com/* ]]; then
            AUTH_URL="${URL/https:\/\//https:\/\/x-token:${GITHUB_TOKEN}@}"
        fi

        echo ""
        info "[${NAME}]"

        if [ -d "${TARGET}/.git" ]; then
            # Already cloned — update
            if git -C "${TARGET}" pull --rebase --quiet 2>&1; then
                ok "Updated ${NAME}"
            else
                warn "Pull failed for ${NAME} — continuing with cached version"
            fi
        else
            # Fresh clone
            if git clone --depth 1 --quiet "${AUTH_URL}" "${TARGET}" 2>&1; then
                ok "Cloned ${NAME} → ${TARGET}"
            else
                fail "Clone failed for ${NAME} (private repo or auth error) — skipping"
                continue
            fi
        fi

        # Install dependencies with uv if pyproject.toml present
        if [ -f "${TARGET}/pyproject.toml" ] && command -v uv &>/dev/null; then
            info "  Installing deps for ${NAME}..."
            if (cd "${TARGET}" && uv sync --quiet 2>&1); then
                ok "  Deps installed for ${NAME}"
            else
                warn "  uv sync failed for ${NAME} — skipping deps"
            fi
        fi
    done

    section "HARVEST COMPLETE — Msg⛛{harvest.complete}"

    # ── Export environment variables ──────────────────────────────────────
    export NUSYQ_HUB_PATH="${REPOS_DIR}/NuSyQ-Hub"
    export SIMULATED_VERSE_PATH="${REPOS_DIR}/SimulatedVerse"
    export NUSYQ_ULTIMATE_PATH="${REPOS_DIR}/NuSyQ-Ultimate"
    export DEV_MENTOR_PATH="${REPOS_DIR}/Dev-Mentor"

    ok "NUSYQ_HUB_PATH=${NUSYQ_HUB_PATH}"
    ok "SIMULATED_VERSE_PATH=${SIMULATED_VERSE_PATH}"
    ok "NUSYQ_ULTIMATE_PATH=${NUSYQ_ULTIMATE_PATH}"

else
    warn "SKIP_HARVEST=1 — skipping repository harvest"
fi

# ── Start the application ───────────────────────────────────────────────────
section "STARTING TERMINAL DEPTHS — port ${PORT}"

exec python -m uvicorn app.backend.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --log-level info
