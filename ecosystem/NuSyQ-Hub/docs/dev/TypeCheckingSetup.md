# Type Checking Setup for NuSyQ-Hub

## Overview

NuSyQ-Hub is a typed Python package following PEP 561 standards. This document
explains how to configure type checkers and install necessary stubs.

## Quick Setup

### 1. Install Development Dependencies

```bash
# Install all dev dependencies including mypy
pip install -e ".[dev]"

# Or install mypy separately
pip install mypy>=1.5.0
```

### 2. Install Type Stubs for Third-Party Libraries

```bash
# Core type stubs
pip install types-requests types-PyYAML types-pytz types-python-dateutil

# Optional: Install all known stubs
mypy --install-types
```

### 3. Configure Your IDE

#### VS Code

The project includes mypy configuration in `pyproject.toml`. VS Code should
automatically use it with the Mypy extension.

**Recommended Extensions:**

- `ms-python.mypy-type-checker` - Official Mypy extension
- `ms-python.python` - Python language support
- `ms-python.vscode-pylance` - Advanced type checking

#### PyCharm

PyCharm includes built-in type checking. Configure it:

1. Settings → Tools → Python Integrated Tools → Type Checker → Mypy
2. Set Mypy path to project virtual environment

## Configuration

### Mypy Settings (in pyproject.toml)

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
ignore_missing_imports = true  # Ignores missing stubs
show_error_codes = true
```

### Key Configuration Options

- `ignore_missing_imports = true` - Prevents errors for libraries without type
  stubs
- `check_untyped_defs = true` - Type-check function bodies even without
  annotations
- `disallow_untyped_defs = false` - Gradually enable stricter checking

## Running Type Checks

### Command Line

```bash
# Check all source code
mypy src/

# Check specific files
mypy src/integration/chatdev_launcher.py

# Check with specific options
mypy src/ --strict --show-error-codes
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.5.0
  hooks:
    - id: mypy
      additional_dependencies: [types-requests, types-PyYAML]
```

## Common Type Stubs Needed

```bash
# Network/HTTP
pip install types-requests

# Configuration
pip install types-PyYAML types-toml

# Date/Time
pip install types-pytz types-python-dateutil

# Utilities
pip install types-setuptools types-pkg-resources
```

## Handling Import Errors

### Option 1: Install Type Stubs

For libraries like `integration.simulatedverse_async_bridge`, the module exists
but type checkers can't find it due to path issues.

**Solution**: Ensure `src/` is in PYTHONPATH:

```bash
# Set in environment
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Or use mypy's path configuration
mypy --python-path src/ src/
```

### Option 2: Type Ignore Comments

For unavoidable import errors:

```python
from integration.simulatedverse_async_bridge import SimulatedVerseBridge  # type: ignore[import]
```

### Option 3: Per-File Configuration

In `pyproject.toml`:

```toml
[[tool.mypy.overrides]]
module = "integration.*"
ignore_missing_imports = true
```

## PEP 561 Compliance

This package includes:

- `src/py.typed` marker file (enables type checking)
- Inline type annotations in source code
- `setup.py` configured to include `py.typed` in distributions

## Troubleshooting

### "Cannot find implementation or library stub"

1. Check if module is installed: `pip list | grep module-name`
2. Install type stubs: `pip install types-module-name`
3. Use `ignore_missing_imports = true` for that module

### "Module has no attribute"

- The library may not have complete type stubs
- Use `# type: ignore` or create a local stub file

### IDE Not Recognizing Types

1. Restart language server
2. Check `pyproject.toml` is in workspace root
3. Ensure correct Python interpreter is selected
4. Clear mypy cache: `rm -rf .mypy_cache`

## Additional Resources

- [PEP 561 - Distributing and Packaging Type Information](https://peps.python.org/pep-0561/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Python Type Checking Guide](https://realpython.com/python-type-checking/)

---

**Note**: Type checking is gradually being improved across the codebase. Current
focus is on core modules (`src/integration/`, `src/orchestration/`,
`src/diagnostics/`).
