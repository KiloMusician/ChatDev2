#!/usr/bin/env python3
"""Process queued background tasks and check system status.

Usage:
    python scripts/process_background_tasks.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_ollama():
    """Check if Ollama is available at localhost:11434."""
    import urllib.error
    import urllib.request

    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            models = [m.get("name", "unknown") for m in data.get("models", [])]
            print("[OK] Ollama is running at localhost:11434")
            print(f"     Available models: {', '.join(models) if models else 'none'}")
            return True
    except urllib.error.URLError as e:
        print("[ERROR] Ollama not available at localhost:11434")
        print(f"        Reason: {e.reason}")
        return False
    except Exception as e:
        print(f"[ERROR] Cannot connect to Ollama: {e}")
        return False


def get_orchestrator_status():
    """Get and display orchestrator status."""
    from src.orchestration.background_task_orchestrator import get_orchestrator

    orchestrator = get_orchestrator()
    status = orchestrator.get_orchestrator_status()

    print("\n=== BackgroundTaskOrchestrator Status ===")
    print(f"Total tasks: {status['total_tasks']}")
    print(f"Worker running: {status['worker_running']}")
    print("\nTask status breakdown:")
    for task_status, count in status["status_counts"].items():
        if count > 0:
            print(f"  - {task_status}: {count}")

    return orchestrator, status


async def process_queued_tasks(orchestrator, max_tasks=5):
    """Process a few queued tasks."""
    from src.orchestration.background_task_orchestrator import TaskStatus

    # Get queued tasks
    queued = orchestrator.list_tasks(status=TaskStatus.QUEUED, limit=max_tasks)

    if not queued:
        print("\n[INFO] No queued tasks to process")
        return 0

    print(f"\n=== Processing {len(queued)} queued tasks ===")

    processed = 0
    for task in queued:
        print(f"\nProcessing: {task.task_id}")
        print(f"  Prompt: {task.prompt[:60]}...")
        print(f"  Target: {task.target.value} / Model: {task.model}")

        try:
            result = await orchestrator.execute_task(task)
            if result.status.value == "completed":
                print(f"  [SUCCESS] Completed in {(result.completed_at - result.started_at).total_seconds():.1f}s")
                if result.result:
                    print(f"  Result preview: {result.result[:100]}...")
                processed += 1
            else:
                print(f"  [FAILED] {result.error}")
        except Exception as e:
            print(f"  [ERROR] {e}")

    return processed


def main():
    """Main entry point."""
    print("=" * 60)
    print("Background Task Processing System")
    print("=" * 60)

    # Check Ollama
    print("\n1. Checking Ollama availability...")
    ollama_available = check_ollama()

    # Get orchestrator status
    print("\n2. Getting orchestrator status...")
    orchestrator, status = get_orchestrator_status()

    queued_count = status["status_counts"].get("queued", 0)

    if queued_count == 0:
        print("\n[INFO] No queued tasks. Nothing to process.")
        return

    if not ollama_available:
        print("\n[WARNING] Ollama is not available. Cannot process tasks.")
        print("Please start Ollama with: ollama serve")
        return

    # Process some tasks
    print(f"\n3. Processing up to 3 queued tasks (out of {queued_count})...")

    processed = asyncio.run(process_queued_tasks(orchestrator, max_tasks=3))

    print("\n=== Summary ===")
    print(f"Processed: {processed} tasks")
    print(f"Remaining queued: {queued_count - processed}")

    # Show updated status
    final_status = orchestrator.get_orchestrator_status()
    print("\nFinal status counts:")
    for task_status, count in final_status["status_counts"].items():
        if count > 0:
            print(f"  - {task_status}: {count}")


if __name__ == "__main__":
    main()
