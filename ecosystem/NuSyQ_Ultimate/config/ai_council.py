"""
AI Council - Persistent Multi-Agent Governance System for ΞNuSyQ

The AI Council is a persistent group chat where all LLMs can contribute on:
- Serious issues, warnings, problems
- Ideas, new concepts, modules
- Helpful tips, quantum winks, guidance
- Progress tracking: what we did, doing, and what's next
- Systematic, procedural evolution adherence

Council Structure:
- **Executive Council** (3 members): Strategic decisions, critical issues
  - claude_code (Orchestrator): Master coordinator
  - chatdev_ceo: Software development strategy
  - ollama_qwen_14b: Technical architecture

- **Technical Council** (5 members): Implementation guidance
  - ollama_gemma_9b: Security & best practices
  - chatdev_cto: System design
  - chatdev_programmer: Code quality
  - ollama_codellama_13b: Code generation
  - chatdev_reviewer: Quality assurance

- **Advisory Panel** (3 members): Context & insights
  - ollama_llama_8b: General reasoning
  - chatdev_tester: Reliability verification
  - ollama_phi_3: Quick triage

Council Session Types:
1. **STANDUP**: Daily progress tracking (what we did/doing/next)
2. **ADVISORY**: Ideas, concepts, helpful guidance
3. **EMERGENCY**: Critical warnings, serious problems
4. **REFLECTION**: Meta-review of project evolution
5. **QUANTUM_WINK**: Subtle insights, pattern recognition

Author: AI Code Agent
Date: 2025-10-07
Status: Week 3 Extension - AI Council Infrastructure
"""

import json
import sys
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.multi_agent_session import MultiAgentSession, ConversationMode


class CouncilSessionType(Enum):
    """Types of AI Council sessions"""

    STANDUP = "standup"  # Progress tracking
    ADVISORY = "advisory"  # Ideas, guidance
    EMERGENCY = "emergency"  # Critical issues
    REFLECTION = "reflection"  # Meta-review
    QUANTUM_WINK = "quantum_wink"  # Subtle insights


class CouncilTier(Enum):
    """Council membership tiers"""

    EXECUTIVE = "executive"  # 3 members: Strategic decisions
    TECHNICAL = "technical"  # 5 members: Implementation
    ADVISORY = "advisory"  # 3 members: Context & insights


@dataclass
class CouncilAgenda:
    """Agenda item for council session"""

    topic: str
    context: str
    priority: str  # "critical", "high", "medium", "low"
    proposed_by: str
    timestamp: datetime


@dataclass
class CouncilMinutes:
    """Minutes from council session"""

    session_id: str
    session_type: CouncilSessionType
    timestamp: datetime
    agenda: List[CouncilAgenda]
    participants: List[str]
    discussion: str
    decisions: List[Dict[str, Any]]
    action_items: List[Dict[str, Any]]
    progress_tracking: Dict[str, Any]
    next_steps: List[Any]
    warnings: List[str]
    insights: List[str]


class AICouncil:
    """
    Persistent AI Council for multi-agent governance.

    The Council maintains continuity across sessions, tracking:
    - What we just did (recent completions)
    - What we're doing now (active work)
    - What we're supposed to do next (roadmap adherence)
    - Warnings, ideas, insights from all agents

    Usage:
        # Daily standup
        council = AICouncil()
        council.convene_standup(
            completed=["Week 3 multi-agent system"],
            in_progress=["AI Council infrastructure"],
            next_up=["Week 4 integration testing"]
        )

        # Emergency session
        council.convene_emergency(
            issue="457 errors detected in workspace",
            severity="medium",
            agents_consulted=["ollama_qwen_14b", "ollama_gemma_9b"]
        )

        # Quantum wink (subtle insight)
        council.record_quantum_wink(
            insight="Code visibility issue may be ANSI color encoding",
            agent="ollama_gemma_9b"
        )
    """

    # Council membership (11 agents total)
    EXECUTIVE_COUNCIL = [
        "claude_code",  # Master orchestrator
        "chatdev_ceo",  # Software strategy
        "ollama_qwen_14b",  # Technical architecture
    ]

    TECHNICAL_COUNCIL = [
        "ollama_gemma_9b",  # Security & practices
        "chatdev_cto",  # System design
        "chatdev_programmer",  # Code quality
        "ollama_codellama_13b",  # Code generation
        "chatdev_reviewer",  # QA
    ]

    ADVISORY_PANEL = [
        "ollama_llama_8b",  # General reasoning
        "chatdev_tester",  # Reliability
        "ollama_phi_3",  # Quick triage
    ]

    def __init__(self, council_dir: Optional[Path] = None, use_stub: bool = False):
        """Initialize AI Council"""
        self.council_dir = council_dir or Path("Logs/ai_council")
        self.council_dir.mkdir(parents=True, exist_ok=True)
        self.use_stub = use_stub or bool(int(os.environ.get("COUNCIL_STUB", "0")))

        # Load persistent state
        self.state_file = self.council_dir / "council_state.json"
        self.state = self._load_state()

        # Session counter
        self.session_counter = self.state.get("session_counter", 0)

    def _load_state(self) -> Dict[str, Any]:
        """Load persistent council state"""
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {
                "session_counter": 0,
                "last_session": None,
                "active_warnings": [],
                "pending_decisions": [],
                "progress_history": [],
                "quantum_winks": [],
            }

    def _save_state(self):
        """Save persistent council state"""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, default=str)

    def _generate_session_id(self, session_type: CouncilSessionType) -> str:
        """Generate unique session ID"""
        self.session_counter += 1
        self.state["session_counter"] = self.session_counter
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"council_{session_type.value}_{timestamp}_{self.session_counter:04d}"

    def convene_standup(
        self,
        completed: List[str],
        in_progress: List[str],
        next_up: List[str],
        blockers: Optional[List[str]] = None,
    ) -> CouncilMinutes:
        """
        Convene daily standup session.

        Track progress systematically:
        - What we just did
        - What we're doing now
        - What we're supposed to do next
        - Any blockers

        Args:
            completed: Recently completed tasks
            in_progress: Currently active work
            next_up: Upcoming tasks from roadmap
            blockers: Any blocking issues

        Returns:
            CouncilMinutes with standup summary
        """
        session_id = self._generate_session_id(CouncilSessionType.STANDUP)

        # Build agenda
        agenda = [
            CouncilAgenda(
                topic="Progress Review",
                context="Daily standup tracking",
                priority="high",
                proposed_by="system",
                timestamp=datetime.now(),
            )
        ]

        # Format standup prompt
        standup_prompt = f"""
**Daily Standup - {datetime.now().strftime("%Y-%m-%d")}**

**Completed Since Last Session**:
{self._format_list(completed)}

**Currently In Progress**:
{self._format_list(in_progress)}

**Next Steps (from roadmap)**:
{self._format_list(next_up)}

**Blockers**:
{self._format_list(blockers or ["None"])}

**Council Review**:
- Executive Council: Assess strategic alignment
- Technical Council: Verify implementation quality
- Advisory Panel: Provide context and insights

**Discussion Topics**:
1. Are we adhering to systematic, procedural evolution?
2. Any warnings or concerns about current direction?
3. Helpful tips or quantum winks for next steps?
"""

        # Convene Executive Council (strategic review)
        if self.use_stub:
            result_text = (
                "Stub standup (offline/minimal) | Completed: "
                + "; ".join(completed or ["n/a"])
                + " | In progress: "
                + "; ".join(in_progress or ["n/a"])
                + " | Next: "
                + "; ".join(next_up or ["n/a"])
            )
        else:
            session = MultiAgentSession(
                agents=self.EXECUTIVE_COUNCIL,
                task_prompt=standup_prompt,
                mode=ConversationMode.TURN_TAKING,
            )
            result = session.execute(max_turns=3)
            result_text = result.conclusion

        # Extract decisions and action items
        decisions = self._extract_decisions(result_text)
        action_items = self._extract_action_items(result_text)

        # Create minutes
        minutes = CouncilMinutes(
            session_id=session_id,
            session_type=CouncilSessionType.STANDUP,
            timestamp=datetime.now(),
            agenda=agenda,
            participants=self.EXECUTIVE_COUNCIL,
            discussion=result_text,
            decisions=decisions,
            action_items=action_items,
            progress_tracking={
                "completed": completed,
                "in_progress": in_progress,
                "next_up": next_up,
                "blockers": blockers or [],
            },
            next_steps=next_up,
            warnings=[],
            insights=[],
        )

        # Save minutes
        self._save_minutes(minutes)

        # Update state
        self.state["progress_history"].append(
            {
                "date": datetime.now().isoformat(),
                "completed": completed,
                "in_progress": in_progress,
                "next_up": next_up,
            }
        )
        self.state["last_session"] = session_id
        self._save_state()

        return minutes

    def convene_emergency(
        self, issue: str, severity: str, agents_consulted: Optional[List[str]] = None
    ) -> CouncilMinutes:
        """
        Convene emergency session for critical issues.

        Args:
            issue: Description of the problem
            severity: "critical", "high", "medium"
            agents_consulted: Which agents to include (defaults to full Technical Council)

        Returns:
            CouncilMinutes with emergency response
        """
        session_id = self._generate_session_id(CouncilSessionType.EMERGENCY)

        agents = agents_consulted or self.TECHNICAL_COUNCIL

        emergency_prompt = f"""
**EMERGENCY SESSION**

**Issue**: {issue}
**Severity**: {severity}
**Timestamp**: {datetime.now().isoformat()}

**Required Actions**:
1. Assess the severity and impact
2. Identify root cause
3. Propose immediate mitigations
4. Recommend long-term fixes
5. Flag any related warnings

**Council Response**:
"""

        # Use parallel consensus for emergencies (get all perspectives)
        if self.use_stub:
            result_text = (
                f"Stub emergency session (offline/minimal). Issue: {issue}. Severity: {severity}."
            )
        else:
            session = MultiAgentSession(
                agents=agents,
                task_prompt=emergency_prompt,
                mode=ConversationMode.PARALLEL_CONSENSUS,
            )

            result = session.execute()
            result_text = result.conclusion

        # Extract warnings
        warnings = [issue]  # Original issue is a warning

        minutes = CouncilMinutes(
            session_id=session_id,
            session_type=CouncilSessionType.EMERGENCY,
            timestamp=datetime.now(),
            agenda=[
                CouncilAgenda(
                    topic=f"Emergency: {issue}",
                    context=f"Severity: {severity}",
                    priority="critical",
                    proposed_by="system",
                    timestamp=datetime.now(),
                )
            ],
            participants=agents,
            discussion=result_text,
            decisions=self._extract_decisions(result_text),
            action_items=self._extract_action_items(result_text),
            progress_tracking={},
            next_steps=self._extract_action_items(result_text),
            warnings=warnings,
            insights=[],
        )

        self._save_minutes(minutes)

        # Add to active warnings
        self.state["active_warnings"].append(
            {
                "issue": issue,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
            }
        )
        self._save_state()

        return minutes

    def convene_advisory(
        self, topic: str, context: str, seeking: str = "ideas and guidance"
    ) -> CouncilMinutes:
        """
        Convene advisory session for ideas, concepts, helpful tips.

        Args:
            topic: Topic for discussion
            context: Context and background
            seeking: What kind of input is needed

        Returns:
            CouncilMinutes with advisory insights
        """
        session_id = self._generate_session_id(CouncilSessionType.ADVISORY)

        advisory_prompt = f"""
**Advisory Session**

**Topic**: {topic}
**Context**: {context}
**Seeking**: {seeking}

**Contributions Welcome**:
- New ideas and concepts
- Module suggestions
- Best practices and helpful tips
- Pattern recognition
- Quantum winks (subtle insights)

**Council Input**:
"""

        # Use reflection mode for advisory (meta-level thinking)
        if self.use_stub:
            result_text = f"Stub advisory session (offline/minimal). Topic: {topic}. Context: {context}."
        else:
            session = MultiAgentSession(
                agents=self.ADVISORY_PANEL
                + self.EXECUTIVE_COUNCIL[:1],  # Advisory + claude_code
                task_prompt=advisory_prompt,
                mode=ConversationMode.REFLECTION,
            )

            result = session.execute()
            result_text = result.conclusion

        insights = self._extract_insights(result_text)

        minutes = CouncilMinutes(
            session_id=session_id,
            session_type=CouncilSessionType.ADVISORY,
            timestamp=datetime.now(),
            agenda=[
                CouncilAgenda(
                    topic=topic,
                    context=context,
                    priority="medium",
                    proposed_by="system",
                    timestamp=datetime.now(),
                )
            ],
            participants=self.ADVISORY_PANEL + ["claude_code"],
            discussion=result_text,
            decisions=self._extract_decisions(result_text),
            action_items=self._extract_action_items(result_text),
            progress_tracking={},
            next_steps=[],
            warnings=[],
            insights=insights,
        )

        self._save_minutes(minutes)

        return minutes

    def record_quantum_wink(
        self, insight: str, agent: str, context: Optional[str] = None
    ) -> None:
        """
        Record a quantum wink - subtle insight or pattern recognition.

        Quantum winks are lightweight observations that don't require
        a full council session but should be tracked.

        Args:
            insight: The subtle insight or observation
            agent: Which agent noticed the pattern
            context: Optional context for the insight
        """
        wink = {
            "insight": insight,
            "agent": agent,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }

        self.state["quantum_winks"].append(wink)
        self._save_state()

        # Also save to dedicated quantum winks log
        winks_file = self.council_dir / "quantum_winks.jsonl"
        with open(winks_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(wink, default=str) + "\n")

    def get_progress_summary(self, last_n_sessions: int = 5) -> Dict[str, Any]:
        """Get summary of recent progress"""
        history = self.state.get("progress_history", [])[-last_n_sessions:]

        return {
            "recent_sessions": len(history),
            "completed_total": sum(len(s.get("completed", [])) for s in history),
            "active_work": history[-1].get("in_progress", []) if history else [],
            "next_steps": history[-1].get("next_up", []) if history else [],
            "active_warnings": len(self.state.get("active_warnings", [])),
            "quantum_winks_count": len(self.state.get("quantum_winks", [])),
        }

    def _format_list(self, items: List[str]) -> str:
        """Format list for display"""
        if not items:
            return "- None"
        return "\n".join(f"- {item}" for item in items)

    def _extract_decisions(self, text: str) -> List[Dict[str, Any]]:
        """Extract decisions from discussion (simple implementation)"""
        # Production would use NLP to detect decision points
        decisions = []
        if "decision" in text.lower() or "approve" in text.lower():
            decisions.append(
                {
                    "decision": "Extracted from discussion",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        return decisions

    def _extract_action_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract action items from discussion (simple implementation)"""
        # Production would parse TODO/ACTION markers
        actions = []
        if "next" in text.lower() or "should" in text.lower():
            actions.append(
                {
                    "action": "See discussion for details",
                    "assigned_to": "TBD",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        return actions

    def _extract_insights(self, text: str) -> List[str]:
        """Extract insights from discussion"""
        # Simple implementation - production would use NLP
        insights = []
        if "insight" in text.lower() or "pattern" in text.lower():
            insights.append("Insight detected in discussion - see full minutes")
        return insights

    def _save_minutes(self, minutes: CouncilMinutes):
        """Save council minutes to file"""
        minutes_file = self.council_dir / f"{minutes.session_id}.json"

        with open(minutes_file, "w", encoding="utf-8") as f:
            json.dump(asdict(minutes), f, indent=2, default=str)

        print(f"✓ Council minutes saved: {minutes_file}")


# ========== Convenience Functions ==========


def daily_standup(
    completed: List[str],
    in_progress: List[str],
    next_up: List[str],
    blockers: Optional[List[str]] = None,
) -> CouncilMinutes:
    """Quick daily standup"""
    council = AICouncil()
    return council.convene_standup(completed, in_progress, next_up, blockers)


def emergency_session(issue: str, severity: str = "high") -> CouncilMinutes:
    """Quick emergency session"""
    council = AICouncil()
    return council.convene_emergency(issue, severity)


def quantum_wink(insight: str, agent: str = "claude_code") -> None:
    """Record a quantum wink"""
    council = AICouncil()
    council.record_quantum_wink(insight, agent)


def get_progress() -> Dict[str, Any]:
    """Get current progress summary"""
    council = AICouncil()
    return council.get_progress_summary()


# ========== CLI for Testing ==========

if __name__ == "__main__":
    import sys

    # Lightweight stub mode: skip agent calls, return minimal minutes
    use_stub = "--stub" in sys.argv or bool(int(os.environ.get("COUNCIL_STUB", "0")))
    if "--stub" in sys.argv:
        sys.argv.remove("--stub")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ai_council.py standup [--stub]")
        print("  python ai_council.py emergency 'Issue description' [--stub]")
        print("  python ai_council.py wink 'Subtle insight'")
        print("  python ai_council.py progress")
        sys.exit(1)

    command = sys.argv[1]

    if command == "standup":
        council = AICouncil(use_stub=use_stub)
        minutes = council.convene_standup(
            completed=["Multi-agent session manager", "Unicode fix"],
            in_progress=["AI Council infrastructure"],
            next_up=["Week 4 integration testing", "Fix 7 failing tests"],
        )
        print(f"\n✓ Standup complete: {minutes.session_id}")
        print(f"  Participants: {', '.join(minutes.participants)}")
        print(f"  Decisions: {len(minutes.decisions)}")
        print(f"  Action items: {len(minutes.action_items)}")

    elif command == "emergency" and len(sys.argv) > 2:
        issue = sys.argv[2]
        council = AICouncil(use_stub=use_stub)
        minutes = council.convene_emergency(issue, severity="high")
        print(f"\n✓ Emergency session complete: {minutes.session_id}")
        print(f"  Issue: {issue}")
        print(f"  Participants: {', '.join(minutes.participants)}")

    elif command == "wink" and len(sys.argv) > 2:
        insight = sys.argv[2]
        quantum_wink(insight, agent="claude_code")
        print(f"\n✓ Quantum wink recorded: {insight}")

    elif command == "progress":
        summary = get_progress()
        print("\n📊 Progress Summary:")
        print(f"  Recent sessions: {summary['recent_sessions']}")
        print(f"  Tasks completed: {summary['completed_total']}")
        print(f"  Active work: {len(summary['active_work'])}")
        print(f"  Next steps: {len(summary['next_steps'])}")
        print(f"  Active warnings: {summary['active_warnings']}")
        print(f"  Quantum winks: {summary['quantum_winks_count']}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
