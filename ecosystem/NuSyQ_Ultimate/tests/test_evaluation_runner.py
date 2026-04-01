import importlib.util
from pathlib import Path


def _load_evaluator():
    # Try package import first
    try:
        mod = importlib.import_module("evaluation.evaluator")
        return mod.Evaluator
    except ImportError as exc:
        # If pytest runs tests in temp folders, use the current working dir
        repo_root = Path.cwd()
        path = repo_root / "src" / "evaluation" / "evaluator.py"
        spec = importlib.util.spec_from_file_location(
            "evaluation.evaluator", str(path)
        )
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            # Register in sys.modules for proper dataclass introspection
            import sys as _sys
            _sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)  # type: ignore[arg-type]
            return mod.Evaluator
        else:
            raise ImportError("Unable to load Evaluator class") from exc


def test_evaluator_run_setup_only(tmp_path: Path):
    evaluator_cls = _load_evaluator()
    evaluator = evaluator_cls(python_exe="python", output_dir=tmp_path)
    # Run a simple setup-only evaluation
    report = evaluator.run_page(
        ["Create a tiny CLI"], ["qwen2.5-coder:7b"], repeats=1, max_runtime=10
    )
    assert "report" in report
    assert report["summary"]["total_runs"] == 1
    assert isinstance(report["summary"]["avg_duration"], float)
