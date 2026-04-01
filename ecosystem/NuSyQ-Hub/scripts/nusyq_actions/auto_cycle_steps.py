"""Auto-cycle step handlers extracted from the spine.

These handlers are intentionally self-contained and only assume `paths`
provides a `.nusyq_hub` attribute pointing to the Hub root.
"""

from __future__ import annotations

import json
import sys

from scripts.nusyq_actions.shared import emit_action_receipt


def handle_pu_queue_processing(paths, max_pus: int = 3, real_mode: bool = False) -> int:
    """Process PU queue with rate limiting."""
    mode_label = "REAL" if real_mode else "SIMULATED"
    print(f"🔄 PU Queue Processing [{mode_label} MODE, max={max_pus}]")
    print("=" * 50)

    hub = getattr(paths, "nusyq_hub", None)
    if str(hub) not in sys.path:
        sys.path.insert(0, str(hub))

    try:
        import asyncio

        from src.automation.unified_pu_queue import UnifiedPUQueue  # type: ignore

        pu_runner_path = hub / "scripts" / "pu_queue_runner.py"
        if not pu_runner_path.exists():
            print(f"[WARN] PU queue runner not found at {pu_runner_path}")
            emit_action_receipt(
                "pu_queue",
                exit_code=0,
                metadata={"status": "skipped", "reason": "missing_runner"},
            )
            return 0

        queue = UnifiedPUQueue()
        processable_statuses = {"queued", "approved", "delegated"}
        processable = [pu for pu in queue.queue if pu.status in processable_statuses]
        if not processable:
            print("\nInfo: No PUs ready for processing")
            emit_action_receipt(
                "pu_queue",
                exit_code=0,
                metadata={"status": "empty", "max_pus": max_pus, "real_mode": real_mode},
            )
            return 0

        to_process = processable[:max_pus]
        print(
            f"\n📝 Found {len(processable)} processable PUs"
            f" ({', '.join(sorted(processable_statuses))}), processing {len(to_process)}"
        )

        async def process_pu(pu):
            sys.path.insert(0, str(hub / "scripts"))
            from pu_queue_runner import _execute_pu_real  # type: ignore

            if not pu.assigned_agents:
                assigned = queue.assign_agents(pu.id)
                if assigned:
                    pu.assigned_agents = assigned

            pu.status = "executing"
            print(f"  ⚙️  {pu.id} | {pu.title[:50]}...")

            if real_mode:
                result = await _execute_pu_real(pu)
                pu.execution_results = result
                pu.status = "completed" if result.get("success") else "failed"
            else:
                pu.execution_results = {"note": "simulated completion", "executor": "auto_cycle"}
                pu.status = "completed"

            return pu.status == "completed"

        async def process_all():
            results = []
            for pu in to_process:
                success = await process_pu(pu)
                results.append(success)
            return results

        results = asyncio.run(process_all())
        queue._save_queue()

        succeeded = sum(results)
        print(f"\n✅ Processed {succeeded}/{len(to_process)} PUs successfully")

        report_path = hub / "state" / "reports" / "pu_queue_status.md"
        total = len(queue.queue)
        completed = len([p for p in queue.queue if p.status == "completed"])
        queued = len([p for p in queue.queue if p.status == "queued"])
        report_path.write_text(
            f"# PU Queue Status (Auto-Cycle)\n\n"
            f"Total: {total} | Completed: {completed} | Queued: {queued}\n\n"
            f"Last cycle: {len(to_process)} PUs processed ({succeeded} succeeded)\n",
            encoding="utf-8",
        )
        emit_action_receipt(
            "pu_queue",
            exit_code=0,
            metadata={
                "processed": len(to_process),
                "succeeded": succeeded,
                "real_mode": real_mode,
                "report_path": str(report_path),
            },
        )
        return 0
    except Exception as e:
        print(f"[ERROR] PU queue processing failed: {e}")
        import traceback

        traceback.print_exc()
        emit_action_receipt(
            "pu_queue",
            exit_code=1,
            metadata={"error": str(e), "real_mode": real_mode},
        )
        return 1


def handle_queue_execution(paths) -> int:
    """Execute next item from work queue."""
    print("📋 Work Queue Execution")
    print("=" * 50)

    hub = getattr(paths, "nusyq_hub", None)
    if str(hub) not in sys.path:
        sys.path.insert(0, str(hub))

    try:
        import asyncio

        from src.tools.work_queue_executor import WorkQueueExecutor  # type: ignore

        executor = WorkQueueExecutor(repo_root=hub)
        result = asyncio.run(executor.execute_next_item())

        print("\n" + json.dumps(result, indent=2))

        if result.get("status") == "success":
            print(f"\n✅ Item executed: {result.get('title', 'Unknown')}")
            emit_action_receipt(
                "queue",
                exit_code=0,
                metadata={"status": "success", "title": result.get("title")},
            )
            return 0
        elif result.get("status") in {"empty", "no_queued_items"}:
            print(f"\nInfo: {result.get('message', 'Work queue is empty')}")
            emit_action_receipt(
                "queue",
                exit_code=0,
                metadata={"status": result.get("status")},
            )
            return 0
        else:
            print(f"\n❌ Execution failed: {result.get('error', 'Unknown error')}")
            emit_action_receipt(
                "queue",
                exit_code=1,
                metadata={"status": result.get("status"), "error": result.get("error")},
            )
            return 1
    except Exception as e:
        print(f"[ERROR] Queue execution failed: {e}")
        import traceback

        traceback.print_exc()
        emit_action_receipt(
            "queue",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return 1


def handle_metrics_dashboard(paths) -> int:
    """Display AI system metrics dashboard."""
    print("📊 AI SYSTEM METRICS DASHBOARD")
    print("=" * 70)

    hub = getattr(paths, "nusyq_hub", None)
    if not hub:
        print("[ERROR] NuSyQ-Hub path not found")
        emit_action_receipt(
            "metrics_dashboard",
            exit_code=1,
            metadata={"error": "missing_hub_path"},
        )
        return 1

    try:
        import sys as sys_module

        from src.system.ai_metrics_tracker import generate_metrics_report  # type: ignore

        hours = 24
        if "--hours" in sys_module.argv:
            idx = sys_module.argv.index("--hours")
            if idx + 1 < len(sys_module.argv):
                try:
                    hours = int(sys_module.argv[idx + 1])
                except ValueError:
                    print(f"⚠️  Invalid hours value, using default: {hours}")

        report = generate_metrics_report(hub, hours=hours)
        print(report)

        print("\n" + "=" * 70)
        print("💡 Tips:")
        print("  • Use --hours N to view different time periods")
        print("  • Metrics are recorded automatically during health checks")
        print("  • Gate decisions are logged when work gating is enforced")
        emit_action_receipt(
            "metrics_dashboard",
            exit_code=0,
            metadata={"hours": hours},
        )
        return 0

    except ImportError as exc:
        print(f"[ERROR] Could not import metrics tracker: {exc}")
        emit_action_receipt(
            "metrics_dashboard",
            exit_code=1,
            metadata={"error": str(exc)},
        )
        return 1
    except Exception as exc:
        print(f"[ERROR] Metrics dashboard failed: {exc}")
        import traceback

        traceback.print_exc()
        emit_action_receipt(
            "metrics_dashboard",
            exit_code=1,
            metadata={"error": str(exc)},
        )
        return 1


def handle_quest_replay(paths) -> int:
    """Replay historical quests and extract learning."""
    print("🔄 Quest Replay & Learning")
    print("=" * 50)

    hub = getattr(paths, "nusyq_hub", None)
    if str(hub) not in sys.path:
        sys.path.insert(0, str(hub))

    try:
        import asyncio

        from src.tools.quest_replay_engine import QuestReplayEngine  # type: ignore

        engine = QuestReplayEngine(repo_root=hub)

        print("\n1️⃣  Replaying recent quests...")
        replay = asyncio.run(engine.replay_recent_quests(limit=5))
        if replay.get("status") == "success":
            print(f"   ✅ Analyzed {replay.get('quests_analyzed', 0)} quests")
            print(f"   📌 Patterns identified: {len(replay.get('patterns', {}))}")
            rec_count = len(replay.get("recommendations", []))
            print(f"   💡 Recommendations: {rec_count}")
            for rec in replay.get("recommendations", [])[:3]:
                print(f"      - {rec}")

        print("\n2️⃣  Analyzing work queue history...")
        history = asyncio.run(engine.analyze_work_queue_history())
        if history.get("status") == "success":
            print(f"   📋 Total items: {history.get('total_items', 0)}")
            print(f"   ✅ Success rate: {history.get('overall_success_rate', 0)}%")

        print("\n3️⃣  Predicting next work items...")
        predictions = asyncio.run(engine.predict_next_items(count=3))
        if predictions.get("status") == "success":
            for pred in predictions.get("predictions", [])[:3]:
                print(f"   🎯 {pred.get('title', 'Unknown')} (confidence: {pred.get('confidence', 0)})")

        print("\n✅ Quest replay complete")
        emit_action_receipt(
            "quest_replay",
            exit_code=0,
            metadata={"status": "success"},
        )
        return 0
    except Exception as e:
        print(f"[ERROR] Quest replay failed: {e}")
        import traceback

        traceback.print_exc()
        emit_action_receipt(
            "quest_replay",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return 1


def handle_cross_sync(paths) -> int:
    """Sync cultivation data to SimulatedVerse."""
    print("🌉 Cross-Ecosystem Sync")
    print("=" * 50)

    hub = getattr(paths, "nusyq_hub", None)
    if str(hub) not in sys.path:
        sys.path.insert(0, str(hub))

    try:
        import asyncio

        from src.tools.cross_ecosystem_sync import CrossEcosystemSync  # type: ignore

        syncer = CrossEcosystemSync(repo_root=hub)
        result = asyncio.run(syncer.sync_to_simverse())

        print(f"\nStatus: {result.get('status', 'unknown')}")
        print(f"Items synced: {result.get('synced_items', 0)}")

        for key, detail in result.get("details", {}).items():
            status = detail.get("status", "unknown")
            synced = detail.get("items_synced", 0)
            print(f"  • {key}: {status} ({synced} items)")

        print("\n✅ Cross-sync complete")
        emit_action_receipt(
            "cross_sync",
            exit_code=0,
            metadata={"status": result.get("status"), "synced_items": result.get("synced_items")},
        )
        return 0
    except Exception as e:
        print(f"[ERROR] Cross-sync failed: {e}")
        import traceback

        traceback.print_exc()
        emit_action_receipt(
            "cross_sync",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return 1
