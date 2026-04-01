#!/usr/bin/env python3
"""
agents/validator.py — Content Quality Validator

Validates generated content (challenges, lore, code, man pages) for quality:
  - JSON validity and required fields
  - Minimum content length / completeness
  - No placeholder/boilerplate text
  - LLM quality score (optional, uses LLM to rate the content)
  - Python syntax validity for generated code
  - Stores validation results in memory.py

Usage:
    python3 agents/validator.py                       # validate all recent generated content
    python3 agents/validator.py --type challenge      # validate challenges only
    python3 agents/validator.py --type code           # validate generated code
    python3 agents/validator.py --type lore           # validate lore pages
    python3 agents/validator.py --file <path>         # validate a specific file
    python3 agents/validator.py --score               # use LLM quality scoring
    python3 agents/validator.py --task <id>           # run for orchestrator task
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent.parent
BASE_URL = "http://localhost:7337"

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

_PLACEHOLDER_PATTERNS = [
    re.compile(r"\b(TODO|FIXME|PLACEHOLDER|INSERT HERE|YOUR TEXT|EXAMPLE ONLY)\b", re.I),
    re.compile(r"\.\.\.$"),
    re.compile(r"Lorem ipsum", re.I),
    re.compile(r"<FILL IN>", re.I),
]

_REQUIRED_CHALLENGE_FIELDS = {"title", "description", "category", "flag", "xp"}
_REQUIRED_LORE_FIELDS = {"name", "faction"}


def log(level: str, msg: str, **ctx):
    ts = time.strftime("%H:%M:%S")
    colors = {"INFO": "\033[36m", "OK": "\033[32m", "WARN": "\033[33m",
              "ERROR": "\033[31m", "PASS": "\033[32m", "FAIL": "\033[31m"}
    c = colors.get(level, "\033[0m")
    r = "\033[0m"
    kv = "  ".join(f"{k}={v}" for k, v in ctx.items())
    print(f"{c}[{level}]{r} {ts} {msg}" + (f"  | {kv}" if kv else ""))


def _post(path: str, data: dict) -> dict:
    try:
        req = urllib.request.Request(
            BASE_URL + path, json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def _get(path: str) -> dict:
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=8) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


class ValidationReport:
    def __init__(self, item_id: str, content_type: str):
        self.item_id = item_id
        self.content_type = content_type
        self.checks: list[tuple[str, str, str]] = []
        self.overall = PASS

    def add(self, check_name: str, status: str, detail: str = ""):
        self.checks.append((check_name, status, detail))
        if status == FAIL:
            self.overall = FAIL
        elif status == WARN and self.overall == PASS:
            self.overall = WARN

    def print(self):
        c_map = {PASS: "\033[32m", FAIL: "\033[31m", WARN: "\033[33m"}
        overall_c = c_map.get(self.overall, "")
        r = "\033[0m"
        print(f"  [{overall_c}{self.overall}{r}] {self.content_type}:{self.item_id}")
        for name, status, detail in self.checks:
            sc = c_map.get(status, "")
            d = f" — {detail}" if detail else ""
            print(f"         {sc}{status}{r}  {name}{d}")

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "content_type": self.content_type,
            "overall": self.overall,
            "checks": [{"name": n, "status": s, "detail": d} for n, s, d in self.checks],
        }


def _has_placeholder(text: str) -> bool:
    return any(p.search(text) for p in _PLACEHOLDER_PATTERNS)


def _check_min_length(text: str, min_chars: int) -> tuple[str, str]:
    if len(text) < min_chars:
        return FAIL, f"too short ({len(text)} < {min_chars} chars)"
    return PASS, f"{len(text)} chars"


def _check_no_placeholder(text: str) -> tuple[str, str]:
    if _has_placeholder(text):
        return WARN, "contains placeholder text"
    return PASS, ""


def _llm_quality_score(content: str, content_type: str) -> float | None:
    result = _post("/api/llm/generate", {
        "prompt": (
            f"Rate this {content_type} content for Terminal Depths (a cyberpunk hacking game) "
            f"on a scale of 1-10. Consider: relevance, atmosphere, specificity, quality.\n\n"
            f"Content (first 400 chars):\n{content[:400]}\n\n"
            f"Output ONLY a single integer from 1 to 10. Nothing else."
        ),
        "max_tokens": 5,
        "temperature": 0.1,
    })
    text = result.get("text", "").strip()
    try:
        score = float(re.search(r"\d+", text).group())
        return min(10.0, max(1.0, score))
    except Exception:
        return None


class Validator:
    def __init__(self, use_llm_scoring: bool = False):
        self.use_llm_scoring = use_llm_scoring
        self.reports: list[ValidationReport] = []
        self.passes = 0
        self.warns = 0
        self.fails = 0

    def _record(self, report: ValidationReport):
        self.reports.append(report)
        if report.overall == PASS:
            self.passes += 1
        elif report.overall == WARN:
            self.warns += 1
        else:
            self.fails += 1
        report.print()

        try:
            sys.path.insert(0, str(BASE_DIR))
            from memory import get_memory
            mem = get_memory()
            mem.log_interaction(
                "validation",
                f"{report.content_type}:{report.item_id}",
                report.overall,
                success=(report.overall != FAIL),
            )
        except Exception:
            pass

    def validate_challenge(self, content: str | dict, item_id: str = "?") -> ValidationReport:
        report = ValidationReport(item_id, "challenge")
        if isinstance(content, str):
            try:
                data = json.loads(content)
                report.add("json_valid", PASS)
            except json.JSONDecodeError as e:
                report.add("json_valid", FAIL, str(e))
                self._record(report)
                return report
        else:
            data = content

        missing = _REQUIRED_CHALLENGE_FIELDS - set(data.keys())
        if missing:
            report.add("required_fields", FAIL, f"missing: {missing}")
        else:
            report.add("required_fields", PASS)

        xp = data.get("xp", 0)
        if not isinstance(xp, (int, float)) or xp <= 0 or xp > 1000:
            report.add("xp_valid", WARN, f"xp={xp} (expected 1-1000)")
        else:
            report.add("xp_valid", PASS, f"xp={xp}")

        desc = str(data.get("description", ""))
        s, d = _check_min_length(desc, 30)
        report.add("description_length", s, d)

        flag = str(data.get("flag", ""))
        if not flag or flag == "flag{...}":
            report.add("flag_set", WARN, "flag is placeholder")
        else:
            report.add("flag_set", PASS)

        s, d = _check_no_placeholder(json.dumps(data))
        report.add("no_placeholder", s, d)

        if self.use_llm_scoring:
            score = _llm_quality_score(json.dumps(data), "CTF challenge")
            if score is not None:
                status = PASS if score >= 6 else (WARN if score >= 4 else FAIL)
                report.add("llm_quality", status, f"score={score}/10")

        self._record(report)
        return report

    def validate_lore(self, content: str, item_id: str = "?") -> ValidationReport:
        report = ValidationReport(item_id, "lore")

        s, d = _check_min_length(content, 80)
        report.add("min_length", s, d)

        s, d = _check_no_placeholder(content)
        report.add("no_placeholder", s, d)

        has_header = content.startswith("#")
        report.add("has_header", PASS if has_header else WARN, "" if has_header else "no markdown header")

        if self.use_llm_scoring:
            score = _llm_quality_score(content, "lore text")
            if score is not None:
                status = PASS if score >= 6 else (WARN if score >= 4 else FAIL)
                report.add("llm_quality", status, f"score={score}/10")

        self._record(report)
        return report

    def validate_code(self, content: str, item_id: str = "?") -> ValidationReport:
        report = ValidationReport(item_id, "code")

        s, d = _check_min_length(content, 50)
        report.add("min_length", s, d)

        s, d = _check_no_placeholder(content)
        report.add("no_placeholder", s, d)

        try:
            ast.parse(content)
            report.add("syntax_valid", PASS)
        except SyntaxError as e:
            report.add("syntax_valid", FAIL, str(e))

        has_docstring = '"""' in content or "'''" in content
        report.add("has_docstring", PASS if has_docstring else WARN, "" if has_docstring else "no docstring found")

        if self.use_llm_scoring:
            score = _llm_quality_score(content, "Python code")
            if score is not None:
                status = PASS if score >= 6 else (WARN if score >= 4 else FAIL)
                report.add("llm_quality", status, f"score={score}/10")

        self._record(report)
        return report

    def validate_man_page(self, content: str, item_id: str = "?") -> ValidationReport:
        report = ValidationReport(item_id, "man_page")

        s, d = _check_min_length(content, 100)
        report.add("min_length", s, d)

        required_sections = ["NAME", "SYNOPSIS", "DESCRIPTION"]
        found = [s for s in required_sections if f"## {s}" in content.upper() or f"# {s}" in content.upper() or s in content]
        missing = set(required_sections) - set(found)
        if missing:
            report.add("required_sections", WARN, f"missing: {missing}")
        else:
            report.add("required_sections", PASS)

        s, d = _check_no_placeholder(content)
        report.add("no_placeholder", s, d)

        self._record(report)
        return report

    def validate_file(self, path: Path) -> ValidationReport | None:
        if not path.exists():
            log("ERROR", f"File not found: {path}")
            return None
        content = path.read_text()
        name = path.stem

        if path.parent.name == "commands":
            return self.validate_man_page(content, name)
        elif path.parent.name == "lore" or path.parent.name == "fragments":
            return self.validate_lore(content, name)
        elif path.suffix == ".py":
            return self.validate_code(content, name)
        elif path.suffix == ".json":
            return self.validate_challenge(content, name)
        else:
            return self.validate_lore(content, name)

    def validate_all_generated(self, content_type: str | None = None, limit: int = 20):
        try:
            sys.path.insert(0, str(BASE_DIR))
            from memory import get_memory
            mem = get_memory()
        except Exception as e:
            log("ERROR", f"Cannot load memory: {e}")
            return

        types_to_check = [content_type] if content_type else ["challenge", "lore_fragment", "lore_agent", "code", "doc"]
        for ct in types_to_check:
            items = mem.get_generated(ct, limit=limit)
            log("INFO", f"Validating {len(items)} {ct} items")
            for item in items:
                content = item.get("content", "")
                item_id = str(item.get("id", "?"))
                if ct in ("lore_fragment", "lore_agent", "lore_faction", "lore_world_node"):
                    self.validate_lore(content, item_id)
                elif ct == "challenge":
                    self.validate_challenge(content, item_id)
                elif ct == "code":
                    self.validate_code(content, item_id)
                else:
                    self.validate_lore(content, item_id)

    def print_summary(self):
        print(f"\n{'='*50}")
        print(f"  VALIDATION SUMMARY")
        print(f"  PASS={self.passes}  WARN={self.warns}  FAIL={self.fails}")
        total = self.passes + self.warns + self.fails
        if total:
            rate = round(self.passes / total * 100)
            print(f"  Quality rate: {rate}%  ({self.passes}/{total} passing)")
        print()

    def get_failed(self) -> list[ValidationReport]:
        return [r for r in self.reports if r.overall == FAIL]


def _run_task(task_id: str):
    task_path = BASE_DIR / "tasks" / f"{task_id}.json"
    if not task_path.exists():
        log("ERROR", f"Task not found: {task_id}")
        return
    with open(task_path) as f:
        task = json.load(f)
    target = task.get("target", "")
    v = Validator(use_llm_scoring=False)
    if target and Path(target).exists():
        v.validate_file(Path(target))
    else:
        ct = task.get("details", "").lower()
        for keyword in ("challenge", "lore", "code", "doc"):
            if keyword in ct:
                v.validate_all_generated(keyword)
                break
        else:
            v.validate_all_generated()
    v.print_summary()
    task["status"] = "done"
    task["result"] = f"pass={v.passes} warn={v.warns} fail={v.fails}"
    task["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(task_path, "w") as f:
        json.dump(task, f, indent=2)


def main():
    ap = argparse.ArgumentParser(description="Content quality validator")
    ap.add_argument("--type", metavar="TYPE", help="Content type: challenge|lore|code|doc")
    ap.add_argument("--file", metavar="PATH", help="Validate a specific file")
    ap.add_argument("--score", action="store_true", help="Use LLM quality scoring")
    ap.add_argument("--limit", type=int, default=20, help="Max items per type")
    ap.add_argument("--task", metavar="TASK_ID", help="Run for orchestrator task")
    ap.add_argument("--json", action="store_true", help="Output reports as JSON")
    args = ap.parse_args()

    if args.task:
        _run_task(args.task)
        return

    v = Validator(use_llm_scoring=args.score)

    if args.file:
        v.validate_file(Path(args.file))
    else:
        v.validate_all_generated(args.type, limit=args.limit)

    v.print_summary()

    if args.json:
        print(json.dumps([r.to_dict() for r in v.reports], indent=2))

    failed = v.get_failed()
    if failed:
        log("WARN", f"{len(failed)} items FAILED validation — review and regenerate")
        sys.exit(1)


if __name__ == "__main__":
    main()
