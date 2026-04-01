"""
Tests for Proof Gates System

Verifies that proof gate verification works correctly.
"""
# pylint: disable=redefined-outer-name

import pytest

from config.proof_gates import (
    ProofGate,
    ProofGateVerifier,
    ProofType,
    create_proof_gate,
)


@pytest.fixture
def workspace_root(tmp_path):
    """Create temporary workspace for testing."""
    return tmp_path


@pytest.fixture
def verifier(workspace_root):
    """Create proof gate verifier."""
    return ProofGateVerifier(workspace_root)


class TestProofGateCreation:
    """Test proof gate creation."""

    def test_create_proof_gate(self):
        """Test proof gate creation."""
        gate = create_proof_gate("file_exists", path="test.py", description="Test file")
        assert gate.kind == ProofType.FILE_EXISTS
        assert gate.path == "test.py"
        assert gate.description == "Test file"

    def test_proof_gate_enum_conversion(self):
        """Test string to enum conversion."""
        gate = ProofGate(kind="test_pass", path="test.py")
        assert gate.kind == ProofType.TEST_PASS


class TestFileExistsVerification:
    """Test file existence verification."""

    def test_file_exists_pass(self, verifier, workspace_root):
        """Test file exists verification passes."""
        # Create test file
        test_file = workspace_root / "test.py"
        test_file.write_text("# Test file")

        gate = ProofGate(kind=ProofType.FILE_EXISTS, path="test.py")

        result = verifier.verify_gate(gate)
        assert result.passed is True
        assert "File exists" in result.evidence

    def test_file_exists_fail(self, verifier):
        """Test file exists verification fails."""
        gate = ProofGate(kind=ProofType.FILE_EXISTS, path="nonexistent.py")

        result = verifier.verify_gate(gate)
        assert result.passed is False
        assert "not found" in result.evidence

    def test_file_exists_with_pattern(self, verifier, workspace_root):
        """Test file exists with pattern verification."""
        test_file = workspace_root / "test.py"
        test_file.write_text('def hello():\n    return "world"')

        gate = ProofGate(kind=ProofType.FILE_EXISTS, path="test.py", pattern=r"def\s+hello")

        result = verifier.verify_gate(gate)
        assert result.passed is True
        assert "Pattern found" in result.evidence


class TestSchemaValidation:
    """Test schema validation."""

    def test_yaml_valid(self, verifier, workspace_root):
        """Test YAML schema validation passes."""
        yaml_file = workspace_root / "test.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2")

        gate = ProofGate(kind=ProofType.SCHEMA_VALID, path="test.yaml")

        result = verifier.verify_gate(gate)
        assert result.passed is True
        assert "Valid YAML" in result.evidence

    def test_json_valid(self, verifier, workspace_root):
        """Test JSON schema validation passes."""
        json_file = workspace_root / "test.json"
        json_file.write_text('{"key": "value", "list": [1, 2, 3]}')

        gate = ProofGate(kind=ProofType.SCHEMA_VALID, path="test.json")

        result = verifier.verify_gate(gate)
        assert result.passed is True
        assert "Valid JSON" in result.evidence

    def test_yaml_invalid(self, verifier, workspace_root):
        """Test YAML schema validation fails."""
        yaml_file = workspace_root / "test.yaml"
        yaml_file.write_text("key: value\n  invalid: indentation")

        gate = ProofGate(kind=ProofType.SCHEMA_VALID, path="test.yaml")

        result = verifier.verify_gate(gate)
        assert result.passed is False
        assert "validation error" in result.evidence


class TestCodeIntegration:
    """Test code integration verification."""

    def test_code_integration_valid(self, verifier, workspace_root):
        """Test code integration passes for valid Python."""
        py_file = workspace_root / "test.py"
        py_file.write_text("import sys\n\ndef main():\n    pass")

        gate = ProofGate(kind=ProofType.CODE_INTEGRATION, path="test.py")

        result = verifier.verify_gate(gate)
        assert result.passed is True
        assert "Syntax valid" in result.evidence

    def test_code_integration_syntax_error(self, verifier, workspace_root):
        """Test code integration fails for syntax errors."""
        py_file = workspace_root / "test.py"
        py_file.write_text("def broken(\n    pass")  # Missing closing paren

        gate = ProofGate(kind=ProofType.CODE_INTEGRATION, path="test.py")

        result = verifier.verify_gate(gate)
        assert result.passed is False
        assert "Syntax error" in result.evidence

    def test_code_integration_with_pattern(self, verifier, workspace_root):
        """Test code integration with import pattern."""
        py_file = workspace_root / "test.py"
        py_file.write_text("from config import proof_gates\n\ndef main():\n    pass")

        gate = ProofGate(
            kind=ProofType.CODE_INTEGRATION,
            path="test.py",
            pattern=r"from\s+config\s+import",
        )

        result = verifier.verify_gate(gate)
        assert result.passed is True
        assert "Integration pattern found" in result.evidence


class TestReportValidation:
    """Test report validation."""

    def test_report_ok_success(self, verifier, workspace_root):
        """Test report validation passes."""
        report_file = workspace_root / "report.md"
        report_file.write_text(
            "# Test Report\n✅ All tests passed\n✅ No errors found\n", encoding="utf-8"
        )

        gate = ProofGate(kind=ProofType.REPORT_OK, path="report.md")

        result = verifier.verify_gate(gate)
        assert result.passed is True
        assert "Success markers: 2" in result.evidence

    def test_report_ok_failure(self, verifier, workspace_root):
        """Test report validation fails."""
        report_file = workspace_root / "report.md"
        report_file.write_text(
            "# Test Report\n❌ Tests failed\n❌ Multiple errors\n", encoding="utf-8"
        )

        gate = ProofGate(kind=ProofType.REPORT_OK, path="report.md")

        result = verifier.verify_gate(gate)
        assert result.passed is False
        assert "Failure markers: 2" in result.evidence


class TestErrorElimination:
    """Test error elimination verification."""

    def test_error_eliminated(self, verifier, workspace_root):
        """Test error pattern no longer present."""
        py_file = workspace_root / "test.py"
        py_file.write_text('def clean_code():\n    return "fixed"')

        gate = ProofGate(kind=ProofType.ERROR_ELIMINATED, path="test.py", pattern=r"TODO|FIXME|XXX")

        result = verifier.verify_gate(gate)
        assert result.passed is True
        assert "NOT FOUND" in result.evidence

    def test_error_still_present(self, verifier, workspace_root):
        """Test error pattern still present."""
        py_file = workspace_root / "test.py"
        py_file.write_text("def broken():\n    # TODO: Fix this")

        gate = ProofGate(kind=ProofType.ERROR_ELIMINATED, path="test.py", pattern=r"TODO|FIXME|XXX")

        result = verifier.verify_gate(gate)
        assert result.passed is False
        assert "STILL PRESENT" in result.evidence


class TestVerifyAll:
    """Test batch verification."""

    def test_verify_all_pass(self, verifier, workspace_root):
        """Test all gates pass."""
        # Create test files
        (workspace_root / "test1.py").write_text("# Test 1")
        (workspace_root / "test2.yaml").write_text("key: value")

        gates = [
            ProofGate(kind=ProofType.FILE_EXISTS, path="test1.py"),
            ProofGate(kind=ProofType.SCHEMA_VALID, path="test2.yaml"),
        ]

        results = verifier.verify_all(gates)
        assert all(r.passed for r in results.values())

    def test_verify_all_mixed(self, verifier, workspace_root):
        """Test mixed pass/fail."""
        (workspace_root / "test1.py").write_text("# Test 1")

        gates = [
            ProofGate(kind=ProofType.FILE_EXISTS, path="test1.py"),
            ProofGate(kind=ProofType.FILE_EXISTS, path="missing.py"),
        ]

        results = verifier.verify_all(gates)
        passed = [r.passed for r in results.values()]
        assert True in passed
        assert False in passed


class TestReportGeneration:
    """Test report generation."""

    def test_generate_report(self, verifier, workspace_root):
        """Test report generation."""
        (workspace_root / "test.py").write_text("# Test")

        gates = [
            ProofGate(kind=ProofType.FILE_EXISTS, path="test.py"),
            ProofGate(kind=ProofType.FILE_EXISTS, path="missing.py"),
        ]

        results = verifier.verify_all(gates)
        report = verifier.generate_report(results)

        assert "PROOF GATE VERIFICATION REPORT" in report
        assert "✅ PASS" in report
        assert "❌ FAIL" in report
        assert "1/2 gates passed" in report


class TestTaskCompletion:
    """Test complete task verification."""

    def test_verify_task_completion(self, workspace_root):
        """Test task completion verification."""
        # Create test files in workspace
        (workspace_root / "feature.py").write_text("def new_feature():\n    pass")
        (workspace_root / "config.yaml").write_text("enabled: true")

        # Create verifier with test workspace
        verifier = ProofGateVerifier(workspace_root)

        # Define proof gates
        gates = [
            {"kind": "file_exists", "path": "feature.py"},
            {"kind": "schema_valid", "path": "config.yaml"},
            {
                "kind": "code_integration",
                "path": "feature.py",
                "pattern": r"def\s+new_feature",
            },
        ]

        # Manually verify using verifier instance
        proof_gates = []
        for gate_spec in gates:
            gate = ProofGate(
                kind=ProofType(gate_spec["kind"]),
                path=gate_spec.get("path"),
                pattern=gate_spec.get("pattern"),
            )
            proof_gates.append(gate)

        results = verifier.verify_all(proof_gates)

        # Should all pass
        assert all(r.passed for r in results.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
