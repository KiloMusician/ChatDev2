"""
agents/serena/drift.py — DriftDetector: Serena's guardian of coherence.

Drift Detection Engine  (Mladenc Correction ⟁ VIII)
====================================================
Continuously answers: "What is drifting away from intended design?"

Detected drift classes
──────────────────────
1. DOC_DEBT        — public functions/classes with no docstring
2. ARCH_BOUNDARY   — imports that cross architectural layer boundaries
3. ROLE_DRIFT      — agent personality YAMLs missing required fields
4. ORPHAN_CHUNK    — Memory Palace chunks whose source files no longer exist
5. STALE_INDEX     — files on disk not yet indexed by the walker
6. PROTOCOL_DRIFT  — OmniTag patterns that are malformed or unresolved

Every DriftSignal carries:
  category, severity (info / warn / critical), path, message, auto_fix (bool)

Usage
─────
  from agents.serena.drift import DriftDetector
  detector = DriftDetector(repo_root, memory_palace)
  signals  = detector.detect_all()
"""

from __future__ import annotations

import ast
import json
import re
import sqlite3
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


# ────────────────────────────────────────────────────────────────────────────
# DriftSignal
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class DriftSignal:
    category:  str
    severity:  str          # info | warn | critical
    path:      str
    message:   str
    auto_fix:  bool = False
    tick:      float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        icon = {"info": "◦", "warn": "⚠", "critical": "✕"}.get(self.severity, "?")
        return f"[{icon} {self.category}] {self.path}: {self.message}"


# ────────────────────────────────────────────────────────────────────────────
# Architectural layer definitions
# ────────────────────────────────────────────────────────────────────────────

# Layers: game_engine must not import from cli / agents must not import app
ARCH_LAYERS: dict[str, List[str]] = {
    "app/game_engine": [
        "cli",                    # game engine ≠ CLI concerns
        "app/backend/scheduler",  # game engine ≠ scheduler
    ],
    "cli": [
        "app/game_engine",        # CLI should call the API, not import directly
    ],
    "agents": [
        "app/backend",            # agents ≠ web layer
    ],
}

# Required fields that every personality YAML must have
REQUIRED_YAML_FIELDS = [
    "id", "name", "role", "faction", "codename",
    "traits", "system_prompt",
]

# OmniTag pattern — e.g. [Msg⛛{uuid}], [Ctx⛛{tag}], [Ref⛛{name}]
OMNI_TAG_RE = re.compile(r"\[(\w+)⛛\{([^}]+)\}\]")


# ────────────────────────────────────────────────────────────────────────────
# DriftDetector
# ────────────────────────────────────────────────────────────────────────────

class DriftDetector:
    """
    Serena's Drift Detection Engine.

    All detection methods are zero-token (pure static analysis / DB queries).
    Each returns a list of DriftSignal objects.  detect_all() combines them.
    """

    def __init__(self, repo_root: Path, db_path: Optional[Path] = None):
        self.repo_root = Path(repo_root)
        self.db_path   = db_path
        self._signals: List[DriftSignal] = []

    # ── helpers ──────────────────────────────────────────────────────────────

    def _rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.repo_root))
        except ValueError:
            return str(p)

    def _iter_py(self, scope: Optional[str] = None):
        root = self.repo_root / scope if scope else self.repo_root
        skip = {".pythonlibs", ".mypy_cache", ".pytest_cache",
                "venv", "__pycache__", "build", "cache",
                "node_modules", "attached_assets", ".git"}
        for f in root.rglob("*.py"):
            if any(p in skip for p in f.parts):
                continue
            yield f

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    # ── 1. DOC_DEBT — undocumented public API ────────────────────────────────

    def detect_doc_debt(self, scope: Optional[str] = None) -> List[DriftSignal]:
        """
        Finds public functions and classes that have no docstring.
        Scope restricts the search to a sub-directory (e.g. 'app/game_engine').
        """
        signals = []
        limit   = 500  # cap to keep this fast

        for py_file in self._iter_py(scope):
            if limit <= 0:
                break
            limit -= 1
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                         ast.ClassDef)):
                    continue
                if node.name.startswith("_"):
                    continue
                if not ast.get_docstring(node):
                    signals.append(DriftSignal(
                        category="DOC_DEBT",
                        severity="info",
                        path=f"{self._rel(py_file)}:{node.lineno}",
                        message=f"public {'class' if isinstance(node, ast.ClassDef) else 'def'} "
                                f"'{node.name}' has no docstring",
                        auto_fix=True,
                    ))
        return signals

    # ── 2. ARCH_BOUNDARY — cross-layer imports ───────────────────────────────

    def detect_arch_boundary(self) -> List[DriftSignal]:
        """
        Checks that architectural layers do not import each other
        in ways that violate the intended dependency direction.
        Approved exceptions are loaded from policy.yaml boundary_exceptions.
        """
        signals = []

        # Load approved boundary exceptions from policy.yaml
        _exceptions: list = []
        try:
            import yaml
            _policy_path = self.repo_root / "agents" / "serena" / "policy.yaml"
            if _policy_path.exists():
                _pol = yaml.safe_load(_policy_path.read_text())
                _exceptions = _pol.get("boundary_exceptions", []) if _pol else []
        except Exception:
            pass

        def _is_excepted(layer: str, mod: str, rel_path: str) -> bool:
            # Normalize slashes for cross-platform comparison
            rel_norm = rel_path.replace("\\", "/")
            for exc in _exceptions:
                if exc.get("layer") != layer:
                    continue
                if exc.get("imports", "") not in mod:
                    continue
                locs = exc.get("locations", ["*"])
                if "*" in locs or any(loc in rel_norm for loc in locs):
                    return True
            return False

        for layer, forbidden_imports in ARCH_LAYERS.items():
            layer_dir = self.repo_root / layer
            if not layer_dir.exists():
                continue

            for py_file in layer_dir.rglob("*.py"):
                if "__pycache__" in py_file.parts:
                    continue
                try:
                    src = py_file.read_text(encoding="utf-8", errors="replace")
                    tree = ast.parse(src)
                except (SyntaxError, OSError):
                    continue

                for node in ast.walk(tree):
                    if not isinstance(node, (ast.Import, ast.ImportFrom)):
                        continue
                    if isinstance(node, ast.ImportFrom):
                        mod = (node.module or "").replace("/", ".")
                    else:
                        mod = ".".join(a.name for a in node.names)

                    for forbidden in forbidden_imports:
                        fmod = forbidden.replace("/", ".")
                        if mod.startswith(fmod) or fmod in mod:
                            if _is_excepted(layer, mod, self._rel(py_file)):
                                continue
                            signals.append(DriftSignal(
                                category="ARCH_BOUNDARY",
                                severity="warn",
                                path=f"{self._rel(py_file)}:{node.lineno}",
                                message=f"layer '{layer}' imports forbidden module '{mod}' "
                                        f"(forbidden: '{forbidden}')",
                                auto_fix=False,
                            ))
        return signals

    # ── 3. ROLE_DRIFT — malformed personality YAMLs ──────────────────────────

    def detect_role_drift(self) -> List[DriftSignal]:
        """
        Checks every personality YAML in agents/personalities/ for missing
        required fields.
        """
        signals = []
        personalities_dir = self.repo_root / "agents" / "personalities"
        if not personalities_dir.exists():
            return signals

        try:
            import yaml as _yaml
        except ImportError:
            return signals

        for yf in personalities_dir.glob("*.yaml"):
            try:
                data = _yaml.safe_load(yf.read_text())
            except Exception:
                signals.append(DriftSignal(
                    category="ROLE_DRIFT",
                    severity="critical",
                    path=self._rel(yf),
                    message="YAML parse error — cannot validate personality",
                    auto_fix=False,
                ))
                continue

            if not isinstance(data, dict):
                continue

            for field_name in REQUIRED_YAML_FIELDS:
                if field_name not in data:
                    signals.append(DriftSignal(
                        category="ROLE_DRIFT",
                        severity="warn",
                        path=self._rel(yf),
                        message=f"personality missing required field '{field_name}'",
                        auto_fix=False,
                    ))

        return signals

    # ── 4. ORPHAN_CHUNK — indexed chunks whose source files are gone ──────────

    def detect_orphan_chunks(self) -> List[DriftSignal]:
        """
        Queries the Memory Palace DB for chunks whose source file no longer
        exists on disk.  Returns at most 50 signals to avoid overwhelming output.
        """
        signals = []
        if not self.db_path or not Path(self.db_path).exists():
            return signals

        try:
            conn = self._connect()
            rows = conn.execute(
                "SELECT DISTINCT path FROM code_index LIMIT 2000"
            ).fetchall()
            conn.close()
        except Exception:
            return signals

        count = 0
        for (src_file,) in rows:
            p = self.repo_root / src_file
            if not p.exists():
                signals.append(DriftSignal(
                    category="ORPHAN_CHUNK",
                    severity="warn",
                    path=src_file,
                    message="source file no longer exists — chunk is stale",
                    auto_fix=True,
                ))
                count += 1
                if count >= 50:
                    break

        return signals

    # ── 5. STALE_INDEX — on-disk files missing from the index ────────────────

    def detect_stale_index(self, scope: Optional[str] = None) -> List[DriftSignal]:
        """
        Finds Python files that exist on disk but are not yet in the index.
        Scoped to the game scope directories by default.
        """
        signals = []
        if not self.db_path or not Path(self.db_path).exists():
            return signals

        try:
            conn = self._connect()
            indexed = {
                r[0] for r in conn.execute(
                    "SELECT DISTINCT path FROM code_index"
                ).fetchall()
            }
            conn.close()
        except Exception:
            return signals

        count = 0
        for py_file in self._iter_py(scope):
            rel = self._rel(py_file)
            if rel not in indexed:
                signals.append(DriftSignal(
                    category="STALE_INDEX",
                    severity="info",
                    path=rel,
                    message="file exists but is not indexed — run 'serena walk'",
                    auto_fix=True,
                ))
                count += 1
                if count >= 30:
                    break

        return signals

    # ── 6. PROTOCOL_DRIFT — malformed OmniTag references ─────────────────────

    def detect_protocol_drift(self) -> List[DriftSignal]:
        """
        Scans chronicle / memory observations for OmniTag patterns,
        checks for empty payloads or unknown tag types.
        """
        signals = []
        if not self.db_path or not Path(self.db_path).exists():
            return signals

        known_tags = {"Msg", "Ctx", "Ref", "Task", "Fact", "Err", "Obs"}

        try:
            conn = self._connect()
            rows = conn.execute(
                "SELECT id, note FROM observations LIMIT 500"
            ).fetchall()
            conn.close()
        except Exception:
            return signals

        for (obs_id, note) in rows:
            if not note:
                continue
            for m in OMNI_TAG_RE.finditer(note):
                tag_type, payload = m.group(1), m.group(2)
                if tag_type not in known_tags:
                    signals.append(DriftSignal(
                        category="PROTOCOL_DRIFT",
                        severity="info",
                        path=f"observations#{obs_id}",
                        message=f"unknown OmniTag type '{tag_type}⛛{{{payload}}}'",
                        auto_fix=False,
                    ))
                elif not payload.strip():
                    signals.append(DriftSignal(
                        category="PROTOCOL_DRIFT",
                        severity="warn",
                        path=f"observations#{obs_id}",
                        message=f"empty OmniTag payload [{tag_type}⛛{{}}]",
                        auto_fix=False,
                    ))

        return signals

    # ── master detector ───────────────────────────────────────────────────────

    def detect_all(self,
                   scope: Optional[str] = None,
                   fast: bool = True) -> List[DriftSignal]:
        """
        Run all drift detectors.  fast=True skips the slower doc-debt scan
        (which AST-parses every file).

        Returns signals sorted by severity (critical > warn > info).
        """
        _severity_order = {"critical": 0, "warn": 1, "info": 2}

        signals: List[DriftSignal] = []

        signals += self.detect_role_drift()
        signals += self.detect_orphan_chunks()
        signals += self.detect_stale_index(scope=scope)
        signals += self.detect_arch_boundary()
        signals += self.detect_protocol_drift()

        if not fast:
            signals += self.detect_doc_debt(scope=scope)

        signals.sort(key=lambda s: _severity_order.get(s.severity, 9))
        self._signals = signals
        return signals

    # ── alignment check (Mladenc alignment) ──────────────────────────────────

    def align_check(self) -> dict:
        """
        Check the system's alignment against the ideal architecture (Mladenc).

        Returns a dict:
          {
            "aligned": bool,
            "score": float,    # 0.0 (chaos) → 1.0 (Mladenc)
            "checks": [...]
          }
        """
        checks = []

        def _check(name: str, condition: bool, msg_ok: str, msg_fail: str):
            checks.append({
                "name":    name,
                "passed":  condition,
                "message": msg_ok if condition else msg_fail,
            })

        # Architecture checks
        _check(
            "serena_package",
            (self.repo_root / "agents" / "serena" / "__init__.py").exists(),
            "agents/serena/ package exists",
            "agents/serena/__init__.py missing — Serena not properly packaged",
        )
        _check(
            "memory_palace",
            bool(self.db_path) and Path(self.db_path).exists(),
            "Memory Palace (SQLite) is present",
            "Memory Palace DB not found — run 'serena walk' first",
        )
        _check(
            "policy_gate",
            (self.repo_root / "agents" / "serena" / "policy.yaml").exists(),
            "Consent gate (policy.yaml) is in place",
            "policy.yaml missing — SAFE classification is void",
        )
        _check(
            "personality_yamls",
            bool(list((self.repo_root / "agents" / "personalities").glob("*.yaml"))
                 if (self.repo_root / "agents" / "personalities").exists() else []),
            "Agent personalities are defined",
            "No personality YAMLs found — agents have no identity",
        )
        _check(
            "game_engine",
            (self.repo_root / "app" / "game_engine" / "commands.py").exists(),
            "Game engine (commands.py) is present",
            "commands.py missing — Terminal Depths offline",
        )
        _check(
            "no_critical_drift",
            not any(s.severity == "critical"
                    for s in self.detect_role_drift()),
            "No critical role drift detected",
            "CRITICAL role drift — personality YAMLs are broken",
        )

        passed  = sum(1 for c in checks if c["passed"])
        total   = len(checks)
        score   = round(passed / total, 2) if total else 0.0
        aligned = score >= 0.80

        return {
            "aligned":   aligned,
            "score":     score,
            "passed":    passed,
            "total":     total,
            "checks":    checks,
            "horizon":   "𝕄ₗₐ⧉𝕕𝕖𝕟𝕔 — perfect coherence is the unreachable attractor",
        }
