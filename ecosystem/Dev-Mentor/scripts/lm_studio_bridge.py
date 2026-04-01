#!/usr/bin/env python3
"""LM Studio Bridge: Routes local LM Studio models to container network
Enables seamless LLM inference routing between local and containerized services
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

import aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ============================================================================
# CONFIGURATION
# ============================================================================

LM_STUDIO_HOST = os.getenv("LM_STUDIO_HOST", "host.docker.internal")
LM_STUDIO_PORT = int(os.getenv("LM_STUDIO_PORT", "1234"))
LM_STUDIO_URL = f"http://{LM_STUDIO_HOST}:{LM_STUDIO_PORT}"
BRIDGE_PORT = 1234

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="LM Studio Bridge", version="1.0.0")

# ============================================================================
# MODELS
# ============================================================================


class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9


class CompletionResponse(BaseModel):
    choices: list
    model: str
    usage: dict[str, int]


# ============================================================================
# ROUTES
# ============================================================================


@app.get("/health")
async def health():
    """Check LM Studio availability"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{LM_STUDIO_URL}/api/status", timeout=aiohttp.ClientTimeout(total=2)
            ) as r:
                if r.status == 200:
                    return {"status": "healthy", "lm_studio": "connected"}
                else:
                    return {"status": "degraded", "lm_studio": "error"}
    except Exception as e:
        logger.warning(f"LM Studio health check failed: {e}")
        return {"status": "unhealthy", "lm_studio": "unreachable", "error": str(e)}


@app.get("/v1/models")
async def list_models():
    """List available models from LM Studio"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{LM_STUDIO_URL}/v1/models", timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    raise HTTPException(
                        status_code=r.status, detail="LM Studio unavailable"
                    )
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/completions")
async def create_completion(request: CompletionRequest):
    """Proxy completion request to LM Studio"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{LM_STUDIO_URL}/v1/completions",
                json={
                    "model": request.model,
                    "prompt": request.prompt,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                },
                timeout=aiohttp.ClientTimeout(total=300),
            ) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    error_text = await r.text()
                    logger.error(f"LM Studio error: {error_text}")
                    raise HTTPException(status_code=r.status, detail=error_text)
    except aiohttp.ClientError as e:
        logger.error(f"Connection to LM Studio failed: {e}")
        raise HTTPException(status_code=503, detail="LM Studio unavailable")
    except Exception as e:
        logger.error(f"Completion request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/completions")
async def create_chat_completion(request: dict[str, Any]):
    """Proxy chat completion request to LM Studio"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{LM_STUDIO_URL}/v1/chat/completions",
                json=request,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    error_text = await r.text()
                    logger.error(f"LM Studio error: {error_text}")
                    raise HTTPException(status_code=r.status, detail=error_text)
    except aiohttp.ClientError as e:
        logger.error(f"Connection to LM Studio failed: {e}")
        raise HTTPException(status_code=503, detail="LM Studio unavailable")
    except Exception as e:
        logger.error(f"Chat completion request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting LM Studio Bridge → {LM_STUDIO_URL}")
    uvicorn.run(app, host="0.0.0.0", port=BRIDGE_PORT, log_level="info")
