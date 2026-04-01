import py_compile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def find_python_files(root: Path):
    for p in root.rglob("*.py"):
        # skip virtualenvs, caches, and tests
        if any(part in ("venv", ".venv", ".mypy_cache", "__pycache__") for part in p.parts):
            continue
        # skip hidden directories
        if any(part.startswith(".") for part in p.parts):
            continue
        yield p


@pytest.mark.parametrize("py_file", list(find_python_files(ROOT / "src")))
def test_py_compile(py_file):
    """Ensure Python files are syntactically valid (py_compile).

    This is a fast smoke check that avoids executing module-level code.
    """
    # Retry on PermissionError (Windows pycache race with parallel tests)
    for attempt in range(3):
        try:
            py_compile.compile(str(py_file), doraise=True)
            break
        except py_compile.PyCompileError as e:
            pytest.fail(f"Syntax error compiling {py_file}: {e}")
        except PermissionError:
            if attempt < 2:
                time.sleep(0.1 * (attempt + 1))
            else:
                # On final attempt, skip rather than fail (pycache race)
                pytest.skip(f"Windows pycache permission race: {py_file}")
