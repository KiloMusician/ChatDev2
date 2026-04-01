#!/usr/bin/env python3
"""Non-blocking, token-efficient error scanner + fixer.
Scans for syntax/lint errors and fixes easiest ones first (fewest errors per file).
"""

import json
from collections import defaultdict
from pathlib import Path


class ChugModeErrorFixer:
    def __init__(self, repo_path: str):
        self.repo = Path(repo_path)
        self.errors_by_file = defaultdict(list)
        self.files_by_error_count = []

    def quick_syntax_check(self) -> dict:
        """Non-blocking syntax check using compile()"""
        print("🔍 QUICK SYNTAX SCAN (non-blocking)")

        py_files = list(self.repo.glob("src/**/*.py"))[:50]  # First 50 only

        for py_file in py_files:
            try:
                with open(py_file, encoding="utf-8", errors="ignore") as f:
                    compile(f.read(), str(py_file), "exec")
            except SyntaxError as e:
                self.errors_by_file[str(py_file)].append({"type": "SyntaxError", "line": e.lineno, "msg": e.msg})
            except Exception:
                pass  # Skip other errors

        return self.errors_by_file

    def sort_by_complexity(self):
        """Sort files by error count (easiest first)"""
        self.files_by_error_count = sorted(self.errors_by_file.items(), key=lambda x: len(x[1]))
        return self.files_by_error_count

    def report_easiest_wins(self, max_show=10):
        """Show files with 1-3 errors (quick wins)"""
        print("\n✨ EASIEST WINS (1-3 errors per file):")
        print("=" * 70)

        count = 0
        for filepath, errors in self.files_by_error_count:
            if len(errors) > 3:
                break
            if len(errors) > 0:
                print(f"\n📄 {Path(filepath).name} ({len(errors)} error(s))")
                for err in errors:
                    print(f"   Line {err.get('line', '?')}: {err['msg']}")
                count += 1
                if count >= max_show:
                    break

        return count

    def generate_fix_targets(self):
        """Return prioritized list of files to fix"""
        targets = []

        # Group by error count
        for filepath, errors in self.files_by_error_count:
            error_count = len(errors)
            if error_count > 0:
                targets.append({"file": filepath, "error_count": error_count, "errors": errors})

        return targets


def main():
    repos = [
        "C:/Users/keath/Desktop/Legacy/NuSyQ-Hub",
        "C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse",
        "C:/Users/keath/NuSyQ",
    ]

    all_targets = []

    for repo_path in repos:
        try:
            repo_name = Path(repo_path).name
            print(f"\n📦 Scanning {repo_name}...")

            fixer = ChugModeErrorFixer(repo_path)
            fixer.quick_syntax_check()
            fixer.sort_by_complexity()

            targets = fixer.generate_fix_targets()
            all_targets.extend(targets)

            print(f"   Found {len(targets)} files with errors")

        except Exception as e:
            print(f"   ⚠️  Error scanning: {e}")

    # Sort all targets by error count
    all_targets.sort(key=lambda x: x["error_count"])

    print("\n" + "=" * 70)
    print(f"📋 TOTAL FIXABLE FILES: {len(all_targets)}")
    print("=" * 70)

    # Show easiest wins
    print("\n🎯 TOP 10 EASIEST FIXES (sort by error count):")
    for i, target in enumerate(all_targets[:10], 1):
        file_name = Path(target["file"]).name
        print(f"{i}. {file_name}: {target['error_count']} error(s)")

    # Save for next phase
    with open("fix_targets.json", "w") as f:
        json.dump(all_targets[:20], f, indent=2)

    print("\n✅ Fix targets saved to: fix_targets.json")


if __name__ == "__main__":
    main()
