"""OmniTag: {.

    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

"""
structure_organizer.py

Purpose:
- Utilities to organize, lint, and suggest structural improvements for the
    repository (files, folders, package layout).

Who/What/Where/When/Why/How:
- Who: Developers and automated agents analyzing project layout.
- What: Provides helpers to suggest reorganizations and to produce
    human-readable reports of file-organization issues.
- Where: Run from the repository root or import into higher-level tools.
- When: Run during repo audits, pre-merge checks, or design discussions.
- Why: Keep the repository consistent and navigable for humans and AI.
- How: Use the module functions to produce suggested move/copy operations
    and to generate `reports/` artifacts for review.

Integration & tips:
- Complement `src/utils/file_organization_auditor.py` and `docs/` checklists.
- Prefer safe, reversible suggestions — do not perform destructive moves
    without an explicit approval step (e.g., create a patch file instead).

"""
