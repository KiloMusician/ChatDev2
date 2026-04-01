# NuSyQ-Hub Tracing Playbook

This playbook explains how to run local tracing end-to-end using OpenTelemetry with a local Collector and Jaeger UI.

## Quick Start

1) Bring up the local stack (if Docker is installed):

```
docker compose -f dev/observability/docker-compose.observability.yml up -d
```

- Collector: OTLP at http://localhost:4318
- Jaeger UI: http://localhost:16686

2) Run a traced command:

```
# Snapshot with receipts (prints trace_id/span_id)
python scripts/start_nusyq.py snapshot

# Trace doctor
python scripts/start_nusyq.py trace_doctor
```

3) Open Jaeger UI and search for service `nusyq-hub`.

## Environment Variables (defaults shown)

- `NUSYQ_TRACE=1` — set to `0` to disable tracing
- `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`
- `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`
- `OTEL_TRACES_EXPORTER=otlp`
- `OTEL_PROPAGATORS=tracecontext,baggage`
- `OTEL_TRACES_SAMPLER=parentbased_traceidratio`
- `OTEL_TRACES_SAMPLER_ARG=1.0`

## When Docker is not available

- Traces still work using the ConsoleSpanExporter fallback (printed to console).
- The collector configuration is provided in `config/otel-collector.yaml` for reference.

## Receipts

Each action writes a receipt to `docs/tracing/RECEIPTS/` including trace ids.

## Troubleshooting

- Run `python scripts/start_nusyq.py trace_doctor` to validate setup.
- If `opentelemetry` is not installed, tracing gracefully disables itself.
- If the collector is down, tracing falls back to console exporter.
