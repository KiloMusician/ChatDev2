# Exception Narrowing Pattern Reference

**Purpose**: Standard exception handling patterns to replace bare `except:` clauses

## Why Narrow Exceptions?

Bare `except:` catches **everything**, including:
- ❌ `KeyboardInterrupt` (Ctrl+C) - breaks user control
- ❌ `SystemExit` - breaks program exit
- ❌ `MemoryError` - masks critical system issues
- ❌ Silent failures - makes debugging impossible

**Better**: Catch specific exceptions you know how to handle.

## Standard Exception Patterns

### File Operations
```python
# File reading, writing, path operations
try:
    with open(file_path, 'r') as f:
        content = f.read()
except (OSError, IOError, FileNotFoundError):
    logger.error(f"Failed to read {file_path}")

# File stat/metadata operations
try:
    mtime = os.path.getmtime(file_path)
except (OSError, ValueError):
    mtime = time.time()  # fallback
```

**Exception Types**:
- `OSError` - Broad OS errors (permissions, disk, network)
- `IOError` - I/O specific errors (often aliased to OSError)
- `FileNotFoundError` - File doesn't exist (subclass of OSError)
- `ValueError` - Invalid path format or conversion

### Network/HTTP Operations
```python
# HTTP requests
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except (
    OSError,
    requests.RequestException,
    requests.Timeout,
    ValueError,
) as e:
    logger.error(f"HTTP request failed: {e}")
```

**Exception Types**:
- `requests.RequestException` - Base requests exception (connection, HTTP, etc.)
- `requests.Timeout` - Request timed out (subclass of RequestException)
- `OSError` - Network-level errors
- `ValueError` - Invalid URL or parameter format

### Subprocess Operations
```python
# Running external commands
try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        timeout=30,
        check=True,  # Raises CalledProcessError on non-zero exit
    )
except (
    subprocess.SubprocessError,
    subprocess.TimeoutExpired,
    subprocess.CalledProcessError,
    OSError,
) as e:
    logger.error(f"Subprocess failed: {e}")
```

**Exception Types**:
- `subprocess.SubprocessError` - Base subprocess exception
- `subprocess.TimeoutExpired` - Command exceeded timeout
- `subprocess.CalledProcessError` - Non-zero exit code (with check=True)
- `OSError` - Command not found, permission denied

### Data Parsing
```python
# JSON/dict parsing
try:
    value = data['key']['nested']
    count = int(value)
except (KeyError, IndexError, AttributeError, ValueError) as e:
    logger.warning(f"Failed to parse data: {e}")
    value = default_value
```

**Exception Types**:
- `KeyError` - Dictionary key doesn't exist
- `IndexError` - List index out of range
- `AttributeError` - Attribute doesn't exist on object
- `ValueError` - Type conversion failed (int, float, etc.)

### Regex/String Operations
```python
# Regular expression matching
try:
    match = re.match(pattern, text)
    result = match.group(1)
except (IndexError, AttributeError, ValueError):
    result = None  # No match or invalid group
```

**Exception Types**:
- `IndexError` - Group number out of range
- `AttributeError` - match is None (no .group() method)
- `ValueError` - Invalid regex or group reference

### Database Operations
```python
# Database queries
try:
    cursor.execute(query, params)
    result = cursor.fetchone()
except (sqlite3.Error, sqlite3.OperationalError) as e:
    logger.error(f"Database error: {e}")
    connection.rollback()
```

**Exception Types**:
- `sqlite3.Error` - Base SQLite exception
- `sqlite3.OperationalError` - Database locked, schema errors
- `sqlite3.IntegrityError` - Constraint violations

### Import Operations
```python
# Dynamic imports
try:
    from src.module import Component
except (ImportError, ModuleNotFoundError) as e:
    logger.warning(f"Failed to import: {e}")
    # Fallback import or graceful degradation
```

**Exception Types**:
- `ImportError` - Module exists but import failed
- `ModuleNotFoundError` - Module doesn't exist (subclass of ImportError)

## Multi-Context Exception Handling

When an operation involves multiple failure modes:

```python
# Example: File + JSON + Network operation
try:
    with open(config_file, 'r') as f:
        config = json.load(f)

    response = requests.post(url, json=config, timeout=10)
    response.raise_for_status()

except (OSError, IOError) as e:
    logger.error(f"File error: {e}")
except (json.JSONDecodeError, ValueError) as e:
    logger.error(f"JSON parsing error: {e}")
except (requests.RequestException, requests.Timeout) as e:
    logger.error(f"Network error: {e}")
```

**Strategy**: Separate exception handlers for different failure categories.

## Fallback Pattern (Last Resort)

If you truly need to catch unexpected errors:

```python
try:
    # Operation
    result = complex_operation()
except (ExpectedError1, ExpectedError2) as e:
    # Handle known errors
    logger.error(f"Known error: {e}")
    result = default_value
except Exception as e:
    # Catch unknown errors BUT:
    # 1. Log with full traceback
    # 2. Re-raise or propagate
    # 3. Don't silently continue
    logger.exception(f"Unexpected error: {e}")
    raise  # Re-raise to preserve stack trace
```

**Key**: Use `except Exception` **only** when:
1. You log the full traceback (`logger.exception()`)
2. You re-raise the exception OR it's truly a last-ditch fallback
3. You document why you're catching broad exceptions

## Line Length Management

For long exception tuples (79 character limit):

```python
# ✅ Good: Multi-line formatting
except (
    subprocess.SubprocessError,
    subprocess.TimeoutExpired,
    OSError,
) as e:
    logger.error(f"Subprocess failed: {e}")

# ❌ Bad: Single line over 79 characters
except (subprocess.SubprocessError, subprocess.TimeoutExpired, OSError) as e:
```

## Error Parameter Usage

Always capture the exception for logging:

```python
# ✅ Good: Capture exception for context
except (OSError, ValueError) as e:
    logger.error(f"Operation failed: {e}", exc_info=True)

# ⚠️ Acceptable: Silent handling with comment
except (OSError, ValueError):
    # Expected error: file may not exist yet
    pass

# ❌ Bad: Bare pass without comment
except (OSError, ValueError):
    pass
```

## Testing Exception Handling

Verify your exception narrowing works:

```python
import pytest

def test_narrow_exception_handling():
    # Test that specific exceptions are caught
    with pytest.raises(ValueError):
        problematic_function(invalid_input)

    # Test that unexpected exceptions propagate
    with pytest.raises(AttributeError):
        problematic_function(unexpected_input)
```

## Remediation Checklist

When replacing `except:` with narrow exceptions:

- [ ] Identify what operations are in the try block
- [ ] List expected failure modes for each operation
- [ ] Choose specific exception classes for those failures
- [ ] Add error parameter (`as e`) for logging
- [ ] Log the exception with context
- [ ] Test that expected exceptions are caught
- [ ] Test that unexpected exceptions propagate

## Common Anti-Patterns

### ❌ Anti-Pattern 1: Silent Broad Catch
```python
try:
    critical_operation()
except:
    pass  # BAD: Silently ignores ALL errors
```

### ❌ Anti-Pattern 2: Catching Too Much
```python
try:
    simple_dict_access = data['key']
except Exception:  # BAD: KeyError is specific enough
    pass
```

### ❌ Anti-Pattern 3: Not Logging
```python
try:
    important_operation()
except (OSError, ValueError):
    pass  # BAD: No logging, error context lost
```

### ✅ Correct Pattern
```python
try:
    result = risky_operation()
except (OSError, ValueError) as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    result = safe_default_value
```

## Real-World Examples from Remediation

### Example 1: HTTP Request Error
**File**: ChatDev/visualizer/app.py  
**Before**:
```python
try:
    response = requests.post(url, json=data)
except:
    logging.info("Error sending message to visualization server")
```

**After**:
```python
try:
    response = requests.post(url, json=data, timeout=10)
except (OSError, requests.RequestException, ValueError) as e:
    logging.info("Error sending message to visualization server: %s", e)
```

### Example 2: Subprocess Error
**File**: SimulatedVerse/scripts/runners/ultimate_cascade_activator.py  
**Before**:
```python
try:
    result = subprocess.run(["git", "push"], ...)
except:
    print(f"Git push failed")
```

**After**:
```python
try:
    result = subprocess.run(["git", "push"], timeout=30, ...)
except (
    subprocess.SubprocessError,
    subprocess.TimeoutExpired,
    OSError,
) as e:
    print(f"Git push failed: {e}")
```

### Example 3: File Metadata
**File**: SimulatedVerse/narrative-architectures/corridor-navigation/corridor_system.py  
**Before**:
```python
try:
    return os.path.getmtime(file_path)
except:
    return time.time()
```

**After**:
```python
try:
    return os.path.getmtime(file_path)
except (OSError, ValueError):
    return time.time()
```

## Exception Hierarchy Quick Reference

Python's exception hierarchy (key branches):

```
BaseException
├── SystemExit (caught by bare except)
├── KeyboardInterrupt (caught by bare except)
├── GeneratorExit
└── Exception
    ├── OSError
    │   ├── FileNotFoundError
    │   ├── PermissionError
    │   └── TimeoutError
    ├── ValueError
    │   └── json.JSONDecodeError
    ├── TypeError
    ├── AttributeError
    ├── KeyError
    ├── IndexError
    ├── ImportError
    │   └── ModuleNotFoundError
    ├── subprocess.SubprocessError
    │   ├── subprocess.TimeoutExpired
    │   └── subprocess.CalledProcessError
    └── requests.RequestException
        ├── requests.Timeout
        ├── requests.HTTPError
        └── requests.ConnectionError
```

**Rule**: Catch `Exception` instead of bare `except:` to allow `KeyboardInterrupt` and `SystemExit` to propagate.

---

**Last Updated**: 2025-01-18  
**Maintained By**: NuSyQ Multi-AI Orchestration System  
**Related Documents**:
- `docs/Agent-Sessions/REMEDIATION_WAVE_20250118_SUMMARY.md`
- `docs/SUBPROCESS_TIMEOUT_REFERENCE.md`
