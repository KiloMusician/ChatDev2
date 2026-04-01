#!/usr/bin/env python3
"""CodexBuilder - Automatic Rule Generation and Evolution

Generates new rule files from logs, detects patterns, clusters similar errors,
proposes new symbolic glyph assignments, and evolves existing rules.

Capabilities:
- Rule merging
- Rule splitting
- Deprecating outdated patterns
- Generating glyphs from semantic vectors
- Linking rules through conceptual similarity

OmniTag: [zen-engine, rule-generation, evolution, meta-learning]
MegaTag: ZEN_ENGINE⨳BUILDER⦾RULE_EVOLUTION→∞
"""

import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from zen_engine.agents.codex_loader import CodexLoader
from zen_engine.agents.error_observer import ErrorEvent, ErrorObserver

logger = logging.getLogger(__name__)


@dataclass
class RuleProposal:
    """Proposed new rule for the Codex."""

    proposed_id: str
    confidence: float  # 0.0 to 1.0
    trigger_patterns: list[str]
    error_patterns: list[str]
    contexts: dict[str, list[str]]
    lesson_short: str
    lesson_long: str
    suggested_fixes: list[dict[str, str]]
    tags: list[str]
    proposed_glyph: str | None = None
    supporting_events: list[str] = None  # Event IDs

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CodexBuilder:
    """Automatic Rule Generation and Evolution System.

    Analyzes error events, detects patterns, and proposes new rules.
    """

    def __init__(
        self,
        codex_loader: CodexLoader | None = None,
        observer: ErrorObserver | None = None,
    ):
        """Initialize the CodexBuilder."""
        self.codex = codex_loader or CodexLoader()
        self.observer = observer or ErrorObserver()

        # Pattern clustering
        self.error_clusters: dict[str, list[ErrorEvent]] = defaultdict(list)
        self.pattern_frequency: Counter = Counter()

    def analyze_events(self, events: list[ErrorEvent]) -> list[RuleProposal]:
        """Analyze multiple error events to propose new rules.

        Args:
            events: List of ErrorEvent objects

        Returns:
            List of RuleProposal objects
        """
        # Cluster events by symptom
        self._cluster_events(events)

        # Detect patterns
        proposals = []

        for symptom, cluster in self.error_clusters.items():
            if len(cluster) >= 3:  # Minimum 3 occurrences to propose rule
                proposal = self._generate_rule_from_cluster(symptom, cluster)
                if proposal:
                    proposals.append(proposal)

        return proposals

    def _cluster_events(self, events: list[ErrorEvent]):
        """Cluster events by symptom."""
        self.error_clusters.clear()

        for event in events:
            symptom = event.symptom
            self.error_clusters[symptom].append(event)

            # Track pattern frequency
            for pattern in event.patterns_detected:
                self.pattern_frequency[pattern] += 1

    def _generate_rule_from_cluster(
        self, symptom: str, events: list[ErrorEvent]
    ) -> RuleProposal | None:
        """Generate a rule proposal from a cluster of similar events."""
        if not events:
            return None

        # Extract common patterns
        error_patterns = self._extract_common_error_patterns(events)
        trigger_patterns = self._extract_common_trigger_patterns(events)
        contexts = self._extract_contexts(events)
        tags = self._generate_tags(symptom, contexts)

        # Generate lesson
        lesson_short, lesson_long = self._generate_lesson(symptom, events)

        # Generate suggested fixes
        suggested_fixes = self._generate_suggested_fixes(symptom, events)

        # Generate glyph
        proposed_glyph = self._propose_glyph(symptom, tags)

        # Calculate confidence based on cluster size and pattern consistency
        confidence = min(len(events) / 10.0, 1.0) * self._calculate_pattern_consistency(events)

        # Generate rule ID
        rule_id = symptom.replace(" ", "_").lower()

        return RuleProposal(
            proposed_id=rule_id,
            confidence=confidence,
            trigger_patterns=trigger_patterns,
            error_patterns=error_patterns,
            contexts=contexts,
            lesson_short=lesson_short,
            lesson_long=lesson_long,
            suggested_fixes=suggested_fixes,
            tags=tags,
            proposed_glyph=proposed_glyph,
            supporting_events=[e.id for e in events],
        )

    def _extract_common_error_patterns(self, events: list[ErrorEvent]) -> list[str]:
        """Extract common error message patterns."""
        patterns = []

        # Collect all error lines
        all_errors = []
        for event in events:
            all_errors.extend(event.error_lines)

        # Find common substrings
        pattern_counts = Counter()
        for error in all_errors:
            # Extract key phrases (simple heuristic)
            if "Error:" in error or "error:" in error:
                # Extract error type
                match = re.search(r"(\w+Error:)", error)
                if match:
                    pattern_counts[match.group(1)] += 1

        # Take top patterns
        patterns = [p for p, _ in pattern_counts.most_common(5)]

        return patterns

    def _extract_common_trigger_patterns(self, events: list[ErrorEvent]) -> list[str]:
        """Extract command patterns that trigger errors."""
        commands = []

        for event in events:
            cmd = event.context.get("command_before_error", "")
            if cmd:
                commands.append(cmd)

        if not commands:
            return []

        # Detect common command prefixes
        pattern_counts = Counter()

        for cmd in commands:
            # Extract first word (command verb)
            first_word = cmd.split()[0] if cmd.split() else ""
            if first_word:
                pattern_counts[f"^{first_word}"] += 1

        patterns = [p for p, _ in pattern_counts.most_common(3)]

        return patterns

    def _extract_contexts(self, events: list[ErrorEvent]) -> dict[str, list[str]]:
        """Extract common execution contexts."""
        shells = set()
        platforms = set()
        languages = set()

        for event in events:
            shells.add(event.shell)
            platforms.add(event.context.get("platform", "unknown"))
            if event.language_intent:
                languages.add(event.language_intent)

        contexts = {
            "shells": list(shells - {"unknown"}),
            "platforms": list(platforms - {"unknown"}),
        }

        if languages:
            contexts["languages"] = list(languages)

        return contexts

    def _generate_tags(self, symptom: str, contexts: dict[str, list[str]]) -> list[str]:
        """Generate tags for the rule."""
        tags = []

        # Add symptom-based tags
        symptom_words = symptom.replace("_", " ").split()
        tags.extend(symptom_words[:2])  # First 2 words

        # Add context tags
        tags.extend(contexts.get("shells", []))
        tags.extend(contexts.get("languages", []))

        # Add level tag (default to intermediate)
        tags.append("intermediate")

        return list(set(tags))  # Deduplicate

    def _generate_lesson(self, symptom: str, events: list[ErrorEvent]) -> tuple[str, str]:
        """Generate lesson short and long descriptions."""
        # Simple heuristic-based lesson generation
        symptom_clean = symptom.replace("_", " ").title()

        short = f"Avoid {symptom_clean.lower()} by following best practices."

        # Build longer lesson from context
        contexts = self._extract_contexts(events)
        shells = contexts.get("shells", [])
        languages = contexts.get("languages", [])

        long = f"{symptom_clean} occurs when "

        if shells:
            long += f"using {', '.join(shells)} "
        if languages:
            long += f"with {', '.join(languages)} code "

        long += "without proper configuration or setup. Review error messages carefully and consult documentation."

        return short, long

    def _generate_suggested_fixes(
        self, symptom: str, events: list[ErrorEvent]
    ) -> list[dict[str, str]]:
        """Generate suggested fix strategies."""
        # Simple template-based suggestions
        suggestions = []

        if "import" in symptom.lower() or "module" in symptom.lower():
            suggestions.append(
                {
                    "strategy": "install_dependency",
                    "description": "Install missing dependency with package manager",
                    "when_to_use": "When module import fails",
                }
            )

        if "timeout" in symptom.lower():
            suggestions.append(
                {
                    "strategy": "add_timeout",
                    "description": "Add timeout parameter to prevent hanging",
                    "when_to_use": "For long-running operations",
                }
            )

        if "encoding" in symptom.lower():
            suggestions.append(
                {
                    "strategy": "specify_encoding",
                    "description": "Explicitly set encoding='utf-8'",
                    "when_to_use": "For file operations",
                }
            )

        # Generic suggestion if no specific ones
        if not suggestions:
            suggestions.append(
                {
                    "strategy": "review_documentation",
                    "description": "Consult official documentation for this error",
                    "when_to_use": "When specific fix is unclear",
                }
            )

        return suggestions

    def _propose_glyph(self, symptom: str, tags: list[str]) -> str | None:
        """Propose a glyph for this rule."""
        # Simple glyph generation based on domain
        # In production, this would use semantic analysis

        glyph_map = {
            "import": "∏∑",
            "module": "∏∑",
            "timeout": "⧖∞",
            "encoding": "⟨UTF⟩",
            "git": "⊕∇",
            "async": "⟳⧖",
            "circular": "⊛∞",
            "environment": "⟐∅",
        }

        for keyword, glyph_base in glyph_map.items():
            if keyword in symptom.lower() or keyword in " ".join(tags).lower():
                return glyph_base + "⊗"

        return None

    def _calculate_pattern_consistency(self, events: list[ErrorEvent]) -> float:
        """Calculate how consistent the error patterns are in the cluster."""
        if not events:
            return 0.0

        # Check consistency of patterns_detected
        all_patterns = [pattern for event in events for pattern in event.patterns_detected]

        if not all_patterns:
            return 0.5  # Neutral

        pattern_counts = Counter(all_patterns)
        most_common_count = pattern_counts.most_common(1)[0][1]

        # Consistency = how many events share the most common pattern
        return most_common_count / len(events)

    def merge_rules(self, rule_id_1: str, rule_id_2: str) -> dict[str, Any] | None:
        """Merge two similar rules into one.

        Args:
            rule_id_1: First rule ID
            rule_id_2: Second rule ID

        Returns:
            Merged rule dictionary, or None if merge not possible
        """
        rule1 = self.codex.get_rule(rule_id_1)
        rule2 = self.codex.get_rule(rule_id_2)

        if not rule1 or not rule2:
            logger.error("One or both rules not found")
            return None

        # Create merged rule
        merged = {
            "id": f"{rule_id_1}_merged",
            "version": 1,
            "triggers": {
                "errors": list(
                    set(rule1.triggers.get("errors", []) + rule2.triggers.get("errors", []))
                ),
                "command_patterns": list(
                    set(
                        rule1.triggers.get("command_patterns", [])
                        + rule2.triggers.get("command_patterns", [])
                    )
                ),
            },
            "contexts": {
                "shells": list(
                    set(rule1.contexts.get("shells", []) + rule2.contexts.get("shells", []))
                ),
                "platforms": list(
                    set(rule1.contexts.get("platforms", []) + rule2.contexts.get("platforms", []))
                ),
            },
            "lesson": rule1.lesson,  # Keep first rule's lesson
            "suggestions": rule1.suggestions + rule2.suggestions,
            "actions": rule1.actions,
            "tags": list(set(rule1.tags + rule2.tags)),
            "lore": rule1.lore,
            "meta": {
                "merged_from": [rule_id_1, rule_id_2],
                "merged_at": datetime.now().isoformat(),
            },
        }

        return merged

    def evolve_rule(self, rule_id: str, feedback: dict[str, Any]) -> dict[str, Any] | None:
        """Evolve a rule based on feedback.

        Args:
            rule_id: Rule to evolve
            feedback: Feedback data (success_rate, user_feedback, etc.)

        Returns:
            Evolved rule, or None if evolution not needed
        """
        rule = self.codex.get_rule(rule_id)

        if not rule:
            return None

        # Increment version
        evolved = {
            "id": rule.id,
            "version": rule.version + 1,
            "triggers": rule.triggers,
            "contexts": rule.contexts,
            "lesson": rule.lesson,
            "suggestions": rule.suggestions,
            "actions": rule.actions,
            "tags": rule.tags,
            "lore": rule.lore,
            "meta": {
                **rule.meta,
                "evolution_reason": feedback.get("reason", "user_feedback"),
                "evolved_at": datetime.now().isoformat(),
            },
        }

        # Apply feedback-based modifications
        if feedback.get("success_rate", 1.0) < 0.5:
            # Low success rate - mark for review
            evolved["actions"]["auto_fix"] = False
            evolved["meta"]["needs_review"] = True

        return evolved

    def save_proposal(self, proposal: RuleProposal, output_path: Path | None = None):
        """Save rule proposal to file."""
        if output_path is None:
            output_path = Path("zen-engine/codex/rules/proposals")

        output_path.mkdir(parents=True, exist_ok=True)

        proposal_file = output_path / f"{proposal.proposed_id}_proposal.json"
        with open(proposal_file, "w", encoding="utf-8") as f:
            json.dump(proposal.to_dict(), f, indent=2)

        logger.info(f"💾 Proposal saved: {proposal_file}")


def demo_codex_builder():
    """Demonstrate CodexBuilder capabilities."""
    print("🏗️  ZEN-ENGINE CODEX BUILDER DEMO\n")

    # Create sample events
    observer = ErrorObserver()
    builder = CodexBuilder()

    # Simulate multiple similar errors
    events = [
        observer.observe_error(
            error_text="TypeError: unsupported operand type(s) for +: 'int' and 'str'",
            command="result = 5 + '10'",
            shell="python",
        ),
        observer.observe_error(
            error_text='TypeError: can only concatenate str (not "int") to str',
            command="text = 'Number: ' + 42",
            shell="python",
        ),
        observer.observe_error(
            error_text="TypeError: unsupported operand type(s)",
            command="x = 10 + '5'",
            shell="python",
        ),
    ]

    # Filter out None events
    events = [e for e in events if e is not None]

    if not events:
        print("❌ No events detected")
        return

    print(f"📥 Analyzing {len(events)} error events...")

    # Generate proposals
    proposals = builder.analyze_events(events)

    print(f"\n✅ Generated {len(proposals)} rule proposals\n")

    for proposal in proposals:
        print("=" * 60)
        print(f"Proposed Rule: {proposal.proposed_id}")
        print(f"Confidence: {proposal.confidence:.2%}")
        print(f"Lesson: {proposal.lesson_short}")
        print(f"Tags: {', '.join(proposal.tags)}")
        if proposal.proposed_glyph:
            print(f"Glyph: {proposal.proposed_glyph}")
        print(f"Supporting Events: {len(proposal.supporting_events or [])}")


if __name__ == "__main__":
    demo_codex_builder()
