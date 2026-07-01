"""Probe raw chat completion latency for one or more local model routes.

This is intentionally stdlib-only so future smoke passes can compare live local
aliases and direct Ollama models without depending on the ChatDev workflow runtime.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from typing import Any

DEFAULT_SYSTEM_PROMPT = """Write one small runnable pygame game in `game.py`.

Requirements:
- one file only
- no external assets
- visible non-black background
- 60 FPS with `pygame.time.Clock()`
- clean `pygame.QUIT` handling with `pygame.quit()` and `sys.exit()`
- restart on `R`
- simple shapes and one tiny core mechanic

After writing the full code, call:
`save_file(path="game.py", content="<full code>")`

Then output exactly:
`Phase 1 smoke complete. Code saved to game.py.`

Put code only inside the tool call."""

DEFAULT_USER_PROMPT = "Create the smallest possible Python game prototype. Keep it to one file and minimal."
PROMPT_PRESETS = {
    "gamedev-phase1-full": (
        DEFAULT_SYSTEM_PROMPT,
        DEFAULT_USER_PROMPT,
    ),
    "pygame-stub": (
        "Write one short Python file named game.py that only opens a pygame window, shows a non-black background, handles quit, and exits cleanly. Return minimal code behavior only.",
        "Make the smallest possible pygame stub.",
    ),
}


def _probe_openai_compatible(
    *,
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    started_at = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        elapsed = round(time.time() - started_at, 2)
        content = None
        if body.get("choices"):
            content = body["choices"][0]["message"].get("content")
        return {
            "model": model,
            "status": "ok",
            "elapsed_seconds": elapsed,
            "has_content": bool(content),
            "content_preview": (content or "")[:200],
        }
    except urllib.error.HTTPError as exc:
        elapsed = round(time.time() - started_at, 2)
        error_text = exc.read().decode("utf-8", errors="replace")
        return {
            "model": model,
            "status": "http_error",
            "elapsed_seconds": elapsed,
            "error": error_text,
        }
    except Exception as exc:  # pragma: no cover - live probe helper
        elapsed = round(time.time() - started_at, 2)
        return {
            "model": model,
            "status": "error",
            "elapsed_seconds": elapsed,
            "error": str(exc),
        }


def _probe_ollama_generate(
    *,
    base_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": f"{system_prompt}\n\n{user_prompt}",
        "stream": False,
        "options": {
            "temperature": 0,
        },
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started_at = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        elapsed = round(time.time() - started_at, 2)
        content = body.get("response")
        return {
            "model": model,
            "status": "ok",
            "elapsed_seconds": elapsed,
            "has_content": bool(content),
            "content_preview": (content or "")[:200],
            "done": body.get("done"),
        }
    except urllib.error.HTTPError as exc:
        elapsed = round(time.time() - started_at, 2)
        error_text = exc.read().decode("utf-8", errors="replace")
        return {
            "model": model,
            "status": "http_error",
            "elapsed_seconds": elapsed,
            "error": error_text,
        }
    except Exception as exc:  # pragma: no cover - live probe helper
        elapsed = round(time.time() - started_at, 2)
        return {
            "model": model,
            "status": "error",
            "elapsed_seconds": elapsed,
            "error": str(exc),
        }


def _resolve_prompts(
    *,
    preset: str | None,
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, str]:
    if not preset:
        return system_prompt, user_prompt
    return PROMPT_PRESETS[preset]


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe raw local model completion latency.")
    parser.add_argument(
        "--mode",
        choices=("openai-compatible", "ollama-generate"),
        default="openai-compatible",
        help="Request shape to use for the probe",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:4000/v1",
        help="Base URL for the selected mode: LiteLLM /v1 for openai-compatible, Ollama host root for ollama-generate",
    )
    parser.add_argument("--api-key", default="local", help="Bearer token for the OpenAI-compatible endpoint")
    parser.add_argument("--model", action="append", required=True, help="Model alias to probe; repeat for multiple models")
    parser.add_argument(
        "--preset",
        choices=tuple(PROMPT_PRESETS.keys()),
        help="Named prompt preset; overrides --system-prompt and --user-prompt",
    )
    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM_PROMPT, help="System prompt to send")
    parser.add_argument("--user-prompt", default=DEFAULT_USER_PROMPT, help="User prompt to send")
    parser.add_argument("--max-tokens", type=int, default=700, help="Completion token cap")
    parser.add_argument("--timeout-seconds", type=float, default=190.0, help="Client-side request timeout")
    args = parser.parse_args()
    system_prompt, user_prompt = _resolve_prompts(
        preset=args.preset,
        system_prompt=args.system_prompt,
        user_prompt=args.user_prompt,
    )

    for model in args.model:
        if args.mode == "openai-compatible":
            result = _probe_openai_compatible(
                base_url=args.base_url,
                api_key=args.api_key,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=args.max_tokens,
                timeout_seconds=args.timeout_seconds,
            )
        else:
            result = _probe_ollama_generate(
                base_url=args.base_url,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                timeout_seconds=args.timeout_seconds,
            )
        result["mode"] = args.mode
        result["preset"] = args.preset
        print(json.dumps(result, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
