"""Artifact Trust Layer foundation for Phase 1A.

Goals:
    1. Capture run metadata (models, env, flags, costs) to run_manifest.json
    2. Create per-run artifact bundles in state/artifacts/<run_id>/
    3. Generate run_manifest.json, replay.sh, and handoff.md per execution
    4. Enable reproducibility and agent handoff
    5. Track dependencies and blast radius

Design (minimal Phase 1A):
    - ArtifactManager class wraps each action/run
    - Emits to state/artifacts/<run_id>/manifest.json
    - Generates replay.sh with env/model/flags
    - Collects diffs (before/after for touched files)
    - Provides agent handoff context
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ArtifactMetadata:
    """Per-run artifact metadata for reproducibility."""

    run_id: str
    timestamp: str  # ISO 8601
    action: str  # e.g., "analyze", "generate", "heal"
    repo: str  # NuSyQ-Hub, SimulatedVerse, NuSyQ
    branch: str
    commit: str
    agent: str  # Which agent ran this
    model: str  # LLM model used (if any)
    user: str | None = None
    cost_estimate: float = 0.0
    touched_files: list = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    exit_code: int = 0


@dataclass
class RunManifest:
    """Complete immutable record of a single run."""

    metadata: ArtifactMetadata
    environment: dict = field(default_factory=dict)
    flags: dict = field(default_factory=dict)
    dependencies: dict = field(default_factory=dict)  # tool -> version
    artifacts: dict = field(default_factory=dict)  # artifact_name -> path
    hash: str = ""  # SHA256 of manifest for signing

    def compute_hash(self) -> str:
        """Compute SHA256 hash of manifest (excluding hash field itself)."""
        manifest_copy = asdict(self)
        manifest_copy["hash"] = ""  # Exclude hash field from computation
        content = json.dumps(manifest_copy, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()


class ArtifactManager:
    """Manages artifact creation, storage, and retrieval.

    Phase 1A: Minimal wiring
    - Create run_id per action
    - Capture metadata and environment
    - Emit run_manifest.json
    - Generate replay.sh template
    """

    def __init__(self, repo_root: Path, action: str, agent: str = "copilot", model: str = ""):
        """Initialize ArtifactManager with repo_root, action, agent, ...."""
        self.repo_root = Path(repo_root)
        self.action = action
        self.agent = agent
        self.model = model or os.environ.get("CURRENT_MODEL", "unknown")
        self.run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Paths
        self.artifacts_dir = self.repo_root / "state" / "artifacts" / self.run_id
        self.manifest_path = self.artifacts_dir / "manifest.json"
        self.replay_path = self.artifacts_dir / "replay.sh"
        self.handoff_path = self.artifacts_dir / "handoff.md"
        self.diffs_dir = self.artifacts_dir / "diffs"
        self.logs_dir = self.artifacts_dir / "logs"

        # Initialize
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.diffs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Metadata
        self.metadata = ArtifactMetadata(
            run_id=self.run_id,
            timestamp=datetime.now().isoformat(),
            action=action,
            repo=self._detect_repo(),
            branch=self._get_git_branch(),
            commit=self._get_git_commit(),
            agent=agent,
            model=self.model,
        )
        self.manifest = RunManifest(metadata=self.metadata)

    def _detect_repo(self) -> str:
        """Detect which repo this is running from."""
        if "NuSyQ-Hub" in str(self.repo_root):
            return "NuSyQ-Hub"
        elif "SimulatedVerse" in str(self.repo_root):
            return "SimulatedVerse"
        elif "NuSyQ" in str(self.repo_root):
            return "NuSyQ"
        return "unknown"

    def _get_git_branch(self) -> str:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _get_git_commit(self) -> str:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()[:12] if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def start(self) -> None:
        """Mark run as started, capture environment."""
        self.metadata.status = "running"
        self.manifest.environment = dict(os.environ)
        self.manifest.environment.pop("PATH", None)  # Too verbose
        self.manifest.environment.pop("PATHEXT", None)
        # Keep CHATDEV_PATH, PYTHONPATH, etc.

    def add_flag(self, key: str, value: Any) -> None:
        """Track a CLI flag or config value."""
        self.manifest.flags[key] = value

    def add_touched_file(self, file_path: str | Path) -> None:
        """Track that this file was touched."""
        self.metadata.touched_files.append(str(file_path))

    def add_dependency(self, tool: str, version: str) -> None:
        """Track a tool dependency (python, node, etc.)."""
        self.manifest.dependencies[tool] = version

    def add_artifact(self, name: str, path: str | Path) -> None:
        """Register an artifact (plan, test_results, logs, etc.)."""
        self.manifest.artifacts[name] = str(path)

    def capture_file_diff(
        self, file_path: Path, before_content: str = "", after_content: str = ""
    ) -> None:
        """Capture before/after diff for a file."""
        diff_file = self.diffs_dir / f"{file_path.name}.diff"
        diff_content = f"--- {file_path}\n"
        if before_content or after_content:
            import difflib

            diff = difflib.unified_diff(
                before_content.splitlines(keepends=True),
                after_content.splitlines(keepends=True),
                fromfile=str(file_path) + ".before",
                tofile=str(file_path) + ".after",
            )
            diff_content += "".join(diff)
        with open(diff_file, "w") as f:
            f.write(diff_content)
        self.add_artifact(f"diff_{file_path.name}", diff_file)

    def complete(self, exit_code: int = 0) -> None:
        """Mark run as completed."""
        self.metadata.status = "completed"
        self.metadata.exit_code = exit_code
        self._emit_manifest()
        self._emit_replay_sh()
        self._emit_handoff_md()

    def failed(self, exit_code: int = 1, error_msg: str = "") -> None:
        """Mark run as failed."""
        self.metadata.status = "failed"
        self.metadata.exit_code = exit_code
        error_file = self.logs_dir / "error.txt"
        error_file.write_text(error_msg)
        self._emit_manifest()

    def _emit_manifest(self) -> None:
        """Write run_manifest.json."""
        # Compute hash
        self.manifest.hash = self.manifest.compute_hash()

        manifest_json = asdict(self.manifest)
        manifest_json["metadata"] = asdict(self.metadata)

        with open(self.manifest_path, "w") as f:
            json.dump(manifest_json, f, indent=2, default=str)

    def _emit_replay_sh(self) -> None:
        """Generate replay.sh for reproducibility."""
        lines = [
            "#!/bin/bash",
            "# Auto-generated replay script for reproducibility",
            f"# Run ID: {self.run_id}",
            f"# Timestamp: {self.metadata.timestamp}",
            f"# Action: {self.metadata.action}",
            f"# Agent: {self.metadata.agent}",
            f"# Model: {self.metadata.model}",
            "",
            "# Environment setup",
            "export PYTHONUNBUFFERED=1",
        ]

        # Capture key environment variables
        key_env_vars = ["CHATDEV_PATH", "PYTHONPATH", "NODE_ENV", "CURRENT_MODEL"]
        for var in key_env_vars:
            if var in self.manifest.environment:
                lines.append(f'export {var}="{self.manifest.environment[var]}"')

        lines.extend(
            [
                "",
                "# Navigate to repo",
                f'cd "{self.repo_root}"',
                "",
                "# Checkout correct commit if needed",
                f"git checkout {self.metadata.commit} 2>/dev/null || true",
                "",
                "# Execute action",
                f"python scripts/start_nusyq.py {self.metadata.action}",
                "",
                f"# Original manifest: {self.manifest_path}",
            ]
        )

        replay_content = "\n".join(lines)
        with open(self.replay_path, "w") as f:
            f.write(replay_content)
        os.chmod(self.replay_path, 0o755)

    def _emit_handoff_md(self) -> None:
        """Generate handoff.md for next agent context."""
        lines = [
            f"# Handoff Report — {self.run_id}",
            "",
            f"**Action**: {self.metadata.action}",
            f"**Agent**: {self.metadata.agent}",
            f"**Model**: {self.metadata.model}",
            f"**Status**: {self.metadata.status}",
            f"**Exit Code**: {self.metadata.exit_code}",
            "",
            "## What Changed",
            f"- Touched {len(self.metadata.touched_files)} file(s)",
        ]

        for f in self.metadata.touched_files[:10]:
            lines.append(f"  - `{f}`")
        if len(self.metadata.touched_files) > 10:
            lines.append(f"  ... and {len(self.metadata.touched_files) - 10} more")

        lines.extend(
            [
                "",
                "## Artifacts Generated",
            ]
        )

        for name, path in self.manifest.artifacts.items():
            lines.append(f"  - `{name}`: {path}")

        lines.extend(
            [
                "",
                "## Next Steps",
                "1. Review diffs in `diffs/` directory",
                "2. Verify tests in Tests terminal",
                "3. Check `manifest.json` for dependencies",
                "",
                "## Do Not Touch",
                "- `manifest.json` (immutable record)",
                "- Commit hash (recorded for replay)",
                "",
                "## Replay Command",
                "```bash",
                f"bash {self.replay_path}",
                "```",
            ]
        )

        with open(self.handoff_path, "w") as f:
            f.write("\n".join(lines))

    def summary(self) -> dict:
        """Return summary dict for logging/display."""
        return {
            "run_id": self.run_id,
            "action": self.metadata.action,
            "status": self.metadata.status,
            "repo": self.metadata.repo,
            "manifest": str(self.manifest_path),
            "handoff": str(self.handoff_path),
            "replay": str(self.replay_path),
        }


# CLI example (for testing)
if __name__ == "__main__":
    manager = ArtifactManager(Path.cwd(), action="test_phase_1a", agent="copilot", model="gpt-4")
    manager.start()
    manager.add_flag("verbose", True)
    manager.add_dependency("python", "3.13.0")
    manager.add_touched_file("test_file.py")
    manager.complete(exit_code=0)
    logger.info(json.dumps(manager.summary(), indent=2))
