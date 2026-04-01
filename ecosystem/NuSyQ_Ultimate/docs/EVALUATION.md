# NuSyQ Evaluation Framework

This repository includes a lightweight evaluation harness for the ChatDev orchestration:

- `src/evaluation/evaluator.py`: Core evaluator that executes `nusyq_chatdev.py` for tasks and collects metrics.
- `src/evaluation/runner.py`: CLI wrapper to run a set of tasks and models and collect a JSON report.
- `tests/test_evaluation_runner.py`: Basic smoke test for the evaluator.
- `tests/eval_tasks.jsonl`: Example tasks file for evaluation.

Basic usage

1. Run a quick evaluation:

```bash
cd c:\Users\keath\NuSyQ
python src/evaluation/runner.py --tasks tests/eval_tasks.jsonl --models qwen2.5-coder:7b --repeats 1 --max-runtime 10
```

2. The report will be saved under `Reports/evaluation/` as `evaluation_report_<timestamp>.json`.

Design notes

- The evaluator runs each task in a fresh process and captures `stdout`, `stderr`, `exit_code`, runtime, and timestamps.
- The default behavior is `--setup-only` so the evaluator doesn't start long-running orchestration jobs by default. Pass `setup_only=False` in code if you want to run full executions.
- Tracing is instrumented via `tracing_setup.py`, which is a no-op if OpenTelemetry is not installed.

Extending the evaluator

- To compute advanced metrics, plug in custom evaluators (for example using azure.ai.evaluation evaluate() API) into the run lifecycle.
- You can add code-based or prompt-based evaluators for metrics such as Task Adherence, Coherence, or F1, as described in `docs/TRACING.md` and the Azure SDK docs.

Notes

- The evaluation framework is intentionally agnostic — it does not require external dependencies (OTLP exporter) to run and is safe for CI environments.
- If you'd like, I can implement Azure SDK backing for comprehensive evaluations (using `azure.ai.evaluation`) and some example evaluators such as Task Adherence and Similarity scoring.
