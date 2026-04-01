#!/usr/bin/env python3
"""scripts/dispatch_task.py — Task Dispatcher

Reads task files from tasks/ directory and dispatches them to the
appropriate sub-agent based on the task type. Can also create new
tasks from command-line descriptions using the LLM to break them down.

Usage:
    python3 scripts/dispatch_task.py                    # dispatch all pending
    python3 scripts/dispatch_task.py --create "task"    # create + dispatch one task
    python3 scripts/dispatch_task.py --status           # show queue status
    python3 scripts/dispatch_task.py --list             # list all tasks
    python3 scripts/dispatch_task.py --task <id>        # dispatch specific task
    python3 scripts/dispatch_task.py --flush            # clear done/failed tasks
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.parent
TASKS_DIR = BASE_DIR / "tasks"
FILE_TASKS_DIR = TASKS_DIR / "legacy_runtime"
TASKS_DIR.mkdir(exist_ok=True)
FILE_TASKS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://localhost:8008"
SWARM_ROLES = frozenset(
    {
        "scout",
        "lorekeeper",
        "tester",
        "builder",
        "architect",
        "orchestrator",
        "serena_class",
        "custom",
    }
)

AGENT_ROUTING: dict = {
    "implement": "agents/implementer.py",
    "code": "agents/implementer.py",
    "command": "agents/implementer.py",
    "test": "agents/tester.py",
    "validate": "agents/tester.py",
    "check": "agents/tester.py",
    "document": "agents/documenter.py",
    "doc": "agents/documenter.py",
    "man": "agents/documenter.py",
    "lore": "agents/documenter.py",
    "generate": "agents/content_generator.py",
    "content": "agents/content_generator.py",
    "challenge": "agents/content_generator.py",
    "story": "agents/content_generator.py",
    "analyze": "agents/implementer.py",
    "audit": "agents/implementer.py",
    "improve": "agents/implementer.py",
    "fix": "agents/implementer.py",
    "refactor": "agents/implementer.py",
    "play": "agents/player.py",
}

_ALLOWED_AGENTS = frozenset(
    {
        "agents/implementer.py",
        "agents/tester.py",
        "agents/documenter.py",
        "agents/content_generator.py",
        "agents/player.py",
        "agents/orchestrator.py",
    }
)


def log(level: str, msg: str, **ctx):
    ts = time.strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[36m",
        "OK": "\033[32m",
        "WARN": "\033[33m",
        "ERROR": "\033[31m",
        "TASK": "\033[35m",
        "DISPATCH": "\033[34m",
    }
    c = colors.get(level, "\033[0m")
    r = "\033[0m"
    kv = "  ".join(f"{k}={v}" for k, v in ctx.items())
    print(f"{c}[{level}]{r} {ts} {msg}" + (f"  | {kv}" if kv else ""))


def _post(path: str, data: dict) -> dict:
    try:
        req = urllib.request.Request(
            BASE_URL + path,
            json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def _route_task(task: dict) -> str:
    task_type = task.get("type", task.get("agent", "")).lower()
    title = task.get("title", "").lower()

    agent = AGENT_ROUTING.get(task_type)
    if agent:
        return agent

    for keyword, agent_script in AGENT_ROUTING.items():
        if keyword in title:
            return agent_script

    return "agents/implementer.py"


def _infer_spawn_role(task: dict) -> str:
    for key in ("role", "target"):
        value = str(task.get(key, "")).strip().lower()
        if value in SWARM_ROLES:
            return value

    haystack = " ".join(
        [
            str(task.get("title", "")),
            str(task.get("details", "")),
        ]
    ).lower()
    for role in sorted(SWARM_ROLES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(role)}\b", haystack):
            return role
    return "custom"


def _write_task_update(task_path: Path, status: str, result: str) -> None:
    if task_path.exists():
        with open(task_path) as f:
            updated = json.load(f)
    else:
        updated = {}
    updated["status"] = status
    updated["result"] = result
    updated["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    task_path.write_text(json.dumps(updated, indent=2))


def _llm_decompose(description: str) -> list[dict]:
    result = _post(
        "/api/llm/generate",
        {
            "prompt": (
                f"Break this development task into 1-4 specific sub-tasks for Terminal Depths:\n"
                f"Task: {description}\n\n"
                f"For each sub-task output a JSON object on its own line:\n"
                f'{{ "title": "...", "type": "implement|test|document|generate", "details": "..." }}\n'
                f"Output ONLY the JSON lines, nothing else."
            ),
            "max_tokens": 300,
            "temperature": 0.3,
        },
    )
    text = result.get("text", "")
    tasks = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                t = json.loads(line)
                if "title" in t:
                    tasks.append(t)
            except json.JSONDecodeError:
                pass
    if not tasks:
        tasks = [{"title": description, "type": "implement", "details": description}]
    return tasks


def create_task(
    title: str,
    task_type: str = "implement",
    details: str = "",
    priority: int = 5,
    target: str = "",
) -> str:
    task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    task = {
        "id": task_id,
        "title": title,
        "type": task_type,
        "details": details,
        "target": target,
        "priority": priority,
        "status": "pending",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "result": "",
    }
    path = FILE_TASKS_DIR / f"{task_id}.json"
    path.write_text(json.dumps(task, indent=2))
    log("TASK", f"Created: {title}", id=task_id, type=task_type)
    return task_id


def load_tasks(status_filter: str | None = "pending") -> list[dict]:
    tasks = []
    for path in sorted(FILE_TASKS_DIR.glob("*.json")):
        try:
            t = json.load(open(path))
            t["_path"] = str(path)
            if status_filter is None or t.get("status") == status_filter:
                tasks.append(t)
        except Exception:
            pass
    return sorted(tasks, key=lambda t: t.get("priority", 5))


def dispatch_task(task: dict, dry_run: bool = False) -> dict:
    task_type = str(task.get("type", "")).lower()
    if task_type == "spawn_agent":
        role = _infer_spawn_role(task)
        if dry_run:
            return {"ok": True, "dry_run": True, "type": "spawn_agent", "role": role}

        payload = {
            "role": role,
            "name": task.get("name"),
            "personality": task.get("personality", "professional"),
            "spawned_by": task.get("spawned_by", "dispatch_task"),
        }
        result = _post("/api/swarm/spawn", payload)
        success = bool(result.get("ok"))
        summary = json.dumps(result, ensure_ascii=False)
        task_path = FILE_TASKS_DIR / f"{task['id']}.json"
        _write_task_update(task_path, "done" if success else "failed", summary)
        log(
            "OK" if success else "WARN",
            f"Spawn task {'complete' if success else 'failed'}: {task['title']}",
            role=role,
        )
        return {"ok": success, "output": summary, "role": role}

    agent_script = _route_task(task)

    if agent_script not in _ALLOWED_AGENTS:
        log("ERROR", f"Agent not in allowlist: {agent_script}")
        return {"ok": False, "error": "agent not allowed"}

    agent_path = BASE_DIR / agent_script
    if not agent_path.exists():
        log("WARN", f"Agent script not found: {agent_script}")
        return {"ok": False, "error": "agent not found"}

    log("DISPATCH", f"{task['title']}", agent=agent_script, id=task.get("id", "?"))

    if dry_run:
        return {"ok": True, "dry_run": True, "agent": agent_script}

    try:
        result = subprocess.run(
            [sys.executable, str(agent_path), "--task", task["id"]],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(BASE_DIR),
        )

        success = result.returncode == 0
        output = (result.stdout + result.stderr).strip()[-500:]

        task_path = FILE_TASKS_DIR / f"{task['id']}.json"
        updated = json.loads(task_path.read_text()) if task_path.exists() else task
        if updated.get("status") not in ("done", "failed"):
            _write_task_update(task_path, "done" if success else "failed", output)

        if success:
            log("OK", f"Task complete: {task['title']}")
        else:
            log("WARN", f"Task failed: {task['title']}", rc=result.returncode)

        return {"ok": success, "output": output, "agent": agent_script}

    except subprocess.TimeoutExpired:
        log("ERROR", f"Task timed out: {task['title']}")
        task_path = FILE_TASKS_DIR / f"{task['id']}.json"
        if task_path.exists():
            _write_task_update(task_path, "failed", "timeout")
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        log("ERROR", f"Dispatch error: {e}")
        return {"ok": False, "error": str(e)}


def show_status():
    all_tasks = load_tasks(status_filter=None)
    by_status: dict = {}
    for t in all_tasks:
        s = t.get("status", "unknown")
        by_status.setdefault(s, []).append(t)

    print(f"\n{'='*50}")
    print(f"  TASK QUEUE STATUS  |  {len(all_tasks)} total")
    print(f"{'='*50}")
    for status, tasks in sorted(by_status.items()):
        color = {
            "pending": "\033[33m",
            "done": "\033[32m",
            "failed": "\033[31m",
            "running": "\033[36m",
        }.get(status, "\033[0m")
        print(f"{color}  {status.upper():<12}\033[0m {len(tasks)}")
        if status == "pending":
            for t in tasks[:5]:
                print(f"    - [{t.get('type','?'):12}] {t.get('title','?')[:60]}")

    pending = by_status.get("pending", [])
    if pending:
        print(f"\n  Next up: {pending[0].get('title','?')}")
    print()


def flush_completed():
    done_dir = FILE_TASKS_DIR / "done"
    done_dir.mkdir(exist_ok=True)
    moved = 0
    for path in FILE_TASKS_DIR.glob("*.json"):
        try:
            t = json.load(open(path))
            if t.get("status") in ("done", "failed"):
                path.rename(done_dir / path.name)
                moved += 1
        except Exception:
            pass
    log("OK", f"Flushed {moved} completed tasks to tasks/legacy_runtime/done/")


def main():
    ap = argparse.ArgumentParser(description="Terminal Depths task dispatcher")
    ap.add_argument(
        "--create", metavar="DESCRIPTION", help="Create and dispatch a new task"
    )
    ap.add_argument(
        "--type",
        default="implement",
        help="Task type (implement/test/document/generate/spawn_agent)",
    )
    ap.add_argument(
        "--decompose",
        action="store_true",
        help="Use LLM to decompose --create into sub-tasks",
    )
    ap.add_argument("--status", action="store_true", help="Show queue status")
    ap.add_argument("--list", action="store_true", help="List all tasks")
    ap.add_argument("--task", metavar="TASK_ID", help="Dispatch specific task by ID")
    ap.add_argument(
        "--flush", action="store_true", help="Move done/failed tasks to tasks/done/"
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="Show what would run, don't execute"
    )
    ap.add_argument(
        "--limit", type=int, default=5, help="Max tasks to dispatch in one run"
    )
    args = ap.parse_args()

    if args.status:
        show_status()
        return

    if args.flush:
        flush_completed()
        return

    if args.list:
        tasks = load_tasks(status_filter=None)
        for t in tasks:
            status_color = {
                "done": "\033[32m",
                "failed": "\033[31m",
                "pending": "\033[33m",
            }.get(t.get("status", ""), "\033[0m")
            print(
                f"{status_color}[{t.get('status','?'):8}]\033[0m  {t.get('id','?'):35}  {t.get('title','?')[:50]}"
            )
        return

    if args.create:
        if args.decompose:
            log("INFO", "Decomposing task with LLM...")
            sub_tasks = _llm_decompose(args.create)
            ids = []
            for st in sub_tasks:
                tid = create_task(
                    title=st.get("title", args.create),
                    task_type=st.get("type", args.type),
                    details=st.get("details", ""),
                )
                ids.append(tid)
            log("INFO", f"Created {len(ids)} sub-tasks")
            tasks_to_run = [load_tasks()[0]] if load_tasks() else []
        else:
            tid = create_task(args.create, task_type=args.type)
            tasks_to_run = [t for t in load_tasks() if t["id"] == tid]
    elif args.task:
        tasks_to_run = [
            t for t in load_tasks(status_filter=None) if t["id"] == args.task
        ]
        if not tasks_to_run:
            log("ERROR", f"Task not found: {args.task}")
            return
    else:
        tasks_to_run = load_tasks()[: args.limit]

    if not tasks_to_run:
        log("INFO", "No pending tasks to dispatch")
        show_status()
        return

    log("INFO", f"Dispatching {len(tasks_to_run)} task(s)")
    results = {"ok": 0, "fail": 0}
    for task in tasks_to_run:
        r = dispatch_task(task, dry_run=args.dry_run)
        if r.get("ok"):
            results["ok"] += 1
        else:
            results["fail"] += 1

    log("OK", "Dispatch complete", succeeded=results["ok"], failed=results["fail"])


if __name__ == "__main__":
    main()
