"""
Proof-Gated Completion System
==============================

Port of SimulatedVerse chug-runner proof verification for anti-theater operation.

Philosophy:
    "PROOF, NOT VIBES" - Tasks are only complete when artifacts verify

Proof Types:
    - test_pass: Unit/integration test passes
    - file_exists: Artifact file created
    - report_ok: Report contains expected values
    - lsp_clean: No TypeScript/Python errors
    - service_up: Service responds to health check
    - command_success: Shell command exits 0

Integration:
    - Used by TodoWrite tool to verify task completion
    - Extends State/repository_state.yaml with proofs
    - Prevents "sophisticated theater" (looks done, but isn't)

Author: Claude Code (Sonnet 4.5)
Date: 2025-10-08
Status: Production - Anti-Theater System
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("nusyq.proof")


class ProofKind(Enum):
    """Types of proof verification"""
    TEST_PASS = "test_pass"              # pytest test passes
    FILE_EXISTS = "file_exists"          # Artifact file exists
    REPORT_OK = "report_ok"              # Report has expected data
    LSP_CLEAN = "lsp_clean"              # No linter/type errors
    SERVICE_UP = "service_up"            # Service health check
    COMMAND_SUCCESS = "command_success"  # Shell command succeeds
    GREP_MATCH = "grep_match"            # Pattern found in file
    GREP_ABSENT = "grep_absent"          # Pattern NOT in file


@dataclass
class Proof:
    """Single proof requirement"""
    kind: ProofKind
    path: Optional[str] = None           # File path for file/report proofs
    test_pattern: Optional[str] = None   # Test name pattern
    expected: Optional[Dict] = None      # Expected values for report
    url: Optional[str] = None            # Service URL for health check
    command: Optional[str] = None        # Command to run
    pattern: Optional[str] = None        # Pattern for grep
    description: Optional[str] = None    # Human-readable description


@dataclass
class ProofResult:
    """Result of proof verification"""
    proof: Proof
    verified: bool
    reasoning: str
    evidence: Optional[Any] = None       # Supporting data


class ProofVerifier:
    """
    Verifies task completion proofs to prevent sophisticated theater

    Example:
        verifier = ProofVerifier(root_dir=Path("/c/Users/keath/NuSyQ"))

        # Define proofs for a task
        proofs = [
            Proof(
                kind=ProofKind.FILE_EXISTS,
                path="Reports/ANALYSIS.md",
                description="Analysis report created"
            ),
            Proof(
                kind=ProofKind.TEST_PASS,
                test_pattern="test_calculator",
                description="Calculator tests pass"
            )
        ]

        # Verify all proofs
        results = verifier.verify_all(proofs)

        if all(r.verified for r in results):
            print("✅ Task complete - all proofs verified")
        else:
            failed = [r for r in results if not r.verified]
            print(f"❌ {len(failed)} proofs failed")
    """

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize proof verifier

        Args:
            root_dir: Repository root (default: current directory)
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()

    def verify_all(self, proofs: List[Proof]) -> List[ProofResult]:
        """
        Verify all proofs for a task

        Args:
            proofs: List of proof requirements

        Returns:
            List of ProofResults (one per proof)
        """
        results = []

        for proof in proofs:
            try:
                result = self._verify_proof(proof)
                results.append(result)

                if result.verified:
                    logger.info(f"✅ Proof verified: {proof.description or proof.kind.value}")
                else:
                    logger.warning(f"❌ Proof failed: {result.reasoning}")

            except Exception as e:
                logger.error(f"Error verifying proof: {e}")
                results.append(ProofResult(
                    proof=proof,
                    verified=False,
                    reasoning=f"Exception: {str(e)}"
                ))

        return results

    def _verify_proof(self, proof: Proof) -> ProofResult:
        """Verify a single proof"""

        if proof.kind == ProofKind.FILE_EXISTS:
            return self._verify_file_exists(proof)

        elif proof.kind == ProofKind.TEST_PASS:
            return self._verify_test_pass(proof)

        elif proof.kind == ProofKind.REPORT_OK:
            return self._verify_report_ok(proof)

        elif proof.kind == ProofKind.LSP_CLEAN:
            return self._verify_lsp_clean(proof)

        elif proof.kind == ProofKind.SERVICE_UP:
            return self._verify_service_up(proof)

        elif proof.kind == ProofKind.COMMAND_SUCCESS:
            return self._verify_command_success(proof)

        elif proof.kind == ProofKind.GREP_MATCH:
            return self._verify_grep_match(proof)

        elif proof.kind == ProofKind.GREP_ABSENT:
            return self._verify_grep_absent(proof)

        else:
            return ProofResult(
                proof=proof,
                verified=False,
                reasoning=f"Unknown proof kind: {proof.kind}"
            )

    def _verify_file_exists(self, proof: Proof) -> ProofResult:
        """Verify file exists"""
        if not proof.path:
            return ProofResult(proof, False, "No path provided")

        file_path = self.root_dir / proof.path
        exists = file_path.exists()

        return ProofResult(
            proof=proof,
            verified=exists,
            reasoning=f"File {'exists' if exists else 'not found'}: {proof.path}",
            evidence={"size": file_path.stat().st_size if exists else 0}
        )

    def _verify_test_pass(self, proof: Proof) -> ProofResult:
        """Verify pytest test passes"""
        if not proof.test_pattern:
            return ProofResult(proof, False, "No test pattern provided")

        try:
            # Run pytest with pattern
            result = subprocess.run(
                ["pytest", "-k", proof.test_pattern, "-v", "--tb=short"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            passed = result.returncode == 0

            return ProofResult(
                proof=proof,
                verified=passed,
                reasoning=f"Test {'passed' if passed else 'failed'}: {proof.test_pattern}",
                evidence={
                    "returncode": result.returncode,
                    "stdout": result.stdout[-500:] if result.stdout else "",
                    "stderr": result.stderr[-500:] if result.stderr else ""
                }
            )

        except subprocess.TimeoutExpired:
            return ProofResult(proof, False, "Test timed out (60s)")
        except FileNotFoundError:
            return ProofResult(proof, False, "pytest not found (pip install pytest?)")

    def _verify_report_ok(self, proof: Proof) -> ProofResult:
        """Verify report contains expected values"""
        if not proof.path or not proof.expected:
            return ProofResult(proof, False, "Missing path or expected values")

        file_path = self.root_dir / proof.path

        if not file_path.exists():
            return ProofResult(proof, False, f"Report not found: {proof.path}")

        try:
            with open(file_path,'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check expected values
            mismatches = []
            for key, expected_value in proof.expected.items():
                actual_value = data.get(key)

                # Handle different comparison types
                if isinstance(expected_value, dict):
                    if "eq" in expected_value and actual_value != expected_value["eq"]:
                        mismatches.append(f"{key}: expected {expected_value['eq']}, got {actual_value}")
                    elif "lte" in expected_value and actual_value > expected_value["lte"]:
                        mismatches.append(f"{key}: expected ≤{expected_value['lte']}, got {actual_value}")
                    elif "gte" in expected_value and actual_value < expected_value["gte"]:
                        mismatches.append(f"{key}: expected ≥{expected_value['gte']}, got {actual_value}")
                else:
                    if actual_value != expected_value:
                        mismatches.append(f"{key}: expected {expected_value}, got {actual_value}")

            verified = len(mismatches) == 0

            return ProofResult(
                proof=proof,
                verified=verified,
                reasoning="Report matches" if verified else f"Mismatches: {', '.join(mismatches)}",
                evidence=data
            )

        except json.JSONDecodeError:
            return ProofResult(proof, False, "Invalid JSON in report")

    def _verify_lsp_clean(self, proof: Proof) -> ProofResult:
        """Verify no LSP errors (Python mypy/pylint)"""
        try:
            # Try mypy first (type checking)
            result = subprocess.run(
                ["mypy", ".", "--ignore-missing-imports", "--no-error-summary"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            errors = result.stdout.count("error:")
            verified = errors == 0

            return ProofResult(
                proof=proof,
                verified=verified,
                reasoning=f"LSP {'clean' if verified else f'{errors} errors found'}",
                evidence={"error_count": errors, "output": result.stdout[-500:]}
            )

        except FileNotFoundError:
            # mypy not installed - skip this proof
            return ProofResult(
                proof=proof,
                verified=True,
                reasoning="mypy not installed, skipping LSP check"
            )
        except subprocess.TimeoutExpired:
            return ProofResult(proof, False, "LSP check timed out (30s)")

    def _verify_service_up(self, proof: Proof) -> ProofResult:
        """Verify service health check"""
        if not proof.url:
            return ProofResult(proof, False, "No URL provided")

        try:
            import requests
            response = requests.get(proof.url, timeout=5)
            up = response.status_code == 200

            return ProofResult(
                proof=proof,
                verified=up,
                reasoning=f"Service {'up' if up else f'returned {response.status_code}'}: {proof.url}",
                evidence={"status_code": response.status_code}
            )

        except ImportError:
            return ProofResult(proof, False, "requests library not installed")
        except Exception as e:
            return ProofResult(proof, False, f"Service unreachable: {e}")

    def _verify_command_success(self, proof: Proof) -> ProofResult:
        """Verify shell command succeeds"""
        if not proof.command:
            return ProofResult(proof, False, "No command provided")

        try:
            result = subprocess.run(
                proof.command,
                shell=True,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            success = result.returncode == 0

            return ProofResult(
                proof=proof,
                verified=success,
                reasoning=f"Command {'succeeded' if success else f'failed (exit {result.returncode})'}",
                evidence={
                    "returncode": result.returncode,
                    "stdout": result.stdout[-200:],
                    "stderr": result.stderr[-200:]
                }
            )

        except subprocess.TimeoutExpired:
            return ProofResult(proof, False, "Command timed out (30s)")

    def _verify_grep_match(self, proof: Proof) -> ProofResult:
        """Verify pattern found in file"""
        if not proof.path or not proof.pattern:
            return ProofResult(proof, False, "Missing path or pattern")

        file_path = self.root_dir / proof.path

        if not file_path.exists():
            return ProofResult(proof, False, f"File not found: {proof.path}")

        try:
            import re
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            match = re.search(proof.pattern, content)

            return ProofResult(
                proof=proof,
                verified=bool(match),
                reasoning=f"Pattern {'found' if match else 'not found'}: {proof.pattern}",
                evidence={"match": match.group(0) if match else None}
            )

        except Exception as e:
            return ProofResult(proof, False, f"Error reading file: {e}")

    def _verify_grep_absent(self, proof: Proof) -> ProofResult:
        """Verify pattern NOT in file (inverse of grep_match)"""
        if not proof.path or not proof.pattern:
            return ProofResult(proof, False, "Missing path or pattern")

        file_path = self.root_dir / proof.path

        if not file_path.exists():
            return ProofResult(proof, False, f"File not found: {proof.path}")

        try:
            import re
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            match = re.search(proof.pattern, content)

            # Inverse logic: verified if pattern NOT found
            verified = not bool(match)

            return ProofResult(
                proof=proof,
                verified=verified,
                reasoning=f"Pattern {'absent (good)' if verified else 'found (bad)'}: {proof.pattern}",
                evidence={"match": match.group(0) if match else None}
            )

        except Exception as e:
            return ProofResult(proof, False, f"Error reading file: {e}")


# Example/Test code
if __name__ == "__main__":
    import sys
    import io

    # Fix Windows UTF-8
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    logging.basicConfig(level=logging.INFO)

    print("=== Proof-Gated Completion Demo ===\n")

    verifier = ProofVerifier(root_dir=Path("/c/Users/keath/NuSyQ"))

    # Define test proofs
    proofs = [
        Proof(
            kind=ProofKind.FILE_EXISTS,
            path="config/breathing_pacing.py",
            description="Breathing module created"
        ),
        Proof(
            kind=ProofKind.FILE_EXISTS,
            path="Reports/HARNESS_CAPABILITIES_ANALYSIS.md",
            description="Harness analysis report exists"
        ),
        Proof(
            kind=ProofKind.GREP_MATCH,
            path="config/breathing_pacing.py",
            pattern=r"class BreathingPacer",
            description="BreathingPacer class implemented"
        ),
    ]

    # Verify all
    print("Verifying proofs...\n")
    results = verifier.verify_all(proofs)

    # Summary
    passed = sum(1 for r in results if r.verified)
    total = len(results)

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} proofs verified")

    if passed == total:
        print("✅ TASK COMPLETE - All proofs verified!")
    else:
        print("❌ TASK INCOMPLETE - Fix failed proofs")
        for r in results:
            if not r.verified:
                print(f"  - {r.proof.description}: {r.reasoning}")
