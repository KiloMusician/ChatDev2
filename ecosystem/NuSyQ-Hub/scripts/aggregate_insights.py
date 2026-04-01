#!/usr/bin/env python
"""Convenience CLI wrapper for aggregated insights.

Delegates to report_aggregator; prints high-level summary for quick terminal use.
"""

from __future__ import annotations

import sys

try:
    from src.tools import report_aggregator
except ImportError:  # add fallback path adjustment
    import pathlib

    _root = pathlib.Path(__file__).resolve().parents[1]
    if str(_root) not in sys.path:
        sys.path.append(str(_root))
    from src.tools import report_aggregator


def main() -> int:
    insights = report_aggregator.aggregate_insights()
    report_aggregator.write_outputs(insights, write_markdown=True, write_json=True)
    data = insights.to_dict()
    print("Aggregated Insights Summary:\n")
    print(f"Generated: {data['generated_at']}")
    print(f"Action Plan Present: {data['action_plan_present']}")
    print(f"Issue Stubs Present: {data['issue_stubs_present']}")
    print(f"Latest Session Log Path: {data.get('latest_session_log_path')}")
    print("\nPrioritized Next Actions:")
    for act in data["prioritized_next_actions"]:
        print(f" - {act}")
    if data["missing_components"]:
        print("\nMissing Components:")
        for m in data["missing_components"]:
            print(f" - {m}")
    print("\nAction Plan Severity Counts:")
    for sev, count in data["action_plan_counts"].items():
        print(f" - {sev.title()}: {count}")
    print("\nIssue Stub Severity Counts:")
    for sev, count in data["issue_stub_counts"].items():
        print(f" - {sev.title()}: {count}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
