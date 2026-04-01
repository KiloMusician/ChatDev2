#!/usr/bin/env python3
import json
import sys
import time
import pathlib
import subprocess
import random

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "engine" / "weights.json").read_text()) if (ROOT / "engine" / "weights.json").exists() else {
  "llm_enabled": False,
  "token_budget": {"window": "session", "max_tokens": 0, "burst": 0},
  "priority": ["fix:errors","tests:green","perf:hot","mobile:ui","docs:track","ascii:ux","idl:mechanics","exp:lore","sync:gh"]
}

def zero_token_tasks():
  # Heuristics—fast scans & auto-fixers that cost no tokens
  return [
    ["npm","run","lint"], ["npm","run","fmt"],
    ["bash","scripts/rif","doctor"],
    ["python3","engine/tools/repair.py","--quick"],
    ["npm","test"]
  ]

def maybe_use_llm():
  if not CFG.get("llm_enabled"): return False
  budget = CFG["token_budget"]["max_tokens"]
  return budget and budget > 0

def run(cmd):
  print(f"→ {' '.join(cmd)}")
  try:
    subprocess.run(cmd, cwd=ROOT, check=False)
  except Exception as e:
    print("! error:", e)

def choose_next():
  # Very lightweight scheduler: shuffle priorities, prefer unresolved areas
  priorities = CFG.get("priority", [])
  random.shuffle(priorities)
  return priorities[:5]

def main():
  mode = "--mode=full" in " ".join(sys.argv) and "full" or ("--mode=micro" in " ".join(sys.argv) and "micro" or "micro")
  no_llm = "--no-llm" in sys.argv
  maybe_llm_flag = "--maybe-llm" in sys.argv

  print("[cascade] mode:", mode)
  for zt in zero_token_tasks():
    run(zt)

  next5 = choose_next()
  print("[cascade] focus lanes:", next5)

  if maybe_llm_flag and not no_llm and maybe_use_llm():
    # Placeholder: call agent gateway only if budget permits (external token spend zone)
    run(["python3","engine/tools/agent_gateway.py","--lane",",".join(next5)])
  else:
    print("[cascade] zero-token route selected (no external calls).")

  # Log a tiny progress memo for the Temple of Knowledge
  tk = ROOT / "docs" / "temple" / "floor-01" / "progress.log"
  tk.parent.mkdir(parents=True, exist_ok=True)
  with open(tk,"a",encoding="utf-8") as f:
    f.write(f"{int(time.time())}\t{mode}\t{json.dumps(next5)}\n")

if __name__ == "__main__":
  main()