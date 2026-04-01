"""lattice_mcp.py — MCP HTTP server exposing the Lattice knowledge graph to Gordon.

Runs on PORT (default 9101). Exposes the Lattice REST endpoints as MCP-labelled
FastAPI routes so Gordon can query, search, and seed the knowledge store without
calling game commands.

Endpoint map (all MCP-labelled):
  GET  /health                       — liveness check
  GET  /api/lattice/nodes            — list all nodes (optionally filtered by kind)
  GET  /api/lattice/search?q=...     — cosine-similarity search
  POST /api/lattice/nodes            — add a new knowledge node
  GET  /api/lattice/edges            — list all edges
  POST /api/lattice/edges            — add an edge between nodes
  GET  /api/lattice/stats            — store statistics
  POST /api/lattice/broadcast        — publish a knowledge event to Redis

Usage (container):
  MCP_MODULE=lattice_mcp python lattice_mcp.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# ── Path setup — when run as /app/lattice_mcp.py inside the container
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# lattice.py is copied to /app/lattice.py by Dockerfile.mcp
try:
    from lattice import _conn, _ensure_schema
    from lattice import router as lattice_router
except ImportError as e:
    print(f"[lattice_mcp] WARNING: could not import lattice module: {e}", flush=True)
    lattice_router = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [lattice_mcp] %(message)s")
log = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "9101"))

app = FastAPI(
    title="Lattice MCP",
    description="Knowledge graph MCP server for the Terminal Depths Lattice. "
    "Exposes search, node CRUD, and edge CRUD so Gordon can query "
    "and seed the collective knowledge store.",
    version="1.0.0",
)


@app.get("/health")
async def health():
    """MCP liveness check — Gordon polls this."""
    db_ok = False
    try:
        with _conn() as conn:
            conn.execute("SELECT 1")
        db_ok = True
    except Exception as e:
        log.warning("DB health check failed: %s", e)
    return JSONResponse(
        {
            "status": "ok" if db_ok else "degraded",
            "service": "lattice_mcp",
            "port": PORT,
        }
    )


@app.get("/")
async def root():
    return {"service": "lattice_mcp", "docs": "/docs", "health": "/health"}


if lattice_router is not None:
    app.include_router(lattice_router)
    log.info("Lattice router mounted at /api/lattice/")
else:

    @app.get("/api/lattice/unavailable")
    async def unavailable():
        return JSONResponse(
            {"error": "Lattice module unavailable — check container build"},
            status_code=503,
        )


if __name__ == "__main__":
    log.info("Starting Lattice MCP server on port %d", PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
