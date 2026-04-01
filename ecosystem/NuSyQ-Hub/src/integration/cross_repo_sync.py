"""Cross-Repo SNS Synchronization.

Synchronizes SNS notation definitions and patterns across NuSyQ-Hub, SimulatedVerse, and SNS-Core.

[OmniTag: cross_repo_sync, sns_core, synchronization, distributed_system]
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class SNSDefinition:
    """SNS notation definition for synchronization."""

    symbol: str
    meaning: str
    category: str  # structural, flow, data, operational, aggressive
    aliases: list[str] = field(default_factory=list)
    usage_example: str = ""
    token_savings_pct: float = 0.0
    checksum: str = ""

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum for integrity verification."""
        content = f"{self.symbol}{self.meaning}{self.category}".encode()
        return hashlib.sha256(content).hexdigest()


class CrossRepoSNSSynchronizer:
    """Synchronizes SNS notation definitions across repositories."""

    def __init__(
        self,
        hub_path: Path = Path("c:/Users/keath/Desktop/Legacy/NuSyQ-Hub"),
        simverse_path: Path = Path("c:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"),
        sns_core_path: Path = Path("c:/Users/keath/Desktop/Legacy/NuSyQ-Hub/temp_sns_core"),
    ):
        """Initialize synchronizer.

        Args:
            hub_path: Path to NuSyQ-Hub repo
            simverse_path: Path to SimulatedVerse repo
            sns_core_path: Path to SNS-Core repo/module
        """
        self.hub_path = hub_path
        self.simverse_path = simverse_path
        self.sns_core_path = sns_core_path
        self.sync_log_file = hub_path / "state" / "sns_sync.jsonl"
        self.definitions_file = hub_path / "state" / "sns_definitions.json"
        self.sync_log_file.parent.mkdir(parents=True, exist_ok=True)

    def get_sns_definitions(self) -> dict[str, SNSDefinition]:
        """Extract SNS definitions from all repos.

        Returns:
            Dictionary of symbol -> SNSDefinition
        """
        definitions = {}

        # Read from SNS-Core
        symbols_file = self.sns_core_path / "symbols.md"
        if symbols_file.exists():
            content = symbols_file.read_text()
            # Parse markdown format: # Symbol: ⨳
            # Meaning: system/scope boundary
            lines = content.split("\n")
            current_symbol = None
            for line in lines:
                if line.startswith("# Symbol:"):
                    current_symbol = line.split(": ")[-1].strip()
                elif line.startswith("Meaning:") and current_symbol:
                    meaning = line.split(": ")[-1].strip()
                    definitions[current_symbol] = SNSDefinition(
                        symbol=current_symbol,
                        meaning=meaning,
                        category="structural",
                    )

        # Read from NuSyQ-Hub helper
        helper_file = self.hub_path / "src" / "utils" / "sns_core_helper.py"
        if helper_file.exists():
            content = helper_file.read_text()
            # Extract SNS_SYMBOLS dictionary
            if "SNS_SYMBOLS = {" in content:
                start = content.find("SNS_SYMBOLS = {")
                end = content.find("}", start) + 1
                symbols_str = content[start:end]
                # Parse dictionary (simplified)
                for line in symbols_str.split("\n"):
                    if ":" in line and '"' in line:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            symbol = parts[0].strip().strip('"').strip("'")
                            meaning = parts[1].strip().strip(",").strip('"').strip("'")
                            if symbol and meaning:
                                definitions[symbol] = SNSDefinition(
                                    symbol=symbol,
                                    meaning=meaning,
                                    category="mixed",
                                )

        return definitions

    def detect_definition_changes(self) -> dict[str, Any]:
        """Detect changes in SNS definitions across repos.

        Returns:
            Dictionary of changes detected
        """
        current_defs = self.get_sns_definitions()
        previous_defs = {}

        # Load previous definitions if they exist
        if self.definitions_file.exists():
            with open(self.definitions_file) as f:
                data = json.load(f)
                previous_defs = {
                    k: SNSDefinition(**v) for k, v in data.get("definitions", {}).items()
                }

        changes: dict[str, Any] = {
            "added": [],
            "removed": [],
            "modified": [],
            "timestamp": datetime.now().isoformat(),
        }

        # Find added/modified
        for symbol, defn in current_defs.items():
            if symbol not in previous_defs:
                changes["added"].append(
                    {
                        "symbol": symbol,
                        "meaning": defn.meaning,
                        "category": defn.category,
                    }
                )
            elif defn.meaning != previous_defs[symbol].meaning:
                changes["modified"].append(
                    {
                        "symbol": symbol,
                        "old_meaning": previous_defs[symbol].meaning,
                        "new_meaning": defn.meaning,
                    }
                )

        # Find removed
        for symbol in previous_defs:
            if symbol not in current_defs:
                changes["removed"].append({"symbol": symbol})

        return changes

    def propagate_definitions_to_repos(self) -> dict[str, Any]:
        """Propagate updated SNS definitions to all repos.

        Returns:
            Propagation result summary
        """
        definitions = self.get_sns_definitions()
        results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "repos_updated": [],
            "errors": [],
        }

        # Save canonical definitions
        self._save_definitions_to_file(definitions)

        # Update SNS-Core
        try:
            self._update_sns_core_symbols(definitions)
            results["repos_updated"].append("sns-core")
        except Exception as e:
            results["errors"].append(f"SNS-Core update failed: {e}")

        # Update NuSyQ-Hub helper
        try:
            self._update_hub_helper(definitions)
            results["repos_updated"].append("nusyq-hub")
        except Exception as e:
            results["errors"].append(f"NuSyQ-Hub update failed: {e}")

        # Update SimulatedVerse
        try:
            self._update_simverse(definitions)
            results["repos_updated"].append("simulated-verse")
        except Exception as e:
            results["errors"].append(f"SimulatedVerse update failed: {e}")

        return results

    def _save_definitions_to_file(self, definitions: dict[str, SNSDefinition]) -> None:
        """Save definitions to JSON file.

        Args:
            definitions: SNS definitions to save
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "definitions": {
                k: {
                    "symbol": v.symbol,
                    "meaning": v.meaning,
                    "category": v.category,
                    "aliases": v.aliases,
                    "usage_example": v.usage_example,
                    "token_savings_pct": v.token_savings_pct,
                }
                for k, v in definitions.items()
            },
        }
        with open(self.definitions_file, "w") as f:
            json.dump(data, f, indent=2)

    def _update_sns_core_symbols(self, definitions: dict[str, SNSDefinition]) -> None:
        """Update SNS-Core symbols.md file.

        Args:
            definitions: SNS definitions to propagate
        """
        symbols_file = self.sns_core_path / "symbols.md"
        symbols_file.parent.mkdir(parents=True, exist_ok=True)

        content = "# SNS-Core Symbol Definitions\n\n"
        content += f"Last Updated: {datetime.now().isoformat()}\n\n"

        for symbol, defn in sorted(definitions.items()):
            content += f"## Symbol: {symbol}\n"
            content += f"**Meaning:** {defn.meaning}\n"
            content += f"**Category:** {defn.category}\n"
            if defn.usage_example:
                content += f"**Example:** {defn.usage_example}\n"
            if defn.token_savings_pct > 0:
                content += f"**Token Savings:** {defn.token_savings_pct}%\n"
            content += "\n"

        symbols_file.write_text(content)

    def _update_hub_helper(self, definitions: dict[str, SNSDefinition]) -> None:
        """Update NuSyQ-Hub SNS helper.

        Args:
            definitions: SNS definitions to propagate
        """
        helper_file = self.hub_path / "src" / "utils" / "sns_core_helper.py"
        content = helper_file.read_text()

        # Find SNS_SYMBOLS and replace
        if "SNS_SYMBOLS = {" in content:
            start = content.find("SNS_SYMBOLS = {")
            end = content.find("}", start) + 1

            new_symbols = "SNS_SYMBOLS = {\n"
            for symbol, defn in sorted(definitions.items()):
                new_symbols += f'    "{symbol}": "{defn.meaning}",\n'
            new_symbols += "}"

            content = content[:start] + new_symbols + content[end:]
            helper_file.write_text(content)

    def _update_simverse(self, definitions: dict[str, SNSDefinition]) -> None:
        """Update SimulatedVerse SNS integration.

        Args:
            definitions: SNS definitions to propagate
        """
        config_file = self.simverse_path / "config" / "sns_definitions.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "timestamp": datetime.now().isoformat(),
            "definitions": [
                {
                    "symbol": defn.symbol,
                    "meaning": defn.meaning,
                    "category": defn.category,
                }
                for defn in definitions.values()
            ],
        }

        config_file.write_text(json.dumps(data, indent=2))

    def create_git_hook(self) -> str:
        """Create git hook for automatic synchronization on push.

        Returns:
            Git hook script content
        """
        return """#!/bin/bash
# Post-push hook: Synchronize SNS definitions across repos

echo "SNS Synchronization: Checking for definition changes..."

python3 << 'EOF'
from pathlib import Path
from src.integration.cross_repo_sync import CrossRepoSNSSynchronizer

sync = CrossRepoSNSSynchronizer()
changes = sync.detect_definition_changes()

if changes['added'] or changes['modified'] or changes['removed']:
    print("SNS definition changes detected, propagating...")
    result = sync.propagate_definitions_to_repos()
    print(f"Updated repos: {', '.join(result['repos_updated'])}")
else:
    print("No SNS definition changes detected.")
EOF

exit 0
"""

    def install_sync_hooks(self) -> dict[str, Any]:
        """Install synchronization hooks in all repos.

        Returns:
            Installation result summary
        """
        results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "hooks_installed": [],
            "errors": [],
        }

        repos = [
            (self.hub_path, "nusyq-hub"),
            (self.simverse_path, "simulated-verse"),
        ]

        hook_content = self.create_git_hook()

        for repo_path, repo_name in repos:
            try:
                hook_file = repo_path / ".git" / "hooks" / "post-push"
                hook_file.parent.mkdir(parents=True, exist_ok=True)
                hook_file.write_text(hook_content)
                hook_file.chmod(0o755)
                results["hooks_installed"].append(repo_name)
            except Exception as e:
                results["errors"].append(f"{repo_name} hook install failed: {e}")

        return results

    def generate_sync_report(self) -> dict[str, Any]:
        """Generate comprehensive synchronization report.

        Returns:
            Sync report with status
        """
        changes = self.detect_definition_changes()
        definitions = self.get_sns_definitions()

        return {
            "timestamp": datetime.now().isoformat(),
            "total_definitions": len(definitions),
            "recent_changes": {
                "added": len(changes["added"]),
                "modified": len(changes["modified"]),
                "removed": len(changes["removed"]),
            },
            "change_details": changes,
            "repos_status": {
                "nusyq-hub": self.hub_path.exists(),
                "simulated-verse": self.simverse_path.exists(),
                "sns-core": self.sns_core_path.exists(),
            },
            "next_steps": [
                "1. Review detected changes",
                "2. Propagate definitions: propagate_definitions_to_repos()",
                "3. Install hooks: install_sync_hooks()",
                "4. Verify sync: Run SNS utilities in each repo",
            ],
        }
