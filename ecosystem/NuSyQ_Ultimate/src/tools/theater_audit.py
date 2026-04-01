#!/usr/bin/env python3
"""
🎭 THEATER AUDIT - Ruthless OS Edition
======================================
Inspired by SimulatedVerse's Ruthless Operating System.
Scans codebase for "sophisticated theater" and generates elimination plan.

Theater Patterns Detected:
- TODO comments without issue links
- FIXME without context
- pass # placeholder
- NotImplementedError without plan
- Hardcoded console.log('THIS SHOULD...')
- if (false) or if True: pass
- Empty except: pass blocks
- Functions that only raise NotImplementedError

Philosophy: NO THEATER ALLOWED. Either implement it or remove it.
"""

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class TheaterInstance:
    """A single instance of theater detected"""

    file: str
    line_number: int
    line_content: str
    pattern_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    recommendation: str


@dataclass
class TheaterReport:
    """Complete theater audit report"""

    timestamp: datetime
    files_scanned: int
    total_lines: int
    theater_instances: List[TheaterInstance]
    theater_score: float  # 0.0 = no theater, 1.0 = all theater
    severity_breakdown: Dict[str, int]
    elimination_plan: List[str]


class TheaterAuditor:
    """Ruthless theater detection and elimination"""

    # Theater patterns with severity
    PATTERNS = {
        # Critical - Code that pretends to work
        r"if\s+(False|True)\s*:.*pass": ("CRITICAL", "Dead code masquerading as logic"),
        r"except\s*:\s*pass": ("CRITICAL", "Silent failure - hides bugs"),
        r'raise\s+NotImplementedError\(["\'].*?["\']?\)\s*$': (
            "CRITICAL",
            "Placeholder without plan",
        ),
        # High - Obvious placeholders
        r"TODO": ("HIGH", "TODO without issue link or date"),
        r"FIXME": ("HIGH", "FIXME without explanation"),
        r"XXX": ("HIGH", "XXX marker - unclear intent"),
        r"HACK": ("HIGH", "Acknowledged hack - needs proper solution"),
        r"pass\s*#\s*(?:placeholder|TODO|FIXME)": ("HIGH", "Explicit placeholder"),
        # Medium - Suspicious patterns
        r'print\(["\']THIS SHOULD': ("MEDIUM", "Debug print left in code"),
        r'console\.log\(["\']THIS SHOULD': ("MEDIUM", "Debug log left in code"),
        r"^\s*pass\s*$": ("MEDIUM", "Empty implementation"),
        r"def\s+\w+\([^)]*\)\s*:\s*pass\s*$": ("MEDIUM", "Empty function"),
        # Low - Could be legitimate
        r"# ?NOTE": ("LOW", "Unstructured note - consider docstring"),
        r"# ?TEMP": ("LOW", "Temporary code - should be cleaned"),
    }

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.instances: List[TheaterInstance] = []
        self.files_scanned = 0
        self.total_lines = 0

    def scan_file(self, file_path: Path) -> List[TheaterInstance]:
        """Scan a single file for theater"""
        instances = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                self.total_lines += len(lines)

                for line_num, line in enumerate(lines, 1):
                    for pattern, (severity, recommendation) in self.PATTERNS.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            instances.append(
                                TheaterInstance(
                                    file=str(file_path.relative_to(self.workspace)),
                                    line_number=line_num,
                                    line_content=line.strip(),
                                    pattern_type=pattern,
                                    severity=severity,
                                    recommendation=recommendation,
                                )
                            )
        except (OSError, UnicodeDecodeError, ValueError, TypeError, re.error) as e:
            print(f"  ⚠️  Error scanning {file_path}: {e}")

        return instances

    def scan_directory(self, directory: Path, extensions: Optional[List[str]] = None) -> int:
        """Recursively scan directory for theater"""
        if extensions is None:
            extensions = [".py"]
        print(f"🔍 Scanning: {directory.relative_to(self.workspace)}")

        count = 0
        for ext in extensions:
            for file_path in directory.rglob(f"*{ext}"):
                # Skip venv, node_modules, etc.
                if any(
                    part in file_path.parts
                    for part in [".venv", "venv", "node_modules", "__pycache__", ".git"]
                ):
                    continue

                self.files_scanned += 1
                instances = self.scan_file(file_path)
                self.instances.extend(instances)
                count += len(instances)

                if instances:
                    print(f"  ❌ {file_path.name}: {len(instances)} theater instances")

        return count

    def calculate_theater_score(self) -> float:
        """Calculate theater score (0.0 = clean, 1.0 = all theater)"""
        if self.total_lines == 0:
            return 0.0
        return len(self.instances) / self.total_lines

    def get_severity_breakdown(self) -> Dict[str, int]:
        """Count instances by severity"""
        breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for instance in self.instances:
            breakdown[instance.severity] += 1
        return breakdown

    def generate_elimination_plan(self) -> List[str]:
        """Generate actionable elimination plan"""
        plan = []

        # Group by file
        by_file: Dict[str, List[TheaterInstance]] = {}
        for instance in self.instances:
            if instance.file not in by_file:
                by_file[instance.file] = []
            by_file[instance.file].append(instance)

        # Sort files by severity (most critical first)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_files = sorted(
            by_file.items(), key=lambda x: min(severity_order[i.severity] for i in x[1])
        )

        for file, instances in sorted_files:
            plan.append(f"\n## {file} ({len(instances)} instances)")

            # Group by severity
            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                severe_instances = [i for i in instances if i.severity == severity]
                if severe_instances:
                    plan.append(f"\n### {severity} ({len(severe_instances)})")
                    for inst in severe_instances[:5]:  # Limit to 5 per severity
                        plan.append(f"- Line {inst.line_number}: `{inst.line_content[:60]}...`")
                        plan.append(f"  → {inst.recommendation}")

        return plan

    def generate_report(self) -> TheaterReport:
        """Generate comprehensive theater report"""
        return TheaterReport(
            timestamp=datetime.now(),
            files_scanned=self.files_scanned,
            total_lines=self.total_lines,
            theater_instances=self.instances,
            theater_score=self.calculate_theater_score(),
            severity_breakdown=self.get_severity_breakdown(),
            elimination_plan=self.generate_elimination_plan(),
        )

    def save_report(self, report: TheaterReport, output_dir: Path):
        """Save report as JSON and Markdown"""
        output_dir.mkdir(exist_ok=True)

        # JSON report (for programmatic use)
        json_file = output_dir / f"THEATER_AUDIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            # Convert dataclasses to dict
            report_dict = asdict(report)
            json.dump(report_dict, f, indent=2, default=str)

        # Markdown report (for humans)
        md_file = output_dir / (f"THEATER_AUDIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        md_content = self._generate_markdown(report)
        md_file.write_text(md_content, encoding="utf-8")

        print("\n💾 Reports saved:")
        print(f"  • {json_file.name}")
        print(f"  • {md_file.name}")

        return md_file

    def _generate_markdown(self, report: TheaterReport) -> str:
        """Generate markdown report"""
        severity = report.severity_breakdown

        md = f"""# 🎭 Theater Audit Report - Ruthless Edition

**Generated**: {report.timestamp.isoformat()}
**Philosophy**: SimulatedVerse Ruthless OS - NO THEATER ALLOWED

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| Files Scanned | {report.files_scanned} |
| Total Lines | {report.total_lines:,} |
| Theater Instances | {len(report.theater_instances)} |
        | **Theater Score** | **{report.theater_score:.4f}** (
        | {report.theater_score * 100:.2f}% ) |

### Theater Score Interpretation
- **0.00-0.01**: Excellent - Minimal theater
- **0.01-0.05**: Good - Some cleanup needed
- **0.05-0.10**: Warning - Significant theater detected
- **0.10+**: Critical - System drowning in theater!

---

## 🎯 Severity Breakdown

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 CRITICAL | {severity["CRITICAL"]} | Code that pretends to work |
| 🟠 HIGH | {severity["HIGH"]} | Obvious placeholders |
| 🟡 MEDIUM | {severity["MEDIUM"]} | Suspicious patterns |
| 🟢 LOW | {severity["LOW"]} | Could be legitimate |

---

## 📋 Elimination Plan

Priority order: CRITICAL → HIGH → MEDIUM → LOW

{"".join(report.elimination_plan)}

---

## 🎯 Top 10 Worst Offenders

"""
        # Show top 10 theater instances by severity
        sorted_instances = sorted(
            report.theater_instances,
            key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[x.severity],
        )[:10]

        for i, inst in enumerate(sorted_instances, 1):
            md += f"\n### {i}. {inst.file}:{inst.line_number} [{inst.severity}]\n"
            md += f"```python\n{inst.line_content}\n```\n"
            md += f"**Issue**: {inst.recommendation}\n"

        md += f"""
---

## 🔧 Recommended Actions

### Immediate (CRITICAL & HIGH)
1. Fix or remove all CRITICAL instances ({severity["CRITICAL"]} items)
2. Address HIGH severity items ({severity["HIGH"]} items)
3. Run tests after each fix to verify no breakage

### Short Term (MEDIUM)
1. Implement or remove MEDIUM severity items ({severity["MEDIUM"]} items)
2. Add proper error handling instead of silent failures
3. Replace debug prints with proper logging

### Long Term (LOW)
1. Convert unstructured comments to docstrings
2. Establish code review checklist to prevent theater
3. Add linting rules to catch theater patterns

---

## 🚫 Ruthless OS Principle

    > "The only acceptable amount of theater is ZERO. "
    > "Every TODO is a lie about future work."
    > "Every FIXME is an admission of current failure. "
    > "Every placeholder is technical debt."
> masquerading as progress. FIX IT OR DELETE IT." - Ruthless Operating System

---

## 📈 Next Steps

1. Run this audit weekly to track progress
2. Use ChatDev to implement placeholders systematically
3. Add CI/CD checks to prevent new theater
4. Celebrate when Theater Score reaches 0.00!

**Generated by**: Autonomous Theater Auditor
**Inspired by**: SimulatedVerse Ruthless OS
**Philosophy**: Culture Mind - Benevolent but NO THEATER
"""

        return md


def main():
    """Run theater audit"""
    workspace = Path(__file__).parent.parent

    print("=" * 70)
    print("🎭 THEATER AUDIT - RUTHLESS OPERATING SYSTEM EDITION")
    print("=" * 70)
    print("Philosophy: NO THEATER ALLOWED. Fix it or delete it.\n")

    auditor = TheaterAuditor(workspace)

    # Scan config directory (most critical)
    print("📁 Scanning config/...")
    auditor.scan_directory(workspace / "config")

    # Scan scripts directory
    print("\n📁 Scanning scripts/...")
    auditor.scan_directory(workspace / "scripts")

    # Scan tests directory
    print("\n📁 Scanning tests/...")
    auditor.scan_directory(workspace / "tests")

    # Scan MCP server
    print("\n📁 Scanning mcp_server/...")
    auditor.scan_directory(workspace / "mcp_server")

    # Generate report
    print("\n" + "=" * 70)
    print("📊 AUDIT COMPLETE")
    print("=" * 70)

    report = auditor.generate_report()

    print(f"\nFiles Scanned: {report.files_scanned}")
    print(f"Total Lines: {report.total_lines:,}")
    print(f"Theater Instances: {len(report.theater_instances)}")
    print(f"\n🎯 Theater Score: {report.theater_score:.4f} ({report.theater_score * 100:.2f}%)")

    severity = report.severity_breakdown
    print("\nSeverity Breakdown:")
    print(f"  🔴 CRITICAL: {severity['CRITICAL']}")
    print(f"  🟠 HIGH:     {severity['HIGH']}")
    print(f"  🟡 MEDIUM:   {severity['MEDIUM']}")
    print(f"  🟢 LOW:      {severity['LOW']}")

    # Save report
    report_file = auditor.save_report(report, workspace / "Reports")

    # Verdict
    print("\n" + "=" * 70)
    if report.theater_score < 0.01:
        print("✅ VERDICT: EXCELLENT - Minimal theater detected!")
    elif report.theater_score < 0.05:
        print("⚠️  VERDICT: GOOD - Some cleanup recommended")
    elif report.theater_score < 0.10:
        print("🔴 VERDICT: WARNING - Significant theater detected!")
    else:
        print("💀 VERDICT: CRITICAL - System drowning in theater!")
    print("=" * 70)

    print(f"\n📄 Full report: Reports/{report_file.name}")


if __name__ == "__main__":
    main()
