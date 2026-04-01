"""Compatibility shim for tests that import `copilot_agent_launcher` as a top-level module.

The real implementation lives in `src/scripts/copilot_agent_launcher.py` so tests that
expect the module at the project root will continue to work. This shim re-exports
the implementation from the src package.

This is a small, durable fix to make imports predictable without changing tests.
"""

from src.scripts.copilot_agent_launcher import (
    analyze_file,
    extract_classes,
    extract_functions,
    extract_imports,
    generate_agent_task,
    get_changed_files,
    get_language,
    get_target_files,
    main,
    parse_args,
)

__all__ = [
    "analyze_file",
    "extract_classes",
    "extract_functions",
    "extract_imports",
    "generate_agent_task",
    "get_changed_files",
    "get_language",
    "get_target_files",
    "main",
    "parse_args",
]
