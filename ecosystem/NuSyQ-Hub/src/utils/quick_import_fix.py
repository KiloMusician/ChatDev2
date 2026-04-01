"""quick_import_fix.py.

Purpose:
- Conservative, text-based fixes for common import-name mistakes across
    the repository (useful during bulk audits).

Warning:
- This script performs textual replacements and should be run under version
    control. Always review diffs before committing.

Integration:
- Emit a patch file or run in a dry-run mode before applying changes.

OmniTag: {
        "purpose": "file_systematically_tagged",
        "tags": ["Python"],
        "category": "auto_tagged",
        "evolution_stage": "v1.0"
}

"""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def fix_file_imports(file_path: Path) -> bool:
    """Fix common import issues in a specific file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Common fixes
        fixes = [
            # Fix broken matplotlib import
            (r"^matplotlib\.pyplot$", "import matplotlib.pyplot as plt"),
            (r"^numpy$", "import numpy as np"),
            (r"^pandas$", "import pandas as pd"),
            (r"^scipy$", "import scipy"),
            (r"^sklearn$", "import sklearn"),
            # Fix incomplete import statements
            (r"^import matplotlib\.pyplot$", "import matplotlib.pyplot as plt"),
            (r"^import numpy$", "import numpy as np"),
            (r"^import pandas$", "import pandas as pd"),
        ]

        lines = content.split("\n")
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            for pattern, replacement in fixes:
                if re.match(pattern, line_stripped):
                    lines[i] = replacement

        content = "\n".join(lines)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

    except OSError:
        # IO-related errors while reading/writing files
        logger.debug("Suppressed OSError", exc_info=True)

    return False


def main() -> None:
    """Fix known import issues."""
    repo_env = os.getenv("KILO_FOOLISH_ROOT", Path.home() / "Documents" / "GitHub" / "KILO-FOOLISH")
    repository_root = Path(repo_env).expanduser()

    # Known problematic files
    problematic_files = [
        "Transcendent_Spine/kilo-foolish-transcendent-spine/tests/spine_tests.py",
        "Transcendent_Spine/kilo-foolish-transcendent-spine/tests/integration_tests.py",
    ]

    fixes_applied = 0

    for file_rel_path in problematic_files:
        file_path = repository_root / file_rel_path
        if file_path.exists():
            if fix_file_imports(file_path):
                fixes_applied += 1
        else:
            pass


if __name__ == "__main__":
    main()
