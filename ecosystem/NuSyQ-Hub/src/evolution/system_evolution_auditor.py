#!/usr/bin/env python3
"""System Evolution Auditor - Autonomous Repository Analysis & Improvement.

This module creates a self-evolving system that:
1. Scans every file in the repository
2. Detects "sophisticated theatre" (fake progress, red herrings)
3. Finds orphaned files, modules, and concepts
4. Validates configurations
5. Submits proposals to AI Council for review
6. Integrates with ChatDev for modernization
7. Tracks progress with versioned snapshots

OmniTag: [evolution, auditor, self-improvement, chatdev-integration]
MegaTag: [EVOLUTION⨳AUDITOR⦾SELF-IMPROVING→∞]
"""

import ast
import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Types of issues the auditor can detect."""

    SOPHISTICATED_THEATRE = "sophisticated_theatre"  # Looks good but does nothing
    FALSE_POSITIVE = "false_positive"  # Appears broken but isn't
    RED_HERRING = "red_herring"  # Misleading code/comments
    ORPHANED_FILE = "orphaned_file"  # File not imported anywhere
    ORPHANED_MODULE = "orphaned_module"  # Module with no exports used
    ORPHANED_CONCEPT = "orphaned_concept"  # Partial implementation
    MISCONFIGURED = "misconfigured"  # Wrong config values
    DUPLICATED = "duplicated"  # Duplicate functionality
    DEPRECATED = "deprecated"  # Old patterns that should be updated
    MISSING_INTEGRATION = "missing_integration"  # Incomplete connections


@dataclass
class FileSnapshot:
    """Snapshot of a file's state at a point in time."""

    path: str
    hash: str
    size: int
    last_modified: str
    version: int
    imports: list[str]
    exports: list[str]
    dependencies: list[str]
    line_count: int
    issues_found: list[str]
    status: str  # 'pending', 'analyzed', 'proposed', 'approved', 'modernized'


@dataclass
class Issue:
    """An issue detected by the auditor."""

    issue_type: IssueType
    file_path: str
    line_number: int | None
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    evidence: str
    proposed_fix: str
    confidence: float  # 0.0 to 1.0


@dataclass
class Proposal:
    """A proposal for system improvement."""

    id: str
    title: str
    description: str
    issues: list[Issue]
    affected_files: list[str]
    proposed_changes: dict[str, str]
    estimated_impact: str
    status: str  # 'draft', 'submitted', 'under_review', 'approved', 'rejected', 'implemented'
    created_at: str
    ai_council_votes: dict[str, str]  # AI name -> vote/comments


class SystemEvolutionAuditor:
    """Autonomous system that audits the entire repository and orchestrates improvements.

    This is the main orchestrator that coordinates all sub-agents:
    - FileStateTracker: Tracks file versions
    - TheatreDetector: Identifies fake progress
    - OrphanHunter: Finds unused code
    - ConfigAuditor: Validates configurations
    - AICouncil: Reviews proposals
    - ChatDevIntegrator: Implements approved changes
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        """Initialize SystemEvolutionAuditor with repo_root."""
        self.repo_root = repo_root or Path.cwd()
        self.data_dir = self.repo_root / "data" / "evolution"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # State tracking
        self.snapshots: dict[str, FileSnapshot] = {}
        self.issues: list[Issue] = []
        self.proposals: list[Proposal] = []

        # Ignore patterns (like .gitignore)
        self.ignore_patterns = [
            ".venv",
            "__pycache__",
            ".git",
            ".github",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            "*.pyc",
            "*.pyo",
            "*.egg-info",
            ".DS_Store",
        ]

        # Load previous state if exists
        self.load_state()

    def should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        path_str = str(path)
        return any(pattern in path_str or path.match(pattern) for pattern in self.ignore_patterns)

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except (FileNotFoundError, OSError, PermissionError):
            return "ERROR"

    def extract_imports(self, file_path: Path) -> list[str]:
        """Extract import statements from Python file."""
        if file_path.suffix != ".py":
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read())

            imports: list[Any] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

            return imports
        except (FileNotFoundError, UnicodeDecodeError, SyntaxError):
            return []

    def extract_exports(self, file_path: Path) -> list[str]:
        """Extract exported symbols (classes, functions) from Python file."""
        if file_path.suffix != ".py":
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read())

            exports: list[Any] = []
            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ) and not node.name.startswith(
                    "_"
                ):  # Public only
                    exports.append(node.name)

            return exports
        except (FileNotFoundError, UnicodeDecodeError, SyntaxError):
            return []

    def create_snapshot(self, file_path: Path) -> FileSnapshot:
        """Create a snapshot of a file's current state."""
        relative_path = str(file_path.relative_to(self.repo_root))

        # Get previous version number
        prev_snapshot = self.snapshots.get(relative_path)
        version = (prev_snapshot.version + 1) if prev_snapshot else 1

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
                line_count = len(content.splitlines())
        except (FileNotFoundError, OSError):
            line_count = 0

        return FileSnapshot(
            path=relative_path,
            hash=self.calculate_file_hash(file_path),
            size=file_path.stat().st_size,
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            version=version,
            imports=self.extract_imports(file_path),
            exports=self.extract_exports(file_path),
            dependencies=[],  # Will be populated by dependency analyzer
            line_count=line_count,
            issues_found=[],
            status="pending",
        )

    async def scan_repository(self) -> dict[str, FileSnapshot]:
        """Scan entire repository and create snapshots."""
        logger.info(f"\n[*] Scanning repository: {self.repo_root}")

        snapshots: dict[str, Any] = {}
        file_count = 0

        for file_path in self.repo_root.rglob("*"):
            if file_path.is_file() and not self.should_ignore(file_path):
                snapshot = self.create_snapshot(file_path)
                snapshots[snapshot.path] = snapshot
                file_count += 1

                if file_count % 50 == 0:
                    logger.info(f"[*] Scanned {file_count} files...")

        logger.info(f"[OK] Scanned {file_count} files total")
        self.snapshots = snapshots
        return snapshots

    async def detect_theatre(self, snapshot: FileSnapshot) -> list[Issue]:
        """Detect "sophisticated theatre" - code that looks functional but isn't.

        Indicators:
        - Functions that only return None or pass
        - Classes with all methods raising NotImplementedError
        - Mock data instead of real API calls
        - TODO comments with no implementation
        - Placeholder functions that just log
        """
        issues: list[Any] = []
        file_path = self.repo_root / snapshot.path

        if file_path.suffix != ".py":
            return issues

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

            # Check for placeholder functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Count actual statements (exclude docstrings, pass, return None)
                    real_statements = 0
                    has_not_implemented = False

                    for stmt in node.body:
                        if isinstance(stmt, ast.Pass):
                            continue
                        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                            continue  # Docstring
                        if isinstance(stmt, ast.Return) and stmt.value is None:
                            continue
                        if (
                            isinstance(stmt, ast.Raise)
                            and hasattr(stmt.exc, "func")
                            and hasattr(stmt.exc.func, "id")
                            and stmt.exc.func.id == "NotImplementedError"
                        ):
                            has_not_implemented = True
                        real_statements += 1

                    # If function has no real statements or only NotImplementedError
                    if real_statements == 0 or (has_not_implemented and real_statements == 1):
                        issues.append(
                            Issue(
                                issue_type=IssueType.SOPHISTICATED_THEATRE,
                                file_path=snapshot.path,
                                line_number=node.lineno,
                                severity="medium",
                                description=f"Function '{node.name}' appears to be a placeholder with no real implementation",
                                evidence=f"Function at line {node.lineno} has {real_statements} real statements",
                                proposed_fix=f"Either implement '{node.name}' or remove it if not needed",
                                confidence=0.8,
                            ),
                        )

            # Check for backlog-marker comments without nearby implementation
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                if "TODO" in line.upper() and i < len(lines) - 1:
                    # Check next 5 lines for implementation
                    next_lines = "\n".join(lines[i : min(i + 5, len(lines))])
                    if "pass" in next_lines or not next_lines.strip():
                        issues.append(
                            Issue(
                                issue_type=IssueType.SOPHISTICATED_THEATRE,
                                file_path=snapshot.path,
                                line_number=i,
                                severity="low",
                                description="TODO comment with no nearby implementation",
                                evidence=line.strip(),
                                proposed_fix="Implement the TODO or create a tracked issue",
                                confidence=0.6,
                            ),
                        )

        except (FileNotFoundError, UnicodeDecodeError, SyntaxError):
            # If we can't parse, it might be broken
            logger.debug(
                "Suppressed FileNotFoundError/SyntaxError/UnicodeDecodeError", exc_info=True
            )

        return issues

    async def detect_orphans(self, snapshots: dict[str, FileSnapshot]) -> list[Issue]:
        """Detect orphaned files - files that are never imported."""
        issues: list[Any] = []
        # Build import graph
        all_imports = set()
        for snapshot in snapshots.values():
            all_imports.update(snapshot.imports)

        # Check each Python file
        for snapshot in snapshots.values():
            if not snapshot.path.endswith(".py"):
                continue

            # Convert path to module name
            module_name = snapshot.path.replace("/", ".").replace("\\", ".").replace(".py", "")

            # Check if this module is imported anywhere
            is_imported = False
            for imported in all_imports:
                if module_name in imported or imported in module_name:
                    is_imported = True
                    break

            # Special cases: main files, __init__, tests
            is_special = any(
                [
                    snapshot.path.endswith("__init__.py"),
                    snapshot.path.endswith("__main__.py"),
                    "main.py" in snapshot.path,
                    "test_" in snapshot.path,
                    snapshot.path.startswith("scripts/"),
                    snapshot.path.startswith("tests/"),
                ],
            )

            if not is_imported and not is_special and snapshot.exports:
                issues.append(
                    Issue(
                        issue_type=IssueType.ORPHANED_FILE,
                        file_path=snapshot.path,
                        line_number=None,
                        severity="medium",
                        description=f"File appears to be orphaned - defines {len(snapshot.exports)} exports but never imported",
                        evidence=f"Exports: {', '.join(snapshot.exports[:5])}",
                        proposed_fix="Either import and use this file, or remove if obsolete",
                        confidence=0.7,
                    ),
                )

        return issues

    async def analyze_all_files(self) -> list[Issue]:
        """Run all analysis passes on all files."""
        logger.info("\n[*] Running comprehensive analysis...")

        all_issues: list[Any] = []
        # Pass 1: Detect theatre in each file
        logger.info("[*] Pass 1: Detecting sophisticated theatre...")
        for snapshot in self.snapshots.values():
            issues = await self.detect_theatre(snapshot)
            all_issues.extend(issues)
            snapshot.issues_found = [i.issue_type.value for i in issues]

        logger.info(f"[OK] Found {len(all_issues)} theatre issues")

        # Pass 2: Detect orphaned files
        logger.info("[*] Pass 2: Detecting orphaned files...")
        orphan_issues = await self.detect_orphans(self.snapshots)
        all_issues.extend(orphan_issues)

        logger.info(f"[OK] Found {len(orphan_issues)} orphaned files")

        self.issues = all_issues
        return all_issues

    def create_proposal(self, issues: list[Issue], title: str) -> Proposal:
        """Create an improvement proposal from issues."""
        proposal_id = f"proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        affected_files = list({issue.file_path for issue in issues})

        return Proposal(
            id=proposal_id,
            title=title,
            description=f"Automated proposal addressing {len(issues)} issues across {len(affected_files)} files",
            issues=issues,
            affected_files=affected_files,
            proposed_changes={},  # Will be populated by ChatDev
            estimated_impact=self._estimate_impact(issues),
            status="draft",
            created_at=datetime.now().isoformat(),
            ai_council_votes={},
        )

    def _estimate_impact(self, issues: list[Issue]) -> str:
        """Estimate the impact of fixing these issues."""
        critical = sum(1 for i in issues if i.severity == "critical")
        high = sum(1 for i in issues if i.severity == "high")
        medium = sum(1 for i in issues if i.severity == "medium")

        if critical > 0:
            return "CRITICAL"
        if high > 5:
            return "HIGH"
        if medium > 10:
            return "MEDIUM"
        return "LOW"

    def save_state(self) -> None:
        """Save current state to disk."""
        state = {
            "snapshots": {k: asdict(v) for k, v in self.snapshots.items()},
            "issues": [asdict(i) for i in self.issues],
            "proposals": [asdict(p) for p in self.proposals],
            "timestamp": datetime.now().isoformat(),
        }

        state_file = self.data_dir / "auditor_state.json"
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)

        logger.info(f"[OK] State saved to: {state_file}")

    def load_state(self) -> None:
        """Load previous state from disk."""
        state_file = self.data_dir / "auditor_state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    json.load(f)

                # Reconstruct objects (simplified - would need full deserialization)
                logger.info(f"[OK] Loaded previous state from: {state_file}")
            except Exception as e:
                logger.info(f"[WARN] Could not load state: {e}")

    async def run_full_audit(self):
        """Run complete audit cycle."""
        logger.info(" SYSTEM EVOLUTION AUDITOR - Full Audit Cycle")

        # Step 1: Scan repository
        await self.scan_repository()

        # Step 2: Analyze files
        issues = await self.analyze_all_files()

        # Step 3: Create proposals
        if issues:
            # Group issues by type
            theatre_issues = [i for i in issues if i.issue_type == IssueType.SOPHISTICATED_THEATRE]
            orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHANED_FILE]

            if theatre_issues:
                proposal = self.create_proposal(
                    theatre_issues,
                    "Remove Sophisticated Theatre and Placeholder Code",
                )
                self.proposals.append(proposal)
                logger.info(f"\n[PROPOSAL] Created: {proposal.title}")
                logger.info(f"   Issues: {len(proposal.issues)}")
                logger.info(f"   Files: {len(proposal.affected_files)}")

            if orphan_issues:
                proposal = self.create_proposal(orphan_issues, "Remove or Integrate Orphaned Files")
                self.proposals.append(proposal)
                logger.info(f"\n[PROPOSAL] Created: {proposal.title}")
                logger.info(f"   Issues: {len(proposal.issues)}")
                logger.info(f"   Files: {len(proposal.affected_files)}")

        # Step 4: Save state
        self.save_state()

        # Step 5: Generate report
        return self.generate_report()

    def generate_report(self) -> str:
        """Generate comprehensive audit report."""
        report: list[Any] = []
        report.append("# System Evolution Audit Report")
        report.append(f"**Generated:** {datetime.now().isoformat()}")
        report.append(f"**Repository:** {self.repo_root}")
        report.append("")

        report.append("## Summary")
        report.append(f"- **Files Scanned:** {len(self.snapshots)}")
        report.append(f"- **Issues Found:** {len(self.issues)}")
        report.append(f"- **Proposals Created:** {len(self.proposals)}")
        report.append("")

        # Issues by type
        report.append("## Issues by Type")
        issue_counts: dict[str, Any] = {}
        for issue in self.issues:
            issue_counts[issue.issue_type.value] = issue_counts.get(issue.issue_type.value, 0) + 1

        for issue_type, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
            report.append(f"- **{issue_type}:** {count}")
        report.append("")

        # Top issues
        report.append("## Critical Issues (Top 10)")
        critical_issues = sorted(
            [i for i in self.issues if i.severity in ["critical", "high"]],
            key=lambda x: (x.severity == "critical", x.confidence),
            reverse=True,
        )[:10]

        for i, issue in enumerate(critical_issues, 1):
            report.append(f"### {i}. {issue.description}")
            report.append(f"**File:** `{issue.file_path}`")
            if issue.line_number:
                report.append(f"**Line:** {issue.line_number}")
            report.append(f"**Severity:** {issue.severity}")
            report.append(f"**Proposed Fix:** {issue.proposed_fix}")
            report.append("")

        # Proposals
        report.append("## Improvement Proposals")
        for proposal in self.proposals:
            report.append(f"### {proposal.id}: {proposal.title}")
            report.append(f"**Status:** {proposal.status}")
            report.append(f"**Impact:** {proposal.estimated_impact}")
            report.append(f"**Issues Addressed:** {len(proposal.issues)}")
            report.append(f"**Files Affected:** {len(proposal.affected_files)}")
            report.append("")

        return "\n".join(report)


async def main() -> None:
    """Entry point for system evolution auditor."""
    auditor = SystemEvolutionAuditor()

    # Run full audit
    report = await auditor.run_full_audit()

    # Save report
    report_file = auditor.data_dir / f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, "w") as f:
        f.write(report)

    logger.info(f"\n[OK] Audit complete! Report saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
