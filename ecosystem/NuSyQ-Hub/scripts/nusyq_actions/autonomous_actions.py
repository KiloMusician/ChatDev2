"""Action module: Autonomous development and cycling operations."""

from __future__ import annotations

import asyncio
import contextlib
import os
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING

from scripts.nusyq_actions.shared import emit_action_receipt, load_otel_bridge

if TYPE_CHECKING:
    from scripts.start_nusyq import RepoPaths

# Import otel bridge for tracing (legacy and canonical paths).
otel, _OTEL_SOURCE, _OTEL_IMPORT_ERROR = load_otel_bridge()


def handle_develop_system(args: list[str], paths: RepoPaths) -> int:
    """Run autonomous development loop (analyze → heal → repeat)."""
    print("🔄 Autonomous Development Loop")
    print("=" * 50)

    # Parse arguments
    max_iterations = 3
    halt_on_error = False

    for arg in args[1:]:
        if arg.startswith("--iterations="):
            max_iterations = int(arg.split("=", 1)[1])
        elif arg == "--halt-on-error":
            halt_on_error = True

    print("\nConfiguration:")
    print(f"  Max iterations: {max_iterations}")
    print(f"  Halt on error: {halt_on_error}")
    print("  Loop: analyze → heal → (repeat)\n")

    if str(paths.nusyq_hub) not in sys.path:
        sys.path.insert(0, str(paths.nusyq_hub))

    try:
        from src.tools.agent_task_router import AgentTaskRouter

        router = AgentTaskRouter(repo_root=paths.nusyq_hub)
        span_cm = (
            otel.start_action_span(
                "nusyq.develop_system.loop",
                {
                    "iterations.max": max_iterations,
                    "halt_on_error": halt_on_error,
                },
            )
            if otel
            else contextlib.nullcontext()
        )
        with span_cm:
            result = asyncio.run(
                router.develop_system(
                    max_iterations=max_iterations,
                    halt_on_error=halt_on_error,
                )
            )

        if result["status"] == "success":
            print(f"\n✅ Development loop complete: {result['iterations']} iterations")
            print(f"Log saved: {result['log_path']}")
            emit_action_receipt(
                "develop_system",
                exit_code=0,
                metadata={
                    "iterations": result.get("iterations"),
                    "log_path": result.get("log_path"),
                    "halt_on_error": halt_on_error,
                },
            )
            return 0
        else:
            print(f"\n❌ Development loop failed: {result.get('error', 'Unknown error')}")
            emit_action_receipt(
                "develop_system",
                exit_code=1,
                metadata={"error": result.get("error"), "halt_on_error": halt_on_error},
            )
            return 1

    except Exception as exc:
        print(f"[ERROR] Development loop failed: {exc}")
        import traceback

        traceback.print_exc()
        emit_action_receipt(
            "develop_system",
            exit_code=1,
            metadata={"error": str(exc), "halt_on_error": halt_on_error},
        )
        return 1


def handle_auto_cycle(
    args: list[str],
    paths: RepoPaths,
    pu_queue_handler: Callable[[RepoPaths, int, bool], int],
    queue_handler: Callable[[RepoPaths], int],
    replay_handler: Callable[[RepoPaths], int],
    metrics_handler: Callable[[RepoPaths], int],
    sync_handler: Callable[[RepoPaths], int],
    next_action_handler: Callable[[RepoPaths], int],
    culture_ship_handler: Callable[[bool], int] | None = None,
    gate_handler: Callable[[RepoPaths], int] | None = None,
) -> int:
    """Run an autonomous cycle: pu_queue → queue → replay → metrics → sync.

    Options:
      --iterations=N   number of cycles (default 1)
      --sleep=SECONDS  delay between cycles (default 5)
      --max-pus=N      max PUs to process per cycle (default 3)
      --real-pus       use real PU execution (default: simulated)
      --culture-ship   run Culture Ship cycle as part of each auto cycle
      --culture-ship-dry-run  run Culture Ship step in dry-run mode
      --skip-gate      skip ai_work_gate pre-check (default: gate enabled)
      --strict-gate    abort cycle immediately if gate check fails
      --pattern=sequential|hybrid  execution strategy (default: sequential)

    Env toggles (for persistent on/off control):
      NUSYQ_AUTO_CYCLE_CULTURE_SHIP=1
      NUSYQ_AUTO_CYCLE_REAL_PUS=1
      NUSYQ_AUTO_CYCLE_GATE=0
      NUSYQ_AUTO_CYCLE_STRICT_GATE=1
      NUSYQ_AUTO_CYCLE_PATTERN=hybrid
    """
    if any(arg in {"--help", "-h", "help"} for arg in args[1:]):
        print("Usage:")
        print("  python scripts/start_nusyq.py auto_cycle [options]")
        print("\nOptions:")
        print("  --iterations=N          Number of cycles (default: 1)")
        print("  --sleep=SECONDS         Delay between cycles (default: 5)")
        print("  --max-pus=N             Max PUs per cycle (default: 3)")
        print("  --real-pus              Execute real PU actions")
        print("  --sim-pus               Force simulated PU mode")
        print("  --culture-ship          Include Culture Ship cycle")
        print("  --culture-ship-dry-run  Include Culture Ship in dry-run mode")
        print("  --skip-gate             Skip ai_work_gate pre-check")
        print("  --strict-gate           Abort when gate check fails")
        print("  --pattern=sequential|hybrid")
        return 0

    print("🔁 Autonomous Cycle: pu_queue → queue → replay → metrics → sync → next_actions")
    print("=" * 50)

    def _env_flag(name: str, default: bool = False) -> bool:
        value = str(os.getenv(name, "1" if default else "0")).strip().lower()
        return value in {"1", "true", "yes", "on"}

    def _normalize_pattern(value: str | None) -> str:
        raw = (value or "").strip().lower()
        return raw if raw in {"sequential", "hybrid"} else "sequential"

    # defaults
    iterations = 1
    sleep_s = 5
    max_pus = int(os.getenv("NUSYQ_AUTO_CYCLE_MAX_PUS", "3") or "3")
    real_pus = _env_flag("NUSYQ_AUTO_CYCLE_REAL_PUS", default=False)
    include_culture_ship = _env_flag("NUSYQ_AUTO_CYCLE_CULTURE_SHIP", default=False)
    culture_ship_dry_run = False
    gate_enabled = _env_flag("NUSYQ_AUTO_CYCLE_GATE", default=True)
    strict_gate = _env_flag("NUSYQ_AUTO_CYCLE_STRICT_GATE", default=False)
    execution_pattern = _normalize_pattern(os.getenv("NUSYQ_AUTO_CYCLE_PATTERN", "sequential"))

    for arg in args[1:]:
        if arg.startswith("--iterations="):
            try:
                iterations = int(arg.split("=", 1)[1])
            except ValueError:
                pass
        elif arg.startswith("--sleep="):
            try:
                sleep_s = int(arg.split("=", 1)[1])
            except ValueError:
                pass
        elif arg.startswith("--max-pus="):
            try:
                max_pus = int(arg.split("=", 1)[1])
            except ValueError:
                pass
        elif arg == "--real-pus":
            real_pus = True
        elif arg == "--sim-pus":
            real_pus = False
        elif arg in {"--culture-ship", "--with-culture-ship"}:
            include_culture_ship = True
        elif arg == "--no-culture-ship":
            include_culture_ship = False
        elif arg == "--culture-ship-dry-run":
            include_culture_ship = True
            culture_ship_dry_run = True
        elif arg == "--skip-gate":
            gate_enabled = False
        elif arg == "--strict-gate":
            strict_gate = True
        elif arg.startswith("--pattern="):
            execution_pattern = _normalize_pattern(arg.split("=", 1)[1])

    pu_mode = "REAL" if real_pus else "SIMULATED"
    culture_ship_mode = "ENABLED" if include_culture_ship else "DISABLED"
    if include_culture_ship and culture_ship_dry_run:
        culture_ship_mode = "DRY_RUN"
    gate_mode = "STRICT" if strict_gate else "SOFT"
    print(
        f"Configuration: iterations={iterations}, sleep={sleep_s}s, max_pus={max_pus}, "
        f"pu_mode={pu_mode}, culture_ship={culture_ship_mode}, gate={'ON' if gate_enabled else 'OFF'}"
        f"({gate_mode}), pattern={execution_pattern}\n"
    )

    any_failures = False
    for i in range(1, iterations + 1):
        print(f"\n=== Cycle {i}/{iterations} ===")
        span_cm = (
            otel.start_action_span(
                "nusyq.auto_cycle.iteration",
                {
                    "iteration": i,
                    "iterations.total": iterations,
                },
            )
            if otel
            else contextlib.nullcontext()
        )
        with span_cm as iter_span:
            # Optional pre-flight gate to ensure required AI systems are available.
            gate_rc = 0
            if gate_enabled and gate_handler:
                gate_cm = (
                    otel.start_action_span("nusyq.auto_cycle.step.ai_work_gate") if otel else contextlib.nullcontext()
                )
                with gate_cm:
                    gate_rc = gate_handler(paths)
                if gate_rc != 0:
                    print("⚠️  ai_work_gate failed for this cycle")
                    any_failures = True
                    if strict_gate:
                        print("❌ Strict gate enabled; aborting autonomous cycle.")
                        emit_action_receipt(
                            "auto_cycle",
                            exit_code=1,
                            metadata={
                                "iterations": i,
                                "sleep_s": sleep_s,
                                "max_pus": max_pus,
                                "pu_mode": pu_mode,
                                "culture_ship": culture_ship_mode,
                                "gate_enabled": gate_enabled,
                                "strict_gate": strict_gate,
                                "pattern": execution_pattern,
                                "halt_reason": "ai_work_gate_failed",
                            },
                        )
                        return 1

            # Execute cycle steps with tracing
            step_cm = otel.start_action_span("nusyq.auto_cycle.step.pu_queue") if otel else contextlib.nullcontext()
            with step_cm:
                rc0 = pu_queue_handler(paths, max_pus, real_pus)

            step_cm = otel.start_action_span("nusyq.auto_cycle.step.queue") if otel else contextlib.nullcontext()
            with step_cm:
                rc1 = queue_handler(paths)

            step_cm = otel.start_action_span("nusyq.auto_cycle.step.replay") if otel else contextlib.nullcontext()
            with step_cm:
                rc2 = replay_handler(paths)

            rc3 = rc4 = rc5 = rc6 = 0
            if execution_pattern == "hybrid":

                async def _run_hybrid_tail() -> tuple[int, int, int, int]:
                    tasks = [
                        asyncio.to_thread(metrics_handler, paths),
                        asyncio.to_thread(sync_handler, paths),
                        asyncio.to_thread(next_action_handler, paths),
                    ]
                    if include_culture_ship and culture_ship_handler:
                        tasks.append(asyncio.to_thread(culture_ship_handler, culture_ship_dry_run))
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    normalized: list[int] = []
                    for item in results:
                        if isinstance(item, Exception):
                            normalized.append(1)
                        else:
                            try:
                                normalized.append(int(item))
                            except Exception:
                                normalized.append(1)
                    if len(normalized) == 3:
                        normalized.append(0)
                    return normalized[0], normalized[1], normalized[2], normalized[3]

                rc3, rc4, rc5, rc6 = asyncio.run(_run_hybrid_tail())
            else:
                step_cm = otel.start_action_span("nusyq.auto_cycle.step.metrics") if otel else contextlib.nullcontext()
                with step_cm:
                    rc3 = metrics_handler(paths)

                step_cm = otel.start_action_span("nusyq.auto_cycle.step.sync") if otel else contextlib.nullcontext()
                with step_cm:
                    rc4 = sync_handler(paths)

                step_cm = (
                    otel.start_action_span("nusyq.auto_cycle.step.next_actions") if otel else contextlib.nullcontext()
                )
                with step_cm:
                    rc5 = next_action_handler(paths)

                if include_culture_ship and culture_ship_handler:
                    step_cm = (
                        otel.start_action_span("nusyq.auto_cycle.step.culture_ship")
                        if otel
                        else contextlib.nullcontext()
                    )
                    with step_cm:
                        rc6 = culture_ship_handler(culture_ship_dry_run)

            failures = [
                name
                for name, rc in [
                    ("ai_work_gate", gate_rc),
                    ("pu_queue", rc0),
                    ("queue", rc1),
                    ("replay", rc2),
                    ("metrics", rc3),
                    ("sync", rc4),
                    ("next_actions", rc5),
                    ("culture_ship", rc6),
                ]
                if rc != 0
            ]

            if failures:
                print("\n⚠️  One or more steps failed in this cycle")
                any_failures = True
                try:
                    if iter_span:
                        iter_span.add_event(
                            "cycle.failure",
                            {
                                "failed_steps": ",".join(failures),
                            },
                        )
                except Exception:
                    pass

        if i < iterations:
            try:
                asyncio.run(asyncio.sleep(sleep_s))
            except Exception:
                import time as _t

                _t.sleep(sleep_s)

    print("\n✅ Autonomous cycle complete")
    rc = 1 if any_failures else 0
    emit_action_receipt(
        "auto_cycle",
        exit_code=rc,
        metadata={
            "iterations": iterations,
            "sleep_s": sleep_s,
            "max_pus": max_pus,
            "pu_mode": pu_mode,
            "culture_ship": culture_ship_mode,
            "gate_enabled": gate_enabled,
            "strict_gate": strict_gate,
            "pattern": execution_pattern,
        },
    )
    return rc
