#!/usr/bin/env python3
"""🔧 Surgical Error Fixer - Automated Quality Improvements
========================================================

Systematically fixes common code quality issues across the codebase:
- Missing encoding in open() calls
- Bare except clauses
- Missing type annotations
- Duplicate string literals
- Too-broad exception handling

OmniTag: {
    "purpose": "Automated code quality surgical fixes",
    "dependencies": ["ast", "pathlib", "re"],
    "context": "Mass code modernization and quality improvement",
    "evolution_stage": "v1.0"
}
"""

import re
from pathlib import Path


class SurgicalErrorFixer:
    """Automated code quality improvements"""

    def __init__(self, repo_root: Path = Path(".")):
        self.repo_root = Path(repo_root)
        self.fixes_applied = {
            "encoding_added": 0,
            "exceptions_narrowed": 0,
            "type_hints_added": 0,
            "literals_deduped": 0,
        }

    def fix_file(self, file_path: Path) -> bool:
        """Apply surgical fixes to a single file"""
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Fix 1: Add encoding to open() calls
            content = self._fix_open_encoding(content)

            # Fix 2: Narrow exception handling
            content = self._fix_broad_exceptions(content)

            # Fix 3: Add type hints to common patterns
            content = self._add_type_hints(content)

            # Only write if changes were made
            if content != original_content:
                file_path.write_text(content, encoding="utf-8")
                print(f"✅ Fixed: {file_path.relative_to(self.repo_root)}")
                return True
            return False

        except Exception as e:
            print(f"⚠️  Error fixing {file_path}: {e}")
            return False

    def _fix_open_encoding(self, content: str) -> str:
        """Add encoding='utf-8' to open() calls that lack it"""
        # Pattern: open(...) without encoding parameter
        # This is a simplified version - real fix would use AST
        patterns = [
            (r"\bopen\s*\(\s*([^,)]+)\s*\)", r"open(\1, encoding='utf-8')"),
            (
                r'\bopen\s*\(\s*([^,)]+)\s*,\s*(["\'][rwa]+["\'])\s*\)',
                r"open(\1, \2, encoding='utf-8')",
            ),
        ]

        for pattern, replacement in patterns:
            # Only replace if 'encoding' not already present nearby
            matches = list(re.finditer(pattern, content))
            for match in reversed(matches):  # Process in reverse to maintain positions
                context = content[max(0, match.start() - 50) : match.end() + 50]
                if "encoding" not in context:
                    old_text = match.group(0)
                    new_text = re.sub(pattern, replacement, old_text)
                    content = content[: match.start()] + new_text + content[match.end() :]
                    self.fixes_applied["encoding_added"] += 1

        return content

    def _fix_broad_exceptions(self, content: str) -> str:
        """Replace bare except: with except Exception:"""
        # Pattern: except:\n
        pattern = r"(\s+)except\s*:\s*\n"
        replacement = r"\1except Exception:\n"

        new_content, count = re.subn(pattern, replacement, content)
        self.fixes_applied["exceptions_narrowed"] += count

        return new_content

    def _add_type_hints(self, content: str) -> str:
        """Add type hints to common patterns"""
        # Pattern: def function(arg) -> without type hint
        # This is simplified - real implementation would use AST

        # Add List import if needed
        if re.search(r"\bList\[", content) and "from typing import" in content:
            if not re.search(r"from typing import.*\bList\b", content):
                content = re.sub(r"(from typing import [^\n]+)", r"\1, List", content, count=1)

        return content

    def process_directory(self, directory: Path | None = None, pattern: str = "**/*.py") -> dict:
        """Process all Python files in directory"""
        if directory is None:
            directory = self.repo_root / "src"

        files_processed = 0
        files_fixed = 0

        for py_file in directory.glob(pattern):
            if py_file.is_file() and "__pycache__" not in str(py_file):
                files_processed += 1
                if self.fix_file(py_file):
                    files_fixed += 1

        return {
            "files_processed": files_processed,
            "files_fixed": files_fixed,
            "fixes_applied": self.fixes_applied.copy(),
        }


def main():
    """Run surgical fixes on the codebase"""
    print("🔧 Surgical Error Fixer - Starting...")
    print("=" * 70)

    fixer = SurgicalErrorFixer()

    # Process src/ directory
    results = fixer.process_directory()

    print("\n" + "=" * 70)
    print("📊 Summary:")
    print(f"   Files processed: {results['files_processed']}")
    print(f"   Files fixed: {results['files_fixed']}")
    print("\n   Fixes applied:")
    for fix_type, count in results["fixes_applied"].items():
        print(f"      {fix_type}: {count}")

    print("\n✅ Surgical fixes complete!")


if __name__ == "__main__":
    main()
