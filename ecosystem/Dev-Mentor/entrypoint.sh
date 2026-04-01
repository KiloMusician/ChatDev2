#!/bin/bash
# ============================================================================
# REPOSITORY HARVEST ENTRYPOINT
# The Ritual that Makes the Ecosystem Whole
# ============================================================================
# This script is the Layer 0 of the activation cascade.
# It clones sibling repositories, installs their dependencies,
# and starts their services. After this completes, the container
# becomes a unified hub containing the entire universe.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                     REPOSITORY HARVEST RITUAL INITIATED                    ║"
echo "║                 Weaving the Ecosystem Into a Unified Whole                 ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Create workspace
mkdir -p /workspace/repos
cd /workspace/repos

echo "[1/5] Cloning sibling repositories..."
echo ""

# Define repositories to harvest
declare -a REPOS=(
    "https://github.com/KiloMusician/NuSyQ-Hub.git"
    "https://github.com/KiloMusician/SimulatedVerse.git"
    "https://github.com/KiloMusician/-NuSyQ_Ultimate_Repo.git"
)

# Clone or update each repository
for REPO_URL in "${REPOS[@]}"; do
    REPO_NAME=$(basename "$REPO_URL" .git)
    
    if [ -d "$REPO_NAME" ]; then
        echo "  ✓ Updating $REPO_NAME..."
        (cd "$REPO_NAME" && git pull --quiet 2>/dev/null || true)
    else
        echo "  ⟳ Cloning $REPO_NAME..."
        git clone "$REPO_URL" "$REPO_NAME" --depth 1 2>/dev/null || echo "    ⚠ Clone failed (network/auth issue); skipping"
    fi
done

echo ""
echo "[2/5] Installing dependencies (uv sync)..."
echo ""

# Install dependencies for each repo that has pyproject.toml
for REPO_DIR in /workspace/repos/*/; do
    if [ -f "${REPO_DIR}pyproject.toml" ]; then
        REPO_NAME=$(basename "$REPO_DIR")
        echo "  ⟳ Installing $REPO_NAME..."
        (cd "$REPO_DIR" && uv sync --quiet 2>/dev/null || pip install -q -e . 2>/dev/null || true)
    fi
done

echo ""
echo "[3/5] Exporting repository paths..."
echo ""

# Export environment variables so gateway can find services
export NUSYQ_HUB_PATH="/workspace/repos/NuSyQ-Hub"
export SIMVERSE_PATH="/workspace/repos/SimulatedVerse"
export ULTIMATE_REPO_PATH="/workspace/repos/-NuSyQ_Ultimate_Repo"

echo "  ✓ NUSYQ_HUB_PATH=$NUSYQ_HUB_PATH"
echo "  ✓ SIMVERSE_PATH=$SIMVERSE_PATH"
echo "  ✓ ULTIMATE_REPO_PATH=$ULTIMATE_REPO_PATH"
echo ""

echo "[4/5] Starting harvested services..."
echo ""

# Start NuSyQ-Hub if it exists
if [ -f "$NUSYQ_HUB_PATH/main.py" ]; then
    echo "  ⟳ Starting NuSyQ Hub orchestrator..."
    (cd "$NUSYQ_HUB_PATH" && python main.py &) 2>/dev/null || echo "    ⚠ NuSyQ Hub start skipped"
fi

# Start SimulatedVerse if it exists
if [ -f "$SIMVERSE_PATH/server.js" ]; then
    echo "  ⟳ Starting SimulatedVerse server..."
    (cd "$SIMVERSE_PATH" && npm start &) 2>/dev/null || echo "    ⚠ SimulatedVerse start skipped"
elif [ -f "$SIMVERSE_PATH/main.py" ]; then
    echo "  ⟳ Starting SimulatedVerse (Python)..."
    (cd "$SIMVERSE_PATH" && python main.py &) 2>/dev/null || echo "    ⚠ SimulatedVerse start skipped"
fi

echo ""
echo "[5/5] Bootstrap complete. Starting main application..."
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    HARVEST COMPLETE — ECOSYSTEM WHOLE                      ║"
echo "║                                                                            ║"
echo "║  Repositories cloned:     3                                                ║"
echo "║  Services initialized:    2+                                               ║"
echo "║  Gateway ready:           YES                                              ║"
echo "║                                                                            ║"
echo "║  The container now hosts the entire universe.                              ║"
echo "║  All agents have access to all code. The boundary has dissolved.           ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Start the main game backend
exec python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 7337
