"""
Evaluation runner CLI for NuSyQ

Usage:
    python src/evaluation/runner.py --tasks tasks.jsonl --models qwen2.5-coder:7b --repeats 1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

# Ensure 'src/' is on sys.path so we can import evaluation modules directly
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))


def parse_tasks(path: Path) -> List[str]:
    tasks = []
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                data = json.loads(line)
                tasks.append(str(data.get("task", "")))
    else:
        # assume simple newline separated list
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    tasks.append(line.strip())
    return tasks


def run_cli() -> int:
    parser = argparse.ArgumentParser(description="NuSyQ Evaluation Runner")
    parser.add_argument(
        "--tasks",
        type=Path,
        required=True,
        help="Path to tasks file (jsonl or plain)",
    )
    parser.add_argument(
        "--models",
        type=str,
        default="qwen2.5-coder:7b",
        help="Comma-separated model list",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of repeats per task and model",
    )
    parser.add_argument(
        "--max-runtime",
        type=int,
        default=60,
        help="Max runtime per run in seconds",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Reports/evaluation"),
        help="Output directory for reports",
    )
    args = parser.parse_args()

    tasks = parse_tasks(args.tasks)
    models = [m.strip() for m in args.models.split(",")]

    # Local import to avoid static import issues when 'src' isn't in sys.path during lint
    # Try a standard package import first; otherwise load module by file path
    try:
        import importlib

        mod = importlib.import_module("evaluation.evaluator")
        evaluator_cls = mod.Evaluator
    except ImportError as exc:
        import importlib.util

        path = repo_root / "src" / "evaluation" / "evaluator.py"
        spec = importlib.util.spec_from_file_location(
            "evaluation.evaluator", str(path)
        )
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[arg-type]
            evaluator_cls = mod.Evaluator
        else:
            raise ImportError(
                "Unable to import evaluation.evaluator module"
            ) from exc

    evaluator = evaluator_cls(python_exe="python", output_dir=args.output)
    report = evaluator.run_page(
        tasks, models, repeats=args.repeats, max_runtime=args.max_runtime
    )
    print("Evaluation complete: ", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
