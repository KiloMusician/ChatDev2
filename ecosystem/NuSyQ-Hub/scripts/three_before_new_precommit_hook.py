#!/usr/bin/env python
"""Pre-commit hook for Three Before New enforcement.

This hook prevents commits that add new tools without Three Before New compliance.
Install by linking to .git/hooks/pre-commit or running:
    ln -s ../../scripts/three_before_new_precommit_hook.py .git/hooks/pre-commit

Set TBN_WARN_ONLY=1 environment variable to warn instead of block.
"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))

from scripts.three_before_new_audit import main

if __name__ == "__main__":
    sys.exit(main())
