# NuSyQ TODO Report

**Generated:** 2025-10-05
**Scope:** Core codebase (excludes ChatDev WareHouse examples)
**Total TODOs:** 5 actionable items

---

## High Priority (Security/Production)

### 1. CORS Origin Restriction
**File:** `mcp_server/main.py:179`
**Code:**
```python
# TODO: Restrict to specific origins in production
```

**Issue:** CORS currently allows all origins (`allow_origins=["*"]`)
**Impact:** Security vulnerability in production deployments
**Effort:** 30 minutes
**Fix:**
```python
# Production setting
allow_origins=[
    "http://localhost:3000",
    "https://your-domain.com"
]
```

---

### 2. Path Traversal Protection
**File:** `mcp_server/main.py:741`
**Code:**
```python
# TODO: Add path traversal protection for production
```

**Context:** File read operations in `_file_read()` method
**Impact:** Potential security risk - users could read arbitrary files
**Effort:** 1 hour
**Fix:** Add path validation:
```python
def _validate_path(self, path: Path) -> bool:
    """Ensure path is within allowed directories"""
    allowed_dirs = [Path.cwd(), Path.home() / "NuSyQ"]
    try:
        resolved = path.resolve()
        return any(resolved.is_relative_to(d) for d in allowed_dirs)
    except:
        return False
```

---

### 3. Write Restrictions
**File:** `mcp_server/main.py:783`
**Code:**
```python
# TODO: Implement write restrictions for production
```

**Context:** File write operations in `_file_write()` method
**Impact:** Users could write to system files
**Effort:** 1 hour
**Fix:** Similar path validation as #2, plus file extension whitelist

---

### 4. Process Isolation
**File:** `mcp_server/main.py:918`
**Code:**
```python
# TODO: Implement proper isolation for production
```

**Context:** Subprocess execution in `_run_code()` method
**Impact:** Arbitrary code execution risk
**Effort:** 3-4 hours
**Fix:** Use Docker containers or sandboxing:
```python
# Run in isolated container
subprocess.run([
    'docker', 'run', '--rm', '--network=none',
    '--memory=512m', '--cpus=1',
    'python:3.12-slim', 'python', '-c', code
], ...)
```

---

## Medium Priority (Features/Enhancements)

### 5. Jupyter Integration
**File:** `mcp_server/src/jupyter.py:55`
**Code:**
```python
# TODO: Replace with jupyter_client for true notebook integration
```

**Context:** Current implementation uses subprocess, not proper notebook kernel
**Impact:** Limited Jupyter functionality
**Effort:** 4-6 hours
**Fix:** Use `jupyter_client` library for kernel management

---

## Low Priority (Code Quality)

These are mentioned in [CODE_QUALITY_REPORT.md](CODE_QUALITY_REPORT.md) but not critical:

### 6. ChatDev Timeout Configuration
**File:** Referenced in reports, not in actual code
**Status:** Already configurable via command-line args
**Action:** Document existing functionality

### 7. Ollama Connection Pooling
**File:** Referenced in reports, not in actual code
**Status:** Single session currently sufficient
**Action:** Implement if performance issues arise

### 8. Response Caching
**File:** Referenced in reports
**Status:** Not needed for current use cases
**Action:** Consider for high-traffic scenarios

### 9. Schema Validation
**File:** Referenced in reports
**Status:** YAML parsing provides basic validation
**Action:** Add Pydantic models for stricter validation

### 10. Rate Limiting
**File:** Referenced in reports
**Status:** Not needed for local development
**Action:** Add FastAPI rate limiting middleware for production

---

## ChatDev TODOs (Upstream)

These are in ChatDev framework code and should be addressed upstream:

1. **camel/generators.py:193** - Return role names with generator
2. **chatdev/phase.py:138** - Handle max_tokens_exceeded errors
3. **camel/agents/chat_agent.py:269** - Strict `<INFO>` check
4. **camel/agents/task_agent.py:155** - Include roles information
5. **camel/agents/critic_agent.py:96** - Add editing options support
6. **camel/agents/tool_agents/hugging_face_tool_agent.py:44** - Support other tool agents

**Action:** These should be reported to ChatDev repository, not fixed locally

---

## Implementation Plan

### Phase 1: Security Fixes (High Priority) - Week 1
**Time:** 6-8 hours

1. **Day 1-2:** Path validation and CORS restrictions (#1, #2, #3)
   - Add `_validate_path()` method
   - Update CORS settings with environment variables
   - Add file extension whitelist

2. **Day 3-4:** Process isolation (#4)
   - Research sandboxing options (Docker, firejail, etc.)
   - Implement container-based execution
   - Add resource limits

3. **Day 5:** Testing and documentation
   - Security testing
   - Update deployment docs
   - Add security configuration guide

### Phase 2: Feature Enhancements (Medium Priority) - Week 2
**Time:** 4-6 hours

1. **Jupyter Integration** (#5)
   - Install `jupyter_client`
   - Implement kernel management
   - Add notebook execution API
   - Test with sample notebooks

### Phase 3: Code Quality (Low Priority) - Ongoing
**Time:** 2-4 hours per item (as needed)

- Schema validation with Pydantic
- Rate limiting middleware
- Connection pooling (if performance issues)
- Response caching (if needed)

---

## Priority Matrix

| TODO | Priority | Effort | Impact | Status |
|------|----------|--------|--------|--------|
| #1 CORS | High | 30min | Security | 🔴 Open |
| #2 Path Traversal | High | 1h | Security | 🔴 Open |
| #3 Write Restrictions | High | 1h | Security | 🔴 Open |
| #4 Process Isolation | High | 4h | Security | 🔴 Open |
| #5 Jupyter Integration | Medium | 6h | Feature | 🟡 Open |
| #6-10 Code Quality | Low | 2-4h each | Quality | 🟢 Optional |

---

## Quick Start - Fix Security Issues

### 1. Add Path Validation
Create `mcp_server/src/security_validators.py`:
```python
from pathlib import Path
from typing import List

ALLOWED_DIRS = [
    Path.cwd() / "ChatDev",
    Path.cwd() / "Jupyter",
    Path.home() / "NuSyQ"
]

ALLOWED_EXTENSIONS = [
    '.py', '.js', '.ts', '.md', '.txt', '.json',
    '.yaml', '.yml', '.csv', '.html', '.css'
]

def validate_file_path(path: Path) -> tuple[bool, str]:
    """Validate file path is safe"""
    try:
        resolved = path.resolve()

        # Check directory
        if not any(resolved.is_relative_to(d) for d in ALLOWED_DIRS):
            return False, "Path outside allowed directories"

        # Check extension
        if resolved.suffix not in ALLOWED_EXTENSIONS:
            return False, f"File type {resolved.suffix} not allowed"

        return True, "Valid"
    except Exception as e:
        return False, str(e)
```

### 2. Use in MCP Server
Update `mcp_server/main.py`:
```python
from mcp_server.src.security_validators import validate_file_path

async def _file_read(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Read file with security validation"""
    file_path = Path(args.get("path", ""))

    valid, message = validate_file_path(file_path)
    if not valid:
        return {"success": False, "error": f"Security: {message}"}

    # ... rest of implementation
```

### 3. Configure CORS
Update `.env` or `config/environment.json`:
```json
{
  "security": {
    "allowed_origins": [
      "http://localhost:3000",
      "http://localhost:8000"
    ],
    "allowed_file_extensions": [".py", ".js", ".md"],
    "max_file_size_mb": 10
  }
}
```

---

## Testing Security Fixes

### Test Path Traversal Protection
```python
# Should FAIL
response = requests.post("http://localhost:3000/tools/execute", json={
    "tool": "file_read",
    "arguments": {"path": "/etc/passwd"}  # Try to read system file
})
assert response.json()["success"] == False

# Should SUCCEED
response = requests.post("http://localhost:3000/tools/execute", json={
    "tool": "file_read",
    "arguments": {"path": "ChatDev/NuSyQ_Root_README.md"}  # Allowed directory
})
assert response.json()["success"] == True
```

### Test Write Restrictions
```python
# Should FAIL
response = requests.post("http://localhost:3000/tools/execute", json={
    "tool": "file_write",
    "arguments": {
        "path": "/tmp/../../etc/malicious",  # Path traversal attempt
        "content": "bad"
    }
})
assert response.json()["success"] == False
```

---

## Tracking Progress

Create GitHub issues for each high-priority TODO:
```bash
# Install GitHub CLI if needed
gh auth login

# Create issues
gh issue create --title "Security: Add CORS origin restrictions" --body "See TODO_REPORT.md #1" --label security,high-priority
gh issue create --title "Security: Add path traversal protection" --body "See TODO_REPORT.md #2" --label security,high-priority
gh issue create --title "Security: Add write restrictions" --body "See TODO_REPORT.md #3" --label security,high-priority
gh issue create --title "Security: Implement process isolation" --body "See TODO_REPORT.md #4" --label security,high-priority
gh issue create --title "Feature: Improve Jupyter integration" --body "See TODO_REPORT.md #5" --label enhancement,medium-priority
```

---

## Notes

### Why These TODOs Exist
1. **Development Focus:** Initial development prioritized functionality over security
2. **Local Use:** System designed for trusted local development environment
3. **Production Gap:** TODOs mark the transition points for production deployment

### When to Address
- **Before production deployment:** All High priority items
- **After first production release:** Medium priority items
- **As needed:** Low priority items based on usage patterns

### Related Documents
- [CODE_QUALITY_REPORT.md](CODE_QUALITY_REPORT.md) - Full code analysis
- [Guide_Contributing_AllUsers.md](Guide_Contributing_AllUsers.md) - How to implement fixes
- [docs/QUICK_START.md](docs/QUICK_START.md) - Setup guide

---

**Last Updated:** 2025-10-05
**Next Review:** After implementing Phase 1 security fixes
