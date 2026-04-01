"""NuSyQ Workspace Snapshots (Metadata Directory).

This hidden directory (.snapshots) stores workspace state snapshots.
It is NOT a Python module - the dot prefix makes it a data directory.

Snapshot operations are provided via:
    - src.spine.snapshot_manager (if available)
    - scripts/workspace_snapshot.py (CLI tool)

Directory Structure:
    .snapshots/
        <snapshot_id>/
            metadata.json
            config/
            state/
"""

# This file exists only for documentation purposes.
# The .snapshots directory stores data, not importable Python code.

__all__: list[str] = []
