#!/usr/bin/env python3
"""NuSyQ System Dashboard - Real-time system status and metrics.

Provides:
- Queue statistics
- AI system health
- Terminal activity
- Recent completions
- Performance metrics
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def get_queue_stats():
    """Get background task queue statistics."""
    from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator

    bg = BackgroundTaskOrchestrator()
    stats = bg.get_queue_stats()

    # Get by priority
    by_priority = {}
    by_target = {}
    for t in bg.tasks.values():
        p = t.priority.name
        by_priority[p] = by_priority.get(p, 0) + 1
        tgt = t.target.name
        by_target[tgt] = by_target.get(tgt, 0) + 1

    return {
        "stats": stats,
        "by_priority": by_priority,
        "by_target": by_target,
        "total": len(bg.tasks),
    }


def get_ai_capabilities():
    """Get unified AI orchestrator capabilities."""
    from src.orchestration import UnifiedAIOrchestrator

    orchestrator = UnifiedAIOrchestrator()
    return orchestrator.get_capabilities()


def get_recent_completions(limit: int = 10):
    """Get recently completed tasks."""
    from src.orchestration.background_task_orchestrator import BackgroundTaskOrchestrator

    bg = BackgroundTaskOrchestrator()

    completed = [t for t in bg.tasks.values() if t.status.name == "COMPLETED"]
    completed.sort(key=lambda x: x.completed_at or x.created_at, reverse=True)

    return [
        {
            "task_id": t.task_id[:20],
            "prompt": t.prompt[:50] + "..." if len(t.prompt) > 50 else t.prompt,
            "target": t.target.name,
            "completed": t.completed_at.isoformat() if t.completed_at else "unknown",
        }
        for t in completed[:limit]
    ]


def get_terminal_activity():
    """Get recent activity from terminal logs."""
    log_path = Path(__file__).parent.parent / "data/terminal_logs"
    activity = {}

    for log_file in log_path.glob("*.log"):
        channel = log_file.stem
        try:
            with open(log_file) as f:
                lines = f.readlines()
                activity[channel] = len(lines)
        except Exception:
            activity[channel] = 0

    return activity


def get_ollama_status():
    """Check Ollama service status."""
    import requests

    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.ok:
            models = resp.json().get("models", [])
            return {
                "status": "online",
                "models": len(models),
                "model_names": [m["name"] for m in models[:5]],
            }
    except Exception:
        pass
    return {"status": "offline", "models": 0}


def get_lmstudio_status():
    """Check LM Studio service status."""
    import requests

    try:
        resp = requests.get("http://localhost:1234/v1/models", timeout=5)
        if resp.ok:
            data = resp.json().get("data", [])
            return {
                "status": "online",
                "models": len(data),
                "model_names": [m["id"] for m in data[:3]],
            }
    except Exception:
        pass
    return {"status": "offline", "models": 0}


def print_dashboard():
    """Print comprehensive system dashboard."""
    print("\n" + "═" * 70)
    print("  🎮 NUSYQ SYSTEM DASHBOARD")
    print("  " + datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"))
    print("═" * 70)

    # Queue stats
    queue = get_queue_stats()
    print("\n📋 TASK QUEUE:")
    print(f"   Queued:    {queue['stats']['queued']:>5}")
    print(f"   Running:   {queue['stats']['running']:>5}")
    print(f"   Completed: {queue['stats']['completed']:>5}")
    print(f"   Failed:    {queue['stats']['failed']:>5}")
    print(f"   Total:     {queue['total']:>5}")

    print("\n   By Target:")
    for target, count in sorted(queue["by_target"].items()):
        print(f"     {target}: {count}")

    # AI Capabilities
    caps = get_ai_capabilities()
    print("\n🤖 AI SYSTEMS:")
    for system in caps["systems"]:
        print(f"   ✓ {system}")
    print(f"   Total Capacity: {caps['total_capacity']} concurrent tasks")

    # Services
    ollama = get_ollama_status()
    lmstudio = get_lmstudio_status()
    print("\n🔌 SERVICES:")
    print(f"   Ollama:    {ollama['status']} ({ollama['models']} models)")
    print(f"   LM Studio: {lmstudio['status']} ({lmstudio['models']} models)")

    # Terminal activity
    activity = get_terminal_activity()
    print("\n📺 TERMINAL ACTIVITY (log lines):")
    sorted_activity = sorted(activity.items(), key=lambda x: x[1], reverse=True)[:8]
    for channel, count in sorted_activity:
        bar = "█" * min(count // 100, 20)
        print(f"   {channel:15} {count:>6} {bar}")

    # Recent completions
    recent = get_recent_completions(5)
    print("\n✅ RECENT COMPLETIONS:")
    for task in recent:
        print(f"   {task['prompt']}")

    print("\n" + "═" * 70)


if __name__ == "__main__":
    print_dashboard()
