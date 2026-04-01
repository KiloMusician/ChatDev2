#!/usr/bin/env python3
"""Smoke test for the ChatGPT bridge and mailbox.

This script POSTs a simple terminal event to the bridge and writes a mailbox
command, then checks that the corresponding log files were updated.

Use while the bridge is running locally on 127.0.0.1:8765.
"""

from __future__ import annotations

import time
from pathlib import Path

import requests

BRIDGE = "http://127.0.0.1:8765"
LOG_ROOT = Path("logs") / "terminals"


def post_terminal():
    payload = {"channel": "Main", "level": "info", "message": "smoke-test", "meta": {"smoke": True}}
    r = requests.post(f"{BRIDGE}/api/terminals/send", json=payload, timeout=5)
    print("terminals/send ->", r.status_code, r.text)
    return r.ok


def post_mailbox():
    cmd = {"id": "smoke-1", "command": "echo", "args": {"msg": "hello"}}
    r = requests.post(f"{BRIDGE}/api/mailbox/send", json=cmd, timeout=5)
    print("mailbox/send ->", r.status_code, r.text)
    return r.ok


def post_execute():
    payload = {"command": "start_nusyq", "args": {"action": "help", "timeout_seconds": 20}}
    r = requests.post(f"{BRIDGE}/api/execute", json=payload, timeout=30)
    print("execute ->", r.status_code, r.text[:300])
    return r.ok


def check_logs():
    # check Main log
    main_log = LOG_ROOT / "main.log"
    if not main_log.exists():
        print("Main log not found:", main_log)
        return False
    lines = [line for line in main_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    found = any("smoke-test" in line for line in lines[-20:])
    print("Found smoke-test in main.log:", found)
    return found


def main():
    ok1 = post_terminal()
    ok2 = post_mailbox()
    ok3 = post_execute()
    # wait briefly for bridge to flush
    time.sleep(1.0)
    ok4 = check_logs()
    if ok1 and ok2 and ok3 and ok4:
        print("Smoke test succeeded")
        return 0
    print("Smoke test failed")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
