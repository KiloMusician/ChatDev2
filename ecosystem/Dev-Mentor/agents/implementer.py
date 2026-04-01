#!/usr/bin/env python3
"""
agents/implementer.py — Code Implementation Agent

Analyzes the game engine for gaps, generates stub implementations,
validates existing commands, and reports on coverage.

Usage:
    python3 agents/implementer.py                  # analyze + report
    python3 agents/implementer.py --audit          # audit all commands
    python3 agents/implementer.py --gaps           # show missing features
    python3 agents/implementer.py --coverage       # show coverage estimate
    python3 agents/implementer.py --task <id>      # run orchestrator task
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Set, Tuple

BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
KNOWLEDGE_DIR.mkdir(exist_ok=True)
COMMANDS_FILE = BASE_DIR / "app/game_engine/commands.py"
SCRIPTING_FILE = BASE_DIR / "app/game_engine/scripting.py"


def _get(path: str) -> dict:
    with urllib.request.urlopen("http://localhost:7337" + path, timeout=8) as r:
        return json.loads(r.read())


def get_all_commands() -> List[str]:
    """Get commands from the API."""
    try:
        r = _get("/api/game/commands")
        return r.get("commands", [])
    except Exception:
        return []


def analyze_command_handlers() -> Dict[str, dict]:
    """Analyze commands.py to find all handlers and their complexity."""
    if not COMMANDS_FILE.exists():
        return {}

    source = COMMANDS_FILE.read_text()
    handlers = {}

    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("_cmd_"):
                cmd_name = node.name[5:].replace("_", "-")
                lines = node.end_lineno - node.lineno if hasattr(node, "end_lineno") else 0
                # Count returns (complexity proxy)
                returns = sum(1 for n in ast.walk(node) if isinstance(n, ast.Return))
                # Check for stub indicators
                body_src = ast.unparse(node) if hasattr(ast, "unparse") else ""
                is_stub = lines < 5 or "simulated" in body_src.lower() or "not implemented" in body_src.lower()
                handlers[cmd_name] = {
                    "lines": lines,
                    "returns": returns,
                    "is_stub": is_stub,
                    "lineno": node.lineno,
                }
    except SyntaxError as e:
        print(f"  [WARN] Syntax error parsing commands.py: {e}")

    return handlers


def analyze_ns_api() -> List[str]:
    """Get all ns API methods from scripting.py."""
    if not SCRIPTING_FILE.exists():
        return []

    source = SCRIPTING_FILE.read_text()
    methods = []
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "NS":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                        methods.append(item.name)
    except SyntaxError:
        pass
    return methods


def audit_commands(verbose: bool = False) -> dict:
    """Audit all commands for quality."""
    handlers = analyze_command_handlers()
    api_commands = get_all_commands()

    stubs = [c for c, h in handlers.items() if h.get("is_stub")]
    rich = [c for c, h in handlers.items() if not h.get("is_stub")]
    short = [c for c, h in handlers.items() if h.get("lines", 0) < 3]

    if verbose:
        print("\n  Stub/minimal commands:")
        for cmd in sorted(stubs)[:20]:
            h = handlers[cmd]
            print(f"    {cmd:<25} ({h['lines']} lines)")

    return {
        "total_handlers": len(handlers),
        "total_api": len(api_commands),
        "stub_count": len(stubs),
        "rich_count": len(rich),
        "stub_commands": sorted(stubs)[:20],
        "short_commands": sorted(short)[:10],
    }


def find_gaps() -> dict:
    """Find missing or incomplete features."""
    gaps = []

    # Check for common Unix commands that should exist
    EXPECTED_COMMANDS = [
        "ls", "cat", "grep", "find", "ps", "sudo", "ssh", "nc",
        "nmap", "curl", "wget", "python3", "pip", "git", "vim",
        "nano", "awk", "sed", "cut", "sort", "uniq", "wc", "head",
        "tail", "chmod", "chown", "tar", "zip", "unzip", "diff",
        "ping", "ifconfig", "ip", "ss", "netstat", "traceroute",
        "dig", "nslookup", "whois", "tcpdump", "strace", "ltrace",
        "gdb", "objdump", "strings", "hexdump", "xxd", "base64",
        "openssl", "gpg", "ssh-keygen", "htpasswd",
        # Game-specific
        "devmode", "inspect", "spawn", "teleport", "generate",
        "script", "tutorial", "skills", "achievements", "talk",
        "hack", "exploit", "exfil", "ascend",
    ]

    api_commands = set(get_all_commands())
    missing = [c for c in EXPECTED_COMMANDS if c not in api_commands]

    # Check ns API methods
    ns_methods = analyze_ns_api()
    EXPECTED_NS = [
        "tprint", "ls", "read", "write", "exec", "run", "hack", "scan",
        "getPlayer", "getServer", "getHostname", "addXP", "sleep",
        "fileExists", "spawn", "completeChallenge",
    ]
    missing_ns = [m for m in EXPECTED_NS if m not in ns_methods]

    return {
        "missing_commands": missing,
        "missing_ns_methods": missing_ns,
        "total_expected": len(EXPECTED_COMMANDS),
        "total_found": len(api_commands & set(EXPECTED_COMMANDS)),
        "coverage_pct": round(len(api_commands & set(EXPECTED_COMMANDS)) / len(EXPECTED_COMMANDS) * 100, 1),
    }


def generate_stub(cmd_name: str) -> str:
    """Generate a stub implementation for a missing command."""
    safe_name = cmd_name.replace("-", "_")
    return (
        f"    def _cmd_{safe_name}(self, args: List[str]) -> List[dict]:\n"
        f'        """{cmd_name} — TODO: implement"""\n'
        f"        if \"--help\" in args or \"-h\" in args:\n"
        f"            return [_line(\"{cmd_name}: no help available yet\", \"dim\")]\n"
        f"        return [_line(\"{cmd_name}: (simulated)\", \"dim\")]\n"
    )


def coverage_report() -> dict:
    """Generate a comprehensive coverage report."""
    handlers = analyze_command_handlers()
    api_cmds = get_all_commands()
    ns_methods = analyze_ns_api()
    gaps = find_gaps()

    # File sizes as proxy for completeness
    engine_files = {
        "commands.py": COMMANDS_FILE,
        "scripting.py": SCRIPTING_FILE,
        "filesystem.py": BASE_DIR / "app/game_engine/filesystem.py",
        "gamestate.py": BASE_DIR / "app/game_engine/gamestate.py",
        "session.py": BASE_DIR / "app/game_engine/session.py",
        "story.py": BASE_DIR / "app/game_engine/story.py",
        "npcs.py": BASE_DIR / "app/game_engine/npcs.py",
        "tutorial.py": BASE_DIR / "app/game_engine/tutorial.py",
    }

    file_stats = {}
    for name, path in engine_files.items():
        if path.exists():
            stat = path.stat()
            lines = len(path.read_text().splitlines())
            file_stats[name] = {"bytes": stat.st_size, "lines": lines}

    total_lines = sum(s["lines"] for s in file_stats.values())

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commands": {
            "total": len(handlers),
            "via_api": len(api_cmds),
            "stubs": len([h for h in handlers.values() if h.get("is_stub")]),
        },
        "ns_api": {
            "total_methods": len(ns_methods),
            "methods": ns_methods,
        },
        "gaps": gaps,
        "files": file_stats,
        "total_lines": total_lines,
    }


def main():
    parser = argparse.ArgumentParser(description="Terminal Depths Implementation Agent")
    parser.add_argument("--audit", action="store_true", help="Audit all command handlers")
    parser.add_argument("--gaps", action="store_true", help="Find missing features")
    parser.add_argument("--coverage", action="store_true", help="Coverage report")
    parser.add_argument("--stub", help="Generate stub for a command name")
    parser.add_argument("--task", help="Task ID from orchestrator")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print("=" * 55)
    print("  TERMINAL DEPTHS — IMPLEMENTATION AGENT")
    print("=" * 55)

    if args.stub:
        print(f"\nStub for '{args.stub}':")
        print(generate_stub(args.stub))
        return 0

    if args.audit:
        print("\n[AUDIT] Command handlers")
        result = audit_commands(verbose=args.verbose)
        print(f"  Total handlers:  {result['total_handlers']}")
        print(f"  Via API:         {result['total_api']}")
        print(f"  Stub/minimal:    {result['stub_count']}")
        print(f"  Rich (10+ lines): {result['rich_count']}")
        if result["stub_commands"] and args.verbose:
            print(f"  Top stubs: {result['stub_commands'][:10]}")

    if args.gaps:
        print("\n[GAPS] Missing features")
        gaps = find_gaps()
        print(f"  Expected commands: {gaps['total_expected']}")
        print(f"  Found:            {gaps['total_found']}")
        print(f"  Coverage:         {gaps['coverage_pct']}%")
        if gaps["missing_commands"]:
            print(f"  Missing: {gaps['missing_commands'][:15]}")
        if gaps["missing_ns_methods"]:
            print(f"  Missing ns methods: {gaps['missing_ns_methods']}")

    if args.coverage or (not args.audit and not args.gaps and not args.stub):
        print("\n[COVERAGE] Engine coverage report")
        report = coverage_report()

        print(f"  Commands:       {report['commands']['total']} handlers, {report['commands']['stubs']} stubs")
        print(f"  ns API:         {report['ns_api']['total_methods']} methods")
        print(f"  Coverage:       {report['gaps']['coverage_pct']}%")
        print(f"\n  Engine files:")
        for name, stats in report["files"].items():
            print(f"    {name:<25} {stats['lines']:>5} lines  {stats['bytes']:>8} bytes")
        print(f"\n  Total:  {report['total_lines']} lines of engine code")

        # Save report
        path = KNOWLEDGE_DIR / "coverage_report.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n  Report saved: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
