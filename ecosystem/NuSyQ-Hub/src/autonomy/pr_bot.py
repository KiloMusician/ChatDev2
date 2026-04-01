"""PR Bot - Orchestrate autonomous PR creation and merging.

This module implements the complete autonomous feedback loop:
1. Extract patches from LLM response
2. Apply patches to filesystem
3. Run tests to validate
4. Score risk and determine governance policy
5. Create PR or proposal based on risk level
6. Log results back to quest system
"""

import asyncio
import contextlib
import importlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

aiofiles: Any | None
try:
    aiofiles = importlib.import_module("aiofiles")
except ImportError:
    aiofiles = None

from src.autonomy.patch_builder import PatchBuilder, PatchSet
from src.autonomy.risk_scorer import ApprovalPolicy, RiskScorer

logger = logging.getLogger(__name__)


@dataclass
class AutonomousWorkflowResult:
    """Result from autonomous workflow execution."""

    success: bool
    patch_id: str
    action_taken: str  # "pr_created", "proposal_created", "blocked", "failed"
    pr_url: str | None = None
    risk_score: float | None = None
    risk_level: str | None = None
    errors: list[str] | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        """Implement __post_init__."""
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)
        if self.errors is None:
            self.errors = []


class GitHubPRBot:
    """Orchestrate autonomous PR creation and merging."""

    def __init__(
        self,
        repo_root: Path | None = None,
        github_token: str | None = None,
        repo_owner: str = "KiloMusician",
        repo_name: str = "NuSyQ-Hub",
    ):
        """Initialize PR Bot.

        Args:
            repo_root: Repository root directory
            github_token: GitHub API token (from env if not provided)
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
        """
        self.repo_root = repo_root or Path.cwd()
        self.github_token = github_token or self._get_github_token()
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.patch_builder = PatchBuilder(repo_root=self.repo_root)
        self.risk_scorer = RiskScorer()
        logger.info(f"GitHubPRBot initialized: {repo_owner}/{repo_name}")

    def _get_github_token(self) -> str | None:
        """Get GitHub token from environment."""
        import os

        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if not token:
            logger.warning("No GitHub token found in environment")
        return token

    async def process_llm_response(
        self, task_id: str, llm_response: str, task_description: str = "Autonomous task"
    ) -> dict:
        """Process LLM response through complete autonomous workflow.

        Workflow:
        1. Extract patches from LLM response
        2. Apply patches to filesystem
        3. Run tests
        4. Score risk
        5. Create PR or proposal
        6. Log result

        Args:
            task_id: Unique task identifier
            llm_response: Raw LLM output (code, diffs, JSON operations)
            task_description: Description of the task for PR title/body

        Returns:
            Dictionary with workflow result
        """
        patch_id = f"patch_{task_id}_{int(datetime.now(UTC).timestamp())}"
        patchset = PatchSet(patch_id=patch_id, description=task_description)

        try:
            # Step 1: Extract patches
            logger.info(f"[{patch_id}] Extracting patches from LLM response")
            patches = self._extract_patches_from_response(llm_response)

            if not patches:
                return {
                    "success": False,
                    "patch_id": patch_id,
                    "action_taken": "failed",
                    "error": "No patches extracted from LLM response",
                }

            for patch in patches:
                patchset.add_patch(patch)
            logger.info(f"[{patch_id}] Extracted {len(patches)} patches")

            # Step 2: Validate patches
            if not patchset.validate_all():
                return {
                    "success": False,
                    "patch_id": patch_id,
                    "action_taken": "failed",
                    "errors": patchset.errors,
                }

            # Step 3: Apply patches
            logger.info(f"[{patch_id}] Applying patches to filesystem")
            success, apply_errors = await self.patch_builder.apply_patches(patchset)

            if not success:
                logger.warning(f"[{patch_id}] Apply errors: {apply_errors}")
                patchset.errors.extend(apply_errors)
                return {
                    "success": False,
                    "patch_id": patch_id,
                    "action_taken": "failed",
                    "errors": apply_errors,
                }

            # Step 4: Run tests
            logger.info(f"[{patch_id}] Running tests")
            test_passed, _ = await self.patch_builder.run_tests(patchset)

            # Step 5: Format code
            logger.info(f"[{patch_id}] Formatting code")
            await self.patch_builder.format_code(patchset)

            # Step 6: Score risk
            logger.info(f"[{patch_id}] Scoring risk")
            assessment = self.risk_scorer.score(patchset)
            risk_report = self.risk_scorer.generate_governance_report(assessment)
            logger.info(
                f"[{patch_id}] Risk: {assessment.risk_level.value} ({assessment.risk_score:.2f})"
            )

            # Step 7: Create PR or proposal
            result_data = {
                "success": True,
                "patch_id": patch_id,
                "risk_score": assessment.risk_score,
                "risk_level": assessment.risk_level.value,
                "approval_policy": assessment.approval_policy.value,
                "test_passed": test_passed,
                "files_changed": len(patchset.patches),
            }

            if assessment.approval_policy == ApprovalPolicy.BLOCKED:
                logger.warning(f"[{patch_id}] Patch blocked - creating proposal")
                proposal_path = self._create_proposal_package(
                    patchset, assessment, risk_report, task_description
                )
                result_data["action_taken"] = "blocked"
                result_data["proposal_path"] = str(proposal_path)

            else:
                # Create PR
                logger.info(f"[{patch_id}] Creating PR")
                pr_url = await self._create_github_pr(
                    patchset, assessment, risk_report, task_description
                )

                if pr_url:
                    result_data["action_taken"] = "pr_created"
                    result_data["pr_url"] = pr_url
                    result_data["auto_merge"] = assessment.approval_policy == ApprovalPolicy.AUTO
                else:
                    result_data["action_taken"] = "failed"
                    result_data["error"] = "Failed to create PR"

            # Step 8: Log to quest system
            await self._log_to_quest(result_data)

            return result_data

        except Exception as e:
            logger.error(f"[{patch_id}] Workflow failed: {e}", exc_info=True)
            return {
                "success": False,
                "patch_id": patch_id,
                "action_taken": "failed",
                "error": str(e),
            }

    def _extract_patches_from_response(self, response: str) -> list:
        """Extract patches from LLM response in various formats."""
        patches = []

        # Try JSON format first
        with contextlib.suppress(Exception):
            patches.extend(self.patch_builder.extract_file_operations(response))

        # Try unified diff format
        if "---" in response and "+++" in response:
            patches.extend(self.patch_builder.parse_unified_diff(response))

        # Try markdown code blocks
        code_blocks = self.patch_builder.extract_code_blocks(response)
        # Convert code blocks to patches (heuristic)
        for block in code_blocks:
            if block.language in ("python", "typescript", "javascript", "bash"):
                # Try to infer file path from context
                patches.extend(self.patch_builder.extract_file_operations(block.content))

        return patches

    async def _create_github_pr(
        self, patchset: PatchSet, assessment, risk_report: str, task_description: str
    ) -> str | None:
        """Create a GitHub PR for the patch set.

        Uses GitHub CLI or API to create PR.
        """
        try:
            branch_name = self._create_branch_name(task_description)

            # Get current branch
            proc = await asyncio.create_subprocess_exec(
                "git",
                "rev-parse",
                "--abbrev-ref",
                "HEAD",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_root),
            )
            stdout, _ = await proc.communicate()
            base_branch = stdout.decode().strip() or "master" if stdout else "master"

            # Create and checkout new branch
            logger.info(f"Creating branch: {branch_name}")
            proc = await asyncio.create_subprocess_exec(
                "git",
                "checkout",
                "-b",
                branch_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_root),
            )
            await proc.wait()

            # Commit changes
            logger.info("Committing patches")
            proc = await asyncio.create_subprocess_exec(
                "git",
                "add",
                "-A",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_root),
            )
            await proc.wait()

            commit_message = f"feat({patchset.patch_id}): {task_description}\n\n{risk_report}"
            proc = await asyncio.create_subprocess_exec(
                "git",
                "commit",
                "-m",
                commit_message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_root),
            )
            await proc.wait()

            # Push branch
            logger.info(f"Pushing branch: {branch_name}")
            proc = await asyncio.create_subprocess_exec(
                "git",
                "push",
                "-u",
                "origin",
                branch_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_root),
            )
            await proc.wait()

            # Create PR using GitHub CLI
            pr_body = self._format_pr_body(patchset, assessment, risk_report)

            logger.info("Creating PR via GitHub CLI")
            proc = await asyncio.create_subprocess_exec(
                "gh",
                "pr",
                "create",
                "--title",
                task_description,
                "--body",
                pr_body,
                "--base",
                base_branch,
                "--head",
                branch_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_root),
            )
            stdout, _ = await proc.communicate()
            result_stdout = stdout.decode() if stdout else ""

            # Extract PR URL from output
            if proc.returncode == 0 and result_stdout:
                pr_url = result_stdout.strip()
                logger.info(f"Created PR: {pr_url}")
                return pr_url
            else:
                logger.error("PR creation failed")
                return None

        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return None

    def _create_proposal_package(
        self, patchset: PatchSet, _assessment, risk_report: str, task_description: str
    ) -> Path:
        """Create a proposal package for high-risk patches.

        Package contains:
        - Risk assessment report
        - Unified diff of changes
        - Test results
        - Governance policy justification
        """
        proposal_dir: Path = self.repo_root / "proposals" / patchset.patch_id
        proposal_dir.mkdir(parents=True, exist_ok=True)

        # Write risk report
        report_file = proposal_dir / "RISK_ASSESSMENT.md"
        report_file.write_text(risk_report, encoding="utf-8")
        logger.info(f"Wrote risk assessment to {report_file}")

        # Write patch summary
        summary_file = proposal_dir / "PATCHES.json"
        patches_data = {
            "task_id": patchset.patch_id,
            "task_description": task_description,
            "patches": [
                {"file": p.file_path, "action": p.action.value, "description": p.description}
                for p in patchset.patches
            ],
            "created_at": datetime.now(UTC).isoformat(),
        }
        summary_file.write_text(json.dumps(patches_data, indent=2), encoding="utf-8")

        # Write test results if available
        if patchset.test_results:
            test_file = proposal_dir / "TEST_RESULTS.json"
            test_file.write_text(json.dumps(patchset.test_results, indent=2), encoding="utf-8")

        logger.info(f"Created proposal package at {proposal_dir}")
        return proposal_dir

    def _create_branch_name(self, task_description: str) -> str:
        """Create a sanitized branch name from task description."""
        import re
        from datetime import datetime

        # Sanitize task description
        slug = re.sub(r"[^a-z0-9]+", "-", task_description.lower())
        slug = slug.strip("-")[:30]

        timestamp = datetime.now(UTC).strftime("%Y%m%d")
        return f"agent/{timestamp}/{slug}"

    def _format_pr_body(self, patchset: PatchSet, assessment, risk_report: str) -> str:
        """Format PR description with governance details."""
        body = []
        body.append("## Autonomous Patch Submission\n")
        body.append(f"**Patch ID:** {patchset.patch_id}")
        body.append(f"**Files Changed:** {len(patchset.patches)}")
        body.append(f"**Risk Level:** {assessment.risk_level.value.upper()}")
        body.append(f"**Auto-Merge:** {assessment.approval_policy == ApprovalPolicy.AUTO}\n")

        body.append("## Changes\n")
        for patch in patchset.patches:
            body.append(f"- {patch.action.value}: {patch.file_path}")

        body.append(f"\n## Risk Assessment\n{risk_report}")

        if patchset.test_results:
            body.append("\n## Test Results\n")
            body.append(
                f"**Status:** {'✅ PASSED' if patchset.test_results.get('passed') else '❌ FAILED'}"
            )

        return "\n".join(body)

    async def _log_to_quest(self, result: dict):
        """Log workflow result to quest system."""
        try:
            quest_log = Path("src/Rosetta_Quest_System/quest_log.jsonl")
            quest_log.parent.mkdir(parents=True, exist_ok=True)

            entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "task_type": "autonomous_patch",
                "patch_id": result.get("patch_id"),
                "status": "success" if result.get("success") else "failed",
                "result": result,
            }

            if aiofiles:
                async with aiofiles.open(quest_log, "a") as f:
                    await f.write(json.dumps(entry) + "\n")
            else:
                with open(quest_log, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")

            logger.info("Logged result to quest system")
        except Exception as e:
            logger.warning(f"Failed to log to quest: {e}")

    async def run_autonomous_cycle(self, max_tasks: int = 5) -> dict:
        """Run a complete autonomous cycle processing multiple tasks.

        Args:
            max_tasks: Maximum number of tasks to process

        Returns:
            Summary of processed tasks
        """
        logger.info(f"Starting autonomous cycle (max {max_tasks} tasks)")

        # Import orchestrator to get tasks
        try:
            from src.orchestration.background_task_orchestrator import (
                TaskStatus, get_orchestrator)

            orchestrator = get_orchestrator()

            # Get completed tasks that haven't been processed
            completed_tasks = [
                t
                for t in orchestrator.list_tasks(status=TaskStatus.COMPLETED)
                if not t.metadata.get("autonomy_processed")
            ]

            results: dict[str, Any] = {
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "results": [],
            }

            for task in completed_tasks[:max_tasks]:
                logger.info(f"Processing task {task.task_id}")

                result = await self.process_llm_response(
                    task_id=task.task_id,
                    llm_response=task.result or "",
                    task_description=task.prompt[:100],
                )

                results["results"].append(result)
                if result.get("success"):
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                results["total_processed"] += 1

                # Mark task as processed
                task.metadata["autonomy_processed"] = True
                orchestrator._save_tasks()

            logger.info(f"Autonomous cycle complete: {results['total_processed']} tasks")
            return results

        except ImportError:
            logger.warning("BackgroundTaskOrchestrator not available for autonomous cycle")
            return {"error": "Orchestrator not available"}
