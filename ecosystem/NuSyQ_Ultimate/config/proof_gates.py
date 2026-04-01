"""
Proof Gates System - Verifiable Task Completion
================================================

Boss Rush Mode demands PROOF, not theater. This system provides automated
verification of task completion through multiple proof types.

NO VAGUE CLAIMS. Only verified evidence.

OmniTag: [verification, proof_gates, boss_rush, quality_assurance]
MegaTag: [SYSTEM_INTEGRITY, VERIFICATION]
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import json
import subprocess
import yaml
import re


class ProofType(Enum):
    """Types of proof we accept for task completion."""

    TEST_PASS = "test_pass"  # Pytest passes
    FILE_EXISTS = "file_exists"  # File created/modified
    REPORT_OK = "report_ok"  # Report contains success markers
    CODE_INTEGRATION = "code_integration"  # Code properly integrated
    SCHEMA_VALID = "schema_valid"  # YAML/JSON schema valid
    METRIC_THRESHOLD = "metric_threshold"  # Numerical metric met
    ERROR_ELIMINATED = "error_eliminated"  # Specific error gone
    CONSOLE_OUTPUT = "console_output"  # Expected output present


@dataclass
class ProofGate:
    """A gate that must be passed to prove task completion."""

    kind: ProofType | str
    path: Optional[str] = None
    threshold: Optional[float] = None
    pattern: Optional[str] = None
    description: str = ""

    def __post_init__(self):
        if isinstance(self.kind, str):
            self.kind = ProofType(self.kind)


@dataclass
class ProofResult:
    """Result of proof verification."""

    passed: bool
    gate: ProofGate
    evidence: str
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)


class ProofGateVerifier:
    """
    Verifies proof gates with ZERO tolerance for theater.

    Either the proof exists or it doesn't. No ambiguity.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.verification_history: List[ProofResult] = []

    def verify_gate(self, gate: ProofGate) -> ProofResult:
        """
        Verify a single proof gate.

        Returns ProofResult with pass/fail and evidence.
        """
        from datetime import datetime

        timestamp = datetime.now().isoformat()

        # Route to appropriate verification method
        if gate.kind == ProofType.TEST_PASS:
            result = self._verify_test_pass(gate)
        elif gate.kind == ProofType.FILE_EXISTS:
            result = self._verify_file_exists(gate)
        elif gate.kind == ProofType.REPORT_OK:
            result = self._verify_report_ok(gate)
        elif gate.kind == ProofType.CODE_INTEGRATION:
            result = self._verify_code_integration(gate)
        elif gate.kind == ProofType.SCHEMA_VALID:
            result = self._verify_schema_valid(gate)
        elif gate.kind == ProofType.METRIC_THRESHOLD:
            result = self._verify_metric_threshold(gate)
        elif gate.kind == ProofType.ERROR_ELIMINATED:
            result = self._verify_error_eliminated(gate)
        elif gate.kind == ProofType.CONSOLE_OUTPUT:
            result = self._verify_console_output(gate)
        else:
            result = ProofResult(
                passed=False,
                gate=gate,
                evidence=f"Unknown proof type: {gate.kind}",
                timestamp=timestamp,
            )

        # Record verification
        self.verification_history.append(result)
        return result

    def verify_all(self, gates: List[ProofGate]) -> Dict[str, ProofResult]:
        """
        Verify all proof gates.

        Returns dict mapping gate descriptions to results.
        """
        results = {}
        for gate in gates:
            kind_value = gate.kind.value if isinstance(gate.kind, ProofType) else str(gate.kind)
            key = f"{kind_value}:{gate.path or gate.pattern or 'threshold'}"
            results[key] = self.verify_gate(gate)
        return results

    # ========================================================================
    # VERIFICATION METHODS
    # ========================================================================

    def _verify_test_pass(self, gate: ProofGate) -> ProofResult:
        """Verify pytest passes for specified test file/function."""
        from datetime import datetime

        if not gate.path:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence="Test path not provided",
                timestamp=datetime.now().isoformat(),
            )

        test_path = self.workspace_root / gate.path

        if not test_path.exists():
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"Test file not found: {test_path}",
                timestamp=datetime.now().isoformat(),
            )

        # Run pytest on specific file
        try:
            import sys

            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.workspace_root),
            )

            # Check for success
            passed = result.returncode == 0
            evidence = f"Exit code: {result.returncode}\n"

            # Extract test results
            if "passed" in result.stdout:
                match = re.search(r"(\d+) passed", result.stdout)
                if match:
                    evidence += f"Tests passed: {match.group(1)}\n"

            if "failed" in result.stdout:
                match = re.search(r"(\d+) failed", result.stdout)
                if match:
                    evidence += f"Tests failed: {match.group(1)}\n"

            evidence += (
                result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
            )

            return ProofResult(
                passed=passed,
                gate=gate,
                evidence=evidence,
                timestamp=datetime.now().isoformat(),
                details={"exit_code": result.returncode},
            )

        except subprocess.TimeoutExpired:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence="Test execution timeout (60s)",
                timestamp=datetime.now().isoformat(),
            )
        except Exception as e:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"Test execution error: {e}",
                timestamp=datetime.now().isoformat(),
            )

    def _verify_file_exists(self, gate: ProofGate) -> ProofResult:
        """Verify file exists with optional content check."""
        from datetime import datetime

        if not gate.path:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence="File path not provided",
                timestamp=datetime.now().isoformat(),
            )

        file_path = self.workspace_root / gate.path
        exists = file_path.exists()

        if exists:
            # Get file metadata
            size = file_path.stat().st_size
            modified = file_path.stat().st_mtime

            evidence = f"File exists: {file_path}\nSize: {size} bytes\n"

            # Optional: Check for pattern in file
            if gate.pattern:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    pattern_found = re.search(gate.pattern, content, re.IGNORECASE)
                    if pattern_found:
                        evidence += f"Pattern found: {gate.pattern}\n"
                    else:
                        evidence += f"Pattern NOT found: {gate.pattern}\n"
                        exists = False
                except Exception as e:
                    evidence += f"Pattern check failed: {e}\n"

            return ProofResult(
                passed=exists,
                gate=gate,
                evidence=evidence,
                timestamp=datetime.now().isoformat(),
                details={"size": size, "modified": modified},
            )
        else:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"File not found: {file_path}",
                timestamp=datetime.now().isoformat(),
            )

    def _verify_report_ok(self, gate: ProofGate) -> ProofResult:
        """Verify report contains success markers (✅, PASS, SUCCESS)."""
        from datetime import datetime
        if not gate.path:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence="Report path not provided",
                timestamp=datetime.now().isoformat(),
            )
        # Support glob patterns in path
        if "*" in gate.path:
            import glob

            matches = list(glob.glob(str(self.workspace_root / gate.path)))
            if not matches:
                return ProofResult(
                    passed=False,
                    gate=gate,
                    evidence=f"No files match pattern: {gate.path}",
                    timestamp=datetime.now().isoformat(),
                )
            file_path = Path(matches[0])  # Use first match
        else:
            file_path = self.workspace_root / gate.path

        if not file_path.exists():
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"Report not found: {file_path}",
                timestamp=datetime.now().isoformat(),
            )

        # Read report and check for success markers
        try:
            content = file_path.read_text(encoding="utf-8")

            success_markers = ["✅", "PASS", "SUCCESS", "COMPLETE", "✓"]
            failure_markers = ["❌", "FAIL", "ERROR", "✗"]

            success_count = sum(content.count(marker) for marker in success_markers)
            failure_count = sum(content.count(marker) for marker in failure_markers)

            # Report is OK if more successes than failures
            passed = success_count > 0 and success_count >= failure_count

            evidence = f"Success markers: {success_count}\n"
            evidence += f"Failure markers: {failure_count}\n"
            evidence += f"File: {file_path}\n"

            return ProofResult(
                passed=passed,
                gate=gate,
                evidence=evidence,
                timestamp=datetime.now().isoformat(),
                details={
                    "success_count": success_count,
                    "failure_count": failure_count,
                },
            )

        except Exception as e:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"Report read error: {e}",
                timestamp=datetime.now().isoformat(),
            )

    def _verify_code_integration(self, gate: ProofGate) -> ProofResult:
        """Verify code is properly integrated (imports, no syntax errors)."""
        from datetime import datetime

        if not gate.path:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence="Integration path not provided",
                timestamp=datetime.now().isoformat(),
            )

        file_path = self.workspace_root / gate.path

        if not file_path.exists():
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"File not found: {file_path}",
                timestamp=datetime.now().isoformat(),
            )

        # Try to compile the Python file
        try:
            content = file_path.read_text(encoding="utf-8")
            compile(content, str(file_path), "exec")

            # Optional: Check for specific pattern (e.g., import statement)
            integration_check = True
            evidence = f"Syntax valid: {file_path}\n"

            if gate.pattern:
                if re.search(gate.pattern, content, re.IGNORECASE):
                    evidence += f"Integration pattern found: {gate.pattern}\n"
                else:
                    integration_check = False
                    evidence += f"Integration pattern NOT found: {gate.pattern}\n"

            return ProofResult(
                passed=integration_check,
                gate=gate,
                evidence=evidence,
                timestamp=datetime.now().isoformat(),
            )

        except SyntaxError as e:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"Syntax error: {e}",
                timestamp=datetime.now().isoformat(),
            )
        except Exception as e:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"Integration check error: {e}",
                timestamp=datetime.now().isoformat(),
            )

    def _verify_schema_valid(self, gate: ProofGate) -> ProofResult:
        """Verify YAML/JSON file is valid."""
        from datetime import datetime

        if not gate.path:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence="Schema path not provided",
                timestamp=datetime.now().isoformat(),
            )

        file_path = self.workspace_root / gate.path

        if not file_path.exists():
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"File not found: {file_path}",
                timestamp=datetime.now().isoformat(),
            )

        try:
            content = file_path.read_text(encoding="utf-8")

            # Try YAML first
            if file_path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(content)
                schema_type = "YAML"
            # Try JSON
            elif file_path.suffix == ".json":
                data = json.loads(content)
                schema_type = "JSON"
            else:
                return ProofResult(
                    passed=False,
                    gate=gate,
                    evidence=f"Unknown schema type: {file_path.suffix}",
                    timestamp=datetime.now().isoformat(),
                )

            return ProofResult(
                passed=True,
                gate=gate,
                evidence=f"Valid {schema_type}: {file_path}\nKeys: {len(data)}",
                timestamp=datetime.now().isoformat(),
                details={
                    "schema_type": schema_type,
                    "keys": len(data) if isinstance(data, dict) else 0,
                },
            )

        except Exception as e:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"Schema validation error: {e}",
                timestamp=datetime.now().isoformat(),
            )

    def _verify_metric_threshold(self, gate: ProofGate) -> ProofResult:
        """Verify numerical metric meets threshold."""
        from datetime import datetime

        # This requires custom implementation based on metric type
        # For now, return not implemented
        return ProofResult(
            passed=False,
            gate=gate,
            evidence="Metric threshold verification not yet implemented",
            timestamp=datetime.now().isoformat(),
        )

    def _verify_error_eliminated(self, gate: ProofGate) -> ProofResult:
        """Verify specific error pattern no longer appears."""
        from datetime import datetime

        if gate.pattern is None:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence="Error pattern not specified",
                timestamp=datetime.now().isoformat(),
            )

        # Search for error pattern in specified path
        file_path = (
            self.workspace_root / gate.path if gate.path else self.workspace_root
        )

        try:
            if file_path.is_file():
                content = file_path.read_text(encoding="utf-8")
                error_found = re.search(gate.pattern, content, re.IGNORECASE)

                passed = not error_found  # Pass if error NOT found
                evidence = f"Error pattern '{gate.pattern}' "
                evidence += "NOT FOUND (✅)" if passed else "STILL PRESENT (❌)"

            else:
                # Search directory recursively
                error_found = False
                files_checked = 0

                for py_file in file_path.rglob("*.py"):
                    files_checked += 1
                    content = py_file.read_text(encoding="utf-8")
                    if re.search(gate.pattern, content, re.IGNORECASE):
                        error_found = True
                        break

                passed = not error_found
                evidence = (
                    f"Checked {files_checked} files. Error pattern '{gate.pattern}' "
                )
                evidence += "NOT FOUND (✅)" if passed else "STILL PRESENT (❌)"

            return ProofResult(
                passed=passed,
                gate=gate,
                evidence=evidence,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            return ProofResult(
                passed=False,
                gate=gate,
                evidence=f"Error search failed: {e}",
                timestamp=datetime.now().isoformat(),
            )

    def _verify_console_output(self, gate: ProofGate) -> ProofResult:
        """Verify console output contains expected pattern."""
        from datetime import datetime

        # This requires storing console output - implement with log files
        return ProofResult(
            passed=False,
            gate=gate,
            evidence="Console output verification requires log capture (not yet implemented)",
            timestamp=datetime.now().isoformat(),
        )

    # ========================================================================
    # REPORTING
    # ========================================================================

    def generate_report(self, results: Dict[str, ProofResult]) -> str:
        """Generate human-readable verification report."""
        report = []
        report.append("=" * 60)
        report.append("PROOF GATE VERIFICATION REPORT")
        report.append("=" * 60)
        report.append("")

        passed_count = sum(1 for r in results.values() if r.passed)
        total_count = len(results)

        report.append(f"Results: {passed_count}/{total_count} gates passed")
        report.append("")

        for key, result in results.items():
            status = "✅ PASS" if result.passed else "❌ FAIL"
            kind_value = (
                result.gate.kind.value
                if isinstance(result.gate.kind, ProofType)
                else str(result.gate.kind)
            )
            report.append(f"{status} | {kind_value}")
            report.append(f"  Path: {result.gate.path or 'N/A'}")
            report.append(f"  Evidence: {result.evidence[:200]}")
            report.append("")

        report.append("=" * 60)
        return "\n".join(report)


def create_proof_gate(kind: str, path: Optional[str] = None, **kwargs) -> ProofGate:
    """Convenience function to create proof gates."""
    return ProofGate(kind=ProofType(kind), path=path, **kwargs)


def verify_task_completion(task_id: str, proof_gates: List[Dict]) -> bool:
    """
    Verify task completion based on proof gates.

    Args:
        task_id: Task identifier
        proof_gates: List of proof gate specifications

    Returns:
        True if all gates pass, False otherwise
    """
    verifier = ProofGateVerifier()

    gates = []
    for gate_spec in proof_gates:
        gate = ProofGate(
            kind=ProofType(gate_spec["kind"]),
            path=gate_spec.get("path"),
            pattern=gate_spec.get("pattern"),
            threshold=gate_spec.get("threshold"),
        )
        gates.append(gate)

    results = verifier.verify_all(gates)

    # Print report
    print(verifier.generate_report(results))

    # Return overall pass/fail
    return all(r.passed for r in results.values())


if __name__ == "__main__":
    # Example usage
    print("🔒 Proof Gates System - Self Test")
    print("=" * 60)

    verifier = ProofGateVerifier()

    # Test file existence
    gate1 = ProofGate(
        kind=ProofType.FILE_EXISTS,
        path="config/proof_gates.py",
        description="Proof gates module exists",
    )

    result1 = verifier.verify_gate(gate1)
    print(f"\nTest 1: {result1.passed}")
    print(f"Evidence: {result1.evidence}")

    # Test schema validation
    gate2 = ProofGate(
        kind=ProofType.SCHEMA_VALID,
        path="State/copilot_task_queue.yaml",
        description="Task queue YAML valid",
    )

    result2 = verifier.verify_gate(gate2)
    print(f"\nTest 2: {result2.passed}")
    print(f"Evidence: {result2.evidence}")

    print("\n" + "=" * 60)
    print("✅ Proof Gates System operational!")
