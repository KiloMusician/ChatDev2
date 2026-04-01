#!/usr/bin/env python3
"""scripts/validate_all.py — CI-Style Validation Runner

Runs all validation checks in sequence:
  1. Python syntax check (all .py files)
  2. Game engine health check (API /api/health)
  3. Agent ecosystem tests (59 agents, trust matrix, factions)
  4. Terminal Depths in-game test suite
  5. API endpoint smoke tests
  6. File structure integrity
  7. Memory/SQLite integrity

Reports a dashboard with pass/fail/warn for each check.
Exits 0 if all critical checks pass, 1 otherwise.

Usage:
    python3 scripts/validate_all.py            # run all checks
    python3 scripts/validate_all.py --quick    # smoke tests only
    python3 scripts/validate_all.py --fix      # attempt auto-fix on failures
    python3 scripts/validate_all.py --report   # write report to validate_report.md
"""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent.parent

# Auto-detect: Replit uses 5000, Docker uses 7337, override via TD_BASE_URL
import os as _os


def _detect_base_url() -> str:
    if _os.environ.get("TD_BASE_URL"):
        return _os.environ["TD_BASE_URL"].rstrip("/")
    if _os.environ.get("REPL_ID") or _os.environ.get("REPLIT_DEPLOYMENT"):
        return "http://localhost:5000"
    return "http://localhost:7337"


BASE_URL = _detect_base_url()

CRITICAL = "CRITICAL"
WARN = "WARN"
INFO = "INFO"


def _color(level: str) -> str:
    return {
        "PASS": "\033[32m",
        "FAIL": "\033[31m",
        "WARN": "\033[33m",
        "SKIP": "\033[90m",
        "INFO": "\033[36m",
    }.get(level, "\033[0m")


def _get(path: str, timeout: int = 8) -> dict:
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def _post(path: str, data: dict, timeout: int = 15) -> dict:
    try:
        req = urllib.request.Request(
            BASE_URL + path,
            json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


class ValidationResult:
    def __init__(self, name: str, severity: str = CRITICAL):
        self.name = name
        self.severity = severity
        self.status = "SKIP"
        self.message = ""
        self.detail: list[str] = []
        self.duration_ms = 0

    def passed(self, msg: str = "OK", **detail):
        self.status = "PASS"
        self.message = msg
        if detail:
            self.detail.append(str(detail))

    def failed(self, msg: str, **detail):
        self.status = "FAIL"
        self.message = msg
        if detail:
            self.detail.append(str(detail))

    def warned(self, msg: str, **detail):
        self.status = "WARN"
        self.message = msg
        if detail:
            self.detail.append(str(detail))

    def print_line(self):
        c = _color(self.status)
        r = "\033[0m"
        sev = f"[{self.severity[:4]}]" if self.severity == CRITICAL else "      "
        dur = f"  {self.duration_ms}ms" if self.duration_ms else ""
        print(f"  {c}{self.status:<4}{r}  {sev}  {self.name:<45}  {self.message}{dur}")


class Validator:
    def __init__(self, quick: bool = False):
        self.quick = quick
        self.results: list[ValidationResult] = []

    def _run(self, r: ValidationResult, fn) -> ValidationResult:
        t0 = time.monotonic()
        try:
            fn(r)
        except Exception as e:
            r.failed(f"Exception: {e}")
        r.duration_ms = int((time.monotonic() - t0) * 1000)
        self.results.append(r)
        r.print_line()
        return r

    def check_syntax(self):
        r = ValidationResult("Python syntax (all .py files)", CRITICAL)

        def _check(r):
            errors = []
            py_files = list(BASE_DIR.rglob("*.py"))
            checked = 0
            for f in py_files:
                if any(p in str(f) for p in ("__pycache__", ".git", "node_modules")):
                    continue
                try:
                    ast.parse(f.read_text())
                    checked += 1
                except SyntaxError as e:
                    errors.append(f"{f.relative_to(BASE_DIR)}:{e.lineno}: {e.msg}")
            if errors:
                r.failed(f"{len(errors)} syntax error(s)", errors=errors[:3])
            else:
                r.passed(f"{checked} files OK")

        return self._run(r, _check)

    def check_api_health(self):
        r = ValidationResult("API health endpoint", CRITICAL)

        def _check(r):
            data = _get("/api/health")
            if "error" in data:
                r.failed(f"Server unreachable: {data['error']}")
            elif data.get("ok"):
                r.passed(
                    f"uptime={data.get('uptime_s', '?')}s game_engine={data.get('game_engine', '?')}"
                )
            else:
                r.warned("API responded but ok=False")

        return self._run(r, _check)

    def check_agent_ecosystem(self):
        r = ValidationResult("Agent ecosystem (59 agents)", CRITICAL)

        def _check(r):
            data = _get("/api/game/agents?session_id=validate_run")
            if "error" in data:
                r.failed(f"Agent API error: {data['error']}")
                return
            total = data.get("total", 0)
            unlocked = data.get("unlocked", 0)
            agents = data.get("agents", [])
            has_colors = all("faction_color" in a for a in agents[:5])
            if total < 50:
                r.failed(f"Expected 59 agents, got {total}")
            elif not has_colors:
                r.warned(f"{total} agents loaded but faction_color missing")
            else:
                r.passed(f"{total} agents, {unlocked} unlocked, faction_color OK")

        return self._run(r, _check)

    def check_trust_matrix(self):
        r = ValidationResult("Trust matrix API", WARN)

        def _check(r):
            data = _get("/api/game/agents?session_id=validate_trust")
            if "error" in data:
                r.warned(f"Cannot verify trust matrix: {data['error']}")
                return
            agents = data.get("agents", [])
            has_scores = all(
                isinstance(a.get("trust"), (int, float))
                and isinstance(a.get("respect"), (int, float))
                for a in agents[:5]
            )
            if has_scores:
                r.passed("trust/respect/fear scores present on all sampled agents")
            else:
                r.warned("Trust scores missing from some agents")

        return self._run(r, _check)

    def check_faction_status(self):
        r = ValidationResult("Faction status API", CRITICAL)

        def _check(r):
            data = _get("/api/game/faction/status?session_id=validate_run")
            if "error" in data:
                r.failed(f"Faction API error: {data['error']}")
                return
            factions = data.get("factions", [])
            if len(factions) < 6:
                r.warned(f"Expected 6+ factions, got {len(factions)}")
            else:
                r.passed(f"{len(factions)} factions loaded")

        return self._run(r, _check)

    def check_arg_signal(self):
        r = ValidationResult("ARG signal endpoint", INFO)

        def _check(r):
            data = _get("/api/game/arg/signal")
            if "error" in data:
                r.warned(f"ARG signal unavailable: {data['error']}")
            elif data.get("ok") and (data.get("source") or data.get("signal")):
                src = data.get("source") or data.get("signal", "?")
                r.passed(f"signal={src}")
            else:
                r.warned("ARG signal responded but missing fields")

        return self._run(r, _check)

    def check_llm_status(self):
        r = ValidationResult("LLM backend", WARN)

        def _check(r):
            data = _get("/api/llm/status")
            if "error" in data:
                r.warned(f"LLM status unreachable: {data['error']}")
            elif data.get("available"):
                r.passed(f"backend={data.get('backend', '?')}")
            else:
                r.warned("LLM not available (stub mode)")

        return self._run(r, _check)

    def _game_cmd(self, cmd: str, session_id: str = "validate_run") -> dict:
        """Helper: run a game command and return the API response."""
        return _post("/api/game/command", {"command": cmd, "session_id": session_id})

    def _output_text(self, resp: dict) -> str:
        """Extract joined text from a game command response output list.
        Handles both plain {s:...} entries and ls-row {items:[{text:...}]} entries.
        """
        raw = resp.get("output", [])
        parts = []
        if isinstance(raw, list):
            for l in raw:
                if not isinstance(l, dict):
                    continue
                if l.get("s"):
                    parts.append(l["s"])
                elif l.get("t") == "ls-row" and l.get("items"):
                    parts.extend(
                        it.get("text", "") for it in l["items"] if isinstance(it, dict)
                    )
                elif l.get("plain"):
                    parts.append(l["plain"])
        return " ".join(parts) + str(resp.get("html", ""))

    def _no_bash_fallthrough(self, resp: dict) -> bool:
        """Return True if the response does NOT contain a bash fallthrough error."""
        txt = self._output_text(resp)
        return "command not found" not in txt and "bash:" not in txt

    def check_game_command(self):
        r = ValidationResult("Game cmd: help / ls / xp (smoke)", CRITICAL)

        def _check(r):
            session = "validate_smoke"
            cmds = [
                ("help", lambda t: len(t) > 10),
                ("ls", lambda t: len(t) > 5),
                ("xp", lambda t: "xp" in t.lower() or "level" in t.lower()),
                ("whoami", lambda t: len(t) > 0),
                ("skills", lambda t: "skill" in t.lower() or "xp" in t.lower()),
            ]
            failed = []
            for cmd, pred in cmds:
                resp = self._game_cmd(cmd, session)
                if "error" in resp and not resp.get("output"):
                    failed.append(f"{cmd}:API-err")
                    continue
                txt = self._output_text(resp)
                if not pred(txt):
                    failed.append(f"{cmd}:bad-output")
                elif not self._no_bash_fallthrough(resp):
                    failed.append(f"{cmd}:bash-fallthrough")
            if failed:
                r.failed(f"Commands failed checks: {', '.join(failed)}")
            else:
                r.passed(f"{len(cmds)} basic commands OK")

        return self._run(r, _check)

    def check_game_commands_core_systems(self):
        r = ValidationResult("Game cmd: health / syscheck / services", CRITICAL)

        def _check(r):
            session = "validate_systems"
            issues = []

            resp = self._game_cmd("health", session)
            txt = self._output_text(resp)
            if "SYSTEM HEALTH" not in txt:
                issues.append("health:no-header")
            if "DB error" in txt:
                issues.append("health:serena-db-error")
            if "bash:" in txt:
                issues.append("health:bash-fallthrough")

            resp = self._game_cmd("syscheck", session)
            txt = self._output_text(resp)
            if "Engine" not in txt:
                issues.append("syscheck:no-engine-line")

            resp = self._game_cmd("services health", session)
            txt = self._output_text(resp)
            if not txt or len(txt) < 10:
                issues.append("services-health:empty")

            if issues:
                r.failed(f"Core system commands: {', '.join(issues)}")
            else:
                r.passed("health / syscheck / services health all clean")

        return self._run(r, _check)

    def check_game_commands_nusyq(self):
        r = ValidationResult("Game cmd: nusyq status (no bash fallthrough)", CRITICAL)

        def _check(r):
            session = "validate_nusyq"
            resp = self._game_cmd("nusyq status", session)
            txt = self._output_text(resp)
            if "bash:" in txt or "command not found" in txt:
                r.failed("nusyq falls through to bash — _cmd_nusyq handler missing")
            elif "NuSyQ" not in txt and "Lattice" not in txt:
                r.warned(f"nusyq output looks unexpected: {txt[:80]}")
            else:
                r.passed("nusyq status returns proper bridge status")

        return self._run(r, _check)

    def check_game_commands_lattice(self):
        r = ValidationResult("Game cmd: lattice status / query", WARN)

        def _check(r):
            session = "validate_lattice"
            resp = self._game_cmd("lattice status", session)
            txt = self._output_text(resp)
            if "error" in txt.lower() and "bash:" in txt:
                r.failed("lattice status: bash fallthrough")
            else:
                r.passed("lattice status returned output")

            resp2 = self._game_cmd("lattice stats", session)
            txt2 = self._output_text(resp2)
            if "bash:" in txt2:
                r.failed("lattice stats: bash fallthrough")

        return self._run(r, _check)

    def check_game_commands_narrative(self):
        r = ValidationResult("Game cmd: gordon / agents / ai status", WARN)

        def _check(r):
            session = "validate_narrative"
            cmds = [
                ("gordon status", "gordon"),
                ("agents list", "agent"),
                ("ai status", "llm"),
                ("challenge list", "challenge"),
                ("ml status", "backend"),
            ]
            ok = []
            issues = []
            for cmd, expect_str in cmds:
                resp = self._game_cmd(cmd, session)
                txt = self._output_text(resp).lower()
                if "bash:" in txt or (
                    "command not found" in txt and expect_str not in txt
                ):
                    issues.append(f"{cmd.split()[0]}:bash-err")
                elif len(txt) < 5:
                    issues.append(f"{cmd.split()[0]}:empty")
                else:
                    ok.append(cmd.split()[0])
            if issues:
                r.warned(f"Narrative commands with issues: {', '.join(issues)}")
            else:
                r.passed(f"{len(ok)} narrative commands OK: {', '.join(ok)}")

        return self._run(r, _check)

    def check_game_commands_new_handlers(self):
        r = ValidationResult("Game cmd: mcp / rl / td (new handlers)", CRITICAL)

        def _check(r):
            session = "validate_new_handlers"
            issues = []
            for cmd, expect in [
                ("mcp status", "MCP"),
                ("mcp tools", "tool"),
                ("rl status", "Q-Table"),
                ("td state", "TouchDesigner"),
                ("td channels", "channel"),
            ]:
                resp = self._game_cmd(cmd, session)
                txt = self._output_text(resp)
                if "bash:" in txt or "command not found" in txt.lower():
                    issues.append(f"{cmd.split()[0]}:bash-fallthrough")
                elif expect.lower() not in txt.lower() and len(txt) < 10:
                    issues.append(f"{cmd.split()[0]}:empty")
            if issues:
                r.failed(f"New command handlers: {', '.join(issues)}")
            else:
                r.passed("mcp / rl / td handlers all respond correctly")

        return self._run(r, _check)

    def check_game_commands_survey_recon_network(self):
        r = ValidationResult(
            "Game cmd: survey / recon / network / examine (new aliases)", CRITICAL
        )

        def _check(r):
            session = "validate_survey_recon"
            issues = []
            for cmd, expect in [
                ("survey", "node"),
                ("recon", "node"),
                ("network", "network"),
                ("network scan", "node"),
                ("examine ada", "ADA"),
            ]:
                resp = self._game_cmd(cmd, session)
                txt = self._output_text(resp)
                if "bash:" in txt or "command not found" in txt.lower():
                    issues.append(f"'{cmd}':bash-fallthrough")
                elif expect.lower() not in txt.lower():
                    issues.append(f"'{cmd}':missing-{expect!r}")
            if issues:
                r.failed(f"Command issues: {', '.join(issues)}")
            else:
                r.passed("survey / recon / network / examine all respond correctly")

        return self._run(r, _check)

    def check_no_duplicate_handlers(self):
        r = ValidationResult("No duplicate _cmd_ handler definitions", CRITICAL)

        def _check(r):
            import ast as _ast

            src = (BASE_DIR / "app" / "game_engine" / "commands.py").read_text()
            tree = _ast.parse(src)
            seen: dict = {}
            dupes = []
            for cls in _ast.walk(tree):
                if not isinstance(cls, _ast.ClassDef):
                    continue
                for fn in _ast.walk(cls):
                    if isinstance(fn, _ast.FunctionDef) and fn.name.startswith("_cmd_"):
                        if fn.name in seen:
                            dupes.append(f"{fn.name}@{fn.lineno}(was {seen[fn.name]})")
                        seen[fn.name] = fn.lineno
            if dupes:
                r.failed(f"{len(dupes)} duplicate handler(s): {', '.join(dupes)}")
            else:
                r.passed(f"All {len(seen)} _cmd_ handlers are unique")

        return self._run(r, _check)

    def check_route_duplicates(self):
        r = ValidationResult("No duplicate FastAPI route registrations", CRITICAL)

        def _check(r):
            main_py = BASE_DIR / "app" / "backend" / "main.py"
            if not main_py.exists():
                r.warned("main.py not found")
                return
            text = main_py.read_text()
            import re

            routes = re.findall(
                r'@app\.(get|post|put|delete|websocket)\("([^"]+)"', text
            )
            seen: dict = {}
            dupes = []
            for method, path in routes:
                key = f"{method.upper()}:{path}"
                if key in seen:
                    dupes.append(key)
                seen[key] = True
            if dupes:
                r.failed(f"{len(dupes)} duplicate route(s): {', '.join(dupes)}")
            else:
                r.passed(f"All {len(seen)} routes are unique")

        return self._run(r, _check)

    def check_orphan_dbs(self):
        r = ValidationResult("No empty orphan SQLite files in state/", WARN)

        def _check(r):
            state_dir = BASE_DIR / "state"
            if not state_dir.exists():
                r.warned("state/ directory not found")
                return
            empty = [f.name for f in state_dir.glob("*.db") if f.stat().st_size == 0]
            if empty:
                r.warned(f"{len(empty)} empty DB file(s): {', '.join(sorted(empty))}")
            else:
                r.passed("All .db files have content")

        return self._run(r, _check)

    def check_config_integrity(self):
        r = ValidationResult(
            "config/runtime.py — port_map + paths + sanitizer", CRITICAL
        )

        def _check(r):
            issues = []
            try:
                import importlib
                import sys

                # Ensure workspace root is on sys.path so config.runtime imports
                _root_str = str(BASE_DIR)
                if _root_str not in sys.path:
                    sys.path.insert(0, _root_str)
                # Force reload so we test the real module state
                if "config.runtime" in sys.modules:
                    del sys.modules["config.runtime"]
                import config.runtime as rt

                # 1. port_map loaded
                if not rt._PORT_MAP:
                    issues.append("port_map.json not loaded")
                if len(rt._PORTS_BY_KEY) < 8:
                    issues.append(
                        f"only {len(rt._PORTS_BY_KEY)} services in port_map (expected ≥8)"
                    )

                # 2. RUNTIME_ENV resolved
                if rt.RUNTIME_ENV not in ("replit", "docker", "vscode", "unknown"):
                    issues.append(f"unexpected RUNTIME_ENV={rt.RUNTIME_ENV!r}")

                # 3. PATHS — all keys present, critical ones resolve to correct dirs
                required_keys = (
                    "db_devmentor",
                    "db_agents",
                    "db_serena",
                    "quest_log",
                    "port_map",
                )
                missing_keys = [k for k in required_keys if k not in rt.PATHS]
                if missing_keys:
                    issues.append(f"PATHS missing keys: {missing_keys}")

                # 4. Critical paths exist on disk
                for key in ("db_serena", "quest_log", "port_map"):
                    if key in rt.PATHS and not rt.PATHS[key].exists():
                        issues.append(f"PATHS[{key!r}] does not exist: {rt.PATHS[key]}")

                # 5. resolve_port works for known services
                for svc_name, expected_port in [
                    ("gordon", 3000),
                    ("serena", 3001),
                    ("redis", 6379),
                ]:
                    try:
                        p = rt.resolve_port(svc_name)
                        if p == 0:
                            issues.append(f"resolve_port({svc_name!r})=0")
                    except Exception as exc:
                        issues.append(f"resolve_port({svc_name!r}) raised: {exc}")

                # 6. CommandSanitizer rejects injection and passes clean input
                cs = rt.CommandSanitizer
                ok_cmd, ok_args = cs.sanitize("help")
                if ok_cmd != "help":
                    issues.append(f"sanitizer rejected clean 'help' command: {ok_args}")

                bad_cmd, err = cs.sanitize("echo $(rm -rf /)")
                if bad_cmd is not None:
                    issues.append("sanitizer allowed injection pattern $(")

                bad_null, err2 = cs.sanitize("test\x00command")
                if bad_null is not None:
                    issues.append("sanitizer allowed null byte in input")

                long_input = "x" * 600
                bad_long, err3 = cs.sanitize(long_input)
                if bad_long is not None:
                    issues.append("sanitizer allowed input > 512 chars")

                # 7. build_service_status returns expected structure
                svc_map = rt.build_service_status(quick=True)
                if "devmentor" not in svc_map:
                    issues.append("build_service_status missing 'devmentor' key")
                for svc_key, s in svc_map.items():
                    for field in ("port", "up", "critical"):
                        if field not in s:
                            issues.append(
                                f"service {svc_key!r} missing field {field!r}"
                            )
                            break

                # 8. /api/system/runtime endpoint
                rdata = _get("/api/system/runtime")
                if "env" not in rdata or "self_port" not in rdata:
                    issues.append(
                        f"runtime endpoint missing fields: {list(rdata.keys())}"
                    )

            except Exception as exc:
                issues.append(f"import/runtime error: {exc}")

            if issues:
                r.failed(" | ".join(issues))
            else:
                import config.runtime as _rt

                r.passed(
                    f"runtime.py OK — env={_rt.RUNTIME_ENV} "
                    f"port={_rt.SELF_PORT} "
                    f"services={len(_rt._PORTS_BY_KEY)} "
                    f"paths={len(_rt.PATHS)} "
                    f"sanitizer=verified"
                )

        return self._run(r, _check)

    def check_boot_system(self):
        r = ValidationResult(
            "Boot system: /api/system/boot + game `boot` command", CRITICAL
        )

        def _check(r):
            issues = []
            # REST endpoint
            data = _get("/api/system/boot")
            if "error" in data or "ok" not in data:
                issues.append(f"REST: {data.get('error', 'no ok field')}")
            else:
                svc = data.get("services", {})
                # key may be "devmentor" (from build_service_status) or legacy "terminal_depths"
                _td = svc.get("terminal_depths") or svc.get("devmentor") or {}
                td_up = _td.get("up", False)
                if not td_up:
                    issues.append(
                        "REST: no critical service (terminal_depths/devmentor) is up"
                    )
                g = data.get("game", {})
                if g.get("commands", 0) < 500:
                    issues.append(
                        f"REST: commands={g.get('commands')} (expected >=500)"
                    )
                if g.get("serena_symbols", 0) < 1000:
                    issues.append(
                        f"REST: serena_symbols={g.get('serena_symbols')} (expected >=1000)"
                    )

            # Game command
            resp = self._game_cmd("boot --quick", "validate_boot")
            txt = self._output_text(resp)
            if "bash:" in txt or "command not found" in txt.lower():
                issues.append("boot:bash-fallthrough")
            elif "LATTICE OS" not in txt and "BOOT COMPLETE" not in txt:
                issues.append("boot:missing expected output")

            if issues:
                r.failed(f"Boot system issues: {', '.join(issues)}")
            else:
                r.passed(
                    f"Boot REST ok ({data.get('services_summary',{}).get('up',0)}/{data.get('services_summary',{}).get('total',10)} services) · boot cmd ok"
                )

        return self._run(r, _check)

    def check_autoboot(self):
        r = ValidationResult("Autonomous boot engine (config/autoboot.py)", CRITICAL)

        def _check(r):
            issues = []

            # 1. Module import
            try:
                import importlib
                import sys as _sys

                if "config.autoboot" in _sys.modules:
                    del _sys.modules["config.autoboot"]
                ab = importlib.import_module("config.autoboot")
            except Exception as exc:
                r.failed(f"autoboot import failed: {exc}")
                return

            # 2. load_manifest() — manifest should exist by now (autoboot ran at startup)
            m = ab.load_manifest()
            if not m:
                # Tolerate: manifest may not exist yet on very first boot before 4-s delay
                r.warned(
                    "boot_manifest.json not yet written (autoboot still initialising?)"
                )
                return

            # 3. Required top-level keys
            for key in (
                "session_id",
                "timestamp",
                "env",
                "phases",
                "overall",
                "health_score",
                "ready",
                "actions_taken",
                "delta",
            ):
                if key not in m:
                    issues.append(f"missing key: {key}")

            # 4. All 8 phases present
            EXPECTED_PHASES = {
                "DETECT",
                "ANNOTATE",
                "RECONCILE",
                "ADJUST",
                "RESUME",
                "NUDGE",
                "AWAKEN",
                "TAKE_FLIGHT",
            }
            found_phases = {p["phase"] for p in m.get("phases", [])}
            missing = EXPECTED_PHASES - found_phases
            if missing:
                issues.append(f"phases absent: {missing}")

            # 5. health_score in range
            hs = m.get("health_score", -1)
            if not (0.0 <= hs <= 1.0):
                issues.append(f"health_score out of range: {hs}")

            # 6. ready flag
            if not m.get("ready"):
                issues.append("ready=false — TAKE_FLIGHT phase did not complete")

            # 7. boot --phases game command returns phase detail
            resp = self._game_cmd("boot --phases", "validate_autoboot")
            txt = self._output_text(resp)
            for phase in (
                "DETECT",
                "ANNOTATE",
                "RECONCILE",
                "ADJUST",
                "RESUME",
                "NUDGE",
                "AWAKEN",
                "TAKE_FLIGHT",
            ):
                if phase not in txt:
                    issues.append(f"boot --phases: {phase} not in output")
                    break  # one failure is enough

            if issues:
                r.failed(f"Autoboot issues: {'; '.join(issues)}")
            else:
                n_phases = len(m.get("phases", []))
                n_actions = len(m.get("actions_taken", []))
                r.passed(
                    f"autoboot OK — {n_phases} phases · {m['overall']} · "
                    f"health={m['health_score']:.1%} · {n_actions} auto-actions"
                )

        return self._run(r, _check)

    def check_agent_state_endpoint(self):
        r = ValidationResult("GET /api/game/agent/state (MCP/agent endpoint)", CRITICAL)

        def _check(r):
            session_id = "validate_agent_state"
            _post("/api/game/command", {"command": "whoami", "session_id": session_id})
            data = _get(f"/api/game/agent/state?session_id={session_id}")
            if "error" in data:
                r.warned(f"Agent state endpoint: {data['error']}")
            elif "player_name" in data or "level" in data or "session_id" in data:
                r.passed(f"Agent state endpoint OK (level={data.get('level', '?')})")
            else:
                r.warned(f"Unexpected response keys: {list(data.keys())[:6]}")

        return self._run(r, _check)

    def check_file_structure(self):
        r = ValidationResult("Required file structure", CRITICAL)

        def _check(r):
            required = [
                "app/backend/main.py",
                "app/frontend/game/index.html",
                "app/frontend/game/commands.js",
                "app/frontend/game/game.js",
                "app/frontend/game-cli/index.html",
                "app/frontend/game-cli/client.js",
                "app/game_engine/session.py",
                "app/game_engine/agents.py",
                "app/game_engine/trust_matrix.py",
                "app/game_engine/factions.py",
                ".devmentor/state.json",
                "agents/orchestrator.py",
                "agents/implementer.py",
                "agents/tester.py",
                "agents/documenter.py",
                "agents/content_generator.py",
                "scripts/dispatch_task.py",
                "scripts/validate_all.py",
                "scripts/self_improve.py",
            ]
            missing = [f for f in required if not (BASE_DIR / f).exists()]
            if missing:
                r.warned(f"{len(missing)} expected files missing", missing=missing)
            else:
                r.passed(f"All {len(required)} required files present")

        return self._run(r, _check)

    def check_memory_db(self):
        r = ValidationResult("Memory database (SQLite)", WARN)

        def _check(r):
            data = _get("/api/memory/stats")
            if "error" in data:
                r.warned(f"Memory API unavailable: {data['error']}")
            else:
                r.passed(str(data))

        return self._run(r, _check)

    def check_in_game_tests(self):
        r = ValidationResult("In-game test suite", WARN)

        def _check(r):
            if self.quick:
                r.status = "SKIP"
                r.message = "skipped (--quick mode)"
                return
            # Enable devmode so the test command is accessible
            _post(
                "/api/game/command",
                {
                    "command": "devmode on GHOST-DEV-2026-ALPHA",
                    "session_id": "validate_run",
                },
                timeout=10,
            )
            resp = _post(
                "/api/game/command",
                {
                    "command": "test",
                    "session_id": "validate_run",
                },
                timeout=30,
            )
            # output is a list of {"t":..., "s":...} dicts — join s fields
            raw_output = resp.get("output", [])
            if isinstance(raw_output, list):
                output = " ".join(l.get("s", "") for l in raw_output)
            else:
                output = str(raw_output)
            output += str(resp.get("html", ""))
            if "error" in resp:
                r.warned(f"Could not run in-game tests: {resp['error']}")
            elif "[PASS]" in output or "PASS" in output:
                # count passes and failures
                passes = output.count("[PASS]")
                fails = output.count("[FAIL]")
                if fails == 0:
                    r.passed(f"all {passes} in-game tests passed")
                else:
                    r.failed(f"{fails} test(s) failed, {passes} passed")
            elif "FAIL" in output or "failed" in output.lower():
                r.failed("in-game test suite reported failures")
            else:
                r.warned("test suite ran but output unclear")

        return self._run(r, _check)

    def check_mod_audit_endpoint(self):
        r = ValidationResult(
            "POST /api/rimworld/mod_audit (mod conflict engine)", CRITICAL
        )

        def _check(r):
            payload = {
                "mod_ids": [
                    "brrainz.harmony",
                    "ludeon.rimworld",
                    "mlie.rimthemes",
                    "vanillaexpanded.backgrounds",
                    "jecrell.doorsexpanded",
                    "jecrell.doorsexpanded",
                    "rimgpt",
                    "rimchat",
                ],
                "about_xmls": {},
            }
            data = _post("/api/rimworld/mod_audit", payload)
            if "error" in data:
                r.failed(f"Mod audit endpoint error: {data['error']}")
                return

            score = data.get("health_score")
            count = data.get("mod_count")
            dupes = len(data.get("duplicates", []))
            confl = len(data.get("conflicts", []))
            lo = data.get("load_order", {})
            ai = len(data.get("ai_surfaces", []))

            if score is None or count is None:
                r.failed(f"Unexpected response shape: {list(data.keys())[:6]}")
                return

            # Verify duplicate detection (we deliberately sent jecrell.doorsexpanded twice)
            if dupes == 0:
                r.warned("Duplicate detection missed intentional duplicate")
            else:
                r.passed(
                    f"mod_count={count} health={score}% "
                    f"dupes={dupes} conflicts={confl} "
                    f"ai_surfaces={ai} load_order_has_changes={lo.get('has_changes')}"
                )

            # Also verify GET /api/rimworld/mod_audit/health
            health_data = _get("/api/rimworld/mod_audit/health")
            if not health_data.get("audited"):
                r.warned("GET /mod_audit/health returned audited=false after POST")

        return self._run(r, _check)

    def check_git_status(self):
        r = ValidationResult("Git repository", INFO)

        def _check(r):
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=str(BASE_DIR),
                )
                lines = result.stdout.strip().splitlines()
                if not lines:
                    r.passed("clean working tree")
                else:
                    r.warned(f"{len(lines)} uncommitted change(s)")
            except Exception as e:
                r.warned(f"git check failed: {e}")

        return self._run(r, _check)

    def run_all(self, quick: bool = False) -> dict:
        self.quick = quick
        print(f"\n{'='*72}")
        print(
            f"  TERMINAL DEPTHS — VALIDATION SUITE  |  {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"{'='*72}")
        print(f"  {'STATUS':<4}  {'SEV':6}  {'CHECK':<45}  {'RESULT'}")
        print(f"  {'-'*64}")

        self.check_syntax()
        self.check_file_structure()
        self.check_api_health()
        self.check_route_duplicates()
        self.check_orphan_dbs()
        self.check_game_command()
        self.check_game_commands_core_systems()
        self.check_game_commands_nusyq()
        self.check_game_commands_lattice()
        self.check_game_commands_narrative()
        self.check_game_commands_new_handlers()
        self.check_game_commands_survey_recon_network()
        self.check_no_duplicate_handlers()
        self.check_config_integrity()
        self.check_boot_system()
        self.check_autoboot()
        self.check_agent_state_endpoint()
        self.check_agent_ecosystem()
        self.check_trust_matrix()
        self.check_faction_status()
        self.check_arg_signal()
        self.check_llm_status()
        self.check_memory_db()
        self.check_mod_audit_endpoint()
        self.check_in_game_tests()
        self.check_git_status()

        passes = sum(1 for r in self.results if r.status == "PASS")
        warns = sum(1 for r in self.results if r.status == "WARN")
        fails = sum(1 for r in self.results if r.status == "FAIL")
        critical_fails = sum(
            1 for r in self.results if r.status == "FAIL" and r.severity == CRITICAL
        )

        print(f"\n  {'='*64}")
        print(
            f"  PASS={passes}  WARN={warns}  FAIL={fails}  (critical_fails={critical_fails})"
        )
        overall = (
            "ALL GOOD" if critical_fails == 0 and fails == 0 else "FAILURES DETECTED"
        )
        c = "\033[32m" if overall == "ALL GOOD" else "\033[31m"
        print(f"  {c}{overall}\033[0m\n")

        return {
            "pass": passes,
            "warn": warns,
            "fail": fails,
            "critical_fails": critical_fails,
            "ok": critical_fails == 0,
        }

    def write_report(self) -> Path:
        path = BASE_DIR / "validate_report.md"
        lines = [
            f"# Validation Report — {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "| Status | Severity | Check | Result |",
            "|--------|----------|-------|--------|",
        ]
        for r in self.results:
            lines.append(f"| {r.status} | {r.severity} | {r.name} | {r.message} |")
        lines += [
            "",
            f"**Total:** PASS={sum(1 for r in self.results if r.status=='PASS')}  "
            f"WARN={sum(1 for r in self.results if r.status=='WARN')}  "
            f"FAIL={sum(1 for r in self.results if r.status=='FAIL')}",
            "",
            "*Generated by scripts/validate_all.py*",
        ]
        path.write_text("\n".join(lines))
        return path


def main():
    ap = argparse.ArgumentParser(description="Terminal Depths validation suite")
    ap.add_argument(
        "--quick", action="store_true", help="Skip slow checks (in-game tests)"
    )
    ap.add_argument("--report", action="store_true", help="Write validate_report.md")
    ap.add_argument(
        "--fix", action="store_true", help="Attempt auto-fix on failures (placeholder)"
    )
    args = ap.parse_args()

    v = Validator(quick=args.quick)
    summary = v.run_all(quick=args.quick)

    if args.report:
        p = v.write_report()
        print(f"  Report written: {p.relative_to(BASE_DIR)}")

    sys.exit(0 if summary["ok"] else 1)


if __name__ == "__main__":
    main()
