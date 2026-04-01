"""Nogic Visualizer bridge for command routing and graph access."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import time
import uuid
from ast import (AsyncFunctionDef, ClassDef, FunctionDef, Import, ImportFrom,
                 parse, walk)
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path, PureWindowsPath
from typing import ClassVar
from urllib.parse import quote, unquote, urlparse

logger = logging.getLogger(__name__)


class SymbolKind(str, Enum):
    """Symbol kinds used by Nogic's SQLite index."""

    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    INTERFACE = "interface"
    TYPE = "type"
    ENUM = "enum"
    VARIABLE = "variable"

    @classmethod
    def normalize(cls, value: str | SymbolKind) -> str:
        if isinstance(value, SymbolKind):
            return value.value
        return str(value).strip().lower()


class RelationType(str, Enum):
    """High-level relationship buckets."""

    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    TYPE_USES = "type_usages"


@dataclass
class Symbol:
    """Represents a code symbol extracted by Nogic."""

    id: str
    file_id: str
    kind: str
    name: str
    line: int
    column: int
    visibility: str | None = None
    parent_id: str | None = None
    documentation: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class CodeFile:
    """Represents a file in the Nogic index."""

    id: str
    name: str
    path: str
    language: str
    file_type: str
    parent_id: str | None = None
    collapsed: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class SymbolRelation:
    """Represents a relation edge in the code graph."""

    from_symbol_id: str
    to_symbol_id: str
    relation_type: str
    metadata: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class NogicBridge:
    """Bridge to the Nogic extension and its workspace index database."""

    _LEGACY_DB_PATHS: ClassVar[list] = [
        Path.cwd() / ".nogic" / "nogic.db",
        Path.cwd() / ".nogic" / "db.sqlite",
        Path.home() / ".vscode" / "extensions" / "nogic.nogic-0.1.0" / "nogic.db",
        Path.home() / ".vscode" / "extensions" / "nogic.nogic-0.1.0" / ".nogic" / "db.sqlite",
    ]

    def __init__(
        self,
        workspace_root: Path | str | None = None,
        allow_vscode_commands: bool = False,
    ):
        """Initialize NogicBridge with workspace_root, allow_vscode_commands."""
        base = Path(workspace_root) if workspace_root is not None else Path.cwd()
        self.workspace_root = base.resolve()
        self.allow_vscode_commands = allow_vscode_commands
        self.db_path = self._find_db()
        self._conn: sqlite3.Connection | None = None
        logger.info(
            "Nogic Bridge initialized (workspace=%s, db=%s, allow_vscode_commands=%s)",
            self.workspace_root,
            self.db_path,
            self.allow_vscode_commands,
        )

    # ========== PATH/DISCOVERY ==========

    def _workspace_storage_roots(self) -> list[Path]:
        roots: list[Path] = []
        home = Path.home()
        userprofile = os.environ.get("USERPROFILE")

        roots.append(home / ".config" / "Code" / "User" / "workspaceStorage")
        roots.append(home / "AppData" / "Roaming" / "Code" / "User" / "workspaceStorage")
        if userprofile:
            up = Path(userprofile)
            roots.append(up / "AppData" / "Roaming" / "Code" / "User" / "workspaceStorage")
            win_match = re.match(r"^([A-Za-z]):[\\/](.*)$", userprofile)
            if win_match:
                drive = win_match.group(1).lower()
                rest = win_match.group(2).replace("\\", "/")
                roots.append(
                    Path(f"/mnt/{drive}/{rest}/AppData/Roaming/Code/User/workspaceStorage")
                )

        deduped: list[Path] = []
        seen: set[str] = set()
        for candidate in roots:
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(candidate)
        return deduped

    def _normalize_path(self, path: Path) -> str:
        return str(path).replace("\\", "/").rstrip("/").lower()

    def _normalize_text_path(self, raw: str) -> str:
        return str(raw).replace("\\", "/").rstrip("/").lower()

    def _uri_to_path(self, raw_uri: str) -> Path | None:
        uri = raw_uri.strip()
        if not uri:
            return None

        if uri.startswith("file://"):
            parsed = urlparse(uri)
            path_part = unquote(parsed.path)
            drive_match = re.match(r"^/([A-Za-z]):/(.*)$", path_part)
            if drive_match:
                drive = drive_match.group(1).lower()
                rest = drive_match.group(2)
                if os.name == "nt":
                    return Path(f"{drive.upper()}:/{rest}")
                return Path(f"/mnt/{drive}/{rest}")
            return Path(path_part)

        if uri.startswith("vscode-remote://wsl+"):
            parsed = urlparse(uri)
            # The remote URI path already carries Linux path content.
            if parsed.path:
                return Path(unquote(parsed.path))
        return None

    def _workspace_root_from_workspace_json(self, json_path: Path) -> Path | None:
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        folder_uri = payload.get("folder")
        workspace_uri = payload.get("workspace")

        if isinstance(folder_uri, str):
            return self._uri_to_path(folder_uri)

        if isinstance(workspace_uri, str):
            path = self._uri_to_path(workspace_uri)
            # If this is a *.code-workspace file, use its parent folder for matching.
            if path and path.suffix == ".code-workspace":
                return path.parent
            return path

        return None

    def _db_matches_workspace(self, db_path: Path) -> bool:
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            row = cur.execute("SELECT path FROM files WHERE path IS NOT NULL LIMIT 1").fetchone()
            conn.close()
        except sqlite3.Error:
            return False

        if not row or not row[0]:
            return False

        sample = str(row[0]).replace("\\", "/").lower()
        workspace_norm = self._normalize_path(self.workspace_root)

        if workspace_norm in sample:
            return True
        # Match by trailing folder name as a fallback.
        return self.workspace_root.name.lower() in sample

    def _find_db(self) -> Path | None:
        # First prefer project-local storage when present.
        local_db = self.workspace_root / ".nogic" / "nogic.db"
        if local_db.exists():
            logger.info("Found project-local Nogic DB: %s", local_db)
            return local_db

        # Then search VS Code workspaceStorage entries that match this workspace root.
        matched: list[Path] = []
        workspace_norm = self._normalize_path(self.workspace_root)
        for root in self._workspace_storage_roots():
            if not root.exists():
                continue
            for workspace_dir in root.glob("*/"):
                workspace_json = workspace_dir / "workspace.json"
                nogic_db = workspace_dir / "Nogic.nogic" / "nogic.db"
                if not workspace_json.exists() or not nogic_db.exists():
                    continue
                ws_root = self._workspace_root_from_workspace_json(workspace_json)
                if not ws_root:
                    continue
                ws_norm = self._normalize_path(ws_root)
                if (
                    ws_norm == workspace_norm
                    or workspace_norm.startswith(ws_norm)
                    or ws_norm.startswith(workspace_norm)
                ):
                    matched.append(nogic_db)

        if matched:
            best = max(matched, key=lambda p: p.stat().st_mtime)
            logger.info("Found workspaceStorage Nogic DB: %s", best)
            return best

        # Fallback: scan all workspaceStorage DBs and choose most recent one that looks related.
        candidates: list[Path] = []
        for root in self._workspace_storage_roots():
            if not root.exists():
                continue
            candidates.extend(root.glob("*/Nogic.nogic/nogic.db"))
        for candidate in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
            if self._db_matches_workspace(candidate):
                logger.info("Matched Nogic DB by file-path signature: %s", candidate)
                return candidate

        # Final legacy fallbacks.
        for path in self._LEGACY_DB_PATHS:
            if path.exists():
                logger.info("Found legacy Nogic DB: %s", path)
                return path

        logger.warning(
            "Nogic database not found for workspace %s. Open 'Nogic: Open Visualizer' and index first.",
            self.workspace_root,
        )
        return None

    # ========== CONNECTION ==========

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            if not self.db_path or not self.db_path.exists():
                raise RuntimeError(
                    "Nogic database not accessible. Ensure Nogic Visualizer has been opened and indexed."
                )
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    # ========== VS CODE COMMAND ROUTING ==========

    def _build_command_uri(self, command_id: str, args: list[object] | None = None) -> str:
        if args:
            payload = quote(json.dumps(args, separators=(",", ":")))
            return f"vscode://command/{command_id}?{payload}"
        return f"vscode://command/{command_id}"

    def _run_vscode_command(
        self,
        command_id: str,
        args: list[object] | None = None,
        timeout_seconds: int = 20,
    ) -> bool:
        if not self.allow_vscode_commands:
            logger.warning(
                "Blocked VS Code command '%s' (allow_vscode_commands=False). Use command URI manually if needed.",
                command_id,
            )
            return False

        uri = self._build_command_uri(command_id, args)
        candidates: list[list[str]] = []

        if os.name != "nt" and shutil.which("cmd.exe"):
            candidates.append(["cmd.exe", "/c", "code", "--open-url", uri])
        candidates.append(["code", "--open-url", uri])

        for cmd in candidates:
            try:
                result = subprocess.run(cmd, check=False, timeout=timeout_seconds)
                if result.returncode == 0:
                    logger.info("Triggered VS Code command %s via URI", command_id)
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        logger.error("Failed to trigger VS Code command: %s", command_id)
        return False

    def _to_vscode_file_uri(self, path: Path) -> str:
        resolved = path.resolve()
        text = str(resolved)
        mnt_match = re.match(r"^/mnt/([a-zA-Z])/(.*)$", text)
        if mnt_match:
            drive = mnt_match.group(1).upper()
            rest = mnt_match.group(2).replace("/", "\\")
            win_path = PureWindowsPath(f"{drive}:\\{rest}")
            return "file:///" + quote(str(win_path).replace("\\", "/"))
        return resolved.as_uri()

    def open_visualizer(self) -> bool:
        return self._run_vscode_command("nogic.openVisualizer")

    def add_to_board(self, file_or_path: str) -> bool:
        path = Path(file_or_path).resolve()
        if not path.exists():
            logger.error("Path does not exist: %s", path)
            return False
        return self._run_vscode_command("nogic.addToBoard", [self._to_vscode_file_uri(path)])

    def create_board(self, name: str) -> bool:
        # Current extension command opens a board flow and does not accept a name arg directly.
        logger.info("Triggering create board command (requested name=%s)", name)
        return self._run_vscode_command("nogic.createBoard")

    def start_watch(self) -> bool:
        return self._run_vscode_command("nogic.cliWatchToggle")

    def reindex_workspace(self) -> bool:
        return self._run_vscode_command("nogic.cliReindex")

    def show_cli_status(self) -> bool:
        return self._run_vscode_command("nogic.cliStatus")

    def run_onboarding(self) -> bool:
        return self._run_vscode_command("nogic.cliOnboard")

    def login(self) -> bool:
        return self._run_vscode_command("nogic.cliLogin")

    def get_command_uri(self, command_id: str, args: list[object] | None = None) -> str:
        """Return a command URI that can be run manually in current VS Code window."""
        return self._build_command_uri(command_id, args)

    # ========== GRAPH QUERIES ==========

    def _guess_language(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        mapping = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".json": "json",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".ps1": "powershell",
        }
        return mapping.get(suffix, "unknown")

    def _db_path_to_local_path(self, raw_path: str) -> Path:
        """Convert a DB file path to a local path readable by this agent runtime.

        Nogic stores absolute Windows paths in this workspace, so convert those
        to WSL mount paths when needed.
        """
        text = str(raw_path).strip()
        if not text:
            return self.workspace_root

        win_match = re.match(r"^([A-Za-z]):[\\/](.*)$", text)
        if win_match and os.name != "nt":
            drive = win_match.group(1).lower()
            rest = win_match.group(2).replace("\\", "/")
            return Path(f"/mnt/{drive}/{rest}")

        return Path(text)

    def _load_file_lookup(
        self,
    ) -> tuple[
        dict[str, Path],
        dict[str, str],
        dict[str, list[str]],
        list[dict[str, str]],
    ]:
        """Build reusable lookup maps for file-id/path/module resolution.

        Returns:
            file_id_to_local_path: map file_id -> local filesystem path
            normalized_path_to_file_id: normalized absolute path -> file_id
            python_module_to_file_ids: module name -> matching file_ids
            file_rows: raw file rows (id, path, type) as string dicts
        """
        conn = self._get_connection()
        rows = conn.execute("SELECT id, path, type FROM files").fetchall()

        file_id_to_local_path: dict[str, Path] = {}
        normalized_path_to_file_id: dict[str, str] = {}
        python_module_to_file_ids: dict[str, list[str]] = {}
        file_rows: list[dict[str, str]] = []

        for row in rows:
            file_id = str(row["id"])
            raw_path = str(row["path"])
            row_type = str(row["type"])
            file_rows.append({"id": file_id, "path": raw_path, "type": row_type})

            local_path = self._db_path_to_local_path(raw_path)
            file_id_to_local_path[file_id] = local_path
            normalized_path_to_file_id[self._normalize_path(local_path)] = file_id

            rel = file_id.replace("\\", "/")
            if rel.endswith(".py"):
                if rel.endswith("/__init__.py"):
                    module_name = rel[: -len("/__init__.py")].replace("/", ".")
                else:
                    module_name = rel[: -len(".py")].replace("/", ".")
                if module_name:
                    python_module_to_file_ids.setdefault(module_name, []).append(file_id)

        return (
            file_id_to_local_path,
            normalized_path_to_file_id,
            python_module_to_file_ids,
            file_rows,
        )

    def _extract_python_import_specs(self, source: str) -> list[str]:
        """Extract Python import specs using AST (safe fallback to regex)."""
        specs: list[str] = []

        try:
            tree = parse(source)
            for node in walk(tree):
                if isinstance(node, Import):
                    for alias in node.names:
                        if alias.name:
                            specs.append(alias.name)
                elif isinstance(node, ImportFrom):
                    base = "." * int(node.level or 0) + (node.module or "")
                    if base:
                        specs.append(base)
                    for alias in node.names:
                        name = alias.name
                        if name and name != "*" and (node.level or node.module):
                            dotted = (
                                "." * int(node.level or 0)
                                + (node.module + "." if node.module else "")
                                + name
                            )
                            specs.append(dotted)
        except SyntaxError:
            # Fallback: lightweight line-based extraction.
            for line in source.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                import_match = re.match(r"^\s*import\s+(.+)$", line)
                if import_match:
                    rhs = import_match.group(1).split("#", 1)[0]
                    for chunk in rhs.split(","):
                        token = chunk.strip().split(" as ", 1)[0].strip()
                        if token:
                            specs.append(token)
                    continue
                from_match = re.match(r"^\s*from\s+([.\w]+)\s+import\s+(.+)$", line)
                if from_match:
                    module_spec = from_match.group(1).strip()
                    if module_spec:
                        specs.append(module_spec)

        # Preserve order while deduplicating.
        deduped: list[str] = []
        seen: set[str] = set()
        for spec in specs:
            key = spec.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(key)
        return deduped

    def _extract_python_symbol_rows(
        self,
        *,
        file_id: str,
        source: str,
    ) -> list[dict[str, object]]:
        """Extract class/function/method symbols from Python source text."""
        rows: list[dict[str, object]] = []
        try:
            tree = parse(source)
        except SyntaxError:
            return rows

        for node in tree.body:
            if isinstance(node, ClassDef):
                class_name = node.name
                class_symbol_id = f"{file_id}::{class_name}"
                rows.append(
                    {
                        "id": class_symbol_id,
                        "name": class_name,
                        "kind": SymbolKind.CLASS.value,
                        "line_start": int(getattr(node, "lineno", 0) or 0),
                        "line_end": int(getattr(node, "end_lineno", 0) or 0),
                        "col": int(getattr(node, "col_offset", 0) or 0),
                        "visibility": "private" if class_name.startswith("_") else "public",
                        "parent_symbol_id": None,
                    }
                )

                for child in node.body:
                    if isinstance(child, (FunctionDef, AsyncFunctionDef)):
                        method_name = child.name
                        rows.append(
                            {
                                "id": f"{class_symbol_id}::{method_name}",
                                "name": method_name,
                                "kind": SymbolKind.METHOD.value,
                                "line_start": int(getattr(child, "lineno", 0) or 0),
                                "line_end": int(getattr(child, "end_lineno", 0) or 0),
                                "col": int(getattr(child, "col_offset", 0) or 0),
                                "visibility": (
                                    "private" if method_name.startswith("_") else "public"
                                ),
                                "parent_symbol_id": class_symbol_id,
                            }
                        )

            elif isinstance(node, (FunctionDef, AsyncFunctionDef)):
                fn_name = node.name
                rows.append(
                    {
                        "id": f"{file_id}::{fn_name}",
                        "name": fn_name,
                        "kind": SymbolKind.FUNCTION.value,
                        "line_start": int(getattr(node, "lineno", 0) or 0),
                        "line_end": int(getattr(node, "end_lineno", 0) or 0),
                        "col": int(getattr(node, "col_offset", 0) or 0),
                        "visibility": "private" if fn_name.startswith("_") else "public",
                        "parent_symbol_id": None,
                    }
                )

        return rows

    def _extract_js_import_specs(self, source: str) -> list[str]:
        patterns = [
            r"""import\s+[^'"]*?\s+from\s+['"]([^'"]+)['"]""",
            r"""import\s*['"]([^'"]+)['"]""",
            r"""require\(\s*['"]([^'"]+)['"]\s*\)""",
            r"""import\(\s*['"]([^'"]+)['"]\s*\)""",
        ]
        specs: list[str] = []
        for pattern in patterns:
            specs.extend(re.findall(pattern, source))

        deduped: list[str] = []
        seen: set[str] = set()
        for spec in specs:
            key = spec.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(key)
        return deduped

    def _resolve_python_spec_to_file_id(
        self,
        source_file_id: str,
        spec: str,
        module_to_file_ids: dict[str, list[str]],
    ) -> str | None:
        token = spec.strip()
        if not token:
            return None

        source_rel = source_file_id.replace("\\", "/")
        source_parts = source_rel.split("/")[:-1]

        # Build candidate module names in preference order.
        candidates: list[str] = []
        if token.startswith("."):
            level = len(token) - len(token.lstrip("."))
            remainder = token[level:]
            if level > 0:
                up = max(0, level - 1)
                if up <= len(source_parts):
                    prefix = source_parts[: len(source_parts) - up]
                    if remainder:
                        candidates.append(".".join(prefix + remainder.split(".")))
                    else:
                        candidates.append(".".join(prefix))
        else:
            candidates.append(token)

        # Also try progressively shorter prefixes, which helps with
        # `import package.module` where only package/__init__.py exists.
        expanded: list[str] = []
        for candidate in candidates:
            parts = [p for p in candidate.split(".") if p]
            for i in range(len(parts), 0, -1):
                expanded.append(".".join(parts[:i]))

        for module_name in expanded:
            file_ids = module_to_file_ids.get(module_name)
            if file_ids:
                return file_ids[0]
        return None

    def _resolve_js_spec_to_file_id(
        self,
        source_abs_path: Path,
        spec: str,
        normalized_path_to_file_id: dict[str, str],
    ) -> str | None:
        token = spec.strip()
        if not token:
            return None

        # Keep this conservative; unresolved aliases should be ignored.
        if not (token.startswith(".") or token.startswith("/")):
            return None

        base = (
            self.workspace_root / token.lstrip("/")
            if token.startswith("/")
            else source_abs_path.parent / token
        )

        ext_candidates = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".py"]
        candidates: list[Path] = []

        if base.suffix:
            candidates.append(base)
            # TypeScript projects often import .js while source is .ts/.tsx.
            if base.suffix == ".js":
                candidates.append(base.with_suffix(".ts"))
                candidates.append(base.with_suffix(".tsx"))
        else:
            candidates.append(base)
            for ext in ext_candidates:
                candidates.append(base.with_suffix(ext))
            for ext in ext_candidates:
                candidates.append(base / f"index{ext}")

        seen: set[str] = set()
        for candidate in candidates:
            key = self._normalize_path(candidate)
            if key in seen:
                continue
            seen.add(key)
            target = normalized_path_to_file_id.get(key)
            if target:
                return target
        return None

    def backfill_imports_from_workspace(
        self,
        *,
        clear_existing: bool = False,
    ) -> dict[str, int]:
        """Backfill imports table from source files indexed by Nogic.

        This is an agent-side fallback for workspaces where the extension's
        import extraction is sparse or stale.
        """
        try:
            (
                file_id_to_local_path,
                normalized_path_to_file_id,
                python_module_to_file_ids,
                file_rows,
            ) = self._load_file_lookup()
            conn = self._get_connection()

            if clear_existing:
                conn.execute("DELETE FROM imports")

            candidate_edges: set[tuple[str, str]] = set()
            scanned_files = 0
            parsed_files = 0

            for row in file_rows:
                if row.get("type") != "file":
                    continue
                source_file_id = row["id"]
                source_path = file_id_to_local_path.get(source_file_id)
                if not source_path or not source_path.exists():
                    continue

                suffix = source_path.suffix.lower()
                if suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
                    continue

                scanned_files += 1
                try:
                    content = source_path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue

                parsed_files += 1

                if suffix == ".py":
                    specs = self._extract_python_import_specs(content)
                    for spec in specs:
                        target_file_id = self._resolve_python_spec_to_file_id(
                            source_file_id, spec, python_module_to_file_ids
                        )
                        if target_file_id and target_file_id != source_file_id:
                            candidate_edges.add((source_file_id, target_file_id))
                else:
                    specs = self._extract_js_import_specs(content)
                    for spec in specs:
                        target_file_id = self._resolve_js_spec_to_file_id(
                            source_path, spec, normalized_path_to_file_id
                        )
                        if target_file_id and target_file_id != source_file_id:
                            candidate_edges.add((source_file_id, target_file_id))

            before = int(conn.execute("SELECT COUNT(*) FROM imports").fetchone()[0])
            conn.executemany(
                "INSERT OR IGNORE INTO imports(source_file_id, target_file_id) VALUES (?, ?)",
                sorted(candidate_edges),
            )
            conn.commit()
            after = int(conn.execute("SELECT COUNT(*) FROM imports").fetchone()[0])
            inserted = max(0, after - before)

            return {
                "scanned_files": scanned_files,
                "parsed_files": parsed_files,
                "candidate_edges": len(candidate_edges),
                "inserted_edges": inserted,
                "total_imports": after,
            }
        except Exception as exc:
            logger.error("Failed to backfill imports: %s", exc)
            return {
                "scanned_files": 0,
                "parsed_files": 0,
                "candidate_edges": 0,
                "inserted_edges": 0,
                "total_imports": 0,
            }

    def backfill_python_symbols(self) -> dict[str, int]:
        """Backfill Python symbols (classes/functions/methods) when Nogic has sparse coverage."""
        try:
            conn = self._get_connection()
            file_rows = conn.execute(
                "SELECT id, path, type FROM files WHERE type = 'file' AND path LIKE '%.py'"
            ).fetchall()
            existing_symbol_ids = {
                str(row["id"]) for row in conn.execute("SELECT id FROM symbols").fetchall()
            }
            files_with_symbols = {
                str(row["file_id"])
                for row in conn.execute(
                    """
                    SELECT DISTINCT s.file_id
                    FROM symbols s
                    JOIN files f ON f.id = s.file_id
                    WHERE f.path LIKE '%.py'
                    """
                ).fetchall()
            }

            scanned_files = 0
            parsed_files = 0
            inserted_symbols = 0

            for row in file_rows:
                file_id = str(row["id"])
                scanned_files += 1

                # Preserve extension output: only backfill files currently without symbols.
                if file_id in files_with_symbols:
                    continue

                local_path = self._db_path_to_local_path(str(row["path"]))
                if not local_path.exists():
                    continue

                try:
                    source = local_path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue

                parsed_files += 1
                extracted = self._extract_python_symbol_rows(file_id=file_id, source=source)
                if not extracted:
                    continue

                for symbol in extracted:
                    symbol_id = str(symbol["id"])
                    if symbol_id in existing_symbol_ids:
                        continue
                    conn.execute(
                        """
                        INSERT INTO symbols(
                            id, name, file_id, kind, parent_symbol_id, exported,
                            line_start, line_end, col, is_abstract, is_async, is_static,
                            is_generator, visibility, return_type, extends_name, definition, extra_data
                        )
                        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, NULL, NULL, NULL, NULL, ?, NULL, NULL, NULL, NULL)
                        """,
                        (
                            symbol_id,
                            str(symbol["name"]),
                            file_id,
                            str(symbol["kind"]),
                            symbol.get("parent_symbol_id"),
                            int(symbol.get("line_start", 0)),
                            int(symbol.get("line_end", 0)),
                            int(symbol.get("col", 0)),
                            str(symbol.get("visibility", "public")),
                        ),
                    )
                    existing_symbol_ids.add(symbol_id)
                    inserted_symbols += 1

            conn.commit()
            total_python_symbols = int(
                conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM symbols s
                    JOIN files f ON f.id = s.file_id
                    WHERE f.path LIKE '%.py'
                    """
                ).fetchone()[0]
            )

            return {
                "scanned_files": scanned_files,
                "parsed_files": parsed_files,
                "inserted_symbols": inserted_symbols,
                "total_python_symbols": total_python_symbols,
            }
        except Exception as exc:
            logger.error("Failed to backfill Python symbols: %s", exc)
            return {
                "scanned_files": 0,
                "parsed_files": 0,
                "inserted_symbols": 0,
                "total_python_symbols": 0,
            }

    def seed_board_from_workspace(
        self,
        *,
        board_id: str | None = None,
        max_nodes: int = 24,
    ) -> dict[str, object]:
        """Seed a board with high-signal files so the visualizer is immediately useful."""
        try:
            conn = self._get_connection()
            now_ms = int(time.time() * 1000)

            # Reuse most recent board by default, create one if missing.
            if board_id is None:
                row = conn.execute(
                    "SELECT id FROM boards ORDER BY last_modified DESC LIMIT 1"
                ).fetchone()
                board_id = str(row["id"]) if row else None

            created_board = False
            if board_id is None:
                board_id = f"board_{now_ms}_{uuid.uuid4().hex[:8]}"
                conn.execute(
                    """
                    INSERT INTO boards(id, name, created_at, last_modified, display_mode, layout_direction, dynamic_direction)
                    VALUES (?, ?, ?, ?, 'unified', 'RL', 1)
                    """,
                    (board_id, "Codex Seed Board", now_ms, now_ms),
                )
                created_board = True

            existing_paths = {
                str(row["path"])
                for row in conn.execute(
                    "SELECT path FROM board_nodes WHERE board_id = ?", (board_id,)
                ).fetchall()
            }

            # Seed from deterministic core files/folders + complexity hotspots.
            preferred_tokens = [
                "src",
                "scripts",
                "docs",
                "docs/ROSETTA_STONE.md",
                "docs/AGENT_TUTORIAL.md",
                "src/integrations/nogic_bridge.py",
                "src/integrations/nogic_agent_diagnostics.py",
                ".vscode/tasks.json",
                ".vscode/settings.json",
            ]

            candidate_ids: list[str] = []
            for token in preferred_tokens:
                norm = token.replace("\\", "/")
                rows = conn.execute(
                    """
                    SELECT id
                    FROM files
                    WHERE id = ?
                       OR id = ?
                       OR lower(replace(path, '\\', '/')) LIKE ?
                    LIMIT 5
                    """,
                    (norm, norm.lstrip("./"), f"%/{norm.lower()}"),
                ).fetchall()
                for row in rows:
                    candidate_ids.append(str(row["id"]))

            for hotspot in self.get_complexity_hotspots(threshold=5)[:64]:
                file_id = str(hotspot.get("file_id", "")).strip()
                if file_id:
                    candidate_ids.append(file_id)

            deduped_ids: list[str] = []
            seen_ids: set[str] = set()
            for file_id in candidate_ids:
                if file_id in seen_ids:
                    continue
                seen_ids.add(file_id)
                deduped_ids.append(file_id)
                if len(deduped_ids) >= max_nodes:
                    break

            inserted = 0
            node_rows: list[dict[str, object]] = []
            for idx, file_id in enumerate(deduped_ids):
                if file_id in existing_paths:
                    continue
                file_row = conn.execute(
                    "SELECT id, name, path, type FROM files WHERE id = ? LIMIT 1", (file_id,)
                ).fetchone()
                if not file_row:
                    continue

                node_id = f"node_{now_ms}_{idx}_{uuid.uuid4().hex[:6]}"
                display_name = str(file_row["name"]) or Path(str(file_row["path"])).name
                node_type = str(file_row["type"]) if file_row["type"] else "file"

                conn.execute(
                    """
                    INSERT INTO board_nodes(
                        id, board_id, type, path, symbol_id, name, added_at, position_x, position_y
                    ) VALUES (?, ?, ?, ?, NULL, ?, ?, NULL, NULL)
                    """,
                    (node_id, board_id, node_type, file_id, display_name, now_ms),
                )
                inserted += 1
                node_rows.append(
                    {
                        "id": node_id,
                        "path": file_id,
                        "type": node_type,
                        "name": display_name,
                    }
                )

            conn.execute(
                "UPDATE boards SET last_modified = ? WHERE id = ?",
                (int(time.time() * 1000), board_id),
            )
            conn.commit()

            total_nodes = int(
                conn.execute(
                    "SELECT COUNT(*) FROM board_nodes WHERE board_id = ?", (board_id,)
                ).fetchone()[0]
            )
            return {
                "board_id": board_id,
                "created_board": created_board,
                "inserted_nodes": inserted,
                "total_nodes": total_nodes,
                "sample_nodes": node_rows[:10],
            }
        except Exception as exc:
            logger.error("Failed to seed board nodes: %s", exc)
            return {
                "board_id": board_id,
                "created_board": False,
                "inserted_nodes": 0,
                "total_nodes": 0,
                "sample_nodes": [],
            }

    def seed_board_from_paths(
        self,
        *,
        board_name: str,
        paths: list[str],
        max_nodes: int = 120,
        create_if_missing: bool = True,
    ) -> dict[str, object]:
        """Seed a board from a provided list of workspace-relative paths.

        Args:
            board_name: Name of the Nogic board to update.
            paths: Workspace-relative file paths to add.
            max_nodes: Maximum number of nodes to add.
            create_if_missing: Create the board if it does not exist.

        Returns:
            Summary of inserted nodes and board metadata.
        """
        try:
            conn = self._get_connection()
            now_ms = int(time.time() * 1000)

            row = conn.execute(
                "SELECT id FROM boards WHERE name = ? LIMIT 1",
                (board_name,),
            ).fetchone()
            board_id = str(row["id"]) if row else None

            created_board = False
            if board_id is None and create_if_missing:
                board_id = f"board_{now_ms}_{uuid.uuid4().hex[:8]}"
                conn.execute(
                    """
                    INSERT INTO boards(
                        id, name, created_at, last_modified,
                        display_mode, layout_direction, dynamic_direction
                    ) VALUES (?, ?, ?, ?, 'unified', 'RL', 1)
                    """,
                    (board_id, board_name, now_ms, now_ms),
                )
                created_board = True

            if board_id is None:
                return {
                    "board_id": None,
                    "created_board": False,
                    "inserted_nodes": 0,
                    "total_nodes": 0,
                    "sample_nodes": [],
                }

            existing_paths = {
                str(row["path"])
                for row in conn.execute(
                    "SELECT path FROM board_nodes WHERE board_id = ?",
                    (board_id,),
                ).fetchall()
            }

            _, normalized_path_to_file_id, _, _ = self._load_file_lookup()
            inserted = 0
            node_rows: list[dict[str, object]] = []

            for idx, raw_path in enumerate(paths[:max_nodes]):
                clean_path = str(raw_path).replace("\\", "/").lstrip("./")
                abs_path = (self.workspace_root / clean_path).resolve()
                key = self._normalize_path(abs_path)
                file_id = normalized_path_to_file_id.get(key)
                if not file_id or file_id in existing_paths:
                    continue

                node_id = f"node_{now_ms}_{idx}_{uuid.uuid4().hex[:6]}"
                display_name = Path(clean_path).name
                conn.execute(
                    """
                    INSERT INTO board_nodes(
                        id, board_id, type, path, symbol_id, name, added_at, position_x, position_y
                    ) VALUES (?, ?, 'file', ?, NULL, ?, ?, NULL, NULL)
                    """,
                    (node_id, board_id, file_id, display_name, now_ms),
                )
                inserted += 1
                node_rows.append(
                    {
                        "id": node_id,
                        "path": file_id,
                        "type": "file",
                        "name": display_name,
                    }
                )

            conn.execute(
                "UPDATE boards SET last_modified = ? WHERE id = ?",
                (int(time.time() * 1000), board_id),
            )
            conn.commit()

            total_nodes = int(
                conn.execute(
                    "SELECT COUNT(*) FROM board_nodes WHERE board_id = ?",
                    (board_id,),
                ).fetchone()[0]
            )
            return {
                "board_id": board_id,
                "created_board": created_board,
                "inserted_nodes": inserted,
                "total_nodes": total_nodes,
                "sample_nodes": node_rows[:10],
            }
        except Exception as exc:
            logger.error("Failed to seed board from paths: %s", exc)
            return {
                "board_id": None,
                "created_board": False,
                "inserted_nodes": 0,
                "total_nodes": 0,
                "sample_nodes": [],
            }

    def bootstrap_nogic_configs(
        self,
        *,
        create_user_config_template: bool = True,
        force: bool = False,
    ) -> dict[str, object]:
        """Write safe baseline Nogic config files for agent workflows.

        This does NOT attempt to fake cloud login; it creates templates and
        workspace-local defaults so onboarding can complete predictably.
        """
        workspace_dir = self.workspace_root / ".nogic"
        workspace_cfg = workspace_dir / "config.json"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        workspace_payload: dict[str, object] = {}
        if workspace_cfg.exists() and not force:
            try:
                workspace_payload = json.loads(workspace_cfg.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                workspace_payload = {}

        workspace_payload.setdefault("project_name", self.workspace_root.name)
        workspace_payload.setdefault("project_id", "")
        workspace_payload.setdefault("workspace_root", str(self.workspace_root))
        workspace_payload.setdefault("agent_profile", "codex")
        workspace_payload.setdefault(
            "index",
            {
                "languages": ["python", "typescript", "javascript"],
                "include": ["src/**", "scripts/**", "tests/**", "web/**", "docs/**"],
                "exclude": [
                    ".git/**",
                    ".venv/**",
                    "node_modules/**",
                    "dist/**",
                    "build/**",
                    "**/__pycache__/**",
                    "**/*.min.js",
                ],
            },
        )

        workspace_cfg.write_text(
            json.dumps(workspace_payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

        user_config_candidates: list[Path] = [Path.home() / ".nogic" / "config.json"]
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            user_config_candidates.append(Path(userprofile) / ".nogic" / "config.json")
            win_match = re.match(r"^([A-Za-z]):[\\/](.*)$", userprofile)
            if win_match:
                drive = win_match.group(1).lower()
                rest = win_match.group(2).replace("\\", "/")
                user_config_candidates.append(
                    Path(f"/mnt/{drive}/{rest}") / ".nogic" / "config.json"
                )

        deduped_candidates: list[Path] = []
        seen_candidates: set[str] = set()
        for candidate in user_config_candidates:
            key = self._normalize_text_path(str(candidate))
            if key in seen_candidates:
                continue
            seen_candidates.add(key)
            deduped_candidates.append(candidate)

        user_written_paths: list[str] = []
        if create_user_config_template:
            for user_cfg_path in deduped_candidates:
                user_cfg_path.parent.mkdir(parents=True, exist_ok=True)
                if force or not user_cfg_path.exists():
                    user_payload = {
                        "api_key": "",
                        "access_token": "",
                        "refresh_token": "",
                        "note": "Run 'Nogic: Login' in VS Code to populate credentials.",
                    }
                    user_cfg_path.write_text(
                        json.dumps(user_payload, indent=2, ensure_ascii=True) + "\n",
                        encoding="utf-8",
                    )
                    user_written_paths.append(str(user_cfg_path))

        return {
            "workspace_config": str(workspace_cfg),
            "workspace_written": True,
            "user_config_candidates": [str(p) for p in deduped_candidates],
            "user_written_paths": user_written_paths,
        }

    def get_language_coverage(self) -> dict[str, object]:
        """Return indexed file/symbol counts by language for agent planning."""
        try:
            conn = self._get_connection()
            file_rows = conn.execute("SELECT id, path, type FROM files").fetchall()
            files_by_language: dict[str, int] = {}
            ids_by_language: dict[str, set[str]] = {}
            for row in file_rows:
                if str(row["type"]) != "file":
                    continue
                file_id = str(row["id"])
                lang = self._guess_language(str(row["path"]))
                files_by_language[lang] = files_by_language.get(lang, 0) + 1
                ids_by_language.setdefault(lang, set()).add(file_id)

            symbol_rows = conn.execute("SELECT file_id FROM symbols").fetchall()
            symbols_by_language: dict[str, int] = {}
            for row in symbol_rows:
                file_id = str(row["file_id"])
                matched_lang = None
                for language, file_ids in ids_by_language.items():
                    if file_id in file_ids:
                        matched_lang = language
                        break
                if matched_lang is None:
                    matched_lang = "unknown"
                symbols_by_language[matched_lang] = symbols_by_language.get(matched_lang, 0) + 1

            return {
                "files_by_language": files_by_language,
                "symbols_by_language": symbols_by_language,
            }
        except Exception as exc:
            logger.error("Failed to compute language coverage: %s", exc)
            return {"files_by_language": {}, "symbols_by_language": {}}

    def get_files(self, language: str | None = None) -> list[CodeFile]:
        try:
            conn = self._get_connection()
            rows = conn.execute(
                "SELECT id, name, path, parent_id, type, collapsed FROM files"
            ).fetchall()
            files = [
                CodeFile(
                    id=str(row["id"]),
                    name=str(row["name"]),
                    path=str(row["path"]),
                    language=self._guess_language(str(row["path"])),
                    file_type=str(row["type"]),
                    parent_id=str(row["parent_id"]) if row["parent_id"] is not None else None,
                    collapsed=bool(row["collapsed"]),
                )
                for row in rows
            ]
            if language:
                wanted = language.strip().lower()
                files = [f for f in files if f.language == wanted]
            return files
        except Exception as exc:
            logger.error("Failed to query files: %s", exc)
            return []

    def query_symbols(
        self,
        kind: SymbolKind | str | None = None,
        name_pattern: str | None = None,
        file_path: str | None = None,
    ) -> list[Symbol]:
        try:
            conn = self._get_connection()
            query = """
                SELECT
                    id,
                    file_id,
                    kind,
                    name,
                    line_start,
                    col,
                    visibility,
                    parent_symbol_id,
                    definition
                FROM symbols
                WHERE 1=1
            """
            params: list[object] = []

            if kind:
                query += " AND lower(kind) = ?"
                params.append(SymbolKind.normalize(kind))

            if name_pattern:
                query += " AND name LIKE ?"
                params.append(f"%{name_pattern}%")

            if file_path:
                query += (
                    " AND (file_id LIKE ? OR file_id IN (SELECT id FROM files WHERE path LIKE ?))"
                )
                token = f"%{file_path}%"
                params.extend([token, token])

            rows = conn.execute(query, params).fetchall()
            return [
                Symbol(
                    id=str(row["id"]),
                    file_id=str(row["file_id"]),
                    kind=str(row["kind"]),
                    name=str(row["name"]),
                    line=int(row["line_start"] or 0),
                    column=int(row["col"] or 0),
                    visibility=str(row["visibility"]) if row["visibility"] is not None else None,
                    parent_id=(
                        str(row["parent_symbol_id"])
                        if row["parent_symbol_id"] is not None
                        else None
                    ),
                    documentation=str(row["definition"]) if row["definition"] is not None else None,
                )
                for row in rows
            ]
        except Exception as exc:
            logger.error("Failed to query symbols: %s", exc)
            return []

    def get_imports(self, file_path: str | None = None) -> list[dict[str, object]]:
        try:
            conn = self._get_connection()
            query = """
                SELECT
                    i.id,
                    i.source_file_id,
                    i.target_file_id,
                    sf.path AS source_file,
                    tf.path AS target_path
                FROM imports i
                LEFT JOIN files sf ON sf.id = i.source_file_id
                LEFT JOIN files tf ON tf.id = i.target_file_id
                WHERE 1=1
            """
            params: list[object] = []
            if file_path:
                query += " AND (sf.path LIKE ? OR i.source_file_id LIKE ?)"
                token = f"%{file_path}%"
                params.extend([token, token])
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to query imports: %s", exc)
            return []

    def get_calls(self, from_symbol: str | None = None) -> list[dict[str, object]]:
        try:
            conn = self._get_connection()
            query = """
                SELECT
                    c.id,
                    c.caller_id,
                    c.callee_id,
                    c.callee_name,
                    c.call_type,
                    c.line,
                    c.col,
                    caller.name AS caller_name,
                    caller.name AS from_name,
                    caller.file_id AS caller_file_id,
                    callee.name AS callee_symbol_name,
                    COALESCE(callee.name, c.callee_name) AS to_name,
                    callee.file_id AS callee_file_id
                FROM calls c
                LEFT JOIN symbols caller ON caller.id = c.caller_id
                LEFT JOIN symbols callee ON callee.id = c.callee_id
                WHERE 1=1
            """
            params: list[object] = []
            if from_symbol:
                query += " AND caller.name LIKE ?"
                params.append(f"%{from_symbol}%")
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to query calls: %s", exc)
            return []

    def get_file_call_dependencies(self, file_path: str | None = None) -> list[dict[str, object]]:
        """Return cross-file dependencies inferred from call graph edges.

        This is a useful fallback when Nogic import extraction is sparse.
        """
        try:
            conn = self._get_connection()
            query = """
                SELECT
                    c.id,
                    caller.file_id AS source_file_id,
                    COALESCE(callee.file_id, '') AS target_file_id,
                    caller.name AS source_symbol,
                    COALESCE(callee.name, c.callee_name) AS target_symbol,
                    c.call_type,
                    c.line,
                    c.col
                FROM calls c
                LEFT JOIN symbols caller ON caller.id = c.caller_id
                LEFT JOIN symbols callee ON callee.id = c.callee_id
                WHERE caller.file_id IS NOT NULL
                  AND COALESCE(callee.file_id, '') != ''
                  AND caller.file_id != callee.file_id
            """
            params: list[object] = []
            if file_path:
                query += " AND (caller.file_id LIKE ? OR callee.file_id LIKE ?)"
                token = f"%{file_path}%"
                params.extend([token, token])
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to query file call dependencies: %s", exc)
            return []

    def get_inheritance_chain(self, class_name: str) -> list[dict[str, object]]:
        try:
            conn = self._get_connection()
            query = """
                SELECT
                    i.id,
                    i.child_id,
                    i.parent_name,
                    i.type,
                    child.name AS child_name,
                    child.file_id AS child_file_id
                FROM inheritance i
                LEFT JOIN symbols child ON child.id = i.child_id
                WHERE (child.name LIKE ? OR i.parent_name LIKE ?)
            """
            token = f"%{class_name}%"
            rows = conn.execute(query, [token, token]).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to query inheritance: %s", exc)
            return []

    # ========== METRICS ==========

    def get_statistics(self) -> dict[str, object]:
        try:
            conn = self._get_connection()
            stats: dict[str, object] = {}

            schema_version = conn.execute(
                "SELECT value FROM schema_meta WHERE key = 'version'"
            ).fetchone()
            stats["schema_version"] = schema_version[0] if schema_version else "unknown"

            stats["symbols_by_kind"] = {
                row["kind"]: row["count"]
                for row in conn.execute(
                    "SELECT kind, COUNT(*) AS count FROM symbols GROUP BY kind"
                ).fetchall()
            }
            stats["total_symbols"] = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
            stats["total_files"] = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            stats["total_imports"] = conn.execute("SELECT COUNT(*) FROM imports").fetchone()[0]
            stats["total_calls"] = conn.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
            stats["total_inheritance"] = conn.execute(
                "SELECT COUNT(*) FROM inheritance"
            ).fetchone()[0]
            stats["total_type_usages"] = conn.execute(
                "SELECT COUNT(*) FROM type_usages"
            ).fetchone()[0]
            stats["total_boards"] = conn.execute("SELECT COUNT(*) FROM boards").fetchone()[0]

            return stats
        except Exception as exc:
            logger.error("Failed to get statistics: %s", exc)
            return {}

    def get_complexity_hotspots(self, threshold: int = 10) -> list[dict[str, object]]:
        try:
            conn = self._get_connection()
            query = """
                SELECT
                    s.id,
                    s.name,
                    s.file_id,
                    s.kind,
                    s.line_start,
                    COUNT(c.id) AS call_count
                FROM symbols s
                LEFT JOIN calls c ON c.caller_id = s.id
                WHERE lower(s.kind) IN ('function', 'method')
                GROUP BY s.id, s.name, s.file_id, s.kind, s.line_start
                HAVING call_count >= ?
                ORDER BY call_count DESC
            """
            rows = conn.execute(query, [threshold]).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to find complexity hotspots: %s", exc)
            return []

    def get_board_summary(self) -> list[dict[str, object]]:
        """Return board-level stats including node counts."""
        try:
            conn = self._get_connection()
            query = """
                SELECT
                    b.id,
                    b.name,
                    b.display_mode,
                    b.last_modified,
                    COUNT(n.id) AS node_count
                FROM boards b
                LEFT JOIN board_nodes n ON n.board_id = b.id
                GROUP BY b.id, b.name, b.display_mode, b.last_modified
                ORDER BY b.last_modified DESC
            """
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.error("Failed to get board summary: %s", exc)
            return []

    # ========== LIFECYCLE ==========

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Nogic connection closed")

    def __enter__(self) -> NogicBridge:
        """Enter context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context manager."""
        self.close()


def export_graph_to_json(bridge: NogicBridge | None = None) -> dict[str, object]:
    """Export current Nogic graph slices to JSON-friendly dict."""
    owned = bridge is None
    bridge = bridge or NogicBridge()
    try:
        return {
            "files": [f.to_dict() for f in bridge.get_files()],
            "symbols": [s.to_dict() for s in bridge.query_symbols()],
            "imports": bridge.get_imports(),
            "calls": bridge.get_calls(),
            "statistics": bridge.get_statistics(),
        }
    finally:
        if owned:
            bridge.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with NogicBridge() as bridge:
        logger.info("\nNogic Graph Statistics:")
        for key, value in bridge.get_statistics().items():
            logger.info(f"  {key}: {value}")

        logger.info("\nSample symbols:")
        for sym in bridge.query_symbols()[:5]:
            logger.info(f"  - {sym.name} ({sym.kind}) at {sym.line}:{sym.column}")

        logger.info("\nComplexity hotspots:")
        for hotspot in bridge.get_complexity_hotspots(threshold=5)[:5]:
            logger.info(f"  - {hotspot['name']}: {hotspot['call_count']} calls")
