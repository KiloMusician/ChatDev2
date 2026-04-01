# syntax=docker/dockerfile:1
# Multi-stage Dockerfile for NuSyQ-Hub with security best practices
# Stage 1: Builder
FROM python:3.11-slim AS builder

# Install build dependencies (sorted alphabetically) and Python packages
WORKDIR /build
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    apt-get update && apt-get install -y --no-install-recommends \
    g++ gcc make \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --user -r requirements.txt

# Install optional alembic for migrations
ARG INSTALL_ALEMBIC=yes
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "${INSTALL_ALEMBIC}" = "yes" ]; then pip install --user alembic; fi

# Stage 2: Runtime
FROM python:3.11-slim

# Install runtime dependencies and create non-root user in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r nusyq && useradd -r -g nusyq -u 1000 nusyq

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/nusyq/.local

# Copy application code
COPY --chown=nusyq:nusyq . .

# Set Python path
ENV PATH=/home/nusyq/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Switch to non-root user
USER nusyq

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose port (src/api/main.py binds to 8000)
EXPOSE 8000

# Default command — run the FastAPI API server (not the CLI orchestrator)
# To run orchestration mode: override CMD with ["python", "-m", "src.main", "--mode=orchestration"]
CMD ["python", "-m", "src.api.main"]
