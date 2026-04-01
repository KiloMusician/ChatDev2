"""Simple CLI for nusyq task runtime (Phase 1 tooling).

Usage examples:
  python scripts/nusyq_task.py create "Build Windows EXE" --project "SimulatedVerse"
  python scripts/nusyq_task.py list
  python scripts/nusyq_task.py start 1 --cmd "echo hello && dir"
"""

import argparse
import sys

from src.task_runtime.manager import TaskManager


def main(argv=None):
    parser = argparse.ArgumentParser(prog="nusyq_task")
    sub = parser.add_subparsers(dest="cmd")

    p_create = sub.add_parser("create")
    p_create.add_argument("objective")

    p_list = sub.add_parser("list")
    p_list.add_argument("--status", default=None)

    p_start = sub.add_parser("start")
    p_start.add_argument("task_id", type=int)
    p_start.add_argument("--cmd", required=True)

    args = parser.parse_args(argv)
    manager = TaskManager()

    if args.cmd == "create":
        tid = manager.create_task(args.objective)
        print(f"Created task {tid}")
        return 0

    if args.cmd == "list":
        rows = manager.list_tasks(status=args.status)
        for t in rows:
            print(f"[{t.id}] {t.status} - {t.objective}")
        return 0

    if args.cmd == "start":
        run_id = manager.start_run(args.task_id, args.cmd)
        print(f"Started run {run_id} for task {args.task_id}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
