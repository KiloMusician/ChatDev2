from __future__ import annotations

from typing import Any

try:
    from src.copilot.megatag_processor import \
        MegaTagProcessor as CopilotMegaTagProcessor
except ImportError:  # pragma: no cover - optional dependency
    CopilotMegaTagProcessor = None  # type: ignore[assignment,misc]


class MegaTagProcessor:
    """Compatibility wrapper for MegaTag processing.

    Canonical implementation lives in src/copilot/megatag_processor.py.
    This wrapper preserves legacy methods used by core/integration layers.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize MegaTagProcessor."""
        self._copilot = (
            CopilotMegaTagProcessor(*args, **kwargs)
            if CopilotMegaTagProcessor is not None
            else None
        )
        self.consciousness_bridge: Any | None = None

    def initialize(self) -> None:
        """Initialize the MegaTag processor with consciousness bridge connection."""
        if self._copilot:
            # Copilot processor has no explicit initialize; keep for API compatibility.
            return
        try:
            from src.system.dictionary.consciousness_bridge import \
                ConsciousnessBridge

            self.consciousness_bridge = ConsciousnessBridge()
        except ImportError:
            self.consciousness_bridge = None

    def process_tags(self, tags: list | dict) -> dict[str, Any]:
        """Process tags and return processed tags."""
        if self._copilot and isinstance(tags, dict):
            try:
                return self._copilot.process_mega_tag(tags)
            except Exception:
                return {"processed_tags": tags}
        if isinstance(tags, list):
            return {"processed_tags": tags}
        return tags

    def process_mega_tag(self, tag_data: dict[str, Any]) -> dict[str, Any]:
        """Process a MegaTag payload using the canonical processor when available."""
        if self._copilot:
            try:
                return self._copilot.process_mega_tag(tag_data)
            except Exception:
                return {"processed_tags": tag_data}
        return {"processed_tags": tag_data}

    async def process_megatags(self, megatags: list[str]) -> list[dict[str, Any]]:
        validated_tags = await self.validate_quantum_symbols(megatags)
        extracted_semantics = self.extract_semantics(validated_tags)
        return await self.integrate_with_consciousness_bridge(extracted_semantics)

    async def validate_quantum_symbols(self, megatags: list[str]) -> list[str]:
        """Validate quantum symbols in MegaTags."""
        return [tag for tag in megatags if self.is_valid_quantum_symbol(tag)]

    def is_valid_quantum_symbol(self, tag: str) -> bool:
        """Check if tag contains valid quantum symbols."""
        quantum_symbols = ["⨳", "⦾", "→", "∞", "⟨", "⟩"]
        return any(symbol in tag for symbol in quantum_symbols)

    def extract_semantics(self, tags: list[str]) -> list[dict[str, Any]]:
        """Extract semantic meaning from quantum-tagged content."""
        semantics: list[Any] = []
        for tag in tags:
            parts = tag.split("⨳")
            type_info = parts[0] if parts else "unknown"

            integration_parts = tag.split("⦾")
            integration_points = integration_parts[1:] if len(integration_parts) > 1 else []

            semantics.append(
                {
                    "raw_tag": tag,
                    "type": type_info,
                    "integration_points": integration_points,
                    "quantum_state": tag,
                }
            )
        return semantics

    async def integrate_with_consciousness_bridge(
        self, semantics: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Integrate semantics with consciousness bridge if available."""
        if self.consciousness_bridge:
            return [{"semantic": s, "integrated": True} for s in semantics]
        return semantics


__all__ = ["MegaTagProcessor"]
