# /ops/agents/rg_orchestrator.py
# Python 3.10+
import argparse
import sys
import subprocess
import json
import time
import shutil
import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "logs"
OPS  = ROOT / "ops"
LOGS.mkdir(exist_ok=True, parents=True)

def load_yaml(path: Path):
    try:
        import yaml  # pyyaml
    except Exception:
        print(">> Installing pyyaml locally (no network cache may be used by Replit)...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml", "--quiet"], check=False)
        import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def which(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def any_file_exists(patterns):
    for pat in patterns:
        for p in ROOT.glob("**/*"):
            if p.is_file() and fnmatch.fnmatch(str(p.relative_to(ROOT)), pat):
                return True
    return False

def all_files_exist(paths):
    return all((ROOT / p).exists() for p in paths)

def cap_present(cap):
    cond = cap.get("present_if") or {}
    if "cmd_available" in cond and not which(cond["cmd_available"]): return False
    if "any_file_exists" in cond and not any_file_exists(cond["any_file_exists"]): return False
    if "all_files_exist" in cond and not all_files_exist(cond["all_files_exist"]): return False
    return True

def run_cmd(cmd, timeout_sec=180):
    print(f"$ {cmd}")
    try:
        p = subprocess.run(cmd, shell=True, timeout=timeout_sec, cwd=ROOT)
        return p.returncode
    except subprocess.TimeoutExpired:
        print(f"!! Timeout after {timeout_sec}s")
        return 124

def score_cap(cap, weights):
    # simple static heuristic: higher impact => higher score; lower cost/risk => higher score
    impact = {"low":1,"medium":2,"high":3}.get(cap.get("impact","low"),1)
    risk   = {"low":1,"medium":2,"high":3}.get(cap.get("risk","low"),1)
    # cost tokens always 0 by design here; keep numeric for future
    cost   = cap.get("cost",{}).get("tokens",0)
    speed  = 1  # assume all are ~fast; could be enriched with historical timing
    return (impact*weights["weight_impact"]) - (risk*weights["weight_risk"]) - (cost*weights["weight_cost"]) + (speed*weights["weight_speed"])

def compact_history():
    # read recent git log if present
    rec = {"git": [], "findings": {}, "quests": {}, "docs": {}}
    gitlog = LOGS / "git_recent.log"
    if gitlog.exists():
        rec["git"] = gitlog.read_text(encoding="utf-8").splitlines()[:50]
    scan = LOGS / "scan_findings.txt"
    if scan.exists():
        rec["findings"]["scan"] = scan.read_text(encoding="utf-8").splitlines()[:500]
    pyf = LOGS / "scan_pyflakes.txt"
    if pyf.exists():
        rec["findings"]["pyflakes"] = pyf.read_text(encoding="utf-8").splitlines()[:300]
    qidx = LOGS / "quests_index.json"
    if qidx.exists():
        try: rec["quests"] = json.loads(qidx.read_text(encoding="utf-8"))
        except: pass
    didx = LOGS / "docs_index.json"
    if didx.exists():
        try: rec["docs"] = json.loads(didx.read_text(encoding="utf-8"))
        except: pass
    return rec

def save_report(report):
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = LOGS / f"rg_run_{stamp}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f">> report: {out}")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default=str(OPS / "capabilities.registry.yml"))
    ap.add_argument("--cycle",    default=str(OPS / "playbooks/rg_cycle.yml"))
    ap.add_argument("--max-seconds", type=int, default=900)
    args = ap.parse_args()

    registry = load_yaml(Path(args.registry))
    cycle    = load_yaml(Path(args.cycle))
    weights  = registry.get("meta",{}).get("scoring", registry.get("scoring", {}))
    weights  = {**{"weight_impact":3,"weight_cost":2,"weight_risk":2,"weight_speed":1}, **weights}

    caps_by_id = {c["cap_id"]: c for c in registry["capabilities"]}
    phases = cycle["cycle"]["phases"]
    limits = cycle["cycle"].get("limits",{})
    max_phase_seconds = limits.get("max_phase_seconds", 420)
    max_caps_per_phase = limits.get("max_caps_per_phase", 6)
    help_after = limits.get("ask_for_help_after_sec_without_progress", 120)

    started = time.time()
    report = {"started": started, "phases":[]}
    last_progress_ts = time.time()

    for ph in phases:
        phase_start = time.time()
        used = []
        tried = 0
        phase_log = {"name": ph["name"], "goals": ph.get("goals",[]), "actions":[]}
        print(f"\n=== Phase: {ph['name']} ===")
        try_caps = [caps_by_id[cid] for cid in ph["try_caps"] if cid in caps_by_id]
        # filter by presence
        eligible = [c for c in try_caps if cap_present(c)]
        # sort by score
        eligible.sort(key=lambda c: -score_cap(c, weights))

        for cap in eligible[:max_caps_per_phase]:
            if time.time() - phase_start > max_phase_seconds:
                print(f"-- Phase time budget reached ({max_phase_seconds}s)")
                break
            tried += 1
            print(f"-> {cap['label']} [{cap['cap_id']}]")
            any_success = False
            for cmd in cap.get("cmds", []):
                rc = run_cmd(cmd, timeout_sec=cap.get("timeout_sec", registry["defaults"]["timeout_sec"]))
                if rc == 0 or rc == 1 or rc == 2:  # non-fatal for diagnostic tasks
                    any_success = True
                else:
                    print(f"   (non-zero rc={rc}, continuing)")
            phase_log["actions"].append({"cap_id": cap["cap_id"], "ok": any_success, "time": time.time()})
            if any_success:
                last_progress_ts = time.time()
                used.append(cap["cap_id"])

            # help nudge if stuck too long
            if time.time() - last_progress_ts > help_after:
                hint = "ZETA-HELP: Reorder tasks, pick a different capability, or run diag.ripgrep_errors; avoid token use; commit small; then retry build."
                print(f"!! No progress for {help_after}s — {hint}")
                phase_log.setdefault("hints",[]).append(hint)
                last_progress_ts = time.time()

        # summarize phase
        report["phases"].append(phase_log)
        if time.time() - started > args.max_seconds:
            print(f"== Overall time budget reached ({args.max_seconds}s). Exiting.")
            break

    report["history_compact"] = compact_history()
    save_report(report)
    print(">> Orchestrator finished.")

if __name__ == "__main__":
    main()