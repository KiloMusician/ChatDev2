#!/usr/bin/env python3
"""╔══════════════════════════════════════════════════════════════════════════╗
║ Ollama Port Standardization Tool                                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.ecosystem.port.standardizer                              ║
║ TYPE: Infrastructure Fix Utility                                        ║
║ STATUS: Production                                                       ║
║ VERSION: 1.0.0                                                           ║
║ TAGS: [infrastructure, ollama, port-fix, ecosystem-repair]              ║
║ CONTEXT: Cross-repository port standardization                          ║
║ AGENTS: [AllAgents] - Infrastructure repair utility                     ║
║ DEPS: [pathlib, re, json]                                               ║
║ INTEGRATIONS: [NuSyQ-Hub, SimulatedVerse, NuSyQ Core]                   ║
║ CREATED: 2025-10-08                                                      ║
║ UPDATED: 2025-10-08                                                      ║
║ AUTHOR: GitHub Copilot + Kilo the Prime Architect                       ║
║ STABILITY: High (Infrastructure Critical)                               ║
║ PURPOSE: Fix Ollama port inconsistencies across entire ecosystem        ║
║ USAGE: python ollama_port_standardizer.py [--dry-run] [--verbose]       ║
╚══════════════════════════════════════════════════════════════════════════╝

Standardizes Ollama port usage across all three repositories.
Changes all references from port 11435 to the standard port 11434.

OmniTag: [infrastructure-fix, port-standardization, ollama-connection]
MegaTag: [INFRA⨳FIX⦾OLLAMA→∞]
"""

import argparse
import re
from pathlib import Path
from typing import Any


class OllamaPortStandardizer:
    """Standardizes Ollama port usage across the NuSyQ ecosystem.

    This tool fixes the port inconsistency where Ollama runs on the standard
    port 11434 but various parts of the ecosystem expect it on port 11435.
    """

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.repos = {
            "NuSyQ-Hub": Path("c:/Users/keath/Desktop/Legacy/NuSyQ-Hub"),
            "SimulatedVerse": Path("c:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"),
            "NuSyQ-Core": Path("c:/Users/keath/NuSyQ"),
        }
        self.changes_made = []

        # Patterns to find and replace
        self.patterns = [
            # URL patterns
            (r"http://localhost:11434", "http://localhost:11434"),
            (r"localhost:11435", "localhost:11434"),
            (r'"port":\s*11435', '"port": 11434'),
            (r"port=11435", "port=11434"),
            (r"PORT=11435", "PORT=11434"),
            # API endpoint patterns
            (r"11435/api/", "11434/api/"),
            # Configuration patterns
            (r'"11435"', '"11434"'),
            (r"=11435", "=11434"),
        ]

    def scan_file(self, file_path: Path) -> list[tuple[int, str, str]]:
        """Scan file for port 11435 references.

        Returns:
            List of (line_number, original_line, fixed_line) tuples
        """
        if not file_path.exists() or file_path.is_dir():
            return []

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            lines = content.split("\n")
            changes = []

            for line_num, line in enumerate(lines, 1):
                original_line = line
                modified_line = line

                # Apply all patterns
                for pattern, replacement in self.patterns:
                    modified_line = re.sub(pattern, replacement, modified_line)

                # If line changed, record it
                if original_line != modified_line:
                    changes.append((line_num, original_line, modified_line))

            return changes

        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error scanning {file_path}: {e}")
            return []

    def apply_fixes(self, file_path: Path, changes: list[tuple[int, str, str]]) -> bool:
        """Apply fixes to a file.

        Returns:
            True if file was successfully modified
        """
        if not changes:
            return False

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # Apply changes (in reverse order to maintain line numbers)
            for line_num, _original, fixed in reversed(changes):
                if line_num <= len(lines):
                    lines[line_num - 1] = fixed + "\n"

            # Write back to file
            if not self.dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

            return True

        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            return False

    def process_repository(self, repo_name: str, repo_path: Path) -> dict[str, Any]:
        """Process all files in a repository.

        Returns:
            Dictionary with processing results
        """
        if not repo_path.exists():
            return {"status": "not_found", "files_processed": 0, "files_changed": 0, "changes": []}

        results = {"status": "processed", "files_processed": 0, "files_changed": 0, "changes": []}

        # File types to process
        extensions = {".py", ".json", ".yaml", ".yml", ".js", ".ts", ".md", ".txt", ".ps1", ".sh"}

        # Scan all relevant files
        for file_path in repo_path.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in extensions
                and not any(
                    skip in str(file_path)
                    for skip in [".git", "__pycache__", "node_modules", ".venv"]
                )
            ):
                results["files_processed"] += 1
                changes = self.scan_file(file_path)

                if changes:
                    results["files_changed"] += 1
                    relative_path = file_path.relative_to(repo_path)

                    if self.apply_fixes(file_path, changes):
                        results["changes"].append(
                            {
                                "file": str(relative_path),
                                "line_changes": len(changes),
                                "changes": changes[:3],  # First 3 changes for preview
                            }
                        )

                        if self.verbose:
                            print(f"✅ Fixed {len(changes)} lines in {relative_path}")

        return results

    def generate_report(self, all_results: dict[str, dict[str, Any]]) -> None:
        """Generate comprehensive report of changes made."""
        print("\n" + "=" * 60)
        print("🔧 OLLAMA PORT STANDARDIZATION REPORT")
        print("=" * 60)

        total_files_processed = 0
        total_files_changed = 0
        total_line_changes = 0

        for repo_name, results in all_results.items():
            if results["status"] == "not_found":
                print(f"\n❌ {repo_name}: Repository not found")
                continue

            files_processed = results["files_processed"]
            files_changed = results["files_changed"]
            changes = results["changes"]

            total_files_processed += files_processed
            total_files_changed += files_changed

            print(f"\n📁 {repo_name}:")
            print(f"   Files processed: {files_processed}")
            print(f"   Files changed: {files_changed}")

            if changes:
                print("   📝 Changes made:")
                for change in changes[:5]:  # Show first 5 files
                    line_changes = change["line_changes"]
                    total_line_changes += line_changes
                    print(f"      • {change['file']}: {line_changes} lines")

                if len(changes) > 5:
                    remaining = len(changes) - 5
                    print(f"      ... and {remaining} more files")

        print("\n📊 SUMMARY:")
        print(f"   Total files processed: {total_files_processed}")
        print(f"   Total files changed: {total_files_changed}")
        print(f"   Total line changes: {total_line_changes}")

        if self.dry_run:
            print("\n💡 This was a DRY RUN. Use --apply to make actual changes.")
        else:
            print("\n✅ Changes have been applied!")
            print("\n🎯 NEXT STEPS:")
            print("   1. Test Ollama connection: curl http://localhost:11434/api/tags")
            print("   2. Restart MCP server: cd c:/Users/keath/NuSyQ && python mcp_server/main.py")
            print("   3. Run health check: python ecosystem_health_checker.py")

    def run(self) -> None:
        """Run the port standardization process."""
        print("🔧 Ollama Port Standardization Tool")
        print("=" * 50)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'APPLY CHANGES'}")
        print(f"Verbose: {self.verbose}")
        print()

        all_results = {}

        for repo_name, repo_path in self.repos.items():
            print(f"🔍 Processing {repo_name}...")
            results = self.process_repository(repo_name, repo_path)
            all_results[repo_name] = results

            if results["status"] == "processed":
                print(
                    f"   ✅ {results['files_changed']}/{results['files_processed']} files need updates"
                )
            else:
                print("   ❌ Repository not accessible")

        self.generate_report(all_results)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Standardize Ollama port usage across NuSyQ ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ollama_port_standardizer.py --dry-run     # Preview changes
  python ollama_port_standardizer.py --apply       # Apply changes
  python ollama_port_standardizer.py --apply -v    # Apply with verbose output
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without applying them (default)",
    )
    parser.add_argument("--apply", action="store_true", help="Apply changes to files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # If --apply is specified, turn off dry-run
    dry_run = not args.apply

    standardizer = OllamaPortStandardizer(dry_run=dry_run, verbose=args.verbose)
    standardizer.run()


if __name__ == "__main__":
    main()
