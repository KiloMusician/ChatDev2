╭────────────────────────────────────────────────────────────────────────────────╮
│ 🧠 TESTS TERMINAL - RUN
│ run_id=tests_terminal_20251226_143314 | branch=master | agent=tests_terminal
╰────────────────────────────────────────────────────────────────────────────────╯

⚡ Outcome: ❌ Failed

🎯 Top Signals:
  ❌ [[TESTS]] Pytest failed: {'passed': 0, 'failed': 0, 'skipped': 3, 'xfailed': 0, 'xpassed': 0} (██████████ 100%)


📋 Next Actions:
  [1] Review failures
  [2] Rerun selectively (pytest -k <pattern>)

📊 Execution: ~2s
════════════════════════════════════════════════════════════════════════════════
[MACHINE FOOTER v1.2]
{
  "contract_version": "v1.2",
  "run_id": "tests_terminal_20251226_143314",
  "agent": "tests_terminal",
  "status": "failure",
  "timestamp": "2025-12-26T14:33:01.763363+00:00",
  "signals": [
    {
      "severity": "fail",
      "category": "[TESTS]",
      "message": "Pytest failed: {'passed': 0, 'failed': 0, 'skipped': 3, 'xfailed': 0, 'xpassed': 0}",
      "file": null,
      "line": null,
      "confidence": 1.0,
      "hint": null
    }
  ],
  "artifacts": [
    "state\\receipts",
    "state\\metrics"
  ],
  "next_actions": [
    "Review failures",
    "Rerun selectively (pytest -k <pattern>)"
  ],
  "guild": {
    "quality_gate": "tests",
    "branch": "master"
  },
  "exit_code": 2
}
