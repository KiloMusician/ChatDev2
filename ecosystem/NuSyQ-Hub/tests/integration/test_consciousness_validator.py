"""Tests for Consciousness Validator - ΞNuSyQ protocol validation."""

from typing import Any, Dict, List

import pytest


class ConsciousnessValidator:
    """Validator for ΞNuSyQ protocol compliance and consciousness data structures."""

    def __init__(self):
        """Initialize validator with protocol definitions."""
        self.required_fields = {"type", "value", "timestamp"}
        self.optional_fields = {"metadata", "origin", "tags"}
        self.validation_log: List[Dict[str, Any]] = []

    async def validate(self, data: Dict[str, Any]) -> bool:
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

    def _is_protocol_compliant(self, data: Dict[str, Any]) -> bool:
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
        if not self._is_valid_iso_timestamp(timestamp):
            return False

        return True

    def _is_valid_iso_timestamp(self, timestamp: str) -> bool:
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

    def validate_collection(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
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

    def get_validation_log(self) -> List[Dict[str, Any]]:
        """Get validation log.

        Returns:
            List of validation results
        """
        return self.validation_log.copy()


# ============ PYTEST TESTS ============


class TestConsciousnessValidator:
    """Test suite for Consciousness Validator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for tests."""
        return ConsciousnessValidator()

    def test_init(self, validator):
        """Test validator initialization."""
        assert validator is not None
        assert "type" in validator.required_fields
        assert "value" in validator.required_fields
        assert "timestamp" in validator.required_fields
        assert len(validator.validation_log) == 0

    @pytest.mark.asyncio
    async def test_validate_valid_data(self, validator):
        """Test validation of valid data."""
        data = {
            "type": "state",
            "value": {"indicator": "active"},
            "timestamp": "2026-02-02T11:30:00Z",
        }

        result = await validator.validate(data)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_valid_with_optional(self, validator):
        """Test validation with optional fields."""
        data = {
            "type": "action",
            "value": {"action": "execute"},
            "timestamp": "2026-02-02T11:30:00Z",
            "metadata": {"source": "agent-1"},
            "origin": "consciousness-bridge",
            "tags": ["test", "validation"],
        }

        result = await validator.validate(data)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_missing_required_field(self, validator):
        """Test validation fails with missing required field."""
        data = {
            "type": "observation",
            "timestamp": "2026-02-02T11:30:00Z",
            # Missing "value"
        }

        result = await validator.validate(data)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_invalid_type_field(self, validator):
        """Test validation fails with invalid type field."""
        data = {
            "type": 123,  # Should be string
            "value": "test",
            "timestamp": "2026-02-02T11:30:00Z",
        }

        result = await validator.validate(data)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_invalid_timestamp_format(self, validator):
        """Test validation fails with invalid timestamp."""
        data = {
            "type": "memory",
            "value": "data",
            "timestamp": "not-a-timestamp",  # Invalid format
        }

        result = await validator.validate(data)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_invalid_data_type(self, validator):
        """Test validation fails when input is not dict."""
        result = await validator.validate("not a dict")
        assert result is False

    def test_is_valid_iso_timestamp_true(self, validator):
        """Test ISO timestamp validation - valid cases."""
        assert validator._is_valid_iso_timestamp("2026-02-02T11:30:00Z") is True
        assert validator._is_valid_iso_timestamp("2025-01-01T00:00:00") is True
        assert validator._is_valid_iso_timestamp("2024-12-25T23:59:59Z") is True

    def test_is_valid_iso_timestamp_false(self, validator):
        """Test ISO timestamp validation - invalid cases."""
        assert validator._is_valid_iso_timestamp("not-a-timestamp") is False
        assert validator._is_valid_iso_timestamp("") is False
        assert validator._is_valid_iso_timestamp(None) is False
        assert validator._is_valid_iso_timestamp(12345) is False

    def test_validate_type(self, validator):
        """Test type validation."""
        assert validator.validate_type("string", str) is True
        assert validator.validate_type(123, int) is True
        assert validator.validate_type({"key": "val"}, dict) is True
        assert validator.validate_type("not_int", int) is False

    def test_validate_collection_all_valid(self, validator):
        """Test collection validation - all valid."""
        items = [
            {"type": "state", "value": "data1", "timestamp": "2026-02-02T00:00:00"},
            {"type": "action", "value": "data2", "timestamp": "2026-02-02T01:00:00"},
        ]

        report = validator.validate_collection(items)
        assert report["total"] == 2
        assert report["valid"] == 2
        assert report["invalid"] == 0
        assert report["valid_percentage"] == 100.0

    def test_validate_collection_mixed(self, validator):
        """Test collection validation - mixed valid/invalid."""
        items = [
            {"type": "state", "value": "data1", "timestamp": "2026-02-02T00:00:00"},
            "not_a_dict",
            {"type": "action", "value": "data2", "timestamp": "2026-02-02T01:00:00"},
        ]

        report = validator.validate_collection(items)
        assert report["total"] == 3
        assert report["valid"] == 2
        assert report["invalid"] == 1
        assert report["valid_percentage"] == pytest.approx(66.67, abs=0.1)

    def test_validate_collection_empty(self, validator):
        """Test collection validation - empty collection."""
        report = validator.validate_collection([])
        assert report["total"] == 0
        assert report["valid"] == 0
        assert report["invalid"] == 0
        assert report["valid_percentage"] == 0

    @pytest.mark.asyncio
    async def test_validation_log(self, validator):
        """Test validation logging."""
        data1 = {
            "type": "state",
            "value": "test",
            "timestamp": "2026-02-02T00:00:00",
        }
        data2 = {"type": "invalid"}  # Missing fields

        await validator.validate(data1)
        await validator.validate(data2)

        log = validator.get_validation_log()
        assert len(log) == 2
        assert log[0]["valid"] is True
        assert log[1]["valid"] is False

    def test_protocol_compliant_valid_types(self, validator):
        """Test protocol compliance with valid consciousness types."""
        valid_types = ["state", "action", "observation", "memory", "consciousness"]

        for ctype in valid_types:
            data = {
                "type": ctype,
                "value": "test",
                "timestamp": "2026-02-02T00:00:00Z",
            }
            assert validator._is_protocol_compliant(data) is True

    def test_protocol_compliant_invalid_types(self, validator):
        """Test protocol compliance with invalid consciousness types."""
        data = {
            "type": "invalid_type",
            "value": "test",
            "timestamp": "2026-02-02T00:00:00Z",
        }
        assert validator._is_protocol_compliant(data) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
