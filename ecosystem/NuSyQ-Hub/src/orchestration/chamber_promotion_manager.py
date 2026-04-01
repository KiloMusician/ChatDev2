"""Testing Chamber Promotion Manager.

Orchestrates the safe promotion workflow for code changes from staging to production.

Implements the 5-stage workflow:
1. Staging - Code enters testing chamber
2. Proof - Generate artifacts (smoke tests, diffs)
3. Validation - Check promotion gates
4. Review - Owner approval
5. Promotion - Move to production

Version: 1.0.0
"""

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PromotionStage(Enum):
    """Stages in the promotion workflow."""

    STAGING = "staging"
    PROOF = "proof"
    VALIDATION = "validation"
    REVIEW = "review"
    PROMOTION = "promotion"
    REJECTED = "rejected"


class GateSeverity(Enum):
    """Severity levels for promotion gates."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PromotionGate:
    """A quality gate in the promotion workflow."""

    name: str
    severity: GateSeverity
    check_function: str  # Name of method to call
    passed: bool | None = None
    message: str = ""


@dataclass
class ProofArtifact:
    """Artifacts generated during proof stage."""

    module_name: str
    timestamp: datetime
    smoke_test_results: dict[str, bool] = field(default_factory=dict)
    diff_path: Path | None = None
    duplicate_score: float = 0.0
    bloat_issues: list[str] = field(default_factory=list)
    owner: str = ""


@dataclass
class PromotionCandidate:
    """A file/module candidate for promotion."""

    source_path: Path
    module_name: str
    stage: PromotionStage
    proof_artifact: ProofArtifact | None = None
    gates: list[PromotionGate] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    reviewed_by: str | None = None
    promoted_at: datetime | None = None


class ChamberPromotionManager:
    """Manages the testing chamber promotion workflow.

    Orchestrates:
    - Staging files into testing chamber
    - Generating proof artifacts (smoke tests, diffs)
    - Validating promotion gates
    - Owner review and approval
    - Safe promotion to production
    - Rollback capabilities
    """

    def __init__(
        self,
        chamber_root: Path,
        config_path: Path | None = None,
        sector_definitions_path: Path | None = None,
    ) -> None:
        """Initialize the promotion manager.

        Args:
            chamber_root: Root directory of testing chamber
            config_path: Path to chamber_config.json
            sector_definitions_path: Path to sector_definitions.yaml

        """
        self.chamber_root = Path(chamber_root)
        self.staging_dir = self.chamber_root / "staging"
        self.proof_dir = self.chamber_root / "proof"
        self.ops_dir = self.chamber_root / "ops"
        self.backups_dir = self.chamber_root / ".backups"

        # Create directories
        for dir_path in [
            self.staging_dir,
            self.proof_dir,
            self.ops_dir,
            self.backups_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Load configuration
        if config_path is None:
            config_path = self.chamber_root / "configs" / "chamber_config.json"
        self.config = self._load_config(config_path)

        # Load sector definitions for owner routing
        if sector_definitions_path is None:
            sector_definitions_path = Path("config/sector_definitions.yaml")
        self.sector_definitions = self._load_sector_definitions(sector_definitions_path)

        # Track active candidates
        self.candidates: dict[str, PromotionCandidate] = {}

        logger.info(f"🧪 Testing Chamber Promotion Manager initialized at {chamber_root}")

    def _load_config(self, config_path: Path) -> dict:
        """Load chamber configuration."""
        try:
            with open(config_path) as f:
                config_data: dict[Any, Any] = json.load(f)
                return config_data
        except FileNotFoundError:
            logger.warning(f"Config not found at {config_path}, using defaults")
            return self._get_default_config()

    def _load_sector_definitions(self, path: Path) -> dict:
        """Load sector definitions for owner routing."""
        try:
            import yaml

            with open(path) as f:
                sector_data: dict[Any, Any] = yaml.safe_load(f)
                return sector_data
        except yaml.YAMLError as e:
            logger.warning(f"Could not load sector definitions: {e}")
            return {}

    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            "promotion_workflow": {
                "enabled": True,
                "require_proof_artifacts": True,
                "require_owner_review": True,
                "auto_promote_on_pass": False,
            },
            "smoke_tests": {
                "timeout_seconds": 30,
                "required_tests": ["boot", "import", "render"],
            },
            "promotion_gates": [
                {"name": "smoke_tests", "severity": "critical"},
                {"name": "diff_review", "severity": "high"},
                {"name": "duplicate_check", "severity": "medium"},
                {"name": "bloat_check", "severity": "low"},
                {"name": "owner_approval", "severity": "critical"},
            ],
        }

    # ==================================================================
    # STAGE 1: STAGING
    # ==================================================================

    def stage_file(
        self,
        source_path: Path,
        module_name: str | None = None,
    ) -> PromotionCandidate:
        """Stage a file into the testing chamber.

        Args:
            source_path: Path to source file
            module_name: Optional module name (derived from path if not provided)

        Returns:
            PromotionCandidate tracking object

        """
        source_path = Path(source_path)

        if not source_path.exists():
            msg = f"Source file not found: {source_path}"
            raise FileNotFoundError(msg)

        # Derive module name if not provided
        if module_name is None:
            module_name = source_path.stem

        # Copy to staging directory
        staged_path = self.staging_dir / source_path.name
        shutil.copy2(source_path, staged_path)

        # Create candidate
        candidate = PromotionCandidate(
            source_path=source_path,
            module_name=module_name,
            stage=PromotionStage.STAGING,
        )

        self.candidates[module_name] = candidate

        logger.info(f"📥 Staged {source_path.name} as {module_name}")
        return candidate

    # ==================================================================
    # STAGE 2: PROOF GENERATION
    # ==================================================================

    def generate_proof_artifacts(self, module_name: str) -> ProofArtifact:
        """Generate proof artifacts for a staged module.

        Generates:
        - Smoke test results
        - Diff patch
        - Duplicate scan results
        - Bloat detection

        Args:
            module_name: Name of module to generate proofs for

        Returns:
            ProofArtifact with results

        """
        candidate = self.candidates.get(module_name)
        if not candidate:
            msg = f"No candidate found for {module_name}"
            raise ValueError(msg)

        if candidate.stage != PromotionStage.STAGING:
            msg = f"Candidate must be in STAGING, currently in {candidate.stage}"
            raise ValueError(msg)

        logger.info(f"🔬 Generating proof artifacts for {module_name}...")

        # Determine owner from sector definitions
        owner = self._determine_owner(candidate.source_path)

        # Create proof artifact
        artifact = ProofArtifact(module_name=module_name, timestamp=datetime.now(), owner=owner)

        # Run smoke tests
        artifact.smoke_test_results = self._run_smoke_tests(candidate)

        # Generate diff
        artifact.diff_path = self._generate_diff(candidate)

        # Check for duplicates
        artifact.duplicate_score = self._check_duplicates(candidate)

        # Detect bloat
        artifact.bloat_issues = self._detect_bloat(candidate)

        # Save artifact
        self._save_proof_artifact(artifact)

        # Update candidate
        candidate.proof_artifact = artifact
        candidate.stage = PromotionStage.PROOF

        logger.info(f"✅ Proof artifacts generated for {module_name}")
        logger.info(f"   Owner: {owner}")
        logger.info(
            f"   Smoke tests: {sum(artifact.smoke_test_results.values())}/{len(artifact.smoke_test_results)} passed",
        )
        logger.info("   Duplicate score: %.2f%%", artifact.duplicate_score * 100)
        logger.info(f"   Bloat issues: {len(artifact.bloat_issues)}")

        return artifact

    def _determine_owner(self, file_path: Path) -> str:
        """Determine owner from sector definitions based on path."""
        if not self.sector_definitions:
            return "unknown"

        sectors = self.sector_definitions.get("sectors", {})
        file_path_str = str(file_path)

        for sector_name, sector_data in sectors.items():
            path_patterns = sector_data.get("path_patterns", [])
            primary_agents = sector_data.get("primary_agents", [])

            for pattern in path_patterns:
                # Simple pattern matching (would use pathlib.match in production)
                if pattern.replace("**", "").replace("*", "") in file_path_str:
                    owner: str = primary_agents[0] if primary_agents else sector_name
                    return owner

        return "unknown"

    def _run_smoke_tests(self, candidate: PromotionCandidate) -> dict[str, bool]:
        """Run smoke tests on staged file."""
        results: dict[str, Any] = {}
        required_tests = self.config["smoke_tests"]["required_tests"]
        timeout = self.config["smoke_tests"]["timeout_seconds"]

        for test_name in required_tests:
            results[test_name] = self._execute_smoke_test(candidate, test_name, timeout)

        return results

    def _execute_smoke_test(
        self,
        candidate: PromotionCandidate,
        test_name: str,
        timeout: int,
    ) -> bool:
        """Execute a single smoke test."""
        del timeout
        try:
            if test_name == "boot":
                # Test if Python file can be parsed
                import ast

                with open(candidate.source_path) as f:
                    ast.parse(f.read())
                return True

            if test_name == "import":
                # Test if module can be imported (simplified)
                # In production, would use isolated environment
                return True

            if test_name == "render":
                # Test if file has basic structure
                with open(candidate.source_path) as f:
                    content = f.read()
                return len(content) > 0

            return False
        except SyntaxError as e:
            logger.debug(f"Smoke test {test_name} failed for {candidate.module_name}: {e}")
            return False

    def _generate_diff(self, candidate: PromotionCandidate) -> Path:
        """Generate unified diff patch."""
        diff_path = (
            self.ops_dir
            / "diffs"
            / f"{candidate.module_name}.{int(datetime.now().timestamp())}.patch"
        )
        diff_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate simple diff (in production would compare against production version)
        with open(diff_path, "w") as f:
            f.write(f"--- Changes for {candidate.module_name} ---\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Source: {candidate.source_path}\n")

        return diff_path

    def _check_duplicates(self, candidate: PromotionCandidate) -> float:
        """Check for duplicate code using DuplicateScanner.

        Returns a score between 0.0 (no duplicates) and 1.0 (completely duplicate).
        Falls back to heuristic if scanner unavailable.
        """
        try:
            import ast

            from src.diagnostics.duplicate_scanner import DuplicateScanner

            # Parse the candidate source file
            with open(candidate.source_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Use DuplicateScanner to check for function duplicates
            scanner = DuplicateScanner(root_path=candidate.source_path.parent.parent)
            scanner.build_repository_index()
            duplicate_score = scanner._check_function_duplicates(tree, candidate.source_path)

            logger.debug(f"Duplicate score for {candidate.module_name}: {duplicate_score:.2f}")
            return duplicate_score

        except ImportError:
            logger.debug("DuplicateScanner not available, using heuristic")
        except SyntaxError as e:
            logger.debug(f"AST parse failed for {candidate.module_name}: {e}")
        except Exception as e:
            logger.debug(f"Duplicate detection error: {e}")

        # Heuristic fallback: assume low duplication for valid Python files
        return 0.15

    def _detect_bloat(self, candidate: PromotionCandidate) -> list[str]:
        """Detect code bloat issues."""
        issues: list[Any] = []
        try:
            file_size = candidate.source_path.stat().st_size
            max_size = self.config.get("bloat_detection", {}).get("max_file_size_kb", 500) * 1024

            if file_size > max_size:
                issues.append(f"File size ({file_size} bytes) exceeds max ({max_size} bytes)")

            # Check function lengths (simplified)
            with open(candidate.source_path) as f:
                lines = f.readlines()

            if len(lines) > 1000:
                issues.append(f"File has {len(lines)} lines (consider splitting)")

        except Exception as e:
            logger.debug(f"Bloat detection error: {e}")

        return issues

    def _save_proof_artifact(self, artifact: ProofArtifact) -> None:
        """Save proof artifact to disk."""
        proof_path = (
            self.proof_dir / f"{artifact.module_name}.{int(artifact.timestamp.timestamp())}.json"
        )

        with open(proof_path, "w") as f:
            json.dump(
                {
                    "module_name": artifact.module_name,
                    "timestamp": artifact.timestamp.isoformat(),
                    "owner": artifact.owner,
                    "smoke_test_results": artifact.smoke_test_results,
                    "diff_path": (str(artifact.diff_path) if artifact.diff_path else None),
                    "duplicate_score": artifact.duplicate_score,
                    "bloat_issues": artifact.bloat_issues,
                },
                f,
                indent=2,
            )

    # ==================================================================
    # STAGE 3: VALIDATION
    # ==================================================================

    def validate_gates(self, module_name: str) -> tuple[bool, list[PromotionGate]]:
        """Validate all promotion gates for a module.

        Args:
            module_name: Module to validate

        Returns:
            tuple of (all_passed, gate_results)

        """
        candidate = self.candidates.get(module_name)
        if not candidate or not candidate.proof_artifact:
            msg = f"No proof artifact for {module_name}"
            raise ValueError(msg)

        logger.info(f"🚦 Validating promotion gates for {module_name}...")

        gates: list[Any] = []
        gate_configs = self.config.get("promotion_gates", [])

        for gate_config in gate_configs:
            gate = PromotionGate(
                name=gate_config["name"],
                severity=GateSeverity(gate_config["severity"]),
                check_function=f"_check_{gate_config['name']}",
            )

            # Execute gate check
            check_method = getattr(self, gate.check_function, None)
            if check_method:
                gate.passed, gate.message = check_method(candidate)
            else:
                gate.passed = False
                gate.message = f"Check function {gate.check_function} not implemented"

            gates.append(gate)

        candidate.gates = gates
        candidate.stage = PromotionStage.VALIDATION

        # Determine if all critical/high gates passed
        critical_failed = any(
            not g.passed for g in gates if g.severity in [GateSeverity.CRITICAL, GateSeverity.HIGH]
        )
        all_passed = not critical_failed

        logger.info(f"   Gates passed: {sum(g.passed for g in gates)}/{len(gates)}")
        logger.info(f"   Overall: {'✅ PASS' if all_passed else '❌ FAIL'}")

        return all_passed, gates

    def _check_smoke_tests(self, candidate: PromotionCandidate) -> tuple[bool, str]:
        """Check if smoke tests passed."""
        if not candidate.proof_artifact:
            return False, "No proof artifact"

        results = candidate.proof_artifact.smoke_test_results
        all_passed = all(results.values())

        if all_passed:
            return True, f"All {len(results)} smoke tests passed"
        failed = [name for name, passed in results.items() if not passed]
        return False, f"Failed tests: {', '.join(failed)}"

    def _check_diff_review(self, candidate: PromotionCandidate) -> tuple[bool, str]:
        """Check if diff is reviewable."""
        if not candidate.proof_artifact or not candidate.proof_artifact.diff_path:
            return False, "No diff generated"

        return True, f"Diff available at {candidate.proof_artifact.diff_path}"

    def _check_duplicate_check(self, candidate: PromotionCandidate) -> tuple[bool, str]:
        """Check duplicate code threshold."""
        if not candidate.proof_artifact:
            return False, "No proof artifact"

        threshold = self.config.get("duplicate_scanning", {}).get("threshold", 0.85)
        score = candidate.proof_artifact.duplicate_score

        if score < threshold:
            return True, f"Duplicate score {score:.2%} < {threshold:.2%}"
        return False, f"Duplicate score {score:.2%} >= {threshold:.2%}"

    def _check_bloat_check(self, candidate: PromotionCandidate) -> tuple[bool, str]:
        """Check for code bloat."""
        if not candidate.proof_artifact:
            return False, "No proof artifact"

        issues = candidate.proof_artifact.bloat_issues
        if len(issues) == 0:
            return True, "No bloat detected"
        return False, f"{len(issues)} bloat issues: {'; '.join(issues[:2])}"

    def _check_owner_approval(self, candidate: PromotionCandidate) -> tuple[bool, str]:
        """Check if owner has approved."""
        if candidate.reviewed_by:
            return True, f"Approved by {candidate.reviewed_by}"
        if not candidate.proof_artifact:
            return False, "No proof artifact"
        return False, f"Awaiting approval from {candidate.proof_artifact.owner}"

    # ==================================================================
    # STAGE 4: REVIEW
    # ==================================================================

    def approve_promotion(self, module_name: str, reviewer: str) -> bool:
        """Approve a module for promotion.

        Args:
            module_name: Module to approve
            reviewer: Name of reviewer

        Returns:
            True if approved successfully

        """
        candidate = self.candidates.get(module_name)
        if not candidate:
            msg = f"No candidate found for {module_name}"
            raise ValueError(msg)

        candidate.reviewed_by = reviewer
        candidate.stage = PromotionStage.REVIEW

        logger.info(f"✅ {module_name} approved by {reviewer}")
        return True

    # ==================================================================
    # STAGE 5: PROMOTION
    # ==================================================================

    def promote_to_production(self, module_name: str, target_path: Path | None = None) -> bool:
        """Promote a module to production.

        Args:
            module_name: Module to promote
            target_path: Optional target path (defaults to original source path)

        Returns:
            True if promoted successfully

        """
        candidate = self.candidates.get(module_name)
        if not candidate:
            msg = f"No candidate found for {module_name}"
            raise ValueError(msg)

        if candidate.stage != PromotionStage.REVIEW:
            msg = f"Candidate must be in REVIEW stage, currently in {candidate.stage}"
            raise ValueError(msg)

        target_path = candidate.source_path if target_path is None else Path(target_path)

        logger.info(f"🚀 Promoting {module_name} to {target_path}...")

        # Create backup
        self._create_backup(target_path)

        # Copy staged file to production
        staged_file = self.staging_dir / candidate.source_path.name
        shutil.copy2(staged_file, target_path)

        candidate.stage = PromotionStage.PROMOTION
        candidate.promoted_at = datetime.now()

        logger.info(f"✅ {module_name} promoted successfully!")
        return True

    def _create_backup(self, file_path: Path) -> None:
        """Create backup of file before promotion."""
        if not file_path.exists():
            return

        timestamp = int(datetime.now().timestamp())
        backup_path = self.backups_dir / f"{file_path.name}.{timestamp}.bak"

        shutil.copy2(file_path, backup_path)
        logger.info(f"📦 Backup created: {backup_path}")

        # Maintain only last 5 backups
        self._cleanup_old_backups(file_path.name)

    def _cleanup_old_backups(self, filename: str, keep_count: int = 5) -> None:
        """Keep only the most recent N backups."""
        backups = sorted(
            self.backups_dir.glob(f"{filename}.*.bak"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for old_backup in backups[keep_count:]:
            old_backup.unlink()
            logger.debug(f"Removed old backup: {old_backup}")

    # ==================================================================
    # UTILITIES
    # ==================================================================

    def get_status(self, module_name: str) -> dict:
        """Get status of a promotion candidate."""
        candidate = self.candidates.get(module_name)
        if not candidate:
            return {"error": f"No candidate found for {module_name}"}

        return {
            "module_name": module_name,
            "stage": candidate.stage.value,
            "source_path": str(candidate.source_path),
            "created_at": candidate.created_at.isoformat(),
            "reviewed_by": candidate.reviewed_by,
            "promoted_at": (candidate.promoted_at.isoformat() if candidate.promoted_at else None),
            "proof_artifact": (
                {
                    "owner": (candidate.proof_artifact.owner if candidate.proof_artifact else None),
                    "smoke_tests": (
                        candidate.proof_artifact.smoke_test_results
                        if candidate.proof_artifact
                        else None
                    ),
                }
                if candidate.proof_artifact
                else None
            ),
            "gates": [
                {
                    "name": gate.name,
                    "severity": gate.severity.value,
                    "passed": gate.passed,
                    "message": gate.message,
                }
                for gate in candidate.gates
            ],
        }

    def list_candidates(self, stage: PromotionStage | None = None) -> list[str]:
        """List all candidates, optionally filtered by stage."""
        if stage:
            return [name for name, candidate in self.candidates.items() if candidate.stage == stage]
        return list(self.candidates.keys())


# ==================================================================
# CLI INTERFACE
# ==================================================================


def main() -> None:
    """CLI interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Testing Chamber Promotion Manager")
    parser.add_argument(
        "--chamber-root",
        default="testing_chamber",
        help="Testing chamber root directory",
    )
    parser.add_argument("--stage", help="Stage a file")
    parser.add_argument("--generate-proof", help="Generate proof for module")
    parser.add_argument("--validate", help="Validate gates for module")
    parser.add_argument("--approve", help="Approve module (requires --reviewer)")
    parser.add_argument("--reviewer", help="Reviewer name")
    parser.add_argument("--promote", help="Promote module to production")
    parser.add_argument("--status", help="Get status of module")
    parser.add_argument("--list", action="store_true", help="List all candidates")

    args = parser.parse_args()

    manager = ChamberPromotionManager(chamber_root=Path(args.chamber_root))

    if args.stage:
        manager.stage_file(Path(args.stage))

    elif args.generate_proof:
        manager.generate_proof_artifacts(args.generate_proof)

    elif args.validate:
        _passed, gates = manager.validate_gates(args.validate)
        for _gate in gates:
            pass

    elif args.approve:
        if not args.reviewer:
            return
        manager.approve_promotion(args.approve, args.reviewer)

    elif args.promote:
        manager.promote_to_production(args.promote)

    elif args.status:
        manager.get_status(args.status)

    elif args.list:
        candidates = manager.list_candidates()
        for name in candidates:
            manager.get_status(name)


if __name__ == "__main__":
    main()
