# Unified Error Report

- Timestamp: 2026-03-09T07:10:01.546127
- Scan mode: full
- Partial scan: yes (one or more scanners timed out or failed)
- Targets: nusyq

## Filters
- Include: nusyq
- Tool Errors: 0, Tool Warnings: 186, Tool Infos: 122

## Tool Scan Ground Truth
- Errors: 0, Warnings: 186, Infos: 122, Total: 308
- Note: Tool scan (full mode) using ruff, mypy, pylint across targeted repos: nusyq; partial due to tool timeouts/errors

## Scan Warnings
- mypy timed out for nusyq

## Diagnostics Export Counts
- Errors: 0, Warnings: 0, Infos: 0, Total: 0

## Repository Summary
### nusyq
- Path: /mnt/c/Users/keath/NuSyQ
- Python targets: 3
- Target names: src, tests, scripts
- Total: 308
- Severity: {'warning': 186, 'info': 122}
- Types: {'linting': 189, 'exception': 70, 'import': 44, 'complexity': 5}
- Sources: {'pylint': 307, 'ruff': 1}
