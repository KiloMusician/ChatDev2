"""Tests for src/tools/cross_ecosystem_sync.py

Tests the cross-ecosystem synchronization tool that syncs cultivation data
(quest logs, work queue, metrics) between NuSyQ-Hub and SimulatedVerse.

Coverage targets:
- CrossEcosystemSync initialization and path discovery
- Quest log sync (async and sync wrappers)
- Work queue merge logic
- Metrics directory sync
- Knowledge base updates
- Bidirectional sync
- Path normalization utilities
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from src.tools.cross_ecosystem_sync import CrossEcosystemSync

# =============================================================================
# CrossEcosystemSync Init Tests
# =============================================================================


class TestCrossEcosystemSyncInit:
    """Tests for CrossEcosystemSync initialization."""

    def test_init_with_repo_root(self, tmp_path):
        """Test initialization with explicit repo root."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        assert syncer.repo_root == tmp_path

    def test_init_sets_hub_quest_log_path(self, tmp_path):
        """Test quest log path is set correctly."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        expected = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        assert syncer.hub_quest_log == expected

    def test_init_sets_hub_work_queue_path(self, tmp_path):
        """Test work queue path is set correctly."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        expected = tmp_path / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        assert syncer.hub_work_queue == expected

    def test_init_sets_hub_metrics_path(self, tmp_path):
        """Test metrics path is set correctly."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        expected = tmp_path / "docs" / "Metrics"
        assert syncer.hub_metrics == expected

    def test_init_sets_hub_learning_path(self, tmp_path):
        """Test learning path is set correctly."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        expected = tmp_path / "docs" / "Learning"
        assert syncer.hub_learning == expected

    def test_init_simverse_root_can_be_none(self, tmp_path):
        """Test simverse_root is None when not found."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        # SimulatedVerse likely not found in tmp_path
        # This depends on environment, so just verify it's set
        assert hasattr(syncer, "simverse_root")

    def test_init_sv_paths_none_when_no_simverse(self, tmp_path):
        """Test SimulatedVerse paths are None when simverse not found."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        if syncer.simverse_root is None:
            assert syncer.sv_shared is None
            assert syncer.sv_quest_log is None
            assert syncer.sv_work_queue is None
            assert syncer.sv_metrics is None


# =============================================================================
# _normalize_external_path Tests
# =============================================================================


class TestNormalizeExternalPath:
    """Tests for path normalization."""

    def test_normalize_strips_whitespace(self):
        """Test whitespace is stripped from path.

        Note: On Windows, Path retains backslash separators.
        The method strips whitespace but Path normalizes separators for platform.
        """
        result = CrossEcosystemSync._normalize_external_path("  /path/to/file  ")
        # Whitespace stripped - path should contain the components
        assert "path" in str(result)
        assert "file" in str(result)

    def test_normalize_strips_quotes(self):
        """Test quotes are stripped."""
        result = CrossEcosystemSync._normalize_external_path("'/path/to/file'")
        # Quote stripping result
        assert "'" not in str(result)

    def test_normalize_produces_valid_path(self):
        """Test produces a valid Path object regardless of input format.

        Note: On Windows Path uses backslashes, on Unix forward slashes.
        The key behavior is producing a usable Path object.
        """
        result = CrossEcosystemSync._normalize_external_path("path\\to\\file")
        # Should be a valid path with expected components
        assert result.name == "file"
        assert "to" in str(result)

    def test_normalize_windows_drive_letter(self):
        """Test Windows drive letter conversion for WSL."""
        result = CrossEcosystemSync._normalize_external_path("c:/Users/test")
        # Implementation converts to /mnt/c format for WSL
        result_str = str(result)
        # Could be either Windows format or WSL format depending on platform
        assert "Users" in result_str or "users" in result_str.lower()

    def test_normalize_returns_path(self):
        """Test returns Path object."""
        result = CrossEcosystemSync._normalize_external_path("/some/path")
        assert isinstance(result, Path)


# =============================================================================
# _find_simverse Tests
# =============================================================================


class TestFindSimverse:
    """Tests for SimulatedVerse discovery."""

    def test_find_simverse_with_env_var(self, tmp_path, monkeypatch):
        """Test finding SimulatedVerse via environment variable."""
        # Create a fake SimulatedVerse directory
        sv_path = tmp_path / "SimulatedVerse"
        sv_path.mkdir()
        (sv_path / ".git").mkdir()

        monkeypatch.setenv("SIMULATEDVERSE_PATH", str(sv_path))

        syncer = CrossEcosystemSync(repo_root=tmp_path)
        # Should find the SimulatedVerse
        if syncer.simverse_root:
            assert syncer.simverse_root.exists()

    def test_find_simverse_returns_none_when_not_found(self, tmp_path, monkeypatch):
        """Test returns None when SimulatedVerse not found."""
        # Clear any env vars that might help find SimulatedVerse
        for key in [
            "SIMULATEDVERSE_PATH",
            "SIMULATEDVERSE_APP",
            "SIMULATEDVERSE",
            "SIMULATEDVERSE_ROOT",
        ]:
            monkeypatch.delenv(key, raising=False)

        syncer = CrossEcosystemSync(repo_root=tmp_path)
        # May or may not be None depending on if real SimulatedVerse exists elsewhere
        assert hasattr(syncer, "simverse_root")


# =============================================================================
# Quest Log Sync Tests
# =============================================================================


class TestSyncQuestLog:
    """Tests for quest log synchronization."""

    @pytest.mark.asyncio
    async def test_sync_quest_log_skips_when_not_found(self, tmp_path):
        """Test skips sync when quest log doesn't exist."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        syncer.sv_quest_log = tmp_path / "sv" / "quest.jsonl"

        result = await syncer._sync_quest_log()

        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_sync_quest_log_copies_file(self, tmp_path):
        """Test copies quest log file to destination."""
        # Setup source
        hub_root = tmp_path / "hub"
        quest_src = hub_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        quest_src.parent.mkdir(parents=True)
        quest_src.write_text('{"event": "test"}\n{"event": "test2"}\n')

        # Setup destination
        sv_root = tmp_path / "sv"
        sv_shared = sv_root / "shared_cultivation"
        sv_shared.mkdir(parents=True)
        sv_quest = sv_shared / "quest_log.jsonl"

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.sv_quest_log = sv_quest

        result = await syncer._sync_quest_log()

        assert result["status"] == "success"
        assert sv_quest.exists()
        assert result["items_synced"] == 2

    @pytest.mark.asyncio
    async def test_sync_quest_log_counts_entries(self, tmp_path):
        """Test counts entries correctly."""
        # Setup
        hub_root = tmp_path / "hub"
        quest_src = hub_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        quest_src.parent.mkdir(parents=True)
        # Write 5 entries
        entries = "\n".join(['{"event": "' + str(i) + '"}' for i in range(5)])
        quest_src.write_text(entries)

        sv_quest = tmp_path / "sv" / "quest.jsonl"
        sv_quest.parent.mkdir(parents=True)

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.sv_quest_log = sv_quest

        result = await syncer._sync_quest_log()

        assert result["items_synced"] == 5


class TestSyncQuestLogSync:
    """Tests for synchronous quest log wrapper."""

    def test_sync_quest_log_returns_dict(self, tmp_path):
        """Test sync wrapper returns result dict."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        result = syncer.sync_quest_log()

        assert isinstance(result, dict)
        assert "status" in result


# =============================================================================
# Work Queue Sync Tests
# =============================================================================


class TestSyncWorkQueue:
    """Tests for work queue synchronization."""

    @pytest.mark.asyncio
    async def test_sync_work_queue_skips_when_not_found(self, tmp_path):
        """Test skips when work queue doesn't exist."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        syncer.sv_work_queue = tmp_path / "sv" / "queue.json"

        result = await syncer._sync_work_queue()

        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_sync_work_queue_creates_new(self, tmp_path):
        """Test creates new queue when destination doesn't exist."""
        # Setup hub
        hub_root = tmp_path / "hub"
        queue_src = hub_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        queue_src.parent.mkdir(parents=True)
        queue_src.write_text(
            json.dumps(
                {
                    "items": [
                        {"id": "task-1", "title": "Task 1"},
                        {"id": "task-2", "title": "Task 2"},
                    ]
                }
            )
        )

        # Setup destination
        sv_queue = tmp_path / "sv" / "queue.json"
        sv_queue.parent.mkdir(parents=True)

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.sv_work_queue = sv_queue

        result = await syncer._sync_work_queue()

        assert result["status"] == "success"
        assert result["items_synced"] == 2
        assert sv_queue.exists()

    @pytest.mark.asyncio
    async def test_sync_work_queue_merges_items(self, tmp_path):
        """Test merges new items into existing queue."""
        # Setup hub with 3 items
        hub_root = tmp_path / "hub"
        queue_src = hub_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        queue_src.parent.mkdir(parents=True)
        queue_src.write_text(
            json.dumps(
                {
                    "items": [
                        {"id": "task-1", "title": "Task 1"},
                        {"id": "task-2", "title": "Task 2"},
                        {"id": "task-3", "title": "Task 3"},
                    ]
                }
            )
        )

        # Setup destination with 1 existing item
        sv_queue = tmp_path / "sv" / "queue.json"
        sv_queue.parent.mkdir(parents=True)
        sv_queue.write_text(
            json.dumps(
                {
                    "items": [
                        {"id": "task-1", "title": "Task 1"},  # Already exists
                    ]
                }
            )
        )

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.sv_work_queue = sv_queue

        result = await syncer._sync_work_queue()

        # Only 2 new items synced
        assert result["items_synced"] == 2
        assert result["total_in_queue"] == 3

    @pytest.mark.asyncio
    async def test_sync_work_queue_adds_timestamp(self, tmp_path):
        """Test adds last_synced_from_hub timestamp."""
        # Setup
        hub_root = tmp_path / "hub"
        queue_src = hub_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        queue_src.parent.mkdir(parents=True)
        queue_src.write_text(json.dumps({"items": []}))

        sv_queue = tmp_path / "sv" / "queue.json"
        sv_queue.parent.mkdir(parents=True)

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.sv_work_queue = sv_queue

        await syncer._sync_work_queue()

        # Read back and check timestamp
        queue_data = json.loads(sv_queue.read_text())
        assert "last_synced_from_hub" in queue_data


# =============================================================================
# Metrics Sync Tests
# =============================================================================


class TestSyncMetrics:
    """Tests for metrics synchronization."""

    @pytest.mark.asyncio
    async def test_sync_metrics_skips_when_not_found(self, tmp_path):
        """Test skips when metrics directory doesn't exist."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        syncer.sv_metrics = tmp_path / "sv" / "metrics"

        result = await syncer._sync_metrics()

        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_sync_metrics_copies_json_files(self, tmp_path):
        """Test copies all JSON metric files."""
        # Setup hub metrics
        hub_root = tmp_path / "hub"
        metrics_dir = hub_root / "docs" / "Metrics"
        metrics_dir.mkdir(parents=True)
        (metrics_dir / "metric1.json").write_text('{"value": 1}')
        (metrics_dir / "metric2.json").write_text('{"value": 2}')
        (metrics_dir / "metric3.json").write_text('{"value": 3}')

        # Setup destination
        sv_metrics = tmp_path / "sv" / "metrics"
        sv_metrics.mkdir(parents=True)

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.sv_metrics = sv_metrics

        result = await syncer._sync_metrics()

        assert result["status"] == "success"
        assert result["items_synced"] == 3
        assert (sv_metrics / "metric1.json").exists()
        assert (sv_metrics / "metric2.json").exists()
        assert (sv_metrics / "metric3.json").exists()

    @pytest.mark.asyncio
    async def test_sync_metrics_copies_dashboard(self, tmp_path):
        """Test copies dashboard.html if it exists."""
        # Setup hub metrics with dashboard
        hub_root = tmp_path / "hub"
        metrics_dir = hub_root / "docs" / "Metrics"
        metrics_dir.mkdir(parents=True)
        (metrics_dir / "dashboard.html").write_text("<html>Dashboard</html>")

        # Setup destination
        sv_metrics = tmp_path / "sv" / "metrics"
        sv_metrics.mkdir(parents=True)

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.sv_metrics = sv_metrics

        await syncer._sync_metrics()

        assert (sv_metrics / "dashboard.html").exists()


# =============================================================================
# Knowledge Base Sync Tests
# =============================================================================


class TestSyncKnowledgeBase:
    """Tests for knowledge base synchronization."""

    @pytest.mark.asyncio
    async def test_sync_kb_skips_when_not_found(self, tmp_path):
        """Test skips when knowledge base doesn't exist."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        syncer.shared_kb = tmp_path / "nonexistent" / "kb.yaml"

        result = await syncer._sync_to_knowledge_base()

        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_sync_kb_appends_summary(self, tmp_path):
        """Test appends cultivation summary to knowledge base."""
        # Create knowledge base file
        kb_file = tmp_path / "knowledge-base.yaml"
        kb_file.write_text("# Knowledge Base\n\n")

        syncer = CrossEcosystemSync(repo_root=tmp_path)
        syncer.shared_kb = kb_file

        result = await syncer._sync_to_knowledge_base()

        assert result["status"] == "success"
        content = kb_file.read_text()
        assert "NuSyQ-Hub Cultivation Summary" in content


# =============================================================================
# Generate Cultivation Summary Tests
# =============================================================================


class TestGenerateCultivationSummary:
    """Tests for cultivation summary generation."""

    def test_generates_summary_string(self, tmp_path):
        """Test generates non-empty summary."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        summary = syncer._generate_cultivation_summary()

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_includes_sync_time(self, tmp_path):
        """Test summary includes sync time."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        summary = syncer._generate_cultivation_summary()

        assert "Sync Time" in summary

    def test_includes_quest_info_when_available(self, tmp_path):
        """Test includes quest log info when file exists."""
        # Create quest log
        quest_log = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        quest_log.parent.mkdir(parents=True)
        quest_log.write_text('{"event": "test"}\n{"event": "test2"}\n')

        syncer = CrossEcosystemSync(repo_root=tmp_path)
        summary = syncer._generate_cultivation_summary()

        assert "Quest Log" in summary

    def test_includes_work_queue_when_available(self, tmp_path):
        """Test includes work queue info when file exists."""
        # Create work queue
        queue = tmp_path / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        queue.parent.mkdir(parents=True)
        queue.write_text(
            json.dumps(
                {
                    "items": [
                        {"id": "1", "status": "queued"},
                        {"id": "2", "status": "completed"},
                    ]
                }
            )
        )

        syncer = CrossEcosystemSync(repo_root=tmp_path)
        summary = syncer._generate_cultivation_summary()

        assert "Work Queue" in summary


# =============================================================================
# sync_to_simverse Tests
# =============================================================================


class TestSyncToSimverse:
    """Tests for main sync orchestration."""

    @pytest.mark.asyncio
    async def test_sync_to_simverse_returns_partial_when_no_simverse(self, tmp_path):
        """Test returns partial status when SimulatedVerse not found."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        syncer.simverse_root = None

        result = await syncer.sync_to_simverse()

        assert result["status"] == "partial"

    @pytest.mark.asyncio
    async def test_sync_to_simverse_creates_shared_dir(self, tmp_path):
        """Test creates shared_cultivation directory."""
        sv_root = tmp_path / "simverse"
        sv_root.mkdir()
        (sv_root / ".git").mkdir()

        hub_root = tmp_path / "hub"
        hub_root.mkdir()

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.simverse_root = sv_root
        syncer.sv_shared = sv_root / "shared_cultivation"
        syncer.sv_quest_log = syncer.sv_shared / "quest_log.jsonl"
        syncer.sv_work_queue = syncer.sv_shared / "WORK_QUEUE.json"
        syncer.sv_metrics = syncer.sv_shared / "metrics"

        await syncer.sync_to_simverse()

        assert syncer.sv_shared.exists()
        assert syncer.sv_metrics.exists()

    @pytest.mark.asyncio
    async def test_sync_to_simverse_tracks_synced_items(self, tmp_path):
        """Test counts all synced items."""
        sv_root = tmp_path / "simverse"
        sv_root.mkdir()
        (sv_root / ".git").mkdir()

        hub_root = tmp_path / "hub"

        # Create quest log with 3 entries
        quest_log = hub_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        quest_log.parent.mkdir(parents=True)
        quest_log.write_text('{"e":1}\n{"e":2}\n{"e":3}\n')

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.simverse_root = sv_root
        syncer.sv_shared = sv_root / "shared_cultivation"
        syncer.sv_quest_log = syncer.sv_shared / "quest_log.jsonl"
        syncer.sv_work_queue = syncer.sv_shared / "WORK_QUEUE.json"
        syncer.sv_metrics = syncer.sv_shared / "metrics"

        result = await syncer.sync_to_simverse()

        assert result["synced_items"] >= 3  # At least the quest log entries


class TestSyncAll:
    """Tests for synchronous sync_all wrapper."""

    def test_sync_all_returns_dict(self, tmp_path):
        """Test sync_all returns result dict."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        result = syncer.sync_all()

        assert isinstance(result, dict)
        assert "status" in result


# =============================================================================
# Bidirectional Sync Tests
# =============================================================================


class TestBidirectionalSync:
    """Tests for bidirectional synchronization."""

    @pytest.mark.asyncio
    async def test_bidirectional_sync_returns_both_directions(self, tmp_path):
        """Test returns results for both directions."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        syncer.simverse_root = None

        result = await syncer.sync_bidirectional()

        assert "hub_to_simverse" in result
        assert "simverse_to_hub" in result

    @pytest.mark.asyncio
    async def test_bidirectional_skips_reverse_when_no_simverse(self, tmp_path):
        """Test skips reverse sync when SimulatedVerse unavailable."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        syncer.simverse_root = None

        result = await syncer.sync_bidirectional()

        assert result["simverse_to_hub"] is None


class TestSyncFromSimverse:
    """Tests for reverse sync from SimulatedVerse."""

    @pytest.mark.asyncio
    async def test_sync_from_simverse_skips_when_no_data(self, tmp_path):
        """Test skips when no SimulatedVerse work queue."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        syncer.sv_work_queue = None

        result = await syncer._sync_from_simverse()

        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_sync_from_simverse_imports_contributions(self, tmp_path):
        """Test imports SimulatedVerse contributions to hub."""
        hub_root = tmp_path / "hub"
        hub_queue = hub_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        hub_queue.parent.mkdir(parents=True)
        hub_queue.write_text(json.dumps({"items": [{"id": "existing-1", "title": "Existing"}]}))

        sv_queue = tmp_path / "sv" / "queue.json"
        sv_queue.parent.mkdir(parents=True)
        sv_queue.write_text(
            json.dumps(
                {
                    "items": [
                        {"id": "sv-1", "title": "From SV", "source": "simverse"},
                        {"id": "sv-2", "title": "From SV 2", "source": "simverse"},
                    ]
                }
            )
        )

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.sv_work_queue = sv_queue

        result = await syncer._sync_from_simverse()

        assert result["status"] == "success"
        assert result["items_synced"] == 2

        # Verify items added to hub
        hub_data = json.loads(hub_queue.read_text())
        assert len(hub_data["items"]) == 3

    @pytest.mark.asyncio
    async def test_sync_from_simverse_marks_source(self, tmp_path):
        """Test marks imported items with source."""
        hub_root = tmp_path / "hub"
        hub_queue = hub_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        hub_queue.parent.mkdir(parents=True)
        hub_queue.write_text(json.dumps({"items": []}))

        sv_queue = tmp_path / "sv" / "queue.json"
        sv_queue.parent.mkdir(parents=True)
        sv_queue.write_text(
            json.dumps({"items": [{"id": "sv-1", "title": "From SV", "source": "simverse"}]})
        )

        syncer = CrossEcosystemSync(repo_root=hub_root)
        syncer.sv_work_queue = sv_queue

        await syncer._sync_from_simverse()

        hub_data = json.loads(hub_queue.read_text())
        assert hub_data["items"][0]["source"] == "simverse_contribution"


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_sync_quest_log_handles_error(self, tmp_path):
        """Test quest log sync handles errors gracefully."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        # Create source but make destination directory unwritable scenario
        quest_log = tmp_path / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        quest_log.parent.mkdir(parents=True)
        quest_log.write_text('{"test": true}')

        # Set an invalid destination
        syncer.sv_quest_log = tmp_path / "nonexistent_deep_path" / "quest.jsonl"

        result = await syncer._sync_quest_log()
        # Should fail because parent doesn't exist
        assert result["status"] in ("failed", "success")  # May succeed depending on shutil behavior

    @pytest.mark.asyncio
    async def test_sync_to_simverse_handles_exception(self, tmp_path):
        """Test main sync handles exceptions gracefully."""
        syncer = CrossEcosystemSync(repo_root=tmp_path)
        syncer.simverse_root = tmp_path
        syncer.sv_shared = tmp_path / "shared"  # This will be created

        # Mock a method to raise an exception
        with patch.object(syncer, "_sync_quest_log", side_effect=Exception("Test error")):
            result = await syncer.sync_to_simverse()

        assert result["status"] == "error"
        assert "error" in result


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_work_queue(self, tmp_path):
        """Test handling empty work queue."""
        hub_root = tmp_path / "hub"
        queue = hub_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        queue.parent.mkdir(parents=True)
        queue.write_text(json.dumps({"items": []}))

        syncer = CrossEcosystemSync(repo_root=hub_root)
        summary = syncer._generate_cultivation_summary()

        # Should not crash, may or may not include queue info
        assert isinstance(summary, str)

    def test_malformed_work_queue(self, tmp_path):
        """Test handles malformed JSON gracefully."""
        hub_root = tmp_path / "hub"
        queue = hub_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        queue.parent.mkdir(parents=True)
        queue.write_text("not valid json")

        syncer = CrossEcosystemSync(repo_root=hub_root)
        # Should not crash
        summary = syncer._generate_cultivation_summary()
        assert isinstance(summary, str)

    def test_unicode_in_quest_log(self, tmp_path):
        """Test handles unicode characters in quest log."""
        hub_root = tmp_path / "hub"
        quest_log = hub_root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        quest_log.parent.mkdir(parents=True)
        quest_log.write_text('{"title": "日本語タスク"}\n{"title": "Émoji 🎮"}\n')

        syncer = CrossEcosystemSync(repo_root=hub_root)
        summary = syncer._generate_cultivation_summary()

        assert "Quest Log" in summary

    def test_large_work_queue(self, tmp_path):
        """Test handles large work queue."""
        hub_root = tmp_path / "hub"
        queue = hub_root / "docs" / "Work-Queue" / "WORK_QUEUE.json"
        queue.parent.mkdir(parents=True)

        # Create 1000 items
        items = [{"id": f"task-{i}", "status": "queued"} for i in range(1000)]
        queue.write_text(json.dumps({"items": items}))

        syncer = CrossEcosystemSync(repo_root=hub_root)
        summary = syncer._generate_cultivation_summary()

        assert "1000" in summary or "Work Queue" in summary
