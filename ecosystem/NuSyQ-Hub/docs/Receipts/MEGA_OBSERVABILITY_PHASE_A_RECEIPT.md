# MEGA Observability Phase A Receipt

[RECEIPT]
action: phase_a_trace_inventory
repo: NuSyQ-Hub
cwd: C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
inputs:
  - rg -n "opentelemetry|OTEL_|otel\." src scripts tests docs config
  - rg -n "tracing|trace_|span" src scripts
  - rg -n "observability" src scripts docs config
  - rg -n "OTEL_EXPORTER_OTLP_ENDPOINT|OTEL_SERVICE_NAME|OTEL_RESOURCE_ATTRIBUTES|NUSYQ_TRACE|NUSYQ_TRACING" -S .
outputs:
  - docs/Receipts/MEGA_OBSERVABILITY_PHASE_A_RECEIPT.md
status: success
exit_code: 0
next:
  - Phase B: implement centralized tracing module
  - Phase C: wire tracing in CLI/orchestrators/loops

## Trace Inventory Summary

Observed tracing-related modules and usage:
- src/observability/otel.py: centralized OTEL setup with env-driven endpoint, console fallback, flush/shutdown, correlation IDs.
- src/observability/lightweight_tracer.py: file-based tracer (not wired into entrypoints).
- src/tracing_setup.py: stub tracing_status for health_cli compatibility.
- scripts/start_nusyq.py: tracing init + receipts; uses NUSYQ_TRACE and OTEL_* env; still prints receipts without inputs/exit_code/next.
- src/main.py: uses otel module; wraps startup/mode spans; flushes at end.
- src/orchestration/claude_orchestrator.py: direct opentelemetry init with hardcoded endpoint http://localhost:4318/v1/traces.
- src/orchestration/auto_healing.py: imports opentelemetry trace Status/StatusCode but no central init.

## Misconfigurations / Gaps

- Hardcoded OTLP endpoint in src/orchestration/claude_orchestrator.py.
- Mixed env flags: NUSYQ_TRACE present, but no NUSYQ_TRACING alias handling.
- Logs-to-traces not centralized; logging instrumentation is ad-hoc or missing.
- Orchestrator/router layers lack consistent spans + correlation IDs.
- Receipts in start_nusyq.py omit inputs, exit_code, and deterministic outputs list.
- Snapshot Available Actions does not annotate wired vs stub actions.

## Optional/Dead Code

- lightweight_tracer exists but is not currently connected to any entrypoint.
- tracing_setup stub reports disabled tracing without structured diagnostics.
