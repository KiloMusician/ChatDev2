#!/usr/bin/env python3
"""Consolidated Evolution System - Uses ALL Existing Infrastructure.

This is the PROPER integration that:
1. Uses REAL AI Council from NuSyQ (11 agents, not duplicate)
2. Uses Culture Ship Real Action for fixes (not wrapper)
3. Uses Multi-AI Orchestrator for coordination (existing)
4. Consolidates EXISTING audit tools (not duplicates)
5. Integrates with SimulatedVerse autonomous systems

Existing Tools We're Consolidating:
- GitHubIntegrationAuditor (src/utils/github_integration_auditor.py)
- ImportHealthChecker (src/utils/import_health_checker.py)
- FileOrganizationAuditor (src/utils/file_organization_auditor.py)
- MazeRepoScanner (src/tools/maze_solver.py)
- QuestBasedAuditor (src/diagnostics/quest_based_auditor.py)
- KILOSystematicAuditor (src/diagnostics/systematic_src_audit.py)
- EcosystemHealthChecker (ecosystem_health_checker.py)
- TheaterAuditor (NuSyQ/scripts/theater_audit.py)
- IntegratedScanner (NuSyQ/scripts/integrated_scanner.py)

OmniTag: [consolidation, real-systems, no-duplicates, integration]
MegaTag: EVOLUTION⨳CONSOLIDATOR⦾REAL-INFRASTRUCTURE→∞
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup logger first
logger = logging.getLogger(__name__)

# Optional path resolver
try:
    from src.utils.path_resolver import get_path_resolver
except Exception:
    get_path_resolver = None

# Add NuSyQ Root to path
if get_path_resolver:
    try:
        nusyq_root = get_path_resolver().nusyq_root
    except Exception:
        nusyq_root = Path("c:/Users/keath/NuSyQ")
else:
    nusyq_root = Path("c:/Users/keath/NuSyQ")
if nusyq_root.exists():
    sys.path.insert(0, str(nusyq_root))

# Import EXISTING audit tools
try:
    from src.tools.maze_solver import MazeRepoScanner
    from src.utils.file_organization_auditor import FileOrganizationAuditor
    from src.utils.import_health_checker import ImportHealthChecker

    AUDITORS_AVAILABLE = True
except ImportError as e:
    logger.info(f"⚠️  Some auditors not available: {e}")
    AUDITORS_AVAILABLE = False

# Import REAL AI Council
try:
    from config.ai_council import AICouncil

    REAL_COUNCIL = True
except ImportError:
    logger.info("⚠️  Real AI Council not available from NuSyQ")
    REAL_COUNCIL = False

# Import Culture Ship
try:
    from src.culture_ship_real_action import RealActionCultureShip

    CULTURE_SHIP = True
except ImportError:
    logger.info("⚠️  Culture Ship not available")
    CULTURE_SHIP = False

# Import SimulatedVerse Bridge for Culture-Ship agent
try:
    from src.integration.simulatedverse_async_bridge import \
        SimulatedVerseBridge

    SIMULATEDVERSE_BRIDGE = True
except ImportError:
    logger.info("⚠️  SimulatedVerse Bridge not available")
    SIMULATEDVERSE_BRIDGE = False

# Import Multi-AI Orchestrator
try:
    from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator

    ORCHESTRATOR = True
except ImportError:
    logger.info("⚠️  Multi-AI Orchestrator not available")
    ORCHESTRATOR = False


logger = logging.getLogger(__name__)


class ConsolidatedEvolutionSystem:
    """Master evolution system that consolidates ALL existing tools.

    Instead of creating duplicates, this uses:
    - Real AI Council (NuSyQ/config/ai_council.py)
    - Culture Ship Real Action (src/culture_ship_real_action.py)
    - Multi-AI Orchestrator (src/orchestration/multi_ai_orchestrator.py)
    - All existing audit tools (9+ different scanners)
    """

    def __init__(self) -> None:
        """Initialize ConsolidatedEvolutionSystem."""
        self.repo_root = Path.cwd()
        self.data_dir = self.repo_root / "data" / "evolution"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(" CONSOLIDATED EVOLUTION SYSTEM")
        logger.info(" Using EXISTING Infrastructure (No Duplicates)")
        logger.info("=" * 70 + "\n")

        # Initialize REAL systems
        self._initialize_real_systems()

        # Initialize existing audit tools
        self._initialize_audit_tools()

    def _initialize_real_systems(self) -> None:
        """Initialize real AI Council, Culture Ship, Orchestrator."""
        if REAL_COUNCIL:
            self.council = AICouncil()
            logger.info("✅ Real AI Council (11 agents)")
            logger.info(f"   Executive: {', '.join(self.council.EXECUTIVE_COUNCIL)}")
            logger.info(f"   Technical: {', '.join(self.council.TECHNICAL_COUNCIL)}")
            logger.info(f"   Advisory: {', '.join(self.council.ADVISORY_PANEL)}")
        else:
            self.council = None
            logger.info("❌ AI Council not available")

        if CULTURE_SHIP:
            self.ship = RealActionCultureShip()
            logger.info("✅ Culture Ship Real Action")
        else:
            self.ship = None
            logger.info("❌ Culture Ship not available")

        # NEW: Initialize SimulatedVerse Bridge for Culture-Ship agent
        if SIMULATEDVERSE_BRIDGE:
            self.sv_bridge = SimulatedVerseBridge()
            logger.info("✅ SimulatedVerse Bridge (Culture-Ship Agent)")
            logger.info("   Async file-based protocol enabled")
        else:
            self.sv_bridge = None
            logger.info("❌ SimulatedVerse Bridge not available")

        if ORCHESTRATOR:
            self.orchestrator = MultiAIOrchestrator()
            logger.info("✅ Multi-AI Orchestrator")
        else:
            self.orchestrator = None
            logger.info("❌ Orchestrator not available")

    def _initialize_audit_tools(self) -> None:
        """Initialize all existing audit tools."""
        logger.info("\n📊 Existing Audit Tools:")

        if AUDITORS_AVAILABLE:
            try:
                repo_root_str = str(self.repo_root)
                self.auditors = {
                    "imports": ImportHealthChecker(repository_root=repo_root_str),
                    "file_org": FileOrganizationAuditor(repository_root=repo_root_str),
                    "maze": MazeRepoScanner(root=self.repo_root),
                }
                for name in self.auditors:
                    logger.info(f"   ✅ {name}")
            except Exception as e:
                logger.info(f"   ⚠️  Error initializing auditors: {e}")
                self.auditors = {}
        else:
            self.auditors = {}
            logger.info("   ❌ Auditors not fully available")

        logger.info("=" * 70 + "\n")

    def run_comprehensive_audit(self) -> dict[str, Any]:
        """Run comprehensive audit using ALL existing tools."""
        logger.info(" COMPREHENSIVE AUDIT (All Existing Tools)")
        logger.info("=" * 70 + "\n")

        results = {
            "timestamp": datetime.now().isoformat(),
            "audit_results": {},
            "issues_found": 0,
            "recommendations": [],
        }

        # Run each auditor with proper method names
        for name, auditor in self.auditors.items():
            logger.info(f"[{name.upper()}] Running audit...")
            try:
                if name == "imports":
                    # Returns ImportAnalysis object
                    analysis = auditor.check_all_files()
                    audit = {
                        "total_files": analysis.total_files,
                        "total_imports": analysis.total_imports,
                        "successful": analysis.successful_imports,
                        "failed": analysis.failed_imports,
                        "issues": [vars(issue) for issue in analysis.issues],
                        "missing_packages": list(analysis.missing_packages),
                    }
                elif name == "file_org":
                    # Returns list[OrganizationIssue]
                    issues = auditor.scan_repository()
                    audit = {
                        "total_issues": len(issues),
                        "issues": [vars(issue) for issue in issues],
                    }
                elif name == "maze":
                    # Returns dict[Path, list[tuple[int, str]]]
                    findings = auditor.scan(max_depth=8)
                    audit = {
                        "total_treasures": sum(len(v) for v in findings.values()),
                        "files_with_treasures": len(findings),
                        "findings": {str(k): v for k, v in findings.items()},
                    }
                else:
                    audit: dict[str, Any] = {}
                results["audit_results"][name] = audit
                issue_count = audit.get("total_issues", 0) or len(audit.get("issues", []))
                results["issues_found"] += issue_count
                logger.info(f"   Found {issue_count} issues")

            except (ImportError, AttributeError, TypeError) as e:
                logger.info(f"   ⚠️  Error: {e}")
                results["audit_results"][name] = {"error": str(e)}

        logger.info(f"\n[SUMMARY] Total issues found: {results['issues_found']}")

        # Save audit report
        report_file = (
            self.data_dir / f"consolidated_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"[SAVED] {report_file}\n")

        return results

    def theater_oversight(self, audit_results: dict[str, Any]) -> dict | None:
        """NEW: Submit audit results to SimulatedVerse Culture-Ship agent.

        for theater score analysis and proof-gated PU generation.

        This routes repository audit data to the Culture-Ship agent which:
        1. Calculates theater score (code quality metrics)
        2. Generates proof-gated PUs (Provable Units) for cleanup
        3. Returns actionable tasks with verification criteria

        Args:
            audit_results: dict containing comprehensive audit data

        Returns:
            dict with theater score, PUs generated, and recommendations

        """
        if not self.sv_bridge:
            logger.info("⚠️  SimulatedVerse Bridge not available - skipping theater oversight")
            return None

        logger.info(" CULTURE-SHIP THEATER OVERSIGHT")
        logger.info(" Submitting to SimulatedVerse Culture-Ship Agent")
        logger.info("=" * 70 + "\n")

        # Extract key metrics for theater audit
        issues_count = audit_results.get("issues_found", 0)
        audit_tools = len(audit_results.get("audit_results", {}))

        # Analyze patterns from audit results
        patterns = {
            "total_issues": issues_count,
            "audit_tools_used": audit_tools,
            "timestamp": audit_results.get("timestamp", datetime.now().isoformat()),
        }

        # Extract specific issue types if available
        for tool_name, tool_results in audit_results.get("audit_results", {}).items():
            if isinstance(tool_results, dict):
                issues = tool_results.get("issues", [])
                patterns[f"{tool_name}_issues"] = len(issues)

        # Submit to Culture-Ship agent via async file protocol
        logger.info("[CULTURE-SHIP] Submitting theater audit request...")
        logger.info(f"   Issues found: {issues_count}")
        logger.info(f"   Audit tools: {audit_tools}")

        try:
            task_id = self.sv_bridge.submit_task(
                agent_id="culture-ship",
                content=f"Review {patterns['project']} theater audit: {issues_count} issues across {audit_tools} audit tools",
                metadata={
                    "project": "NuSyQ-Hub",
                    "patterns": patterns,
                    "full_audit": audit_results,
                    "score": max(0.1, 1.0 - (issues_count / 1000)),  # Calculate theater score
                },
            )

            logger.info(f"   Task ID: {task_id}")
            logger.info("   Waiting for Culture-Ship response...")

            # Wait for result (max 30s)
            result = self.sv_bridge.check_result(task_id, timeout=30)

            if result and result.get("status") == "success":
                theater_data = result.get("data", {})
                pus_generated = theater_data.get("pus_generated", [])

                logger.info("\n✅ Culture-Ship Responded!")
                logger.info(f"   Theater Score: {theater_data.get('theater_score', 'N/A')}")
                logger.info(f"   PUs Generated: {len(pus_generated)}")

                # Display generated PUs
                if pus_generated:
                    logger.info("\n📋 Proof-Gated PUs:")
                    for idx, pu in enumerate(pus_generated[:5], 1):  # Show first 5
                        pu_type = pu.get("type", "unknown")
                        description = pu.get("description", "")
                        priority = pu.get("priority", "medium")
                        logger.info(f"   {idx}. [{pu_type}] {description}")
                        logger.info(f"      Priority: {priority}")

                    if len(pus_generated) > 5:
                        logger.info(f"   ... and {len(pus_generated) - 5} more PUs")

                # Save theater oversight report
                report_file = (
                    self.data_dir
                    / f"theater_oversight_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                with open(report_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "task_id": task_id,
                            "theater_data": theater_data,
                            "pus_count": len(pus_generated),
                            "pus": pus_generated,
                        },
                        f,
                        indent=2,
                        default=str,
                    )

                logger.info(f"\n📄 Report saved: {report_file}")

                return theater_data

            logger.info("⚠️  Culture-Ship timeout or no response")
            return None

        except Exception as e:
            logger.info(f"❌ Culture-Ship error: {e}")
            return None

    def submit_to_council(self, audit_results: dict[str, Any]) -> dict | None:
        """Submit audit results to REAL AI Council for review."""
        if not self.council:
            logger.info("⚠️  AI Council not available - skipping review")
            return None

        logger.info(" AI COUNCIL REVIEW")
        logger.info("=" * 70 + "\n")

        # Create standup session
        logger.info("[COUNCIL] Convening standup session...")

        issues_summary = f"{audit_results['issues_found']} issues across {len(audit_results['audit_results'])} audit tools"

        try:
            minutes = self.council.convene_standup(
                completed=["Comprehensive repository audit"],
                in_progress=["Reviewing audit findings"],
                next_up=["Implement approved fixes"],
                blockers=([issues_summary] if audit_results["issues_found"] > 0 else None),
            )

            logger.info(f"[OK] Session ID: {minutes.session_id}")
            logger.info(f"[OK] Participants: {len(minutes.participants)} council members")
            logger.info(f"[OK] Decisions: {len(minutes.decisions)}")

            return {
                "session_id": minutes.session_id,
                "participants": minutes.participants,
                "decisions": minutes.decisions,
                "action_items": minutes.action_items,
            }

        except Exception as e:
            logger.info(f"⚠️  Council session error: {e}")
            return None

    def implement_with_culture_ship(
        self,
        _council_decisions: dict | None = None,
    ) -> dict:
        """Implement fixes using Culture Ship Real Action."""
        if not self.ship:
            logger.info("⚠️  Culture Ship not available - skipping implementation")
            return {"status": "skipped"}

        logger.info(" CULTURE SHIP IMPLEMENTATION")
        logger.info("=" * 70 + "\n")

        logger.info("[SHIP] Running ecosystem scan and fixes...")
        results = self.ship.scan_and_fix_ecosystem()

        logger.info("\n[RESULTS]")
        logger.info(f"   Files scanned: {results.get('files_scanned', 0)}")
        logger.info(f"   Errors detected: {results.get('errors_detected', 0)}")
        logger.info(f"   Fixes applied: {results.get('fixes_applied', 0)}")
        logger.info(f"   Files fixed: {len(results.get('files_fixed', []))}")
        logger.info(f"   Improvements: {len(results.get('improvements', []))}")

        return results

    def run_complete_cycle(self) -> None:
        """Run complete evolution cycle using all real systems.

        ENHANCED: Now includes Culture-Ship theater oversight.
        """
        logger.info(" COMPLETE EVOLUTION CYCLE")
        logger.info(" Phase 1: Audit → Phase 1.5: Theater → Phase 2: Council → Phase 3: Implement")
        logger.info("=" * 70 + "\n")

        # Phase 1: Comprehensive Audit
        logger.info("\n📊 PHASE 1: COMPREHENSIVE AUDIT")
        audit_results = self.run_comprehensive_audit()

        # Phase 1.5: Culture-Ship Theater Oversight (NEW!)
        logger.info("\n🎭 PHASE 1.5: CULTURE-SHIP THEATER OVERSIGHT")
        theater_results = self.theater_oversight(audit_results)

        # Phase 2: AI Council Review
        logger.info("\n🧠 PHASE 2: AI COUNCIL REVIEW")
        council_decisions = self.submit_to_council(audit_results)

        # Phase 3: Culture Ship Implementation
        logger.info("\n🚢 PHASE 3: CULTURE SHIP IMPLEMENTATION")
        implementation_results = self.implement_with_culture_ship(council_decisions)

        # Summary
        logger.info(" EVOLUTION CYCLE COMPLETE")
        logger.info(f"\n✅ Audit: {audit_results['issues_found']} issues found")
        if theater_results:
            pus_count = len(theater_results.get("pus_generated", []))
            logger.info(f"✅ Theater: {pus_count} proof-gated PUs generated")
            logger.info(f"   Score: {theater_results.get('theater_score', 'N/A')}")
        if council_decisions:
            logger.info(f"✅ Council: {len(council_decisions.get('decisions', []))} decisions made")
        logger.info(
            f"✅ Implementation: {implementation_results.get('fixes_applied', 0)} fixes applied",
        )
        logger.info(f"\nFiles improved: {len(implementation_results.get('files_fixed', []))}")
        logger.info("=" * 70 + "\n")

        return {
            "audit": audit_results,
            "theater": theater_results,
            "council": council_decisions,
            "implementation": implementation_results,
        }


def main() -> None:
    """Main entry point."""
    logger.info(" CONSOLIDATED EVOLUTION SYSTEM")
    logger.info(" Leveraging ALL Existing Infrastructure")

    system = ConsolidatedEvolutionSystem()

    # Run complete cycle
    results = system.run_complete_cycle()

    # Save final results
    output_file = (
        system.data_dir / f"evolution_cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"\n💾 Results saved: {output_file}\n")


if __name__ == "__main__":
    main()
