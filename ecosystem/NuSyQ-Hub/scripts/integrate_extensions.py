#!/usr/bin/env python3
"""VS Code Extension Integration Helper.

Checks extension status, provides configuration guidance,
and helps wire up extension features.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class ExtensionIntegrator:
    """Integrate and configure VS Code extensions."""

    EXTENSION_ID_RE = re.compile(r"^[a-z0-9][a-z0-9\-]*\.[a-z0-9][a-z0-9\-]*$")

    def __init__(self, use_code_cli: bool = False) -> None:
        self.repo_root = Path.cwd()
        self.vscode_dir = self.repo_root / ".vscode"
        self.extensions_json = self.vscode_dir / "extensions.json"
        self.settings_json = self.vscode_dir / "settings.json"
        self.reports_dir = self.repo_root / "state" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.use_code_cli = use_code_cli

    @staticmethod
    def _load_jsonc(path: Path) -> dict[str, Any]:
        """Load JSON file that may include line comments."""
        raw = path.read_text(encoding="utf-8")
        cleaned = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("//"))
        return json.loads(cleaned)

    @staticmethod
    def _normalize_extension_folder_name(folder_name: str) -> str:
        """Normalize VS Code extension folder names to extension IDs."""
        raw = folder_name.strip().lower()
        if not raw:
            return ""
        # Strip trailing version suffixes: publisher.name-1.2.3 => publisher.name
        raw = re.sub(r"-\d[\w\.\-]*$", "", raw)
        # Accept only canonical extension IDs.
        if ExtensionIntegrator.EXTENSION_ID_RE.match(raw):
            return raw
        return ""

    @classmethod
    def _normalize_extension_id(cls, raw_value: str) -> str:
        """Normalize extension id text from CLI output and discard noise."""
        raw = raw_value.strip().lower()
        if not raw:
            return ""
        return raw if cls.EXTENSION_ID_RE.match(raw) else ""

    def _get_installed_extensions_from_dir(self) -> list[str]:
        user_profile = Path.home()
        windows_profile = Path(os.environ.get("USERPROFILE", ""))
        wsl_home = Path("/mnt/c/Users")
        wsl_profiles = sorted(wsl_home.glob("*/.vscode/extensions")) if wsl_home.exists() else []
        ext_candidates = [
            windows_profile / ".vscode" / "extensions",
            user_profile / ".vscode" / "extensions",
        ]
        ext_candidates.extend(wsl_profiles)
        for ext_dir in ext_candidates:
            if ext_dir.exists():
                values = [
                    self._normalize_extension_folder_name(item.name) for item in ext_dir.iterdir() if item.is_dir()
                ]
                return sorted({v for v in values if v})
        return []

    def get_installed_extensions(self, profile_name: str | None = None) -> list[str]:
        """Get list of installed VS Code extensions."""
        if not self.use_code_cli:
            # No-spawn default: avoid invoking `code` repeatedly in active editor sessions.
            if profile_name:
                return []
            return self._get_installed_extensions_from_dir()
        try:
            cmd = ["code", "--list-extensions"]
            if profile_name:
                cmd.extend(["--profile", profile_name])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            # Some environments emit progress/noise text via stdout/stderr.
            raw_lines = [*result.stdout.splitlines(), *result.stderr.splitlines()]
            values = [
                normalized for normalized in (self._normalize_extension_id(line) for line in raw_lines) if normalized
            ]
            if profile_name:
                return sorted(set(values))
            dir_values = self._get_installed_extensions_from_dir()
            combined = sorted(set(values) | set(dir_values))
            return combined
        except Exception as e:
            print(f"⚠️  Could not list extensions: {e}")
            if profile_name:
                return []
            return self._get_installed_extensions_from_dir()

    def check_recommended_extensions(self) -> dict[str, Any]:
        """Check which recommended extensions are installed."""
        if not self.extensions_json.exists():
            return {"error": "extensions.json not found"}

        data = self._load_jsonc(self.extensions_json)

        recommended = data.get("recommendations", [])
        installed = self.get_installed_extensions()
        installed_lower = [ext.lower() for ext in installed]

        status: dict[str, Any] = {
            "recommended": recommended,
            "installed": [],
            "missing": [],
            "optional_installed": [],
            "optional_missing": [],
        }

        for ext in recommended:
            if ext.lower() in installed_lower:
                status["installed"].append(ext)
            else:
                status["missing"].append(ext)

        # Check optional recommendations
        optional = data.get("optionalRecommendations", [])
        for ext in optional:
            if ext.lower() in installed_lower:
                status["optional_installed"].append(ext)
            else:
                status["optional_missing"].append(ext)

        return status

    def generate_installation_commands(self, missing: list[str]) -> list[str]:
        """Generate VS Code extension installation commands."""
        return [f"code --install-extension {ext}" for ext in missing]

    def update_python_settings(self) -> None:
        """Update Python-specific settings for extensions."""
        if not self.settings_json.exists():
            print("⚠️  settings.json not found")
            return

        with open(self.settings_json, encoding="utf-8") as f:
            settings = json.load(f)

        updates_needed = False

        def resolve_interpreter(path_value: str | None) -> Path | None:
            if not path_value:
                return None
            candidate = Path(path_value)
            if not candidate.is_absolute():
                candidate = self.repo_root / candidate
            return candidate if candidate.exists() else None

        default_interpreter = settings.get("python.defaultInterpreterPath")
        resolved_default = resolve_interpreter(default_interpreter)

        # Prefer a workspace venv path that works on both Windows and Unix.
        venv_candidates = [
            self.repo_root / ".venv",
            self.repo_root / ".venv" / "Scripts" / "python.exe",
            self.repo_root / ".venv" / "bin" / "python",
            self.repo_root / "venv_kilo" / "Scripts" / "python.exe",
            self.repo_root / "venv_kilo" / "bin" / "python",
        ]
        selected_venv = next((p for p in venv_candidates if p.exists()), None)

        if selected_venv and (not default_interpreter or not resolved_default):
            if (self.repo_root / ".venv").exists():
                settings["python.defaultInterpreterPath"] = "${workspaceFolder}/.venv"
            else:
                settings["python.defaultInterpreterPath"] = str(selected_venv).replace("\\", "/")
            updates_needed = True
            print(f"  ✅ Set Python interpreter path to {settings['python.defaultInterpreterPath']}")

        # Ensure Ruff is enabled
        if "ruff.enable" not in settings:
            settings["ruff.enable"] = True
            updates_needed = True
            print("  ✅ Enabled Ruff")

        # Ensure Black formatter is set
        python_settings = settings.get("[python]", {})
        if "editor.defaultFormatter" not in python_settings:
            python_settings["editor.defaultFormatter"] = "ms-python.black-formatter"
            settings["[python]"] = python_settings
            updates_needed = True
            print("  ✅ Set Black as default formatter")

        if updates_needed:
            with open(self.settings_json, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            print("\n💾 Updated settings.json")

    def configure_continue_dev(self) -> None:
        """Configure Continue.dev extension for Ollama."""
        continue_config = self.repo_root / ".continuerc.json"

        if continue_config.exists():
            print("  ✅ Continue.dev config exists")
            return

        # Create basic Continue config for Ollama
        config = {
            "models": [
                {
                    "title": "Qwen 2.5 Coder",
                    "provider": "ollama",
                    "model": "qwen2.5-coder:14b",
                },
                {
                    "title": "StarCoder2",
                    "provider": "ollama",
                    "model": "starcoder2:15b",
                },
            ],
            "tabAutocompleteModel": {
                "title": "StarCoder2 Autocomplete",
                "provider": "ollama",
                "model": "starcoder2:15b",
            },
            "embeddingsProvider": {
                "provider": "ollama",
                "model": "nomic-embed-text",
            },
        }

        with open(continue_config, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print("  ✅ Created Continue.dev configuration")

    def run_integration(self) -> dict[str, Any]:
        """Run full extension integration."""
        print("🔌 VS Code Extension Integration")
        print("=" * 60)

        status = self.check_recommended_extensions()

        print(f"\n📦 Recommended extensions: {len(status['recommended'])}")
        print(f"✅ Installed: {len(status['installed'])}")
        print(f"❌ Missing: {len(status['missing'])}")

        if status["missing"]:
            print("\n🚀 To install missing extensions, run:")
            for cmd in self.generate_installation_commands(status["missing"]):
                print(f"   {cmd}")

        print("\n🔧 Updating settings...")
        self.update_python_settings()

        print("\n🔧 Configuring Continue.dev...")
        self.configure_continue_dev()

        print("\n" + "=" * 60)
        print("✅ Extension integration complete!")

        return status

    def audit_noise(self, channel: str = "Codex", since_minutes: int = 60) -> dict[str, Any]:
        """Run noise-to-hints analysis using existing output inventory tooling."""
        try:
            from src.diagnostics.output_source_inventory import OutputSourceInventory
        except ImportError as exc:
            return {
                "status": "error",
                "error": f"Output source inventory unavailable: {exc}",
            }

        inventory = OutputSourceInventory(repo_root=self.repo_root)
        hints = inventory.hints_report(channel=channel, since_minutes=since_minutes, sample_lines=5000)
        report_path = self.reports_dir / "extension_noise_hints.json"
        report_path.write_text(json.dumps(hints, indent=2), encoding="utf-8")
        return {
            "status": "ok",
            "channel": channel,
            "since_minutes": since_minutes,
            "summary": hints.get("summary", {}),
            "report_path": str(report_path),
        }

    def build_codex_isolation_plan(
        self,
        profile_name: str = "Codex-Isolation",
        codex_extension: str = "openai.chatgpt",
        phase_size: int = 8,
    ) -> dict[str, Any]:
        """Build a phased extension enablement plan centered on Codex stability."""
        installed, scope = self._resolve_extensions_for_profile(profile_name)
        if not installed:
            return {
                "status": "error",
                "error": (
                    f"No installed extensions discovered for profile '{profile_name}'. Ensure `code` CLI is available."
                ),
            }

        phase_size = max(1, phase_size)
        unwanted = self._workspace_unwanted_extensions()
        others = sorted(
            ext for ext in installed if ext.lower() != codex_extension.lower() and ext.lower() not in unwanted
        )
        excluded_unwanted = sorted(ext for ext in installed if ext.lower() in unwanted)

        # Prioritize low-risk utility extensions first, heavy analyzers later.
        heavy_keywords = (
            "semgrep",
            "sonarqube",
            "mypy",
            "ruff",
            "pylint",
            "jupyter",
            "csharp",
            "docker",
            "kubernetes",
            "copilot",
            "cody",
            "typescript",
            "python",
        )
        low_risk = [ext for ext in others if not any(keyword in ext for keyword in heavy_keywords)]
        heavy = [ext for ext in others if any(keyword in ext for keyword in heavy_keywords)]
        ordered = low_risk + heavy

        phases: list[list[str]] = []
        for idx in range(0, len(ordered), phase_size):
            phases.append(ordered[idx : idx + phase_size])

        commands: dict[str, Any] = {
            "prepare_profile": [
                f'code --profile "{profile_name}" --install-extension {codex_extension} --force',
                f'code --profile "{profile_name}" "{self.repo_root}"',
            ],
            "phase_commands": [],
        }
        for i, phase in enumerate(phases, start=1):
            commands["phase_commands"].append(
                {
                    "phase": i,
                    "extensions": phase,
                    "commands": [f'code --profile "{profile_name}" --install-extension {ext} --force' for ext in phase],
                    "verify": [
                        "python nq outputs hints Codex --since 30 --sample-lines 4000",
                        "python nq outputs stale --minutes 60 --idle-minutes 20",
                        "python scripts/verify_tripartite_workspace.py",
                    ],
                }
            )

        plan = {
            "status": "ok",
            "timestamp": self._timestamp(),
            "profile_name": profile_name,
            "profile_scoped": scope == "profile",
            "extension_scope": scope,
            "used_code_cli": self.use_code_cli,
            "codex_extension": codex_extension,
            "installed_total": len(installed),
            "isolation_total": len(others),
            "excluded_unwanted_total": len(excluded_unwanted),
            "excluded_unwanted": excluded_unwanted,
            "phase_size": phase_size,
            "phases": len(phases),
            "commands": commands,
        }
        plan_path = self.reports_dir / "codex_isolation_plan.json"
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        plan["report_path"] = str(plan_path)
        return plan

    def build_quickwins_report(
        self,
        profile_name: str = "Codex-Isolation",
        with_noise: bool = False,
        channel: str = "Codex",
        since_minutes: int = 60,
    ) -> dict[str, Any]:
        """Build immediate extension optimization actions based on known audits."""
        installed, scope = self._resolve_extensions_for_profile(profile_name)
        installed_set = {ext.lower() for ext in installed}

        keep_primary = {
            "anthropic.claude-code",
            "github.copilot",
            "github.copilot-chat",
            "continue.continue",
        }
        redundant_ai = [
            "codeium.codeium",
            "openai.chatgpt",
            "bito.bito",
            "supermaven.supermaven",
            "feiskyer.chatgpt-copilot",
        ]
        redundant_ollama = [
            "10nates.ollama-autocoder",
            "chrisbunting.ollama-code-generator",
            "codeboss.ollama-ai-assistant",
            "desislavarashev.ollama-commit",
            "diegoomal.ollama-connection",
            "wscats.ollama",
        ]
        underutilized_candidates = [
            "fuzionix.devtool-plus",
            "hbenl.vscode-test-explorer",
            "hediet.debug-visualizer",
            "hediet.vscode-drawio",
            "ms-vsliveshare.vsliveshare",
        ]

        found_redundant_ai = sorted(ext for ext in redundant_ai if ext in installed_set)
        found_redundant_ollama = sorted(ext for ext in redundant_ollama if ext in installed_set)
        found_underutilized = sorted(ext for ext in underutilized_candidates if ext in installed_set)

        settings_status = self._workspace_testing_status()
        actions: list[dict[str, Any]] = []

        if found_redundant_ai:
            actions.append(
                {
                    "id": "consolidate_ai_assistants",
                    "priority": "high",
                    "rationale": "Reduce overlapping AI assistants to lower conflict/noise.",
                    "keep": sorted(ext for ext in keep_primary if ext in installed_set),
                    "disable": found_redundant_ai,
                    "commands": [
                        f'code --profile "{profile_name}" --disable-extension {ext}' for ext in found_redundant_ai
                    ],
                }
            )

        if len(found_redundant_ollama) > 1:
            actions.append(
                {
                    "id": "consolidate_ollama_extensions",
                    "priority": "high",
                    "rationale": "Keep one Ollama UI path to avoid duplicated extension behavior.",
                    "disable": found_redundant_ollama,
                    "commands": [
                        f'code --profile "{profile_name}" --disable-extension {ext}' for ext in found_redundant_ollama
                    ],
                }
            )

        if not settings_status["pytest_enabled"]:
            actions.append(
                {
                    "id": "enable_pytest_discovery",
                    "priority": "high",
                    "rationale": "Audit indicates Test Explorer is underutilized due to disabled pytest.",
                    "settings_patch": {
                        "python.testing.pytestEnabled": True,
                        "python.testing.unittestEnabled": False,
                        "python.testing.autoTestDiscoverOnSaveEnabled": True,
                        "python.testing.pytestArgs": ["tests", "-q"],
                    },
                    "recommended_command": "python scripts/start_nusyq.py doctor",
                }
            )

        if found_underutilized:
            recommended_tasks = [
                "python scripts/start_nusyq.py vscode_extensions_quickwins --with-noise",
                "python scripts/extension_monitor.py",
            ]
            for extension_id in found_underutilized:
                recommended_tasks.extend(self._underutilized_extension_tasks(extension_id))
            actions.append(
                {
                    "id": "activate_underutilized_extensions",
                    "priority": "medium",
                    "rationale": "Installed extensions found with high audit value but low operational usage.",
                    "extensions": found_underutilized,
                    "recommended_tasks": recommended_tasks,
                }
            )

        audit_sources = [
            str(path)
            for path in (
                self.repo_root / "docs" / "VSCODE_EXTENSION_AUDIT.md",
                self.repo_root / "docs" / "Analysis" / "extensions" / "EXTENSION_AUDIT_REPORT_20251227.md",
                self.repo_root / "docs" / "Analysis" / "extensions" / "optimization_plan.md",
                self.repo_root / "GIT_AND_EXTENSION_AUDIT.md",
            )
            if path.exists()
        ]

        report: dict[str, Any] = {
            "status": "ok",
            "timestamp": self._timestamp(),
            "profile_name": profile_name,
            "profile_scoped": scope == "profile",
            "extension_scope": scope,
            "used_code_cli": self.use_code_cli,
            "audit_sources": audit_sources,
            "installed_total": len(installed),
            "redundant_ai_detected": found_redundant_ai,
            "redundant_ollama_detected": found_redundant_ollama,
            "underutilized_detected": found_underutilized,
            "workspace_testing_status": settings_status,
            "actions": actions,
        }

        if with_noise:
            report["noise_audit"] = self.audit_noise(channel=channel, since_minutes=since_minutes)

        report_path = self.reports_dir / "vscode_extension_quickwins.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["report_path"] = str(report_path)
        return report

    @staticmethod
    def _underutilized_extension_tasks(extension_id: str) -> list[str]:
        """Return concrete workflow tasks for high-value but quiet extensions."""
        task_map = {
            "fuzionix.devtool-plus": [
                "Open the DevTool+ side panel and pin JSON Editor, Base64 Encoder / Decoder, and UUID Generator",
                "Use DevTool+ for local receipt/log payload transforms instead of external web tools",
                "Use DevTool+ for UUID/hash generation when wiring quests, receipts, and bridge payloads",
            ],
            "hbenl.vscode-test-explorer": [
                "Open the Testing view and run the focused file or cursor-adjacent test before broad sweeps",
                "Use Test Explorer for targeted regression loops instead of rerunning the full suite",
            ],
            "hediet.vscode-drawio": [
                "Keep architecture diagrams in-editor and update draw.io assets when routing or subsystem boundaries change",
                "Use Draw.io for current-state ecosystem maps instead of external diagram tooling",
            ],
            "ms-vsliveshare.vsliveshare": [
                "Use Live Share for paired debugging or review sessions when reproducing editor-only issues",
                "Start collaboration from the existing Live Share keybindings instead of opening ad hoc screen-share tools",
            ],
            "hediet.debug-visualizer": [
                "Open Debug Visualizer during complex state/debug sessions to inspect large structures without manual print churn",
            ],
        }
        return task_map.get(extension_id, [])

    def _workspace_testing_status(self) -> dict[str, Any]:
        if not self.settings_json.exists():
            return {
                "settings_file_exists": False,
                "pytest_enabled": False,
                "pytest_args_configured": False,
                "auto_discovery_enabled": False,
            }

        try:
            settings = self._load_jsonc(self.settings_json)
        except Exception:
            return {
                "settings_file_exists": True,
                "settings_parseable": False,
                "pytest_enabled": False,
                "pytest_args_configured": False,
                "auto_discovery_enabled": False,
            }

        pytest_args = settings.get("python.testing.pytestArgs")
        return {
            "settings_file_exists": True,
            "settings_parseable": True,
            "pytest_enabled": bool(settings.get("python.testing.pytestEnabled", False)),
            "pytest_args_configured": isinstance(pytest_args, list) and len(pytest_args) > 0,
            "auto_discovery_enabled": bool(settings.get("python.testing.autoTestDiscoverOnSaveEnabled", False)),
        }

    def _workspace_unwanted_extensions(self) -> set[str]:
        if not self.extensions_json.exists():
            return set()
        try:
            data = self._load_jsonc(self.extensions_json)
        except Exception:
            return set()
        unwanted = data.get("unwantedRecommendations", [])
        return {str(ext).strip().lower() for ext in unwanted if str(ext).strip()}

    def _resolve_extensions_for_profile(self, profile_name: str) -> tuple[list[str], str]:
        profile_extensions = self.get_installed_extensions(profile_name=profile_name)
        if profile_extensions:
            return profile_extensions, "profile"
        fallback_extensions = self.get_installed_extensions()
        if fallback_extensions:
            return fallback_extensions, "global_fallback"
        return [], "none"

    @staticmethod
    def _timestamp() -> str:
        from datetime import datetime, timezone

        return datetime.now(UTC).isoformat()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="VS Code extension integration + isolation tooling")
    parser.add_argument(
        "--plan-isolation",
        action="store_true",
        help="Generate Codex-first extension isolation plan",
    )
    parser.add_argument(
        "--audit-noise",
        action="store_true",
        help="Run Codex noise audit using nq outputs hints infrastructure",
    )
    parser.add_argument(
        "--quickwins",
        action="store_true",
        help="Generate immediate extension optimization actions from audit guidance",
    )
    parser.add_argument(
        "--with-noise",
        action="store_true",
        help="Include noise audit output when generating quickwins report",
    )
    parser.add_argument(
        "--profile-name",
        default="Codex-Isolation",
        help="Profile name for generated isolation commands",
    )
    parser.add_argument(
        "--phase-size",
        type=int,
        default=8,
        help="How many extensions to add per re-enable phase",
    )
    parser.add_argument(
        "--channel",
        default="Codex",
        help="Output channel label for noise audit integration",
    )
    parser.add_argument(
        "--since-minutes",
        type=int,
        default=60,
        help="Noise audit lookback window in minutes",
    )
    parser.add_argument(
        "--use-code-cli",
        action="store_true",
        help="Allow invoking `code` CLI (may trigger VS Code process interactions).",
    )
    args = parser.parse_args()

    try:
        integrator = ExtensionIntegrator(use_code_cli=args.use_code_cli)
        if args.plan_isolation:
            plan = integrator.build_codex_isolation_plan(
                profile_name=args.profile_name,
                phase_size=args.phase_size,
            )
            print(json.dumps(plan, indent=2))
            return 0 if plan.get("status") == "ok" else 1

        if args.quickwins:
            quickwins = integrator.build_quickwins_report(
                profile_name=args.profile_name,
                with_noise=args.with_noise,
                channel=args.channel,
                since_minutes=args.since_minutes,
            )
            print(json.dumps(quickwins, indent=2))
            return 0 if quickwins.get("status") == "ok" else 1

        if args.audit_noise:
            audit = integrator.audit_noise(channel=args.channel, since_minutes=args.since_minutes)
            print(json.dumps(audit, indent=2))
            return 0 if audit.get("status") == "ok" else 1

        integrator.run_integration()
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
