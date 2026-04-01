# MCP Server Modularization - Safe Refactor Checklist
<!-- cSpell:ignore pylint flake8 pytest yaml -->

**Status**: P2 (Medium Priority)
**Risk Level**: Medium (monolithic function refactoring)
**Effort**: 1-2 days (includes testing)
**Goal**: Decompose [main.py](main.py) into modular service imports while maintaining backward compatibility

---

## Overview

The MCP server in [main.py](main.py) (8000+ lines) is monolithic with implicit coupling between:
- Ollama query handling
- File operations (read/write)
- Configuration management
- Security validation
- Error handling

The modular architecture already exists in [mcp_server/src/](src/) with tested services:
- [src/models.py](src/models.py) - Request/response validation
- [src/config.py](src/config.py) - Configuration management
- [src/security.py](src/security.py) - Security validation
- [src/ollama.py](src/ollama.py) - Async Ollama queries
- [src/file_ops.py](src/file_ops.py) - Safe file operations

**This checklist guides safe migration** without breaking the server in production.

---

## Phase 1: Preparation & Validation (Risk Mitigation)

### Step 1.1: Baseline Testing
- [ ] Run full test suite: `pytest mcp_server/tests/ -v`
- [ ] Document current test results in `BASELINE_TESTS.log`
- [ ] Check that all 8000+ lines load without import errors
  ```bash
  python -c "from mcp_server.main import app; print('✓ Server imports successfully')"
  ```
- [ ] Record current performance baseline (import time, memory usage)

### Step 1.2: Service Module Validation
- [ ] Verify all services in [src/](src/) import without errors
  ```bash
  python -c "from mcp_server.src import OllamaService, FileOperationsService, ConfigManager, SecurityValidator"
  ```
- [ ] Run service-specific tests: `pytest mcp_server/tests/test_services.py -v`
- [ ] Verify service contracts match main.py function signatures
  - `OllamaService.query()` → signature should match `handle_ollama_query()`
  - `FileOperationsService.read_file()` → match `handle_file_read()`
  - etc.

### Step 1.3: Create Git Branch & Checkpoint
- [ ] Create branch: `git checkout -b p2/mcp-modularization`
- [ ] Create initial commit: `git commit -m "Baseline: monolithic main.py before refactoring"`
- [ ] Document current behavior in `REFACTOR_NOTES.md`

---

## Phase 2: Safe Migration (One Service at a Time)

### Step 2.1: Migrate Ollama Query Handler
**Files Modified**: [main.py](main.py)
**Scope**: Replace internal ollama query function with service import

**Before** (in main.py, ~200 lines):
```python
def handle_ollama_query(payload):
    """Inline Ollama logic..."""
    # ... 200+ lines of code
```

**After** (in main.py, ~10 lines):
```python
from mcp_server.src.ollama import OllamaService

ollama_service = OllamaService()

def handle_ollama_query(payload):
    """Delegate to service."""
    return ollama_service.query(payload)
```

**Checklist**:
- [ ] Copy current `handle_ollama_query()` logic to a backup file
- [ ] Replace with service call in [main.py](main.py)
- [ ] Test: `pytest mcp_server/tests/test_services.py::test_ollama_service -v`
- [ ] Functional test: `curl http://localhost:8765/ollama/query -X POST ...`
- [ ] Commit: `git commit -m "Refactor: Ollama handler uses service layer"`

### Step 2.2: Migrate File Operations Handler
**Files Modified**: [main.py](main.py)
**Scope**: Replace read/write functions with FileOperationsService

**Before**:
```python
def handle_file_read(filepath):
    """Inline file logic..."""
    # ... 100+ lines
```

**After**:
```python
from mcp_server.src.file_ops import FileOperationsService

file_service = FileOperationsService()

def handle_file_read(filepath):
    """Delegate to service."""
    return file_service.read_file(filepath)
```

**Checklist**:
- [ ] Backup original `handle_file_read()` and `handle_file_write()`
- [ ] Replace with service calls
- [ ] Test: `pytest mcp_server/tests/test_services.py -k file_ops -v`
- [ ] Functional tests:
  - [ ] `curl http://localhost:8765/file/read?path=...`
  - [ ] `curl http://localhost:8765/file/write` with content
- [ ] Commit: `git commit -m "Refactor: File operations use service layer"`

### Step 2.3: Migrate Configuration Management
**Files Modified**: [main.py](main.py)
**Scope**: Replace inline config with ConfigManager service

**Before**:
```python
# Scattered throughout main.py
config = yaml.safe_load(open('config.yaml'))
port = config['service']['port']
```

**After**:
```python
from mcp_server.src.config import ConfigManager

config_manager = ConfigManager()
port = config_manager.get('service.port')
```

**Checklist**:
- [ ] Document all current config access points (grep "config\[")
- [ ] Replace with ConfigManager API calls
- [ ] Test configuration loading: `pytest mcp_server/tests/ -k config -v`
- [ ] Verify environment variable overrides still work
- [ ] Commit: `git commit -m "Refactor: Configuration uses ConfigManager service"`

### Step 2.4: Migrate Security Validation
**Files Modified**: [main.py](main.py)
**Scope**: Replace inline validation with SecurityValidator service

**Before**:
```python
# Scattered security checks
if '../' in filepath:
    raise ValueError("Path traversal detected")
```

**After**:
```python
from mcp_server.src.security import SecurityValidator

security = SecurityValidator(config_manager)
security.validate_path(filepath)  # Raises on invalid path
```

**Checklist**:
- [ ] Document all current security checks
- [ ] Replace with SecurityValidator calls
- [ ] Test security rules: `pytest mcp_server/tests/test_services.py::test_security -v`
- [ ] Verify path traversal protection works
- [ ] Verify file size limits enforced
- [ ] Commit: `git commit -m "Refactor: Security uses validator service"`

---

## Phase 3: Integration Testing

### Step 3.1: End-to-End Server Tests
- [ ] Start server: `python mcp_server/main.py`
- [ ] Run integration test suite: `bash scripts/test_mcp_integration.sh`
- [ ] Document any behavioral differences from original
- [ ] Verify no performance regression (import time, latency)

### Step 3.2: Stress Testing
- [ ] Send 100+ concurrent requests to each endpoint
- [ ] Monitor memory usage (should remain stable)
- [ ] Check error handling (should still return proper HTTP codes)
- [ ] Log results to `STRESS_TEST_RESULTS.md`

### Step 3.3: Regression Testing
- [ ] Run existing test suite: `pytest mcp_server/tests/ -v --tb=short`
- [ ] Verify 100% of tests pass
- [ ] Document any skipped tests with reason

---

## Phase 4: Code Quality & Cleanup

### Step 4.1: Lint & Format Checks
- [ ] Run pylint on refactored main.py: `pylint mcp_server/main.py`
- [ ] Run flake8: `flake8 mcp_server/main.py --max-line-length=120`
- [ ] Fix any style issues
- [ ] Commit: `git commit -m "Chore: Lint and style fixes for refactored main.py"`

### Step 4.2: Documentation Updates
- [ ] Update [README.md](../README.md) section "MCP Server Architecture" with new structure
- [ ] Document service initialization in [main.py](main.py) docstring
- [ ] Create [SERVICE_MIGRATION.md](SERVICE_MIGRATION.md) with before/after examples
- [ ] Add inline comments explaining why each service is used

### Step 4.3: Dependency Cleanup
- [ ] Remove any now-redundant imports from [main.py](main.py)
- [ ] Verify no circular imports: `python -m py_compile mcp_server/main.py`
- [ ] Check dependency order (imports should be clean)

---

## Phase 5: Deployment & Rollback Plan

### Step 5.1: Pre-Merge Checklist
- [ ] All tests passing: `pytest mcp_server/ -v`
- [ ] No lint errors: `pylint mcp_server/main.py --fail-under=8.0`
- [ ] Performance baseline verified: latency ±5% acceptable
- [ ] Code review completed
- [ ] Documentation updated

### Step 5.2: Merge Strategy
- [ ] Create pull request with all commits from this checklist
- [ ] Request code review from maintainer
- [ ] Obtain approval before merge
- [ ] Merge to main branch: `git merge p2/mcp-modularization`
- [ ] Tag release: `git tag v2.1.0-refactored`

### Step 5.3: Rollback Plan
If issues emerge in production:
- [ ] Immediate: Revert commit `git revert <merge-commit-hash>`
- [ ] Long-term: Debug issue in separate branch, fix, re-merge
- [ ] Document root cause and prevention in [LESSONS_LEARNED.md](LESSONS_LEARNED.md)

---

## Risk Assessment & Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Breaking change in API | High | Thorough end-to-end testing before merge |
| Performance regression | Medium | Baseline + stress testing; rollback if >10% slower |
| Service import failure | Medium | Pre-validation of all services (Step 1.2) |
| Security validation bypass | High | Test all security rules explicitly (Step 2.4) |
| Configuration mismatch | Medium | Test both YAML and env var overrides |

---

## Success Criteria

✅ **All criteria must be met before declaring P2 complete**:

1. All monolithic functions in [main.py](main.py) delegate to service layer
2. 100% of existing tests pass (no regressions)
3. No lint errors (pylint score ≥ 8.0)
4. No performance regression (import time and latency within ±5%)
5. Security validation tests all pass
6. Documentation updated with new architecture
7. Code review approved
8. Merged to main branch with PR link documented

---

## Files Reference

- [main.py](main.py) - Monolithic server (target of refactoring)
- [src/ollama.py](src/ollama.py) - Ollama service (ready to use)
- [src/file_ops.py](src/file_ops.py) - File operations service (ready to use)
- [src/config.py](src/config.py) - Configuration service (ready to use)
- [src/security.py](src/security.py) - Security validator (ready to use)
- [tests/test_services.py](tests/test_services.py) - Service tests (reference for validation)
- [config.yaml](config.yaml) - Configuration file (reference for ConfigManager)

---

## Timeline Estimate

| Phase | Estimated Time | Notes |
|-------|-----------------|-------|
| Phase 1: Preparation | 2 hours | Testing + validation |
| Phase 2: Migration | 8-10 hours | 4 services × 2-2.5 hours each |
| Phase 3: Integration | 4 hours | End-to-end + stress testing |
| Phase 4: Quality | 2 hours | Lint, docs, cleanup |
| Phase 5: Deployment | 1-2 hours | Review, merge, tag |
| **Total** | **17-20 hours** | ~2-3 days of focused work |

---

## Next Steps (When Approved)

1. Create branch: `git checkout -b p2/mcp-modularization`
2. Start Phase 1 (Preparation)
3. Work through phases sequentially (don't skip Phase 3 testing!)
4. Document progress in PR description
5. Request review when Phase 4 complete
6. Merge after approval

**Owner**: DevOps / Architecture team
**Last Updated**: 2026-01-08
**Status**: Ready for implementation (P2 - Medium priority)
