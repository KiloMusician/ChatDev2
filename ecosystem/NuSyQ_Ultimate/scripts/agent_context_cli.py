"""CLI helper to register files and snippets into AgentContextManager.

Usage:
  python scripts/agent_context_cli.py --namespace kilo --path path/to/file.py

Optional:
  --push-mcp http://localhost:8000/mcp  # POST the context payload to MCP server
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from pathlib import Path as _Path
from typing import Optional

import requests

# Initialize terminal logging (best-effort) so CLI logs are forwarded into
# TerminalManager channels when available.
try:
    from src.system.init_terminal import init_terminal_logging

    init_terminal_logging(channel="AgentContextCLI")
except (ImportError, OSError, RuntimeError):
    pass


def _find_repo_with_agent_manager(start: _Path) -> Optional[_Path]:
    """Walk up directories looking for src/tools/agent_context_manager.py.

    Returns the path to the repository root (the folder that contains `src/`) or None.
    """
    path = start
    while path != path.parent:
        candidate = path / "src" / "tools" / "agent_context_manager.py"
        if candidate.exists():
            return path
        # also check a sibling convention like Foo-Hub or FooRepo
        sibling = path.parent / (path.name + "-Hub")
        if (sibling / "src" / "tools" / "agent_context_manager.py").exists():
            return sibling
        path = path.parent
    return None


# Ensure the repo that contains src/tools/agent_context_manager.py is on sys.path.
# This helps when the CLI is executed from a temporary directory during tests.
script_dir = _Path(__file__).resolve().parent
found = _find_repo_with_agent_manager(script_dir)
if not found:
    found = _find_repo_with_agent_manager(_Path.cwd())

if found:
    rp = str(found)
    if rp not in sys.path:
        sys.path.insert(0, rp)
else:
    # Minimal fallback: add current script parent and its parent so imports may resolve
    for candidate in (script_dir.parent, script_dir.parent.parent):
        sc = str(candidate)
        if sc not in sys.path:
            sys.path.insert(0, sc)


# Try to import the real manager. If it's not available (rare in tests run from tmp
# dirs), fall back to a tiny local manager implementation so CLI tests can still run.
try:
    from src.tools.agent_context_manager import AgentContextManager  # type: ignore
except (ImportError, ModuleNotFoundError):
    # Lightweight fallback manager used only for test environments where the
    # repository layout isn't importable. This mirrors the minimal interface used by tests.
    import json
    from dataclasses import dataclass

    @dataclass
    class AgentContextManager:
        repo_root: Path
        storage_name: str = ".agent_contexts.json"

        def _storage_path(self, namespace: str) -> Path:
            return self.repo_root / f"{namespace}{self.storage_name}"

        def register_from_file(self, path: Path, namespace: str) -> dict:
            content = path.read_text(encoding="utf-8")
            p = self._storage_path(namespace)
            data = {"path": str(path), "content": content}
            p.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return {"namespace": namespace, "path": str(path)}

        def load(self, namespace: str) -> dict:
            p = self._storage_path(namespace)
            if not p.exists():
                return {}
            return json.loads(p.read_text(encoding="utf-8"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--namespace", required=True)
    p.add_argument("--path", required=True)
    p.add_argument("--push-mcp", required=False)
    args = p.parse_args()

    repo_root = Path.cwd()
    mgr = AgentContextManager(repo_root=repo_root)
    file_path = Path(args.path)
    meta = mgr.register_from_file(file_path, args.namespace)
    print("Registered:", meta)

    if args.push_mcp:
        payload = mgr.load(args.namespace)
        try:
            resp = requests.post(args.push_mcp, json=payload, timeout=5)
            print("MCP push status:", resp.status_code)
        except (requests.RequestException, OSError, ValueError, TypeError) as e:
            print("MCP push failed:", e)


if __name__ == "__main__":
    main()
