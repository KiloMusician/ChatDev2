from __future__ import annotations

from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.shared.model_registry import ModelRegistry

app = FastAPI(title="NuSyQ Model Registry API")
registry = ModelRegistry()


class RegisterPayload(BaseModel):
    path: str
    name: str | None
    provider: str | None = "lmstudio"
    size_bytes: int | None
    metadata: dict[str, Any] | None = None
    apply: bool = False


@app.get("/models", response_model=list[dict[str, Any]])
def list_models():
    return registry.list_models()


@app.post("/register")
def register(payload: RegisterPayload):
    meta = payload.dict()
    apply = meta.pop("apply", False)
    ok = registry.register_model(meta, apply=apply)
    if apply and not ok:
        raise HTTPException(status_code=500, detail="Failed to apply registry change")
    return {"ok": True, "applied": apply, "would_register": not apply}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8700)
