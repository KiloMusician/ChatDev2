# File organization checker

"""file_organization_auditor.py.

Purpose:
- Systematically detect misplaced files and suggest safe consolidation
    actions for repository cleanup.

Who/What/Where/When/Why/How:
- Who: Maintainers, CI pipelines, and automated agents performing repo
    hygiene tasks.
- What: Produces audit reports and a set of candidate fix actions (non-
    destructive suggestions by default).
- Where: Run from repository root; outputs logs to `file_organization_audit.log`.
- When: Periodic audits, pre-release cleanups, or as part of onboarding.
- Why: Improve discoverability and reduce duplication across the codebase.
- How: Use `FileOrganizationAuditor` to produce structured reports and
    optionally apply verified, reversible fixes.

Safety & integration:
- This tool writes logs and may perform file moves — run in dry-run mode
    before applying changes. Create patch files for reviewable PRs.

OmniTag: {
        "purpose": "file_systematically_tagged",
        "tags": ["Python"],
        "category": "auto_tagged",
        "evolution_stage": "v1.0"
}
"""

import json
import logging
import os
import re
import shutil
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("file_organization_audit.log"),
        logging.StreamHandler(),
    ],
)


@dataclass
class FileLocation:
    """Represents a file and its expected location."""

    current_path: str
    expected_path: str
    file_type: str
    category: str
    confidence: float
    reason: str


@dataclass
class OrganizationIssue:
    """Represents a file organization issue."""

    file_path: str
    issue_type: str
    suggested_location: str
    confidence: float
    auto_fixable: bool
    reason: str


class FileOrganizationAuditor:
    """Comprehensive file organization auditing system."""

    def __init__(self, repository_root: str) -> None:
        """Initialize FileOrganizationAuditor with repository_root."""
        self.repository_root = Path(repository_root)
        self.issues: list[Any] = []
        self.file_patterns = self._define_file_patterns()
        self.directory_structure = self._define_expected_structure()

    def _define_file_patterns(self) -> dict[str, dict]:
        """Define expected file patterns and their locations."""
        return {
            # Python files
            "python_source": {
                "pattern": r"\.py$",
                "expected_dirs": [
                    "src",
                    "lib",
                    "modules",
                    "core",
                    "spine",
                ],
                "exclude_names": [
                    "__init__.py",
                    "setup.py",
                    "conftest.py",
                ],
            },
            # Test files
            "test_files": {
                "pattern": r"(test_|_test\.py|tests\.py)$",
                "expected_dirs": ["tests", "test"],
                "exclude_names": [],
            },
            # Configuration files
            "config_files": {
                "pattern": r"\.(json|yaml|yml|toml|ini|cfg|conf)$",
                "expected_dirs": [
                    "config",
                    "configs",
                    ".vscode",
                    "setup",
                ],
                "exclude_names": [
                    "package.json",
                    "pyproject.toml",
                    "setup.cfg",
                ],
            },
            # Documentation
            "documentation": {
                "pattern": r"\.(md|rst|txt|doc|docx)$",
                "expected_dirs": [
                    "docs",
                    "documentation",
                    "README",
                ],
                "exclude_names": [
                    "README.md",
                    "CHANGELOG.md",
                    "LICENSE.txt",
                ],
            },
            # Scripts
            "scripts": {
                "pattern": r"\.(ps1|bat|sh|bash)$",
                "expected_dirs": [
                    "scripts",
                    "tools",
                    "setup",
                    "bin",
                ],
                "exclude_names": [],
            },
            # Data files
            "data_files": {
                "pattern": r"\.(csv|json|xml|xlsx|pickle|pkl|db|sqlite)$",
                "expected_dirs": [
                    "data",
                    "datasets",
                    "assets",
                    "resources",
                ],
                "exclude_names": [],
            },
            # Media files
            "media_files": {
                "pattern": r"\.(png|jpg|jpeg|gif|svg|ico|mp3|mp4|avi)$",
                "expected_dirs": [
                    "assets",
                    "media",
                    "images",
                    "resources",
                ],
                "exclude_names": [],
            },
            # Jupyter notebooks
            "notebooks": {
                "pattern": r"\.ipynb$",
                "expected_dirs": [
                    "notebooks",
                    "jupyter",
                    "analysis",
                    "experiments",
                ],
                "exclude_names": [],
            },
            # Web files
            "web_files": {
                "pattern": r"\.(html|css|js|jsx|ts|tsx)$",
                "expected_dirs": [
                    "web",
                    "frontend",
                    "static",
                    "templates",
                ],
                "exclude_names": [],
            },
            # Spine-specific files
            "spine_files": {
                "pattern": r"\.(spine|quantum|transcendent|consciousness|kardeshev)$",
                "expected_dirs": [
                    "Transcendent_Spine",
                    "spine",
                    "quantum",
                ],
                "exclude_names": [],
            },
        }

    def _define_expected_structure(self) -> dict[str, list[str]]:
        """Define the expected repository structure."""
        return {
            "root_files": [
                "README.md",
                "LICENSE",
                "requirements.txt",
                "setup.py",
                "pyproject.toml",
                ".gitignore",
                "CHANGELOG.md",
            ],
            "core_directories": [
                "src",
                "tests",
                "docs",
                "config",
                "tools",
                "scripts",
                "data",
                "assets",
                "Transcendent_Spine",
                "ΞNuSyQ₁-Hub₁",
            ],
            "generated_directories": [
                "__pycache__",
                ".pytest_cache",
                "venv",
                "venv_kilo",
                ".git",
                "node_modules",
                "dist",
                "build",
            ],
        }

    def scan_repository(self) -> list[OrganizationIssue]:
        """Scan the entire repository for organization issues."""
        logging.info("Starting repository organization audit...")

        all_files = self._get_all_files()
        issues: list[Any] = []
        for file_path in all_files:
            file_issues = self._analyze_file_location(file_path)
            issues.extend(file_issues)

        # Additional structure checks
        structure_issues = self._check_directory_structure()
        issues.extend(structure_issues)

        self.issues = issues
        logging.info(f"Found {len(issues)} organization issues")
        return issues

    def _get_all_files(self) -> list[Path]:
        """Get all files in the repository, excluding generated directories."""
        all_files: list[Any] = []
        exclude_dirs = self.directory_structure["generated_directories"]

        for file_path in self.repository_root.rglob("*"):
            if file_path.is_file() and not any(
                excluded in str(file_path) for excluded in exclude_dirs
            ):
                # Check if file is in excluded directory
                all_files.append(file_path)

        return all_files

    def _analyze_file_location(self, file_path: Path) -> list[OrganizationIssue]:
        """Analyze if a file is in the correct location."""
        issues: list[Any] = []
        relative_path = file_path.relative_to(self.repository_root)

        # Determine file type and expected location
        file_type, expected_dirs = self._classify_file(file_path)

        if file_type and expected_dirs:
            current_dir = relative_path.parent
            is_in_expected_location = any(
                expected in str(current_dir).lower() for expected in expected_dirs
            )

            if not is_in_expected_location:
                # Find the best matching expected directory
                suggested_location = self._suggest_location(file_path, expected_dirs)

                issue = OrganizationIssue(
                    file_path=str(relative_path),
                    issue_type="misplaced_file",
                    suggested_location=suggested_location,
                    confidence=self._calculate_confidence(file_path, file_type),
                    auto_fixable=True,
                    reason=f"{file_type} file should be in {expected_dirs}",
                )
                issues.append(issue)

        # Check for specific naming patterns
        naming_issues = self._check_naming_conventions(file_path)
        issues.extend(naming_issues)

        return issues

    def _classify_file(self, file_path: Path) -> tuple[str | None, list[str] | None]:
        """Classify a file and determine its expected location."""
        file_name = file_path.name.lower()

        for file_type, pattern_info in self.file_patterns.items():
            pattern = pattern_info["pattern"]
            exclude_names = pattern_info.get("exclude_names", [])

            # Check if file matches pattern and is not excluded
            if re.search(pattern, file_name, re.IGNORECASE) and file_name not in [
                name.lower() for name in exclude_names
            ]:
                return file_type, pattern_info["expected_dirs"]

        return None, None

    def _suggest_location(self, file_path: Path, expected_dirs: list[str]) -> str:
        """Suggest the best location for a misplaced file."""
        file_path.relative_to(self.repository_root)

        # Check which expected directories exist
        existing_dirs: list[Any] = []
        for expected_dir in expected_dirs:
            potential_path = self.repository_root / expected_dir
            if potential_path.exists():
                existing_dirs.append(expected_dir)

        # Prefer an existing dir; fall back to first expected (will be created)
        suggested_dir = existing_dirs[0] if existing_dirs else expected_dirs[0]

        return str(Path(suggested_dir) / file_path.name)

    def _calculate_confidence(self, file_path: Path, file_type: str) -> float:
        """Calculate confidence score for file placement suggestion."""
        confidence = 0.8  # Base confidence

        # Adjust based on file type specificity
        if file_type in ["test_files", "spine_files"]:
            confidence += 0.15  # Very specific file types
        elif file_type in ["config_files", "scripts"]:
            confidence += 0.1  # Moderately specific

        # Adjust based on current location
        current_dir = file_path.parent.name.lower()
        stale_dir_markers = (
            "temp",
            "tmp",
            "old",
            "backup",
        )
        if any(keyword in current_dir for keyword in stale_dir_markers):
            confidence += 0.1  # Clearly temporary location

        return min(confidence, 1.0)

    def _check_naming_conventions(self, file_path: Path) -> list[OrganizationIssue]:
        """Check for naming convention issues."""
        issues: list[Any] = []
        file_name = file_path.name

        # Check for spaces in filenames (should use underscores or hyphens)
        script_suffixes = (
            ".py",
            ".ps1",
            ".sh",
        )
        if " " in file_name and file_path.suffix.lower() in script_suffixes:
            issue = OrganizationIssue(
                file_path=str(file_path.relative_to(self.repository_root)),
                issue_type="naming_convention",
                suggested_location=str(file_path.relative_to(self.repository_root)).replace(
                    " ", "_"
                ),
                confidence=0.9,
                auto_fixable=True,
                reason="File name contains spaces, should use underscores",
            )
            issues.append(issue)

        # Check for uppercase in Python files (should be lowercase)
        if (
            file_path.suffix == ".py"
            and any(c.isupper() for c in file_path.stem)
            and not file_path.name.startswith("__")
        ):  # Exclude special files like __init__.py
            suggested_name = file_path.stem.lower() + file_path.suffix
            issue = OrganizationIssue(
                file_path=str(file_path.relative_to(self.repository_root)),
                issue_type="naming_convention",
                suggested_location=str(file_path.parent / suggested_name),
                confidence=0.7,
                auto_fixable=True,
                reason="Python files should use lowercase with underscores",
            )
            issues.append(issue)

        return issues

    def _check_directory_structure(self) -> list[OrganizationIssue]:
        """Check for directory structure issues."""
        issues: list[Any] = []
        # Check for empty directories in important locations
        for core_dir in self.directory_structure["core_directories"]:
            dir_path = self.repository_root / core_dir
            if (
                dir_path.exists() and dir_path.is_dir() and not any(dir_path.iterdir())
            ):  # Empty directory
                issue = OrganizationIssue(
                    file_path=str(Path(core_dir)),
                    issue_type="empty_directory",
                    suggested_location="",
                    confidence=0.6,
                    auto_fixable=False,
                    reason="Core directory is empty",
                )
                issues.append(issue)

        # Check for orphaned files in root
        root_files = [f for f in self.repository_root.iterdir() if f.is_file()]
        for file_path in root_files:
            if file_path.name not in self.directory_structure[
                "root_files"
            ] and not file_path.name.startswith(
                "."
            ):  # Ignore hidden files
                _file_type, expected_dirs = self._classify_file(file_path)
                if expected_dirs:
                    issue = OrganizationIssue(
                        file_path=file_path.name,
                        issue_type="orphaned_root_file",
                        suggested_location=self._suggest_location(file_path, expected_dirs),
                        confidence=0.8,
                        auto_fixable=True,
                        reason=f"File should be in {expected_dirs[0]} directory",
                    )
                    issues.append(issue)

        return issues

    def generate_report(self, output_path: str = "file_organization_report.json") -> dict:
        """Generate comprehensive organization report."""
        if not self.issues:
            self.scan_repository()

        # Group issues by type
        issues_by_type = defaultdict(list)
        issues_by_confidence = defaultdict(list)
        auto_fixable: list[Any] = []
        manual_review: list[Any] = []
        for issue in self.issues:
            issues_by_type[issue.issue_type].append(issue)

            confidence_bracket = (
                "high"
                if issue.confidence >= 0.8
                else "medium" if issue.confidence >= 0.6 else "low"
            )
            issues_by_confidence[confidence_bracket].append(issue)

            if issue.auto_fixable:
                auto_fixable.append(issue)
            else:
                manual_review.append(issue)

        report = {
            "summary": {
                "total_issues": len(self.issues),
                "auto_fixable": len(auto_fixable),
                "manual_review": len(manual_review),
                "by_type": {
                    issue_type: len(issues) for issue_type, issues in issues_by_type.items()
                },
                "by_confidence": {
                    conf: len(issues) for conf, issues in issues_by_confidence.items()
                },
            },
            "issues": [asdict(issue) for issue in self.issues],
            "recommendations": self._generate_recommendations(),
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logging.info(f"Generated organization report: {output_path}")
        return report

    def _generate_recommendations(self) -> list[str]:
        """Generate organization recommendations."""
        recommendations: list[Any] = []
        if not self.issues:
            recommendations.append("✅ Repository organization looks good!")
            return recommendations

        # Analyze common issues
        issue_types: dict[str, int] = defaultdict(int)
        for issue in self.issues:
            issue_types[issue.issue_type] += 1

        if issue_types.get("misplaced_file", 0) > 5:
            recommendations.append("📁 Consider reorganizing files into proper directories")

        if issue_types.get("naming_convention", 0) > 3:
            recommendations.append("📝 Standardize file naming conventions")

        if issue_types.get("orphaned_root_file", 0) > 2:
            recommendations.append("🧹 Move orphaned files from root to appropriate directories")

        auto_fixable_count = sum(1 for issue in self.issues if issue.auto_fixable)
        if auto_fixable_count > 0:
            recommendations.append(f"🔧 {auto_fixable_count} issues can be auto-fixed")

        return recommendations

    def auto_fix_issues(self, dry_run: bool = True, confidence_threshold: float = 0.8) -> int:
        """Automatically fix file organization issues."""
        if not self.issues:
            self.scan_repository()

        fixes_applied = 0
        fixable_issues = [
            issue
            for issue in self.issues
            if issue.auto_fixable and issue.confidence >= confidence_threshold
        ]

        logging.info(f"Auto-fixing {len(fixable_issues)} issues (dry_run={dry_run})")

        for issue in fixable_issues:
            try:
                source_path = self.repository_root / issue.file_path
                target_path = self.repository_root / issue.suggested_location

                if issue.issue_type == "misplaced_file":
                    # Create target directory if it doesn't exist
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    if not dry_run:
                        shutil.move(str(source_path), str(target_path))

                    logging.info(
                        f"{'Would move' if dry_run else 'Moved'}: {issue.file_path} -> {issue.suggested_location}"
                    )
                    fixes_applied += 1

                elif issue.issue_type == "naming_convention":
                    if not dry_run:
                        source_path.rename(target_path)

                    logging.info(
                        f"{'Would rename' if dry_run else 'Renamed'}: {issue.file_path} -> {issue.suggested_location}"
                    )
                    fixes_applied += 1

            except Exception as e:
                logging.exception(f"Failed to fix {issue.file_path}: {e}")

        logging.info(
            f"Auto-fix complete: {fixes_applied} fixes {'would be applied' if dry_run else 'applied'}"
        )
        return fixes_applied

    def suggest_directory_structure(self) -> dict[str, list[str]]:
        """Suggest an ideal directory structure based on current files."""
        file_types = defaultdict(list)

        # Analyze all files to suggest structure
        all_files = self._get_all_files()
        for file_path in all_files:
            file_type, _ = self._classify_file(file_path)
            if file_type:
                file_types[file_type].append(file_path)

        return {
            "src/": ["Core Python modules", "Main application code"],
            "tests/": [
                "Unit tests",
                "Integration tests",
                "Test utilities",
            ],
            "docs/": [
                "Documentation",
                "README files",
                "Guides",
            ],
            "config/": [
                "Configuration files",
                "Settings",
                "Environment configs",
            ],
            "tools/": [
                "Utility scripts",
                "Development tools",
                "Automation",
            ],
            "data/": [
                "Datasets",
                "Sample data",
                "Database files",
            ],
            "assets/": [
                "Images",
                "Media files",
                "Static resources",
            ],
            "scripts/": [
                "Build scripts",
                "Deployment scripts",
                "Utilities",
            ],
            "notebooks/": [
                "Jupyter notebooks",
                "Analysis",
                "Experiments",
            ],
            "Transcendent_Spine/": [
                "Spine components",
                "Quantum modules",
                "Advanced systems",
            ],
        }


def main() -> None:
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="KILO-FOOLISH File Organization Auditor")
    parser.add_argument(
        "--repository",
        "-r",
        default=".",
        help="Repository root path",
    )
    parser.add_argument("--fix", action="store_true", help="Automatically fix issues")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed")
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.8,
        help="Confidence threshold for auto-fix",
    )
    parser.add_argument("--output-dir", default=".", help="Output directory for reports")

    args = parser.parse_args()

    # Initialize auditor
    auditor = FileOrganizationAuditor(args.repository)

    # Scan repository
    issues = auditor.scan_repository()

    # Generate report
    report_path = os.path.join(args.output_dir, "file_organization_report.json")
    auditor.generate_report(report_path)

    # Auto-fix if requested
    if args.fix or args.dry_run:
        auditor.auto_fix_issues(
            dry_run=args.dry_run or not args.fix,
            confidence_threshold=args.confidence_threshold,
        )

    # Print summary

    # Show top issues
    if issues:
        for _issue in issues[:5]:
            pass

    # Show directory structure suggestion
    suggested_structure = auditor.suggest_directory_structure()
    for description in suggested_structure.values():
        for _desc in description[:2]:  # Show first 2 descriptions
            pass


if __name__ == "__main__":
    main()
