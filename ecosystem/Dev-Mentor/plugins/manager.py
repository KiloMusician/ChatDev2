"""
Plugin Manager — discovers, loads, and executes DevMentor plugins.

Each plugin is a directory under plugins/ containing:
  manifest.json  — name, version, description, entry_point, category
  <entry_point>  — Python module with plugin(input: str, config: dict) -> str

Usage:
    from plugins.manager import PluginManager
    pm = PluginManager()
    result = pm.run("challenge_generator", '{"category": "networking", "difficulty": "hard"}')
    print(pm.list_plugins())
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional


PLUGINS_DIR = Path(__file__).parent
PLUGIN_TIMEOUT = 30  # seconds


class PluginError(Exception):
    pass


class Plugin:
    def __init__(self, directory: Path):
        self.dir = directory
        manifest_path = directory / "manifest.json"
        if not manifest_path.exists():
            raise PluginError(f"Missing manifest.json in {directory}")
        self.manifest = json.loads(manifest_path.read_text())
        self.name = self.manifest.get("name", directory.name)
        self.version = self.manifest.get("version", "0.1.0")
        self.description = self.manifest.get("description", "")
        self.entry_point = self.manifest.get("entry_point", "plugin.py")
        self.category = self.manifest.get("category", "general")
        self.enabled = self.manifest.get("enabled", True)
        self._module = None

    def _load(self):
        if self._module is not None:
            return
        entry = self.dir / self.entry_point
        if not entry.exists():
            raise PluginError(f"Entry point not found: {entry}")
        spec = importlib.util.spec_from_file_location(f"plugins.{self.name}", entry)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "plugin"):
            raise PluginError(f"Plugin {self.name} must define plugin(input, config) function")
        self._module = mod

    def run(self, input_data: str, config: dict | None = None) -> str:
        self._load()
        result = {"output": None, "error": None}

        def _exec():
            try:
                result["output"] = self._module.plugin(input_data, config or {})
            except Exception as exc:
                result["error"] = str(exc)

        t = threading.Thread(target=_exec, daemon=True)
        t.start()
        t.join(timeout=PLUGIN_TIMEOUT)
        if t.is_alive():
            raise PluginError(f"Plugin {self.name} timed out after {PLUGIN_TIMEOUT}s")
        if result["error"]:
            raise PluginError(result["error"])
        return str(result["output"] or "")

    def metadata(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "enabled": self.enabled,
            "entry_point": self.entry_point,
        }


class PluginManager:
    """Discovers and manages all plugins in the plugins/ directory."""

    def __init__(self, plugins_dir: Path | str = PLUGINS_DIR):
        self._dir = Path(plugins_dir)
        self._plugins: dict[str, Plugin] = {}
        self._lock = threading.Lock()
        self._discover()

    def _discover(self):
        for subdir in self._dir.iterdir():
            if subdir.is_dir() and (subdir / "manifest.json").exists():
                try:
                    p = Plugin(subdir)
                    if p.enabled:
                        self._plugins[p.name] = p
                except Exception as exc:
                    pass  # silently skip bad plugins on startup

    def refresh(self):
        with self._lock:
            self._plugins.clear()
            self._discover()

    def list_plugins(self) -> list[dict]:
        return [p.metadata() for p in self._plugins.values()]

    def get(self, name: str) -> Optional[Plugin]:
        return self._plugins.get(name)

    def run(self, name: str, input_data: str = "", config: dict | None = None) -> dict:
        t0 = time.time()
        plugin = self.get(name)
        if not plugin:
            return {"ok": False, "error": f"Plugin not found: {name}", "plugins": list(self._plugins)}
        try:
            output = plugin.run(input_data, config)
            elapsed = round((time.time() - t0) * 1000)
            return {"ok": True, "plugin": name, "output": output, "duration_ms": elapsed}
        except PluginError as exc:
            return {"ok": False, "error": str(exc)}

    def install(self, git_url: str, quiet: bool = False) -> dict:
        """Clone a plugin repository into the plugins directory."""
        name = git_url.rstrip("/").split("/")[-1].replace(".git", "")
        target = self._dir / name
        if target.exists():
            return {"ok": False, "error": f"Plugin '{name}' already exists"}
        try:
            result = subprocess.run(
                ["git", "clone", "--depth=1", git_url, str(target)],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return {"ok": False, "error": result.stderr[:200]}
            self.refresh()
            return {"ok": True, "installed": name, "path": str(target)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


# ── Module singleton ──────────────────────────────────────────────────────────

_manager: PluginManager | None = None


def get_manager() -> PluginManager:
    global _manager
    if _manager is None:
        _manager = PluginManager()
    return _manager


if __name__ == "__main__":
    pm = PluginManager()
    plugins = pm.list_plugins()
    print(f"Loaded {len(plugins)} plugins:")
    for p in plugins:
        print(f"  [{p['category']}] {p['name']} v{p['version']} — {p['description']}")

    if len(sys.argv) > 1:
        name = sys.argv[1]
        inp = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        result = pm.run(name, inp)
        print(json.dumps(result, indent=2))
