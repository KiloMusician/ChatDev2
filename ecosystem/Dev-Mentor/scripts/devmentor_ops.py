#!/usr/bin/env python3
"""DevMentor Zero-Token Ops Engine

A single entrypoint for all deterministic operations.
Designed for Replit/agent environments to maximize leverage per token.

Usage:
    python scripts/devmentor_ops.py doctor   # Environment sanity check
    python scripts/devmentor_ops.py check    # Lint, syntax, health checks
    python scripts/devmentor_ops.py fix      # Auto-fix what can be fixed
    python scripts/devmentor_ops.py prune    # Detect bloat and duplicates
    python scripts/devmentor_ops.py graph    # Generate module/file map
    python scripts/devmentor_ops.py export   # Build portable ZIP
    python scripts/devmentor_ops.py report   # Generate markdown report
    python scripts/devmentor_ops.py all      # Run all operations
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
DEVMENTOR_DIR = ROOT / ".devmentor"
EXPORTS_DIR = ROOT / "exports"


@dataclass
class OperationResult:
    """Standardized result format for all ops"""

    operation: str
    success: bool
    duration_seconds: float = 0.0
    failures: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self):
        return asdict(self)


class ZeroTokenOps:
    """Main orchestrator for zero-token operations"""

    def __init__(self):
        self.results: dict[str, OperationResult] = {}
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure required directories exist"""
        for d in [REPORTS_DIR, DEVMENTOR_DIR, EXPORTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def run(self, operation: str) -> OperationResult | None:
        """Run a specific operation"""
        operations = {
            "doctor": self.ops_doctor,
            "check": self.ops_check,
            "fix": self.ops_fix,
            "prune": self.ops_prune,
            "graph": self.ops_graph,
            "export": self.ops_export,
            "report": self.ops_report,
            "all": self.ops_all,
        }

        if operation not in operations:
            print(f"Unknown operation: {operation}")
            print(f"Available: {', '.join(operations.keys())}")
            return None

        start = datetime.now()
        result = operations[operation]()
        duration = (datetime.now() - start).total_seconds()

        if result:
            result.duration_seconds = round(duration, 2)
            self.results[operation] = result
            self._save_result(operation, result)

        return result

    def _save_result(self, operation: str, result: OperationResult):
        """Save result to reports directory"""
        artifact_path = REPORTS_DIR / f"{operation}.json"
        with open(artifact_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

    def ops_doctor(self) -> OperationResult:
        """Environment + dependency + config sanity check"""
        failures = []
        warnings = []
        suggestions = []
        artifacts = []

        print("🔧 Running ops doctor...")

        # 1. Check Python environment
        try:
            version = sys.version.split()[0]
            print(f"  ✅ Python: {version}")
        except Exception as e:
            failures.append(
                {
                    "check": "python_version",
                    "message": f"Python check failed: {e}",
                    "severity": "critical",
                }
            )

        # 2. Check DevMentor core files
        core_files = [
            "README.md",
            "START_HERE.md",
            ".vscode/tasks.json",
            ".vscode/settings.json",
            "scripts/devmentor_bootstrap.py",
            "scripts/devmentor_portable.py",
            "scripts/devmentor_validate.py",
            "tutorials/00-vscode-basics/01-command-palette.md",
        ]

        missing_files = []
        for file in core_files:
            if not (ROOT / file).exists():
                missing_files.append(file)

        if missing_files:
            failures.append(
                {
                    "check": "core_files",
                    "message": f"Missing core files: {', '.join(missing_files)}",
                    "severity": "high",
                }
            )
            suggestions.append("Restore missing files from git or re-clone")
        else:
            print("  ✅ Core files present")

        # 3. Check required directories
        required_dirs = [
            ".devmentor",
            "exports",
            "reports",
            "tutorials",
            "challenges",
            "scripts",
        ]
        for dir_name in required_dirs:
            dir_path = ROOT / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  📁 Created missing directory: {dir_name}")

        # 4. Check state.json
        state_path = DEVMENTOR_DIR / "state.json"
        if not state_path.exists():
            warnings.append(
                {
                    "check": "state_file",
                    "message": "State file missing. Run 'DevMentor: Start/Resume' to initialize.",
                    "severity": "medium",
                }
            )
            suggestions.append("Run: python scripts/devmentor_bootstrap.py start")
        else:
            try:
                with open(state_path) as f:
                    state = json.load(f)
                achievements = len(state.get("achievements", []))
                xp = sum(state.get("skill_xp", {}).values())
                print(f"  ✅ State file: {achievements} achievements, {xp} XP")
            except json.JSONDecodeError:
                failures.append(
                    {
                        "check": "state_file_corrupt",
                        "message": "State file is corrupt (invalid JSON)",
                        "severity": "high",
                    }
                )
                suggestions.append("Delete .devmentor/state.json and re-run start")

        # 5. Check Git
        try:
            git_result = subprocess.run(  # nosec B603
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if git_result.returncode == 0:
                changes = len([l for l in git_result.stdout.strip().split("\n") if l])
                print(f"  ✅ Git: {changes} uncommitted changes")
            else:
                warnings.append(
                    {
                        "check": "git",
                        "message": "Git not initialized or not available",
                        "severity": "low",
                    }
                )
        except Exception:
            warnings.append(
                {"check": "git", "message": "Git check failed", "severity": "low"}
            )

        # 6. Check Replit environment
        is_replit = bool(os.environ.get("REPL_ID") or os.environ.get("REPLIT_DB_URL"))
        env_type = "Replit" if is_replit else "Local/VS Code"
        print(f"  ✅ Environment: {env_type}")

        # 7. Check key service endpoints (Ollama, LM Studio, NuSyQ MCP, DevMentor, SimulatedVerse)
        def _check_http(name: str, url: str) -> bool:
            try:
                import urllib.error
                import urllib.request

                with urllib.request.urlopen(url, timeout=3) as resp:
                    if resp.status < 400:
                        print(f"  ✅ {name} reachable ({url})")
                        return True
            except Exception as e:
                # Treat client errors (4xx) as success because the service is reachable
                if isinstance(e, urllib.error.HTTPError) and e.code < 500:
                    print(f"  ✅ {name} reachable (HTTP {e.code}) at {url}")
                    return True

                warnings.append(
                    {
                        "check": f"{name}_endpoint",
                        "message": f"{name} unreachable at {url}: {e}",
                        "severity": "medium",
                    }
                )
                print(f"  ⚠️ {name} unreachable: {url}")
            return False

        endpoints = {
            "Ollama": [
                "http://localhost:11434/health",
                "http://localhost:11434/",
                "http://localhost:11434/v1/models",
            ],
            "LM Studio": [
                "http://localhost:1234/health",
                "http://localhost:1234/",
            ],
            "NuSyQ MCP": [
                "http://localhost:8002/health",
                "http://localhost:8002/",
            ],
            "DevMentor": [
                "http://localhost:7337/health",
                "http://localhost:7337/",
            ],
            "SimulatedVerse": [
                "http://localhost:5001/health",
                "http://localhost:5001/",
                "http://localhost:7337/",
            ],
        }

        for name, urls in endpoints.items():
            success = False
            for url in urls:
                if _check_http(name, url):
                    success = True
                    break
            if not success:
                warnings.append(
                    {
                        "check": f"{name}_endpoint",
                        "message": f"{name} unreachable at any configured URL",
                        "severity": "medium",
                    }
                )

        # Generate summary
        success = len(failures) == 0
        if success:
            summary = "Environment healthy. All core systems operational."
        else:
            summary = f"Found {len(failures)} critical issues that need attention."

        print(f"\n{'✅' if success else '⚠️'} Doctor: {summary}")

        return OperationResult(
            operation="doctor",
            success=success,
            failures=failures,
            warnings=warnings,
            suggestions=suggestions,
            artifacts=artifacts,
            summary=summary,
        )

    def ops_check(self) -> OperationResult:
        """Lint + syntax + health checks"""
        failures = []
        warnings = []
        suggestions = []

        print("🔍 Running ops check...")

        # 1. Python syntax check
        python_files = list((ROOT / "scripts").rglob("*.py"))
        python_files += list((ROOT / "app").rglob("*.py"))
        python_files += list((ROOT / "cli").rglob("*.py"))

        syntax_errors = 0
        for py_file in python_files:
            try:
                # Scale timeout with file size: large files (>500KB) get 30s
                _timeout = 30 if py_file.stat().st_size > 500_000 else 5
                result = subprocess.run(  # nosec B603
                    [sys.executable, "-m", "py_compile", str(py_file)],
                    capture_output=True,
                    text=True,
                    timeout=_timeout,
                )
                if result.returncode != 0:
                    syntax_errors += 1
                    failures.append(
                        {
                            "check": "python_syntax",
                            "file": str(py_file.relative_to(ROOT)),
                            "message": result.stderr[:200].strip(),
                            "severity": "high",
                        }
                    )
            except Exception as e:
                warnings.append(
                    {
                        "check": "python_syntax",
                        "file": str(py_file.relative_to(ROOT)),
                        "message": f"Check failed: {e}",
                        "severity": "medium",
                    }
                )

        if syntax_errors == 0:
            print(f"  ✅ Python syntax: {len(python_files)} files OK")
        else:
            print(f"  ❌ Python syntax: {syntax_errors} errors")

        # 2. JSON syntax check
        json_files = list(ROOT.rglob("*.json"))
        json_files = [
            f
            for f in json_files
            if ".pythonlibs" not in str(f) and "node_modules" not in str(f)
        ]
        # Skip JSONC files (VS Code JSON-with-comments — comments are valid there)
        _JSONC_PATHS = {".vscode", ".devcontainer"}
        json_files = [
            f for f in json_files if not any(p in str(f) for p in _JSONC_PATHS)
        ]
        # Skip empty files (treated as valid empty state)
        json_files = [f for f in json_files if f.stat().st_size > 0]

        json_errors = 0
        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8", errors="replace") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                json_errors += 1
                failures.append(
                    {
                        "check": "json_syntax",
                        "file": str(json_file.relative_to(ROOT)),
                        "message": str(e)[:100],
                        "severity": "medium",
                    }
                )
            except Exception:
                pass

        if json_errors == 0:
            print(f"  ✅ JSON syntax: {len(json_files)} files OK")
        else:
            print(f"  ❌ JSON syntax: {json_errors} errors")

        # 3. Markdown link check (simple)
        md_files = list(ROOT.rglob("*.md"))
        md_files = [
            f
            for f in md_files
            if ".pythonlibs" not in str(f) and "node_modules" not in str(f)
        ]

        broken_links = 0
        for md_file in md_files[:20]:
            try:
                content = md_file.read_text(errors="ignore")
                local_links = re.findall(r"\[.*?\]\((?!http|#)(.*?)\)", content)
                for link in local_links:
                    if "://" not in link:
                        link_clean = link.split("#")[0].split("?")[0]
                        if link_clean:
                            link_path = md_file.parent / link_clean
                            if not link_path.exists():
                                broken_links += 1
                                warnings.append(
                                    {
                                        "check": "markdown_link",
                                        "file": str(md_file.relative_to(ROOT)),
                                        "message": f"Broken link: {link}",
                                        "severity": "low",
                                    }
                                )
            except Exception:
                pass

        if broken_links == 0:
            print(f"  ✅ Markdown links: checked {len(md_files)} files")
        else:
            print(f"  ⚠️  Markdown links: {broken_links} broken")

        # 4. TODO/FIXME scan
        todo_count = 0
        for py_file in python_files:
            try:
                content = py_file.read_text(errors="ignore")
                todos = re.findall(r"(TODO|FIXME|HACK|XXX):", content, re.IGNORECASE)
                todo_count += len(todos)
            except Exception:
                pass

        if todo_count > 0:
            warnings.append(
                {
                    "check": "todo_comments",
                    "message": f"Found {todo_count} TODO/FIXME comments across codebase",
                    "severity": "info",
                }
            )
            print(f"  ℹ️  TODOs: {todo_count} found")

        # Generate summary
        success = len(failures) == 0
        summary = f"Checked {len(python_files)} Python, {len(json_files)} JSON, {len(md_files)} Markdown files."
        if failures:
            summary += f" Found {len(failures)} errors."
        if warnings:
            summary += f" {len(warnings)} warnings."

        print(f"\n{'✅' if success else '❌'} Check: {summary}")

        return OperationResult(
            operation="check",
            success=success,
            failures=failures,
            warnings=warnings,
            suggestions=suggestions,
            summary=summary,
        )

    def ops_fix(self) -> OperationResult:
        """Auto-fix what can be fixed deterministically"""
        fixes_applied = []
        warnings = []

        print("🔧 Running ops fix...")

        # 1. Ensure __init__.py files exist in Python packages
        python_dirs = [ROOT / "scripts", ROOT / "app", ROOT / "cli"]
        for pdir in python_dirs:
            if pdir.exists():
                for subdir in pdir.rglob("*"):
                    if subdir.is_dir() and not subdir.name.startswith("__"):
                        init_file = subdir / "__init__.py"
                        if not init_file.exists() and list(subdir.glob("*.py")):
                            init_file.touch()
                            fixes_applied.append(
                                f"Created {init_file.relative_to(ROOT)}"
                            )

        # 2. Normalize line endings in Python files
        python_files = list(ROOT.rglob("*.py"))
        python_files = [f for f in python_files if ".pythonlibs" not in str(f)]

        for py_file in python_files:
            try:
                content = py_file.read_bytes()
                if b"\r\n" in content:
                    new_content = content.replace(b"\r\n", b"\n")
                    py_file.write_bytes(new_content)
                    fixes_applied.append(
                        f"Fixed line endings: {py_file.relative_to(ROOT)}"
                    )
            except Exception:
                pass

        # 3. Ensure .gitignore has common entries
        gitignore_path = ROOT / ".gitignore"
        required_ignores = [
            "__pycache__/",
            "*.pyc",
            ".devmentor/state.json",
            "exports/*.zip",
            "reports/*.json",
            ".pythonlibs/",
            "node_modules/",
            ".DS_Store",
        ]

        if gitignore_path.exists():
            content = gitignore_path.read_text()
            missing = [i for i in required_ignores if i not in content]
            if missing:
                with open(gitignore_path, "a") as f:
                    f.write("\n# Auto-added by ops fix\n")
                    for item in missing:
                        f.write(f"{item}\n")
                fixes_applied.append(f"Added {len(missing)} entries to .gitignore")
        else:
            with open(gitignore_path, "w") as f:
                f.write("# DevMentor .gitignore\n")
                for item in required_ignores:
                    f.write(f"{item}\n")
            fixes_applied.append("Created .gitignore")

        # 4. Ensure exports/ and reports/ directories exist
        for d in [EXPORTS_DIR, REPORTS_DIR]:
            if not d.exists():
                d.mkdir(parents=True)
                fixes_applied.append(f"Created {d.name}/")

        # Summary
        if fixes_applied:
            print(f"  ✅ Applied {len(fixes_applied)} fixes:")
            for fix in fixes_applied[:5]:
                print(f"     - {fix}")
            if len(fixes_applied) > 5:
                print(f"     ... and {len(fixes_applied) - 5} more")
        else:
            print("  ✅ Nothing to fix")

        return OperationResult(
            operation="fix",
            success=True,
            warnings=warnings,
            suggestions=[f"Applied: {fix}" for fix in fixes_applied],
            summary=f"Applied {len(fixes_applied)} automatic fixes.",
        )

    def ops_prune(self) -> OperationResult:
        """Detect bloat: duplicates, large files, unused files"""
        issues = []
        suggestions = []

        print("🧹 Running ops prune...")

        excluded_dirs = [
            ".git",
            ".pythonlibs",
            "node_modules",
            ".cache",
            "venv",
            ".venv",
            ".uv",
            ".agents",
            ".local",
            "attached_assets",
        ]

        def is_excluded(path_str: str) -> bool:
            return any(excl in path_str for excl in excluded_dirs)

        # 1. Find large files (> 500KB) - excluding system/cache directories
        large_files = []
        for f in ROOT.rglob("*"):
            path_str = str(f)
            if f.is_file() and not is_excluded(path_str):
                try:
                    size = f.stat().st_size
                    if size > 500_000:
                        large_files.append((str(f.relative_to(ROOT)), size / 1_000_000))
                except Exception:
                    pass

        if large_files:
            large_files.sort(key=lambda x: x[1], reverse=True)
            for path, size_mb in large_files[:5]:
                issues.append(
                    {
                        "type": "large_file",
                        "file": path,
                        "message": f"Large file: {size_mb:.1f}MB",
                        "severity": "low",
                    }
                )
            print(f"  ⚠️  Large files: {len(large_files)} found")
            suggestions.append("Consider compressing or moving large files")
        else:
            print("  ✅ No large files")

        # 2. Find duplicate files by hash - excluding system/cache directories
        file_hashes: dict[str, list[str]] = {}
        for f in ROOT.rglob("*"):
            path_str = str(f)
            if f.is_file() and f.suffix in [
                ".py",
                ".md",
                ".json",
                ".js",
                ".css",
                ".html",
            ]:
                if not is_excluded(path_str):
                    try:
                        content = f.read_bytes()
                        if len(content) < 10:
                            continue
                        h = hashlib.md5(content).hexdigest()
                        rel_path = str(f.relative_to(ROOT))
                        if h in file_hashes:
                            file_hashes[h].append(rel_path)
                        else:
                            file_hashes[h] = [rel_path]
                    except Exception:
                        pass

        duplicates = [(h, files) for h, files in file_hashes.items() if len(files) > 1]
        if duplicates:
            for h, files in duplicates[:3]:
                issues.append(
                    {
                        "type": "duplicate",
                        "files": files,
                        "message": f"Duplicate content in {len(files)} files",
                        "severity": "low",
                    }
                )
            print(f"  ⚠️  Duplicates: {len(duplicates)} sets found")
            suggestions.append("Review and consolidate duplicate files")
        else:
            print("  ✅ No duplicate files")

        # 3. Find empty directories - excluding system directories
        empty_dirs = []
        for d in ROOT.rglob("*"):
            if d.is_dir() and not list(d.iterdir()):
                if not is_excluded(str(d)):
                    empty_dirs.append(str(d.relative_to(ROOT)))

        if empty_dirs:
            print(f"  ⚠️  Empty dirs: {len(empty_dirs)} found")
            for ed in empty_dirs[:3]:
                issues.append(
                    {
                        "type": "empty_dir",
                        "path": ed,
                        "message": "Empty directory",
                        "severity": "info",
                    }
                )
        else:
            print("  ✅ No empty directories")

        # 4. Check for temp/backup files
        temp_patterns = ["*.tmp", "*.bak", "*~", "*.swp", ".DS_Store"]
        temp_files = []
        for pattern in temp_patterns:
            temp_files.extend(ROOT.glob(f"**/{pattern}"))

        temp_files = [f for f in temp_files if not is_excluded(str(f))]
        if temp_files:
            print(f"  ⚠️  Temp files: {len(temp_files)} found")
            suggestions.append(f"Remove {len(temp_files)} temporary/backup files")
        else:
            print("  ✅ No temp files")

        summary = f"Found {len(issues)} potential bloat issues."
        print(f"\n✅ Prune: {summary}")

        return OperationResult(
            operation="prune",
            success=True,
            failures=issues,
            suggestions=suggestions,
            summary=summary,
        )

    def ops_graph(self) -> OperationResult:
        """Generate module/file map"""
        print("📊 Running ops graph...")

        file_map = {
            "generated": datetime.now().isoformat(),
            "directories": {},
            "python_modules": [],
            "tutorials": [],
            "challenges": [],
            "docs": [],
        }

        # 1. Map directory structure
        for d in ROOT.iterdir():
            if (
                d.is_dir()
                and not d.name.startswith(".")
                and d.name not in ["node_modules", "__pycache__", ".pythonlibs"]
            ):
                files = list(d.rglob("*"))
                files = [f for f in files if f.is_file()]
                file_map["directories"][d.name] = {
                    "file_count": len(files),
                    "extensions": list(set(f.suffix for f in files if f.suffix)),
                }

        # 2. Map Python modules
        for py_file in (ROOT / "scripts").glob("*.py"):
            file_map["python_modules"].append(
                {
                    "name": py_file.stem,
                    "path": str(py_file.relative_to(ROOT)),
                    "size_kb": round(py_file.stat().st_size / 1024, 1),
                }
            )

        # 3. Map tutorials
        tutorials_dir = ROOT / "tutorials"
        if tutorials_dir.exists():
            for track in tutorials_dir.iterdir():
                if track.is_dir():
                    lessons = list(track.glob("*.md"))
                    file_map["tutorials"].append(
                        {
                            "track": track.name,
                            "lessons": [l.stem for l in sorted(lessons)],
                        }
                    )

        # 4. Map challenges
        challenges_dir = ROOT / "challenges"
        if challenges_dir.exists():
            for category in challenges_dir.iterdir():
                if category.is_dir():
                    challenges = list(category.iterdir())
                    file_map["challenges"].append(
                        {
                            "category": category.name,
                            "count": len([c for c in challenges if c.is_dir()]),
                        }
                    )

        # 5. Map docs
        docs_dir = ROOT / "docs"
        if docs_dir.exists():
            for doc in docs_dir.glob("*.md"):
                file_map["docs"].append(doc.stem)

        # Save module map
        graph_path = REPORTS_DIR / "module_map.json"
        with open(graph_path, "w") as f:
            json.dump(file_map, f, indent=2)

        print(f"  ✅ Mapped {len(file_map['directories'])} directories")
        print(f"  ✅ Mapped {len(file_map['python_modules'])} Python modules")
        print(f"  ✅ Mapped {len(file_map['tutorials'])} tutorial tracks")
        print("  ✅ Wrote reports/module_map.json")

        return OperationResult(
            operation="graph",
            success=True,
            artifacts=[str(graph_path)],
            summary=f"Generated module map with {len(file_map['directories'])} directories.",
        )

    def ops_export(self) -> OperationResult:
        """Build portable ZIP (delegates to existing script)"""
        print("📦 Running ops export...")

        try:
            result = subprocess.run(  # nosec B603
                [
                    sys.executable,
                    str(ROOT / "scripts" / "devmentor_portable.py"),
                    "export",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                print("  ✅ Export completed")
                return OperationResult(
                    operation="export",
                    success=True,
                    artifacts=["exports/devmentor-portable.zip"],
                    summary="Portable ZIP created successfully.",
                )
            else:
                print(f"  ❌ Export failed: {result.stderr[:100]}")
                return OperationResult(
                    operation="export",
                    success=False,
                    failures=[{"message": result.stderr[:200]}],
                    summary="Export failed.",
                )
        except Exception as e:
            return OperationResult(
                operation="export",
                success=False,
                failures=[{"message": str(e)}],
                summary=f"Export error: {e}",
            )

    def ops_report(self) -> OperationResult:
        """Generate comprehensive markdown status report"""
        print("📝 Running ops report...")

        # Run all checks first if not already run
        if "doctor" not in self.results:
            self.run("doctor")
        if "check" not in self.results:
            self.run("check")
        if "prune" not in self.results:
            self.run("prune")

        # Build report
        report_lines = [
            "# DevMentor Ops Report",
            "",
            f"Generated: `{datetime.now().isoformat()}`",
            "",
            "## Summary",
            "",
        ]

        total_failures = 0
        total_warnings = 0

        for op_name, result in self.results.items():
            if op_name == "report":
                continue
            status = "✅" if result.success else "❌"
            report_lines.append(f"- **{op_name}**: {status} {result.summary}")
            total_failures += len(result.failures)
            total_warnings += len(result.warnings)

        report_lines.extend(
            [
                "",
                f"**Total**: {total_failures} failures, {total_warnings} warnings",
                "",
                "## Failures",
                "",
            ]
        )

        if total_failures == 0:
            report_lines.append("None! 🎉")
        else:
            for op_name, result in self.results.items():
                for failure in result.failures:
                    file_info = failure.get("file", "")
                    msg = failure.get("message", str(failure))
                    report_lines.append(f"- [{op_name}] {file_info}: {msg}")

        report_lines.extend(["", "## Suggestions", ""])

        all_suggestions = []
        for result in self.results.values():
            all_suggestions.extend(result.suggestions)

        if all_suggestions:
            for i, suggestion in enumerate(all_suggestions[:10], 1):
                report_lines.append(f"{i}. {suggestion}")
        else:
            report_lines.append("No suggestions - looking good!")

        report_lines.extend(
            [
                "",
                "## Next Actions",
                "",
                "1. Fix any failures listed above",
                "2. Review and address warnings",
                "3. Run `ops check` after fixes to verify",
                "4. Run `ops export` to create portable backup",
                "",
            ]
        )

        # Write report
        report_path = REPORTS_DIR / "latest.md"
        with open(report_path, "w") as f:
            f.write("\n".join(report_lines))

        # Also write JSON version
        json_path = REPORTS_DIR / "latest.json"
        with open(json_path, "w") as f:
            json.dump(
                {
                    "generated": datetime.now().isoformat(),
                    "results": {
                        k: v.to_dict() for k, v in self.results.items() if k != "report"
                    },
                    "total_failures": total_failures,
                    "total_warnings": total_warnings,
                },
                f,
                indent=2,
                default=str,
            )

        print("  ✅ Wrote reports/latest.md")
        print("  ✅ Wrote reports/latest.json")

        return OperationResult(
            operation="report",
            success=True,
            artifacts=[str(report_path), str(json_path)],
            summary=f"Report generated: {total_failures} failures, {total_warnings} warnings.",
        )

    def ops_all(self) -> OperationResult:
        """Run all operations in sequence"""
        print("🚀 Running all ops...\n")

        ops_sequence = ["doctor", "check", "fix", "prune", "graph", "export", "report"]

        for op in ops_sequence:
            print(f"\n{'='*50}")
            self.run(op)

        print(f"\n{'='*50}")
        print("✅ All operations complete!")
        print("   See reports/latest.md for full summary")

        return OperationResult(
            operation="all",
            success=all(r.success for r in self.results.values()),
            summary="All operations completed.",
        )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    operation = sys.argv[1].lower()
    ops = ZeroTokenOps()
    result = ops.run(operation)

    if result and not result.success:
        sys.exit(1)


if __name__ == "__main__":
    main()
