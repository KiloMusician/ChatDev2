"""Consciousness Validator - ΞNuSyQ protocol validation.

Part of the Consciousness Bridge system for multi-agent AI coordination.
"""

from typing import Any


class ConsciousnessValidator:
    """Validator for ΞNuSyQ protocol compliance and consciousness data structures."""

    def __init__(self):
        """Initialize validator with protocol definitions."""
        self.required_fields = {"type", "value", "timestamp"}
        self.optional_fields = {"metadata", "origin", "tags"}
        self.validation_log: list[dict[str, Any]] = []

    async def validate(self, data: dict[str, Any]) -> bool:
        """Validate data against ΞNuSyQ protocol.

        Args:
            data: Dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Type check
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")

            # Required fields check
            missing_fields = self.required_fields - set(data.keys())
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")

            # Type validation
            if not isinstance(data.get("type"), str):
                raise ValueError("Field 'type' must be a string")

            if not isinstance(data.get("timestamp"), str):
                raise ValueError("Field 'timestamp' must be a string")

            # Protocol compliance check
            if not self._is_protocol_compliant(data):
                raise ValueError("Data does not comply with ΞNuSyQ protocol")

            self.validation_log.append({"data": data, "valid": True})
            return True

        except Exception as e:
            self.validation_log.append({"data": data, "valid": False, "error": str(e)})
            return False

    def _is_protocol_compliant(self, data: dict[str, Any]) -> bool:
        """Check ΞNuSyQ protocol compliance.

        Args:
            data: Data to check for protocol compliance

        Returns:
            True if protocol compliant
        """
        # Protocol checks
        allowed_types = {"state", "action", "observation", "memory", "consciousness"}
        if data.get("type") not in allowed_types:
            return False

        # Timestamp validation (ISO format check)
        timestamp = data.get("timestamp", "")
        return self._is_valid_iso_timestamp(timestamp)

    def _is_valid_iso_timestamp(self, timestamp: Any) -> bool:
        """Check if timestamp is in ISO 8601 format.

        Args:
            timestamp: Timestamp string to validate

        Returns:
            True if valid ISO timestamp
        """
        # Simple ISO 8601 check
        if not isinstance(timestamp, str):
            return False

        # Require all three ISO 8601 components: YYYY-MM-DDTHH:MM:SS
        # Check for required patterns: T separator + time colons + date hyphens
        has_date_separator = "-" in timestamp
        has_time_separator = "T" in timestamp
        has_time_colons = ":" in timestamp

        # Must have all three components for valid ISO 8601
        return has_date_separator and has_time_separator and has_time_colons

    def validate_type(self, value: Any, expected_type: type) -> bool:
        """Validate value type.

        Args:
            value: Value to check
            expected_type: Expected Python type

        Returns:
            True if type matches
        """
        return isinstance(value, expected_type)

    def validate_collection(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate a collection of consciousness data.

        Args:
            items: List of data dictionaries to validate

        Returns:
            Validation report with counts
        """
        total = len(items)
        valid_count = sum(1 for item in items if isinstance(item, dict))
        invalid_count = total - valid_count

        return {
            "total": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "valid_percentage": (valid_count / total * 100) if total > 0 else 0,
        }

    def get_validation_log(self) -> list[dict[str, Any]]:
        """Get validation log.

        Returns:
            List of validation results
        """
        return self.validation_log.copy()
