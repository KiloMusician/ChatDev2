#!/usr/bin/env python3
"""Result Applier - Converts LLM task results into actual code changes.

This is the critical feedback loop that makes the system self-improving:
1. Reads completed task results
2. Parses code blocks from LLM responses
3. Applies changes to actual files (with review)
4. Logs changes for audit trail

Without this, the system generates suggestions but never applies them!
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ResultApplier")

AUTO_TEST_PREAMBLE = (
    '"""Auto-generated draft test.\n'
    "Requires manual review before enabling in CI.\n"
    '"""\n'
    "import pytest\n"
    "pytest.skip('Auto-generated draft test; enable after review.', allow_module_level=True)\n\n"
)


@dataclass
class CodeBlock:
    """Extracted code block from LLM response."""

    language: str
    code: str
    filename: str | None = None


@dataclass
class ApplicableResult:
    """A task result that can be applied to the codebase."""

    task_id: str
    prompt: str
    result: str
    code_blocks: list
    suggested_files: list
    action_type: str  # 'create', 'modify', 'test', 'document'


class ResultApplier:
    """Applies LLM-generated results to the codebase."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results_path = self.project_root / "data/task_results"
        self.applied_path = self.project_root / "data/applied_results"
        self.applied_path.mkdir(parents=True, exist_ok=True)
        self.log_path = self.project_root / "data/terminal_logs"
        self.review_stage_path = self.project_root / "state/review_gate/result_applier"
        self.review_stage_path.mkdir(parents=True, exist_ok=True)

    def extract_code_blocks(self, text: str) -> list[CodeBlock]:
        """Extract code blocks from markdown-formatted LLM response."""
        # Pattern for ```language\ncode\n``` where language can contain symbols.
        pattern = r"```([^\n`]*)\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)

        blocks = []
        for lang, code in matches:
            lang = (lang or "text").strip().lower()
            # Try to detect filename from comments
            filename = None
            first_line = code.strip().split("\n")[0] if code.strip() else ""
            if first_line.startswith("#") and ("." in first_line or "/" in first_line):
                # e.g., "# src/utils/helper.py" or "# helper.py"
                potential_file = first_line.lstrip("# ").strip()
                if "." in potential_file:
                    filename = potential_file

            # Infer concrete language from filename extension when fence language is generic.
            if lang in {"text", "markdown", "md"} and filename:
                suffix = Path(filename).suffix.lower()
                inferred = {
                    ".py": "python",
                    ".ts": "typescript",
                    ".tsx": "tsx",
                    ".js": "javascript",
                    ".jsx": "jsx",
                    ".gd": "gdscript",
                    ".yml": "yaml",
                    ".yaml": "yaml",
                    ".json": "json",
                    ".sql": "sql",
                    ".sh": "bash",
                }.get(suffix)
                if inferred:
                    lang = inferred

            blocks.append(CodeBlock(language=lang, code=code.strip(), filename=filename))

        return blocks

    def classify_action(self, prompt: str, result: str) -> str:
        """Classify what type of action this result represents."""
        prompt_lower = prompt.lower()
        _ = result

        if any(w in prompt_lower for w in ["test", "pytest", "unittest"]):
            return "test"
        elif any(w in prompt_lower for w in ["create", "generate", "implement", "add"]):
            return "create"
        elif any(w in prompt_lower for w in ["fix", "modify", "update", "refactor"]):
            return "modify"
        elif any(w in prompt_lower for w in ["document", "readme", "docstring"]):
            return "document"
        elif any(w in prompt_lower for w in ["analyze", "review", "check"]):
            return "analyze"  # No code changes, just analysis
        return "unknown"

    def suggest_target_files(self, prompt: str, code_blocks: list[CodeBlock]) -> list[str]:
        """Suggest where code should be placed based on prompt and content."""
        suggestions = []

        # Check for explicit filenames in blocks
        for block in code_blocks:
            if block.filename:
                suggestions.append(block.filename)

        # Infer from prompt
        if "test" in prompt.lower():
            suggestions.append("tests/")
        if "api" in prompt.lower():
            suggestions.append("src/api/")
        if "orchestration" in prompt.lower():
            suggestions.append("src/orchestration/")

        return list(set(suggestions))

    def analyze_results(self, limit: int = 20) -> list[ApplicableResult]:
        """Analyze task results and find applicable ones."""
        applicable = []

        result_files = sorted(self.results_path.glob("*.json"))[-limit:]

        for result_file in result_files:
            try:
                with open(result_file) as f:
                    data = json.load(f)

                result_text = data.get("result", "")
                if not result_text:
                    continue

                code_blocks = self.extract_code_blocks(result_text)
                if not code_blocks:
                    continue  # No code to apply

                action_type = self.classify_action(data.get("prompt", ""), result_text)
                if action_type == "analyze":
                    continue  # Analysis only, no code changes

                suggested_files = self.suggest_target_files(data.get("prompt", ""), code_blocks)

                applicable.append(
                    ApplicableResult(
                        task_id=data.get("task_id", "unknown"),
                        prompt=data.get("prompt", ""),
                        result=result_text,
                        code_blocks=code_blocks,
                        suggested_files=suggested_files,
                        action_type=action_type,
                    )
                )

            except Exception as e:
                logger.warning(f"Failed to analyze {result_file}: {e}")

        return applicable

    def preview_applications(self, limit: int = 20) -> dict:
        """Preview what would be applied without making changes."""
        applicable = self.analyze_results(limit=limit)

        preview = {
            "total_results": len(list(self.results_path.glob("*.json"))),
            "applicable_results": len(applicable),
            "by_action_type": {},
            "samples": [],
        }

        for result in applicable:
            action = result.action_type
            preview["by_action_type"][action] = preview["by_action_type"].get(action, 0) + 1

        # Show samples
        for result in applicable[:5]:
            preview["samples"].append(
                {
                    "task_id": result.task_id,
                    "prompt": result.prompt[:60] + "...",
                    "action_type": result.action_type,
                    "code_blocks": len(result.code_blocks),
                    "languages": [b.language for b in result.code_blocks],
                    "suggested_files": result.suggested_files,
                }
            )

        return preview

    def apply_test_results(self, dry_run: bool = True, limit: int = 20) -> dict:
        """Apply test-related results to tests/ directory."""
        applicable = [r for r in self.analyze_results(limit=limit) if r.action_type == "test"]

        applied = []
        for result in applicable[:5]:  # Limit to 5 at a time
            for block in result.code_blocks:
                is_python = block.language.lower() in {"python", "py"}
                if not is_python and block.filename:
                    is_python = block.filename.lower().endswith(".py")
                if not is_python:
                    continue

                # Prefer explicit test file paths; otherwise write to tests/auto_generated.
                target_rel = None
                if block.filename:
                    rel = block.filename.replace("\\", "/").lstrip("./")
                    rel_lower = rel.lower()
                    if rel_lower.startswith("tests/") or "/test" in rel_lower or rel_lower.startswith("test"):
                        target_rel = rel

                if not target_rel:
                    test_name = f"test_auto_{result.task_id[-8:]}.py"
                    target_rel = f"tests/auto_generated/{test_name}"

                test_path = (self.project_root / target_rel).resolve()
                try:
                    test_path.relative_to(self.project_root.resolve())
                except ValueError:
                    logger.warning(f"Skipping unsafe target path: {target_rel}")
                    continue

                if not dry_run:
                    test_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(test_path, "w", encoding="utf-8") as f:
                        f.write(f"# Auto-generated from task: {result.task_id}\n")
                        f.write(f"# Prompt: {result.prompt[:100]}...\n\n")
                        f.write(AUTO_TEST_PREAMBLE)
                        f.write(block.code)

                    # Mark as applied
                    applied_marker = self.applied_path / f"{result.task_id}.applied"
                    applied_marker.write_text(datetime.now(UTC).isoformat())

                applied.append(str(test_path))

        return {"applicable_tests": len(applicable), "applied": applied, "dry_run": dry_run}

    def _extension_for_language(self, language: str) -> str:
        ext_map = {
            "python": ".py",
            "py": ".py",
            "typescript": ".ts",
            "tsx": ".tsx",
            "javascript": ".js",
            "jsx": ".jsx",
            "json": ".json",
            "yaml": ".yml",
            "yml": ".yml",
            "gdscript": ".gd",
            "sql": ".sql",
            "bash": ".sh",
            "sh": ".sh",
        }
        return ext_map.get((language or "text").lower(), ".txt")

    def _safe_stage_target(self, result: ApplicableResult, block: CodeBlock, block_idx: int) -> Path:
        if block.filename:
            rel = block.filename.replace("\\", "/").lstrip("./")
        else:
            ext = self._extension_for_language(block.language)
            rel = f"generated/{result.task_id}_block{block_idx}{ext}"

        # Never write outside review stage. Source path is mirrored under staging.
        rel = rel.lstrip("/")
        target = (self.review_stage_path / rel).resolve()
        target.relative_to(self.review_stage_path.resolve())
        return target

    def apply_create_modify_to_staging(self, dry_run: bool = True, limit: int = 20) -> dict:
        """Review gate: stage create/modify outputs for human review before merge."""
        applicable = [r for r in self.analyze_results(limit=limit) if r.action_type in {"create", "modify"}]

        staged_files = []
        manifests = []

        for result in applicable[:10]:
            result_manifest = {
                "task_id": result.task_id,
                "action_type": result.action_type,
                "prompt": result.prompt,
                "staged_at": datetime.now(UTC).isoformat(),
                "files": [],
            }
            for idx, block in enumerate(result.code_blocks, start=1):
                try:
                    target = self._safe_stage_target(result, block, idx)
                except ValueError:
                    logger.warning("Skipping unsafe staged path for task %s", result.task_id)
                    continue

                if not dry_run:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with open(target, "w", encoding="utf-8") as f:
                        f.write(f"# REVIEW GATE STAGING - task: {result.task_id}\n")
                        f.write(f"# action_type: {result.action_type}\n")
                        if block.filename:
                            f.write(f"# suggested_target: {block.filename}\n")
                        f.write(f"# prompt: {result.prompt[:180]}\n\n")
                        f.write(block.code)

                staged_files.append(str(target))
                result_manifest["files"].append(
                    {
                        "staged_file": str(target),
                        "suggested_target": block.filename,
                        "language": block.language,
                    }
                )

            if result_manifest["files"]:
                manifest_path = self.applied_path / f"{result.task_id}.review_gate.json"
                if not dry_run:
                    manifest_path.write_text(json.dumps(result_manifest, indent=2), encoding="utf-8")
                manifests.append(str(manifest_path))

        return {
            "applicable_create_modify": len(applicable),
            "staged_files": staged_files,
            "manifests": manifests,
            "staging_root": str(self.review_stage_path),
            "dry_run": dry_run,
        }

    def log_to_terminal(self, message: str, level: str = "INFO"):
        """Write to suggestions terminal log."""
        log_file = self.log_path / "suggestions.log"
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "channel": "Suggestions",
            "level": level,
            "message": message,
            "meta": {"source": "result_applier"},
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Analyze/apply queued LLM task results.")
    parser.add_argument("--limit", type=int, default=20, help="Number of recent result files to inspect")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply generated test artifacts (default is preview-only dry run)",
    )
    args = parser.parse_args()

    applier = ResultApplier()

    print("=" * 60)
    print("  RESULT APPLIER - Feedback Loop Analysis")
    print("=" * 60)

    preview = applier.preview_applications(limit=args.limit)

    print("\n📊 Results Analysis:")
    print(f"   Total task results: {preview['total_results']}")
    print(f"   Applicable (has code): {preview['applicable_results']}")

    print("\n📋 By Action Type:")
    for action, count in preview["by_action_type"].items():
        print(f"   {action}: {count}")

    print("\n📝 Sample Applicable Results:")
    for sample in preview["samples"]:
        print(f"   [{sample['action_type']}] {sample['prompt']}")
        print(f"      Code blocks: {sample['code_blocks']} ({', '.join(sample['languages'])})")
        print(f"      Suggested: {sample['suggested_files']}")

    print("\n" + "=" * 60)

    # Apply tests (dry run by default)
    test_result = applier.apply_test_results(dry_run=not args.apply, limit=args.limit)
    print("\n🧪 Test Application Preview:")
    print(f"   Applicable tests: {test_result['applicable_tests']}")
    if args.apply:
        print(f"   Applied: {len(test_result['applied'])} files")
    else:
        print(f"   Would apply: {len(test_result['applied'])} files")
    for path in test_result["applied"][:5]:
        print(f"   - {path}")

    stage_result = applier.apply_create_modify_to_staging(dry_run=not args.apply, limit=args.limit)
    print("\n🚧 Review Gate (Create/Modify):")
    print(f"   Applicable create/modify: {stage_result['applicable_create_modify']}")
    if args.apply:
        print(f"   Staged files: {len(stage_result['staged_files'])}")
        print(f"   Manifests: {len(stage_result['manifests'])}")
    else:
        print(f"   Would stage files: {len(stage_result['staged_files'])}")
    print(f"   Staging root: {stage_result['staging_root']}")
    for path in stage_result["staged_files"][:5]:
        print(f"   - {path}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
