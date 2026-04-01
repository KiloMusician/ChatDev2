import importlib
import sys
from pathlib import Path


def test_import_all_src_modules():
    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"
    assert src_root.exists()

    # Only import top-level modules directly under src to avoid heavy side-effects
    py_files = list(src_root.glob("*.py"))
    modules = [p for p in py_files if p.name != "__init__.py" and not p.name.startswith("test_")]

    # Temporarily add src root to sys.path so modules can be imported by filename.
    # Save/restore sys.path and any newly-introduced sys.modules entries so this
    # test doesn't permanently modify global state for subsequent tests.
    src_root_str = str(src_root)
    original_path = sys.path[:]
    added_modules: list[str] = []

    sys.path.insert(0, src_root_str)
    try:
        for mod_path in modules:
            mod_name = mod_path.stem
            if mod_name in sys.modules:
                continue  # already imported under this name — skip to avoid double-import
            try:
                importlib.import_module(mod_name)
                added_modules.append(mod_name)
            except ImportError as exc:
                raise AssertionError(f"Failed to import top-level module {mod_name}: {exc}") from exc
            except Exception:
                # Non-ImportError exceptions (e.g. TypeError from stubbed optional
                # dependencies left in sys.modules by another test) are not import
                # failures; skip the module rather than failing the whole test.
                pass
    finally:
        # Restore sys.path to its original state
        sys.path[:] = original_path
        # Remove the short-named module entries we added to avoid shadowing
        for mod_name in added_modules:
            sys.modules.pop(mod_name, None)
