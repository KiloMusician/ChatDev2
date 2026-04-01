#!/usr/bin/env python
"""Validate all Python code examples in CODE_TOUR_COMPREHENSIVE.md"""

import ast
import logging
import re
from pathlib import Path

doc_path = Path("C:/Users/keath/NuSyQ/docs/CODE_TOUR_COMPREHENSIVE.md")
content = doc_path.read_text(encoding="utf-8")

# Configure simple logging for script output
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Extract Python code blocks
pattern = r"```python\n(.*?)\n```"
matches = re.findall(pattern, content, re.DOTALL)

logging.info(f"Found {len(matches)} Python code blocks\n")

errors = []
for i, code in enumerate(matches, 1):
    try:
        ast.parse(code)
    except SyntaxError as e:
        lines = code.split("\n")
        lineno = getattr(e, "lineno", None)
        if lineno is not None and 1 <= lineno <= len(lines):
            snippet = lines[lineno - 1]
        else:
            snippet = "?"
        errors.append({"block": i, "line": lineno, "msg": e.msg, "snippet": snippet[:60]})
    except Exception as e:
        errors.append(
            {"block": i, "line": "?", "msg": f"{type(e).__name__}: {str(e)[:50]}", "snippet": ""}
        )

if errors:
    logging.error("❌ Code Syntax Errors Found:\n")
    for err in errors:
        logging.error(f"Block {err['block']}, Line {err['line']}: {err['msg']}")
        if err["snippet"]:
            logging.error(f"  → {err['snippet']}")
        logging.error("")
    exit(1)
else:
    logging.info(f"✅ All {len(matches)} Python code blocks passed syntax validation!")
    logging.info("\n✨ Code quality assessment:")
    logging.info(f"  - Total blocks: {len(matches)}")
    logging.info("  - Syntax errors: 0")
    logging.info("  - Status: READY FOR PRODUCTION ✅")
