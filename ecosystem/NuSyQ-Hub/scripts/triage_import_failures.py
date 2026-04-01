"""Triage import failures by creating Processing Units (PUs) for manual or automated handling."""

import json
from pathlib import Path


def load_failures(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def simple_triage(report_path: Path, out_queue_path: Path | None = None) -> int:
    failures = load_failures(report_path)
    created = 0
    if not failures:
        print("No failures to triage.")
        return 0

    out_queue_path = out_queue_path or (Path("data") / "unified_pu_queue.json")
    out_queue_path.parent.mkdir(parents=True, exist_ok=True)

    # Simple behavior: for each failure that is not skipped, append a minimal PU JSON entry
    queue = []
    if out_queue_path.exists():
        try:
            queue = json.loads(out_queue_path.read_text(encoding="utf-8"))
        except Exception:
            queue = []

    for mod, reason in failures.items():
        if reason == "skipped_heavy_imports":
            continue
        pu = {
            "id": "",
            "type": "AnalysisPU",
            "title": f"Resolve import: {mod}",
            "description": f"Import failure for module {mod}: {reason}",
            "source_repo": "nusyq-hub",
            "priority": "medium",
            "proof_criteria": ["module imports", "tests pass", "document dependency decision"],
            "metadata": {"module": mod, "reason": reason},
            "status": "queued",
        }
        queue.append(pu)
        created += 1

    out_queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")
    print(f"Triaged {created} failures -> {out_queue_path}")
    return created


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Triage import failures into PUs")
    parser.add_argument("report", nargs="?", default="reports/import_failures_programmatic.json")
    args = parser.parse_args()

    created = simple_triage(Path(args.report))
    print(f"Created {created} PUs")
