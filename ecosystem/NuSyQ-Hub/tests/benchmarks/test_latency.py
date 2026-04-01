"""Latency benchmarks for NuSyQ Hub key operations."""

import os
import sys
import time
from pathlib import Path

import pytest
from src.ai.ollama_hub import ollama_hub

# Opt-out by default to avoid slow network-dependent benchmarks when Ollama is not running.
if os.environ.get("NUSYQ_ENABLE_OLLAMA_BENCH", "").lower() not in {
    "1",
    "true",
    "yes",
    "on",
}:
    pytest.skip(
        "Ollama latency benchmarks are disabled by default. Set NUSYQ_ENABLE_OLLAMA_BENCH=1 to run.",
        allow_module_level=True,
    )

# Ensure ai package from src is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def dummy_task():
    """Simple task to simulate work for benchmarking."""
    time.sleep(0.01)
    # no explicit return — benchmark will capture None


def test_model_load_latency(benchmark):
    """Measure time to load a model using the Ollama hub."""
    if not ollama_hub.ollama.is_available():
        pytest.skip("Ollama service not available; skipping latency benchmark")

    result = benchmark(ollama_hub.load_model, "dummy-model")
    assert result is True


def test_task_execution_latency(benchmark):
    """Measure time to execute a dummy task."""
    result = benchmark(dummy_task)
    # dummy_task doesn't return a value; ensure benchmark ran
    assert result is None
