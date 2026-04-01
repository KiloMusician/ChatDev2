#!/usr/bin/env python3
"""🌐 Ecosystem Integrator - Unified Intelligence Across All Systems.

===================================================================================

Integrates existing infrastructure to provide actionable intelligence:
- knowledge-base.yaml (NuSyQ Root) - Past solution database
- ZETA_PROGRESS_TRACKER.json - Current phase/task tracking
- quest_log.jsonl - Active quest management
- consciousness_memory.db - Semantic error memory
- MultiAIOrchestrator - Specialist model routing
- Multi-repo error analysis - Cross-repository awareness

OmniTag: {
    "purpose": "Unified ecosystem intelligence and context coordination",
    "dependencies": ["knowledge_base", "zeta_tracker", "quest_system", "consciousness_bridge", "multi_ai_orchestrator"],
    "context": "Meta-orchestration layer connecting all existing systems",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "EcosystemIntegrator",
    "integration_points": ["knowledge_base", "zeta_tracker", "quest_system", "consciousness_memory", "orchestrator", "error_explorer"],
    "related_tags": ["MetaOrchestration", "ContextCoordination", "IntelligentAutomation"]
}

RSHTS: ΞΨΩ∞⟨ECOSYSTEM⟩→ΦΣΣ⟨INTEGRATION⟩→∞⟨INTELLIGENCE⟩
===================================================================================
"""

import json
import logging
import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# Constants for model names
QWEN_CODER_14B = "qwen2.5-coder:14b"
STARCODER_15B = "starcoder2:15b"
GEMMA_9B = "gemma2:9b"
GEMMA_27B = "gemma2:27b"
CODELLAMA_7B = "codellama:7b"
LLAMA_8B = "llama3.1:8b"
DEEPSEEK_16B = "deepseek-coder-v2:16b"


class EcosystemIntegrator:
    """🌐 Unified Ecosystem Intelligence.

    Connects all existing systems for maximum effectiveness:
    - Past solutions from knowledge-base.yaml
    - Current tasks from ZETA_PROGRESS_TRACKER.json
    - Active quests from quest_log.jsonl
    - Error memory from consciousness_memory.db
    - Specialist model routing via MultiAIOrchestrator
    """

    def __init__(self, nusyq_hub_root: str = ".") -> None:
        """Initialize EcosystemIntegrator with nusyq_hub_root."""
        self.hub_root = Path(nusyq_hub_root)
        self.nusyq_root = self._find_nusyq_root()

        # System paths
        self.knowledge_base_path = self.nusyq_root / "knowledge-base.yaml"
        self.zeta_tracker_path = self.hub_root / "config" / "ZETA_PROGRESS_TRACKER.json"
        self.quest_log_path = self.hub_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        self.consciousness_db_path = self.hub_root / "copilot_memory" / "consciousness_memory.db"

        # Loaded data
        self.knowledge_base: dict[str, Any] | None = None
        self.zeta_tracker: dict[str, Any] | None = None
        self.quests: list[dict[str, Any]] = []

        # Model specializations (from knowledge-base.yaml)
        self.model_specializations = {
            QWEN_CODER_14B: [
                "code_generation",
                "refactoring",
                "programmer",
                "import_fixes",
            ],
            STARCODER_15B: [
                "syntax_errors",
                "code_review",
                "parsing",
                "ast_analysis",
            ],
            GEMMA_9B: ["documentation", "explanations", "creative_thinking"],
            GEMMA_27B: ["architecture", "design_patterns", "system_analysis"],
            CODELLAMA_7B: ["testing", "test_generation", "validation"],
            LLAMA_8B: ["communication", "user_interaction", "counseling"],
            DEEPSEEK_16B: ["debugging", "error_analysis", "complex_fixes"],
        }

        # Error intelligence (past solutions)
        self.solution_cache: dict[str, list[dict[str, Any]]] = defaultdict(list)

        # Load all systems
        self._load_all_systems()

    def _find_nusyq_root(self) -> Path:
        """Find NuSyQ root directory (where knowledge-base.yaml lives)."""
        import os

        # Try common locations
        env_root = os.environ.get("NUSYQ_ROOT_PATH")
        candidates = [
            Path(env_root) if env_root else None,
            Path.home() / "NuSyQ",
            self.hub_root.parent.parent / "NuSyQ",
        ]

        for candidate in candidates:
            if not candidate:
                continue
            if (candidate / "knowledge-base.yaml").exists():
                return candidate

        # Fallback: use hub root
        return self.hub_root

    def _load_all_systems(self) -> None:
        """Load all existing knowledge systems."""
        # Load knowledge base
        if self.knowledge_base_path.exists():
            try:
                with open(self.knowledge_base_path, encoding="utf-8") as f:
                    self.knowledge_base = yaml.safe_load(f)
                if self.knowledge_base:
                    self._index_solutions()
            except (OSError, yaml.YAMLError):
                logger.debug("Suppressed OSError/yaml", exc_info=True)

        # Load ZETA tracker
        if self.zeta_tracker_path.exists():
            try:
                with open(self.zeta_tracker_path, encoding="utf-8") as f:
                    self.zeta_tracker = json.load(f)
                if self.zeta_tracker:
                    pass
            except (OSError, json.JSONDecodeError):
                logger.debug("Suppressed OSError/json", exc_info=True)

        # Load quest log
        if self.quest_log_path.exists():
            try:
                with open(self.quest_log_path, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            self.quests.append(json.loads(line))
            except (OSError, json.JSONDecodeError):
                logger.debug("Suppressed OSError/json", exc_info=True)

    def _index_solutions(self) -> None:
        """Index past solutions from knowledge base."""
        if not self.knowledge_base:
            return

        for session in self.knowledge_base.get("sessions", []):
            # Look for error codes in implementation summaries
            impl_summary = str(session.get("implementation_summary", ""))

            # Extract error patterns (E402, F401, etc.)
            error_codes = re.findall(r"[EFB]\d{3,4}", impl_summary)

            for code in error_codes:
                self.solution_cache[code].append(
                    {
                        "session_id": session.get("id"),
                        "date": session.get("date"),
                        "description": session.get("description", "")[:100],
                        "status": session.get("implementation_summary", {}).get(
                            "status",
                            "Unknown",
                        ),
                        "approach": session.get("implementation_summary", {}).get("approach", ""),
                    },
                )

    def get_solution_intelligence(self, error_code: str) -> dict[str, Any]:
        """Get past solution intelligence for an error code."""
        solutions = self.solution_cache.get(error_code, [])

        if not solutions:
            return {
                "found": False,
                "message": f"No past solutions found for {error_code}",
            }

        # Find most successful solution
        successful = [s for s in solutions if "✅" in s["status"]]

        return {
            "found": True,
            "error_code": error_code,
            "total_past_solutions": len(solutions),
            "successful_solutions": len(successful),
            "most_recent": solutions[-1],
            "recommended_approach": (
                successful[-1]["approach"] if successful else "Manual review needed"
            ),
            "sessions": [s["session_id"] for s in solutions],
        }

    def get_current_focus(self) -> dict[str, Any]:
        """Get current focus from ZETA tracker."""
        if not self.zeta_tracker:
            return {"status": "No ZETA tracker loaded"}

        in_progress_tasks: list[dict[str, Any]] = []
        next_pending_tasks: list[dict[str, Any]] = []

        for phase_name, phase_data in self.zeta_tracker.get("phases", {}).items():
            for task in phase_data.get("tasks", []):
                if task.get("status") == "◐":  # In-progress
                    in_progress_tasks.append(
                        {
                            "id": task.get("id"),
                            "description": task.get("description"),
                            "phase": phase_name,
                            "progress_note": task.get("progress_note", "No notes"),
                        },
                    )
                elif task.get("status") == "○" and len(next_pending_tasks) < 3:
                    next_pending_tasks.append(
                        {
                            "id": task.get("id"),
                            "description": task.get("description"),
                            "phase": phase_name,
                        },
                    )

        # Determine recommended focus
        recommended_focus: dict[str, Any] | None = None
        if in_progress_tasks:
            recommended_focus = in_progress_tasks[0]
        elif next_pending_tasks:
            recommended_focus = next_pending_tasks[0]

        return {
            "in_progress": in_progress_tasks,
            "next_pending": next_pending_tasks,
            "recommended_focus": recommended_focus,
        }

    def get_active_quests(self) -> list[dict[str, Any]]:
        """Get active quests from quest system."""
        active_quests: list[Any] = []

        for event in self.quests:
            if event.get("event") == "add_quest":
                quest_data = event.get("details", {})
                if quest_data.get("status") in ["pending", "in-progress"]:
                    active_quests.append(
                        {
                            "title": quest_data.get("title"),
                            "questline": quest_data.get("questline"),
                            "description": quest_data.get("description"),
                            "status": quest_data.get("status"),
                            "tags": quest_data.get("tags", []),
                        },
                    )

        return active_quests[:10]  # Top 10 active quests

    def suggest_quest_for_errors(self, error_summary: dict[str, Any]) -> dict[str, Any] | None:
        """Suggest creating a quest for recurring error patterns."""
        # Look for high-count errors
        high_priority_errors: list[Any] = []

        for repo, errors in error_summary.get("by_repo", {}).items():
            for error_code, count in errors.items():
                if count > 50:  # Threshold for quest creation
                    high_priority_errors.append(
                        {"error_code": error_code, "count": count, "repo": repo},
                    )

        if not high_priority_errors:
            return None

        # Sort by count
        high_priority_errors.sort(key=lambda x: x["count"], reverse=True)
        top_error = high_priority_errors[0]

        return {
            "suggested_quest": {
                "title": f"Eliminate {top_error['error_code']} errors in {top_error['repo']}",
                "description": f"Fix {top_error['count']} occurrences of {top_error['error_code']} errors",
                "questline": "System Health & Audit Automation",
                "priority": "HIGH" if top_error["count"] > 200 else "MEDIUM",
                "estimated_command": f"ruff check --select {top_error['error_code']} --fix {top_error['repo']}",
                "tags": [
                    "error-elimination",
                    "auto-fix",
                    top_error["error_code"].lower(),
                ],
            },
        }

    def route_task_to_specialist(self, task_description: str, error_code: str | None = None) -> str:
        """Route a task to the best specialist model."""
        task_lower = task_description.lower()

        # Syntax errors → starcoder2
        if "syntax" in task_lower or (error_code and "syntax" in error_code.lower()):
            return "starcoder2:15b"

        # Import issues → qwen2.5-coder
        if any(keyword in task_lower for keyword in ["import", "e402", "f401", "f404"]):
            return "qwen2.5-coder:14b"

        # Testing → codellama
        if any(keyword in task_lower for keyword in ["test", "pytest", "unittest"]):
            return "codellama:7b"

        # Documentation → gemma2:9b
        if any(keyword in task_lower for keyword in ["document", "explain", "readme"]):
            return "gemma2:9b"

        # Complex debugging → deepseek-coder-v2
        if any(keyword in task_lower for keyword in ["debug", "complex", "analyze"]):
            return "deepseek-coder-v2:16b"

        # Architecture/design → gemma2:27b
        if any(keyword in task_lower for keyword in ["architecture", "design", "pattern"]):
            return "gemma2:27b"

        # Default: qwen2.5-coder (best general-purpose)
        return "qwen2.5-coder:14b"

    def generate_continuation_plan(self, current_state: dict[str, Any]) -> dict[str, Any]:
        """Generate a continuation plan for next session."""
        plan: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "session_summary": {
                "completed_actions": current_state.get("completed", []),
                "in_progress": current_state.get("in_progress", []),
                "next_priority": [],
            },
            "recommendations": [],
            "context_files": [],
            "continuation_command": "",
        }

        # Get next priority from ZETA tracker
        current_focus = self.get_current_focus()
        if current_focus.get("recommended_focus"):
            plan["session_summary"]["next_priority"].append(current_focus["recommended_focus"])

        # Add active quests
        active_quests = self.get_active_quests()
        for quest in active_quests[:3]:
            plan["session_summary"]["next_priority"].append(
                {
                    "type": "quest",
                    "title": quest["title"],
                    "questline": quest["questline"],
                },
            )

        # Generate recommendations
        if current_state.get("error_count", 0) > 1000:
            plan["recommendations"].append(
                {
                    "priority": 1,
                    "action": "Focus on high-count error codes",
                    "command": "python health.py --errors --view by_severity",
                    "impact": "Reduce error count by targeting top offenders",
                },
            )

        # Add context files
        plan["context_files"] = [
            str(self.zeta_tracker_path),
            str(self.quest_log_path),
            str(self.knowledge_base_path),
        ]

        # Suggested continuation command
        plan["continuation_command"] = "python health.py --resume"

        return plan

    def query_consciousness_memory(self, error_code: str, limit: int = 5) -> list[dict[str, Any]]:
        """Query consciousness memory database for similar past errors."""
        if not self.consciousness_db_path.exists():
            return []

        try:
            with sqlite3.connect(self.consciousness_db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT timestamp, topic, meta_context, semantic_meaning
                    FROM omnitags
                    WHERE topic LIKE ? OR meta_context LIKE ? OR semantic_meaning LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (f"%{error_code}%", f"%{error_code}%", f"%{error_code}%", limit),
                )

                results: list[Any] = []
                for row in cursor.fetchall():
                    results.append(
                        {
                            "timestamp": row[0],
                            "topic": row[1],
                            "meta_context": row[2],
                            "semantic_meaning": row[3],
                        },
                    )

                return results
        except (sqlite3.Error, OSError):
            return []

    def get_comprehensive_intelligence(
        self,
        error_code: str,
        context: dict | None = None,
    ) -> dict[str, Any]:
        """Get comprehensive intelligence across all systems."""
        intelligence: dict[str, Any] = {
            "error_code": error_code,
            "timestamp": datetime.now().isoformat(),
            "sources": {},
        }

        # 1. Past solutions
        solutions = self.get_solution_intelligence(error_code)
        intelligence["sources"]["knowledge_base"] = solutions

        # 2. Consciousness memory
        memory = self.query_consciousness_memory(error_code)
        intelligence["sources"]["consciousness_memory"] = {
            "found": len(memory) > 0,
            "entries": memory,
        }

        # 3. Specialist model recommendation
        task_desc = f"Fix {error_code} errors" + (
            f" in {context.get('repo', 'repository')}" if context else ""
        )
        specialist = self.route_task_to_specialist(task_desc, error_code)
        intelligence["sources"]["specialist_model"] = specialist

        # 4. Active quests (check if already being addressed)
        active_quests = self.get_active_quests()
        related_quests = [
            q for q in active_quests if error_code in q["title"] or error_code in str(q["tags"])
        ]
        intelligence["sources"]["active_quests"] = {
            "found": len(related_quests) > 0,
            "quests": related_quests,
        }

        # 5. Synthesis
        intelligence["synthesis"] = self._synthesize_intelligence(intelligence)

        return intelligence

    def _synthesize_intelligence(self, intelligence: dict[str, Any]) -> dict[str, Any]:
        """Synthesize intelligence from all sources into actionable recommendations."""
        synthesis: dict[str, Any] = {
            "confidence": 0.0,
            "recommended_action": "",
            "reasoning": [],
        }

        kb = intelligence["sources"].get("knowledge_base", {})
        cm = intelligence["sources"].get("consciousness_memory", {})
        quests = intelligence["sources"].get("active_quests", {})

        # High confidence if we've solved this before successfully
        if kb.get("found") and kb.get("successful_solutions", 0) > 0:
            synthesis["confidence"] = 0.95
            synthesis["recommended_action"] = (
                f"Apply approach from {kb['most_recent']['session_id']}: {kb['recommended_approach']}"
            )
            synthesis["reasoning"].append(
                f"Successfully solved {kb['successful_solutions']} times before",
            )

        # Medium confidence if we have consciousness memory
        elif cm.get("found"):
            synthesis["confidence"] = 0.7
            synthesis["recommended_action"] = (
                "Review consciousness memory entries and apply similar patterns"
            )
            synthesis["reasoning"].append(
                f"Found {len(cm['entries'])} related consciousness entries",
            )

        # Lower confidence if it's already an active quest
        elif quests.get("found"):
            synthesis["confidence"] = 0.5
            synthesis["recommended_action"] = (
                f"Continue existing quest: {quests['quests'][0]['title']}"
            )
            synthesis["reasoning"].append("Already being addressed in quest system")

        # No intelligence found
        else:
            synthesis["confidence"] = 0.3
            synthesis["recommended_action"] = (
                "Manual investigation required - no past solutions found"
            )
            synthesis["reasoning"].append("First encounter with this error pattern")

        # Add specialist model
        specialist = intelligence["sources"].get("specialist_model")
        synthesis["reasoning"].append(f"Recommended specialist: {specialist}")

        return synthesis


def main() -> None:
    """Demo/test the ecosystem integrator."""
    integrator = EcosystemIntegrator()

    # Test 1: Get solution intelligence for E402
    integrator.get_solution_intelligence("E402")

    # Test 2: Get current focus
    integrator.get_current_focus()

    # Test 3: Get active quests
    quests = integrator.get_active_quests()
    for _quest in quests[:5]:
        pass

    # Test 4: Route task to specialist
    tasks = [
        "Fix syntax errors in Python files",
        "Fix E402 import placement errors",
        "Generate unit tests for new features",
        "Explain the architecture of the system",
    ]
    for task in tasks:
        integrator.route_task_to_specialist(task)

    # Test 5: Comprehensive intelligence
    integrator.get_comprehensive_intelligence("E402", {"repo": "NuSyQ-Hub"})


if __name__ == "__main__":
    main()
