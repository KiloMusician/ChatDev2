from __future__ import annotations
import argparse
import os
from .selector import load_plan, select_next
from .history import History
from .executor import execute

def main():
    ap = argparse.ArgumentParser(description="ΞNuSyQ Smart Orchestrator - Prefer improve existing over new")
    ap.add_argument("--plan", required=True, help="Path to task_queue.yml")
    ap.add_argument("--batch", type=int, default=None, help="Max tasks to select")
    ap.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    args = ap.parse_args()

    if not os.path.exists(args.plan):
        print(f"❌ Plan file not found: {args.plan}")
        return 1

    try:
        plan = load_plan(args.plan)
        hist = History(plan.meta.get("log_dir", "./.orchestrator/logs"))

        batch = args.batch or plan.meta.get("max_batch", 5)
        picks = select_next(plan, hist, limit=batch)

        # Log decisions for learning
        for d in picks:
            hist.log_decision({
                "task_id": d.task_id,
                "score": d.score,
                "reasons": d.reasons,
                "action": d.chosen_action
            })

        print("🧠 ΞNuSyQ Smart Orchestrator")
        print("═══════════════════════════")
        print(f"📋 Plan: {plan.meta['name']}")
        print(f"🎯 Mode: {plan.meta.get('token_budget_mode', 'offline')} (prefer existing modules)")
        print(f"📊 Selected {len(picks)}/{len(plan.tasks)} tasks")
        print()

        print("--- SELECTED TASKS ---")
        for i, d in enumerate(picks, 1):
            print(f"{i}. {d.task_id}  score={d.score:.2f}  action={d.chosen_action}")
            for r in d.reasons:
                print(f"   • {r}")
            print()

        if picks:
            execute(picks, plan.tasks, dry=args.dry_run)
            
            if args.dry_run:
                print("💡 Remove --dry-run to execute the selected tasks")
            else:
                print("🎉 All selected tasks completed!")
        else:
            print("ℹ️  No tasks selected. All may be complete or require manual intervention.")
            
        return 0
        
    except Exception as e:
        print(f"❌ Orchestrator error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())