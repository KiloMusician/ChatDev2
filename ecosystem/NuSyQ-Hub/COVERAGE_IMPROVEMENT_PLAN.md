# Coverage Improvement Plan - Target: 40%+

**Current Coverage**: 31% (77,848 lines, 54,049 covered)  
**Target**: 40%+ (need ~160 additional covered lines)

## Priority 1: Critical Low-Hanging Fruit (Impact: HIGH)

| Module | Current | Lines | Priority | Impact |
|--------|---------|-------|----------|--------|
| `src/utils/directory_context_generator.py` | 5% | 183 | 🔴 CRITICAL | Core utility for context generation |
| `src/utils/quick_github_audit.py` | 7% | 75 | 🔴 CRITICAL | GitHub integration audit |
| `src/utils/resource_cleanup.py` | 11% | 148 | 🟠 HIGH | Resource management |
| `src/utils/github_instructions_enhancer.py` | 11% | 272 | 🟠 HIGH | Documentation system |
| `src/utils/github_integration_auditor.py` | 13% | 337 | 🟠 HIGH | Integration auditing |

## Priority 2: Medium-Impact Modules

| Module | Current | Lines | Priority | Impact |
|--------|---------|-------|----------|--------|
| `src/utils/generate_structure_tree.py` | 14% | 74 | 🟡 MEDIUM | Structure analysis |
| `src/utils/extract_commands_summary.py` | 16% | 45 | 🟡 MEDIUM | Command extraction |

## Strategy

1. **Phase 1**: Create test files for Priority 1 modules (directory_context_generator, quick_github_audit)
2. **Phase 2**: Write unit tests covering 50%+ of untested lines
3. **Phase 3**: Add integration tests for resource_cleanup
4. **Target Gain**: ~200-250 additional covered lines → 32-34% coverage

## Notes

- Async tests excluded from pre-push (lines remain in coverage analysis)
- Focus on high-value functions with external dependencies
- Mock external dependencies (GitHub API, file I/O) to avoid flakiness
