# Docker Modernization Design — 2026-02-24

## Scope

Fixes to NuSyQ-Hub Docker infrastructure identified in audit:

1. Credential exposure (Postgres, Grafana, Redis)
2. Version pinning (`latest` tags on ollama, prometheus, grafana)
3. Missing SimulatedVerse Dockerfile
4. `docker-validate.yml` only covers dev compose
5. `Dockerfile.minimal` experimental artifact
6. Malformed path in `.dockerignore`

---

## Decisions

### Credentials: `.env` Pattern (Option A)
Docker secrets require Swarm mode and break `docker compose up` workflows — overkill
for this single-node project. Instead:

- Remove hardcoded fallback values from sensitive env vars
- Use `${VAR}` (no fallback) so compose fails fast if `.env` is missing
- Add `REDIS_PASSWORD` env var end-to-end (compose command + health check)
- Update `.env.example` and `deploy/.env.example` with all required vars

### Version Pinning
Three services using `latest` — pinned to stable known versions:

| Service | Before | After |
|---------|--------|-------|
| `ollama` | `ollama/ollama:latest` | `ollama/ollama:0.4.7` |
| `prometheus` | `prom/prometheus:latest` | `prom/prometheus:v2.53.0` |
| `grafana` | `grafana/grafana:latest` | `grafana/grafana:11.1.0` |

Note: verify and bump these periodically against hub.docker.com.

### SimulatedVerse Dockerfile
SimulatedVerse is a Node.js 20 / TypeScript / Express + Vite full-stack app.

**Multi-stage build (2 stages):**
- **Stage 1 — builder** (`node:20-alpine`): `npm ci`, `npm run build` (Vite frontend +
  esbuild server bundle → `dist/`)
- **Stage 2 — runtime** (`node:20-alpine`): copy `dist/`, prod deps only
  (`npm ci --omit=dev`), non-root `node` user, `PORT=5000`

Entry point: `CMD ["node", "dist/index.js"]`
Port: 5000 (matches NuSyQ-Hub's `SIMULATEDVERSE_PORT=5000`)

### docker-validate.yml
Add validation for all compose files alongside existing dev check:
- `docker-compose.yml` (production root)
- `deploy/docker-compose.full-stack.yml`
- Use `--env-file .env.example` so validation doesn't fail on missing required vars

### Archive Dockerfile.minimal
`Dockerfile.minimal` is incomplete (hardcoded 3 deps, fake health check, no
requirements.txt) and creates confusion about which Dockerfiles are production-ready.
Move to `archive/Dockerfile.minimal` with a header comment.

### Fix .dockerignore
Remove line 131: `CUserskeathDesktopLegacyNuSyQ-Hub/` — a malformed Windows path
with no effect but indicating a copy-paste error.

---

## Files Changed

| File | Change |
|------|--------|
| `docker-compose.yml` | Pin versions, add Redis password, remove Grafana default |
| `deploy/.env.example` | Add `REDIS_PASSWORD`, document all required vars |
| `.env.example` (root) | Add `REDIS_PASSWORD` |
| `.dockerignore` | Remove malformed line 131 |
| `archive/Dockerfile.minimal` | Move from root |
| `.github/workflows/docker-validate.yml` | Validate all compose files |
| `SimulatedVerse/Dockerfile` (new) | Node.js 20 Alpine multi-stage |
