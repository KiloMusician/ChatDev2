import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class Translation:
    original: str
    translated: str
    context: str
    confidence: float
    tags: list[str]


class RosettaStone:
    def __init__(self, data_path: Path | None = None):
        self.data_path = data_path or Path("data/dictionaries")
        self.data_path.mkdir(parents=True, exist_ok=True)

        self.translations: dict[str, Translation] = {}
        self.unknown_words: set[str] = set()
        self.symbol_mappings: dict[str, str] = {}
        self.context_patterns: dict[str, list[str]] = {}

        # Load existing data
        self.load_rosetta_data()

    async def process_unknown_words(self, text: str) -> str:
        """Process text and handle unknown words/symbols."""
        unknown_elements = self._extract_unknown_elements(text)

        processed_text = text
        for element in unknown_elements:
            if element not in self.translations:
                # Add to unknown words for manual review
                self.unknown_words.add(element)

                # Attempt auto-translation
                translation = await self._attempt_auto_translation(element, text)
                if translation:
                    self.translations[element] = translation
                    processed_text = processed_text.replace(element, translation.translated)

        await self.save_unknown_words()
        return processed_text

    def _extract_unknown_elements(self, text: str) -> list[str]:
        """Extract potentially unknown words and symbols."""
        patterns = [
            r"[Ξ∞Ψ∫⟨⟩⊗⨁∇Δ∂⛛Φ₁Σ]+",  # Special mathematical/Greek symbols
            r"\b[A-Z]{2,}(?:[0-9]+)?\b",  # All-caps technical terms
            r"(?:[A-Za-z]+[₀-₉]+)+",  # Subscripted terms
            r"(?:[A-Za-z]*[ΞΨΦΣΔΩαβγδε][A-Za-z]*)+",  # Mixed Greek
        ]

        unknown: list[str] = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            unknown.extend(matches)

        return list(set(unknown))

    async def _attempt_auto_translation(self, element: str, context: str) -> Translation | None:
        """Attempt to auto-translate based on context and patterns."""
        # Check symbol mappings
        if element in self.symbol_mappings:
            return Translation(
                original=element,
                translated=self.symbol_mappings[element],
                context=context[:100],
                confidence=0.8,
                tags=["symbol", "auto-translated"],
            )

        # Pattern-based translation
        if "Ξ" in element:
            return Translation(
                original=element,
                translated=f"[Xi-based system: {element}]",
                context=context[:100],
                confidence=0.6,
                tags=["greek", "system-notation", "auto-generated"],
            )

        return None

    def add_manual_translation(
        self,
        original: str,
        translated: str,
        context: str = "",
        tags: list[str] | None = None,
    ):
        """Manually add a translation for an unknown element."""
        self.translations[original] = Translation(
            original=original,
            translated=translated,
            context=context,
            confidence=1.0,
            tags=tags or ["manual"],
        )

        if original in self.unknown_words:
            self.unknown_words.remove(original)

    def load_rosetta_data(self) -> None:
        """Load existing translations and mappings."""
        translations_file = self.data_path / "rosetta_translations.json"
        unknown_file = self.data_path / "unknown_words.json"

        if translations_file.exists():
            with open(translations_file, encoding="utf-8") as f:
                data = json.load(f)
            for key, value in data.items():
                self.translations[key] = Translation(**value)

        if unknown_file.exists():
            with open(unknown_file, encoding="utf-8") as f:
                data = json.load(f)
            self.unknown_words = set(data.get("unknown_words", []))

    async def save_unknown_words(self) -> None:
        """Save current unknown words for review."""
        unknown_file = self.data_path / "unknown_words.json"
        with open(unknown_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "unknown_words": list(self.unknown_words),
                    "last_updated": datetime.now().isoformat(),
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
