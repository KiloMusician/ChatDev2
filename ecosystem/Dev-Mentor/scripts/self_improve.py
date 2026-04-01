#!/usr/bin/env python3
"""scripts/self_improve.py — Codebase Self-Improvement Agent

Analyzes the Terminal Depths codebase for:
  - Code quality issues (long functions, missing docstrings, duplicates)
  - Missing test coverage indicators
  - TODO/FIXME comments needing action
  - Outdated patterns or anti-patterns
  - Documentation gaps

Then uses the LLM to generate targeted improvement suggestions and
optionally creates tasks in the queue for each issue found.

Usage:
    python3 scripts/self_improve.py              # analyze and report
    python3 scripts/self_improve.py --tasksify   # convert findings to tasks
    python3 scripts/self_improve.py --patch <id> # apply a specific suggestion
    python3 scripts/self_improve.py --focus backend   # analyze one module
    python3 scripts/self_improve.py --todos      # extract and queue TODO items
    python3 scripts/self_improve.py --dry-run    # show plan without changes
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import time
import urllib.request
import uuid
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.parent
TASKS_DIR = BASE_DIR / "tasks"
FILE_TASKS_DIR = TASKS_DIR / "legacy_runtime"
TASKS_DIR.mkdir(exist_ok=True)
FILE_TASKS_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://localhost:7337"

SEVERITY_HIGH = "HIGH"
SEVERITY_MED = "MED"
SEVERITY_LOW = "LOW"


def log(level: str, msg: str, **ctx):
    ts = time.strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[36m",
        "OK": "\033[32m",
        "WARN": "\033[33m",
        "ERROR": "\033[31m",
        "FIND": "\033[35m",
        "SUGGEST": "\033[34m",
    }
    c = colors.get(level, "\033[0m")
    r = "\033[0m"
    kv = "  ".join(f"{k}={v}" for k, v in ctx.items())
    print(f"{c}[{level}]{r} {ts} {msg}" + (f"  | {kv}" if kv else ""))


def _post(path: str, data: dict) -> dict:
    try:
        req = urllib.request.Request(
            BASE_URL + path,
            json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def _llm(prompt: str, max_tokens: int = 300) -> str | None:
    r = _post(
        "/api/llm/generate",
        {"prompt": prompt, "max_tokens": max_tokens, "temperature": 0.3},
    )
    return r.get("text", "").strip() or None


class Finding:
    def __init__(
        self,
        severity: str,
        category: str,
        file: str,
        line: int,
        message: str,
        snippet: str = "",
    ):
        self.id = uuid.uuid4().hex[:8]
        self.severity = severity
        self.category = category
        self.file = file
        self.line = line
        self.message = message
        self.snippet = snippet
        self.suggestion = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "severity": self.severity,
            "category": self.category,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "snippet": self.snippet[:200],
            "suggestion": self.suggestion,
        }

    def print_line(self):
        color = {
            SEVERITY_HIGH: "\033[31m",
            SEVERITY_MED: "\033[33m",
            SEVERITY_LOW: "\033[90m",
        }.get(self.severity, "")
        r = "\033[0m"
        print(
            f"  {color}[{self.severity}]{r}  {self.file}:{self.line}  {self.category}: {self.message}"
        )
        if self.suggestion:
            print(f"         \033[34m→ {self.suggestion[:80]}\033[0m")


class SelfImprover:
    def __init__(self):
        self.findings: list[Finding] = []

    def _py_files(self, focus: str | None = None) -> list[Path]:
        all_files = []
        dirs = ["app/backend", "app/game_engine", "agents", "scripts", "mcp"]
        if focus:
            dirs = [d for d in dirs if focus.lower() in d]
        for d in dirs:
            p = BASE_DIR / d
            if p.exists():
                all_files.extend(p.rglob("*.py"))
        return [f for f in all_files if "__pycache__" not in str(f)]

    def analyze_long_functions(self, focus: str | None = None):
        THRESHOLD = 80
        for path in self._py_files(focus):
            try:
                tree = ast.parse(path.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    length = (node.end_lineno or 0) - node.lineno
                    if length > THRESHOLD:
                        self.findings.append(
                            Finding(
                                SEVERITY_MED,
                                "long_function",
                                str(path.relative_to(BASE_DIR)),
                                node.lineno,
                                f"Function `{node.name}` is {length} lines (>{THRESHOLD})",
                                f"def {node.name}",
                            )
                        )

    def analyze_missing_docstrings(self, focus: str | None = None):
        for path in self._py_files(focus):
            try:
                tree = ast.parse(path.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_"):
                        continue
                    if not (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                    ):
                        self.findings.append(
                            Finding(
                                SEVERITY_LOW,
                                "missing_docstring",
                                str(path.relative_to(BASE_DIR)),
                                node.lineno,
                                f"Public function `{node.name}` has no docstring",
                            )
                        )

    def analyze_todos(self, focus: str | None = None):
        patterns = [
            (
                re.compile(r"#\s*(TODO|FIXME|HACK|XXX|BUG)\s*:?\s*(.+)", re.I),
                SEVERITY_MED,
            ),
            (
                re.compile(r"#\s*(TEMP|TEMPORARY|REMOVE|WORKAROUND)\s*:?\s*(.+)", re.I),
                SEVERITY_LOW,
            ),
        ]
        for path in self._py_files(focus):
            try:
                lines = path.read_text().splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines, 1):
                for pattern, severity in patterns:
                    m = pattern.search(line)
                    if m:
                        self.findings.append(
                            Finding(
                                severity,
                                f"todo_{m.group(1).lower()}",
                                str(path.relative_to(BASE_DIR)),
                                i,
                                f"{m.group(1).upper()}: {m.group(2).strip()[:80]}",
                                line.strip()[:100],
                            )
                        )

    def analyze_duplicate_code(self, focus: str | None = None):
        seen_signatures: dict = {}
        for path in self._py_files(focus):
            try:
                tree = ast.parse(path.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if len(node.body) < 5:
                        continue
                    sig = (node.name, len(node.args.args), len(node.body))
                    if sig in seen_signatures:
                        prev_path, prev_line = seen_signatures[sig]
                        if prev_path != str(path):
                            self.findings.append(
                                Finding(
                                    SEVERITY_MED,
                                    "possible_duplicate",
                                    str(path.relative_to(BASE_DIR)),
                                    node.lineno,
                                    f"Function `{node.name}` may duplicate {prev_path}:{prev_line}",
                                )
                            )
                    else:
                        seen_signatures[sig] = (
                            str(path.relative_to(BASE_DIR)),
                            node.lineno,
                        )

    def analyze_large_files(self, focus: str | None = None):
        THRESHOLD = 800
        for path in self._py_files(focus):
            try:
                lines = path.read_text().count("\n")
            except Exception:
                continue
            if lines > THRESHOLD:
                self.findings.append(
                    Finding(
                        SEVERITY_MED,
                        "large_file",
                        str(path.relative_to(BASE_DIR)),
                        1,
                        f"File is {lines} lines (>{THRESHOLD}) — consider splitting",
                    )
                )

    def analyze_bare_excepts(self, focus: str | None = None):
        for path in self._py_files(focus):
            try:
                tree = ast.parse(path.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    self.findings.append(
                        Finding(
                            SEVERITY_LOW,
                            "bare_except",
                            str(path.relative_to(BASE_DIR)),
                            getattr(node, "lineno", 0),
                            "Bare `except:` clause — use `except Exception as e:` instead",
                        )
                    )

    def suggest_improvements(self, sample_size: int = 5):
        high_findings = [f for f in self.findings if f.severity == SEVERITY_HIGH]
        med_findings = [f for f in self.findings if f.severity == SEVERITY_MED]
        targets = (high_findings + med_findings)[:sample_size]

        for finding in targets:
            snippet = finding.snippet or f"# {finding.message}"
            suggestion = _llm(
                f"In a Python file `{finding.file}` at line {finding.line}:\n"
                f"Issue: {finding.message}\n"
                f"Code: {snippet}\n\n"
                f"Give a one-sentence specific fix suggestion. No code blocks needed.",
                max_tokens=100,
            )
            if suggestion:
                finding.suggestion = suggestion

    def run(self, focus: str | None = None, todos_only: bool = False) -> list[Finding]:
        log("INFO", "Scanning codebase...", focus=focus or "all")

        if todos_only:
            self.analyze_todos(focus)
        else:
            self.analyze_long_functions(focus)
            self.analyze_large_files(focus)
            self.analyze_bare_excepts(focus)
            self.analyze_todos(focus)
            self.analyze_duplicate_code(focus)
            self.analyze_missing_docstrings(focus)

        log(
            "FIND",
            f"Found {len(self.findings)} issues",
            high=sum(1 for f in self.findings if f.severity == SEVERITY_HIGH),
            med=sum(1 for f in self.findings if f.severity == SEVERITY_MED),
            low=sum(1 for f in self.findings if f.severity == SEVERITY_LOW),
        )
        return self.findings

    def print_report(self):
        print(f"\n{'='*70}")
        print(f"  SELF-IMPROVEMENT REPORT  |  {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        by_cat: dict = {}
        for f in self.findings:
            by_cat.setdefault(f.category, []).append(f)

        for cat, items in sorted(by_cat.items(), key=lambda x: -len(x[1])):
            print(f"\n  [{cat.upper()}]  ({len(items)} findings)")
            for item in items[:5]:
                item.print_line()
            if len(items) > 5:
                print(f"    ... and {len(items) - 5} more")

        print(
            f"\n  Total: {len(self.findings)} findings across {len(by_cat)} categories"
        )
        print()

    def create_tasks(self, limit: int = 10, dry_run: bool = False) -> int:
        high_priority = sorted(
            [f for f in self.findings if f.severity in (SEVERITY_HIGH, SEVERITY_MED)],
            key=lambda f: (0 if f.severity == SEVERITY_HIGH else 1, f.file),
        )[:limit]

        created = 0
        for finding in high_priority:
            task_id = f"improve_{finding.id}"
            task = {
                "id": task_id,
                "title": f"[{finding.category}] {finding.message[:60]}",
                "type": "improve",
                "details": f"File: {finding.file}:{finding.line}\nIssue: {finding.message}\n"
                f"Suggestion: {finding.suggestion or '(use LLM to generate fix)'}",
                "target": finding.file,
                "priority": 4 if finding.severity == SEVERITY_HIGH else 6,
                "status": "pending",
                "severity": finding.severity,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "result": "",
            }
            if not dry_run:
                path = FILE_TASKS_DIR / f"{task_id}.json"
                if not path.exists():
                    path.write_text(json.dumps(task, indent=2))
                    log("OK", f"Task created: {task['title'][:60]}")
                    created += 1
            else:
                log("INFO", f"[DRY RUN] Would create: {task['title'][:60]}")
                created += 1
        return created

    def extract_todos_to_tasks(self, dry_run: bool = False) -> int:
        todo_findings = [f for f in self.findings if "todo" in f.category]
        created = 0
        for finding in todo_findings:
            task_id = f"todo_{finding.id}"
            task = {
                "id": task_id,
                "title": finding.message[:80],
                "type": "implement",
                "details": f"Source: {finding.file}:{finding.line}\nCode: {finding.snippet}",
                "target": finding.file,
                "priority": 5,
                "status": "pending",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "result": "",
            }
            if not dry_run:
                path = FILE_TASKS_DIR / f"{task_id}.json"
                if not path.exists():
                    path.write_text(json.dumps(task, indent=2))
                    created += 1
            else:
                created += 1
        log("OK", f"{'Would create' if dry_run else 'Created'} {created} TODO tasks")
        return created


def main():
    ap = argparse.ArgumentParser(
        description="Terminal Depths self-improvement analyzer"
    )
    ap.add_argument(
        "--focus", metavar="MODULE", help="Analyze specific module (backend/agents/etc)"
    )
    ap.add_argument(
        "--tasksify", action="store_true", help="Convert findings to task queue entries"
    )
    ap.add_argument(
        "--todos", action="store_true", help="Extract TODO comments to task queue"
    )
    ap.add_argument(
        "--suggest", action="store_true", help="Use LLM to generate fix suggestions"
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="Show plan without writing tasks"
    )
    ap.add_argument(
        "--limit", type=int, default=10, help="Max tasks to create (default: 10)"
    )
    ap.add_argument("--json", action="store_true", help="Output findings as JSON")
    args = ap.parse_args()

    improver = SelfImprover()
    improver.run(focus=args.focus, todos_only=args.todos)

    if args.suggest:
        log("INFO", "Generating LLM suggestions for top findings...")
        improver.suggest_improvements(sample_size=5)

    if args.json:
        print(json.dumps([f.to_dict() for f in improver.findings], indent=2))
        return

    improver.print_report()

    if args.todos:
        improver.extract_todos_to_tasks(dry_run=args.dry_run)
    elif args.tasksify:
        count = improver.create_tasks(limit=args.limit, dry_run=args.dry_run)
        log(
            "OK",
            f"{'Would create' if args.dry_run else 'Created'} {count} improvement tasks",
        )
    else:
        high_med = sum(
            1 for f in improver.findings if f.severity in (SEVERITY_HIGH, SEVERITY_MED)
        )
        if high_med > 0:
            log(
                "WARN",
                f"{high_med} HIGH/MED findings — run with --tasksify to queue fixes",
            )


if __name__ == "__main__":
    main()
