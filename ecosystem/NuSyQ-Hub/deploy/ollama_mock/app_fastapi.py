import asyncio
import json
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import StreamingResponse

app = FastAPI(title="Ollama Mock", version="0.2")

FIXTURES_PATH = os.path.join(os.path.dirname(__file__), "fixtures.json")
try:
    with open(FIXTURES_PATH, encoding="utf8") as f:
        FIXTURES = json.load(f)
except (OSError, json.JSONDecodeError, UnicodeDecodeError):
    FIXTURES = {}


class GenerateRequest(BaseModel):
    model: str | None = "mock-ollama"
    prompt: str | None = None
    input: str | None = None
    parameters: dict[str, Any] | None = None


MOCK_VERSION = "0.5.4-mock"

# Models advertised by the mock — mirrors config/ollama_models.json
MOCK_MODELS = [
    "qwen2.5-coder:14b",
    "qwen2.5-coder:7b",
    "llama3.1:8b",
    "deepseek-coder-v2:16b",
    "nomic-embed-text:latest",
    "phi3.5:latest",
    "mistral:latest",
]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/version")
async def api_version():
    """Real Ollama API compatibility — used by K8s health checks and clients."""
    return {"version": MOCK_VERSION}


@app.get("/api/tags")
async def api_tags():
    """Real Ollama API compatibility — used by model discovery and Continue.dev."""
    return {
        "models": [
            {"name": name, "model": name, "size": 0, "digest": "mock"}
            for name in MOCK_MODELS
        ]
    }


@app.post("/v1/generate")
async def generate(req: GenerateRequest, scenario: str | None = None):
    prompt = req.prompt or req.input or ""
    if scenario:
        fixture = FIXTURES.get(scenario)
        if not fixture:
            raise HTTPException(status_code=404, detail=f"Scenario '{scenario}' not found")
        return {
            "model": req.model,
            "prompt": prompt,
            "response": fixture.get("response"),
            "ok": True,
            "meta": fixture.get("meta", {}),
        }

    # Basic deterministic mock response
    resp = {
        "model": req.model or "mock-ollama",
        "prompt": prompt,
        "response": f"MOCK_RESPONSE: {prompt[:500]}",
        "ok": True,
        "meta": {"token_count": len((prompt or "").split()), "parameters": req.parameters or {}},
    }
    return resp


@app.post("/v1/generate_stream")
async def generate_stream(req: GenerateRequest):
    # Provide both a JSON fragments response (backwards compatible) and
    # an SSE-style streaming endpoint at /v1/generate_sse below.
    prompt = req.prompt or req.input or ""
    fragments = [f"MOCK_PART_{i}: {prompt[:50]}" for i in range(1, 4)]
    return {"model": req.model, "fragments": fragments}


@app.post("/v1/generate_sse")
async def generate_sse(req: GenerateRequest):
    prompt = req.prompt or req.input or ""

    async def event_generator():
        for i in range(1, 4):
            data = {
                "part": i,
                "text": f"MOCK_STREAM_PART_{i}: {prompt[:100]}",
            }
            # SSE frame
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
