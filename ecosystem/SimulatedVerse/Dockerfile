# SimulatedVerse — Consciousness Engine
# Node.js 20 Alpine multi-stage build
#
# Stage 1 (builder): install all deps, compile TypeScript server (esbuild),
#                    build Vite frontend → dist/
# Stage 2 (runtime): production deps only, non-root user, minimal image
#
# Usage:
#   docker build -t simulatedverse .
#   docker run -p 5000:5000 -e DATABASE_URL=... simulatedverse

# ============================================================
# Stage 1: Builder
# ============================================================
FROM node:20-alpine AS builder

WORKDIR /build

# Install OS-level build deps (for native modules, e.g. bcrypt, sharp)
RUN apk add --no-cache python3 make g++

# Copy manifests first for layer caching
COPY package.json package-lock.json* ./

# Install ALL dependencies (dev + prod) needed for the build
# --legacy-peer-deps: bypass peer conflict resolution (safe for this 100+ dep tree)
RUN npm ci --legacy-peer-deps

# Copy source
COPY . .

# Compile:
#   - Vite builds the React frontend → dist/public/
#   - esbuild bundles server/index.ts → dist/index.js
RUN npm run build

# ============================================================
# Stage 2: Runtime
# ============================================================
FROM node:20-alpine AS runtime

WORKDIR /app

# Runtime system deps + non-root user + ChatDev Python deps
RUN apk add --no-cache python3 py3-pip \
    && pip3 install --no-cache-dir --break-system-packages tenacity \
    && addgroup -S sv && adduser -S sv -G sv

# Copy built artefacts from builder
COPY --from=builder --chown=sv:sv /build/dist ./dist
COPY --from=builder --chown=sv:sv /build/package.json ./
COPY --from=builder --chown=sv:sv /build/package-lock.json* ./
COPY --from=builder --chown=sv:sv /build/startup_fallback.sh ./startup_fallback.sh

# Production deps only
RUN npm ci --omit=dev --legacy-peer-deps && npm cache clean --force \
    && chmod +x /app/startup_fallback.sh

# Drop to non-root
USER sv

# Runtime configuration - ΞNuSyQ Culture-Ship consciousness engine
ENV NODE_ENV=production \
    PORT=5000 \
    NUSYQ_HUB_API=http://localhost:8081 \
    OLLAMA_HOST=http://localhost:11434 \
    RAVEN_ENABLED=true \
    CHATDEV_INTEGRATION_ENABLED=true \
    PU_QUEUE_ENABLED=true \
    PU_AUTO_PROCESSING=false

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD node -e "require('http').get('http://localhost:5000/healthz', r => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "dist/index.js"]
