import importlib
import json
from pathlib import Path
from typing import Any


def load_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[2] / "config" / "context_config.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config_data: dict[str, Any] = json.load(f)
            return config_data
    return {"extensions": [], "changed_files_only": False}


def aggregate_context() -> dict[str, Any]:
    config = load_config()
    root_dir = Path(__file__).resolve().parents[2]
    results: dict[str, Any] = {}
    for name in config.get("extensions", []):
        try:
            module = importlib.import_module(f"{__package__}.extensions.{name}")  # nosemgrep
            provider = getattr(module, "provide_context", None)
            if callable(provider):
                results[name] = provider(
                    {
                        "root_dir": str(root_dir),
                        "changed_files_only": config.get("changed_files_only", False),
                    }
                )
        except Exception as exc:
            results[name] = {"error": str(exc)}
    output_path = root_dir / "context.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return results


if __name__ == "__main__":
    aggregate_context()
