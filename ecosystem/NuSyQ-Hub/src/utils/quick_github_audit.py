#!/usr/bin/env python3
"""quick_github_audit.py.

Purpose:
- Quick scanner to validate `.github/` structure, workflows, and instruction
    documents used by Copilot/agent enhancements. Intended for fast health
    checks and to surface missing CI/workflow artifacts.

Who/What/Where/When/Why/How:
- Who: Maintainers and automation agents verifying GitHub-integrated files.
- What: Reports on presence of workflows, detects YAML parse issues, and
    checks for essential instruction documents.
- Where: Run from repository root.
- When: Helpful during repository audits, CI sanity checks, or before
    release/tag operations.
- Why: Ensures agents and CI have the expected configuration available.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import contextlib
import logging
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import]

logger = logging.getLogger(__name__)


def quick_github_audit() -> bool:
    """Quick audit and enhancement of GitHub integration."""
    repo_root = Path.cwd()
    github_dir = repo_root / ".github"

    # Basic structure check

    if github_dir.exists():
        [d.name for d in github_dir.iterdir() if d.is_dir()]

        # Check each subdirectory
        for subdir in ["workflows", "instructions", "prompts"]:
            subdir_path = github_dir / subdir
            exists = subdir_path.exists()
            len(list(subdir_path.glob("*"))) if exists else 0

    # Workflow validation
    workflows_dir = github_dir / "workflows"
    if workflows_dir.exists():
        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))

        for workflow_file in workflow_files:
            try:
                # Ensure UTF-8 read with graceful replacement for bad bytes
                with open(workflow_file, encoding="utf-8", errors="replace") as f:
                    workflow_data = yaml.safe_load(f)

                (
                    workflow_data.get("name", "Unnamed")
                    if isinstance(workflow_data, dict)
                    else "Unnamed"
                )
                (len(workflow_data.get("jobs", {})) if isinstance(workflow_data, dict) else 0)

            except (yaml.YAMLError, OSError, UnicodeDecodeError):
                logger.debug("Suppressed OSError/UnicodeDecodeError/yaml", exc_info=True)
    else:
        pass

    # Instructions check
    instructions_dir = github_dir / "instructions"
    if instructions_dir.exists():
        list(instructions_dir.glob("*.md"))

        essential_instructions = [
            "COPILOT_INSTRUCTIONS_CONFIG.instructions.md",
            "FILE_PRESERVATION_MANDATE.instructions.md",
            "NuSyQ-Hub_INSTRUCTIONS.instructions.md",
        ]

        for essential in essential_instructions:
            exists = (instructions_dir / essential).exists()
    else:
        pass

    # Prompts check
    prompts_dir = github_dir / "prompts"
    if prompts_dir.exists():
        prompt_files = list(prompts_dir.glob("*.md"))

        for prompt_file in prompt_files:
            with contextlib.suppress(OSError):
                prompt_file.stat().st_size / 1024
    else:
        pass

    # Infrastructure integration check
    src_systems = {
        "ChatDev Launcher": "src/integration/chatdev_launcher.py",
        "Testing Chamber": "src/orchestration/chatdev_testing_chamber.py",
        "Quantum Automator": "src/orchestration/quantum_workflow_automation.py",
        "Ollama Integrator": "src/ai/ollama_chatdev_integrator.py",
        "AI Coordinator": "src/core/ai_coordinator.py",
        "Logging System": "LOGGING/infrastructure/modular_logging_system.py",
    }

    for system_path in src_systems.values():
        exists = (repo_root / system_path).exists()

    # Generate enhancement recommendations

    recommendations: list[Any] = []
    # Check for missing workflows
    if workflows_dir.exists():
        existing_workflows = [f.stem for f in workflow_files]
        essential_workflows = ["ci", "test", "security-scan", "coverage-verification"]

        for essential in essential_workflows:
            if not any(essential in existing for existing in existing_workflows):
                recommendations.append(f"   🔄 Add {essential} workflow for automation")

    # Check for integration references
    if github_dir.exists():
        github_files = list(github_dir.rglob("*.md")) + list(github_dir.rglob("*.yml"))
        src_references = 0

        for file in github_files:
            try:
                content = file.read_text(encoding="utf-8", errors="replace")
                if "src/" in content:
                    src_references += 1
            except (OSError, UnicodeDecodeError):
                # skip unreadable files
                continue

        if src_references < 5:
            recommendations.append(
                f"   🔗 Enhance infrastructure integration (current: {src_references} references)"
            )

    # Documentation completeness
    missing_contexts: list[Any] = []
    for subdir in ["workflows", "instructions", "prompts"]:
        subdir_path = github_dir / subdir
        if subdir_path.exists():
            context_file = subdir_path / f"GITHUB_{subdir.upper()}_CONTEXT.md"
            if not context_file.exists():
                missing_contexts.append(context_file.name)

    if missing_contexts:
        recommendations.append(
            "   📚 Add missing context files: {}".format(", ".join(missing_contexts))
        )

    if recommendations:
        for _rec in recommendations:
            pass
    else:
        pass

    return True


if __name__ == "__main__":
    quick_github_audit()
