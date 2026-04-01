"""
Integration tests for medium-term enhancements.
Tests SNS LLM fine-tuning, VS Code UI, cross-repo sync, and performance benchmarking.
"""

import tempfile
from pathlib import Path

from src.ai.sns_llm_fine_tuner import SNSLLMFineTuner, TrainingExample
from src.evaluation.performance_benchmark import (
    BenchmarkResult,
    PerformanceBenchmark,
)
from src.integration.cross_repo_sync import (
    CrossRepoSNSSynchronizer,
    SNSDefinition,
)
from src.ui.vscode_metrics_ui import VSCodeMetricsUI


class TestSNSLLMFineTuner:
    """Test SNS LLM fine-tuning module."""

    def test_training_example_creation(self):
        """Test TrainingExample dataclass."""
        example = TrainingExample(
            input_text="Create a function",
            output_sns="ƒ( )",
            category="aggressive",
            token_savings=65.0,
        )
        assert example.input_text == "Create a function"
        assert example.output_sns == "ƒ( )"
        assert abs(example.token_savings - 65.0) < 0.01

    def test_fine_tuner_initialization(self):
        """Test fine-tuner initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fine_tuner = SNSLLMFineTuner(
                model_name="qwen2.5-coder",
                state_dir=Path(tmpdir),
            )
            assert fine_tuner.model_name == "qwen2.5-coder"
            assert fine_tuner.checkpoint_dir.exists()

    def test_generate_training_data(self):
        """Test training data generation."""
        fine_tuner = SNSLLMFineTuner()
        data = fine_tuner.generate_training_data()

        assert len(data) > 0
        assert all(isinstance(ex, TrainingExample) for ex in data)
        assert any(ex.category == "aggressive" for ex in data)
        assert any(ex.category == "structural" for ex in data)

    def test_prepare_fine_tuning_dataset(self):
        """Test augmented dataset preparation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fine_tuner = SNSLLMFineTuner(state_dir=Path(tmpdir))
            dataset_path = fine_tuner.prepare_fine_tuning_dataset()

            assert Path(dataset_path).exists()
            with open(dataset_path, encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) > 0
                # Should have at least original + variations (3x augmentation)
                assert len(lines) > len(fine_tuner.generate_training_data())

    def test_estimate_training_impact(self):
        """Test impact estimation."""
        fine_tuner = SNSLLMFineTuner()
        impact = fine_tuner.estimate_training_impact()

        assert "total_training_examples" in impact
        assert "avg_token_savings_percent" in impact
        assert impact["avg_token_savings_percent"] > 30
        assert "estimated_cost_savings_yearly" in impact

    def test_create_sns_fine_tuner_factory(self):
        """Test factory function."""
        from src.ai.sns_llm_fine_tuner import create_sns_fine_tuner

        tuner = create_sns_fine_tuner()
        assert isinstance(tuner, SNSLLMFineTuner)


class TestVSCodeMetricsUI:
    """Test VS Code metrics visualization UI."""

    def test_vscode_ui_initialization(self):
        """Test UI initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ui = VSCodeMetricsUI(state_dir=Path(tmpdir))
            assert ui.dashboard is not None

    def test_generate_html_ui(self):
        """Test HTML generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ui = VSCodeMetricsUI(state_dir=Path(tmpdir))
            html = ui.generate_html_ui()

            assert "SNS-Core Metrics Dashboard" in html
            assert "<canvas" in html
            assert "metric-card" in html
            assert "<script" in html

    def test_generate_extension_config(self):
        """Test VS Code extension config generation."""
        ui = VSCodeMetricsUI()
        config = ui.generate_extension_config()

        assert config["name"] == "sns-metrics-dashboard"
        assert "activationEvents" in config
        assert "commands" in config["contributes"]
        assert any("sns-metrics" in cmd["command"] for cmd in config["contributes"]["commands"])

    def test_save_webview_to_file(self):
        """Test saving webview to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            ui = VSCodeMetricsUI(state_dir=Path(tmpdir))
            ui.save_webview_to_file(output_path)

            assert output_path.exists()
            assert "SNS-Core" in output_path.read_text()


class TestCrossRepoSNSSynchronizer:
    """Test cross-repository SNS synchronization."""

    def test_sns_definition_creation(self):
        """Test SNSDefinition dataclass."""
        defn = SNSDefinition(
            symbol="⨳",
            meaning="system boundary",
            category="structural",
            aliases=["system", "scope"],
            token_savings_pct=35.0,
        )
        assert defn.symbol == "⨳"
        assert "system" in defn.aliases

    def test_synchronizer_initialization(self):
        """Test synchronizer initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sync = CrossRepoSNSSynchronizer(
                hub_path=Path(tmpdir) / "hub",
                simverse_path=Path(tmpdir) / "simverse",
                sns_core_path=Path(tmpdir) / "sns_core",
            )
            assert sync.sync_log_file.parent.exists()

    def test_get_sns_definitions(self):
        """Test definition extraction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock SNS-Core symbols file
            sns_core_path = Path(tmpdir) / "sns_core"
            sns_core_path.mkdir()
            symbols_file = sns_core_path / "symbols.md"
            symbols_file.write_text("# Symbol: ⨳\nMeaning: system/scope boundary\n")

            sync = CrossRepoSNSSynchronizer(sns_core_path=sns_core_path)
            defs = sync.get_sns_definitions()

            assert "⨳" in defs
            # Check that the meaning contains expected keywords
            assert "system" in defs["⨳"].meaning or "scope" in defs["⨳"].meaning

    def test_detect_definition_changes(self):
        """Test change detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sync = CrossRepoSNSSynchronizer(hub_path=Path(tmpdir))
            changes = sync.detect_definition_changes()

            assert "added" in changes
            assert "removed" in changes
            assert "modified" in changes
            assert "timestamp" in changes

    def test_create_git_hook(self):
        """Test git hook creation."""
        sync = CrossRepoSNSSynchronizer()
        hook = sync.create_git_hook()

        assert "#!/bin/bash" in hook
        assert "SNS Synchronization" in hook
        assert "propagate_definitions_to_repos" in hook

    def test_generate_sync_report(self):
        """Test sync report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sync = CrossRepoSNSSynchronizer(hub_path=Path(tmpdir))
            report = sync.generate_sync_report()

            assert "timestamp" in report
            assert "total_definitions" in report
            assert "repos_status" in report
            assert "next_steps" in report


class TestPerformanceBenchmark:
    """Test performance benchmarking framework."""

    def test_benchmark_result_creation(self):
        """Test BenchmarkResult dataclass."""
        result = BenchmarkResult(
            test_name="test_1",
            original_text="Create a function",
            sns_output="ƒ( )",
            original_tokens=100,
            sns_tokens=35,
            savings_pct=65.0,
            conversion_time_ms=5.2,
            accuracy_score=95.0,
        )
        assert result.test_name == "test_1"
        assert abs(result.savings_pct - 65.0) < 0.01

    def test_benchmark_initialization(self):
        """Test benchmark framework initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark = PerformanceBenchmark(state_dir=Path(tmpdir))
            assert benchmark.state_dir.exists()

    def test_create_test_dataset(self):
        """Test test dataset creation."""
        benchmark = PerformanceBenchmark()
        dataset = benchmark.create_test_dataset()

        assert "code_generation" in dataset
        assert "documentation" in dataset
        assert "analysis" in dataset
        assert len(dataset["code_generation"]) > 0

    def test_estimate_tokens(self):
        """Test token estimation."""
        benchmark = PerformanceBenchmark()

        # Test token estimation
        short_text = "Hello"
        long_text = "This is a longer text with many words to test token estimation"

        short_tokens = benchmark.estimate_tokens(short_text)
        long_tokens = benchmark.estimate_tokens(long_text)

        assert short_tokens < long_tokens
        assert short_tokens > 0

    def test_benchmark_sns_conversion(self):
        """Test SNS conversion benchmarking."""
        benchmark = PerformanceBenchmark()

        # Mock SNS converter
        def mock_converter(text: str):
            return (f"SNS: {text[:20]}", {"savings": 40})

        results = benchmark.benchmark_sns_conversion(mock_converter)

        assert len(results) > 0
        assert all(isinstance(r, BenchmarkResult) for r in results)
        # Conversion time may be very small but should be >= 0
        assert all(r.conversion_time_ms >= 0 for r in results)

    def test_generate_summary(self):
        """Test summary generation."""
        benchmark = PerformanceBenchmark()

        # Add mock results
        benchmark.results = [
            BenchmarkResult(
                test_name="test_1",
                original_text="text1",
                sns_output="sns1",
                original_tokens=100,
                sns_tokens=40,
                savings_pct=60.0,
                conversion_time_ms=5.0,
                accuracy_score=90.0,
            ),
            BenchmarkResult(
                test_name="test_2",
                original_text="text2",
                sns_output="sns2",
                original_tokens=150,
                sns_tokens=50,
                savings_pct=66.7,
                conversion_time_ms=6.0,
                accuracy_score=95.0,
            ),
        ]

        summary = benchmark.generate_summary()

        assert summary["total_benchmarks"] == 2
        assert summary["avg_savings_pct"] > 0
        assert summary["avg_conversion_time_ms"] > 0
        assert summary["avg_accuracy_score"] > 0

    def test_save_results(self):
        """Test result saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark = PerformanceBenchmark(state_dir=Path(tmpdir))
            benchmark.results = [
                BenchmarkResult(
                    test_name="test",
                    original_text="text",
                    sns_output="sns",
                    original_tokens=100,
                    sns_tokens=40,
                    savings_pct=60.0,
                    conversion_time_ms=5.0,
                    accuracy_score=90.0,
                )
            ]

            benchmark.save_results()

            assert benchmark.results_file.exists()
            assert benchmark.summary_file.exists()

    def test_generate_benchmark_report(self):
        """Test report generation."""
        benchmark = PerformanceBenchmark()
        benchmark.results = [
            BenchmarkResult(
                test_name="code_generation_1",
                original_text="Create a function",
                sns_output="ƒ( )",
                original_tokens=100,
                sns_tokens=35,
                savings_pct=65.0,
                conversion_time_ms=5.0,
                accuracy_score=95.0,
            )
        ]

        report = benchmark.generate_benchmark_report()

        assert "SNS-Core Performance Benchmark Report" in report
        assert "Average Token Savings" in report
        assert "Code Generation" in report


class TestIntegrationMediumTermEnhancements:
    """Integration tests for medium-term enhancements."""

    def test_sns_fine_tuning_workflow(self):
        """Test complete fine-tuning workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fine_tuner = SNSLLMFineTuner(state_dir=Path(tmpdir))

            # Generate training data
            data = fine_tuner.generate_training_data()
            assert len(data) > 0

            # Prepare augmented dataset
            dataset_path = fine_tuner.prepare_fine_tuning_dataset()
            assert Path(dataset_path).exists()

            # Get impact estimation
            impact = fine_tuner.estimate_training_impact()
            assert impact["total_training_examples"] > 0

            # Generate report
            report = fine_tuner.generate_training_report()
            assert report["model"] == "qwen2.5-coder"

    def test_vscode_metrics_workflow(self):
        """Test complete VS Code metrics workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ui = VSCodeMetricsUI(state_dir=Path(tmpdir))

            # Generate UI
            html = ui.generate_html_ui()
            assert html is not None

            # Generate config
            config = ui.generate_extension_config()
            assert config is not None

            # Save to file
            output_file = Path(tmpdir) / "metrics.html"
            ui.save_webview_to_file(output_file)
            assert output_file.exists()

    def test_cross_repo_sync_workflow(self):
        """Test complete synchronization workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sync = CrossRepoSNSSynchronizer(hub_path=Path(tmpdir))

            # Detect changes
            changes = sync.detect_definition_changes()
            assert isinstance(changes, dict)

            # Generate report
            report = sync.generate_sync_report()
            assert "timestamp" in report

    def test_performance_benchmark_workflow(self):
        """Test complete benchmarking workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark = PerformanceBenchmark(state_dir=Path(tmpdir))

            # Create dataset
            dataset = benchmark.create_test_dataset()
            assert len(dataset) > 0

            # Run mock benchmark
            def mock_converter(text: str):
                return (f"SNS: {text[:30]}", {"savings": 40})

            results = benchmark.benchmark_sns_conversion(mock_converter)
            assert len(results) > 0

            # Save results
            benchmark.results = results
            benchmark.save_results()

            assert benchmark.results_file.exists()
            assert benchmark.summary_file.exists()

            # Generate report
            report = benchmark.generate_benchmark_report()
            assert "SNS-Core Performance" in report
