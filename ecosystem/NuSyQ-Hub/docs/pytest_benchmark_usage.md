# PyTest-Benchmark Usage & Coverage

`pytest-benchmark` (third item on our dependency inventory) keeps our performance expectations explicit: it lets us measure latency for mission-critical orchestration flows while giving us flags to skip expensive runs during CI. Here are the touchpoints that make the dependency earn its place.

## Where we use it

- `tests/benchmarks/test_latency.py` depends on the `benchmark` fixture for latency hops (model loading via `src.ai.ollama_hub`, dummy task timing). The file respects `NUSYQ_ENABLE_OLLAMA_BENCH=1` before running to avoid hitting the Ollama cluster unless explicitly permitted.  
- `tests/smoke/test_critical_paths.py` defines a `TestPerformance` class with two benchmarks (`benchmark(GuildBoard)`, `benchmark(load_inventory)`), but the entire class sits behind a commented `@pytest.mark.performance` because we only want those benchmarks on demand (not on every CI run).  
- `tests/test_medium_term_enhancements.py` exercises `PerformanceBenchmark` (from `src/evaluation/performance_benchmark.py`), showing the same benchmark data structures we later report in `docs/benchmark_reports/`.  
- `tests/conftest.py` currently suppresses the plugin (`pytest_plugins = []`) to avoid PytestBenchmark warnings when capture is active, so we keep the plugin around but stop it from registering automatically; we still import it via CLI flags for the benchmarks above.

## Running benchmarks

Use environment controls to avoid noise:

```bash
NUSYQ_ENABLE_OLLAMA_BENCH=1 python -m pytest tests/benchmarks/test_latency.py
```

Set `BENCHMARK_SKIP` or `--benchmark-skip` if you want to run only unit/integration suites without the optional benchmarks. The plugin also responds to `--benchmark-disable-gc` and `--benchmark-columns`, so we can measure throughput as needed.

## Automation & CI hooks

- CI and automation scripts list `pytest-benchmark` in `requirements-dev.txt` and `scripts/generate_ci_requirements.py`, ensuring the plugin ships next to `pytest`.  
- When we want to measure adoption of a new plugin-specific path (e.g., a ChatDev service), run the auditor with `--mode core` to keep focus before enabling the benchmark suite; once enabled, add the new benchmark file to `tests/benchmarks/` with the appropriate markers (`@pytest.mark.feed`, etc.).

## Next actions

1. Keep `tests/benchmarks/test_latency.py` and `tests/smoke/test_critical_paths.py` updated whenever performance expectations change, and document the required environment variables in `docs/terminal_intelligence_system_complete.md` or whichever user guide is relevant.  
2. If we ever build an app/extension, surface “Run benchmark suite” behind an advanced toggle that sets `NUSYQ_ENABLE_OLLAMA_BENCH=1` so the UI can run the plugin without manual env edits.  
3. Track new benchmark artifacts in `docs/benchmark_reports/` (or similar) so `pytest-benchmark` results are preserved alongside the dependency inventory we already maintain.
