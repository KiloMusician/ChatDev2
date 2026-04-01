"""Autonomy System - Guided autonomous development with governance.

This package implements a complete feedback loop for autonomous code generation:

1. **Patch Builder** (patch_builder.py)
   - Extract code blocks from LLM responses
   - Parse diffs and file operations
   - Apply patches to filesystem
   - Run tests to validate changes
   - Format code automatically

2. **Risk Scorer** (risk_scorer.py)
   - Assess patch risk on 0.0-1.0 scale
   - Enforce 4-tier governance: AUTO, REVIEW, PROPOSAL, BLOCKED
   - Generate reports with required checks and reviewers

3. **PR Bot** (pr_bot.py)
   - Orchestrate complete autonomous workflow
   - Create GitHub branches and PRs
   - Handle high-risk changes with proposal packages
   - Log results to quest system

Architecture:
    LLM Output
        ↓
    Patch Builder (extract → apply → format)
        ↓
    Risk Scorer (assess risk level)
        ↓
    PR Bot (create PR or proposal)
        ↓
    Quest Log (persistent record)

Usage:
    from src.autonomy import GitHubPRBot

    bot = GitHubPRBot()
    result = await bot.process_llm_response(
        task_id="task_001",
        llm_response=llm_output,
        task_description="Improve login security"
    )
    # Returns: {"success": True, "pr_url": "...", "risk_level": "low"}
"""

from src.autonomy.patch_builder import (CodeBlock, FilePatch, PatchAction,
                                        PatchBuilder, PatchSet, PatchStatus)
from src.autonomy.pr_bot import GitHubPRBot
from src.autonomy.risk_scorer import (ApprovalPolicy, RiskAssessment,
                                      RiskLevel, RiskScorer)

__all__ = [
    "ApprovalPolicy",
    # Patch Builder
    "CodeBlock",
    "FilePatch",
    # PR Bot
    "GitHubPRBot",
    "PatchAction",
    "PatchBuilder",
    "PatchSet",
    "PatchStatus",
    "RiskAssessment",
    # Risk Scorer
    "RiskLevel",
    "RiskScorer",
]
