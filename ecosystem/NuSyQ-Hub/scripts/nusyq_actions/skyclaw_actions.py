"""Action module: SkyClaw Rust gateway lifecycle operations.

Exposes start/stop/status handlers for the SkyClaw sidecar gateway daemon.
Registered in start_nusyq.py under actions: skyclaw_start, skyclaw_stop,
skyclaw_status.

SkyClaw gateway endpoints (default :8080):
    GET /health  → {status, version, uptime_seconds}
    GET /status  → {status, version, provider, channels, tools, memory_backend}
    GET /dashboard → HTML monitoring dashboard
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from scripts.nusyq_actions.shared import emit_action_receipt


def _run_async(coro: Any) -> Any:
    """Run a coroutine in a new event loop (action modules are called synchronously)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=20)
    except RuntimeError:
        pass
    return asyncio.run(coro)


# ── Status ────────────────────────────────────────────────────────────────────


def handle_skyclaw_status(args: list[str], *, json_mode: bool = False) -> int:
    """Probe and display SkyClaw gateway status.

    Shows binary availability, gateway HTTP health, provider, channels, and tools.
    Exit code 0 = online (binary + gateway), 1 = binary-only or offline.
    """
    try:
        from src.integrations.skyclaw_gateway_client import get_skyclaw_gateway_client

        client = get_skyclaw_gateway_client()
        summary = _run_async(client.summary())

        if json_mode:
            print(json.dumps(summary, indent=2, default=str))
        else:
            _print_skyclaw_summary(summary)

        running = bool(summary.get("running"))
        emit_action_receipt("skyclaw_status", exit_code=0 if running else 1, metadata=summary)
        return 0 if running else 1

    except Exception as exc:
        payload = {"action": "skyclaw_status", "status": "error", "error": str(exc)}
        if json_mode:
            print(json.dumps(payload, indent=2))
        else:
            print(f"[ERROR] skyclaw_status failed: {exc}")
        emit_action_receipt("skyclaw_status", exit_code=1, metadata={"error": str(exc)})
        return 1


def _print_skyclaw_summary(summary: dict[str, Any]) -> None:
    """Pretty-print a skyclaw summary dict."""
    binary = summary.get("binary", {})
    url = summary.get("gateway_url", "?")
    running = summary.get("running", False)
    health = summary.get("health") or {}
    status = summary.get("status") or {}

    print("── SkyClaw Sidecar (Rust) ────────────────────")
    if binary.get("found"):
        wsl = " [WSL]" if binary.get("needs_wsl") else ""
        print(f"  Binary : {binary.get('path', '?')}{wsl}")
    else:
        print("  Binary : not found")

    print(f"  Gateway: {url}")
    if running:
        version = health.get("version", "?")
        uptime = health.get("uptime_seconds")
        uptime_str = f"{uptime:.0f}s" if isinstance(uptime, (int, float)) else "?"
        provider = status.get("provider", "?")
        channels = status.get("channels") or []
        tools = status.get("tools") or []
        print(f"  Status : ✅ ONLINE  v{version}  uptime={uptime_str}")
        print(f"  Provider : {provider}")
        if channels:
            print(f"  Channels : {', '.join(str(c) for c in channels[:8])}")
        if tools:
            print(f"  Tools    : {', '.join(str(t) for t in tools[:10])}")
    else:
        print("  Status : ⚪ Gateway not started  (binary available)")
    print("─────────────────────────────────────────────")


# ── Start ─────────────────────────────────────────────────────────────────────


def handle_skyclaw_start(args: list[str], *, json_mode: bool = False) -> int:
    """Start the SkyClaw gateway daemon.

    Spawns ``skyclaw start`` and waits up to 15 seconds for the gateway to become
    ready.  Exits 0 on success, 1 on failure or if binary is not found.
    """
    try:
        from src.integrations.skyclaw_gateway_client import get_skyclaw_gateway_client

        client = get_skyclaw_gateway_client()
        binary = client.binary_info()

        if not binary.get("found"):
            payload: dict[str, Any] = {
                "action": "skyclaw_start",
                "status": "error",
                "error": "SkyClaw binary not found",
            }
            if json_mode:
                print(json.dumps(payload, indent=2))
            else:
                print("[ERROR] SkyClaw binary not found — cannot start gateway")
            emit_action_receipt("skyclaw_start", exit_code=1, metadata=payload)
            return 1

        ok = _run_async(client.start_gateway(wait=True))
        payload = {
            "action": "skyclaw_start",
            "status": "ok" if ok else "failed",
            "gateway_url": client.gateway_url,
            **binary,
        }
        if json_mode:
            print(json.dumps(payload, indent=2))
        elif ok:
            print(f"✅ SkyClaw gateway started at {client.gateway_url}")
        else:
            print("❌ SkyClaw gateway failed to start (see logs)")

        emit_action_receipt("skyclaw_start", exit_code=0 if ok else 1, metadata=payload)
        return 0 if ok else 1

    except Exception as exc:
        payload = {"action": "skyclaw_start", "status": "error", "error": str(exc)}
        if json_mode:
            print(json.dumps(payload, indent=2))
        else:
            print(f"[ERROR] skyclaw_start failed: {exc}")
        emit_action_receipt("skyclaw_start", exit_code=1, metadata={"error": str(exc)})
        return 1


# ── Stop ──────────────────────────────────────────────────────────────────────


def handle_skyclaw_stop(args: list[str], *, json_mode: bool = False) -> int:
    """Stop the SkyClaw gateway daemon (if managed by this process).

    Only terminates the process started by ``skyclaw_start`` in the same session.
    To kill an externally-started gateway, use the OS or the SkyClaw CLI directly.
    """
    try:
        from src.integrations.skyclaw_gateway_client import get_skyclaw_gateway_client

        client = get_skyclaw_gateway_client()
        _run_async(client.stop_gateway())

        payload: dict[str, Any] = {
            "action": "skyclaw_stop",
            "status": "ok",
            "gateway_url": client.gateway_url,
        }
        if json_mode:
            print(json.dumps(payload, indent=2))
        else:
            print("⏹️  SkyClaw gateway stopped")

        emit_action_receipt("skyclaw_stop", exit_code=0, metadata=payload)
        return 0

    except Exception as exc:
        payload = {"action": "skyclaw_stop", "status": "error", "error": str(exc)}
        if json_mode:
            print(json.dumps(payload, indent=2))
        else:
            print(f"[ERROR] skyclaw_stop failed: {exc}")
        emit_action_receipt("skyclaw_stop", exit_code=1, metadata={"error": str(exc)})
        return 1
