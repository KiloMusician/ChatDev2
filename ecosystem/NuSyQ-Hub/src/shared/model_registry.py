from __future__ import annotations

import contextlib
import json
import logging
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


try:
    import portalocker
except Exception:  # pragma: no cover - portalocker optional in some envs
    portalocker = None

try:
    from jsonschema import Draft7Validator, ValidationError
except Exception:  # pragma: no cover - jsonschema optional in some envs
    Draft7Validator = None
    ValidationError = Exception


REGISTRY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "name": {"type": "string"},
        "source": {"type": "string"},
        "format": {"type": "string"},
        "size_bytes": {"type": "number"},
        "metadata": {"type": "object"},
    },
    "required": ["path", "name", "source"],
    "additionalProperties": True,
}


class ModelRegistry:
    """JSON-backed Model Registry with basic schema validation and file locking.

    - Uses an atomic write on save.
    - Uses `portalocker` (when available) to guard concurrent access.
    - Validates metadata against a small JSON schema before persisting.
    """

    def __init__(self, path: Path | None = None) -> None:
        """Initialize ModelRegistry with path."""
        self.path = Path(path) if path else Path("state") / "registry.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _acquire_lock(self, fh):
        if portalocker is not None:
            portalocker.lock(fh, portalocker.LOCK_EX)

    def _release_lock(self, fh):
        if portalocker is not None:
            with contextlib.suppress(Exception):
                portalocker.unlock(fh)

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            # read under lock if portalocker available
            if portalocker is not None:
                with self.path.open("r", encoding="utf-8") as fh:
                    self._acquire_lock(fh)
                    try:
                        data = json.load(fh)
                    finally:
                        self._release_lock(fh)
                return data or []
            else:
                return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_atomic(self, data: list[dict[str, Any]]) -> None:
        serialized = json.dumps(data, indent=2, ensure_ascii=False)
        if portalocker is not None:
            # On Windows, os.replace() fails while the file is open (WinError 5).
            # Write directly into the locked file handle instead (seek+truncate).
            self.path.touch(exist_ok=True)
            with self.path.open("r+", encoding="utf-8") as fh:
                self._acquire_lock(fh)
                try:
                    fh.seek(0)
                    fh.write(serialized)
                    fh.truncate()
                finally:
                    self._release_lock(fh)
        else:
            # No portalocker: use atomic rename for best-effort crash safety.
            tmp = Path(tempfile.mktemp(dir=str(self.path.parent)))
            tmp.write_text(serialized, encoding="utf-8")
            tmp.replace(self.path)

    def list_models(self) -> list[dict[str, Any]]:
        return self._load()

    def find(self, path: str) -> dict[str, Any] | None:
        for item in self._load():
            if item.get("path") == path:
                return item
        return None

    def validate_metadata(self, metadata: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate metadata against a small JSON schema. Returns (valid, errors)."""
        if Draft7Validator is None:
            # If jsonschema is not available, do a minimal sanity check
            required = REGISTRY_SCHEMA.get("required", [])
            missing = [k for k in required if k not in metadata]
            if missing:
                return False, [f"missing required fields: {missing}"]
            return True, []

        validator = Draft7Validator(REGISTRY_SCHEMA)
        errors = []
        missing_fields = []
        for err in sorted(validator.iter_errors(metadata), key=lambda e: e.path):
            msg = err.message
            # Normalize required-property messages to include the word 'missing'
            if "required property" in msg or "is a required property" in msg:
                # extract the field name from message like "'path' is a required property"
                try:
                    import re

                    m = re.findall(r"'([^']+)'", msg)
                    for name in m:
                        if name not in missing_fields:
                            missing_fields.append(name)
                except Exception:
                    logger.debug("Suppressed Exception", exc_info=True)
            else:
                errors.append(f"{list(err.path)}: {msg}")

        if missing_fields:
            errors.insert(0, f"missing required fields: {missing_fields}")
        return (len(errors) == 0, errors)

    def register_model(self, metadata: dict[str, Any], apply: bool = False) -> bool:
        """Register model metadata.

        - If apply==False: dry-run (returns False as previous behavior).
        - If apply==True: validates metadata and persists; raises ValueError on invalid input.
        """
        if not apply:
            # dry-run (preserve previous behavior)
            return False

        valid, errors = self.validate_metadata(metadata)
        if not valid:
            raise ValueError(f"Invalid metadata: {errors}")

        data = self._load()
        # avoid duplicates by path
        existing = None
        for item in data:
            if item.get("path") == metadata.get("path"):
                existing = item
                break
        if existing:
            existing.update(metadata)
        else:
            data.append(metadata)
        self._save_atomic(data)
        return True

    def health(self) -> dict[str, Any]:
        items = self._load()
        return {"count": len(items)}
