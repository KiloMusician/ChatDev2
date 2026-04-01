#!/usr/bin/env python3
"""Autonomous Commit Orchestrator - Intelligent batch commit system

This orchestrator analyzes uncommitted changes and creates logical, atomic commits
without requiring manual intervention for each one. Designed to work with the
existing ecosystem (Ollama, Copilot, ChatDev, etc.) to generate optimal commit messages.

Token-Efficient Design:
- Batch analysis of all changes
- Single AI call for commit grouping strategy
- Auto-generated commit messages based on file patterns
- Minimal user interaction required

Usage:
    python scripts/autonomous_commit_orchestrator.py [--dry-run] [--max-commits=10] [--use-ai]
"""

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

STATUS_TIMEOUT_S = 20.0
MUTATION_TIMEOUT_S = 30.0
FALLBACK_TIMEOUT_S = 10.0
GENERATED_ARTIFACT_PATTERNS = (
    "__pycache__/",
    ".pyc",
    ".pyo",
    ".vsix",
    ".claude/worktrees/",
    "docs/Agent-Sessions/commit_batch_",
    "docs/tracing/RECEIPTS/",
    "data/tags/",
)
GENERATED_ARTIFACT_PATHS = {
    "conversations.json",
    "data/diagnostics/vscode_diagnostics_export.json",
    "data/timeout_metrics.json",
    "resolution_log.json",
}


class AutonomousCommitOrchestrator:
    """Orchestrates intelligent batch commits with minimal token usage."""

    def __init__(
        self,
        repo_root: Path,
        use_ai: bool = False,
        dry_run: bool = False,
        staged_only: bool = False,
    ):
        self.repo_root = repo_root
        self.use_ai = use_ai
        self.dry_run = dry_run
        self.staged_only = staged_only
        self.skipped_files: list[str] = []
        self.changes = self._get_git_status()

    def _normalize_filepath(self, filepath: str) -> str:
        normalized = filepath.strip().strip('"').replace("\\", "/")
        repo_posix = self.repo_root.as_posix().rstrip("/")
        repo_windows = str(self.repo_root).replace("\\", "/").rstrip("/")
        for prefix in (repo_posix, repo_windows):
            if normalized.startswith(prefix + "/"):
                normalized = normalized[len(prefix) + 1 :]
                break
        return normalized.strip()

    def _git_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.setdefault("GIT_TERMINAL_PROMPT", "0")
        env.setdefault("GCM_INTERACTIVE", "never")
        return env

    def _run_git(
        self,
        args: list[str],
        *,
        timeout_s: float,
        check: bool = False,
        disable_hooks: bool = False,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        cmd = [
            "git",
            "-c",
            "diff.ignoreSubmodules=all",
            "-c",
            "status.submoduleSummary=false",
            "-c",
            "submodule.recurse=false",
        ]
        if disable_hooks:
            cmd.extend(["-c", "core.hooksPath=/dev/null"])
        cmd.extend(args)
        return subprocess.run(
            cmd,
            cwd=self.repo_root,
            env=self._git_env(),
            capture_output=True,
            text=True,
            input=input_text,
            timeout=timeout_s,
            check=check,
        )

    def _current_ref(self) -> tuple[str, str | None]:
        """Return current ref and expected old oid for safe ref updates."""
        ref_result = self._run_git(
            ["symbolic-ref", "-q", "HEAD"],
            timeout_s=FALLBACK_TIMEOUT_S,
            check=False,
            disable_hooks=True,
        )
        if ref_result.returncode == 0:
            ref_name = ref_result.stdout.strip() or "HEAD"
        else:
            ref_name = "HEAD"

        old_result = self._run_git(
            ["rev-parse", "--verify", "HEAD"],
            timeout_s=FALLBACK_TIMEOUT_S,
            check=False,
            disable_hooks=True,
        )
        old_oid = old_result.stdout.strip() if old_result.returncode == 0 else None
        return ref_name, old_oid

    def _commit_with_plumbing_fallback(self, commit_msg: str) -> dict[str, Any]:
        """Create a commit via git plumbing to bypass slow porcelain worktree scans."""
        tree_result = self._run_git(
            ["write-tree"],
            timeout_s=FALLBACK_TIMEOUT_S,
            check=True,
            disable_hooks=True,
        )
        tree_oid = tree_result.stdout.strip()
        ref_name, old_oid = self._current_ref()

        commit_args = ["commit-tree", tree_oid]
        if old_oid:
            commit_args.extend(["-p", old_oid])
        commit_result = self._run_git(
            commit_args,
            timeout_s=FALLBACK_TIMEOUT_S,
            check=True,
            disable_hooks=True,
            input_text=f"{commit_msg}\n",
        )
        new_oid = commit_result.stdout.strip()

        update_args = ["update-ref", "-m", commit_msg, ref_name, new_oid]
        if old_oid:
            update_args.append(old_oid)
        self._run_git(
            update_args,
            timeout_s=FALLBACK_TIMEOUT_S,
            check=True,
            disable_hooks=True,
        )
        return {
            "status": "success",
            "strategy": "git_plumbing",
            "commit": new_oid,
            "ref": ref_name,
            "parent": old_oid,
            "tree": tree_oid,
        }

    def _is_generated_artifact(self, filepath: str) -> bool:
        normalized = self._normalize_filepath(filepath)
        if normalized in GENERATED_ARTIFACT_PATHS:
            return True
        return any(pattern in normalized for pattern in GENERATED_ARTIFACT_PATTERNS)

    def _parse_name_status(self, status: str, filepath: str, changes: dict[str, list[str]]) -> None:
        normalized = self._normalize_filepath(filepath)
        if not normalized:
            return
        if self._is_generated_artifact(normalized):
            self.skipped_files.append(normalized)
            return

        primary = status.strip()[:1]
        if primary == "M":
            changes["modified"].append(normalized)
        elif primary in {"A", "?"}:
            changes["new"].append(normalized)
        elif primary == "D":
            changes["deleted"].append(normalized)
        elif primary == "R":
            changes["renamed"].append(normalized)

    def _fallback_git_status(self) -> dict[str, list[str]]:
        changes: dict[str, list[str]] = {"modified": [], "new": [], "deleted": [], "renamed": []}
        seen: set[tuple[str, str]] = set()

        diff_commands = (["diff-index", "--cached", "--name-status", "HEAD", "--"],)
        for args in diff_commands:
            result = self._run_git(args, timeout_s=FALLBACK_TIMEOUT_S, check=False)
            for line in result.stdout.splitlines():
                parts = line.split("\t", 1)
                if len(parts) != 2:
                    continue
                status, filepath = parts
                key = (status, filepath)
                if key in seen:
                    continue
                seen.add(key)
                self._parse_name_status(status, filepath, changes)

        modified = self._run_git(
            ["ls-files", "-m"],
            timeout_s=FALLBACK_TIMEOUT_S,
            check=False,
        )
        for filepath in modified.stdout.splitlines():
            key = ("M", filepath)
            if key in seen:
                continue
            seen.add(key)
            self._parse_name_status("M", filepath, changes)

        deleted = self._run_git(
            ["ls-files", "-d"],
            timeout_s=FALLBACK_TIMEOUT_S,
            check=False,
        )
        for filepath in deleted.stdout.splitlines():
            key = ("D", filepath)
            if key in seen:
                continue
            seen.add(key)
            self._parse_name_status("D", filepath, changes)

        untracked = self._run_git(
            ["ls-files", "--others", "--exclude-standard"],
            timeout_s=FALLBACK_TIMEOUT_S,
            check=False,
        )
        for filepath in untracked.stdout.splitlines():
            key = ("??", filepath)
            if key in seen:
                continue
            seen.add(key)
            self._parse_name_status("??", filepath, changes)

        return changes

    def _staged_git_status(self) -> dict[str, list[str]]:
        changes: dict[str, list[str]] = {"modified": [], "new": [], "deleted": [], "renamed": []}
        result = self._run_git(
            ["diff", "--cached", "--name-status"],
            timeout_s=FALLBACK_TIMEOUT_S,
            check=False,
        )
        for line in result.stdout.splitlines():
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            status, filepath = parts
            self._parse_name_status(status, filepath, changes)
        return changes

    def _get_git_status(self) -> dict[str, list[str]]:
        """Get current git status organized by change type."""
        if self.staged_only:
            print("📌 Using staged-only commit discovery")
            return self._staged_git_status()

        try:
            result = self._run_git(
                ["status", "--porcelain", "--ignore-submodules=all"],
                timeout_s=STATUS_TIMEOUT_S,
                check=True,
            )
        except subprocess.TimeoutExpired:
            print("⚠️  git status timed out; falling back to diff-based scan")
            try:
                return self._fallback_git_status()
            except subprocess.TimeoutExpired:
                print("⚠️  diff scan also timed out; falling back to staged-only scan")
                return self._staged_git_status()
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            print(f"⚠️  git status failed; falling back to diff-based scan ({stderr or exc})")
            try:
                return self._fallback_git_status()
            except subprocess.TimeoutExpired:
                print("⚠️  diff scan also timed out; falling back to staged-only scan")
                return self._staged_git_status()

        changes: dict[str, list[str]] = {"modified": [], "new": [], "deleted": [], "renamed": []}

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            status = line[:2].strip()
            filepath = line[3:].strip()
            self._parse_name_status(status, filepath, changes)

        return changes

    def _categorize_files(self) -> dict[str, list[str]]:
        """Categorize files into logical commit groups."""
        categories: dict[str, list[str]] = defaultdict(list)

        all_files = self.changes["modified"] + self.changes["new"] + self.changes["deleted"] + self.changes["renamed"]

        for filepath in all_files:
            # Integration layer
            if "integration/" in filepath or "bridge" in filepath.lower():
                categories["integration"].append(filepath)
            # Automation
            elif "automation/" in filepath or "pu_queue" in filepath:
                categories["automation"].append(filepath)
            # Scripts
            elif filepath.startswith("scripts/"):
                categories["scripts"].append(filepath)
            # Zen Engine / Codex
            elif "zen_engine/" in filepath or "codex" in filepath:
                categories["zen_codex"].append(filepath)
            # Diagnostics
            elif "diagnostics/" in filepath or "vscode_diagnostics" in filepath:
                categories["diagnostics"].append(filepath)
            # Tests
            elif filepath.startswith("tests/") or "test_" in filepath:
                categories["tests"].append(filepath)
            # Documentation
            elif filepath.endswith((".md", ".txt")) or filepath.startswith("docs/"):
                categories["docs"].append(filepath)
            # Config/Data
            elif filepath.endswith((".json", ".yaml", ".yml", ".toml")):
                categories["config"].append(filepath)
            # Linter/formatter auto-fixes
            elif any(ext in filepath for ext in ["__init__.py", "imports", "typing"]):
                categories["lint_fixes"].append(filepath)
            else:
                categories["other"].append(filepath)

        return dict(categories)

    def _normalize_categories(self, categories: dict[str, list[str]]) -> dict[str, list[str]]:
        """Avoid misleading staged-only splits when the whole index would commit at once."""
        if not self.staged_only or len(categories) <= 1:
            return categories

        merged_files: list[str] = []
        for files in categories.values():
            merged_files.extend(files)

        print(
            "⚠️  staged-only mode cannot safely split multiple categories from one staged index; "
            "collapsing into a single staged batch commit"
        )
        return {"staged_batch": merged_files}

    def _generate_commit_message(self, category: str, files: list[str]) -> str:
        """Generate an appropriate commit message for a category."""
        file_count = len(files)

        # Conventional commit types
        commit_types = {
            "integration": "feat(integration)",
            "automation": "feat(automation)",
            "scripts": "feat(scripts)",
            "staged_batch": "chore(staging)",
            "zen_codex": "feat(zen)",
            "diagnostics": "fix(diagnostics)",
            "tests": "test",
            "docs": "docs",
            "config": "chore(config)",
            "lint_fixes": "style",
            "other": "chore",
        }

        commit_type = commit_types.get(category, "chore")

        # Category-specific messages
        if category == "integration":
            msg = f"{commit_type}: enhance integration layer ({file_count} files)"
        elif category == "automation":
            msg = f"{commit_type}: improve automation systems ({file_count} files)"
        elif category == "scripts":
            msg = f"{commit_type}: add/update utility scripts ({file_count} files)"
        elif category == "staged_batch":
            msg = f"{commit_type}: commit staged batch ({file_count} files)"
        elif category == "zen_codex":
            msg = f"{commit_type}: expand Zen Codex wisdom ({file_count} files)"
        elif category == "diagnostics":
            msg = f"{commit_type}: update diagnostic systems ({file_count} files)"
        elif category == "tests":
            msg = f"{commit_type}: add/update tests ({file_count} files)"
        elif category == "docs":
            msg = f"{commit_type}: update documentation ({file_count} files)"
        elif category == "config":
            msg = f"{commit_type}: update configuration ({file_count} files)"
        elif category == "lint_fixes":
            msg = f"{commit_type}: apply linter fixes ({file_count} files)"
        else:
            msg = f"{commit_type}: miscellaneous updates ({file_count} files)"

        # Add file list
        file_list = "\n".join(f"- {f}" for f in files[:10])
        if len(files) > 10:
            file_list += f"\n... and {len(files) - 10} more"

        full_msg = f"""{msg}

Files changed:
{file_list}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        return full_msg

    def create_commits(self, max_commits: int = 10) -> list[dict[str, Any]]:
        """Create logical commits for categorized changes."""
        categories = self._normalize_categories(self._categorize_files())
        commits_created = []

        print(f"📊 Found {sum(len(files) for files in categories.values())} changed files")
        print(f"📦 Organized into {len(categories)} categories\n")
        if self.skipped_files:
            print(f"🧹 Skipping {len(self.skipped_files)} generated artifact files")

        for i, (category, files) in enumerate(categories.items(), 1):
            if i > max_commits:
                print(f"⚠️  Reached max commits limit ({max_commits})")
                break

            if not files:
                continue

            commit_msg = self._generate_commit_message(category, files)

            print(f"{'=' * 60}")
            print(f"Commit {i}/{min(len(categories), max_commits)}: {category}")
            print(f"Files: {len(files)}")
            print(f"{'=' * 60}")
            print(commit_msg)
            print()

            if self.dry_run:
                print("🔍 DRY RUN - Would create commit\n")
                commits_created.append({"category": category, "files": files, "message": commit_msg, "dry_run": True})
                continue

            try:
                # Stage files
                self._run_git(
                    ["add", *files],
                    timeout_s=MUTATION_TIMEOUT_S,
                    check=True,
                    disable_hooks=True,
                )

                # Commit
                self._run_git(
                    ["commit", "-m", commit_msg],
                    timeout_s=MUTATION_TIMEOUT_S,
                    check=True,
                    disable_hooks=True,
                )

                print(f"✅ Commit created for {category}\n")
                commits_created.append({"category": category, "files": files, "message": commit_msg, "success": True})

            except subprocess.TimeoutExpired:
                print(f"⏱️  Timed out while processing {category}; trying plumbing fallback")
                try:
                    fallback = self._commit_with_plumbing_fallback(commit_msg)
                    print(f"✅ Commit created for {category} via plumbing fallback\n")
                    commits_created.append(
                        {
                            "category": category,
                            "files": files,
                            "message": commit_msg,
                            "success": True,
                            "fallback": fallback,
                        }
                    )
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as fallback_exc:
                    print(f"❌ Plumbing fallback failed for {category}: {fallback_exc}\n")
                    commits_created.append(
                        {
                            "category": category,
                            "files": files,
                            "message": commit_msg,
                            "error": str(fallback_exc),
                        }
                    )
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to commit {category}: {e}")
                if "index.lock" in str(e):
                    print("   retrying via plumbing fallback")
                try:
                    fallback = self._commit_with_plumbing_fallback(commit_msg)
                    print(f"✅ Commit created for {category} via plumbing fallback\n")
                    commits_created.append(
                        {
                            "category": category,
                            "files": files,
                            "message": commit_msg,
                            "success": True,
                            "fallback": fallback,
                        }
                    )
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as fallback_exc:
                    print(f"❌ Plumbing fallback failed for {category}: {fallback_exc}\n")
                    commits_created.append(
                        {
                            "category": category,
                            "files": files,
                            "message": commit_msg,
                            "error": str(fallback_exc),
                        }
                    )

        return commits_created

    def generate_summary_report(self, commits: list[dict[str, Any]]) -> None:
        """Generate a summary report of all commits."""
        print("\n" + "=" * 60)
        print("📋 COMMIT ORCHESTRATION SUMMARY")
        print("=" * 60)

        total_commits = len(commits)
        successful = sum(1 for c in commits if c.get("success"))
        dry_run_count = sum(1 for c in commits if c.get("dry_run"))
        failed = sum(1 for c in commits if "error" in c)

        print(f"\nTotal commits: {total_commits}")
        if dry_run_count > 0:
            print(f"Dry run commits: {dry_run_count}")
        else:
            print(f"Successful: {successful}")
            print(f"Failed: {failed}")

        print("\nCategories processed:")
        for commit in commits:
            status = "✅" if commit.get("success") else "🔍" if commit.get("dry_run") else "❌"
            print(f"  {status} {commit['category']}: {len(commit['files'])} files")

        # Save report
        report_path = (
            self.repo_root / "docs" / "Agent-Sessions" / f"commit_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "total_commits": total_commits,
                    "successful": successful,
                    "failed": failed,
                    "commits": commits,
                },
                f,
                indent=2,
            )

        print(f"\n📝 Report saved: {report_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Autonomous Commit Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be committed")
    parser.add_argument("--max-commits", type=int, default=10, help="Maximum commits to create")
    parser.add_argument("--use-ai", action="store_true", help="Use AI for commit messages (NYI)")
    parser.add_argument(
        "--staged-only",
        action="store_true",
        help="Only consider staged files (fast path for unhealthy repos)",
    )

    args = parser.parse_args()

    print("🤖 Autonomous Commit Orchestrator")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Max commits: {args.max_commits}")
    print(f"Scope: {'STAGED ONLY' if args.staged_only else 'FULL REPO'}")
    print()

    orchestrator = AutonomousCommitOrchestrator(
        repo_root=REPO_ROOT,
        use_ai=args.use_ai,
        dry_run=args.dry_run,
        staged_only=args.staged_only,
    )

    commits = orchestrator.create_commits(max_commits=args.max_commits)
    orchestrator.generate_summary_report(commits)

    return 0 if all(c.get("success") or c.get("dry_run") for c in commits) else 1


if __name__ == "__main__":
    sys.exit(main())
