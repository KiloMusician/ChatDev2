# Unified Error Report

- Timestamp: 2026-03-24T01:03:17.539922
- Scan mode: full
- Partial scan: yes (one or more scanners timed out or failed)
- Targets: nusyq-hub, simulated-verse, nusyq
- Tool Errors: 43, Tool Warnings: 993, Tool Infos: 677

## Tool Scan Ground Truth
- Errors: 43, Warnings: 993, Infos: 677, Total: 1713
- Note: Tool scan (full mode) using ruff, mypy, pylint across targeted repos: nusyq-hub, simulated-verse, nusyq; partial due to tool timeouts/errors

## Scan Warnings
- mypy timed out for nusyq-hub
- pylint timed out for simulated-verse
- budget exceeded before nusyq

## Diagnostics Export Counts
- Errors: 0, Warnings: 0, Infos: 0, Total: 0

## Repository Summary
### nusyq-hub
- Path: C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
- Python targets: 6
- Target names: src, tests, scripts, core, ml, tools
- Total: 1713
- Severity: {'warning': 993, 'info': 677, 'error': 43}
- Types: {'exception': 492, 'complexity': 84, 'linting': 805, 'import': 331, 'syntax': 1}
- Sources: {'pylint': 1505, 'ruff': 208}
### simulated-verse
- Path: C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse
- Python targets: 5
- Target names: src, tests, scripts, ml, tools
- Total: 0
- Severity: {}
- Types: {}
- Sources: {}
