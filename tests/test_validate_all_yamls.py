"""Tests for the CI YAML gate (``tools/validate_all_yamls.py``).

``validate-yamls.yml`` is the only workflow that actually gates content in this
repo, and its single meaningful step is ``uv run python
tools/validate_all_yamls.py``.  These tests pin the one property a gate must
have: it has to be able to say no -- including when it is handed nothing to
check.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "tools" / "validate_all_yamls.py"
KNOWN_GOOD_YAML = REPO_ROOT / "yaml_instance" / "demo_code.yaml"


def _run_validator(workdir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=str(workdir),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


class ValidateAllYamlsGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workdir = Path(self._tmp.name)
        self.yaml_dir = self.workdir / "yaml_instance"
        self.addCleanup(self._tmp.cleanup)

    def test_passes_on_a_known_good_workflow(self) -> None:
        """Positive control: the gate must be able to say yes."""
        self.yaml_dir.mkdir()
        shutil.copy(KNOWN_GOOD_YAML, self.yaml_dir / KNOWN_GOOD_YAML.name)

        result = _run_validator(self.workdir)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fails_on_a_malformed_workflow(self) -> None:
        """Negative control: a control that cannot disagree proves nothing."""
        self.yaml_dir.mkdir()
        (self.yaml_dir / "broken.yaml").write_text(
            "nodes: [unclosed\n  : : :\n", encoding="utf-8"
        )

        result = _run_validator(self.workdir)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fails_when_no_yaml_files_are_found(self) -> None:
        """An empty yaml_instance/ must not be reported as a clean bill of health.

        The gate used to ``return`` here, which exits 0 -- so renaming, moving
        or emptying yaml_instance/ (or the glob drifting off ``*.yaml``) would
        turn the CI job green while validating nothing at all.
        """
        self.yaml_dir.mkdir()

        result = _run_validator(self.workdir)

        self.assertNotEqual(
            result.returncode,
            0,
            "validator reported success while validating zero files:\n"
            + result.stdout
            + result.stderr,
        )

    def test_fails_when_the_directory_is_missing(self) -> None:
        result = _run_validator(self.workdir)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
