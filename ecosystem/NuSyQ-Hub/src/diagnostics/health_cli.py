#!/usr/bin/env python3
"""NuSyQ Health CLI - Restored clean implementation.

This module is a minimal entrypoint that forwards work to the
diagnostics modules in src.diagnostics.
"""

from __future__ import annotations

import argparse
import importlib
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def _run(cmd: list[str], timeout: int = 120) -> int:
    try:
        proc = subprocess.run(cmd, capture_output=False, timeout=timeout, check=False)
    except FileNotFoundError:
        return 1
    return proc.returncode


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="NuSyQ Health CLI - Restored wrapper")
    parser.add_argument("--stats", action="store_true", help="Quick error statistics")
    parser.add_argument("--ollama", action="store_true", help="Test Ollama integration")
    parser.add_argument("--resume", action="store_true", help="Show current focus")
    parser.add_argument("--awaken", action="store_true", help="Run system awakener")
    parser.add_argument("--intelligence", metavar="ERROR_CODE", help="Get intelligence")
    parser.add_argument("--full", action="store_true", help="Run full pipeline")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-execute safe fixes (when available)",
    )
    parser.add_argument("--tracing", action="store_true", help="Show tracing status (if available)")
    parser.add_argument(
        "--otel-compose",
        action="store_true",
        help="Print a small Docker Compose snippet to run a local OTLP collector for testing",
    )
    args = parser.parse_args(argv)

    if args.stats:
        rc = _run(["ruff", "check", "--statistics"], timeout=30)
        sys.exit(rc)
    if args.tracing:
        _exit_with_tracing_status()
    if args.otel_compose:
        _print_otel_compose_and_exit()

    if args.ollama:
        rc = _run(["ollama", "list"], timeout=30)
        sys.exit(rc)
    if args.resume:
        rc = _run([sys.executable, "-m", "src.diagnostics.ecosystem_integrator"], timeout=120)
        sys.exit(rc)
    if args.awaken:
        rc = _run([sys.executable, "src/diagnostics/system_awakener.py"], timeout=180)
        sys.exit(rc)
    if args.intelligence:
        rc = _run(
            [
                sys.executable,
                "-m",
                "src.diagnostics.ecosystem_integrator",
                args.intelligence,
            ],
            timeout=180,
        )
        sys.exit(rc)

    # Default: run the actionable intelligence agent
    if args.full:
        cmd = [sys.executable, "src/diagnostics/integrated_health_orchestrator.py"]
        if args.fix:
            cmd.append("--auto-execute")
    else:
        cmd = [sys.executable, "src/diagnostics/actionable_intelligence_agent.py"]
        if args.fix:
            cmd.append("--auto-execute")

    rc = _run(cmd, timeout=300)
    sys.exit(rc)


if __name__ == "__main__":
    main()


def _exit_with_tracing_status() -> None:
    tracing = None
    for module_name in (
        "tracing_setup",
        "nusyq.tracing_setup",
        "src.tracing_setup",
    ):
        try:
            tracing = importlib.import_module(module_name)  # nosemgrep
            break
        except Exception:
            # Some tracing shim packages throw AttributeError (or similar) when loaded.
            tracing = None

    if tracing and hasattr(tracing, "tracing_status"):
        tracing.tracing_status()
        sys.exit(0)

    sys.stderr.write(
        "Tracing not configured: missing tracing_setup.tracing_status. "
        "Install/enable tracing_setup or ignore if tracing is optional.\n"
    )
    sys.exit(1)


def _print_otel_compose_and_exit() -> None:
    compose_snippet = """
version: '3.9'
services:
    otlp-collector:
        image: otel/opentelemetry-collector:latest
        command: ["--config=/etc/otel-collector-config.yaml"]
        ports:
            - "4317:4317"   # OTLP gRPC
            - "4318:4318"   # OTLP HTTP
        volumes:
            - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
""".strip()

    print(compose_snippet)
    sys.exit(0)
