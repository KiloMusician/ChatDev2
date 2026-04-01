"""Generate API documentation from docstrings using Sphinx.

This script builds HTML documentation under ``docs/api/_build`` using
``sphinx-apidoc`` and ``sphinx-build``. Docstrings are parsed with Google
style conventions via ``sphinx.ext.napoleon``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs" / "api"
BUILD = DOCS / "_build"


def generate_docs() -> None:
    """Generate HTML API documentation in ``docs/api/_build``."""
    BUILD.mkdir(parents=True, exist_ok=True)

    # Generate reStructuredText sources from the Python modules
    subprocess.run(
        ["sphinx-apidoc", "-o", str(DOCS), str(ROOT / "src")],
        check=True,
    )

    # Build HTML documentation
    subprocess.run(
        ["sphinx-build", "-b", "html", str(DOCS), str(BUILD)],
        check=True,
    )


if __name__ == "__main__":
    generate_docs()
