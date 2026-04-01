"""
walker.py — Serena's Walker: The Codebase Traversal Engine.

The Walker moves through all repositories like light through glass —
present everywhere, distorting nothing. It detects changed files via
git, extracts structure using Python's ast module, and feeds the
Memory Palace with semantic chunks.

ΨΞΦΩ role: Ψ-input layer — the intake of raw signal from the world.
"""
from __future__ import annotations

import ast
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

LOG = logging.getLogger("serena.walker")


# ──────────────────────────────────────────────────────────────────────────────
# Chunk types
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CodeChunk:
    """
    A semantic unit extracted from a source file.
    Could be a module, class, function, or raw text block.
    """
    path:       str                   # relative file path
    kind:       str                   # "module" | "class" | "function" | "text"
    name:       str                   # identifier or "" for module-level
    lineno:     int                   # starting line number (1-indexed)
    end_lineno: int                   # ending line number
    text:       str                   # source text of this chunk
    docstring:  Optional[str] = None  # extracted docstring if any
    tags:       List[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        first = self.text.strip().splitlines()[0][:80] if self.text.strip() else ""
        return f"{self.kind}:{self.name or 'module'} @ {self.path}:{self.lineno} — {first}"

    def to_dict(self) -> dict:
        return {
            "path":       self.path,
            "kind":       self.kind,
            "name":       self.name,
            "lineno":     self.lineno,
            "end_lineno": self.end_lineno,
            "text":       self.text,
            "docstring":  self.docstring,
            "tags":       self.tags,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Python AST chunker
# ──────────────────────────────────────────────────────────────────────────────

class PythonChunker:
    """Splits a Python file into CodeChunks using ast."""

    @staticmethod
    def chunk(path: str, source: str) -> List[CodeChunk]:
        chunks: List[CodeChunk] = []
        lines = source.splitlines(keepends=True)

        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as exc:
            LOG.debug("Syntax error in %s: %s", path, exc)
            return [CodeChunk(
                path=path, kind="text", name="", lineno=1,
                end_lineno=len(lines), text=source[:2000],
                tags=["parse_error"],
            )]

        # Module-level docstring
        module_doc = ast.get_docstring(tree)

        def _get_text(node: ast.AST) -> str:
            start = node.lineno - 1
            end   = getattr(node, "end_lineno", node.lineno)
            return "".join(lines[start:end])

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node)
                chunks.append(CodeChunk(
                    path=path, kind="function", name=node.name,
                    lineno=node.lineno,
                    end_lineno=getattr(node, "end_lineno", node.lineno),
                    text=_get_text(node),
                    docstring=doc,
                    tags=["python", "function"],
                ))
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                chunks.append(CodeChunk(
                    path=path, kind="class", name=node.name,
                    lineno=node.lineno,
                    end_lineno=getattr(node, "end_lineno", node.lineno),
                    text=_get_text(node)[:3000],  # cap class text
                    docstring=doc,
                    tags=["python", "class"],
                ))

        # Add a module-level chunk for the file header
        header_lines = "".join(lines[:min(30, len(lines))])
        chunks.append(CodeChunk(
            path=path, kind="module", name="",
            lineno=1, end_lineno=min(30, len(lines)),
            text=header_lines,
            docstring=module_doc,
            tags=["python", "module"],
        ))

        return chunks


# ──────────────────────────────────────────────────────────────────────────────
# Text chunker (markdown, yaml, txt)
# ──────────────────────────────────────────────────────────────────────────────

class TextChunker:
    """Splits non-Python text files into chunks by paragraph/section."""

    CHUNK_LINES = 30

    @classmethod
    def chunk(cls, path: str, text: str) -> List[CodeChunk]:
        lines  = text.splitlines()
        chunks = []
        i      = 0
        idx    = 0
        while i < len(lines):
            block = lines[i: i + cls.CHUNK_LINES]
            chunks.append(CodeChunk(
                path=path, kind="text", name=f"block_{idx}",
                lineno=i + 1, end_lineno=i + len(block),
                text="\n".join(block),
                tags=["text"],
            ))
            i   += cls.CHUNK_LINES
            idx += 1
        return chunks


# ──────────────────────────────────────────────────────────────────────────────
# Git utilities
# ──────────────────────────────────────────────────────────────────────────────

def _git_changed_files(repo_root: Path, since: Optional[str] = None) -> Set[str]:
    """Return set of files changed since `since` ref or since last commit."""
    try:
        if since:
            result = subprocess.run(
                ["git", "diff", "--name-only", since, "HEAD"],
                capture_output=True, text=True, cwd=repo_root,
            )
        else:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True, text=True, cwd=repo_root,
            )
        if result.returncode == 0:
            return set(result.stdout.splitlines())
    except Exception:
        pass
    return set()


def _git_all_tracked(repo_root: Path) -> List[str]:
    """Return list of all git-tracked files."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, cwd=repo_root,
        )
        if result.returncode == 0:
            return result.stdout.splitlines()
    except Exception:
        pass
    return []


# ──────────────────────────────────────────────────────────────────────────────
# The Walker
# ──────────────────────────────────────────────────────────────────────────────

SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache",
             "node_modules", ".vscode", ".devmentor",
             "outputs", ".local", "sessions", "state", "dist", "build",
             ".pythonlibs", ".cache", ".npm", "venv", ".venv", "site-packages",
             "lib", ".uv", "attached_assets"}

INDEXABLE_EXTS = {".py", ".md", ".yaml", ".yml", ".txt", ".json"}
CHUNK_SIZE_LIMIT      = 50_000   # bytes — skip non-Python files larger than this
PY_CHUNK_SIZE_LIMIT   = 500_000  # bytes — Python files (AST-parsed into small chunks)


class RepoWalker:
    """
    Walks a repository tree, extracts CodeChunks, and calls on_chunk()
    for each one. Designed for incremental updates: it can walk only
    changed files or the full tree.

    ΨΞΦΩ role: Ψ — the raw signal intake. Walks as Serena walks —
    present everywhere, distorting nothing.
    """

    def __init__(
        self,
        repo_root: Path,
        on_chunk: Optional[Callable[[CodeChunk], None]] = None,
    ):
        self.repo_root = Path(repo_root)
        self.on_chunk  = on_chunk or (lambda c: None)
        self._py       = PythonChunker()
        self._txt      = TextChunker()
        self.stats: Dict[str, int] = {
            "files_visited": 0,
            "chunks_emitted": 0,
            "errors": 0,
            "elapsed_s": 0,
        }

    def _should_skip(self, path: Path) -> bool:
        for part in path.parts:
            if part in SKIP_DIRS:
                return True
        return False

    def _process_file(self, path: Path) -> List[CodeChunk]:
        rel = str(path.relative_to(self.repo_root))
        try:
            is_py = path.suffix.lower() == ".py"
            limit = PY_CHUNK_SIZE_LIMIT if is_py else CHUNK_SIZE_LIMIT
            if path.stat().st_size > limit:
                return []
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            LOG.debug("Could not read %s: %s", rel, exc)
            self.stats["errors"] += 1
            return []

        ext = path.suffix.lower()
        if ext == ".py":
            return self._py.chunk(rel, text)
        else:
            return self._txt.chunk(rel, text)

    def walk_full(self) -> int:
        """Walk the entire repo. Returns total chunks emitted."""
        t0 = time.monotonic()
        self.stats = {k: 0 for k in self.stats}
        for p in self.repo_root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in INDEXABLE_EXTS:
                continue
            if self._should_skip(p.relative_to(self.repo_root)):
                continue
            self.stats["files_visited"] += 1
            for chunk in self._process_file(p):
                self.on_chunk(chunk)
                self.stats["chunks_emitted"] += 1
        self.stats["elapsed_s"] = round(time.monotonic() - t0, 2)
        LOG.info(
            "Walker.walk_full: files=%d chunks=%d errors=%d elapsed=%.2fs",
            self.stats["files_visited"], self.stats["chunks_emitted"],
            self.stats["errors"], self.stats["elapsed_s"],
        )
        return self.stats["chunks_emitted"]

    def walk_changed(self, since: Optional[str] = None) -> int:
        """Walk only files changed since `since` git ref."""
        changed = _git_changed_files(self.repo_root, since)
        if not changed:
            # Fall back to full walk if git can't tell us what changed
            return self.walk_full()
        t0 = time.monotonic()
        count = 0
        for rel_path in changed:
            p = self.repo_root / rel_path
            if not p.exists() or p.suffix.lower() not in INDEXABLE_EXTS:
                continue
            if self._should_skip(Path(rel_path)):
                continue
            for chunk in self._process_file(p):
                self.on_chunk(chunk)
                count += 1
        self.stats["elapsed_s"] = round(time.monotonic() - t0, 2)
        self.stats["chunks_emitted"] += count
        return count

    def walk_dirs(self, dirs: List[str], max_files: int = 200) -> int:
        """
        Walk only the specified dirs. Fast scoped walk for in-game use.
        Returns total chunks emitted.
        """
        t0 = time.monotonic()
        self.stats = {k: 0 for k in self.stats}
        count = 0
        for d in dirs:
            base = self.repo_root / d
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if count >= max_files:
                    break
                if not p.is_file():
                    continue
                if p.suffix.lower() not in INDEXABLE_EXTS:
                    continue
                if self._should_skip(p.relative_to(self.repo_root)):
                    continue
                self.stats["files_visited"] += 1
                for chunk in self._process_file(p):
                    self.on_chunk(chunk)
                    self.stats["chunks_emitted"] += 1
                count += 1
        self.stats["elapsed_s"] = round(time.monotonic() - t0, 2)
        LOG.info(
            "Walker.walk_dirs dirs=%r files=%d chunks=%d elapsed=%.2fs",
            dirs, self.stats["files_visited"], self.stats["chunks_emitted"],
            self.stats["elapsed_s"],
        )
        return self.stats["chunks_emitted"]

    def walk_file(self, rel_path: str) -> List[CodeChunk]:
        """Walk a single file and return its chunks (no on_chunk callback)."""
        p = self.repo_root / rel_path
        return self._process_file(p)
