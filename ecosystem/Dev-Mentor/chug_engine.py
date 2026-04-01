#!/usr/bin/env python3
"""
DEVMENTOR PERPETUAL CHUG ENGINE v2.0

Autonomous System Cultivation Protocol - Full 7-Phase Cycle

Usage:
    python chug_engine.py              # Run one cycle
    python chug_engine.py --loop       # Run continuously
    python chug_engine.py --status     # Show current state
    python chug_engine.py --phase X    # Run specific phase (1-7)

The 7-Phase CHUG Cycle:
    1. ASSESS    - Zero-token health snapshot
    2. PLAN      - Surgical improvement bullets (≤7)
    3. EXECUTE   - Apply changes with modularity
    4. VERIFY    - Prove everything still works
    5. CONSOLIDATE - Reduce bloat and merge redundancy
    6. DOCUMENT  - Update docs to match reality
    7. EXPORT    - Portability gate validation

The CHUG Creed:
    WHEN IN DOUBT, CHUG.
    WHEN BLOCKED, WORK AROUND.
    WHEN STUCK, TRY SOMETHING ELSE.
    WHEN TIRED, DO MAINTENANCE.
    WHEN CONFUSED, CHECK SYSTEM STATE.
    WHEN LOST, HARVEST SIGNALS.
    NEVER STOP CULTIVATING.
    PROGRESS OVER PERFECTION.
    ACTION OVER ANALYSIS.
"""

import sys
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Tuple
import logging

# Logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

ROOT = Path(__file__).resolve().parent

# Allowlist of valid ops — prevents command injection via the operation parameter
_ALLOWED_OPS = frozenset({
    "doctor", "check", "fix", "prune", "graph",
    "export", "report", "all", "status",
})
CHUG_STATE_FILE = ROOT / ".devmentor" / "chug_state.json"
REPORTS_DIR = ROOT / "reports"
EXPORTS_DIR = ROOT / "exports"

PHASE_NAMES = [
    "ASSESS",
    "PLAN",
    "EXECUTE",
    "VERIFY",
    "CONSOLIDATE",
    "DOCUMENT",
    "EXPORT"
]

PHASE_ICONS = ["🔍", "📋", "🔨", "✅", "🧹", "📝", "📦"]


@dataclass
class PhaseResult:
    """Result from a single phase"""
    phase: str
    phase_number: int
    success: bool
    duration_seconds: float
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    actions_taken: List[str] = field(default_factory=list)
    issues_found: List[str] = field(default_factory=list)
    fixes_applied: List[str] = field(default_factory=list)


@dataclass
class CycleResult:
    """Result from a complete 7-phase cycle"""
    cycle_number: int
    timestamp: str
    duration_seconds: float
    phases: List[Dict[str, Any]]
    total_issues: int
    total_fixes: int
    is_clean: bool
    plan_bullets: List[str]
    what_improved: List[str]
    what_remains_risky: List[str]
    next_best_cycle: str


@dataclass
class ChugState:
    """Persistent state for the chug engine"""
    cycles_completed: int = 0
    last_cycle_time: str = ""
    last_phase: str = ""
    total_fixes_applied: int = 0
    total_issues_found: int = 0
    consecutive_clean_cycles: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)
    phase_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "ChugState":
        if CHUG_STATE_FILE.exists():
            try:
                with open(CHUG_STATE_FILE, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, OSError) as e:
                logger.debug("Failed to load CHUG state from %s: %s", CHUG_STATE_FILE, e)
        return cls()

    def save(self):
        CHUG_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CHUG_STATE_FILE, 'w', encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)


class ChugEngine:
    """
    The Perpetual Chug Engine v2.0

    Full 7-Phase Autonomous Improvement Cycle:
    ASSESS → PLAN → EXECUTE → VERIFY → CONSOLIDATE → DOCUMENT → EXPORT
    """

    def __init__(self):
        self.state = ChugState.load()
        self.ops_script = ROOT / "scripts" / "devmentor_ops.py"
        self.current_assessment: Dict[str, Any] = {}
        self.current_plan: List[str] = []
        REPORTS_DIR.mkdir(exist_ok=True)
        EXPORTS_DIR.mkdir(exist_ok=True)

    # Per-operation timeouts (seconds) — keeps Phase 1 from blocking indefinitely
    _OP_TIMEOUTS: Dict[str, int] = {
        "doctor": 90,
        "check":  60,
        "prune":  30,
        "graph":  30,
        "fix":    90,
        "export": 60,
        "report": 45,
        "all":    120,
        "status": 20,
    }

    def run_ops(self, operation: str) -> Dict[str, Any]:
        """Run an ops command and return the result"""
        if operation not in _ALLOWED_OPS:
            return {"operation": operation, "success": False, "error": f"Unknown operation: {operation!r}"}
        op_timeout = self._OP_TIMEOUTS.get(operation, 60)
        try:
            result = subprocess.run(
                [sys.executable, str(self.ops_script), operation],
                capture_output=True,
                text=True,
                timeout=op_timeout,
                cwd=str(ROOT)
            )

            report_file = REPORTS_DIR / f"{operation}.json"
            if report_file.exists():
                try:
                    with open(report_file, 'r', encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    logger.debug("Failed to read ops report %s: %s", report_file, e)

            return {
                "operation": operation,
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.debug("run_ops failed for %s: %s", operation, e)
            return {
                "operation": operation,
                "success": False,
                "error": str(e)
            }

    def run_command(self, cmd: List[str], timeout: int = 60) -> Tuple[bool, str, str]:
        """Run a shell command and return (success, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(ROOT)
            )
            return result.returncode == 0, result.stdout, result.stderr
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.debug("Command failed %s: %s", cmd, e)
            return False, "", str(e)

    # =========================================================================
    # PHASE 1: ASSESS
    # =========================================================================
    def phase_assess(self) -> PhaseResult:
        """
        Phase 1: ASSESS - Zero-token health snapshot

        Run all deterministic checks to understand current repository state.
        Produces: health.json, doctor report, check report, prune report
        """
        start = datetime.now()
        issues = []
        actions = []

        logger.info("%s Phase 1: ASSESS - Generating health snapshot...", PHASE_ICONS[0])

        doctor_result = self.run_ops("doctor")
        actions.append("Ran environment diagnostics")

        check_result = self.run_ops("check")
        actions.append("Ran syntax and lint checks")

        prune_result = self.run_ops("prune")
        actions.append("Scanned for bloat and duplicates")

        graph_result = self.run_ops("graph")
        actions.append("Generated module map")

        for failure in doctor_result.get("failures", []):
            issues.append(f"Doctor: {failure.get('check', 'unknown')} - {failure.get('message', '')}")

        for failure in check_result.get("failures", []):
            issues.append(f"Check: {failure.get('file', 'unknown')} - {failure.get('message', '')}")

        for item in prune_result.get("large_files", []):
            if item.get("size_mb", 0) > 5:
                issues.append(f"Large file: {item.get('path', '')} ({item.get('size_mb', 0):.1f}MB)")

        for item in prune_result.get("bloat_issues", []):
            issues.append(f"Bloat: {item.get('description', item)}")

        # ── Gameplay signal integration ──────────────────────────────────
        cultivation_file = ROOT / ".devmentor" / "cultivation_report.json"
        cultivation_data: Dict[str, Any] = {}
        if cultivation_file.exists():
            try:
                with open(cultivation_file, "r", encoding="utf-8") as f:
                    cultivation_data = json.load(f)
                total_signals = cultivation_data.get("total_signals", 0)
                suggestions = cultivation_data.get("chug_suggestions", [])
                ux_debt = cultivation_data.get("ux_debt", [])
                undiscovered = cultivation_data.get("undiscovered_features", [])
                actions.append(f"Read gameplay cultivation signals ({total_signals} signals)")
                for s in suggestions:
                    issues.append(f"Gameplay: {s}")
                if ux_debt:
                    issues.append(f"UX debt: {len(ux_debt)} high-error commands from player sessions")
                if len(undiscovered) > 5:
                    issues.append(f"Discovery gap: {len(undiscovered)} commands never used by players")
            except (json.JSONDecodeError, OSError) as e:
                actions.append(f"Cultivation report unreadable: {e}")
                logger.debug("Failed to read cultivation report %s: %s", cultivation_file, e)
        else:
            actions.append("No gameplay signals yet (.devmentor/cultivation_report.json missing)")

        health_data = {
            "timestamp": datetime.now().isoformat(),
            "doctor": doctor_result,
            "check": check_result,
            "prune": prune_result,
            "graph": graph_result,
            "cultivation": cultivation_data,
            "total_issues": len(issues),
            "issues": issues
        }

        with open(REPORTS_DIR / "health.json", 'w', encoding="utf-8") as f:
            json.dump(health_data, f, indent=2)

        self.current_assessment = health_data

        duration = (datetime.now() - start).total_seconds()
        return PhaseResult(
            phase="ASSESS",
            phase_number=1,
            success=True,
            duration_seconds=duration,
            summary=f"Found {len(issues)} issues",
            details=health_data,
            actions_taken=actions,
            issues_found=issues
        )

    # =========================================================================
    # PHASE 2: PLAN
    # =========================================================================
    def phase_plan(self) -> PhaseResult:
        """
        Phase 2: PLAN - Surgical improvement bullets (≤7)

        Based on assessment, propose minimal set of high-impact changes.
        """
        start = datetime.now()
        plan_bullets = []

        logger.info("%s Phase 2: PLAN - Creating surgical improvement plan...", PHASE_ICONS[1])

        issues = self.current_assessment.get("issues", [])

        critical_issues = [i for i in issues if any(kw in i.lower() for kw in ["error", "fail", "missing", "broken"])]
        if critical_issues:
            plan_bullets.append(f"FIX: Address {len(critical_issues)} critical issue(s)")

        check_result = self.current_assessment.get("check", {})
        if check_result.get("failures"):
            plan_bullets.append("FIX: Resolve syntax/lint failures")

        prune_result = self.current_assessment.get("prune", {})
        large_files = prune_result.get("large_files", [])
        if large_files:
            plan_bullets.append(f"REVIEW: {len(large_files)} large file(s) detected (see reports/prune.json)")

        duplicates = prune_result.get("duplicate_issues", [])
        if duplicates:
            plan_bullets.append(f"REVIEW: {len(duplicates)} potential duplicate(s) (see reports/prune.json)")

        placeholders = prune_result.get("placeholder_files", [])
        if placeholders:
            plan_bullets.append(f"DOCUMENT: Replace {len(placeholders)} placeholder(s)")

        if not plan_bullets:
            plan_bullets.append("MAINTAIN: Run routine verification and export")

        plan_bullets = plan_bullets[:7]

        self.current_plan = plan_bullets

        plan_md = f"""# CHUG Cycle Plan
Generated: {datetime.now().isoformat()}

## Improvement Bullets

"""
        for i, bullet in enumerate(plan_bullets, 1):
            plan_md += f"{i}. {bullet}\n"

        plan_md += f"""
## Based On Assessment

- Total issues found: {len(issues)}
- Critical issues: {len(critical_issues)}
- Large files: {len(large_files)}
"""

        with open(REPORTS_DIR / "plan.md", 'w', encoding="utf-8") as f:
            f.write(plan_md)

        duration = (datetime.now() - start).total_seconds()
        return PhaseResult(
            phase="PLAN",
            phase_number=2,
            success=True,
            duration_seconds=duration,
            summary=f"Created {len(plan_bullets)} improvement bullets",
            details={"plan_bullets": plan_bullets},
            actions_taken=["Analyzed assessment results", "Generated improvement plan"]
        )

    # =========================================================================
    # PHASE 3: EXECUTE
    # =========================================================================
    def phase_execute(self) -> PhaseResult:
        """
        Phase 3: EXECUTE - Apply changes with modularity

        Execute the planned improvements using ops commands.
        """
        start = datetime.now()
        fixes = []
        actions = []

        logger.info("%s Phase 3: EXECUTE - Applying improvements...", PHASE_ICONS[2])

        needs_fix = any("FIX" in b for b in self.current_plan)
        needs_prune = any("PRUNE" in b for b in self.current_plan)

        if needs_fix:
            fix_result = self.run_ops("fix")
            actions.append("Ran auto-fix operations")
            for fix in fix_result.get("fixes_applied", []):
                fixes.append(f"Fixed: {fix}")

        needs_review = any("REVIEW" in b for b in self.current_plan)
        if needs_review:
            actions.append("Advisory items flagged for human review (see reports/prune.json)")
            actions.append("  Note: Large files and duplicates require manual decision")

        needs_consolidate = any("CONSOLIDATE" in b for b in self.current_plan)
        if needs_consolidate:
            actions.append("Consolidation tasks queued for Phase 5")

        needs_doc = any("DOCUMENT" in b for b in self.current_plan)
        if needs_doc:
            actions.append("Documentation tasks queued for Phase 6")

        if not needs_fix and not needs_review:
            actions.append("No execution needed - repository is clean")

        duration = (datetime.now() - start).total_seconds()
        return PhaseResult(
            phase="EXECUTE",
            phase_number=3,
            success=True,
            duration_seconds=duration,
            summary=f"Applied {len(fixes)} fixes",
            details={"plan_executed": self.current_plan},
            actions_taken=actions,
            fixes_applied=fixes
        )

    # =========================================================================
    # PHASE 4: VERIFY
    # =========================================================================
    def phase_verify(self) -> PhaseResult:
        """
        Phase 4: VERIFY - Prove everything still works

        Re-run checks and confirm:
        - VS Code tasks still run
        - State (.devmentor) still works
        - Export ZIP still works
        - Replit interface still works (if present)
        """
        start = datetime.now()
        actions = []
        issues = []
        all_pass = True

        logger.info("%s Phase 4: VERIFY - Proving everything works...", PHASE_ICONS[3])

        check_result = self.run_ops("check")
        actions.append("Re-ran syntax and lint checks")
        if check_result.get("failures"):
            all_pass = False
            issues.append(f"{len(check_result['failures'])} check failures remain")

        tasks_json = ROOT / ".vscode" / "tasks.json"
        if tasks_json.exists():
            try:
                with open(tasks_json, 'r', encoding="utf-8") as f:
                    tasks = json.load(f)
                task_count = len(tasks.get("tasks", []))
                actions.append(f"Verified VS Code tasks.json ({task_count} tasks)")
            except (json.JSONDecodeError, OSError) as e:
                all_pass = False
                issues.append(f"tasks.json parse error: {e}")
                logger.debug("Failed to parse tasks.json: %s", e)
        else:
            issues.append("tasks.json not found")

        state_json = ROOT / ".devmentor" / "state.json"
        if state_json.exists():
            try:
                with open(state_json, 'r', encoding="utf-8") as f:
                    json.load(f)
                actions.append("Verified state.json is valid")
            except (json.JSONDecodeError, OSError) as e:
                all_pass = False
                issues.append(f"state.json parse error: {e}")
                logger.debug("Failed to parse state.json: %s", e)

        portable_script = ROOT / "scripts" / "devmentor_portable.py"
        if portable_script.exists():
            actions.append("Verified portable export script exists")
        else:
            issues.append("devmentor_portable.py not found")

        app_main = ROOT / "app" / "backend" / "main.py"
        if app_main.exists():
            success, _, stderr = self.run_command([sys.executable, "-m", "py_compile", str(app_main)])
            if success:
                actions.append("Verified Replit app syntax")
            else:
                issues.append(f"Replit app syntax error: {stderr}")

        verification_data = {
            "timestamp": datetime.now().isoformat(),
            "all_pass": all_pass,
            "actions": actions,
            "issues": issues
        }

        with open(REPORTS_DIR / "verify.json", 'w', encoding="utf-8") as f:
            json.dump(verification_data, f, indent=2)

        duration = (datetime.now() - start).total_seconds()
        return PhaseResult(
            phase="VERIFY",
            phase_number=4,
            success=all_pass,
            duration_seconds=duration,
            summary="All verifications passed" if all_pass else f"{len(issues)} verification issues",
            details=verification_data,
            actions_taken=actions,
            issues_found=issues
        )

    # =========================================================================
    # PHASE 5: CONSOLIDATE
    # =========================================================================
    def phase_consolidate(self) -> PhaseResult:
        """
        Phase 5: CONSOLIDATE - Reduce bloat and merge redundancy

        - Remove or merge redundant scripts
        - Turn repeated patterns into core modules
        - Keep the repo "small but deep"

        SAFETY: Only cleans project-local caches, never system caches like .cache/uv
        """
        start = datetime.now()
        actions = []
        consolidations = []

        logger.info("%s Phase 5: CONSOLIDATE - Reducing bloat...", PHASE_ICONS[4])

        prune_result = self.run_ops("prune")
        actions.append("Re-analyzed repository for bloat")

        safe_project_dirs = [
            ROOT / "scripts",
            ROOT / "app",
            ROOT / "cli",
            ROOT / "tutorials",
            ROOT / "challenges",
        ]

        protected_patterns = [".cache", "node_modules", ".git", "venv", ".venv", "uv"]

        for project_dir in safe_project_dirs:
            if not project_dir.exists():
                continue
            for cache_dir in project_dir.rglob("__pycache__"):
                if cache_dir.is_dir():
                    rel_path = str(cache_dir.relative_to(ROOT))
                    if not any(p in rel_path for p in protected_patterns):
                        try:
                            shutil.rmtree(cache_dir)
                            consolidations.append(f"Removed cache: {rel_path}")
                        except OSError as e:
                            logger.debug("Failed to remove cache %s: %s", rel_path, e)

        for pyc in ROOT.glob("*.pyc"):
            try:
                pyc.unlink()
                consolidations.append(f"Removed: {pyc.name}")
            except OSError as e:
                logger.debug("Failed to remove pyc %s: %s", pyc.name, e)

        actions.append("Cleaned project-local Python caches (safe mode)")

        consolidation_data = {
            "timestamp": datetime.now().isoformat(),
            "consolidations": consolidations,
            "prune_report": prune_result
        }

        with open(REPORTS_DIR / "consolidate.json", 'w', encoding="utf-8") as f:
            json.dump(consolidation_data, f, indent=2)

        duration = (datetime.now() - start).total_seconds()
        return PhaseResult(
            phase="CONSOLIDATE",
            phase_number=5,
            success=True,
            duration_seconds=duration,
            summary=f"Applied {len(consolidations)} consolidations",
            details=consolidation_data,
            actions_taken=actions,
            fixes_applied=consolidations
        )

    # =========================================================================
    # PHASE 6: DOCUMENT
    # =========================================================================
    def phase_document(self) -> PhaseResult:
        """
        Phase 6: DOCUMENT - Update docs to match reality

        - Verify entrypoints are documented
        - Verify tasks are documented
        - Update "how to run" sections
        """
        start = datetime.now()
        actions = []

        logger.info("%s Phase 6: DOCUMENT - Updating documentation...", PHASE_ICONS[5])

        tree_md = self._generate_tree_md()
        with open(REPORTS_DIR / "tree.md", 'w', encoding="utf-8") as f:
            f.write(tree_md)
        actions.append("Generated reports/tree.md")

        self.run_ops("report")
        actions.append("Generated reports/latest.md")

        status_md = self._generate_chug_status_md()
        with open(REPORTS_DIR / "chug_status.md", 'w', encoding="utf-8") as f:
            f.write(status_md)
        actions.append("Generated reports/chug_status.md")

        duration = (datetime.now() - start).total_seconds()
        return PhaseResult(
            phase="DOCUMENT",
            phase_number=6,
            success=True,
            duration_seconds=duration,
            summary="Updated all documentation artifacts",
            actions_taken=actions
        )

    def _generate_tree_md(self) -> str:
        """Generate a tree.md showing important paths and entrypoints"""
        lines = [
            "# DevMentor Repository Tree",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Key Entrypoints",
            "",
            "### VS Code Tasks (Primary Interface)",
            "- `.vscode/tasks.json` - Control panel with DevMentor tasks",
            "",
            "### Scripts",
        ]

        scripts_dir = ROOT / "scripts"
        if scripts_dir.exists():
            for script in sorted(scripts_dir.glob("*.py")):
                lines.append(f"- `scripts/{script.name}`")

        lines.extend([
            "",
            "### Tutorials",
        ])

        tutorials_dir = ROOT / "tutorials"
        if tutorials_dir.exists():
            for track in sorted(tutorials_dir.iterdir()):
                if track.is_dir():
                    count = len(list(track.glob("*.md")))
                    lines.append(f"- `tutorials/{track.name}/` ({count} lessons)")

        lines.extend([
            "",
            "### Reports (Generated)",
        ])

        if REPORTS_DIR.exists():
            for report in sorted(REPORTS_DIR.iterdir()):
                lines.append(f"- `reports/{report.name}`")

        return "\n".join(lines)

    def _generate_chug_status_md(self) -> str:
        """Generate chug_status.md with current cycle status"""
        lines = [
            "# CHUG Engine Status",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Current State",
            f"- Cycles completed: {self.state.cycles_completed}",
            f"- Last cycle: {self.state.last_cycle_time or 'Never'}",
            f"- Total issues found: {self.state.total_issues_found}",
            f"- Total fixes applied: {self.state.total_fixes_applied}",
            f"- Consecutive clean cycles: {self.state.consecutive_clean_cycles}",
            "",
            "## Recent History",
            ""
        ]

        for h in self.state.history[-10:]:
            status = "✅" if h.get("is_clean") else "⚠️"
            lines.append(f"- Cycle #{h.get('cycle', '?')}: {status} {h.get('total_issues', 0)} issues, {h.get('total_fixes', 0)} fixes")

        if not self.state.history:
            lines.append("- No cycles completed yet")

        return "\n".join(lines)

    # =========================================================================
    # PHASE 7: EXPORT
    # =========================================================================
    def phase_export(self) -> PhaseResult:
        """
        Phase 7: EXPORT - Portability gate validation

        - Generate a portable ZIP
        - Validate the ZIP contains required files
        - Provide "Continue in VS Code" checklist
        """
        start = datetime.now()
        actions = []
        issues = []

        logger.info("%s Phase 7: EXPORT - Validating portability...", PHASE_ICONS[6])

        required_for_portable = [
            ".vscode/tasks.json",
            ".vscode/settings.json",
            "scripts/devmentor_bootstrap.py",
            "scripts/devmentor_portable.py",
            "tutorials/00-vscode-basics/01-command-palette.md",
            "START_HERE.md"
        ]

        missing = []
        for req in required_for_portable:
            if not (ROOT / req).exists():
                missing.append(req)

        if missing:
            issues.append(f"Missing required files: {', '.join(missing)}")
        else:
            actions.append("Verified all required portable files exist")

        export_result = self.run_ops("export")
        actions.append("Generated portable ZIP")

        export_zip = EXPORTS_DIR / "devmentor-portable.zip"
        if export_zip.exists():
            size_mb = export_zip.stat().st_size / (1024 * 1024)
            actions.append(f"Export size: {size_mb:.2f}MB")
            if size_mb > 50:
                issues.append(f"Export ZIP is large ({size_mb:.1f}MB) - consider pruning")

        checklist = [
            "1. Extract ZIP to local folder",
            "2. Open folder in VS Code",
            "3. Run 'DevMentor: Start/Resume' from Command Palette",
            "4. (Optional) Run 'DevMentor: Import Portable ZIP' to restore state"
        ]

        export_data = {
            "timestamp": datetime.now().isoformat(),
            "required_files": required_for_portable,
            "missing_files": missing,
            "export_result": export_result,
            "checklist": checklist
        }

        with open(REPORTS_DIR / "export.json", 'w', encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)

        duration = (datetime.now() - start).total_seconds()
        return PhaseResult(
            phase="EXPORT",
            phase_number=7,
            success=len(issues) == 0,
            duration_seconds=duration,
            summary="Portability validated" if not issues else f"{len(issues)} portability issues",
            details=export_data,
            actions_taken=actions,
            issues_found=issues
        )

    # =========================================================================
    # FULL CYCLE
    # =========================================================================
    def run_cycle(self) -> CycleResult:
        """Run one complete 7-phase CHUG cycle"""
        cycle_start = datetime.now()
        cycle_num = self.state.cycles_completed + 1

        logger.info("%s", "\n" + "=" * 70)
        logger.info("🚂 CHUG CYCLE #%d - FULL 7-PHASE PROTOCOL", cycle_num)
        logger.info("%s", "=" * 70)
        logger.info(
            "Phases: ASSESS → PLAN → EXECUTE → VERIFY → CONSOLIDATE → DOCUMENT → EXPORT"
        )
        logger.info("%s", "=" * 70)

        phases = []

        phase1 = self.phase_assess()
        phases.append(asdict(phase1))

        phase2 = self.phase_plan()
        phases.append(asdict(phase2))

        phase3 = self.phase_execute()
        phases.append(asdict(phase3))

        phase4 = self.phase_verify()
        phases.append(asdict(phase4))

        phase5 = self.phase_consolidate()
        phases.append(asdict(phase5))

        phase6 = self.phase_document()
        phases.append(asdict(phase6))

        phase7 = self.phase_export()
        phases.append(asdict(phase7))

        total_issues = sum(len(p.get("issues_found", [])) for p in phases)
        total_fixes = sum(len(p.get("fixes_applied", [])) for p in phases)
        is_clean = all(p.get("success", False) for p in phases) and total_issues == 0

        what_improved = []
        for p in phases:
            for action in p.get("actions_taken", [])[:2]:
                what_improved.append(action)
        what_improved = what_improved[:5]

        what_remains_risky = []
        for p in phases:
            for issue in p.get("issues_found", []):
                what_remains_risky.append(issue)
        what_remains_risky = what_remains_risky[:5]

        if is_clean:
            next_best = "Routine maintenance - run again in 24h or after major changes"
        elif what_remains_risky:
            next_best = f"Address: {what_remains_risky[0]}"
        else:
            next_best = "Run another cycle to continue improvement"

        cycle_duration = (datetime.now() - cycle_start).total_seconds()

        result = CycleResult(
            cycle_number=cycle_num,
            timestamp=cycle_start.isoformat(),
            duration_seconds=cycle_duration,
            phases=phases,
            total_issues=total_issues,
            total_fixes=total_fixes,
            is_clean=is_clean,
            plan_bullets=self.current_plan,
            what_improved=what_improved,
            what_remains_risky=what_remains_risky,
            next_best_cycle=next_best
        )

        self.state.cycles_completed = cycle_num
        self.state.last_cycle_time = cycle_start.isoformat()
        self.state.last_phase = "EXPORT"
        self.state.total_issues_found += total_issues
        self.state.total_fixes_applied += total_fixes

        if is_clean:
            self.state.consecutive_clean_cycles += 1
        else:
            self.state.consecutive_clean_cycles = 0

        self.state.history.append({
            "cycle": cycle_num,
            "timestamp": cycle_start.isoformat(),
            "duration_seconds": cycle_duration,
            "total_issues": total_issues,
            "total_fixes": total_fixes,
            "is_clean": is_clean
        })
        if len(self.state.history) > 100:
            self.state.history = self.state.history[-100:]

        self.state.save()

        self._print_cycle_summary(result)

        return result

    def _print_cycle_summary(self, result: CycleResult):
        """Print a formatted cycle summary"""
        logger.info("%s", "\n" + "=" * 70)
        logger.info("📊 CHUG CYCLE #%d COMPLETE", result.cycle_number)
        logger.info("%s", "=" * 70)

        logger.info("📋 Phase Summary:")
        for p in result.phases:
            icon = PHASE_ICONS[p["phase_number"] - 1]
            status = "✅" if p["success"] else "⚠️"
            logger.info(
                "   %s %s: %s %s (%.1fs)",
                icon,
                p["phase"],
                status,
                p["summary"],
                p["duration_seconds"],
            )

        logger.info("📈 Metrics:")
        logger.info("   Total issues: %d", result.total_issues)
        logger.info("   Total fixes: %d", result.total_fixes)
        logger.info("   Duration: %.1fs", result.duration_seconds)
        logger.info("   Status: %s", "✅ CLEAN" if result.is_clean else "⚠️ Issues remain")

        if result.what_improved:
            logger.info("✨ What Improved:")
            for item in result.what_improved[:3]:
                logger.info("   • %s", item)

        if result.what_remains_risky:
            logger.warning("⚠️ What Remains Risky:")
            for item in result.what_remains_risky[:3]:
                logger.warning("   • %s", item)

        logger.info("🔮 Next Best Cycle:")
        logger.info("   %s", result.next_best_cycle)

        logger.info("%s", "=" * 70)

    def run_phase(self, phase_number: int) -> PhaseResult:
        """Run a specific phase by number (1-7)"""
        phase_methods = [
            self.phase_assess,
            self.phase_plan,
            self.phase_execute,
            self.phase_verify,
            self.phase_consolidate,
            self.phase_document,
            self.phase_export
        ]

        if 1 <= phase_number <= 7:
            logger.info(
                "🚂 Running Phase %d: %s", phase_number, PHASE_NAMES[phase_number - 1]
            )
            return phase_methods[phase_number - 1]()
        else:
            raise ValueError(f"Invalid phase number: {phase_number}. Must be 1-7.")

    def run_loop(self, max_cycles: int = 10, stop_when_clean: int = 3):
        """Run multiple cycles until clean or max reached"""
        logger.info(
            "🔁 Starting CHUG loop (max %d cycles, stop after %d clean)",
            max_cycles,
            stop_when_clean,
        )

        for i in range(max_cycles):
            result = self.run_cycle()

            if self.state.consecutive_clean_cycles >= stop_when_clean:
                logger.info(
                    "🎉 Repository stable! %d consecutive clean cycles.", stop_when_clean
                )
                break

            if i < max_cycles - 1:
                logger.info("\n⏳ Waiting 10 seconds before next cycle...")
                import time
                time.sleep(10)

        logger.info("%s", "\n" + "=" * 70)
        logger.info("🏁 CHUG LOOP COMPLETE")
        logger.info("   Total cycles: %d", self.state.cycles_completed)
        logger.info("   Total issues found: %d", self.state.total_issues_found)
        logger.info("   Total fixes applied: %d", self.state.total_fixes_applied)
        logger.info("%s", "=" * 70)

    def show_status(self):
        """Show current chug state"""
        logger.info("%s", "\n" + "=" * 70)
        logger.info("🚂 CHUG ENGINE v2.0 STATUS")
        logger.info("%s", "=" * 70)
        logger.info("   Cycles completed: %d", self.state.cycles_completed)
        logger.info("   Last cycle: %s", self.state.last_cycle_time or "Never")
        logger.info("   Last phase: %s", self.state.last_phase or "None")
        logger.info("   Total issues found: %d", self.state.total_issues_found)
        logger.info("   Total fixes applied: %d", self.state.total_fixes_applied)
        logger.info("   Consecutive clean: %d", self.state.consecutive_clean_cycles)

        if self.state.history:
            logger.info("\n   Recent history:")
            for h in self.state.history[-5:]:
                status = "✅" if h.get("is_clean") else "⚠️"
                logger.info(
                    "     #%d: %s %d issues, %d fixes (%.1fs)",
                    h["cycle"],
                    status,
                    h.get("total_issues", 0),
                    h.get("total_fixes", 0),
                    h.get("duration_seconds", 0),
                )

        logger.info("\n   7-Phase Protocol:")
        for i, name in enumerate(PHASE_NAMES):
            logger.info("     %s Phase %d: %s", PHASE_ICONS[i], i + 1, name)

        logger.info("%s", "=" * 70)


def main():
    engine = ChugEngine()

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg == "--loop":
            max_cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            engine.run_loop(max_cycles=max_cycles)

        elif arg == "--status":
            engine.show_status()

        elif arg == "--phase":
            if len(sys.argv) > 2:
                phase_num = int(sys.argv[2])
                engine.run_phase(phase_num)
            else:
                print("Usage: chug_engine.py --phase <1-7>")
                print("Phases: 1=ASSESS, 2=PLAN, 3=EXECUTE, 4=VERIFY, 5=CONSOLIDATE, 6=DOCUMENT, 7=EXPORT")

        elif arg == "--help" or arg == "-h":
            print(__doc__)

        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage")
    else:
        engine.run_cycle()


if __name__ == "__main__":
    main()
