#!/usr/bin/env python3
"""CodexLoader - Load and Query the ZenCodex

Provides intelligent loading, caching, and querying of the ZenCodex.
Supports version management, tag-based searches, and rule evolution.

OmniTag: [zen-engine, codex-management, knowledge-base]
MegaTag: ZEN_ENGINE⨳CODEX_LOADER⦾WISDOM_RETRIEVAL→∞
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ZenRule:
    """Represents a single rule from the ZenCodex."""

    id: str
    version: int
    triggers: dict[str, Any]
    contexts: dict[str, Any]
    lesson: dict[str, Any]
    suggestions: list[dict[str, Any]]
    actions: dict[str, Any]
    tags: list[str]
    lore: dict[str, Any]
    meta: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ZenRule":
        """Create ZenRule from dictionary."""
        return cls(
            id=data["id"],
            version=data["version"],
            triggers=data.get("triggers", {}),
            contexts=data.get("contexts", {}),
            lesson=data.get("lesson", {}),
            suggestions=data.get("suggestions", []),
            actions=data.get("actions", {}),
            tags=data.get("tags", []),
            lore=data.get("lore", {}),
            meta=data.get("meta", {}),
        )

    def matches_tag(self, tag: str) -> bool:
        """Check if rule has specific tag."""
        return tag.lower() in [t.lower() for t in self.tags]

    def matches_context(
        self, shell: str | None = None, platform: str | None = None, language: str | None = None
    ) -> bool:
        """Check if rule matches given context."""
        if shell and shell not in self.contexts.get("shells", []):
            return False
        if platform and platform not in self.contexts.get("platforms", ["all"]):
            if "all" not in self.contexts.get("platforms", []):
                return False
        if language and language not in self.contexts.get("languages", []):
            return False
        return True

    def get_best_suggestion(self, context: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Get the most appropriate suggestion for the given context."""
        if not self.suggestions:
            return None

        # Simple heuristic: return first suggestion
        # Could be enhanced with context-aware selection
        return self.suggestions[0]

    def to_dict(self) -> dict[str, Any]:
        """Convert ZenRule to dictionary for serialization."""
        return {
            "id": self.id,
            "version": self.version,
            "triggers": self.triggers,
            "contexts": self.contexts,
            "lesson": self.lesson,
            "suggestions": self.suggestions,
            "actions": self.actions,
            "tags": self.tags,
            "lore": self.lore,
            "meta": self.meta,
        }


class CodexLoader:
    """Load and manage the ZenCodex.

    Provides caching, querying, and version management for rules.
    """

    def __init__(self, codex_path: Path | str = "zen_engine/codex/zen.json"):
        """Initialize the CodexLoader."""
        self.codex_path = Path(codex_path)
        self.codex_data: dict[str, Any] = {}
        self.rules: dict[str, ZenRule] = {}
        self.rules_by_tag: dict[str, list[ZenRule]] = {}
        self.last_loaded: datetime | None = None

        self.load_codex()

    def load_codex(self, force_reload: bool = False) -> bool:
        """Load the ZenCodex from disk.

        Args:
            force_reload: Force reload even if already loaded

        Returns:
            True if loaded successfully
        """
        if self.rules and not force_reload:
            logger.debug("Codex already loaded, skipping reload")
            return True

        if not self.codex_path.exists():
            logger.error(f"Codex not found at {self.codex_path}")
            return False

        try:
            with open(self.codex_path, encoding="utf-8") as f:
                self.codex_data = json.load(f)

            # Parse rules
            self.rules = {}
            for rule_data in self.codex_data.get("rules", []):
                rule = ZenRule.from_dict(rule_data)
                self.rules[rule.id] = rule

            # Build tag index
            self._build_tag_index()

            self.last_loaded = datetime.now()
            logger.info(f"✅ Codex loaded: {len(self.rules)} rules from {self.codex_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load codex: {e}")
            return False

    def _build_tag_index(self):
        """Build index of rules by tag for fast lookup."""
        self.rules_by_tag = {}
        for rule in self.rules.values():
            for tag in rule.tags:
                tag_lower = tag.lower()
                if tag_lower not in self.rules_by_tag:
                    self.rules_by_tag[tag_lower] = []
                self.rules_by_tag[tag_lower].append(rule)

    def get_rule(self, rule_id: str) -> ZenRule | None:
        """Get a specific rule by ID."""
        return self.rules.get(rule_id)

    def get_rules_by_tag(self, tag: str) -> list[ZenRule]:
        """Get all rules with a specific tag."""
        return self.rules_by_tag.get(tag.lower(), [])

    def get_rules_by_tags(self, tags: list[str], match_all: bool = False) -> list[ZenRule]:
        """Get rules matching tags.

        Args:
            tags: List of tags to match
            match_all: If True, rules must have ALL tags. If False, ANY tag matches.

        Returns:
            List of matching rules
        """
        if not tags:
            return list(self.rules.values())

        if match_all:
            # Rule must have ALL tags
            matching = []
            for rule in self.rules.values():
                if all(rule.matches_tag(tag) for tag in tags):
                    matching.append(rule)
            return matching
        else:
            # Rule must have ANY tag
            matching_rules = set()
            for tag in tags:
                matching_rules.update(self.get_rules_by_tag(tag))
            return list(matching_rules)

    def get_rules_by_context(
        self,
        shell: str | None = None,
        platform: str | None = None,
        language: str | None = None,
    ) -> list[ZenRule]:
        """Get rules matching execution context."""
        matching = []
        for rule in self.rules.values():
            if rule.matches_context(shell=shell, platform=platform, language=language):
                matching.append(rule)
        return matching

    def get_rule_clusters(self) -> dict[str, list[str]]:
        """Get rule clusters from codex."""
        clusters: dict[str, list[str]] = self.codex_data.get("rule_clusters", {})
        return clusters

    def get_cluster(self, cluster_name: str) -> list[ZenRule]:
        """Get all rules in a specific cluster."""
        clusters = self.get_rule_clusters()
        rule_ids = clusters.get(cluster_name, [])
        return [self.rules[rid] for rid in rule_ids if rid in self.rules]

    def get_foundational_rules(self) -> list[ZenRule]:
        """Get all foundational-level rules."""
        return self.get_rules_by_tag("foundational")

    def get_auto_fixable_rules(self) -> list[ZenRule]:
        """Get all auto-fixable rules."""
        return [rule for rule in self.rules.values() if rule.actions.get("auto_fix", False)]

    def search_rules(self, query: str) -> list[ZenRule]:
        """Search rules by keyword in lesson, suggestions, or lore.

        Args:
            query: Search query

        Returns:
            List of matching rules
        """
        query_lower = query.lower()
        matching = []

        for rule in self.rules.values():
            # Search in lesson
            if query_lower in rule.lesson.get("short", "").lower():
                matching.append(rule)
                continue
            if query_lower in rule.lesson.get("long", "").lower():
                matching.append(rule)
                continue

            # Search in lore
            if query_lower in rule.lore.get("story", "").lower():
                matching.append(rule)
                continue

            # Search in tags
            if any(query_lower in tag.lower() for tag in rule.tags):
                matching.append(rule)
                continue

        return matching

    def get_meta(self) -> dict[str, Any]:
        """Get codex metadata."""
        meta: dict[str, Any] = self.codex_data.get("meta", {})
        return meta

    def get_evolution_history(self) -> list[dict[str, Any]]:
        """Get codex evolution history."""
        history: list[dict[str, Any]] = self.codex_data.get("evolution_history", [])
        return history

    def stats(self) -> dict[str, Any]:
        """Get codex statistics."""
        return {
            "total_rules": len(self.rules),
            "total_tags": len(self.rules_by_tag),
            "auto_fixable_rules": len(self.get_auto_fixable_rules()),
            "foundational_rules": len(self.get_foundational_rules()),
            "clusters": len(self.get_rule_clusters()),
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "codex_version": self.codex_data.get("meta", {}).get("version", "unknown"),
        }

    def save_rule(self, rule: ZenRule, update_version: bool = True) -> bool:
        """Save a new rule or update existing rule in zen.json.

        Args:
            rule: ZenRule to save
            update_version: If True and rule exists, increment version

        Returns:
            True if saved successfully
        """
        try:
            # Check if rule already exists
            existing_rule = self.rules.get(rule.id)
            if existing_rule and update_version:
                rule.version = existing_rule.version + 1
                rule.meta["updated_at"] = datetime.now().isoformat()
                logger.info(f"Updating rule {rule.id} to version {rule.version}")
            else:
                rule.meta["created_at"] = datetime.now().isoformat()
                logger.info(f"Creating new rule {rule.id} version {rule.version}")

            # Update in-memory rules
            self.rules[rule.id] = rule

            # Update codex_data
            rule_dicts = [r.to_dict() for r in self.rules.values()]
            self.codex_data["rules"] = rule_dicts

            # Save atomically (write to temp file, then rename)
            temp_path = self.codex_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.codex_data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(self.codex_path)

            # Rebuild tag index
            self._build_tag_index()

            logger.info(f"✅ Rule {rule.id} saved to {self.codex_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save rule {rule.id}: {e}")
            return False

    def save_rules_batch(self, rules: list[ZenRule]) -> dict[str, Any]:
        """Save multiple rules at once (more efficient than individual saves).

        Args:
            rules: List of ZenRule objects to save

        Returns:
            Dict with success count and failed rule IDs
        """
        results = {"success": 0, "failed": []}

        try:
            # Update all rules in memory first
            for rule in rules:
                existing_rule = self.rules.get(rule.id)
                if existing_rule:
                    rule.version = existing_rule.version + 1
                    rule.meta["updated_at"] = datetime.now().isoformat()
                else:
                    rule.meta["created_at"] = datetime.now().isoformat()

                self.rules[rule.id] = rule

            # Update codex_data
            rule_dicts = [r.to_dict() for r in self.rules.values()]
            self.codex_data["rules"] = rule_dicts

            # Save atomically
            temp_path = self.codex_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.codex_data, f, indent=2, ensure_ascii=False)

            temp_path.replace(self.codex_path)

            # Rebuild tag index
            self._build_tag_index()

            results["success"] = len(rules)
            logger.info(f"✅ Saved {len(rules)} rules to {self.codex_path}")

        except Exception as e:
            logger.error(f"❌ Failed to save rules batch: {e}")
            results["failed"] = [r.id for r in rules]

        return results


def demo_codex_loader():
    """Demonstrate CodexLoader capabilities."""
    print("📚 ZEN-ENGINE CODEX LOADER DEMO\n")

    loader = CodexLoader()

    # Show stats
    print("📊 Codex Statistics:")
    stats = loader.stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Get foundational rules
    print("\n🎓 Foundational Rules:")
    foundational = loader.get_foundational_rules()
    for rule in foundational[:3]:
        print(f"   - {rule.id}: {rule.lesson['short']}")

    # Get PowerShell-related rules
    print("\n⚙️  PowerShell Rules:")
    ps_rules = loader.get_rules_by_tag("powershell")
    for rule in ps_rules:
        print(f"   - {rule.id}: {rule.lesson['short']}")

    # Search for "import" issues
    print("\n🔍 Search Results for 'import':")
    results = loader.search_rules("import")
    for rule in results[:3]:
        print(f"   - {rule.id}: {rule.lesson['short']}")

    # Get auto-fixable rules
    print("\n🔧 Auto-Fixable Rules:")
    auto_fix = loader.get_auto_fixable_rules()
    for rule in auto_fix[:3]:
        print(f"   - {rule.id}: {rule.actions['fix_strategy']}")


if __name__ == "__main__":
    demo_codex_loader()
