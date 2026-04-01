"""Tests for src/evaluation/performance_benchmark.py — BenchmarkResult, PerformanceBenchmark."""

import pytest


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    @pytest.fixture
    def result(self):
        from src.evaluation.performance_benchmark import BenchmarkResult
        return BenchmarkResult(
            test_name="test_email_validation",
            original_text="Create a function that validates email addresses",
            sns_output="fn: validate_email → bool [email: str]",
            original_tokens=50,
            sns_tokens=12,
            savings_pct=76.0,
            conversion_time_ms=8.5,
            accuracy_score=92.0,
        )

    def test_fields_populated(self, result):
        assert result.test_name == "test_email_validation"
        assert result.original_tokens == 50
        assert result.sns_tokens == 12
        assert result.savings_pct == 76.0
        assert result.accuracy_score == 92.0

    def test_default_model_unknown(self, result):
        assert result.model_used == "unknown"

    def test_timestamp_set(self, result):
        assert result.timestamp is not None
        assert len(result.timestamp) > 0

    def test_to_dict_keys(self, result):
        d = result.to_dict()
        assert "test_name" in d
        assert "original_tokens" in d
        assert "sns_tokens" in d
        assert "savings_pct" in d
        assert "conversion_time_ms" in d
        assert "accuracy_score" in d
        assert "model_used" in d
        assert "timestamp" in d

    def test_to_dict_truncates_long_text(self):
        from src.evaluation.performance_benchmark import BenchmarkResult
        long_text = "X" * 500
        br = BenchmarkResult(
            test_name="t", original_text=long_text, sns_output=long_text,
            original_tokens=100, sns_tokens=20, savings_pct=80.0,
            conversion_time_ms=5.0, accuracy_score=90.0
        )
        d = br.to_dict()
        assert len(d["original_text"]) <= 100
        assert len(d["sns_output"]) <= 100

    def test_to_dict_rounds_floats(self, result):
        d = result.to_dict()
        # savings_pct and accuracy_score should be rounded
        assert isinstance(d["savings_pct"], float)
        assert isinstance(d["accuracy_score"], float)

    def test_custom_model(self):
        from src.evaluation.performance_benchmark import BenchmarkResult
        br = BenchmarkResult(
            test_name="t", original_text="x", sns_output="y",
            original_tokens=10, sns_tokens=5, savings_pct=50.0,
            conversion_time_ms=1.0, accuracy_score=85.0,
            model_used="qwen2.5-coder:14b"
        )
        assert br.model_used == "qwen2.5-coder:14b"


class TestPerformanceBenchmark:
    """Tests for PerformanceBenchmark framework."""

    @pytest.fixture
    def perf_bench(self, tmp_path):
        from src.evaluation.performance_benchmark import PerformanceBenchmark
        return PerformanceBenchmark(state_dir=tmp_path, ollama_url="http://localhost:11434")

    def test_instantiation(self, perf_bench):
        assert perf_bench is not None

    def test_state_dir_created(self, tmp_path):
        from src.evaluation.performance_benchmark import PerformanceBenchmark
        new_dir = tmp_path / "bench_state"
        PerformanceBenchmark(state_dir=new_dir, ollama_url="http://localhost:11434")
        assert new_dir.exists()

    def test_results_empty_on_init(self, perf_bench):
        assert perf_bench.results == []

    def test_create_test_dataset_returns_dict(self, perf_bench):
        dataset = perf_bench.create_test_dataset()
        assert isinstance(dataset, dict)
        assert len(dataset) > 0

    def test_create_test_dataset_has_categories(self, perf_bench):
        dataset = perf_bench.create_test_dataset()
        assert "code_generation" in dataset
        assert isinstance(dataset["code_generation"], list)
        assert len(dataset["code_generation"]) > 0

    def test_results_file_path(self, perf_bench, tmp_path):
        assert perf_bench.results_file == tmp_path / "benchmark_results.jsonl"

    def test_summary_file_path(self, perf_bench, tmp_path):
        assert perf_bench.summary_file == tmp_path / "benchmark_summary.json"

    def test_ollama_url_stored(self, perf_bench):
        assert perf_bench.ollama_url == "http://localhost:11434"


class TestEvaluationPackage:
    """Tests for src/evaluation package."""

    def test_import_benchmark_result(self):
        from src.evaluation.performance_benchmark import BenchmarkResult
        assert BenchmarkResult is not None

    def test_import_performance_benchmark(self):
        from src.evaluation.performance_benchmark import PerformanceBenchmark
        assert PerformanceBenchmark is not None

    def test_import_run_function(self):
        from src.evaluation.performance_benchmark import run_performance_benchmark
        assert run_performance_benchmark is not None
