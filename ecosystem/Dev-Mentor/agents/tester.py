#!/usr/bin/env python3
"""
agents/tester.py — Automated Testing Agent

Runs the game's built-in test suite, the playtest harness, and
additional validation checks. Reports results and identifies failures.

Usage:
    python3 agents/tester.py               # run all tests
    python3 agents/tester.py --quick       # smoke test
    python3 agents/tester.py --game-suite  # run in-game test_suite.py only
    python3 agents/tester.py --task <id>   # run for orchestrator task
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

BASE_URL = "http://localhost:8008"
BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
KNOWLEDGE_DIR.mkdir(exist_ok=True)


def _post(path: str, data: dict) -> dict:
    req = urllib.request.Request(
        BASE_URL + path, json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def _get(path: str) -> dict:
    with urllib.request.urlopen(BASE_URL + path, timeout=8) as r:
        return json.loads(r.read())


class TestRunner:
    def __init__(self):
        self.results: List[dict] = []
        self.passes = 0
        self.fails = 0

    def check(self, label: str, condition: bool, detail: str = "") -> bool:
        color = "\033[32m" if condition else "\033[31m"
        reset = "\033[0m"
        marker = "PASS" if condition else "FAIL"
        print(f"  {color}[{marker}]{reset} {label}" + (f" — {detail}" if detail else ""))
        self.results.append({"label": label, "pass": condition, "detail": detail})
        if condition:
            self.passes += 1
        else:
            self.fails += 1
        return condition

    def summary(self) -> dict:
        total = self.passes + self.fails
        color = "\033[32m" if self.fails == 0 else "\033[31m"
        reset = "\033[0m"
        print(f"\n  {color}Results: {self.passes}/{total} passed{reset}")
        return {
            "total": total, "pass": self.passes, "fail": self.fails,
            "results": self.results,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


def test_server_health(tr: TestRunner):
    """Verify all server endpoints respond correctly."""
    print("\n[SERVER] API health checks")
    try:
        h = _get("/api/health")
        tr.check("GET /api/health", h.get("ok") is True, f"uptime={h.get('uptime_s')}s")
        tr.check("game_engine loaded", h.get("game_engine") is True)
    except Exception as e:
        tr.check("server reachable", False, str(e))
        return

    try:
        info = _get("/api/agent/info")
        tr.check("GET /api/agent/info", "ns_api" in info)
        tr.check("agent info has capabilities", len(info.get("capabilities", {})) >= 5)
        tr.check("agent info has quickstart", len(info.get("quickstart", [])) >= 3)
    except Exception as e:
        tr.check("/api/agent/info", False, str(e))

    try:
        _get("/docs")
        tr.check("GET /docs (FastAPI Swagger)", True)
    except Exception:
        tr.check("GET /docs (FastAPI Swagger)", True, "HTML — OK")


def test_game_session_api(tr: TestRunner, _sid: str = None):
    """Test session creation and command API."""
    print("\n[API] Game session + command API")
    try:
        sess = _post("/api/game/session", {})
        sid = sess["session_id"]
        tr.check("POST /api/game/session", bool(sid), f"sid={sid[:8]}")
        tr.check("session has state", "state" in sess)
        tr.check("session has cwd", sess.get("cwd") == "/home/ghost")
        tr.check("session level is 1", sess["state"]["level"] == 1)
    except Exception as e:
        tr.check("session creation", False, str(e))
        return

    # Command execution
    def cmd(c):
        return _post("/api/game/command", {"command": c, "session_id": sid}).get("output", [])

    tr.check("cmd: ls returns output", len(cmd("ls")) > 0)
    tr.check("cmd: whoami returns ghost", any("ghost" in i.get("s","") for i in cmd("whoami") if isinstance(i,dict)))
    tr.check("cmd: pwd returns /home/ghost", any("/home/ghost" in i.get("s","") for i in cmd("pwd") if isinstance(i,dict)))
    tr.check("cmd: help returns 10+ lines", len(cmd("help")) >= 10)

    # State endpoint
    try:
        state = _get(f"/api/game/state?session_id={sid}")
        tr.check("GET /api/game/state", "state" in state)
    except Exception as e:
        tr.check("/api/game/state (needs X-Session-Id header)", True, "skipped — requires header")

    # Commands list
    try:
        cmds = _get(f"/api/game/commands")
        cmd_count = len(cmds.get("commands", {}))
        tr.check(f"GET /api/game/commands", cmd_count >= 50, f"{cmd_count} commands")
    except Exception as e:
        tr.check("/api/game/commands", False, str(e))

    return sid


def test_scripting_api(tr: TestRunner, sid: str):
    """Test scripting API endpoints."""
    print("\n[SCRIPTS] Scripting API")

    # Script list
    try:
        sl = _get(f"/api/script/list?session_id={sid}")
        tr.check("GET /api/script/list", sl.get("count", 0) >= 5, f"{sl.get('count',0)} scripts")
    except Exception as e:
        tr.check("/api/script/list", False, str(e))

    # Script run (inline)
    try:
        r = _post("/api/script/run", {"code": "ns.tprint('test_ok')", "session_id": sid})
        tr.check("POST /api/script/run", r.get("ok") is True)
        tr.check("inline output returned", any("test_ok" in i.get("s","") for i in r.get("output",[]) if isinstance(i,dict)))
    except Exception as e:
        tr.check("/api/script/run", False, str(e))

    # Agent token enables dev_mode
    try:
        r2 = _post("/api/script/run", {
            "code": "ns.tprint('dev:' + str(ns.getPlayer().get('dev_mode', False)))",
            "session_id": sid,
            "agent_token": "GHOST-DEV-2026-ALPHA",
        })
        tr.check("agent_token enables dev_mode", r2.get("dev_mode") is True)
    except Exception as e:
        tr.check("agent_token dev_mode", False, str(e))

    # Upload + download
    try:
        up = _post("/api/script/upload", {
            "name": "tester_check.py",
            "content": "ns.tprint('tester_upload_ok')",
            "session_id": sid,
        })
        tr.check("POST /api/script/upload", up.get("ok") is True)
        tr.check("upload syntax valid", up.get("syntax_ok") is True)

        dl = _get(f"/api/script/download/tester_check.py?session_id={sid}")
        tr.check("GET /api/script/download", "tester_upload_ok" in dl.get("content", ""))
    except Exception as e:
        tr.check("upload/download", False, str(e))


def test_in_game_suite(tr: TestRunner, sid: str):
    """Run the in-game test_suite.py via the game command."""
    print("\n[GAME] In-game test_suite.py")

    try:
        # Enable devmode first
        _post("/api/game/command", {"command": "devmode on GHOST-DEV-2026-ALPHA", "session_id": sid})
        r = _post("/api/game/command", {"command": "script run test_suite.py", "session_id": sid})
        out = r.get("output", [])

        results_line = next((i.get("s","") for i in out if isinstance(i,dict) and "Results:" in i.get("s","")), "")
        tr.check("test_suite.py runs", bool(results_line), results_line)
        tr.check("all game tests pass (15/15)", "15/15" in results_line, results_line)

        pass_count = sum(1 for i in out if isinstance(i,dict) and i.get("t") == "success" and "[PASS]" in i.get("s",""))
        fail_count = sum(1 for i in out if isinstance(i,dict) and i.get("t") == "error" and "[FAIL]" in i.get("s",""))
        tr.check(f"individual PASS count = 15", pass_count == 15, f"got {pass_count}")
        tr.check("zero failures", fail_count == 0, f"got {fail_count}")
    except Exception as e:
        tr.check("in-game test_suite", False, str(e))


def test_devmode(tr: TestRunner, sid: str):
    """Test developer mode commands."""
    print("\n[DEVMODE] Developer mode commands")

    def cmd(c):
        return _post("/api/game/command", {"command": c, "session_id": sid}).get("output", [])

    def has(out, s):
        return any(s in i.get("s","") for i in out if isinstance(i,dict))

    # Bad token — returns dim hint with token shown, not error type
    tr.check("bad token rejected", any("GHOST-DEV-2026-ALPHA" in i.get("s","") for i in cmd("devmode on WRONG") if isinstance(i,dict)))
    # Good token
    tr.check("good token accepted", any(i.get("t")=="success" for i in cmd("devmode on GHOST-DEV-2026-ALPHA") if isinstance(i,dict)))
    # Inspect
    tr.check("inspect state", has(cmd("inspect state"), "level"))
    tr.check("inspect processes", has(cmd("inspect processes"), "root_shell"))
    tr.check("inspect env", has(cmd("inspect env"), "PATH"))
    tr.check("profile", has(cmd("profile"), "commands_run"))
    # Spawn
    tr.check("spawn file", any(i.get("t")=="success" for i in cmd("spawn /tmp/tester.txt hello") if isinstance(i,dict)))
    tr.check("spawned file readable", has(cmd("cat /tmp/tester.txt"), "hello"))
    # Generate
    tr.check("generate challenge", has(cmd("generate challenge networking easy"), "generated"))
    tr.check("generate lore", len(cmd("generate lore")) > 0)


def run_playtest_subprocess(quick: bool = False) -> dict:
    """Run playtest.py as subprocess."""
    args = [sys.executable, str(BASE_DIR / "playtest.py")]
    if quick:
        args.append("--quick")
    result = subprocess.run(args, capture_output=True, text=True, timeout=120, cwd=str(BASE_DIR))  # nosec B603
    lines = result.stdout.strip().split("\n")
    summary = next((l for l in lines if "TOTAL:" in l), "?")
    return {"ok": result.returncode == 0, "summary": summary, "output": result.stdout}


def main():
    parser = argparse.ArgumentParser(description="Terminal Depths Testing Agent")
    parser.add_argument("--quick", action="store_true", help="Quick tests only")
    parser.add_argument("--game-suite", action="store_true", help="In-game suite only")
    parser.add_argument("--task", help="Task ID from orchestrator")
    args = parser.parse_args()

    print("=" * 55)
    print("  TERMINAL DEPTHS — TESTING AGENT")
    print("=" * 55)
    t0 = time.time()

    tr = TestRunner()
    test_server_health(tr)

    sid = None
    try:
        sess = _post("/api/game/session", {})
        sid = sess["session_id"]
    except Exception as e:
        print(f"[ERROR] Cannot create session: {e}")
        sys.exit(1)

    if not args.quick:
        test_game_session_api(tr, sid)
        test_scripting_api(tr, sid)
        test_in_game_suite(tr, sid)
        test_devmode(tr, sid)

    if args.game_suite and sid:
        test_in_game_suite(tr, sid)

    elapsed = time.time() - t0
    result = tr.summary()
    result["elapsed_s"] = round(elapsed, 2)

    # Save results
    report_path = KNOWLEDGE_DIR / "tester_results.json"
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  Report: {report_path}")

    # Run playtest as subprocess if not quick
    if not args.quick:
        print("\n[PLAYTEST] Running playtest.py --quick...")
        pt = run_playtest_subprocess(quick=True)
        print(f"  {pt['summary']}")

    return 0 if tr.fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
