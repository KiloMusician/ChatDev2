# Docker Modernization Guide - NuSyQ-Hub

## Overview

This document describes the **modernized Docker setup** for NuSyQ-Hub, implementing:
- Modern Compose Specification (no deprecated `version` field)
- Enhanced health checks and dependency management
- Docker Compose V2 commands
- Automated health monitoring
- WSL/Windows/Linux compatibility improvements

**Last Updated:** 2026-02-03  
**Docker Compose Version:** v5.0.2  
**Docker Desktop Version:** 4.59.0

---

## What Changed? 🔄

### 1. Compose File Modernization

**Before (Deprecated):**
```yaml
version: "3.9"  # ❌ No longer needed

services:
  app:
    environment:
      - KEY=value  # ❌ Old syntax
    volumes:
      - ./app:/app:cached  # ❌ Inconsistent format
```

**After (Modern):**
```yaml
# ✅ No version field (uses Compose Specification)

services:
  app:
    environment:
      KEY: "value"  # ✅ Modern syntax
    volumes:
      - type: bind
        source: ./app
        target: /app
        consistency: cached  # ✅ Explicit configuration
    init: true  # ✅ Better signal handling
    profiles:
      - dev
      - full
```

### 2. Enhanced Health Checks

**Before:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
```

**After:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "python -c 'import requests; requests.get(\"http://localhost:5000/health\", timeout=5)' || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Benefits:**
- More accurate (uses Python instead of curl)
- Better error handling
- Proper timeout configuration
- Defined start period for slow-starting services

### 3. Dependency Management

**Before:**
```yaml
depends_on:
  - ollama
```

**After:**
```yaml
depends_on:
  ollama:
    condition: service_healthy
    restart: true
  simulatedverse:
    condition: service_started
    restart: true
```

**Benefits:**
- Services wait for dependencies to be healthy
- Automatic restart on dependency failure
- Clearer dependency relationships

### 4. Resource Limits

**New:**
```yaml
deploy:
  resources:
    limits:
      cpus: "4.0"
      memory: 4G
    reservations:
      cpus: "1.0"
      memory: 1G
```

**Benefits:**
- Prevents runaway resource consumption
- Guarantees minimum resource allocation
- Better multi-service orchestration

---

## New Commands (Docker Compose V2) 🚀

### Starting Services

**❌ Old (deprecated):**
```bash
docker-compose up
docker-compose -f deploy/docker-compose.full-stack.yml up --build
```

**✅ New (modern):**
```bash
# Basic start
docker compose up

# Full stack with build
docker compose -f deploy/docker-compose.full-stack.yml up --build

# With profiles
docker compose --profile dev up
docker compose --profile production up

# Background mode
docker compose up -d
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f nusyq-hub

# Last 100 lines
docker compose logs --tail=100 nusyq-hub
```

### Stopping Services

```bash
# Stop (keep containers)
docker compose stop

# Down (remove containers)
docker compose down

# Down with volumes (WARNING: deletes data!)
docker compose down -v
```

### Health Checks

```bash
# Check service status
docker compose ps

# Check specific service
docker compose ps nusyq-hub

# View health status
docker inspect nusyq-hub-main --format='{{.State.Health.Status}}'
```

---

## Automated Health Monitoring 🏥

New script: `scripts/docker_health_monitor.py`

### Features

- Real-time container health monitoring
- Automatic restart of unhealthy containers
- Health metrics export to JSON
- Continuous watch mode

### Usage

```bash
# Single check
python scripts/docker_health_monitor.py

# Continuous monitoring (30s interval)
python scripts/docker_health_monitor.py --watch

# Custom interval
python scripts/docker_health_monitor.py --watch --interval 60

# Disable auto-restart
python scripts/docker_health_monitor.py --watch --no-restart

# Export metrics
python scripts/docker_health_monitor.py --export
```

### Example Output

```
🐳 Docker Container Health Status
================================================================================
📊 Summary:
  Total:     3
  ✅ Healthy:   2
  ⚠️  Unhealthy: 1
  🛑 Stopped:   0
  🔄 Restarted: 1

📦 Container Details:
Name                           Status       Health       Uptime          Restarts  
--------------------------------------------------------------------------------
✅ nusyq-hub-main              running      healthy      2h 15m          0  
⚠️  nusyq-ollama               running      unhealthy    1h 45m          1  
✅ nusyq-redis                 running      N/A          2h 10m          0  
```

### Metrics Export

Metrics are saved to: `data/docker_health_metrics.json`

```json
[
  {
    "status": "success",
    "timestamp": "2026-02-03T14:30:00",
    "total_containers": 3,
    "healthy": 2,
    "unhealthy": 1,
    "stopped": 0,
    "restarted": 1,
    "containers": [...]
  }
]
```

---

## Lifecycle Manager Integration 🔄

Enhanced `src/system/lifecycle_manager.py` with:

### Better Docker Detection

```python
def _check_docker_compose(self) -> bool:
    """Check if Docker Compose V2 is available."""

def _get_docker_context(self) -> str:
    """Get current Docker context (desktop-linux, etc)."""
```

### WSL Detection

```python
def _is_wsl(self) -> bool:
    """Detect when running inside WSL."""
    return bool(
        os.environ.get("WSL_DISTRO_NAME") or
        Path("/run/WSL").exists()
    )
```

### Usage

```bash
# Start all services
python -m src.system.lifecycle_manager start

# Check status
python -m src.system.lifecycle_manager status

# Stop all services
python -m src.system.lifecycle_manager stop

# Full restart
python -m src.system.lifecycle_manager restart
```

---

## Platform-Specific Notes 📝

### Windows

**Docker Desktop must be running:**
1. Look for Docker whale icon in system tray
2. Click and verify "Docker Desktop is running"
3. WSL integration enabled in Settings → Resources → WSL Integration

**Start Docker Desktop:**
```powershell
# PowerShell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### WSL (Windows Subsystem for Linux)

**Docker runs on Windows host, accessed from WSL:**

```bash
# Check Docker context
docker context show  # Should show "desktop-linux"

# Verify daemon
docker ps

# If fails, ensure Docker Desktop is running on Windows
```

**Wait for Docker:**
```bash
python scripts/wait_for_docker.py --timeout 60
```

### Linux (Native)

**Docker Engine:**
```bash
# Start daemon
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

**Rootless Docker:**
```bash
# Start user daemon
dockerd-rootless.sh

# Check
docker context use rootless
docker ps
```

### macOS

**Docker Desktop:**
```bash
# Start
open -a Docker

# Check
docker ps
```

---

## Troubleshooting 🔧

### Issue: "Cannot connect to Docker daemon"

**Windows/WSL:**
1. Open Docker Desktop on Windows
2. Wait for whale icon to say "Docker Desktop is running"
3. In WSL: `python scripts/wait_for_docker.py --timeout 60`
4. Verify: `docker ps`

**Linux:**
```bash
sudo systemctl start docker
# OR
dockerd-rootless.sh
```

### Issue: "docker compose: command not found"

**Solution:**
Upgrade to Docker Desktop 3.4+ or install Docker Compose V2:
```bash
# Linux
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Issue: Containers fail health checks

**1. Check logs:**
```bash
docker compose logs -f <service-name>
```

**2. Inspect health:**
```bash
docker inspect <container-name> --format='{{json .State.Health}}'
```

**3. Manual health check:**
```bash
# For Python services
docker exec <container-name> python -c "import requests; requests.get('http://localhost:5000/health')"
```

**4. Use health monitor:**
```bash
python scripts/docker_health_monitor.py --watch
```

### Issue: Slow starts / timeouts

**Increase start_period in compose file:**
```yaml
healthcheck:
  start_period: 120s  # Increase from 40s
```

**Or disable health check temporarily:**
```yaml
healthcheck:
  disable: true
```

---

## Migration Checklist ✅

If upgrading from old setup:

- [ ] Update Docker Desktop to 4.0+ (for Compose V2)
- [ ] Replace `docker-compose` commands with `docker compose`
- [ ] Remove `version:` field from custom compose files
- [ ] Update environment variables to modern syntax (`KEY: "value"` not `- KEY=value`)
- [ ] Add health checks to custom services
- [ ] Test with `docker compose config` to validate syntax
- [ ] Update CI/CD pipelines to use `docker compose`
- [ ] Add resource limits to prevent runaway containers
- [ ] Enable BuildKit: `export DOCKER_BUILDKIT=1`
- [ ] Configure profiles for different environments (dev, prod, test)

---

## Related Files 📁

### Compose Files
- `deploy/docker-compose.yml` - Basic development
- `deploy/docker-compose.full-stack.yml` - Full AI stack with Ollama, SimulatedVerse
- `deploy/docker-compose.dev.yml` - Development with hot reload
- `deploy/docker-compose.agents.yml` - Agent services only
- `dev/observability/docker-compose.observability.yml` - Observability (OTEL, Jaeger)
- `dev/observability/docker-compose.postgres.yml` - PostgreSQL core
- `dev/observability/docker-compose.timescale.yml` - TimescaleDB

### Scripts
- `scripts/docker_health_monitor.py` - Health monitoring service
- `scripts/wait_for_docker.py` - Wait for Docker daemon
- `src/system/lifecycle_manager.py` - System lifecycle orchestration

### Documentation
- `docs/SYSTEM_USAGE_GUIDE.md` - Overall system usage
- `AI_AGENT_QUICK_REFERENCE.md` - Quick command reference
- This file: `docs/DOCKER_MODERNIZATION_GUIDE.md`

---

## Best Practices 🌟

### 1. Use Profiles
Organize services by environment:
```yaml
services:
  dev-tools:
    profiles: [dev]

  prod-cache:
    profiles: [production]

  observability:
    profiles: [dev, production, observability]
```

Start with: `docker compose --profile dev up`

### 2. Health Checks for All Services
Every long-running service should have a health check:
```yaml
healthcheck:
  test: ["CMD-SHELL", "your-health-check-command"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 3. BuildKit Enabled
Add to `.env` or shell profile:
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

**Benefits:**
- Faster builds
- Better layer caching
- Parallel build stages
- Build secrets support

### 4. Named Volumes
Use explicit volume names:
```yaml
volumes:
  ollama-data:
    name: nusyq-ollama-models
    driver: local
```

**Benefits:**
- Persistent across `docker compose down`
- Easier to backup
- Clear ownership

### 5. Init Process
Add to services that spawn child processes:
```yaml
services:
  app:
    init: true
```

**Benefits:**
- Proper signal handling (SIGTERM, SIGINT)
- Reaps zombie processes
- Clean shutdown

---

## Performance Tips ⚡

### 1. Volume Bind Consistency
```yaml
volumes:
  - type: bind
    source: ./app
    target: /app
    consistency: cached  # Fast! (host → container lag OK)
    # delegated  # Faster! (container → host lag OK)
    # consistent # Slowest (strict sync)
```

**Use `cached` for code mounts (read-heavy).**

### 2. Resource Limits
Prevent one service from consuming everything:
```yaml
deploy:
  resources:
    limits:
      cpus: "2.0"
      memory: 2G
```

### 3. Build Cache
Enable BuildKit cache:
```yaml
build:
  cache_from:
    - myapp:latest
    - myapp:dev
```

### 4. Parallel Starts
Compose starts services in parallel by default (respects `depends_on`).

To force sequential: use `depends_on` chains.

---

## Security Considerations 🔒

### 1. Secrets
Never commit secrets to compose files. Use:

**Environment files:**
```bash
# .env (add to .gitignore)
POSTGRES_PASSWORD=secure_password_here
```

**Docker secrets (Swarm):**
```yaml
secrets:
  db_password:
    file: ./secrets/db_password.txt

services:
  db:
    secrets:
      - db_password
```

### 2. Network Isolation
```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

### 3. Read-Only Containers
```yaml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
```

---

## Future Enhancements 🔮

Planned improvements:

1. **Docker Swarm support** for multi-node deployment
2. **Kubernetes manifests** generated from compose files
3. **Auto-scaling** based on container metrics
4. **Service mesh integration** (Istio, Linkerd)
5. **Advanced monitoring** (Prometheus, Grafana dashboards)
6. **Automated backups** of volumes
7. **Blue-green deployments**
8. **Canary releases**

---

## Support & Feedback 💬

**Issues:** Log to `src/Rosetta_Quest_System/quest_log.jsonl`  
**Questions:** Reference this guide or `SYSTEM_USAGE_GUIDE.md`  
**Updates:** Check lifecycle manager and health monitor logs

---

**Last Update:** 2026-02-03  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
