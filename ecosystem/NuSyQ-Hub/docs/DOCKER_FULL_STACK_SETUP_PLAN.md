# Docker Full-Stack Setup Plan - NuSyQ-Hub

**Created:** 2026-02-03  
**Status:** Docker Desktop running on Windows, WSL integration needs configuration  
**Goal:** Bring up complete NuSyQ AI orchestration stack

---

## 🔍 Current State Assessment

### ✅ CONFIRMED WORKING:
- **Docker Desktop:** Running on Windows host
- **Docker Daemon:** Responding to `docker ps -a`, `docker volume ls`, `docker network ls`
- **Existing Container:** `docker/lsp` (zealous_margulis) running for ~1 hour
- **Default Networks:** bridge, host, none (created)
- **Volumes:** Only `docker-lsp` exists

### ❌ NOT WORKING:
- **WSL Integration:** `/usr/bin/docker` in WSL points to `/mnt/wsl/docker-desktop/cli-tools/usr/bin/docker` but can't reach daemon
- **docker.sock:** Not accessible from WSL (causes I/O errors)
- **NuSyQ Stack:** No containers, images, or volumes exist for NuSyQ-Hub yet

### 📋 MISSING (To Be Created):
According to `deploy/docker-compose.full-stack.yml` and `deploy/docker-compose.dev.yml`:

**Images:**
- `nusyq-hub:production` (full-stack)
- `nusyq-hub:dev` (development)
- `nusyq-ollama-mock:dev` (dev stack only)
- `simulatedverse:latest` (full-stack)
- Plus: `ollama/ollama:latest`, `postgres:15-alpine`, `redis:7-alpine` (pulled from Docker Hub)

**Containers (Full Stack):**
- `nusyq-hub-main` (ports 8000, 8080)
- `nusyq-ollama` (port 11434)
- `nusyq-simulatedverse` (ports 5000, 3000)
- `nusyq-quest-tracker` (port 8501)
- `nusyq-redis` (port 6379)
- `nusyq-postgres` (port 5432)

**Containers (Dev Stack):**
- `nusyq-hub-dev` (ports 5000, 5678)
- `nusyq-postgres` (port 5432)
- `nusyq-redis` (port 6379)
- `ollama-mock` (port 8080)
- `nusyq-db-migrate` (one-shot, manual profile)

**Volumes:**
- `nusyq-ollama-models` (Ollama models ~37GB)
- `nusyq-simulatedverse-data` (SimulatedVerse state)
- `nusyq-temple-knowledge` (Temple of Knowledge data)
- `nusyq-chatdev-projects` (ChatDev WareHouse)
- `nusyq-quest-logs` (Quest system logs)
- `nusyq-ai-cache` (AI model cache)
- `nusyq-redis-data` (Redis persistence)
- `nusyq-postgres-data` (PostgreSQL data)
- Plus dev stack: `nusyq_pgdata`, `nusyq_redisdata`, `nusyq_logs`

**Networks:**
- `nusyq-ai-network` (172.28.0.0/16 subnet, full-stack)
- `nusyq-net` (dev stack)

**Kubernetes:** NOT REQUIRED for default workflow (optional manifests in `deploy/k8s/`)

---

## SimulatedVerse Source Path

- `deploy/docker-compose.full-stack.yml` now builds `simulatedverse:latest` from `${SIMULATEDVERSE_PATH:-../../../SimulatedVerse/SimulatedVerse}`. When you execute this file from within WSL (e.g., `/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub`), that default resolves to `/mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse`. Export `SIMULATEDVERSE_PATH` ahead of time if your copy of SimulatedVerse lives on a different drive or relative location.
- The same canonical location is mirrored in `config/workspace_mapping.yaml` and `config/orchestration_defaults.json`; keeping those files up to date helps the automated diagnostics (`scripts/start_nusyq.py error_report`, `src/diagnostics/multi_repo_error_explorer.py`, etc.) locate the sister repo without manual chasing.
- Run `ls "$SIMULATEDVERSE_PATH"` (WSL) or `dir %SIMULATEDVERSE_PATH%` (PowerShell) as part of the pre-flight check so Docker Compose fails fast with a missing-context message instead of halfway through the build.

## 📐 Expected Docker Desktop View

### Images Tab Should Show:
```
REPOSITORY              TAG           SIZE        CREATED
nusyq-hub              production    ~2.5GB      (after build)
nusyq-hub              dev          ~2.8GB      (after build)
simulatedverse         latest       ~1.2GB      (after build)
nusyq-ollama-mock      dev          ~150MB      (after build)
ollama/ollama          latest       ~5.2GB      (pulled)
postgres               15-alpine    ~230MB      (pulled)
redis                  7-alpine     ~28MB       (pulled)
```

### Containers Tab Should Show (Full Stack):
```
NAME                    IMAGE                     STATUS      PORTS
nusyq-hub-main          nusyq-hub:production     healthy     8000, 8080
nusyq-ollama            ollama/ollama:latest     healthy     11434
nusyq-simulatedverse    simulatedverse:latest    running     5000, 3000
nusyq-quest-tracker     nusyq-hub:production     running     8501
nusyq-redis             redis:7-alpine           running     6379
nusyq-postgres          postgres:15-alpine       healthy     5432
```

### Volumes Tab Should Show:
```
NAME                          SIZE
nusyq-ollama-models           ~37GB (after Ollama pulls models)
nusyq-simulatedverse-data     ~500MB
nusyq-temple-knowledge        ~200MB
nusyq-chatdev-projects        ~1GB
nusyq-quest-logs              ~50MB
nusyq-ai-cache                ~500MB
nusyq-redis-data              ~10MB
nusyq-postgres-data           ~50MB
```

### Settings → Resources → WSL Integration Should Show:
```
☑ Enable integration with my default WSL distro
☑ Ubuntu-22.04 (or your WSL distro name)
```

### Settings → Resources → Advanced Should Have:
```
CPUs: 4 or more
Memory: 8 GB or more
Swap: 2 GB
Disk image size: 100 GB+ (to accommodate Ollama models)
```

---

## 🛠️ Step-by-Step Setup Plan

### Phase 1: Fix WSL Integration (Windows Host)

**1.1 Verify Docker Desktop Settings**
```powershell
# On Windows PowerShell
# Open Docker Desktop → Settings → General
# Confirm:
# ☑ Use the WSL 2 based engine
# ☑ Start Docker Desktop when you log in

# Open Settings → Resources → WSL Integration
# Enable your WSL distro (Ubuntu-22.04, etc.)
# Click "Apply & Restart"
```

**1.2 Increase Resource Limits**
```powershell
# Settings → Resources → Advanced
# Set:
CPUs: 4-8 (depending on your system)
Memory: 8-16 GB
Swap: 2 GB
Disk image size: 120 GB (for Ollama models)

# Click "Apply & Restart"
```

**1.3 Configure File Sharing**
```powershell
# Settings → Resources → File sharing
# Add if not present:
C:\Users\keath\Desktop\Legacy\NuSyQ-Hub

# Click "Apply & Restart"
```

**1.4 Verify Docker Desktop Status**
```powershell
# Wait for whale icon in system tray to say "Docker Desktop is running"
# Run these commands on Windows PowerShell:

docker version
# Should show Client and Server versions

docker ps
# Should show running containers

docker info
# Should show system-wide information
```

### Phase 2: Verify WSL Connection (Inside WSL)

**2.1 Wait for Docker Socket**
```bash
# Inside WSL terminal
cd /mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub

# Activate Python environment
source .venv/bin/activate

# Wait for Docker to be ready
python scripts/wait_for_docker.py --timeout 60

# Expected output:
# ✅ Docker daemon is ready!
```

**2.2 Test Docker Commands**
```bash
# Should work without errors now:
docker version
docker ps
docker info

# If still fails with I/O error, restart WSL:
# On Windows PowerShell:
wsl --shutdown
# Then reopen WSL terminal
```

### Phase 3: Build & Deploy (Choose ONE Stack)

#### Option A: Development Stack (Recommended for testing)

**3.1 Build Development Images**
```bash
# Inside WSL, in NuSyQ-Hub directory
cd /mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub

# Build development stack (takes ~10-15 minutes first time)
docker compose -f deploy/docker-compose.dev.yml build

# Expected output:
# ✅ Building nusyq-hub... done
# ✅ Building ollama-mock... done
```

**3.2 Start Development Stack**
```bash
# Start with full profile (all services)
docker compose -f deploy/docker-compose.dev.yml --profile full up -d

# Check status
docker compose -f deploy/docker-compose.dev.yml ps

# Expected output:
# NAME              STATUS        PORTS
# nusyq-hub-dev     healthy       0.0.0.0:5000->5000/tcp
# nusyq-postgres    running       0.0.0.0:5432->5432/tcp
# nusyq-redis       running       0.0.0.0:6379->6379/tcp
# ollama-mock       running       0.0.0.0:8080->8080/tcp
```

**3.3 Monitor Health Checks**
```bash
# Watch logs
docker compose -f deploy/docker-compose.dev.yml logs -f nusyq-hub

# Check health status
python scripts/docker_health_monitor.py

# Test endpoints
curl http://localhost:${SIMULATEDVERSE_PORT}/health
# Expected: {"status": "healthy", ...}
```

#### Option B: Full Production Stack

**3.1 Verify SimulatedVerse Path**
```bash
# Check if SimulatedVerse exists
ls -la /mnt/c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse/

# If missing, full-stack won't work (simulatedverse service will fail)
```

**3.2 Build Full Stack**
```powershell
# On Windows PowerShell (better for large builds)
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub

# Build all services (takes 20-30 minutes first time)
docker compose -f deploy\docker-compose.full-stack.yml build

# Expected images created:
# - nusyq-hub:production
# - simulatedverse:latest
```

**3.3 Start Full Stack**
```powershell
# Start all services
docker compose -f deploy\docker-compose.full-stack.yml up -d

# Check status
docker compose -f deploy\docker-compose.full-stack.yml ps

# Expected:
# nusyq-hub-main        healthy    8000, 8080
# nusyq-ollama          healthy    11434
# nusyq-simulatedverse  running    ${SIMULATEDVERSE_PORT}, 3000
# nusyq-quest-tracker   running    8501
# nusyq-redis           running    6379
# nusyq-postgres        healthy    5432
```

**3.4 Wait for Ollama Models (First Run Only)**
```bash
# Ollama automatically pulls models on first start:
# - qwen2.5-coder:7b (~10 GB)
# - starcoder2:15b (~15 GB)
# - gemma2:9b (~12 GB)

# Monitor progress
docker logs -f nusyq-ollama

# This takes 30-60 minutes depending on internet speed
# Volumes will grow to ~37GB
```

### Phase 4: Validate Stack Health

**4.1 Check All Services**
```bash
# Activate Python environment
cd /mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub
source .venv/bin/activate

# Run lifecycle manager check
python -m src.system.lifecycle_manager status

# Expected output:
# ✅ Docker: Running
# ✅ Ollama: Running (port 11434 or 8080)
# ✅ Quest System: Running
# ... etc
```

**4.2 Run Health Monitor**
```bash
# Single check
python scripts/docker_health_monitor.py

# Continuous monitoring
python scripts/docker_health_monitor.py --watch --interval 30

# Export metrics
python scripts/docker_health_monitor.py --export
# Saves to: data/docker_health_metrics.json
```

**4.3 Test Endpoints**
```bash
# Dev stack:
curl http://localhost:${SIMULATEDVERSE_PORT}/health          # NuSyQ-Hub
curl http://localhost:8080/health          # Ollama Mock
curl http://localhost:5432                 # PostgreSQL (should refuse HTTP)
curl http://localhost:6379                 # Redis (should refuse HTTP)

# Full stack:
curl http://localhost:8000/health          # NuSyQ-Hub API
curl http://localhost:8080                 # Orchestration UI
curl http://localhost:11434/api/tags       # Ollama (list models)
curl http://localhost:${SIMULATEDVERSE_PORT}                 # SimulatedVerse
curl http://localhost:3000                 # React UI
curl http://localhost:8501                 # Quest Tracker (Streamlit)
```

### Phase 5: Run System Diagnostics

**5.1 Start Lifecycle Manager**
```bash
# This triggers full orchestration startup
python -m src.system.lifecycle_manager start

# Expected:
# ✅ Docker check passed
# ✅ Ollama check passed
# ✅ Quest system initialized
# ✅ Terminals activated
# ✅ Agents ready
```

**5.2 Generate Error Report**
```bash
# Comprehensive diagnostics scan
python scripts/start_nusyq.py error_report --timeout 300

# This creates:
# - state/reports/current_state.md
# - docs/Reports/diagnostics/unified_error_report_*.md
# - Logs full diagnostic scan (ruff, mypy, pylint across 3 repos)
```

**5.3 Review Diagnostics**
```bash
# Check current error baseline
cat state/reports/current_state.md

# Expected metrics (from last scan):
# Total Diagnostics: 3,479
# ├─ Errors:   59
# ├─ Warnings: 6
# └─ Infos:    3,414 (mostly style hints)
```

---

## 🎯 Success Criteria

### ✅ Stack is Healthy When:
1. **Docker Desktop:** All containers show "healthy" or "running" status
2. **Lifecycle Manager:** `python -m src.system.lifecycle_manager status` shows all green
3. **Health Monitor:** `python scripts/docker_health_monitor.py` reports 100% healthy
4. **Endpoints:** All `curl` tests return valid responses
5. **Volumes:** Docker Desktop shows expected volumes with reasonable sizes
6. **Diagnostics:** Error count stays at 59 or improves (no regressions)

### ❌ Common Failure Signs:
- Containers stuck in "starting" state → Check logs with `docker logs <container>`
- Health checks failing → Verify ports not in use: `netstat -an | findstr "5000 8000 11434"`
- Out of disk space → Ollama models need ~40GB, check Docker disk size
- WSL I/O errors → Restart Docker Desktop and WSL (`wsl --shutdown`)

---

## 🚨 Troubleshooting Guide

### Problem: WSL still can't reach Docker

**Solution:**
```powershell
# On Windows:
1. Open Docker Desktop
2. Settings → General → "Use the WSL 2 based engine" (checked)
3. Settings → Resources → WSL Integration
4. Enable your distro
5. Click "Apply & Restart"
6. Wait 2 minutes for restart
7. In WSL: docker ps (should work now)
```

### Problem: Containers fail to build

**Solution:**
```bash
# Clear Docker build cache
docker builder prune -a

# Rebuild without cache
docker compose -f deploy/docker-compose.dev.yml build --no-cache

# Check build logs
docker compose -f deploy/docker-compose.dev.yml build --progress=plain
```

### Problem: Health checks never pass

**Solution:**
```bash
# Inspect specific container
docker inspect nusyq-hub-dev --format='{{json .State.Health}}' | jq

# Check if service is actually listening
docker exec nusyq-hub-dev netstat -tlnp | grep 5000

# View last 100 log lines
docker logs --tail=100 nusyq-hub-dev
```

### Problem: "Port already in use"

**Solution:**
```powershell
# On Windows, find what's using the port
netstat -ano | findstr ":5000"
# Kill process: taskkill /PID <PID> /F

# Or change ports in docker-compose.yml:
ports:
  - "5001:5000"  # Map to different host port
```

### Problem: Ollama models won't download

**Solution:**
```bash
# Check internet connectivity
docker exec nusyq-ollama ping -c 2 ollama.ai

# Manually pull models
docker exec nusyq-ollama ollama pull qwen2.5-coder:7b

# Check disk space
docker exec nusyq-ollama df -h /root/.ollama
```

---

## 📊 Monitoring & Maintenance

### Daily Operations

```bash
# Check stack status
docker compose -f deploy/docker-compose.dev.yml ps

# View logs
docker compose -f deploy/docker-compose.dev.yml logs -f --tail=50

# Restart unhealthy services
python scripts/docker_health_monitor.py --watch

# Update diagnostics
python scripts/start_nusyq.py error_report
```

### Cleanup Commands

```bash
# Stop all services
docker compose -f deploy/docker-compose.dev.yml down

# Stop + remove volumes (WARNING: deletes data)
docker compose -f deploy/docker-compose.dev.yml down -v

# Remove unused images
docker image prune -a

# Full cleanup (removes EVERYTHING)
docker system prune -a --volumes
```

### Backup Important Data

```bash
# Backup quest logs
docker cp nusyq-hub-dev:/workspace/quests ./backups/quests_$(date +%Y%m%d)

# Backup PostgreSQL
docker exec nusyq-postgres pg_dump -U nusyq nusyq > backup_$(date +%Y%m%d).sql

# Backup Ollama models (large!)
docker run --rm -v nusyq-ollama-models:/source -v C:/Backups:/dest alpine tar -czf /dest/ollama_models.tar.gz -C /source .
```

---

## 🔗 Related Documentation

- [DOCKER_MODERNIZATION_GUIDE.md](./DOCKER_MODERNIZATION_GUIDE.md) - Compose v2 migration details
- [AGENTS.md](../AGENTS.md) - Agent navigation protocol & system integration
- [ROSETTA_STONE.md](.vscode/prime_anchor/docs/ROSETTA_STONE.md) - Overall system architecture
- [docker_health_monitor.py](../scripts/docker_health_monitor.py) - Automated health monitoring
- [lifecycle_manager.py](../src/system/lifecycle_manager.py) - Service orchestration

---

## 📝 Notes

- **Dev vs Full Stack:** Use `docker-compose.dev.yml` for development (lighter, faster). Use `docker-compose.full-stack.yml` for production-like testing.
- **Ollama Models:** First run downloads ~37GB of models. Be patient. Subsequent starts are instant.
- **SimulatedVerse:** Full stack requires `../../SimulatedVerse/SimulatedVerse/` to exist. Dev stack doesn't need it.
- **Kubernetes:** Optional. The deploy/k8s/ manifests are for advanced deployment. Compose is recommended.
- **Resource Needs:** Full stack needs 16GB RAM minimum. Dev stack works with 8GB.

---

**Last Updated:** 2026-02-03  
**Validated With:** Docker Desktop 4.59.0, Docker Compose v5.0.2, WSL 2
