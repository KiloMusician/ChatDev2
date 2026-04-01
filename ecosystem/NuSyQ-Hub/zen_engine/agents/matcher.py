#!/usr/bin/env python3
"""Matcher - Match Error Events to ZenCodex Rules

Determines if rules apply to error events, computes match confidence,
and proposes suggestions with ranking.

OmniTag: [zen-engine, pattern-matching, rule-matching, ai]
MegaTag: ZEN_ENGINE⨳MATCHER⦾WISDOM_APPLICATION→∞
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

from zen_engine.agents.codex_loader import CodexLoader, ZenRule
from zen_engine.agents.error_observer import ErrorEvent

logger = logging.getLogger(__name__)


@dataclass
class RuleMatch:
    """Represents a matched rule with confidence score."""

    rule: ZenRule
    event: ErrorEvent
    confidence: float  # 0.0 to 1.0
    match_reasons: list[str]
    suggested_action: dict[str, Any] | None = None

    def get_advice(self) -> str:
        """Generate human-readable advice from match."""
        lesson = self.rule.lesson.get("short", "No lesson available")
        suggestion = self.suggested_action

        advice = f"🧘 Zen Advice: {lesson}\n"

        if suggestion:
            strategy = suggestion.get("strategy", "unknown")
            example_after = suggestion.get("example_after", "")

            advice += f"\n💡 Suggested fix ({strategy}):\n"
            if example_after:
                advice += f"   {example_after}\n"

            when_to_use = suggestion.get("when_to_use", "")
            if when_to_use:
                advice += f"\n   Use when: {when_to_use}\n"

        if self.rule.actions.get("auto_fix"):
            advice += f"\n🤖 Auto-fix available: {self.rule.actions.get('fix_strategy', 'yes')}\n"

        advice += f"\n📖 Learn more: Rule ID {self.rule.id} (v{self.rule.version})"

        return advice

    def get_lore(self) -> str:
        """Get the narrative lore for this rule."""
        lore = self.rule.lore
        if not lore:
            return ""

        glyph = lore.get("glyph", "")
        story = lore.get("story", "")
        moral = lore.get("moral", "")

        lore_text = f"✨ Zen Lore [{glyph}]\n"
        if story:
            lore_text += f"\n{story}\n"
        if moral:
            lore_text += f"\n💎 Moral: {moral}\n"

        return lore_text


class Matcher:
    """Match error events to ZenCodex rules with confidence scoring.

    Uses pattern matching, context analysis, and semantic similarity
    to determine which rules apply to an error event.
    """

    def __init__(self, codex_loader: CodexLoader | None = None):
        """Initialize the Matcher."""
        self.codex = codex_loader or CodexLoader()

    def match_event_to_rules(self, event: ErrorEvent) -> list[RuleMatch]:
        """Match an error event to all applicable rules.

        Args:
            event: The ErrorEvent to match

        Returns:
            List of RuleMatch objects, sorted by confidence (highest first)
        """
        matches = []

        # Try all rules in codex
        for rule in self.codex.rules.values():
            confidence, reasons = self._compute_match_confidence(event, rule)

            if confidence > 0.3:  # Minimum confidence threshold
                suggested_action = rule.get_best_suggestion(event.context)
                match = RuleMatch(
                    rule=rule,
                    event=event,
                    confidence=confidence,
                    match_reasons=reasons,
                    suggested_action=suggested_action,
                )
                matches.append(match)

        # Sort by confidence (highest first)
        matches.sort(key=lambda m: m.confidence, reverse=True)

        return matches

    def _compute_match_confidence(
        self, event: ErrorEvent, rule: ZenRule
    ) -> tuple[float, list[str]]:
        """Compute match confidence between event and rule.

        Returns:
            Tuple of (confidence_score, list_of_match_reasons)
        """
        confidence = 0.0
        reasons = []

        # 1. Check error pattern triggers (40% weight)
        error_match_score = self._match_error_patterns(
            event.error_lines, rule.triggers.get("errors", [])
        )
        if error_match_score > 0:
            confidence += error_match_score * 0.4
            reasons.append(f"error_pattern_match ({error_match_score:.2f})")

        # 2. Check command pattern triggers (30% weight)
        command = event.context.get("command_before_error", "")
        command_match_score = self._match_command_patterns(
            command, rule.triggers.get("command_patterns", [])
        )
        if command_match_score > 0:
            confidence += command_match_score * 0.3
            reasons.append(f"command_pattern_match ({command_match_score:.2f})")

        # 3. Check context match (20% weight)
        context_match_score = self._match_context(event, rule)
        if context_match_score > 0:
            confidence += context_match_score * 0.2
            reasons.append(f"context_match ({context_match_score:.2f})")

        # 4. Check if event explicitly suggests this rule (10% weight)
        if rule.id in event.suggested_rules:
            confidence += 0.1
            reasons.append("explicit_suggestion")

        return confidence, reasons

    def _match_error_patterns(self, error_lines: list[str], patterns: list[str]) -> float:
        """Check if error lines match any of the patterns.

        Returns:
            Score from 0.0 to 1.0
        """
        if not patterns:
            return 0.0

        error_text = "\n".join(error_lines)
        matches = 0

        for pattern in patterns:
            if re.search(pattern, error_text, re.IGNORECASE):
                matches += 1

        # Return proportion of patterns matched
        return matches / len(patterns)

    def _match_command_patterns(self, command: str, patterns: list[str]) -> float:
        """Check if command matches any of the patterns.

        Returns:
            Score from 0.0 to 1.0 (1.0 if any pattern matches)
        """
        if not patterns or not command:
            return 0.0

        for pattern in patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return 1.0

        return 0.0

    def _match_context(self, event: ErrorEvent, rule: ZenRule) -> float:
        """Check if event context matches rule contexts.

        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.0
        checks = 0

        # Check shell match
        rule_shells = rule.contexts.get("shells", [])
        if rule_shells:
            checks += 1
            if event.shell in rule_shells:
                score += 1.0

        # Check platform match
        rule_platforms = rule.contexts.get("platforms", ["all"])
        if rule_platforms and "all" not in rule_platforms:
            checks += 1
            platform = event.context.get("platform", "unknown")
            if platform in rule_platforms:
                score += 1.0

        # Check language match
        rule_languages = rule.contexts.get("languages", [])
        if rule_languages:
            checks += 1
            if event.language_intent in rule_languages:
                score += 1.0

        if checks == 0:
            return 0.0

        return score / checks

    def select_best_rule(self, matches: list[RuleMatch]) -> RuleMatch | None:
        """Select the best matching rule from a list of matches.

        Args:
            matches: List of RuleMatch objects

        Returns:
            Best match, or None if no matches
        """
        if not matches:
            return None

        # Matches are already sorted by confidence
        return matches[0]

    def rank_matches(self, matches: list[RuleMatch]) -> list[RuleMatch]:
        """Rank matches by confidence and other criteria.

        Currently just returns matches sorted by confidence,
        but could be extended with additional ranking logic.

        Args:
            matches: List of RuleMatch objects

        Returns:
            Sorted list of matches
        """
        return sorted(matches, key=lambda m: m.confidence, reverse=True)

    def compose_multi_rule_advice(self, event: ErrorEvent, matches: list[RuleMatch]) -> str:
        """Compose advice from multiple matching rules.

        Args:
            event: The error event
            matches: List of matching rules

        Returns:
            Formatted advice string
        """
        if not matches:
            return "❓ No matching rules found in ZenCodex."

        advice = f"🔍 Zen-Engine Analysis for: {event.symptom}\n"
        advice += f"   Event ID: {event.id}\n\n"

        # Show top 3 matches
        for i, match in enumerate(matches[:3], 1):
            advice += f"\n{'=' * 60}\n"
            advice += f"Match #{i} (Confidence: {match.confidence:.2%})\n"
            advice += f"{'=' * 60}\n"
            advice += match.get_advice()

            if i == 1 and match.rule.lore:
                advice += f"\n\n{match.get_lore()}"

        if len(matches) > 3:
            advice += f"\n\n💡 {len(matches) - 3} additional rules available"

        return advice


def demo_matcher():
    """Demonstrate Matcher capabilities."""
    from zen_engine.agents.error_observer import ErrorObserver

    print("🎯 ZEN-ENGINE MATCHER DEMO\n")

    # Create components
    observer = ErrorObserver()
    matcher = Matcher()

    # Test case 1: Python in PowerShell
    print("Test Case 1: Python in PowerShell")
    print("-" * 60)
    event = observer.observe_error(
        error_text="The term 'import' is not recognized as the name of a cmdlet",
        command="import os",
        shell="powershell",
        platform="windows",
        agent="copilot",
    )

    if event:
        matches = matcher.match_event_to_rules(event)
        advice = matcher.compose_multi_rule_advice(event, matches)
        print(advice)

    # Test case 2: Missing module
    print("\n\nTest Case 2: Missing Python Module")
    print("-" * 60)
    event2 = observer.observe_error(
        error_text="ModuleNotFoundError: No module named 'numpy'",
        command="import numpy as np",
        shell="bash",
        platform="linux",
        agent="user",
    )

    if event2:
        matches2 = matcher.match_event_to_rules(event2)
        best_match = matcher.select_best_rule(matches2)
        if best_match:
            print(f"Best Match: {best_match.rule.id}")
            print(f"Confidence: {best_match.confidence:.2%}")
            print(f"\n{best_match.get_advice()}")


if __name__ == "__main__":
    demo_matcher()
