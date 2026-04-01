"""Tests for src/integration/cross_repo_sync.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.integration.cross_repo_sync import CrossRepoSNSSynchronizer, SNSDefinition


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_sync(tmp_path: Path) -> CrossRepoSNSSynchronizer:
    """Return a synchronizer wired entirely to tmp_path."""
    hub = tmp_path / "hub"
    simverse = tmp_path / "simverse"
    sns_core = tmp_path / "sns_core"
    for d in (hub, simverse, sns_core):
        d.mkdir(parents=True, exist_ok=True)
    (hub / "state").mkdir(parents=True, exist_ok=True)
    return CrossRepoSNSSynchronizer(
        hub_path=hub,
        simverse_path=simverse,
        sns_core_path=sns_core,
    )


# ---------------------------------------------------------------------------
# TestSNSDefinitionDataclass
# ---------------------------------------------------------------------------


class TestSNSDefinitionDataclass:
    def test_required_fields(self) -> None:
        defn = SNSDefinition(symbol="⨳", meaning="boundary", category="structural")
        assert defn.symbol == "⨳"
        assert defn.meaning == "boundary"
        assert defn.category == "structural"

    def test_optional_defaults(self) -> None:
        defn = SNSDefinition(symbol="→", meaning="flow", category="flow")
        assert defn.aliases == []
        assert defn.usage_example == ""
        assert defn.token_savings_pct == 0.0
        assert defn.checksum == ""

    def test_aliases_are_independent_per_instance(self) -> None:
        a = SNSDefinition(symbol="A", meaning="a", category="c")
        b = SNSDefinition(symbol="B", meaning="b", category="c")
        a.aliases.append("alpha")
        assert b.aliases == [], "default_factory must give independent lists"

    def test_compute_checksum_returns_hex_string(self) -> None:
        defn = SNSDefinition(symbol="⨳", meaning="boundary", category="structural")
        cs = defn.compute_checksum()
        assert isinstance(cs, str)
        assert len(cs) == 64  # SHA-256 hex digest

    def test_compute_checksum_is_deterministic(self) -> None:
        defn = SNSDefinition(symbol="⨳", meaning="boundary", category="structural")
        assert defn.compute_checksum() == defn.compute_checksum()

    def test_compute_checksum_differs_on_different_content(self) -> None:
        a = SNSDefinition(symbol="A", meaning="alpha", category="structural")
        b = SNSDefinition(symbol="B", meaning="beta", category="structural")
        assert a.compute_checksum() != b.compute_checksum()

    def test_full_field_construction(self) -> None:
        defn = SNSDefinition(
            symbol="→",
            meaning="flow direction",
            category="flow",
            aliases=["->", "arrow"],
            usage_example="A → B means A flows to B",
            token_savings_pct=42.5,
            checksum="abc123",
        )
        assert defn.aliases == ["->", "arrow"]
        assert defn.usage_example == "A → B means A flows to B"
        assert defn.token_savings_pct == 42.5
        assert defn.checksum == "abc123"


# ---------------------------------------------------------------------------
# TestCrossRepoSNSSynchronizerInit
# ---------------------------------------------------------------------------


class TestCrossRepoSNSSynchronizerInit:
    def test_paths_are_set(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        assert sync.hub_path == tmp_path / "hub"
        assert sync.simverse_path == tmp_path / "simverse"
        assert sync.sns_core_path == tmp_path / "sns_core"

    def test_sync_log_file_parent_created(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        assert sync.sync_log_file.parent.exists()

    def test_definitions_file_path(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        assert sync.definitions_file.name == "sns_definitions.json"
        assert sync.definitions_file.parent == tmp_path / "hub" / "state"


# ---------------------------------------------------------------------------
# TestGetSNSDefinitions
# ---------------------------------------------------------------------------


class TestGetSNSDefinitions:
    def test_returns_empty_when_no_files(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        defs = sync.get_sns_definitions()
        assert isinstance(defs, dict)
        assert len(defs) == 0

    def test_parses_symbols_md(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        symbols_md = tmp_path / "sns_core" / "symbols.md"
        symbols_md.write_text(
            "# Symbol: ⨳\nMeaning: scope boundary\n\n# Symbol: →\nMeaning: data flow\n"
        )
        defs = sync.get_sns_definitions()
        assert "⨳" in defs
        assert defs["⨳"].meaning == "scope boundary"
        assert defs["⨳"].category == "structural"
        assert "→" in defs

    def test_parsed_definitions_are_sns_definition_instances(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        symbols_md = tmp_path / "sns_core" / "symbols.md"
        symbols_md.write_text("# Symbol: X\nMeaning: test symbol\n")
        defs = sync.get_sns_definitions()
        assert isinstance(defs["X"], SNSDefinition)


# ---------------------------------------------------------------------------
# TestDetectDefinitionChanges
# ---------------------------------------------------------------------------


class TestDetectDefinitionChanges:
    def test_all_added_when_no_previous_file(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        symbols_md = tmp_path / "sns_core" / "symbols.md"
        symbols_md.write_text("# Symbol: ⨳\nMeaning: boundary\n")
        changes = sync.detect_definition_changes()
        assert isinstance(changes["added"], list)
        assert any(c["symbol"] == "⨳" for c in changes["added"])

    def test_removed_when_symbol_disappears(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        # Seed previous definitions file
        prev = {
            "definitions": {
                "⨳": {
                    "symbol": "⨳",
                    "meaning": "old",
                    "category": "structural",
                    "aliases": [],
                    "usage_example": "",
                    "token_savings_pct": 0.0,
                    "checksum": "",
                }
            }
        }
        sync.definitions_file.write_text(json.dumps(prev))
        # No symbols.md → current_defs is empty
        changes = sync.detect_definition_changes()
        assert any(c["symbol"] == "⨳" for c in changes["removed"])

    def test_modified_detected(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        prev = {
            "definitions": {
                "⨳": {
                    "symbol": "⨳",
                    "meaning": "old meaning",
                    "category": "structural",
                    "aliases": [],
                    "usage_example": "",
                    "token_savings_pct": 0.0,
                    "checksum": "",
                }
            }
        }
        sync.definitions_file.write_text(json.dumps(prev))
        symbols_md = tmp_path / "sns_core" / "symbols.md"
        symbols_md.write_text("# Symbol: ⨳\nMeaning: new meaning\n")
        changes = sync.detect_definition_changes()
        assert len(changes["modified"]) == 1
        assert changes["modified"][0]["old_meaning"] == "old meaning"
        assert changes["modified"][0]["new_meaning"] == "new meaning"

    def test_changes_dict_has_timestamp(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        changes = sync.detect_definition_changes()
        assert "timestamp" in changes
        assert isinstance(changes["timestamp"], str)

    def test_no_changes_when_identical(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        prev = {
            "definitions": {
                "⨳": {
                    "symbol": "⨳",
                    "meaning": "boundary",
                    "category": "structural",
                    "aliases": [],
                    "usage_example": "",
                    "token_savings_pct": 0.0,
                    "checksum": "",
                }
            }
        }
        sync.definitions_file.write_text(json.dumps(prev))
        symbols_md = tmp_path / "sns_core" / "symbols.md"
        symbols_md.write_text("# Symbol: ⨳\nMeaning: boundary\n")
        changes = sync.detect_definition_changes()
        assert changes["added"] == []
        assert changes["modified"] == []
        assert changes["removed"] == []


# ---------------------------------------------------------------------------
# TestSaveDefinitionsToFile
# ---------------------------------------------------------------------------


class TestSaveDefinitionsToFile:
    def test_saves_json_file(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        defn = SNSDefinition(symbol="⨳", meaning="boundary", category="structural")
        sync._save_definitions_to_file({"⨳": defn})
        assert sync.definitions_file.exists()
        data = json.loads(sync.definitions_file.read_text())
        assert "definitions" in data
        assert "⨳" in data["definitions"]

    def test_saved_data_includes_all_fields(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        defn = SNSDefinition(
            symbol="→",
            meaning="flow",
            category="flow",
            aliases=["arrow"],
            usage_example="A→B",
            token_savings_pct=50.0,
        )
        sync._save_definitions_to_file({"→": defn})
        data = json.loads(sync.definitions_file.read_text())
        entry = data["definitions"]["→"]
        assert entry["meaning"] == "flow"
        assert entry["aliases"] == ["arrow"]
        assert entry["token_savings_pct"] == 50.0


# ---------------------------------------------------------------------------
# TestUpdateSNSCoreSymbols
# ---------------------------------------------------------------------------


class TestUpdateSNSCoreSymbols:
    def test_creates_symbols_md(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        defn = SNSDefinition(symbol="⨳", meaning="boundary", category="structural")
        sync._update_sns_core_symbols({"⨳": defn})
        symbols_file = tmp_path / "sns_core" / "symbols.md"
        assert symbols_file.exists()
        content = symbols_file.read_text()
        assert "⨳" in content
        assert "boundary" in content

    def test_symbols_md_includes_example_when_set(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        defn = SNSDefinition(
            symbol="⨳",
            meaning="boundary",
            category="structural",
            usage_example="⨳system⨳",
        )
        sync._update_sns_core_symbols({"⨳": defn})
        content = (tmp_path / "sns_core" / "symbols.md").read_text()
        assert "⨳system⨳" in content


# ---------------------------------------------------------------------------
# TestUpdateSimverse
# ---------------------------------------------------------------------------


class TestUpdateSimverse:
    def test_creates_config_json(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        defn = SNSDefinition(symbol="⨳", meaning="boundary", category="structural")
        sync._update_simverse({"⨳": defn})
        config_file = tmp_path / "simverse" / "config" / "sns_definitions.json"
        assert config_file.exists()
        data = json.loads(config_file.read_text())
        assert "definitions" in data
        assert any(d["symbol"] == "⨳" for d in data["definitions"])


# ---------------------------------------------------------------------------
# TestCreateGitHook
# ---------------------------------------------------------------------------


class TestCreateGitHook:
    def test_returns_string(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        hook = sync.create_git_hook()
        assert isinstance(hook, str)

    def test_hook_contains_shebang(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        hook = sync.create_git_hook()
        assert hook.strip().startswith("#!/bin/bash")

    def test_hook_references_synchronizer(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        hook = sync.create_git_hook()
        assert "CrossRepoSNSSynchronizer" in hook


# ---------------------------------------------------------------------------
# TestGenerateSyncReport
# ---------------------------------------------------------------------------


class TestGenerateSyncReport:
    def test_report_has_expected_keys(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        report = sync.generate_sync_report()
        for key in ("timestamp", "total_definitions", "recent_changes", "repos_status", "next_steps"):
            assert key in report, f"missing key: {key}"

    def test_repos_status_reflects_existence(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        report = sync.generate_sync_report()
        # hub, simverse, sns_core dirs were created in _make_sync
        assert report["repos_status"]["nusyq-hub"] is True
        assert report["repos_status"]["simulated-verse"] is True
        assert report["repos_status"]["sns-core"] is True

    def test_total_definitions_zero_when_empty(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        report = sync.generate_sync_report()
        assert report["total_definitions"] == 0

    def test_recent_changes_counts_are_ints(self, tmp_path: Path) -> None:
        sync = _make_sync(tmp_path)
        report = sync.generate_sync_report()
        rc = report["recent_changes"]
        assert isinstance(rc["added"], int)
        assert isinstance(rc["modified"], int)
        assert isinstance(rc["removed"], int)


# ---------------------------------------------------------------------------
# TestPackageImport
# ---------------------------------------------------------------------------


class TestPackageImport:
    def test_module_importable(self) -> None:
        import src.integration.cross_repo_sync as m

        assert hasattr(m, "CrossRepoSNSSynchronizer")
        assert hasattr(m, "SNSDefinition")

    def test_integration_package_importable(self) -> None:
        import src.integration
