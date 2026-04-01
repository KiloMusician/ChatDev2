# WSL Integration Guide

## Current Status

**WSL Available:** ✅ Yes (WSL2)  
**Observed Agent Runtime (2026-02-26):** `Ubuntu-22.04` via WSL Bash  
**Tooling Mode:** Mixed Windows + WSL toolchains  
**Build Scripts:** ✅ Implemented (PowerShell + WSL-compatible paths)

### Runtime Context Snapshot (2026-02-26)

- Codex/agent command execution runs in WSL Bash (`/bin/bash`) even when driven from VS Code UI.
- Windows-side `git.exe` and `gh.exe` may be authenticated while WSL `git` is not.
- WSL push/fetch can fail unless credential helper bridge is configured for WSL git.
- `.venv` / interpreter wiring can drift between Windows-style and Linux-style paths.
- SimulatedVerse HTTP from WSL may require Windows gateway IP (`ip route` default gateway), not `localhost`.
- SimulatedVerse startup behavior differs by shell:
  - `cmd.exe /c "npm run dev:minimal"` works and exposes health at `http://127.0.0.1:5001/api/health`.
  - WSL `npm run dev:minimal` can fail with `tsx` IPC pipe `ENOTSUP` on `/mnt/c/...` paths.
- In this workspace, `git describe --dirty --always --long --abbrev=40` can hang from WSL on `/mnt/c` mounts.
  - This impacted pytest smoke runs via plugin calls.
  - Health smoke pipeline now disables `pytest-benchmark` (`-p no:benchmark`) to avoid false timeouts.

### Integration Trace Focus Areas

1. **Git/Auth Boundary**
   - Windows Git Credential Manager (`git.exe`) may work while `/usr/bin/git` in WSL cannot authenticate.
   - Verify with `git ls-remote` in the same shell that will run push/pull.

2. **Hook Execution Boundary**
   - Check active hooks path (`git config core.hooksPath`) and line endings in active hook scripts.
   - CRLF shebangs in active hooks can break under WSL (`python3\r` errors).

3. **Python Runtime Boundary**
   - Confirm interpreter path used by CLI/tests (`which python` + VS Code interpreter setting).
   - Prefer one canonical environment path for both test and orchestration commands.

4. **WSL Networking Boundary**
   - Services started in Windows shell may not be reachable from WSL via `localhost`.
   - Probe with both:
     - `curl http://127.0.0.1:<port>/...`
     - `curl http://$(ip route | awk '/^default/ {print $3; exit}'):<port>/...`

5. **SimulatedVerse Port Boundary**
   - Legacy docs/configs mention both `5000` and `5002`.
   - Current health check probes both to avoid false negatives.

## Existing Infrastructure

### 1. Build Scripts (PowerShell)

#### `scripts/wsl_build.ps1`
- Builds Docker images inside WSL2
- Sanitizes build context
- Avoids Windows permission issues
- Tags with git SHA

Usage:
```powershell
./scripts/wsl_build.ps1 -Tag v1.0.0
```

#### `scripts/build_docker.ps1`
- Multi-architecture builds
- Registry push support
- Platform selection
- Docker buildx integration

Usage:
```powershell
./scripts/build_docker.ps1 -Registry ghcr.io/user -ImageName nusyq-hub -Tag latest -Push
```

### 2. Docker Utilities

- `scripts/check_docker_k8s.ps1` - Verify Docker/K8s status
- `scripts/cleanup_docker.ps1` - Clean up containers/images

## Potential Use Cases

### 1. **Cross-Platform Testing** ✅
- Run Linux-based tests in WSL
- Verify cross-platform compatibility
- Test shell scripts in real bash environment

### 2. **Docker Integration** ✅ (Implemented)
- Build images without Windows permission issues
- Access Linux Docker daemon
- Multi-arch builds

### 3. **Performance** 🚧 (Needs Implementation)
- Run CPU-intensive tasks in WSL (potentially faster)
- Parallel test execution
- Build optimization

### 4. **Development Tools** 🚧 (Needs Implementation)
- Run Linux-only linters
- Use native Unix tools
- Shell script development/testing

### 5. **CI/CD Simulation** 🚧 (Needs Implementation)
- Test GitHub Actions locally
- Simulate Linux CI environment
- Pre-flight checks before push

## Implementation Ideas

### Quick Wins

#### 1. WSL Test Runner
```powershell
# scripts/wsl_test.ps1
wsl -e bash -c "cd /mnt/c/path/to/project && pytest tests/"
```

#### 2. WSL Linting
```powershell
# Run shellcheck on all shell scripts
wsl -e bash -c "find . -name '*.sh' -exec shellcheck {} +"
```

#### 3. Parallel Processing
```python
# Use WSL for CPU-bound tasks
subprocess.run(["wsl", "-e", "python3", "heavy_processing.py"])
```

### Modernization Needed

#### 1. Missing Dockerfiles
- No Dockerfile.prod found
- No Dockerfile.dev found
- Build scripts reference non-existent files

**Action:** Create Dockerfiles or update scripts

#### 2. Context Sanitization
- `scripts/create_sanitized_context.py` referenced but may be missing
- Need to verify existence and functionality

**Action:** Check/create sanitization script

#### 3. WSL Distribution
- Agent sessions currently run on Ubuntu-22.04, but some legacy scripts/docs still assume docker-desktop paths
- Distribution assumptions should be validated per-shell before automation runs

**Action:** Standardize scripts on distro-agnostic `/mnt/c/...` paths and verify with `wsl --list --verbose`

## Activation Steps

### 1. Verify WSL Status ✅
```powershell
wsl --status
wsl --list --verbose
```

### 2. Install Full Distribution (Optional)
```powershell
wsl --install -d Ubuntu-22.04
```

### 3. Create Missing Docker Infrastructure
- [ ] Create Dockerfile.prod
- [ ] Create Dockerfile.dev
- [ ] Create/verify sanitized context script
- [ ] Test build pipeline

### 4. Implement WSL Utilities
- [ ] WSL test runner
- [ ] Cross-platform CI simulator
- [ ] Performance comparison tool

## Current Limitations

1. **No Dockerfiles** - Build scripts can't run without Dockerfile.prod
2. **Distro Assumption Drift** - docs/scripts may disagree on default WSL distro
3. **No Integration Tests** - WSL capabilities not tested
4. **Missing Documentation** - Usage patterns not documented

## Recommendations

### Immediate Actions
1. ✅ Document current WSL status
2. Create Dockerfile.prod and Dockerfile.dev
3. Verify/create sanitization script
4. Test build pipeline end-to-end

### Future Enhancements
1. WSL-based CI simulation
2. Cross-platform test suite
3. Performance benchmarking (Windows vs WSL)
4. Shell script linting pipeline
5. Parallel test execution

## WSL Command Reference

```powershell
# List distributions
wsl --list --verbose

# Run command in WSL
wsl -e bash -c "command"

# Access Windows files from WSL
cd /mnt/c/Users/...

# Access WSL files from Windows
\\wsl$\Ubuntu\home\user\...

# Set default distribution
wsl --set-default Ubuntu-22.04

# Shutdown WSL
wsl --shutdown
```

## Conclusion

**Status:** Partially Implemented
**Readiness:** 60%
**Primary Gap:** Missing Dockerfiles
**Recommendation:** Create Docker infrastructure to unlock WSL build capabilities

WSL integration is scaffolded but needs Docker artifacts to be fully functional.
