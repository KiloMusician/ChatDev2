# Terminal Depths + Dev-Mentor — Python/FastAPI + CLI
# Multi-stage build: builder installs all deps; runtime is lean.
#
# Build:   docker build -t dev-mentor .
# Run:     docker run -p 7337:7337 --env-file .env dev-mentor
# Compose: docker compose up dev-mentor          (standard Lattice stack)
#          docker compose --profile lattice up    (+ Gordon/Serena/SkyClaw)
#          docker compose --profile rimworld up   (+ RimWorld VNC)

# ============================================================
# Stage 1: Builder — install all Python deps
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# OS-level build deps (git for VCS installs, curl for health probes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install uv — fast Python package manager used by entrypoint.sh
RUN pip install --no-cache-dir uv

# Copy dependency manifests
COPY requirements.txt pyproject.toml uv.lock* ./

# Install ALL runtime dependencies from requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy entire source tree (what isn't needed is in .dockerignore)
COPY app/       ./app/
COPY cli/       ./cli/
COPY agents/    ./agents/
COPY core/      ./core/
COPY config/    ./config/
COPY mcp/       ./mcp/
COPY scripts/   ./scripts/
COPY services/  ./services/
COPY docs/      ./docs/
COPY *.py       ./
# Root markdown files (TORCH.md, AGENTS.md, NEXT_ACTIONS.md, README.md, etc.)
# — agents and the game engine reference these for onboarding and backlog.
COPY *.md       ./

# ============================================================
# Stage 2: Runtime — lean, non-root image
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Minimal OS deps needed at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git bash && \
    rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd -m -u 1000 devmentor

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ \
                    /usr/local/lib/python3.11/site-packages/

# Copy uv binary from builder
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy source code from builder
COPY --from=builder /build /app

# Create writable runtime directories that are NOT in .dockerignore
# (state/, var/ are mounted as volumes in compose but must exist as fallback)
RUN mkdir -p \
    /app/state \
    /app/var \
    /app/sessions \
    /app/reports \
    /workspace/repos \
    /workspace/state \
    /workspace/sessions && \
    chown -R devmentor:devmentor /app /workspace

# Make entrypoint executable
RUN chmod +x /app/scripts/entrypoint.sh

# Drop to non-root
USER devmentor

# ── Ports ──────────────────────────────────────────────────────────────────
# 7337 = Docker/VSCode/local  (5000 = Replit only, set via PORT env var)
EXPOSE 7337

# ── Environment defaults ────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=7337 \
    TD_ENDPOINT="" \
    REPOS_DIR="/workspace/repos" \
    SKIP_HARVEST="0" \
    NUSYQ_HUB_PATH=/workspace/repos/NuSyQ-Hub \
    SIMVERSE_PATH=/workspace/repos/SimulatedVerse \
    ULTIMATE_REPO_PATH=/workspace/repos/NuSyQ-Ultimate

# ── Health check ────────────────────────────────────────────────────────────
HEALTHCHECK --interval=20s --timeout=8s --start-period=45s --retries=4 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# ── Entrypoint ──────────────────────────────────────────────────────────────
# Clones ecosystem repos (SKIP_HARVEST=1 to skip), then starts uvicorn.
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
