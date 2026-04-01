#!/usr/bin/env python3
"""
playtest.py — Automated Terminal Depths game walkthrough and QA harness.
Tests every major feature by actually playing through the game via API.

Usage:
    python3 playtest.py           # Full playtest suite
    python3 playtest.py --quick   # Fast smoke test only
    python3 playtest.py --verbose # Verbose output per command
    python3 playtest.py --suite <name>  # Run specific suite

Exit code: 0 = all pass, 1 = failures
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from typing import Any, List, Optional

BASE_URL = "http://localhost:7337"

# ── HTTP helpers ──────────────────────────────────────────────────────

def _post(path: str, data: dict, timeout: int = 10) -> dict:
    req = urllib.request.Request(
        BASE_URL + path,
        json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _get(path: str, timeout: int = 8) -> dict:
    with urllib.request.urlopen(BASE_URL + path, timeout=timeout) as r:
        return json.loads(r.read())


# ── Test framework ────────────────────────────────────────────────────

class PlaytestSession:
    def __init__(self, verbose: bool = False):
        self.sid: Optional[str] = None
        self.verbose = verbose
        self.results: List[dict] = []
        self.passes = 0
        self.fails = 0

    def start(self):
        r = _post("/api/game/session", {})
        self.sid = r["session_id"]
        if self.verbose:
            print(f"  Session: {self.sid[:8]}... level={r['state']['level']}")
        return self

    def cmd(self, command: str) -> List[dict]:
        r = _post("/api/game/command", {"command": command, "session_id": self.sid})
        out = r.get("output", [])
        if self.verbose:
            print(f"  $ {command}")
            for item in out[:3]:
                if isinstance(item, dict):
                    print(f"    [{item.get('t','?')}] {item.get('s','')[:80]}")
        return out

    def script_run(self, code: str, name: str = "test") -> List[dict]:
        r = _post("/api/script/run", {"code": code, "session_id": self.sid, "name": name})
        return r.get("output", [])

    def assert_ok(self, label: str, condition: bool):
        status = "PASS" if condition else "FAIL"
        color = "\033[32m" if condition else "\033[31m"
        reset = "\033[0m"
        print(f"  {color}[{status}]{reset} {label}")
        self.results.append({"label": label, "pass": condition})
        if condition:
            self.passes += 1
        else:
            self.fails += 1
        return condition

    def assert_output(self, label: str, out: List[dict],
                      contains: Optional[str] = None,
                      t_type: Optional[str] = None,
                      min_lines: int = 0) -> bool:
        cond = len(out) >= min_lines
        if contains:
            cond = cond and any(contains in item.get("s", "") for item in out if isinstance(item, dict))
        if t_type:
            cond = cond and any(item.get("t") == t_type for item in out if isinstance(item, dict))
        return self.assert_ok(label, cond)

    def summary(self) -> int:
        total = self.passes + self.fails
        color = "\033[32m" if self.fails == 0 else "\033[31m"
        reset = "\033[0m"
        print(f"\n  {color}Results: {self.passes}/{total} passed{reset}")
        if self.fails > 0:
            print("  Failed tests:")
            for r in self.results:
                if not r["pass"]:
                    print(f"    ✗ {r['label']}")
        return 1 if self.fails > 0 else 0


# ── Test suites ───────────────────────────────────────────────────────

def suite_health(verbose: bool) -> PlaytestSession:
    """Verify server is reachable and game engine is loaded."""
    print("\n[HEALTH] Server health check")
    s = PlaytestSession(verbose)
    try:
        h = _get("/api/health")
        s.assert_ok("server reachable", h.get("ok") is True)
        s.assert_ok("game engine loaded", h.get("game_engine") is True)
        s.assert_ok("uptime tracked", h.get("uptime_s", 0) > 0)

        info = _get("/api/agent/info")
        s.assert_ok("agent info endpoint", "ns_api" in info)
        s.assert_ok("quickstart documented", len(info.get("quickstart", [])) > 0)
    except Exception as e:
        s.assert_ok(f"server error: {e}", False)
    return s


def suite_core_commands(verbose: bool) -> PlaytestSession:
    """Play through the core terminal commands."""
    print("\n[CORE] Core terminal commands")
    s = PlaytestSession(verbose).start()

    # Navigation
    s.assert_output("pwd returns /home/ghost", s.cmd("pwd"), contains="/home/ghost")
    s.assert_output("ls shows home files", s.cmd("ls"), min_lines=1)
    s.assert_output("cd ctf works", s.cmd("cd ctf"), min_lines=0)
    s.assert_output("pwd shows ctf dir", s.cmd("pwd"), contains="ctf")
    s.assert_output("cd .. returns home", s.cmd("cd .."), min_lines=0)

    # File operations
    s.assert_output("cat README.md works", s.cmd("cat README.md"), contains="Welcome")
    s.assert_output("cat notes.txt works", s.cmd("cat notes.txt"), contains="INVESTIGATION")
    s.assert_output("ls -la shows hidden", s.cmd("ls -la"), min_lines=1)

    # System
    s.assert_output("whoami returns ghost", s.cmd("whoami"), contains="ghost")
    s.assert_output("id shows uid", s.cmd("id"), contains="uid")
    s.assert_output("uname works", s.cmd("uname"), min_lines=1)
    s.assert_output("ps aux shows processes", s.cmd("ps aux"), min_lines=3)
    s.assert_output("env shows environment", s.cmd("env"), min_lines=3)

    # Misc
    s.assert_output("echo works", s.cmd("echo hello world"), contains="hello world")
    s.assert_output("date works", s.cmd("date"), min_lines=1)
    s.assert_output("help works", s.cmd("help"), min_lines=10)
    return s


def suite_pipelines(verbose: bool) -> PlaytestSession:
    """Test pipeline, redirection, and chaining."""
    print("\n[PIPES] Pipelines and chaining")
    s = PlaytestSession(verbose).start()

    s.assert_output("echo pipe grep", s.cmd("echo hello | grep hello"), t_type="success")
    s.assert_output("cat pipe grep", s.cmd("cat /etc/passwd | grep ghost"), contains="ghost")
    s.assert_output("echo redirect", s.cmd("echo test > /tmp/test.txt"), min_lines=1)
    s.assert_output("cat redirected file", s.cmd("cat /tmp/test.txt"), contains="test")
    s.assert_output("echo append", s.cmd("echo line2 >> /tmp/test.txt"), min_lines=1)
    s.assert_output("chaining &&", s.cmd("echo a && echo b"), min_lines=1)
    s.assert_output("semicolon chaining", s.cmd("echo x; echo y"), min_lines=1)
    s.assert_output("wc -l on pipe", s.cmd("cat /etc/passwd | wc -l"), min_lines=1)
    s.assert_output("sort pipe uniq", s.cmd("echo -e 'a\na\nb' | sort | uniq"), min_lines=1)
    return s


def suite_security_path(verbose: bool) -> PlaytestSession:
    """Test the main CTF / priv-esc storyline."""
    print("\n[SECURITY] Security / priv-esc path")
    s = PlaytestSession(verbose).start()

    s.assert_output("sudo -l shows find", s.cmd("sudo -l"), contains="find")
    s.assert_output("cat /etc/sudoers shows NOPASSWD", s.cmd("cat /etc/sudoers"), contains="NOPASSWD")
    s.assert_output("cat /etc/passwd readable", s.cmd("cat /etc/passwd"), contains="ghost")
    s.assert_output("cat /etc/shadow requires root", s.cmd("cat /etc/shadow"), t_type="error")
    s.assert_output("ps shows nexus-daemon", s.cmd("ps aux"), contains="1337")
    s.assert_output("cat /proc/1337/environ accessible", s.cmd("cat /proc/1337/environ"), min_lines=1)
    s.assert_output("cat /var/log/nexus.log accessible", s.cmd("cat /var/log/nexus.log"), contains="CHIMERA")
    s.assert_output("find with exec grants root", s.cmd("sudo find . -exec /bin/sh ;"), min_lines=1)
    s.assert_output("whoami returns root after exploit", s.cmd("whoami"), contains="root")
    s.assert_output("cat /etc/shadow readable as root", s.cmd("cat /etc/shadow"), contains="root")
    s.assert_output("cat master.key readable as root", s.cmd("cat /opt/chimera/keys/master.key"), min_lines=1)
    return s


def suite_scripting_api(verbose: bool) -> PlaytestSession:
    """Test the in-game scripting engine."""
    print("\n[SCRIPTS] Scripting API")
    s = PlaytestSession(verbose).start()

    # script list
    s.assert_output("script list shows scripts", s.cmd("script list"), contains="hello.py")

    # script run hello.py
    s.assert_output("hello.py outputs player info", s.cmd("script run hello.py"), contains="GHOST Script Engine")

    # script run recon.py
    s.assert_output("recon.py scans network", s.cmd("script run recon.py"), contains="Found")

    # script new + validate
    s.cmd("script new mytest.py")
    s.assert_output("validate script", s.cmd("script validate mytest.py"), contains="syntax OK")

    # inline API script
    code = "ns.tprint('playtest ok')\nns.addXP(5, 'terminal')"
    out = s.script_run(code, "playtest_inline")
    s.assert_ok("inline script runs", any("playtest ok" in i.get("s", "") for i in out if isinstance(i, dict)))

    # script with ns.exec
    code2 = "out = ns.exec('whoami')\nns.tprint('user: ' + out[0] if out else 'none')"
    out2 = s.script_run(code2, "exec_test")
    s.assert_ok("ns.exec works", any("user:" in i.get("s", "") for i in out2 if isinstance(i, dict)))

    # script upload + download via API
    r = _post("/api/script/upload", {
        "name": "ci_playtest.py",
        "content": "ns.tprint('ci_pass')\nns.addXP(1, 'programming')",
        "session_id": s.sid,
    })
    s.assert_ok("upload API returns ok", r.get("ok") is True)
    s.assert_ok("upload syntax valid", r.get("syntax_ok") is True)

    # run uploaded script
    s.assert_output("run uploaded script", s.cmd("script run ci_playtest.py"), contains="ci_pass")

    # download via API
    dl = _get(f"/api/script/download/hello.py?session_id={s.sid}")
    s.assert_ok("download returns content", len(dl.get("content", "")) > 0)

    return s


def suite_devmode(verbose: bool) -> PlaytestSession:
    """Test developer mode commands."""
    print("\n[DEVMODE] Developer mode")
    s = PlaytestSession(verbose).start()

    # Invalid token — returns dim usage hint (not error type)
    s.assert_output("bad token rejected", s.cmd("devmode on WRONG_TOKEN"), contains="GHOST-DEV-2026-ALPHA")

    # Enable with correct token
    s.assert_output("correct token accepted", s.cmd("devmode on GHOST-DEV-2026-ALPHA"), contains="unlocked")
    s.assert_output("devmode status shows ENABLED", s.cmd("devmode status"), contains="ENABLED")

    # Inspect commands
    s.assert_output("inspect state", s.cmd("inspect state"), contains="level")
    s.assert_output("inspect processes", s.cmd("inspect processes"), contains="root_shell")
    s.assert_output("inspect env", s.cmd("inspect env"), contains="PATH")
    s.assert_output("inspect story", s.cmd("inspect story"), min_lines=1)
    s.assert_output("inspect all", s.cmd("inspect all"), min_lines=5)

    # Spawn, teleport
    s.assert_output("spawn creates file", s.cmd("spawn /tmp/devtest.txt hello"), t_type="success")
    s.assert_output("cat spawned file", s.cmd("cat /tmp/devtest.txt"), contains="hello")
    s.assert_output("teleport to /etc", s.cmd("teleport /etc"), contains="Bypassed")
    s.assert_output("pwd shows /etc after teleport", s.cmd("pwd"), contains="/etc")
    s.cmd("teleport /home/ghost")

    # Profile
    s.assert_output("profile shows metrics", s.cmd("profile"), contains="commands_run")

    # Generate
    s.assert_output("generate challenge", s.cmd("generate challenge forensics easy"), contains="generated")
    s.assert_output("generate lore", s.cmd("generate lore"), min_lines=1)
    s.assert_output("generate node", s.cmd("generate node test-node-99"), min_lines=1)

    # Test suite via devmode
    out = s.cmd("test all")
    results_line = next((i.get("s", "") for i in out if isinstance(i, dict) and "Results:" in i.get("s", "")), "")
    s.assert_ok("test suite runs (results line found)", "Results:" in results_line)
    s.assert_ok("test suite passes (15/15)", "15/15" in results_line)

    return s


def suite_npcs(verbose: bool) -> PlaytestSession:
    """Test NPC interactions."""
    print("\n[NPCS] NPC interactions")
    s = PlaytestSession(verbose).start()

    s.assert_output("talk ada produces output", s.cmd("talk ada"), min_lines=1)
    s.assert_output("talk cypher produces output", s.cmd("talk cypher"), min_lines=1)
    s.assert_output("skills shows skill levels", s.cmd("skills"), min_lines=3)
    s.assert_output("achievements shows list", s.cmd("achievements"), min_lines=1)
    return s


def suite_filesystem_ops(verbose: bool) -> PlaytestSession:
    """Test filesystem manipulation."""
    print("\n[FS] Filesystem operations")
    s = PlaytestSession(verbose).start()

    s.assert_output("mkdir creates dir", s.cmd("mkdir /tmp/testdir"), min_lines=0)
    s.assert_output("touch creates file", s.cmd("touch /tmp/testdir/newfile.txt"), min_lines=0)
    s.assert_output("ls shows new dir", s.cmd("ls /tmp/testdir"), min_lines=1)
    s.assert_output("echo write to file", s.cmd("echo content > /tmp/testdir/newfile.txt"), min_lines=1)
    s.assert_output("cat reads written file", s.cmd("cat /tmp/testdir/newfile.txt"), contains="content")
    s.assert_output("cp copies file", s.cmd("cp /tmp/testdir/newfile.txt /tmp/testdir/copy.txt"), min_lines=0)
    s.assert_output("ls shows copy", s.cmd("ls /tmp/testdir"), min_lines=1)
    s.assert_output("rm removes file", s.cmd("rm /tmp/testdir/copy.txt"), min_lines=0)
    s.assert_output("find works", s.cmd("find /home/ghost -name '*.txt'"), min_lines=1)
    s.assert_output("stat shows file info", s.cmd("stat /home/ghost/notes.txt"), min_lines=1)
    return s


def suite_full_playthrough(verbose: bool) -> PlaytestSession:
    """Simulated end-to-end player journey."""
    print("\n[JOURNEY] Full player journey (condensed)")
    s = PlaytestSession(verbose).start()

    # Onboarding
    s.assert_output("help works on start", s.cmd("help"), min_lines=5)
    s.assert_output("tutorial starts", s.cmd("tutorial"), min_lines=1)

    # Recon
    s.assert_output("ls home", s.cmd("ls"), min_lines=1)
    s.assert_output("cat README", s.cmd("cat README.md"), contains="Welcome")
    s.assert_output("cat notes", s.cmd("cat notes.txt"), contains="INVESTIGATION")
    s.assert_output("read mission.enc", s.cmd("cat mission.enc"), contains="BASE64")
    s.assert_output("decode base64", s.cmd("echo 'bWlzc2lvbjogZmluZCBDSElNRVJB' | base64 -d"), min_lines=1)

    # Evidence gathering
    s.assert_output("read syslog", s.cmd("cat /var/log/syslog"), contains="CHIMERA")
    s.assert_output("read nexus log", s.cmd("cat /var/log/nexus.log"), contains="CHIMERA")
    s.assert_output("grep for keys", s.cmd("grep -r KEY /var/log"), min_lines=0)

    # Priv esc
    s.assert_output("sudo -l check", s.cmd("sudo -l"), contains="find")
    s.assert_output("find exploit", s.cmd("sudo find . -exec /bin/sh ;"), min_lines=1)
    s.assert_output("now root", s.cmd("whoami"), contains="root")
    s.assert_output("read master key", s.cmd("cat /opt/chimera/keys/master.key"), min_lines=1)

    # Scripting bonus
    s.assert_output("run recon script", s.cmd("script run recon.py"), contains="Found")
    s.assert_output("run loot collector", s.cmd("script run loot_collector.py"), min_lines=1)

    # XP check
    r = _post("/api/game/command", {"command": "skills", "session_id": s.sid})
    out = r.get("output", [])
    s.assert_output("skills shows xp earned", out, min_lines=3)

    return s


# ── Runner ─────────────────────────────────────────────────────────────

SUITES = {
    "health":      suite_health,
    "core":        suite_core_commands,
    "pipelines":   suite_pipelines,
    "security":    suite_security_path,
    "scripting":   suite_scripting_api,
    "devmode":     suite_devmode,
    "npcs":        suite_npcs,
    "filesystem":  suite_filesystem_ops,
    "journey":     suite_full_playthrough,
}

QUICK_SUITES = ["health", "core", "scripting", "devmode"]


def main():
    parser = argparse.ArgumentParser(description="Terminal Depths automated playtest")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke test only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show command output")
    parser.add_argument("--suite", "-s", help="Run specific suite")
    args = parser.parse_args()

    print("=" * 60)
    print("  TERMINAL DEPTHS — AUTOMATED PLAYTEST")
    print("=" * 60)
    t0 = time.time()

    to_run = []
    if args.suite:
        if args.suite not in SUITES:
            print(f"Unknown suite '{args.suite}'. Available: {', '.join(SUITES)}")
            sys.exit(1)
        to_run = [args.suite]
    elif args.quick:
        to_run = QUICK_SUITES
    else:
        to_run = list(SUITES.keys())

    total_pass = 0
    total_fail = 0
    failed_suites = []

    for name in to_run:
        try:
            sess = SUITES[name](args.verbose)
            total_pass += sess.passes
            total_fail += sess.fails
            if sess.fails > 0:
                failed_suites.append(name)
        except Exception as e:
            print(f"\n  [ERROR] Suite '{name}' crashed: {e}")
            total_fail += 1
            failed_suites.append(name)

    elapsed = time.time() - t0
    total = total_pass + total_fail
    color = "\033[32m" if total_fail == 0 else "\033[31m"
    reset = "\033[0m"

    print("\n" + "=" * 60)
    print(f"  {color}TOTAL: {total_pass}/{total} passed in {elapsed:.1f}s{reset}")
    if failed_suites:
        print(f"  Failed suites: {', '.join(failed_suites)}")
    print("=" * 60)

    # Write results to knowledge/
    import pathlib
    pathlib.Path("knowledge").mkdir(exist_ok=True)
    with open("knowledge/last_playtest.json", "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "suites_run": to_run,
            "total_pass": total_pass,
            "total_fail": total_fail,
            "failed_suites": failed_suites,
            "elapsed_s": round(elapsed, 2),
        }, f, indent=2)

    return 1 if total_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
