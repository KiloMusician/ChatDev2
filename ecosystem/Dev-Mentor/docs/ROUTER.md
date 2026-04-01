# Open Router

Last updated: 2026-03-21

## Purpose

Open Router is the resilient AI gateway for the Dev-Mentor ecosystem. It
provides one HTTP surface for LLM work while handling retries, fallback chains,
circuit-breaker state, basic rate limiting, caching, and Prometheus-friendly
metrics.

It keeps direct provider logic out of callers like `llm_client.py` and
`chatdev_worker.py`, while still allowing them to fall back to direct backends
when the router is disabled.

## Service

- Script: [`scripts/model_router.py`](/mnt/c/Users/keath/Dev-Mentor/scripts/model_router.py)
- Package: [`services/router`](/mnt/c/Users/keath/Dev-Mentor/services/router)
- Config: [`config/router.yml`](/mnt/c/Users/keath/Dev-Mentor/config/router.yml)
- Port: `9001`
- Health: `GET /health`
- Metrics: `GET /metrics`

## Endpoints

- `POST /route/{service}`
  - Primary execution surface
  - Current service implemented: `llm`
- `POST /api/route`
  - Legacy model-selection compatibility endpoint
- `GET /api/models`
  - Legacy model registry listing

Example:

```bash
curl -s http://localhost:9001/route/llm \
  -H 'content-type: application/json' \
  -d '{
    "action": "generate",
    "prompt": "Say hello from the router",
    "max_tokens": 64,
    "temperature": 0.2
  }'
```

## Routing Model

Configuration lives in `config/router.yml`.

Current `llm` routing supports:

- Replit AI
- Ollama
- LM Studio
- OpenAI
- Claude

Action routing determines preferred fallback order per action, for example
`generate`, `chat`, and `code`.

## llm_client Integration

`llm_client.py` can route through Open Router when explicitly enabled.

Feature flags:

- `USE_ROUTER=1`
- or `LLM_BACKEND=router`

Environment:

- `MODEL_ROUTER_URL=http://localhost:9001`

Default behavior remains conservative: without the flag, `llm_client.py`
continues using its direct local backends.

## Docker Compose

The compose service is `model-router`.

It depends on:

- `redis`
- `ollama`

Relevant environment:

- `MODEL_ROUTER_PORT`
- `ROUTER_CONFIG_PATH`
- `REDIS_URL`
- `OLLAMA_HOST`

## Operational Notes

- Redis stores circuit-breaker and rate-limit state when available.
- If Redis is unavailable, router state falls back to in-memory storage.
- External providers are treated as configured/ready when their required auth
  env vars exist; the router does not spam their remote APIs for health checks.
- `cascade.sh` now starts and reports the router as part of the lattice stack.
