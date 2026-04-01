#!/usr/bin/env python3
"""🎯 KILO-FOOLISH System Health Assessment & Enhancement Roadmap.

Comprehensive analysis of repository health with actionable enhancement recommendations.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SystemHealthAssessment:
    """Generate comprehensive system health assessment and enhancement roadmap."""

    def __init__(self) -> None:
        """Initialize SystemHealthAssessment."""
        self.repo_root = Path.cwd()
        self.timestamp = datetime.now().isoformat()

    def collect(self) -> dict[str, Any] | None:
        """Collect health metrics and roadmap from latest quick system analysis."""
        analysis_files = list(self.repo_root.glob("quick_system_analysis_*.json"))
        if not analysis_files:
            return None

        latest_analysis = max(analysis_files, key=lambda f: f.stat().st_mtime)
        with latest_analysis.open() as f:
            data = json.load(f)

        health_metrics = self._calculate_health_metrics(data)
        roadmap = self._generate_enhancement_roadmap(data, health_metrics)
        return {
            "analysis_path": str(latest_analysis),
            "health_metrics": health_metrics,
            "roadmap": roadmap,
            "raw": data,
        }

    def render_report(self, health_metrics: dict[str, Any], roadmap: dict[str, Any]) -> str:
        """Render a human-readable report string."""
        lines: list[str] = []
        lines.append("=== SYSTEM HEALTH REPORT ===\n")
        lines.append(f"Timestamp: {self.timestamp}\n")
        lines.append(f"Overall Health Score: {health_metrics['overall_health_score']:.2f}\n")
        lines.append(f"Health Grade: {health_metrics['health_grade']}\n")
        lines.append(f"Working Files: {health_metrics['working_files']}\n")
        lines.append(f"Broken Files: {health_metrics['broken_files']}\n")
        lines.append(f"Launch Pad Files: {health_metrics['launch_pad_files']}\n")
        lines.append(f"Enhancement Candidates: {health_metrics['enhancement_candidates']}\n")
        lines.append("\n-- Roadmap (immediate priorities) --\n")
        for item in roadmap.get("immediate_priorities", []):
            lines.append(f"* {item['description']}\n")
        advanced = roadmap.get("advanced_ai_readiness", {})
        if advanced:
            lines.append("\n-- Advanced AI Readiness --\n")
            for capability, details in advanced.items():
                lines.append(f"* {capability}: {details['status']} ({details['summary']})\n")
        return "".join(lines)

    def _print_health_report(self, health_metrics: dict[str, Any], roadmap: dict[str, Any]) -> None:
        """Print a compact health report to stdout."""
        logger.info(self.render_report(health_metrics, roadmap))

    def _save_comprehensive_report(
        self,
        health_metrics: dict[str, Any],
        roadmap: dict[str, Any],
        raw_data: dict[str, Any],
    ) -> None:
        """Persist comprehensive report JSON to local artifact file."""
        report = {
            "timestamp": self.timestamp,
            "health_metrics": health_metrics,
            "enhancement_roadmap": roadmap,
            "raw_analysis_data": raw_data,
        }

        report_file = f"system_health_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

    def analyze_system_health(self) -> None:
        """Run comprehensive system health analysis with console + file output."""
        collected = self.collect()
        if not collected:
            return

        self._print_health_report(collected["health_metrics"], collected["roadmap"])
        self._save_comprehensive_report(
            collected["health_metrics"], collected["roadmap"], collected["raw"]
        )

        try:
            from src.system.agent_awareness import emit as _emit

            _metrics = collected["health_metrics"]
            _score = _metrics.get("overall_health_score", 0)
            _grade = _metrics.get("health_grade", "?")
            _level = "WARNING" if _score < 0.7 else "INFO"
            _emit(
                "system",
                f"System health: score={_score:.2f} grade={_grade}",
                level=_level,
                source="system_health_assessor",
            )
        except Exception:
            pass

    def _calculate_health_metrics(self, data: dict) -> dict[str, Any]:
        """Calculate overall system health metrics."""
        total_files = (
            len(data["working_files"])
            + len(data["broken_files"])
            + len(data["launch_pad_files"])
            + len(data["enhancement_candidates"])
        )

        health_score = (
            (
                (len(data["working_files"]) * 1.0)
                + (len(data["enhancement_candidates"]) * 0.7)
                + (len(data["launch_pad_files"]) * 0.3)
                + (len(data["broken_files"]) * 0.0)
            )
            / max(total_files, 1)
            * 100
        )

        # Integration analysis
        integration_scores: dict[str, Any] = {}
        for category in ["working_files", "enhancement_candidates", "launch_pad_files"]:
            high = sum(1 for f in data[category] if f.get("integration_level") == "high")
            medium = sum(1 for f in data[category] if f.get("integration_level") == "medium")
            low = sum(1 for f in data[category] if f.get("integration_level") == "low")
            total = len(data[category])

            if total > 0:
                integration_scores[category] = {
                    "high": high,
                    "medium": medium,
                    "low": low,
                    "integration_score": (high * 1.0 + medium * 0.7 + low * 0.3) / total * 100,
                }

        # Directory health analysis
        directory_health = self._analyze_directory_health(data)

        return {
            "overall_health_score": health_score,
            "total_files": total_files,
            "working_files": len(data["working_files"]),
            "broken_files": len(data["broken_files"]),
            "launch_pad_files": len(data["launch_pad_files"]),
            "enhancement_candidates": len(data["enhancement_candidates"]),
            "integration_scores": integration_scores,
            "directory_health": directory_health,
            "health_grade": self._get_health_grade(health_score),
        }

    def _analyze_directory_health(self, data: dict) -> dict[str, Any]:
        """Analyze health by directory."""
        directory_stats: dict[str, Any] = {}
        for category in [
            "working_files",
            "broken_files",
            "launch_pad_files",
            "enhancement_candidates",
        ]:
            for file_info in data[category]:
                path_parts = Path(file_info["path"]).parts
                if len(path_parts) > 1:
                    dir_name = path_parts[1]  # src/[directory_name]

                    if dir_name not in directory_stats:
                        directory_stats[dir_name] = {
                            "working": 0,
                            "broken": 0,
                            "launch_pad": 0,
                            "enhancement": 0,
                            "total": 0,
                        }

                    if category == "working_files":
                        directory_stats[dir_name]["working"] += 1
                    elif category == "broken_files":
                        directory_stats[dir_name]["broken"] += 1
                    elif category == "launch_pad_files":
                        directory_stats[dir_name]["launch_pad"] += 1
                    elif category == "enhancement_candidates":
                        directory_stats[dir_name]["enhancement"] += 1

                    directory_stats[dir_name]["total"] += 1

        # Calculate health scores for each directory
        for _dir_name, stats in directory_stats.items():
            if stats["total"] > 0:
                health_score = (
                    (
                        (stats["working"] * 1.0)
                        + (stats["enhancement"] * 0.7)
                        + (stats["launch_pad"] * 0.3)
                        + (stats["broken"] * 0.0)
                    )
                    / stats["total"]
                    * 100
                )

                stats["health_score"] = health_score
                stats["health_grade"] = self._get_health_grade(health_score)

        return directory_stats

    def _get_health_grade(self, score: float) -> str:
        """Convert health score to letter grade."""
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def _generate_enhancement_roadmap(self, data: dict, health_metrics: dict) -> dict[str, Any]:
        """Generate comprehensive enhancement roadmap."""
        advanced_ai_readiness = self._audit_advanced_ai_capabilities()
        roadmap: dict[str, Any] = {
            "immediate_priorities": [],
            "short_term_goals": [],
            "medium_term_goals": [],
            "long_term_vision": [],
            "integration_improvements": [],
            "consolidation_opportunities": [],
            "advanced_ai_readiness": advanced_ai_readiness,
        }

        # Immediate priorities (Critical fixes)
        if data["broken_files"]:
            roadmap["immediate_priorities"].append(
                {
                    "category": "Critical Fixes",
                    "description": f"Fix {len(data['broken_files'])} broken files preventing system operation",
                    "files": [f["path"] for f in data["broken_files"][:5]],
                    "impact": "High",
                    "effort": "Medium",
                }
            )

        # Short-term goals (Launch pad completion)
        if data["launch_pad_files"]:
            roadmap["short_term_goals"].append(
                {
                    "category": "Launch Pad Completion",
                    "description": f"Complete implementation of {len(data['launch_pad_files'])} launch pad files",
                    "files": [f["path"] for f in data["launch_pad_files"]],
                    "impact": "High",
                    "effort": "High",
                }
            )

        missing_advanced = [
            name
            for name, details in advanced_ai_readiness.items()
            if details["status"] == "missing"
        ]
        partial_advanced = [
            name
            for name, details in advanced_ai_readiness.items()
            if details["status"] == "partial"
        ]
        if missing_advanced:
            roadmap["short_term_goals"].append(
                {
                    "category": "Advanced AI Foundation Gaps",
                    "description": "Stand up missing advanced-AI capability anchors before adding new orchestration layers",
                    "capabilities": missing_advanced,
                    "impact": "High",
                    "effort": "Medium",
                }
            )
        if partial_advanced:
            roadmap["medium_term_goals"].append(
                {
                    "category": "Advanced AI Hardening",
                    "description": "Convert partial advanced-AI capabilities into production-ready system surfaces",
                    "capabilities": partial_advanced,
                    "impact": "High",
                    "effort": "Medium",
                }
            )

        # Medium-term goals (Enhancement candidates)
        low_integration_files = [
            f for f in data["enhancement_candidates"] if f.get("integration_level") == "low"
        ]
        if low_integration_files:
            roadmap["medium_term_goals"].append(
                {
                    "category": "Integration Enhancement",
                    "description": f"Enhance integration level for {len(low_integration_files)} files",
                    "files": [f["path"] for f in low_integration_files[:10]],
                    "impact": "Medium",
                    "effort": "Medium",
                }
            )

        # Long-term vision
        roadmap["long_term_vision"].append(
            {
                "category": "System Optimization",
                "description": "Achieve 95%+ system health with full KILO-FOOLISH integration",
                "targets": [
                    "All files with high integration level",
                    "Comprehensive documentation coverage",
                    "Automated testing for all components",
                    "Unified quantum-consciousness architecture",
                ],
            }
        )

        # Integration improvements
        for dir_name, stats in health_metrics["directory_health"].items():
            if stats["health_score"] < 80:
                roadmap["integration_improvements"].append(
                    {
                        "directory": dir_name,
                        "current_health": f"{stats['health_score']:.1f}% (Grade {stats['health_grade']})",
                        "issues": {
                            "broken": stats["broken"],
                            "launch_pad": stats["launch_pad"],
                            "needs_enhancement": stats["enhancement"],
                        },
                        "recommendation": "Priority attention needed",
                    }
                )

        return roadmap

    def _audit_advanced_ai_capabilities(self) -> dict[str, dict[str, Any]]:
        """Audit practical readiness for advanced AI capability anchors."""
        capability_specs = {
            "agentic_rl": {
                "anchors": [
                    self.repo_root / "src" / "orchestration" / "advanced_consensus_voter.py",
                    self.repo_root / "src" / "observability" / "autonomy_dashboard.py",
                ],
                "partial": True,
                "summary": "Adaptive voting and autonomy metrics exist; no true RL policy loop yet.",
            },
            "meta_learning": {
                "anchors": [self.repo_root / "src" / "ai" / "ai_intermediary.py"],
                "partial": True,
                "summary": "Intermediary now tracks event-pattern learning, but not few-shot adaptation across models.",
            },
            "few_shot_adaptation": {
                "anchors": [
                    self.repo_root / "src" / "ai" / "ai_intermediary.py",
                    self.repo_root / "src" / "search" / "smart_search.py",
                ],
                "partial": True,
                "summary": "Context-aware routing exists, but explicit few-shot adaptation logic is still partial.",
            },
            "continual_learning": {
                "anchors": [
                    self.repo_root / "src" / "ai" / "ai_intermediary.py",
                    self.repo_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl",
                ],
                "partial": True,
                "summary": "Quest/memory/event capture exists, but continual policy updates remain partial.",
            },
            "multi_modal_context": {
                "anchors": [
                    self.repo_root / "src" / "ai" / "ai_intermediary.py",
                    self.repo_root / "src" / "search" / "smart_search.py",
                ],
                "partial": True,
                "summary": "Text/code/context routing exists; image/log/telemetry fusion is still partial.",
            },
            "knowledge_graph_embeddings": {
                "anchors": [
                    self.repo_root / "src" / "tools" / "embeddings_exporter.py",
                    self.repo_root / "docs" / "graphs" / "README.md",
                ],
                "partial": True,
                "summary": "Embedding export and dependency graphs exist; a unified queryable knowledge graph is still partial.",
            },
            "ensemble_consensus": {
                "anchors": [
                    self.repo_root / "src" / "orchestration" / "advanced_consensus_voter.py",
                    self.repo_root
                    / "src"
                    / "orchestration"
                    / "bridges"
                    / "consensus_voting_bridge.py",
                ],
                "partial": False,
                "summary": "Weighted multi-agent consensus is implemented and test-backed.",
            },
            "observability_anomaly": {
                "anchors": [
                    self.repo_root / "src" / "observability" / "tracing.py",
                    self.repo_root / "src" / "diagnostics" / "health_monitor_daemon.py",
                ],
                "partial": True,
                "summary": "Tracing and health monitoring exist; dedicated anomaly models remain partial.",
            },
            "causal_inference": {
                "anchors": [
                    self.repo_root / "src" / "ai" / "ai_intermediary.py",
                    self.repo_root
                    / "src"
                    / "consciousness"
                    / "temple_of_knowledge"
                    / "floor_3_systems.py",
                ],
                "partial": True,
                "summary": "Causality-chain extraction and causal-loop analysis exist; a dedicated inference engine remains partial.",
            },
            "federated_learning": {
                "anchors": [
                    self.repo_root / "src" / "orchestration" / "specialization_learner.py",
                    self.repo_root / "src" / "tools" / "agent_task_router.py",
                ],
                "partial": True,
                "summary": "Cross-agent specialization learning exists; full federated training and parameter exchange remain partial.",
            },
            "graph_learning": {
                "anchors": [
                    self.repo_root / "src" / "tools" / "dependency_analyzer.py",
                    self.repo_root / "state" / "reports" / "graph_learning_latest.json",
                ],
                "partial": True,
                "summary": "Dependency graph ranking and impact analysis now exist; learned graph policies and GNN execution remain partial.",
            },
        }

        readiness: dict[str, dict[str, Any]] = {}
        for capability, spec in capability_specs.items():
            anchors = [str(path.relative_to(self.repo_root)) for path in spec["anchors"]]
            existing = [
                anchor
                for anchor, path in zip(anchors, spec["anchors"], strict=False)
                if path.exists()
            ]
            if len(existing) == len(anchors):
                status = "partial" if spec["partial"] else "ready"
            elif existing:
                status = "partial"
            else:
                status = "missing"

            readiness[capability] = {
                "status": status,
                "anchors": anchors,
                "detected": existing,
                "summary": spec["summary"],
            }

        return readiness


# Backwards-compatible alias: some modules import SystemHealthAssessor
# while this module historically provided SystemHealthAssessment. Provide
# a simple alias to avoid import errors during gradual refactors.
class SystemHealthAssessor(SystemHealthAssessment):
    """Compatibility alias for older import paths."""

    pass

    def _print_health_report(self, health_metrics: dict, roadmap: dict) -> None:
        """Print comprehensive health report."""
        # Overall Health

        # Directory Health
        for _dir_name, _stats in sorted(
            health_metrics["directory_health"].items(),
            key=lambda x: x[1]["health_score"],
            reverse=True,
        ):
            pass

        # Enhancement Roadmap

        if roadmap["immediate_priorities"]:
            for _priority in roadmap["immediate_priorities"]:
                pass

        if roadmap["short_term_goals"]:
            for _goal in roadmap["short_term_goals"]:
                pass

        if roadmap["medium_term_goals"]:
            for _goal in roadmap["medium_term_goals"]:
                pass

        # Top directories needing attention
        needs_attention = [
            d for d, s in health_metrics["directory_health"].items() if s["health_score"] < 80
        ]
        if needs_attention:
            for dir_name in needs_attention:
                health_metrics["directory_health"][dir_name]

    def _save_comprehensive_report(
        self, health_metrics: dict, roadmap: dict, raw_data: dict
    ) -> None:
        """Save comprehensive report to file."""
        report = {
            "timestamp": self.timestamp,
            "health_metrics": health_metrics,
            "enhancement_roadmap": roadmap,
            "raw_analysis_data": raw_data,
        }

        report_file = f"system_health_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)


if __name__ == "__main__":
    assessor = SystemHealthAssessment()
    assessor.analyze_system_health()
