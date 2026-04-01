"""Patch Builder - Extract and apply code patches from LLM responses.

This module provides functionality to:
1. Extract code blocks from LLM responses (markdown format, JSON, etc.)
2. Parse diffs and file operations
3. Apply patches deterministically to files
4. Run tests to validate changes
5. Format code using black/ruff

The patch lifecycle:
    PROPOSED → APPLYING → APPLIED → TESTING → PASSED/FAILED → FORMATTED → READY_FOR_PR
"""

import asyncio
import importlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

aiofiles: Any | None
try:
    aiofiles = importlib.import_module("aiofiles")
except ImportError:
    aiofiles = None

logger = logging.getLogger(__name__)


class PatchAction(Enum):
    """Type of file operation."""

    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    REPLACE = "replace"
    APPEND = "append"


class PatchStatus(Enum):
    """Patch lifecycle status."""

    PROPOSED = "proposed"
    APPLYING = "applying"
    APPLIED = "applied"
    TESTING = "testing"
    PASSED = "passed"
    FAILED = "failed"
    FORMATTED = "formatted"
    READY_FOR_PR = "ready_for_pr"


@dataclass
class CodeBlock:
    """Extracted code block from LLM response."""

    language: str
    content: str
    confidence: float = 0.95  # How confident we are in this block
    line_start: int | None = None
    line_end: int | None = None


@dataclass
class FilePatch:
    """Single file operation within a patch set."""

    file_path: str
    action: PatchAction
    old_content: str | None = None
    new_content: str | None = None
    description: str = ""

    def validate(self) -> tuple[bool, str]:
        """Validate patch consistency."""
        if self.action == PatchAction.CREATE:
            return self._validate_create()
        if self.action == PatchAction.DELETE:
            return self._validate_delete()
        if self.action == PatchAction.MODIFY:
            return self._validate_modify()
        if self.action == PatchAction.REPLACE:
            return self._validate_replace()
        if self.action == PatchAction.APPEND:
            return self._validate_append()
        raise RuntimeError(f"Unsupported patch action: {self.action}")

    def _validate_create(self) -> tuple[bool, str]:
        if not self.new_content:
            return False, "CREATE requires new_content"
        if self.old_content:
            return False, "CREATE should not have old_content"
        return True, "Valid"

    def _validate_delete(self) -> tuple[bool, str]:
        if not self.old_content:
            return False, "DELETE requires old_content"
        return True, "Valid"

    def _validate_modify(self) -> tuple[bool, str]:
        if not self.old_content or not self.new_content:
            return False, "MODIFY requires both old_content and new_content"
        return True, "Valid"

    def _validate_replace(self) -> tuple[bool, str]:
        if not self.old_content or not self.new_content:
            return False, "REPLACE requires both old_content and new_content"
        return True, "Valid"

    def _validate_append(self) -> tuple[bool, str]:
        if not self.new_content:
            return False, "APPEND requires new_content"
        return True, "Valid"


@dataclass
class PatchSet:
    """Collection of file patches with status tracking."""

    patch_id: str
    patches: list[FilePatch] = field(default_factory=list)
    status: PatchStatus = PatchStatus.PROPOSED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    applied_at: datetime | None = None
    test_results: dict | None = None
    errors: list[str] = field(default_factory=list)
    description: str = ""

    def add_patch(self, patch: FilePatch) -> bool:
        """Add patch and validate."""
        valid, msg = patch.validate()
        if not valid:
            self.errors.append(f"Invalid patch for {patch.file_path}: {msg}")
            return False
        self.patches.append(patch)
        return True

    def validate_all(self) -> bool:
        """Validate all patches in set."""
        self.errors.clear()
        for patch in self.patches:
            valid, msg = patch.validate()
            if not valid:
                self.errors.append(f"Invalid patch for {patch.file_path}: {msg}")
        return len(self.errors) == 0


class PatchBuilder:
    """Build, apply, and test code patches."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize patch builder.

        Args:
            repo_root: Root directory of the repository (defaults to current dir)
        """
        self.repo_root = repo_root or Path.cwd()
        logger.info(f"PatchBuilder initialized with repo root: {self.repo_root}")

    def extract_code_blocks(self, text: str) -> list[CodeBlock]:
        """Extract code blocks from markdown-formatted LLM response.

        Handles patterns like:
        ```python
        code here
        ```

        And variations with language identifiers.
        """
        blocks = []
        # Match ```language\ncode\n```
        pattern = r"```(\w+)?\n(.*?)\n```"
        matches = re.finditer(pattern, text, re.DOTALL)

        for match in matches:
            language = match.group(1) or "text"
            content = match.group(2).strip()
            blocks.append(CodeBlock(language=language, content=content, confidence=0.95))

        return blocks

    def parse_unified_diff(self, diff_text: str) -> list[FilePatch]:
        """Parse unified diff format into FilePatch objects.

        Handles standard git diff output:
        --- a/path/to/file
        +++ b/path/to/file
        @@ -1,5 +1,6 @@
        -old line
        +new line
        """
        patches = []
        current_file = None
        old_content_lines = []
        new_content_lines = []
        in_diff = False

        for line in diff_text.split("\n"):
            current_file = self._parse_diff_file_header(line, current_file)
            if line.startswith("+++ b/"):
                in_diff = True
            elif line.startswith("-") and not line.startswith("---"):
                old_content_lines.append(line[1:])
            elif line.startswith("+") and not line.startswith("+++"):
                new_content_lines.append(line[1:])
            elif line.startswith("@@"):
                # New hunk, save previous
                patch = self._create_diff_patch(current_file, old_content_lines, new_content_lines)
                if patch and in_diff:
                    patches.append(patch)
                old_content_lines = []
                new_content_lines = []

        return patches

    def _parse_diff_file_header(self, line: str, current_file: str | None) -> str | None:
        if line.startswith("--- a/"):
            return line[6:]
        return current_file

    def _create_diff_patch(
        self, current_file: str | None, old_lines: list[str], new_lines: list[str]
    ) -> FilePatch | None:
        if not current_file or not old_lines or not new_lines:
            return None
        return FilePatch(
            file_path=current_file,
            action=PatchAction.MODIFY,
            old_content="\n".join(old_lines),
            new_content="\n".join(new_lines),
        )

    def extract_file_operations(self, json_text: str) -> list[FilePatch]:
        """Parse file operations from JSON format.

        Expected format:
        {
            "operations": [
                {
                    "path": "src/file.py",
                    "action": "create",
                    "content": "..."
                }
            ]
        }
        """
        patches = []
        try:
            data = json.loads(json_text)
            operations = data.get("operations", [])

            for op in operations:
                try:
                    action = PatchAction(op["action"].lower())
                    patch = FilePatch(
                        file_path=op["path"],
                        action=action,
                        new_content=op.get("content"),
                        old_content=op.get("old_content"),
                        description=op.get("description", ""),
                    )
                    valid, msg = patch.validate()
                    if valid:
                        patches.append(patch)
                    else:
                        logger.warning(f"Invalid operation for {op['path']}: {msg}")
                except (KeyError, ValueError) as e:
                    logger.warning(f"Malformed operation: {e}")
                    continue
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON operations: {e}")

        return patches

    async def apply_patches(self, patchset: PatchSet) -> tuple[bool, list[str]]:
        """Apply all patches in the set to the filesystem.

        Returns:
            Tuple of (success, error_list)
        """
        patchset.status = PatchStatus.APPLYING
        patchset.applied_at = datetime.now(UTC)
        errors = []

        for patch in patchset.patches:
            file_path = self.repo_root / patch.file_path

            try:
                if patch.action == PatchAction.CREATE:
                    self._apply_create(file_path, patch)
                elif patch.action == PatchAction.DELETE:
                    self._apply_delete(file_path, patch)
                elif patch.action == PatchAction.MODIFY:
                    result = self._apply_modify(file_path, patch)
                    if not result:
                        errors.append(f"Failed to modify {patch.file_path}")
                elif patch.action == PatchAction.REPLACE:
                    self._apply_replace(file_path, patch)
                elif patch.action == PatchAction.APPEND:
                    await self._apply_append(file_path, patch)

            except Exception as e:
                error_msg = f"Failed to apply patch to {patch.file_path}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue

        patchset.status = PatchStatus.APPLIED
        return len(errors) == 0, errors

    def _apply_create(self, file_path: Path, patch) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(patch.new_content or "", encoding="utf-8")
        logger.info(f"Created {patch.file_path}")

    def _apply_delete(self, file_path: Path, patch) -> None:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted {patch.file_path}")

    def _apply_modify(self, file_path: Path, patch) -> bool:
        if not file_path.exists():
            logger.error(f"File not found for MODIFY: {patch.file_path}")
            return False
        current_content = file_path.read_text(encoding="utf-8")
        if not patch.old_content or patch.old_content not in current_content:
            logger.error(f"Old content not found in {patch.file_path}")
            return False
        new_content = current_content.replace(patch.old_content, patch.new_content or "")
        file_path.write_text(new_content, encoding="utf-8")
        logger.info(f"Modified {patch.file_path}")
        return True

    def _apply_replace(self, file_path: Path, patch) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(patch.new_content or "", encoding="utf-8")
        logger.info(f"Replaced {patch.file_path}")

    async def _apply_append(self, file_path: Path, patch) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if aiofiles:
            async with aiofiles.open(file_path, "a", encoding="utf-8") as f:
                await f.write((patch.new_content or "") + "\n")
        else:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write((patch.new_content or "") + "\n")
        logger.info(f"Appended to {patch.file_path}")

    async def run_tests(
        self, patchset: PatchSet, test_pattern: str = "tests/", timeout_seconds: float = 300.0
    ) -> tuple[bool, dict]:
        """Run tests to validate patches.

        Args:
            patchset: Patch set to test
            test_pattern: Pattern for test discovery (default: pytest)
            timeout_seconds: Timeout for test execution

        Returns:
            Tuple of (all_passed, test_results_dict)
        """
        patchset.status = PatchStatus.TESTING

        try:
            cmd = ["python", "-m", "pytest", test_pattern, "-v", "--tb=short"]
            result = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=str(self.repo_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=timeout_seconds,
            )

            stdout, stderr = await result.communicate()
            output = stdout.decode("utf-8", errors="replace")

            test_results = {
                "return_code": result.returncode,
                "passed": result.returncode == 0,
                "output": output[:2000] if output else "",  # Truncate output
                "stderr": stderr.decode("utf-8", errors="replace")[:500],
            }

            patchset.test_results = test_results
            patchset.status = PatchStatus.PASSED if result.returncode == 0 else PatchStatus.FAILED

            logger.info(f"Test results: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            return result.returncode == 0, test_results

        except TimeoutError:
            error_msg = f"Tests timed out after {timeout_seconds} seconds"
            patchset.errors.append(error_msg)
            patchset.status = PatchStatus.FAILED
            return False, {"passed": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Test execution failed: {e}"
            patchset.errors.append(error_msg)
            patchset.status = PatchStatus.FAILED
            return False, {"passed": False, "error": error_msg}

    async def format_code(
        self, patchset: PatchSet, use_black: bool = True, use_ruff: bool = True
    ) -> tuple[bool, list[str]]:
        """Format modified files using black and ruff.

        Args:
            patchset: Patch set with files to format
            use_black: Whether to run black formatter
            use_ruff: Whether to run ruff linter/fixer

        Returns:
            Tuple of (success, error_list)
        """
        errors = []
        files_to_format = [
            str(self.repo_root / p.file_path)
            for p in patchset.patches
            if (self.repo_root / p.file_path).exists()
        ]

        if not files_to_format:
            return True, []

        if use_black:
            try:
                cmd = ["python", "-m", "black", "--quiet", *files_to_format]
                result = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                logger.info(f"Formatted {len(files_to_format)} files with black")
            except Exception as e:
                errors.append(f"Black formatting failed: {e}")
                logger.warning(f"Black formatting error: {e}")

        if use_ruff:
            try:
                cmd = ["python", "-m", "ruff", "check", "--fix", "--quiet", *files_to_format]
                result = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                logger.info(f"Fixed issues with ruff in {len(files_to_format)} files")
            except Exception as e:
                errors.append(f"Ruff fixing failed: {e}")
                logger.warning(f"Ruff fixing error: {e}")

        patchset.status = PatchStatus.FORMATTED
        return len(errors) == 0, errors

    def estimate_risk(self, patchset: PatchSet) -> float:
        """Estimate risk score for a patch set (0.0-1.0).

        Factors:
        - Number of files changed (+0.05 each)
        - Critical paths (orchestration, core) (+0.3 each)
        - Deletions (+0.2 each)
        - Test failures (x1.3)
        """
        score = 0.0

        # File count risk
        score += min(len(patchset.patches) * 0.05, 0.4)

        # Critical path risk
        critical_keywords = ["orchestration", "core", "auth", "security", "main"]
        for patch in patchset.patches:
            if any(keyword in patch.file_path.lower() for keyword in critical_keywords):
                score += 0.3

        # Deletion risk
        deletions = sum(1 for p in patchset.patches if p.action == PatchAction.DELETE)
        score += deletions * 0.2

        # Test failure risk
        if patchset.test_results and not patchset.test_results.get("passed"):
            score *= 1.3

        return min(score, 1.0)
