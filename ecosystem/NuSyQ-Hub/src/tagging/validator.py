from __future__ import annotations

from typing import Any


class Validator:
    """Comprehensive schema validator for repository tagging systems.

    Supported tags and expected shapes:
    - OmniTag: dict with required key 'purpose' (str), optional keys:
        'dependencies' (list[str]), 'context' (str), 'evolution_stage' (str)
    - MegaTag: str pattern like "TYPE⨳INTEGRATION⦾[...]→∞" OR dict with keys
        'type' (str), 'integration_points' (list[str])
    - RSHTS: non-empty str (symbolic pattern). Must contain at least one semantic marker (⨳, ◊, ♦, ●, ○, ◉).
    Contract:
    - validate(data) returns True iff all items pass; errors accessible via get_errors().
    - validate_item(item) validates a single record containing any of the tags above.
    - No external dependencies; intentionally minimal and robust.
    - get_errors() returns a list of error strings for failed validations.
    """

    def __init__(self, strict: bool = True) -> None:
        """Initialize Validator with strict."""
        self.strict = strict
        self._errors: list[str] = []

    # ------------------------------- Public API -------------------------------
    def validate(self, data: list[dict[str, Any]]) -> bool:
        """Validate a list of tagging records.

        Each record may contain any of: 'OmniTag', 'MegaTag', 'RSHTS'.
        Returns True iff all records pass validation.
        Errors are accumulated and accessible via get_errors().
        """
        self._errors.clear()
        all_ok = True
        for item in data:
            ok = self.validate_item(item)
            if not ok:
                all_ok = False
        return all_ok

    def validate_item(self, item: dict[str, Any]) -> bool:
        ok = True

        # OmniTag
        if "OmniTag" in item:
            passed, msg = self._validate_omnitag(item["OmniTag"])
            if not passed:
                ok = False
                self._record_error(f"OmniTag invalid: {msg}")

        # MegaTag
        if "MegaTag" in item:
            passed, msg = self._validate_megatag(item["MegaTag"])
            if not passed:
                ok = False
                self._record_error(f"MegaTag invalid: {msg}")

        # RSHTS
        if "RSHTS" in item:
            passed, msg = self._validate_rshts(item["RSHTS"])
            if not passed:
                ok = False
                self._record_error(f"RSHTS invalid: {msg}")

        # If strict and none of the known tags exist, flag it
        if self.strict and not any(k in item for k in ("OmniTag", "MegaTag", "RSHTS")):
            ok = False
            self._record_error("Record contains no known tags (OmniTag, MegaTag, RSHTS)")

        return ok

    def get_errors(self) -> list[str]:
        """Return a list of error strings for failed validations."""
        return list(self._errors)

    # ----------------------------- Internal helpers ----------------------------
    def _validate_omnitag(self, tag: Any) -> tuple[bool, str]:
        """Validate OmniTag schema."""
        if not isinstance(tag, dict):
            return False, "OmniTag must be a dict"

        # Required
        purpose = tag.get("purpose")
        if not isinstance(purpose, str) or not purpose.strip():
            return False, "OmniTag.purpose must be a non-empty string"

        # Optional but typed
        deps = tag.get("dependencies")
        if deps is not None and (
            not isinstance(deps, list) or not all(isinstance(d, str) for d in deps)
        ):
            return False, "OmniTag.dependencies must be a list[str] when present"

        context = tag.get("context")
        if context is not None and not isinstance(context, str):
            return False, "OmniTag.context must be a string when present"

        evo = tag.get("evolution_stage")
        if evo is not None and not isinstance(evo, str):
            return False, "OmniTag.evolution_stage must be a string when present"

        return True, "ok"

    def _validate_megatag(self, tag: Any) -> tuple[bool, str]:
        """Validate MegaTag schema."""
        # Accept either string pattern or structured dict
        if isinstance(tag, str):
            s = tag.strip()
            if not s:
                return False, "MegaTag string cannot be empty"
            # Heuristic: ensure it contains the expected semantic markers
            markers = ["⨳", "⦾", "→∞"]
            if not all(m in s for m in markers):
                return False, "MegaTag string missing expected markers (⨳, ⦾, →∞)"
            return True, "ok"

        if isinstance(tag, dict):
            t = tag.get("type")
            points = tag.get("integration_points")
            if not isinstance(t, str) or not t:
                return False, "MegaTag.type must be a non-empty string"
            if points is not None and (
                not isinstance(points, list) or not all(isinstance(p, str) for p in points)
            ):
                return (
                    False,
                    "MegaTag.integration_points must be a list[str] when present",
                )
            return True, "ok"

        return False, "MegaTag must be a string or dict"

    def _validate_rshts(self, tag: Any) -> tuple[bool, str]:
        """Validate RSHTS symbolic tag schema."""
        if not isinstance(tag, str) or not tag.strip():
            return False, "RSHTS must be a non-empty string"
        # Heuristic for symbolic richness
        if not any(ch in tag for ch in ("⨳", "◊", "♦", "●", "○", "◉")):
            return False, "RSHTS lacks expected symbolic markers"
        return True, "ok"

    def _record_error(self, msg: str) -> None:
        self._errors.append(msg)
