#!/usr/bin/env python3
"""Simulate the Culture Ship processing tasks from SimulatedVerse/tasks/ and writing results.

This is a helper script for local testing to simulate the Culture Ship agent responding to tasks created by the SimulatedVerseBridge.
"""

import json
import os
import time
from pathlib import Path

SIMULATEDVERSE_ROOT = Path(os.getenv("SIMULATEDVERSE_ROOT") or os.getenv("SIMULATEDVERSE_PATH") or "")
if not SIMULATEDVERSE_ROOT:
    # Try to resolve relative sibling to repo
    SIMULATEDVERSE_ROOT = Path(__file__).resolve().parents[1] / ".." / "SimulatedVerse" / "SimulatedVerse"
    SIMULATEDVERSE_ROOT = SIMULATEDVERSE_ROOT.resolve()
TASKS_DIR = SIMULATEDVERSE_ROOT / "tasks"
RESULTS_DIR = SIMULATEDVERSE_ROOT / "results"


def process_task_file(task_file: Path):
    try:
        data = json.loads(task_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Failed to parse task file {task_file}: {exc}")
        return
    except OSError as exc:
        print(f"Failed to read task file {task_file}: {exc}")
        return

    task_id = data.get("task_id")
    agent_id = data.get("agent_id")

    print(f"Processing task {task_id} for agent {agent_id}")

    # Simple simulated response
    result = {
        "task_id": task_id,
        "processed_by": "culture-ship-sim",
        "status": "ok",
        "summary": f"Simulated Culture Ship response for {data.get('content', '')[:80]}",
        "original_metadata": data.get("metadata", {}),
        "timestamp": int(time.time() * 1000),
    }

    result_file = RESULTS_DIR / f"{task_id}_result.json"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote simulated result to {result_file}")


if __name__ == "__main__":
    print("Simulated Culture Ship Agent started. Watching for tasks...")
    while True:
        try:
            task_files = list(TASKS_DIR.glob("*.json"))
            if not task_files:
                time.sleep(1)
                continue

            for tf in task_files:
                process_task_file(tf)
                # Remove the task file to simulate processing
                try:
                    tf.unlink()
                except OSError as exc:
                    print(f"Failed to remove task file {tf}: {exc}")

            time.sleep(0.5)
        except KeyboardInterrupt:
            print("Stopping simulated agent")
            break
        except (OSError, RuntimeError) as exc:
            print(f"Error while watching tasks: {exc}")
            time.sleep(1)
