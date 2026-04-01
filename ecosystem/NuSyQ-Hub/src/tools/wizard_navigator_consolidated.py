#!/usr/bin/env python3
"""🧙 Wizard Navigator - Canonical Version.

Rogue-like repository exploration with AI integration.
Consolidates 3 previous versions into single production implementation.

OmniTag: {
    "purpose": "Repository exploration wizard with AI assistance",
    "dependencies": ["pathlib", "chatdev_integration"],
    "context": "Interactive navigation and code analysis",
    "evolution_stage": "v2.0-consolidated"
}
"""

import contextlib
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    from datetime import UTC
except ImportError:  # pragma: no cover - Python 3.10
    from datetime import timezone

    UTC = timezone.utc  # noqa: UP017

logger = logging.getLogger(__name__)


class WizardNavigator:
    """Interactive repository navigator with rogue-like exploration.

    Features:
    - Directory-based room navigation
    - File inspection and analysis
    - AI-assisted code exploration via ChatDev
    - Quest/achievement integration
    - Temple knowledge archival
    """

    def __init__(self, root: str | Path = ".") -> None:
        """Initialize Wizard Navigator.

        Args:
            root: Repository root directory
        """
        self.root = Path(root).resolve()
        self.current_path = self.root
        self.visited_paths: set[Path] = set()
        self.discoveries: list[dict] = []
        self.recent_paths: list[str] = []
        self.bookmarks: dict[str, str] = {}
        self.notes: dict[str, list[str]] = {}
        self.defaults = self._load_defaults()
        self.wizard_defaults = self.defaults.get("wizard_navigator", {})
        self.notes_scope = str(self.wizard_defaults.get("notes_scope", "per_repo"))
        self.exclude_dirs = {
            entry.strip("/\\")
            for entry in self.wizard_defaults.get("exclude_from_scans", [])
            if isinstance(entry, str) and entry
        }
        self.cross_repo_search_limit = int(
            self.wizard_defaults.get("cross_repo_search_limit", 50) or 50
        )
        self.cross_repo_search_depth = self.wizard_defaults.get(
            "cross_repo_search_depth", "shallow"
        )
        self.use_ripgrep = bool(self.wizard_defaults.get("use_ripgrep_if_available", True))
        self.readiness_weights = self.wizard_defaults.get(
            "readiness_weights",
            {"tests": 0.4, "docs": 0.3, "config": 0.2, "coverage": 0.1},
        )
        self.mandatory_readiness = set(
            self.wizard_defaults.get(
                "mandatory_readiness_signals", ["README", "tests", "config", "tasks"]
            )
        )
        self.observability_granularity = int(
            self.wizard_defaults.get("observability_granularity", 3) or 3
        )
        self.state_path = self._resolve_state_path()
        self._load_state()
        self.repo_root = self._detect_repo_root()
        self.repo_roots = self._find_repo_roots()

        logger.info(f"🧙 Wizard Navigator initialized at {self.root}")

    def _resolve_state_path(self) -> Path:
        data_dir = self.root / "data"
        if data_dir.exists():
            return data_dir / "wizard_navigator_state.json"
        return self.root / ".wizard_navigator_state.json"

    def _load_defaults(self) -> dict[str, Any]:
        defaults_path = self.root / "config" / "ecosystem_defaults.json"
        if not defaults_path.exists():
            return {}
        try:
            data = json.loads(defaults_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
            return {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _load_state(self) -> None:
        if not self.state_path.exists():
            return
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        self.bookmarks = {str(key): str(value) for key, value in state.get("bookmarks", {}).items()}
        self.recent_paths = [str(p) for p in state.get("recent_paths", [])]
        self.notes = {
            str(key): [str(item) for item in value]
            for key, value in state.get("notes", {}).items()
            if isinstance(value, list)
        }

        last_path = state.get("last_path")
        if last_path:
            candidate = Path(last_path)
            if candidate.exists():
                self.current_path = candidate

    def _save_state(self) -> None:
        state = {
            "root": str(self.root),
            "last_path": str(self.current_path),
            "bookmarks": self.bookmarks,
            "recent_paths": self.recent_paths[-20:],
            "notes": self.notes,
            "saved_at": datetime.now(UTC).isoformat(),
        }
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except OSError:
            return

    def _remember_path(self, path: Path) -> None:
        entry = str(path)
        if entry in self.recent_paths:
            self.recent_paths.remove(entry)
        self.recent_paths.append(entry)
        self.recent_paths = self.recent_paths[-20:]
        self._save_state()

    def _detect_repo_root(self) -> Path | None:
        if (self.root / ".git").exists():
            return self.root
        try:
            result = subprocess.run(
                ["git", "-C", str(self.root), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return None
        if result.returncode != 0:
            return None
        resolved = result.stdout.strip()
        return Path(resolved) if resolved else None

    def _find_repo_roots(self) -> dict[str, Path]:
        roots: dict[str, Path] = {}
        env_map = {
            "nusyq_hub": os.getenv("NUSYQ_HUB_PATH"),
            "simulatedverse": os.getenv("SIMULATEDVERSE_PATH"),
            "nusyq": os.getenv("NUSYQ_ROOT_PATH"),
        }
        for key, value in env_map.items():
            if value:
                path = Path(value).expanduser()
                if path.exists():
                    roots[key] = path

        parent = self.root.parent
        candidates = {
            "nusyq_hub": self.root,
            "simulatedverse": parent / "SimulatedVerse",
            "nusyq": parent / "NuSyQ",
        }
        for key, path in candidates.items():
            if key not in roots and path.exists():
                roots[key] = path

        return roots

    def _parse_args(self, args: list[str]) -> tuple[set[str], dict[str, str], list[str]]:
        flags: set[str] = set()
        values: dict[str, str] = {}
        rest: list[str] = []
        iterator = iter(args)
        for token in iterator:
            if token in ("-a", "--all"):
                flags.add("all")
            elif token in ("-e", "--ext"):
                values["ext"] = next(iterator, "")
            elif token in ("-d", "--depth"):
                values["depth"] = next(iterator, "")
            elif token in ("-n", "--limit", "--count"):
                values["limit"] = next(iterator, "")
            elif token in ("-r", "--deep", "--recursive"):
                flags.add("deep")
            elif token in ("--regex",):
                flags.add("regex")
            elif token in ("--case",):
                flags.add("case")
            elif token in ("--system",):
                flags.add("system")
            else:
                rest.append(token)
        return flags, values, rest

    def _normalize_ext(self, ext: str | None) -> str | None:
        if not ext:
            return None
        ext = ext.strip()
        if not ext:
            return None
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext.lower()

    def _is_hidden(self, path: Path) -> bool:
        return any(part.startswith(".") for part in path.parts if part and part != path.anchor)

    def _is_excluded(self, path: Path) -> bool:
        return any(part in self.exclude_dirs for part in path.parts if part)

    def _iter_files(self, root: Path, recursive: bool, show_hidden: bool) -> list[Path]:
        if recursive:
            candidates = [p for p in root.rglob("*") if p.is_file()]
        else:
            candidates = [p for p in root.iterdir() if p.is_file()]
        candidates = [p for p in candidates if not self._is_excluded(p)]
        if show_hidden:
            return candidates
        return [p for p in candidates if not self._is_hidden(p)]

    def _iter_text_lines(self, path: Path, limit_bytes: int) -> list[tuple[int, str]]:
        try:
            if path.stat().st_size > limit_bytes:
                return []
        except OSError:
            return []
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                return [(idx, line.rstrip("\n")) for idx, line in enumerate(handle, 1)]
        except OSError:
            return []

    def _format_size(self, size: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.0f} {unit}"
            size = int(size / 1024)
        return f"{size:.0f} TB"

    def get_current_room(self) -> dict:
        """Get current room description."""
        if not self.current_path.exists():
            return {
                "name": "Unknown",
                "description": "Path does not exist",
                "exits": [],
                "items": [],
            }

        # Get subdirectories (exits)
        exits = [d.name for d in self.current_path.iterdir() if d.is_dir()]

        # Get files (items)
        items = [f.name for f in self.current_path.iterdir() if f.is_file()]

        # Mark as visited
        self.visited_paths.add(self.current_path)
        self._remember_path(self.current_path)

        return {
            "name": self.current_path.name or "root",
            "path": str(self.current_path),
            "description": f"A directory containing {len(items)} files and {len(exits)} subdirectories",
            "exits": exits,
            "items": items,
            "visited": self.current_path in self.visited_paths,
        }

    def display_room(self, show_hidden: bool = False, ext_filter: str | None = None) -> str:
        """Display current room with ASCII art."""
        room = self.get_current_room()
        exits = room["exits"]
        items = room["items"]
        if not show_hidden:
            exits = [name for name in exits if not name.startswith(".")]
            items = [name for name in items if not name.startswith(".")]
        normalized_ext = self._normalize_ext(ext_filter)
        if normalized_ext:
            items = [name for name in items if name.lower().endswith(normalized_ext)]

        output = [
            f"\n{'=' * 60}",
            f"🏛️  {room['name']}",
            f"{'=' * 60}",
            f"📍 {room['path']}",
            f"{room['description']}",
            "",
        ]

        if exits:
            output.append("🚪 Exits:")
            for exit_name in exits[:10]:  # Limit display
                marker = "✓" if (self.current_path / exit_name) in self.visited_paths else "○"
                output.append(f"   {marker} {exit_name}")
            if len(exits) > 10:
                output.append(f"   ... and {len(exits) - 10} more")

        if items:
            output.append("\n📜 Items:")
            for item in items[:10]:  # Limit display
                output.append(f"   • {item}")
            if len(items) > 10:
                output.append(f"   ... and {len(items) - 10} more")

        output.append(f"{'=' * 60}\n")
        return "\n".join(output)

    def move(self, direction: str) -> str:
        """Move to a subdirectory.

        Args:
            direction: Directory name or special command (.., root)

        Returns:
            Movement result message
        """
        if direction == "..":
            # Go up one level
            if self.current_path != self.root:
                self.current_path = self.current_path.parent
                self._remember_path(self.current_path)
                return f"⬆️  Moved up to {self.current_path.name}"
            return "⚠️  Already at root directory"

        if direction == "root":
            self.current_path = self.root
            self._remember_path(self.current_path)
            return "🏠 Returned to root"

        # Try to move to named directory
        target = self.current_path / direction
        if target.exists() and target.is_dir():
            self.current_path = target
            self._remember_path(self.current_path)
            return f"➡️  Moved to {direction}"

        return f"❌ Cannot move to '{direction}' - not found or not a directory"

    def inspect(self, item_name: str) -> str:
        """Inspect a file in the current room.

        Args:
            item_name: File name to inspect

        Returns:
            File information
        """
        target = self.current_path / item_name

        if not target.exists():
            return f"❌ '{item_name}' not found"

        if target.is_dir():
            return f"📁 '{item_name}' is a directory - use 'go {item_name}' to enter"

        # File inspection
        stats = target.stat()
        size_kb = stats.st_size / 1024

        info = [
            f"📄 {item_name}",
            f"   Size: {size_kb:.2f} KB",
            f"   Type: {target.suffix or 'no extension'}",
        ]

        # Try to read first few lines for text files
        if target.suffix in [".py", ".txt", ".md", ".json", ".yaml", ".toml", ".sh"]:
            try:
                with target.open("r", encoding="utf-8") as f:
                    lines = [f.readline().strip() for _ in range(5)]
                info.append("\n   Preview:")
                for line in lines:
                    if line:
                        info.append(f"   {line[:80]}")
            except (FileNotFoundError, UnicodeDecodeError, OSError, PermissionError):
                info.append("   (binary or unreadable)")

        return "\n".join(info)

    def search(self, pattern: str) -> str:
        """Search for files matching pattern in current subtree.

        Args:
            pattern: Glob pattern (e.g., "*.py", "test_*")

        Returns:
            Search results
        """
        matches = [p for p in self.current_path.rglob(pattern) if not self._is_excluded(p)]

        if not matches:
            return f"🔍 No files matching '{pattern}' found"

        results = [f"🔍 Found {len(matches)} matches for '{pattern}':\n"]
        for match in matches[:20]:  # Limit results
            rel_path = match.relative_to(self.current_path)
            results.append(f"   • {rel_path}")

        if len(matches) > 20:
            results.append(f"   ... and {len(matches) - 20} more")

        return "\n".join(results)

    def stats(self) -> str:
        """Get exploration statistics."""
        total_dirs = sum(1 for _ in self.root.rglob("*") if _.is_dir())
        visited_pct = (len(self.visited_paths) / total_dirs * 100) if total_dirs > 0 else 0

        return f"""
📊 Exploration Statistics:
   Visited: {len(self.visited_paths)} rooms
   Total: {total_dirs} directories
   Coverage: {visited_pct:.1f}%
   Discoveries: {len(self.discoveries)}
"""

    def add_bookmark(self, name: str) -> str:
        """Bookmark the current location."""
        if not name:
            return "Usage: bookmark <name>"
        self.bookmarks[name] = str(self.current_path)
        self._save_state()
        return f"Bookmarked '{name}' -> {self.current_path}"

    def list_bookmarks(self) -> str:
        """List saved bookmarks."""
        if not self.bookmarks:
            return "No bookmarks saved."
        lines = ["Bookmarks:"]
        for name, path in sorted(self.bookmarks.items()):
            lines.append(f"  {name}: {path}")
        return "\n".join(lines)

    def jump_to_bookmark(self, name: str) -> str:
        """Jump to a bookmarked path."""
        if not name:
            return "Usage: jump <bookmark>"
        target = self.bookmarks.get(name)
        if not target:
            return f"No bookmark named '{name}'."
        path = Path(target)
        if not path.exists():
            return f"Bookmark '{name}' points to missing path: {target}"
        self.current_path = path
        self._remember_path(self.current_path)
        return self.display_room()

    def list_recent(self) -> str:
        """List recently visited paths."""
        if not self.recent_paths:
            return "No recent paths recorded."
        lines = ["Recent paths:"]
        for entry in reversed(self.recent_paths[-10:]):
            lines.append(f"  {entry}")
        return "\n".join(lines)

    def snapshot(self) -> str:
        """Write a markdown snapshot of the current room."""
        reports_dir = self.root / "state" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"wizard_snapshot_{timestamp}.md"

        room = self.get_current_room()
        lines = [
            "# Wizard Navigator Snapshot",
            "",
            f"- Generated: {datetime.now(UTC).isoformat()}",
            f"- Path: {room['path']}",
            f"- Exits: {len(room['exits'])}",
            f"- Items: {len(room['items'])}",
            "",
            "## Exits",
        ]
        lines.extend([f"- {exit_name}" for exit_name in room["exits"][:25]])
        if len(room["exits"]) > 25:
            lines.append(f"- ... and {len(room['exits']) - 25} more")
        lines.extend(["", "## Items"])
        lines.extend([f"- {item}" for item in room["items"][:25]])
        if len(room["items"]) > 25:
            lines.append(f"- ... and {len(room['items']) - 25} more")

        report_path.write_text("\n".join(lines), encoding="utf-8")
        return f"Snapshot saved: {report_path}"

    def trail(self) -> str:
        """Write a navigation trail report."""
        reports_dir = self.root / "state" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"wizard_trail_{timestamp}.md"

        visited = sorted(str(path) for path in self.visited_paths)
        lines = [
            "# Wizard Navigator Trail",
            "",
            f"- Generated: {datetime.now(UTC).isoformat()}",
            f"- Current: {self.current_path}",
            "",
            "## Recent Paths",
        ]
        lines.extend([f"- {entry}" for entry in reversed(self.recent_paths[-20:])])
        lines.extend(["", "## Visited Paths"])
        lines.extend([f"- {entry}" for entry in visited[:200]])
        if len(visited) > 200:
            lines.append(f"- ... and {len(visited) - 200} more")

        report_path.write_text("\n".join(lines), encoding="utf-8")
        return f"Trail saved: {report_path}"

    def tree(self, depth: int = 2, show_hidden: bool = False, limit: int = 200) -> str:
        """Render a shallow tree of the current directory."""
        lines: list[str] = []
        base = self.current_path

        def walk(path: Path, prefix: str, current_depth: int) -> None:
            if len(lines) >= limit:
                return
            try:
                entries = sorted(
                    path.iterdir(),
                    key=lambda p: (not p.is_dir(), p.name.lower()),
                )
            except OSError:
                return

            for entry in entries:
                if not show_hidden and self._is_hidden(entry):
                    continue
                if self._is_excluded(entry):
                    continue
                marker = "/" if entry.is_dir() else ""
                lines.append(f"{prefix}{entry.name}{marker}")
                if len(lines) >= limit:
                    return
                if entry.is_dir() and current_depth < depth:
                    walk(entry, prefix + "  ", current_depth + 1)
                    if len(lines) >= limit:
                        return

        lines.append(str(base))
        walk(base, "  ", 1)
        if len(lines) >= limit:
            lines.append("... tree truncated ...")
        return "\n".join(lines)

    def size_report(self, deep: bool = False, limit: int = 10, show_hidden: bool = False) -> str:
        """List largest files in the current room (or subtree)."""
        files = self._iter_files(self.current_path, recursive=deep, show_hidden=show_hidden)
        sizes: list[tuple[int, Path]] = []
        for path in files:
            try:
                sizes.append((path.stat().st_size, path))
            except OSError:
                continue
        sizes.sort(key=lambda item: item[0], reverse=True)
        top = sizes[:limit]
        if not top:
            return "No files found."

        lines = ["Largest files:"]
        for size, path in top:
            rel_path = path
            with contextlib.suppress(ValueError):
                rel_path = path.relative_to(self.current_path)
            lines.append(f"  {self._format_size(size)}  {rel_path}")
        return "\n".join(lines)

    def grep(
        self,
        pattern: str,
        deep: bool = True,
        use_regex: bool = False,
        case_sensitive: bool = False,
        limit: int = 50,
        show_hidden: bool = False,
    ) -> str:
        """Search for a pattern in files."""
        if not pattern:
            return "Usage: grep <pattern> [--regex] [--case] [--deep] [--limit N]"

        regex = None
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                regex = re.compile(pattern, flags)
            except re.error as exc:
                return f"Invalid regex: {exc}"
        needle = pattern if case_sensitive else pattern.lower()

        matches: list[str] = []
        files = self._iter_files(self.current_path, recursive=deep, show_hidden=show_hidden)
        for path in files:
            for line_index, line in self._iter_text_lines(path, limit_bytes=1_000_000):
                haystack = line if case_sensitive else line.lower()
                hit = regex.search(line) if regex else (needle in haystack)
                if hit:
                    try:
                        rel_path = path.relative_to(self.current_path)
                    except ValueError:
                        rel_path = path
                    matches.append(f"{rel_path}:{line_index}: {line.strip()}")
                    if len(matches) >= limit:
                        break
            if len(matches) >= limit:
                break

        if not matches:
            return "No matches found."
        return "\n".join(matches)

    def todos(self, deep: bool = True, limit: int = 50, show_hidden: bool = False) -> str:
        """Search for explicit TODO/FIXME/HACK markers."""
        pattern = re.compile(r"^\s*#.*\b(TODO|FIXME|HACK)\b")
        matches: list[str] = []
        files = self._iter_files(self.current_path, recursive=deep, show_hidden=show_hidden)
        for path in files:
            for line_index, line in self._iter_text_lines(path, limit_bytes=1_000_000):
                if pattern.search(line):
                    try:
                        rel_path = path.relative_to(self.current_path)
                    except ValueError:
                        rel_path = path
                    matches.append(f"{rel_path}:{line_index}: {line.strip()}")
                    if len(matches) >= limit:
                        break
            if len(matches) >= limit:
                break
        if not matches:
            return "No TODO/FIXME/HACK markers found."
        return "\n".join(matches)

    def tag_scan(self, limit: int = 50, show_hidden: bool = False) -> str:
        """Scan for OmniTag/MegaTag/RSHTS markers in current room."""
        patterns = ("OmniTag", "MegaTag", "RSHTS")
        matches: list[str] = []
        files = self._iter_files(self.current_path, recursive=False, show_hidden=show_hidden)
        for path in files:
            for line_index, line in self._iter_text_lines(path, limit_bytes=500_000):
                if any(token in line for token in patterns):
                    matches.append(f"{path.name}:{line_index}: {line.strip()}")
                    if len(matches) >= limit:
                        break
            if len(matches) >= limit:
                break
        if not matches:
            return "No OmniTag/MegaTag/RSHTS markers found in this room."
        return "\n".join(matches)

    def inventory(self, show_hidden: bool = False) -> str:
        """List runnable scripts and common source files in this room."""
        extensions = [".py", ".ps1", ".sh", ".bat", ".cmd", ".js", ".ts"]
        files = [
            p
            for p in self.current_path.iterdir()
            if p.is_file()
            and (show_hidden or not self._is_hidden(p))
            and p.suffix.lower() in extensions
        ]
        if not files:
            return "No runnable scripts found in this room."
        lines = ["Inventory:"]
        for path in sorted(files, key=lambda p: p.name.lower())[:50]:
            lines.append(f"  {path.name}")
        if len(files) > 50:
            lines.append(f"  ... and {len(files) - 50} more")
        return "\n".join(lines)

    def probe(self, item_name: str) -> str:
        """Show metadata and git info for a file."""
        if not item_name:
            return "Usage: probe <file>"
        target = self.current_path / item_name
        if not target.exists():
            return f"'{item_name}' not found"
        try:
            stat = target.stat()
        except OSError:
            return f"Unable to stat '{item_name}'"

        lines = [
            f"Path: {target}",
            f"Size: {self._format_size(stat.st_size)}",
            f"Modified: {datetime.fromtimestamp(stat.st_mtime).isoformat()}",
            f"Type: {target.suffix or 'no extension'}",
        ]

        if self.repo_root:
            try:
                rel_path = target.relative_to(self.repo_root)
            except ValueError:
                rel_path = target
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.repo_root),
                    "log",
                    "-1",
                    "--pretty=format:%h %ad %s",
                    "--date=short",
                    "--",
                    str(rel_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                lines.append(f"Git: {result.stdout.strip()}")
        return "\n".join(lines)

    def git_status(self) -> str:
        """Show git status for the current room."""
        if not self.repo_root:
            return "Git status unavailable (no repo root detected)."
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return "Git status unavailable."
        lines = result.stdout.splitlines()
        if not lines:
            return "Working tree clean."

        filtered: list[str] = []
        try:
            current_rel = self.current_path.relative_to(self.repo_root)
        except ValueError:
            current_rel = None
        for line in lines:
            status = line[:2]
            path = line[3:] if len(line) > 3 else ""
            if current_rel and not path.startswith(str(current_rel)):
                continue
            filtered.append(f"{status} {path}")

        if not filtered:
            return "No changes under current room."
        return "\n".join(filtered)

    def open_item(self, item_name: str, use_system: bool = False) -> str:
        """Open a file with the system handler."""
        if not item_name:
            return "Usage: open <file> [--system]"
        target = self.current_path / item_name
        if not target.exists():
            return f"'{item_name}' not found"
        if not use_system:
            return f"Use 'open --system {item_name}' to launch with system handler."
        try:
            if os.name == "nt":
                startfile = getattr(os, "startfile", None)
                if startfile is None:
                    return "System open not supported on this platform."
                startfile(target)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(target)], check=False)
            else:
                subprocess.run(["xdg-open", str(target)], check=False)
        except OSError as exc:
            return f"Open failed: {exc}"
        return f"Opened {target}"

    def stats_by_extension(self, deep: bool = True, show_hidden: bool = False) -> str:
        """Summarize file counts by extension."""
        files = self._iter_files(self.current_path, recursive=deep, show_hidden=show_hidden)
        counts: dict[str, int] = {}
        for path in files:
            ext = path.suffix.lower() or "<none>"
            counts[ext] = counts.get(ext, 0) + 1
        if not counts:
            return "No files found."
        top = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:20]
        lines = ["Extension counts:"]
        for ext, count in top:
            lines.append(f"  {ext}: {count}")
        return "\n".join(lines)

    def add_note(self, text: str) -> str:
        """Add a note for the current room."""
        if not text:
            return "Usage: note <text>"
        key = str(self.current_path)
        entry = f"{datetime.now(UTC).isoformat()} - {text}"
        self.notes.setdefault(key, []).append(entry)
        self._save_state()
        return f"Note saved for {self.current_path}"

    def list_notes(self, path_text: str | None = None) -> str:
        """List notes for a path (defaults to current)."""
        target = Path(path_text).resolve() if path_text else self.current_path
        notes = self.notes.get(str(target), [])
        if not notes:
            return f"No notes for {target}"
        lines = [f"Notes for {target}:"]
        lines.extend([f"  {entry}" for entry in notes[-20:]])
        return "\n".join(lines)

    def explain(self) -> str:
        """Show local README/docs hints for the current room."""
        candidates = [
            self.current_path / "README.md",
            self.current_path / "README.txt",
            self.current_path / "README",
        ]
        for candidate in candidates:
            if candidate.exists():
                preview = self._iter_text_lines(candidate, limit_bytes=100_000)[:12]
                lines = [f"Explain: {candidate.name}"]
                lines.extend([f"  {line}" for _, line in preview if line.strip()])
                return "\n".join(lines) if len(lines) > 1 else f"Explain: {candidate}"

        base = self.repo_root or self.root
        system_map = base / "docs" / "SYSTEM_MAP.md"
        if not system_map.exists():
            system_map = base / "SYSTEM_MAP.md"
        if system_map.exists():
            preview = self._iter_text_lines(system_map, limit_bytes=150_000)[:12]
            lines = [f"Explain: {system_map.name}"]
            lines.extend([f"  {line}" for _, line in preview if line.strip()])
            return "\n".join(lines) if len(lines) > 1 else f"Explain: {system_map}"

        docs_dir = base / "docs"
        if docs_dir.exists():
            docs = [
                p.name for p in sorted(docs_dir.iterdir()) if p.is_file() and not self._is_hidden(p)
            ][:10]
            if docs:
                return "Docs available: " + ", ".join(docs)

        parent = self.current_path.parent
        if parent != self.current_path and (parent / "README.md").exists():
            return f"Explain: see {parent / 'README.md'}"
        return "No local README or system map found for this room."

    def health(self) -> str:
        """Quick health indicators for the current repo."""
        base = self.repo_root or self.root
        checks = {
            "pyproject.toml": (base / "pyproject.toml").exists(),
            "requirements.txt": (base / "requirements.txt").exists(),
            "pytest.ini": (base / "pytest.ini").exists(),
            "tests/": (base / "tests").exists(),
            "docs/": (base / "docs").exists(),
            "package.json": (base / "package.json").exists(),
        }
        lines = ["Health (presence checks):"]
        for key, value in checks.items():
            lines.append(f"  {key}: {'OK' if value else 'MISSING'}")
        return "\n".join(lines)

    def _run_command(self, cmd: list[str], timeout: int = 60) -> str:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_root or self.current_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return f"Command failed: {exc}"
        output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        output_lines = output.strip().splitlines()
        if len(output_lines) > 60:
            output_lines = output_lines[-60:]
        return "\n".join(output_lines) if output_lines else "No output."

    def run_lint(self) -> str:
        """Run a quick lint command if available."""
        base = self.repo_root or self.root
        if (base / "ruff.toml").exists() or (base / "pyproject.toml").exists():
            return self._run_command([sys.executable, "-m", "ruff", "check", "."])
        if (base / ".pylintrc").exists():
            return self._run_command([sys.executable, "-m", "pylint", "."])
        return "No lint config detected for this repo."

    def run_tests(self) -> str:
        """Run a quick test command if available."""
        base = self.repo_root or self.root
        if (base / "pytest.ini").exists() or (base / "tests").exists():
            return self._run_command([sys.executable, "-m", "pytest", "-q"])
        if (base / "package.json").exists():
            return self._run_command(["npm", "test"], timeout=90)
        return "No test runner detected for this repo."

    def watch(self, interval: float = 1.0, iterations: int = 5, deep: bool = False) -> str:
        """Watch for file changes for a short window."""
        iterations = max(1, min(iterations, 30))
        interval = max(0.2, min(interval, 10.0))
        files = self._iter_files(self.current_path, recursive=deep, show_hidden=False)
        snapshot = {str(p): p.stat().st_mtime for p in files if p.exists()}
        changes: set[str] = set()
        for _ in range(iterations):
            time.sleep(interval)
            files = self._iter_files(self.current_path, recursive=deep, show_hidden=False)
            for path in files:
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    continue
                key = str(path)
                if key not in snapshot or snapshot[key] != mtime:
                    changes.add(key)
                    snapshot[key] = mtime
        if not changes:
            return "No file changes detected."
        lines = ["Changed files:"]
        lines.extend([f"  {Path(path).name}" for path in sorted(changes)[:20]])
        if len(changes) > 20:
            lines.append(f"  ... and {len(changes) - 20} more")
        return "\n".join(lines)

    def observability(self) -> str:
        """Show recent logs/metrics for context."""
        base = self.repo_root or self.root
        candidates = [
            base / "logs",
            base / "docs" / "Metrics",
            base / "state" / "reports",
        ]
        lines = ["Observability (recent files):"]
        for folder in candidates:
            if not folder.exists():
                continue
            files = sorted(
                [p for p in folder.rglob("*") if p.is_file()],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if not files:
                continue
            lines.append(f"  {folder}:")
            for item in files[: self.observability_granularity]:
                lines.append(f"    - {item.name}")
        if len(lines) == 1:
            return "No observability artifacts found."
        return "\n".join(lines)

    def lifecycle(self) -> str:
        """Summarize last lifecycle catalog."""
        base = self.repo_root or self.root
        path = base / "state" / "reports" / "lifecycle_catalog_latest.json"
        if not path.exists():
            return "No lifecycle catalog found."
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return "Lifecycle catalog unreadable."
        services = data.get("services", [])
        active = [svc for svc in services if svc.get("active")]
        lines = [f"Active services: {len(active)}"]
        for svc in active[:8]:
            lines.append(f"  - {svc.get('name')} ({svc.get('repo')})")
        terminal_state = data.get("intelligent_terminal_state", {})
        if terminal_state:
            lines.append(f"Terminal groups: {terminal_state.get('total_terminals', 0)}")
        return "\n".join(lines)

    def capability_lookup(self, query: str) -> str:
        """Search capability inventory for a query."""
        if not query:
            return "Usage: capability <keyword>"
        base = self.repo_root or self.root
        candidates = [
            base / "CAPABILITIES.md",
            base / "capability_inventory_output.txt",
            base / "docs" / "CAPABILITIES.md",
        ]
        results: list[str] = []
        needle = query.lower()
        for path in candidates:
            if not path.exists():
                continue
            for line_index, line in self._iter_text_lines(path, limit_bytes=500_000):
                if needle in line.lower():
                    results.append(f"{path.name}:{line_index}: {line.strip()}")
                    if len(results) >= 20:
                        break
            if len(results) >= 20:
                break
        if not results:
            return f"No capability matches for '{query}'."
        return "\n".join(results)

    def teleport(self, destination: str) -> str:
        """Switch root to another repo if found."""
        if not destination:
            return "Usage: teleport <nusyq|simulatedverse|hub>"
        key = destination.lower().strip()
        alias_map = {
            "hub": "nusyq_hub",
            "nusyq-hub": "nusyq_hub",
            "simulatedverse": "simulatedverse",
            "nusyq": "nusyq",
        }
        mapped = alias_map.get(key, key)
        target = self.repo_roots.get(mapped)
        if not target or not target.exists():
            return f"Teleport failed: repo '{destination}' not found."
        self.root = target.resolve()
        self.current_path = self.root
        self.visited_paths = set()
        self.recent_paths = []
        if self.notes_scope == "per_repo":
            self.bookmarks = {}
            self.notes = {}
            self.state_path = self._resolve_state_path()
            self._load_state()
        self.repo_root = self._detect_repo_root()
        self.repo_roots = self._find_repo_roots()
        self._remember_path(self.current_path)
        return self.display_room()

    def cross_search(self, pattern: str, limit: int = 50) -> str:
        """Search across known repo roots."""
        if not pattern:
            return "Usage: xsearch <pattern>"

        try:
            limit = min(int(limit), self.cross_repo_search_limit)
        except (TypeError, ValueError):
            limit = self.cross_repo_search_limit

        depth = None
        if isinstance(self.cross_repo_search_depth, str):
            depth = 3 if self.cross_repo_search_depth == "shallow" else None
        else:
            try:
                depth = int(self.cross_repo_search_depth)
            except (TypeError, ValueError):
                depth = None

        results: list[str] = []
        if self.use_ripgrep and shutil.which("rg"):
            for name, root in self.repo_roots.items():
                if not root.exists() or len(results) >= limit:
                    continue
                remaining = max(limit - len(results), 1)
                cmd = [
                    "rg",
                    "--no-heading",
                    "--line-number",
                    "--max-count",
                    str(remaining),
                ]
                if depth is not None:
                    cmd.extend(["--max-depth", str(depth)])
                for excluded in sorted(self.exclude_dirs):
                    cmd.extend(["--glob", f"!{excluded}/**"])
                cmd.extend([pattern, str(root)])

                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                except OSError:
                    continue

                for line in (result.stdout or "").splitlines():
                    parts = line.split(":", 2)
                    if len(parts) < 3:
                        continue
                    path_text, line_no, text = parts
                    try:
                        rel_path = Path(path_text).resolve().relative_to(root.resolve())
                    except ValueError:
                        rel_path = Path(path_text)
                    results.append(f"{name}:{rel_path}:{line_no}: {text}")
                    if len(results) >= limit:
                        break

            if results:
                return "\n".join(results)

        for name, root in self.repo_roots.items():
            if not root.exists() or len(results) >= limit:
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if self._is_excluded(path):
                    continue
                try:
                    rel = path.relative_to(root)
                except ValueError:
                    rel = path
                if depth is not None and len(rel.parts) > depth:
                    continue
                for line_index, line in self._iter_text_lines(path, limit_bytes=500_000):
                    if pattern.lower() in line.lower():
                        results.append(f"{name}:{rel}:{line_index}: {line.strip()}")
                        if len(results) >= limit:
                            break
                if len(results) >= limit:
                    break

        if not results:
            return "No matches found across repos."
        return "\n".join(results)

    def achievements(self) -> str:
        """Simple achievements based on exploration activity."""
        achievements = []
        visited = len(self.visited_paths)
        if visited >= 5:
            achievements.append("Explorer I")
        if visited >= 25:
            achievements.append("Explorer II")
        if visited >= 100:
            achievements.append("Explorer III")
        if self.notes:
            achievements.append("Archivist")
        if self.bookmarks:
            achievements.append("Cartographer")
        if not achievements:
            return "No achievements yet."
        return "Achievements: " + ", ".join(achievements)

    def readiness(self) -> str:
        """Heuristic readiness score for the current repo."""
        base = self.repo_root or self.root
        signals = {
            "README": (base / "README.md").exists(),
            "tests": (base / "tests").exists() or (base / "pytest.ini").exists(),
            "config": (base / "config").exists(),
            "tasks": (base / ".vscode" / "tasks.json").exists(),
            "docs": (base / "docs").exists(),
            "coverage": (base / "coverage.xml").exists(),
        }
        weights = {
            "tests": float(self.readiness_weights.get("tests", 0.4)),
            "docs": float(self.readiness_weights.get("docs", 0.3)),
            "config": float(self.readiness_weights.get("config", 0.2)),
            "coverage": float(self.readiness_weights.get("coverage", 0.1)),
        }
        total_weight = sum(weights.values()) or 1.0
        score = 0.0
        for key, weight in weights.items():
            if signals.get(key):
                score += weight
        percent = int((score / total_weight) * 100)

        present = [name for name, ok in signals.items() if ok]
        missing = [name for name in self.mandatory_readiness if not signals.get(name)]
        status = f"Readiness score: {percent}/100 ({', '.join(present)})"
        if missing:
            status += f" | Missing: {', '.join(missing)}"
        return status

    def related(self, item_name: str) -> str:
        """Find files with the same stem across the repo."""
        if not item_name:
            return "Usage: related <file>"
        stem = Path(item_name).stem.lower()
        base = self.repo_root or self.root
        matches = []
        for path in base.rglob("*"):
            if path.is_file() and path.stem.lower() == stem:
                try:
                    rel = path.relative_to(base)
                except ValueError:
                    rel = path
                matches.append(str(rel))
                if len(matches) >= 20:
                    break
        if not matches:
            return f"No related files for stem '{stem}'."
        return "\n".join(matches)

    def quest_note(self, text: str) -> str:
        """Append a note to the quest log."""
        if not text:
            return "Usage: quest <note>"
        base = self.repo_root or self.root
        quest_path = base / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        if not quest_path.exists():
            return "Quest log not found."
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "type": "wizard_note",
            "path": str(self.current_path),
            "note": text,
        }
        try:
            with quest_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")
        except OSError as exc:
            return f"Quest log write failed: {exc}"
        return "Quest log note appended."

    def handle_command(self, command: str) -> str:
        """Process user command.

        Args:
            command: User input string

        Returns:
            Command result
        """
        try:
            parts = shlex.split(command, posix=False)
        except ValueError as exc:
            return f"Invalid command: {exc}"
        if not parts:
            return self.display_room()

        action = parts[0].lower()
        args = parts[1:]
        canonical = {
            "move": "go",
            "cd": "go",
            "ls": "look",
            "l": "look",
            "examine": "inspect",
            "cat": "inspect",
            "find": "search",
            "status": "stats",
            "mark": "bookmark",
            "pin": "bookmark",
            "marks": "bookmarks",
            "pins": "bookmarks",
            "goto": "jump",
            "snap": "snapshot",
            "largest": "size",
            "rg": "grep",
            "todos": "TODO",
            "tag": "tags",
            "inv": "inventory",
            "info": "probe",
            "about": "explain",
            "tests": "test",
            "obs": "observability",
            "cap": "capability",
            "tp": "teleport",
            "xgrep": "xsearch",
            "achieve": "achievements",
            "ready": "readiness",
            "link": "related",
            "git": "diff",
            "?": "help",
            "h": "help",
            "assist": "ai",
            "analyze": "ai",
        }.get(action, action)

        text_arg = " ".join(args).strip()
        simple_handlers = {
            "bookmark": lambda: self.add_bookmark(text_arg),
            "bookmarks": self.list_bookmarks,
            "jump": lambda: self.jump_to_bookmark(text_arg),
            "recent": self.list_recent,
            "snapshot": self.snapshot,
            "trail": self.trail,
            "probe": lambda: self.probe(text_arg),
            "note": lambda: self.add_note(text_arg),
            "notes": lambda: self.list_notes(text_arg or None),
            "explain": self.explain,
            "health": self.health,
            "lint": self.run_lint,
            "test": self.run_tests,
            "observability": self.observability,
            "lifecycle": self.lifecycle,
            "capability": lambda: self.capability_lookup(text_arg),
            "teleport": lambda: self.teleport(text_arg),
            "achievements": self.achievements,
            "readiness": self.readiness,
            "related": lambda: self.related(text_arg),
            "quest": lambda: self.quest_note(text_arg),
            "diff": self.git_status,
            "help": self._help_text,
            "ai": lambda: self._ai_assist(text_arg),
        }
        if canonical in simple_handlers:
            return simple_handlers[canonical]()

        if canonical == "go":
            if not args:
                return self.display_room()
            return self.move(args[0]) + "\n" + self.display_room()

        if canonical == "look":
            flags, values, rest = self._parse_args(args)
            ext_filter = values.get("ext")
            if rest and not ext_filter:
                ext_filter = rest[0]
            return self.display_room(show_hidden="all" in flags, ext_filter=ext_filter)

        if canonical == "inspect":
            if not args:
                return "Usage: inspect <file>"
            return self.inspect(args[0])

        if canonical == "search":
            if not text_arg:
                return "Usage: search <pattern>"
            return self.search(text_arg)

        if canonical == "stats":
            flags, values, rest = self._parse_args(args)
            if "ext" in values or "ext" in rest:
                return self.stats_by_extension(deep="deep" in flags, show_hidden="all" in flags)
            return self.stats()

        if canonical == "tree":
            flags, values, rest = self._parse_args(args)
            depth = int(values["depth"]) if values.get("depth", "").isdigit() else 2
            if depth == 2 and rest and rest[0].isdigit():
                depth = int(rest[0])
            limit = int(values["limit"]) if values.get("limit", "").isdigit() else 200
            return self.tree(depth=depth, show_hidden="all" in flags, limit=limit)

        if canonical == "size":
            flags, values, rest = self._parse_args(args)
            limit = int(values["limit"]) if values.get("limit", "").isdigit() else 10
            if limit == 10 and rest and rest[0].isdigit():
                limit = int(rest[0])
            return self.size_report(deep="deep" in flags, limit=limit, show_hidden="all" in flags)

        if canonical == "grep":
            flags, values, rest = self._parse_args(args)
            limit = int(values["limit"]) if values.get("limit", "").isdigit() else 50
            return self.grep(
                " ".join(rest).strip(),
                deep="deep" in flags,
                use_regex="regex" in flags,
                case_sensitive="case" in flags,
                limit=limit,
                show_hidden="all" in flags,
            )

        if canonical == "TODO":
            flags, values, _ = self._parse_args(args)
            limit = int(values["limit"]) if values.get("limit", "").isdigit() else 50
            return self.todos(deep="deep" in flags, limit=limit, show_hidden="all" in flags)

        if canonical == "tags":
            flags, values, _ = self._parse_args(args)
            limit = int(values["limit"]) if values.get("limit", "").isdigit() else 50
            return self.tag_scan(limit=limit, show_hidden="all" in flags)

        if canonical == "inventory":
            flags, _, _ = self._parse_args(args)
            return self.inventory(show_hidden="all" in flags)

        if canonical == "watch":
            flags, _, rest = self._parse_args(args)
            interval = 1.0
            iterations = 5
            if rest:
                with contextlib.suppress(ValueError):
                    interval = float(rest[0])
                if len(rest) > 1:
                    with contextlib.suppress(ValueError):
                        iterations = int(rest[1])
            return self.watch(interval=interval, iterations=iterations, deep="deep" in flags)

        if canonical == "xsearch":
            _, values, rest = self._parse_args(args)
            limit = int(values["limit"]) if values.get("limit", "").isdigit() else 50
            return self.cross_search(" ".join(rest).strip(), limit=limit)

        if canonical == "open":
            flags, _, rest = self._parse_args(args)
            return self.open_item(" ".join(rest).strip(), use_system="system" in flags)

        return f"❓ Unknown command: '{action}'. Type 'help' for commands."

    def _help_text(self) -> str:
        """Get help text."""
        return """
🧙 Wizard Navigator Commands:
   go/move/cd <dir>          - Navigate to directory
   go ..                    - Go up one level
   go root                  - Return to root
   look/ls/l [--all] [--ext py] - Display current room
   inspect/cat <file>        - Examine a file
   search/find <pattern>     - Search for files (e.g., '*.py')
   stats/status [--ext]      - Show exploration statistics
   bookmark/mark/pin <name>  - Save current location
   bookmarks/marks/pins      - List bookmarks
   jump/goto <name>          - Jump to a bookmark
   recent                    - Show recent paths
   snapshot/snap             - Save room summary to state/reports
   trail                     - Save navigation trail report
   tree [depth] [--all]      - Show a shallow directory tree
   size [--deep] [--limit N] - List largest files
   grep <pattern> [--regex] [--case] [--deep] [--limit N]
   TODO [--deep] [--limit N] - Find TODO/FIXME/HACK
   tags [--limit N]          - Scan for OmniTag/MegaTag/RSHTS
   inventory/inv [--all]     - List runnable scripts in room
   probe/info <file>         - Show file metadata + git info
   note <text>               - Add a note for the current room
   notes [path]              - List notes for a path
   explain/about             - Show local README hints
   health                    - Quick repo health presence checks
   lint                       - Run a quick lint check
   test/tests                 - Run a quick test command
   watch [secs] [n] [--deep] - Watch files for changes
   observability/obs         - Show recent logs/metrics
   lifecycle                 - Summarize lifecycle catalog
   capability/cap <query>    - Search capability inventory
   teleport/tp <repo>        - Switch repo root (nusyq/hub/simulatedverse)
   xsearch <pattern>         - Search across known repos
   achievements/achieve      - Show exploration achievements
   readiness/ready           - Heuristic repo readiness score
   related/link <file>       - Find matching stems across repo
   quest <note>              - Append a note to quest log
   diff/git                  - Show git status for current room
   open <file> [--system]    - Open with system handler
   ai/assist <query>         - AI-assisted analysis (requires integration)
   help/?/h                  - Show this help
   quit/exit                 - Exit navigator
"""

    def _ai_assist(self, query: str) -> str:
        """AI-assisted exploration with Ollama/ChatDev integration.

        Args:
            query: User query for AI assistance

        Returns:
            AI response with code navigation guidance
        """
        # Get room context first (outside try block for fallback)
        room = self.get_current_room()

        try:
            # Import AI integrator (lazy import to avoid setup.py execution)
            import asyncio

            # Avoid importing from setup module that triggers setup.py
            from src.ai.ollama_chatdev_integrator import \
                EnhancedOllamaChatDevIntegrator

            # Create integrator instance
            integrator = EnhancedOllamaChatDevIntegrator()
            integrator.check_systems()

            # Prepare context-aware prompt
            context_prompt = f"""You are a repository navigation AI assistant helping explore code.

Current Location: {room["path"]}
Directory: {room["name"]}
Files: {len(room["items"])} files
Subdirectories: {len(room["exits"])} subdirectories

Recent discoveries: {len(self.discoveries)}
Visited paths: {len(self.visited_paths)}

User query: {query or "What should I explore here?"}

Provide helpful navigation guidance, code insights, or exploration suggestions.
Keep response concise (2-3 sentences)."""

            messages = [
                {
                    "role": "system",
                    "content": "You are a code navigation wizard assistant.",
                },
                {"role": "user", "content": context_prompt},
            ]

            # Get event loop for async call
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Call AI integrator
            result = loop.run_until_complete(
                integrator.enhanced_intelligent_chat(messages, task_type="analysis")
            )

            if result.get("status") == "success":
                response = result.get("response", "No response")
                model = result.get("model", "unknown")
                return f"""
🧙 AI Wizard Assistance ({model}):
{"=" * 60}
{response}
{"=" * 60}
📍 Location: {room["name"]}
🔍 Items: {len(room["items"])} | Exits: {len(room["exits"])}
"""
            else:
                # Fallback to simple analysis
                return self._simple_analysis(query, room)

        except Exception as e:
            logger.warning(f"AI assistance failed: {e}")
            return self._simple_analysis(query, room)

    def _simple_analysis(self, query: str, room: dict) -> str:
        """Simple analysis when AI unavailable."""
        del query
        suggestions: list[Any] = []
        # Analyze file types
        py_files = [f for f in room["items"] if f.endswith(".py")]
        md_files = [f for f in room["items"] if f.endswith(".md")]

        if py_files:
            suggestions.append(
                f"• Found {len(py_files)} Python files - try 'inspect {py_files[0]}'"
            )
        if md_files:
            suggestions.append(f"• Found {len(md_files)} documentation files - good for context")
        if room["exits"]:
            suggestions.append(f"• {len(room['exits'])} directories to explore")

        return f"""
📊 Quick Analysis (AI offline):
{"=" * 60}
Location: {room["name"]}

{chr(10).join(suggestions) if suggestions else "Use explore/search commands to investigate."}
{"=" * 60}
"""


# Backward compatibility aliases
RepositoryWizard = WizardNavigator


def main() -> None:
    """CLI entry point for interactive navigation."""
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    wizard = WizardNavigator(root)

    logger.info("🧙‍♂️ Wizard Navigator v2.0 - Consolidated Edition")
    logger.info(wizard.display_room())

    while True:
        try:
            cmd = input("🧙 > ").strip()
            if cmd.lower() in ("quit", "exit", "q"):
                logger.info("👋 Farewell, adventurer!")
                break

            result = wizard.handle_command(cmd)
            logger.info(result)

        except KeyboardInterrupt:
            logger.info("\n👋 Farewell, adventurer!")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
