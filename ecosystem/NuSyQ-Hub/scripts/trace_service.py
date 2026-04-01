#!/usr/bin/env python3
"""Minimal trace service placeholder.

Exposes:
  GET /health -> 200 OK {"status":"ok"}
  POST /v1/traces -> 200 OK (accepts and discards payload)

This is a lightweight stand-in to satisfy health checks until a real collector is wired.
"""

from __future__ import annotations

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response

LOG_PATH = Path(__file__).resolve().parents[1] / "data" / "service_logs" / "trace_service_stub.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("trace_service")
logger.setLevel(logging.INFO)
_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(_handler)
logger.propagate = False

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/")
@app.post("/v1/traces")
@app.post("/v1/traces/")
@app.post("/v1/traces{rest:path}")
async def ingest(request: Request, rest: str = ""):
    body = await request.body()
    logger.info(
        "received traces path=/%s length=%s headers=%s",
        rest,
        len(body),
        dict(request.headers),
    )
    return Response(status_code=200)


@app.get("/v1/traces")
@app.get("/v1/traces/")
@app.get("/v1/traces{rest:path}")
async def traces_health(rest: str = ""):
    return {"status": "ok", "path": f"/v1/traces{rest}"}


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=4318, log_level="info")


if __name__ == "__main__":
    main()
