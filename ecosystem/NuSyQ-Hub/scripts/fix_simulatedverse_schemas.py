#!/usr/bin/env python3
"""Fix SimulatedVerse Schema Export Issues.

Multiple files importing from broken schema exports.
This script patches all schema imports to use fallbacks.
"""

import re
from pathlib import Path


class SimulatedVerseSchemaPatcher:
    """Patch SimulatedVerse schema import issues."""

    def __init__(self):
        self.simulatedverse_path = Path("c:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse")
        self.backup_suffix = ".backup_schema_fix"
        self.fixes_applied: list[tuple[str, str]] = []

    def find_broken_imports(self) -> list[Path]:
        """Find all files importing from broken schemas."""
        broken_files = []

        # Patterns that indicate schema imports
        patterns = [
            r'from ["\'].*shared/schema.*["\']',
            r'import.*from ["\'].*shared/schemas/.*["\']',
            r"import.*gameEvents",
            r"import.*Proposal",
        ]

        for ts_file in self.simulatedverse_path.rglob("*.ts"):
            if ".backup" in str(ts_file) or "node_modules" in str(ts_file):
                continue

            try:
                content = ts_file.read_text(encoding="utf-8")
                for pattern in patterns:
                    if re.search(pattern, content):
                        broken_files.append(ts_file)
                        break
            except (OSError, UnicodeDecodeError):
                pass

        return broken_files

    def comment_out_schema_imports(self, file_path: Path) -> bool:
        """Comment out broken schema imports."""
        try:
            content = file_path.read_text(encoding="utf-8")
            original = content

            # Backup
            backup_path = Path(str(file_path) + self.backup_suffix)
            backup_path.write_text(content, encoding="utf-8")

            # Comment out broken imports
            patterns_to_comment = [
                # gameEvents import
                (r"^(\s*)(gameEvents,?\s*)$", r"\1// PATCHED: \2"),
                # Proposal import
                (
                    r"^(import\s*{\s*Proposal\s*}.*shared/schemas/proposal.*)",
                    r"// PATCHED: \1",
                ),
                # Full schema imports with gameEvents
                (
                    r"^(import\s*{[^}]*gameEvents[^}]*}.*shared/schema.*)",
                    r"// PATCHED: \1",
                ),
            ]

            modified = False
            for pattern, replacement in patterns_to_comment:
                new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                if new_content != content:
                    content = new_content
                    modified = True

            # Also comment out usage of these imports
            if "gameEvents" in original or "Proposal" in original:
                # Comment out gameEvents in schema object
                content = re.sub(
                    r"schema:\s*{\s*([^}]*gameEvents[^}]*)}",
                    r"schema: { /* PATCHED: \1 */ }",
                    content,
                )

                # Comment out lines using gameStates/gameEvents/players tables
                content = re.sub(
                    r"^(\s*)(\.from\(gameStates\).*)$",
                    r"\1// PATCHED: \2",
                    content,
                    flags=re.MULTILINE,
                )
                content = re.sub(
                    r"^(\s*)(\.insert\(gameStates\).*)$",
                    r"\1// PATCHED: \2",
                    content,
                    flags=re.MULTILINE,
                )
                content = re.sub(
                    r"^(\s*)(\.update\(gameStates\).*)$",
                    r"\1// PATCHED: \2",
                    content,
                    flags=re.MULTILINE,
                )

                modified = True

            if modified:
                file_path.write_text(content, encoding="utf-8")
                relative = file_path.relative_to(self.simulatedverse_path)
                self.fixes_applied.append((str(relative), "Schema imports commented out"))
                return True

            return False

        except (OSError, AttributeError, RuntimeError):
            return False

    def create_minimal_schemas(self):
        """Create minimal schema exports to prevent import errors."""
        # Create minimal proposal schema
        proposal_schema_path = self.simulatedverse_path / "shared" / "schemas" / "proposal.ts"
        if proposal_schema_path.exists():
            backup = Path(str(proposal_schema_path) + self.backup_suffix)
            proposal_schema_path.rename(backup)

        minimal_proposal = """// Minimal proposal schema (patched)
import { z } from "zod";

export const Proposal = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().optional(),
  status: z.enum(['pending', 'approved', 'rejected']).default('pending'),
  created_at: z.date().optional(),
});

export type ProposalType = z.infer<typeof Proposal>;
"""

        proposal_schema_path.write_text(minimal_proposal, encoding="utf-8")

        # Add missing exports to main schema
        schema_path = self.simulatedverse_path / "shared" / "schema.ts"
        if schema_path.exists():
            content = schema_path.read_text(encoding="utf-8")

            # Add gameEvents if missing
            if "gameEvents" not in content:
                content += """

// Minimal DB table stubs (patched to prevent import errors)
export const gameEvents = null;  // TODO: Implement proper Drizzle table
export const gameStates = null;  // TODO: Implement proper Drizzle table
export const players = null;  // TODO: Implement proper Drizzle table
export const games = null;  // TODO: Implement proper Drizzle table
export const multiplayerSessions = null;  // TODO: Implement proper Drizzle table
export const playerProfiles = null;  // TODO: Implement proper Drizzle table

// Type stubs
export type GameEvent = any;  // TODO: Implement proper type
export type GameState = any;  // TODO: Implement proper type
export type Player = any;  // TODO: Implement proper type
export type Game = any;  // TODO: Implement proper type
export type MultiplayerSession = any;  // TODO: Implement proper type
export type PlayerProfile = any;  // TODO: Implement proper type
"""
                schema_path.write_text(content, encoding="utf-8")

    def disable_persistence_routes(self):
        """Disable routes that require DB persistence."""
        index_path = self.simulatedverse_path / "server" / "index.ts"
        if not index_path.exists():
            return

        content = index_path.read_text(encoding="utf-8")

        # Backup
        backup = Path(str(index_path) + self.backup_suffix)
        backup.write_text(content, encoding="utf-8")

        # Comment out game persistence routes
        content = re.sub(
            r"^(import gamePersistenceRoutes.*)",
            r"// PATCHED: \1",
            content,
            flags=re.MULTILINE,
        )
        content = re.sub(
            r"^(\s*app\.use\(.*gamePersistenceRoutes.*)",
            r"// PATCHED: \1",
            content,
            flags=re.MULTILINE,
        )

        # Comment out any other persistence imports
        content = re.sub(
            r"^(.*from.*game-persistence.*)",
            r"// PATCHED: \1",
            content,
            flags=re.MULTILINE,
        )

        index_path.write_text(content, encoding="utf-8")
        self.fixes_applied.append(("server/index.ts", "Disabled persistence routes"))

    def run_fix(self):
        """Run complete fix process."""
        # Create minimal schemas
        self.create_minimal_schemas()

        # Disable persistence routes
        self.disable_persistence_routes()

        # Find and patch broken imports
        broken_files = self.find_broken_imports()

        patched_count = 0
        for file_path in broken_files:
            if self.comment_out_schema_imports(file_path):
                patched_count += 1
                file_path.relative_to(self.simulatedverse_path)

        # Summary
        for _file_path, _fix_type in self.fixes_applied[:10]:  # Show first 10
            pass
        if len(self.fixes_applied) > 10:
            pass


def main():
    """Run schema patcher."""
    patcher = SimulatedVerseSchemaPatcher()
    patcher.run_fix()


if __name__ == "__main__":
    main()
