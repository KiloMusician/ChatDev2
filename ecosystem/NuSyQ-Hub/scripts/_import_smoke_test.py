import importlib
import sys
from pathlib import Path

# Ensure repo root is on sys.path when running from workspace
repo_root = Path(".").resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

modules = [
    "src.tools.scan_guard",
    "src.unified_documentation_engine",
    "src.real_time_context_monitor",
    "src.utils.directory_context_generator",
    "src.utils.enhanced_directory_context_generator",
    "src.tools.repo_scan",
    "src.tools.kilo_discovery_system",
    "src.healing.quantum_problem_resolver",
    "src.tools.maze_solver",
]

print("Repo root:", repo_root)
for m in modules:
    try:
        importlib.import_module(m)
        print("OK", m)
    except BaseException as e:  # catch SystemExit and other base exceptions too
        # We intentionally catch BaseException so imports that call sys.exit
        # (bad practice but present in some modules) are reported instead
        # of terminating this harness.
        print("ERR", m, type(e).__name__, str(e))
