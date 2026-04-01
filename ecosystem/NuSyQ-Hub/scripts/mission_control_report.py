#!/usr/bin/env python3
"""Generate Mission Control report with attestation, audits, and governance insights."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from src.config.feature_flag_manager import is_feature_enabled
from src.resilience.mission_control_attestation import (
    MissionControlReportBuilder,
)


def collect_artifacts(root: Path) -> list[dict]:
    """Collect artifact bundles from state/artifacts."""
    if not root.exists():
        return []
    bundles = []
    for manifest in root.glob("*/run_manifest.json"):
        try:
            data = json.loads(manifest.read_text())
            bundles.append(
                {
                    "run_id": manifest.parent.name,
                    "task": data.get("task"),
                    "model": data.get("models", {}).get("primary") or data.get("model"),
                    "use_ollama": data.get("use_ollama"),
                    "created": data.get("timestamps", {}).get("created"),
                    "plan_steps": len(data.get("plan_bundle", {}).get("high_level", [])),
                }
            )
        except Exception:
            continue
    return sorted(bundles, key=lambda x: x.get("created") or 0, reverse=True)


def main() -> None:
    if not is_feature_enabled("mission_control_enabled"):
        print("mission_control_enabled flag is off; no report generated.")
        return

    artifacts_root = Path("state") / "artifacts"
    report_path = Path("state") / "reports" / "mission_control_summary.json"
    culture_ship_path = Path("state") / "reports" / "culture_ship_report.json"

    # Collect artifacts
    entries = collect_artifacts(artifacts_root)
    summary = {
        "count": len(entries),
        "latest": entries[:10],
        "attestation_enabled": True,
    }

    # Build enriched Culture Ship report (with audits, patterns, lessons)
    try:
        builder = MissionControlReportBuilder()
        culture_ship_report = builder.build_report()
        builder.save_report(culture_ship_report, culture_ship_path)
        summary["culture_ship_report"] = {
            "report_id": culture_ship_report.report_id,
            "timestamp": culture_ship_report.timestamp,
            "audit_summary": culture_ship_report.audit_summary,
            "health_score": culture_ship_report.health_score,
            "patterns_count": len(culture_ship_report.patterns_observed),
            "violations_count": len(culture_ship_report.policy_violations),
            "lessons_count": len(culture_ship_report.lessons_learned),
        }
        print(f"Wrote Culture Ship report to {culture_ship_path}")
    except Exception as e:
        print(f"Warning: Culture Ship report failed: {e}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote Mission Control summary to {report_path}")
