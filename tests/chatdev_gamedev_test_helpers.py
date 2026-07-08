from __future__ import annotations

from typing import Any


def build_smoke_receipt_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "session_name": "test-smoke-receipt",
        "status": "artifact_emitted",
        "bounded_stop_reason": "artifact_threshold_reached",
        "repo_root": r"C:\dev\_sandboxes\chatdev-factory-prototype-smoke",
        "first_artifact_path": r"WareHouse\proof\code_workspace\game.py",
        "yaml_file": r"C:\dev\active\ChatDev2\yaml_instance\GameDev_mechanic_smoke.yaml",
        "runtime_python": r"C:\dev\active\ChatDev2\.venv-gamedev313\Scripts\python.exe",
        "override_model": "ecosystem-devstral",
        "env_defaults": {
            "BASE_URL": "http://127.0.0.1:4000/v1",
            "API_KEY": "ollama-local-model",
        },
        "token_usage": {
            "model_usages": {"ecosystem-coder-fast": {"total_tokens": 123}},
            "call_history": [
                {
                    "provider": "openai",
                    "model_name": "ecosystem-coder-fast",
                }
            ],
        },
        "artifact_runtime_validation": [
            {
                "relative_path": "code_workspace/game.py",
                "valid": True,
                "outcome": "completed",
            }
        ],
    }
    payload.update(overrides)
    return payload
