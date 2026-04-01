"""
Evaluator core for NuSyQ — lightweight evaluation runner for ChatDev tasks.

This module provides an `Evaluator` class that runs `nusyq_chatdev.py` tasks
and gathers metrics (success, return code, runtime, stdout sample).

It is purposely small and does not require Azure Evaluation SDK. A separate
adapter can be added to use the Azure SDK if desired.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.telemetry import tracing_setup as tracing


@dataclass
class RunResult:
    task: str
    model: str
    exit_code: int
    duration_seconds: float
    stdout_sample: str
    stderr_sample: str
    start_time: str
    end_time: str


class Evaluator:
    """Run a set of tasks and capture simple metrics.

    The evaluator is intentionally simple so it works in most developer
    environments without external dependencies.
    """

    def __init__(
        self,
        python_exe: str = "python",
        output_dir: Path | str = "Reports/evaluation"
    ):
        self.python_exe = python_exe
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_task(
        self,
        task: str,
        model: str = "qwen2.5-coder:7b",
        max_runtime: int = 60,
        setup_only: bool = True
    ) -> RunResult:
        chatdev_path = (
            Path(__file__).resolve().parents[1] / "../.." / 'nusyq_chatdev.py'
        )
        cmd = [
            self.python_exe,
            str(chatdev_path)
        ]
        # Normalize path to module's script path in top-level repo
        cmd = [
            self.python_exe,
            str(Path(__file__).resolve().parents[2] / "nusyq_chatdev.py"),
        ]
        cmd.extend([
            "--task",
            task,
            "--model",
            model,
            "--max-runtime",
            str(max_runtime),
        ])
        if setup_only:
            cmd.append("--setup-only")

        start_time = datetime.now()
        start_ts = time.time()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max_runtime + 5,
                env={**os.environ, "OPENAI_API_KEY": "ollama-local-model"},
                check=False,
            )
            exit_code = proc.returncode
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
        except subprocess.TimeoutExpired as e:
            exit_code = -1
            # TimeoutExpired may carry bytes or str depending on capture_output
            # usage; normalize
            if isinstance(e.stdout, (bytes, bytearray)):
                stdout = e.stdout.decode("utf-8")
            else:
                stdout = e.stdout or ""

            if isinstance(e.stderr, (bytes, bytearray)):
                stderr = e.stderr.decode("utf-8")
            else:
                stderr = e.stderr or "TIMEOUT"
        end_ts = time.time()
        duration = end_ts - start_ts
        stdout_sample = stdout[:200] + "..." if len(stdout) > 200 else stdout
        stderr_sample = stderr[:200] + "..." if len(stderr) > 200 else stderr
        result = RunResult(
            task=task,
            model=model,
            exit_code=exit_code,
            duration_seconds=duration,
            stdout_sample=stdout_sample,
            stderr_sample=stderr_sample,
            start_time=start_time.isoformat(),
            end_time=datetime.now().isoformat(),
        )
        return result

    def run_page(
        self,
        tasks: List[str],
        models: List[str],
        repeats: int = 1,
        max_runtime: int = 60,
        setup_only: bool = True,
    ) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        with tracing.start_span(
            "run_evaluation",
            {"task_count": len(tasks), "models": ",".join(models)},
        ):
            for model in models:
                for task in tasks:
                    for i in range(repeats):
                        run_span_name = f"run_task_{task[:20]}_{i}"
                        with tracing.start_span(
                            run_span_name,
                            {"model": model.strip()},
                        ):
                            res = self.run_task(
                                task,
                                model,
                                max_runtime=max_runtime,
                                setup_only=setup_only,
                            )
                            results.append(asdict(res))

        # Save report to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"evaluation_report_{timestamp}.json"
        with open(report_file, "w", encoding="utf-8") as fh:
            json.dump({"results": results}, fh, indent=2)

        summary = self._summarize(results)
        return {"report": str(report_file), "summary": summary}

    @staticmethod
    def _summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(results)
        successes = len([r for r in results if r.get("exit_code") == 0])
        durations = [r.get("duration_seconds", 0) for r in results]
        avg_duration = sum(durations) / total if total > 0 else 0.0
        return {
            "total_runs": total,
            "success_rate": successes / total if total > 0 else 0.0,
            "avg_duration": avg_duration,
        }
