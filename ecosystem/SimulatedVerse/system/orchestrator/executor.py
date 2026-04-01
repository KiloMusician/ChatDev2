from __future__ import annotations
import subprocess
import os
from typing import List
from .task_types import Decision, Task
from .module_index import test_command

def run_cmd(cmd: List[str]) -> int:
    print("$", " ".join(cmd), flush=True)
    return subprocess.call(cmd)

def execute(decisions: List[Decision], tasks: List[Task], dry: bool=True) -> None:
    task_map = {t.id:t for t in tasks}
    for d in decisions:
        t = task_map[d.task_id]
        print(f"\n==> {t.id}: {t.title} [{t.kind}] score={d.score:.2f}")
        print("Reasons:", ", ".join(d.reasons))
        print("Action:", d.chosen_action)
        print("Targets:", ", ".join(t.targets))
        if t.notes: print("Notes:", t.notes)

        if dry: 
            print("DRY-RUN: logging only.") 
            continue

        # Example conservative actions — expand as needed:
        if t.kind in ("fix","complete","refactor"):
            # run tests first to reproduce
            run_cmd(test_command())
            # static checks for ΞNuSyQ (use what we have)
            if os.path.exists("tools/simbot.mjs"):
                run_cmd(["node", "tools/simbot.mjs"])
            if os.path.exists("tools/taskOrganizer.mjs"):
                run_cmd(["node", "tools/taskOrganizer.mjs", "ops/tasks.yaml"])
            # after code edits (human+agent), test again
            run_cmd(test_command())

        if t.kind == "test":
            run_cmd(test_command())
            # Additional ΞNuSyQ consciousness tests
            if "consciousness" in " ".join(t.targets):
                run_cmd(["node", "src/engine/consciousness.mjs", "--test"])

        if t.kind == "docs":
            # Update replit.md with architecture changes
            if "architecture" in " ".join(t.targets):
                print("📝 Remember to update replit.md with architecture documentation")

        if t.kind == "perf":
            # Run performance guards and profiling
            if os.path.exists("src/engine/perf_guard.mjs"):
                run_cmd(["node", "src/engine/perf_guard.mjs", "--report"])

        # Commit small, frequent
        run_cmd(["git","add","."])
        run_cmd(["git","commit","-m", f"orchestrator: {t.id} {t.title} (score {d.score:.2f})"])
        
        print(f"✅ Completed {t.id} with score {d.score:.2f}")
        print("─" * 50)