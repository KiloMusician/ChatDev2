"""OmniTag: {.

    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Tagging", "Async"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .mega_tag import MegaTag
from .nusyq_tag import NuSyQTag
from .omni_tag import OmniTag
from .rsev_tag import RSEVTag


@dataclass
class TagRule:
    pattern: str
    tags: list[str]
    priority: int
    context_required: bool = False


class TagManager:
    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize TagManager with config_path."""
        self.config_path = config_path or Path("config/tagging_rules.json")

        # Initialize tag systems
        self.omni_tag = OmniTag()
        self.mega_tag = MegaTag()
        self.nusyq_tag = NuSyQTag()
        self.rsev_tag = RSEVTag()

        self.tag_rules: list[TagRule] = []
        self.tag_hierarchy: dict[str, list[str]] = {}
        self.load_tag_rules()

    async def extract_tags(self, text: str, context: str = "") -> list[str]:
        """Extract tags using all tagging systems."""
        all_tags: list[Any] = []
        # Run all tag systems
        omni_tags = await self.omni_tag.extract_tags(text)
        mega_tags = await self.mega_tag.extract_tags(text)
        nusyq_tags = await self.nusyq_tag.extract_tags(text)
        rsev_tags = await self.rsev_tag.extract_tags(text)

        # Rule-based tagging
        rule_tags = self._apply_tag_rules(text, context)

        # Combine and deduplicate
        all_tags.extend(omni_tags + mega_tags + nusyq_tags + rsev_tags + rule_tags)
        return list(set(all_tags))

    def _apply_tag_rules(self, text: str, context: str) -> list[str]:
        """Apply configured tagging rules."""
        tags: list[Any] = []
        for rule in self.tag_rules:
            if self._rule_matches(rule, text, context):
                tags.extend(rule.tags)
        return tags

    def _rule_matches(self, rule: TagRule, text: str, context: str) -> bool:
        """Check if a tagging rule matches the text."""
        import re

        # Check main pattern
        if not re.search(rule.pattern, text, re.IGNORECASE):
            return False

        # Check context requirement
        return not (rule.context_required and not context)

    def load_tag_rules(self) -> None:
        """Load tagging rules from configuration."""
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)
                for rule_data in data.get("rules", []):
                    rule = TagRule(**rule_data)
                    self.tag_rules.append(rule)

                self.tag_hierarchy = data.get("hierarchy", {})
