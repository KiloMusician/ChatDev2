"""
Terminal Depths — In-Game Scripting Engine (Bitburner-style)
Python sandbox with `ns` (netscript) API object.
Scripts run in exec() with restricted builtins and full ns API access.
"""
from __future__ import annotations

import math
import random
import re
import time
import traceback
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .session import GameSession

_SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "chr": chr,
    "dict": dict, "dir": dir, "divmod": divmod, "enumerate": enumerate,
    "filter": filter, "float": float, "format": format, "frozenset": frozenset,
    "getattr": getattr, "hasattr": hasattr, "hash": hash, "hex": hex,
    "int": int, "isinstance": isinstance, "issubclass": issubclass,
    "iter": iter, "len": len, "list": list, "map": map, "max": max,
    "min": min, "next": next, "oct": oct, "ord": ord, "pow": pow,
    "print": print, "range": range, "repr": repr, "reversed": reversed,
    "round": round, "set": set, "slice": slice, "sorted": sorted,
    "str": str, "sum": sum, "tuple": tuple, "type": type, "vars": vars,
    "zip": zip, "True": True, "False": False, "None": None,
    "math": math, "random": random, "re": re,
    "__build_class__": __build_class__,
    "__name__": "__main__",
}


class NS:
    """
    Netscript API — mirrors Bitburner's ns object.
    Exposes game engine to scripts running in the sandbox.
    """

    def __init__(self, session: "GameSession", args: List[str] | None = None):
        self._session = session
        self._output: List[dict] = []
        self._start = time.time()
        self.args: List[str] = args or []

    # ── Output ──────────────────────────────────────────────────────────

    def tprint(self, *args) -> None:
        """Print to the terminal (adds a line to script output)."""
        msg = " ".join(str(a) for a in args)
        self._output.append({"t": "info", "s": msg})

    def tprintRaw(self, line: dict) -> None:
        """Print a raw output-line dict (advanced)."""
        self._output.append(line)

    def print(self, *args) -> None:
        self.tprint(*args)

    # ── Filesystem ───────────────────────────────────────────────────────

    def ls(self, path: str = ".") -> List[str]:
        """List files in a directory. Returns list of names."""
        result = self._session.fs.ls(path)
        if result.get("error"):
            raise FileNotFoundError(result["error"])
        return [e["name"] for e in result.get("entries", [])]

    def read(self, filename: str) -> str:
        """Read a file. Raises FileNotFoundError on missing."""
        r = self._session.fs.cat(filename)
        if r.get("error"):
            raise FileNotFoundError(r["error"])
        self._session.gs.files_read += 1
        return r["content"]

    def write(self, filename: str, content: str, mode: str = "w") -> None:
        """Write (or append) to a file."""
        if mode == "a":
            existing = self._session.fs.cat(filename)
            old = existing.get("content", "") if not existing.get("error") else ""
            content = old + content
        self._session.fs.write_file(filename, content)

    def fileExists(self, filename: str) -> bool:
        """Check if a file exists."""
        r = self._session.fs.cat(filename)
        return not r.get("error")

    def rm(self, filename: str) -> bool:
        """Remove a file."""
        r = self._session.fs.rm(filename)
        return not r.get("error")

    def mv(self, src: str, dst: str) -> None:
        """Move/rename a file."""
        self._session.fs.mv(src, dst)

    def getScriptName(self) -> str:
        """Returns the name of the running script."""
        return getattr(self, "_script_name", "anonymous")

    # ── Player / Server info ─────────────────────────────────────────────

    def getPlayer(self) -> dict:
        """Return player stats dict."""
        return self._session.gs.to_dict()

    def getHostname(self) -> str:
        """Return current node hostname."""
        return "terminal-depths-node-7"

    def getServer(self, target: str | None = None) -> dict:
        """Return server info dict."""
        servers = {
            "node-7":         {"hostname": "node-7",         "ip": "10.0.1.7",   "ram": 32,  "cores": 4,  "root": False, "level": 1},
            "nexus-gateway":  {"hostname": "nexus-gateway",  "ip": "10.0.1.1",   "ram": 64,  "cores": 8,  "root": False, "level": 5},
            "chimera-control":{"hostname": "chimera-control","ip": "10.0.1.254", "ram": 256, "cores": 16, "root": False, "level": 10},
            "node-1":         {"hostname": "node-1",         "ip": "10.0.1.11",  "ram": 8,   "cores": 2,  "root": True,  "level": 1},
        }
        t = target or "node-7"
        return servers.get(t, {"hostname": t, "ip": "10.0.1.99", "ram": 16, "cores": 2, "root": False, "level": 3})

    def getSkill(self, skill: str) -> int:
        """Return skill level (0-100)."""
        return self._session.gs.skills.get(skill, 0)

    # ── Actions ──────────────────────────────────────────────────────────

    def hack(self, target: str = "nexus-gateway") -> dict:
        """Simulate hacking a target. Returns result dict."""
        skill = self._session.gs.skills.get("security", 0)
        success_chance = min(0.9, 0.2 + skill * 0.01)
        success = random.random() < success_chance
        xp_gain = 15 if success else 3
        money = random.randint(500, 5000) if success else 0
        self._session.gs.add_xp(xp_gain, "security")
        return {
            "success": success,
            "target": target,
            "xp_gained": xp_gain,
            "money": money,
            "message": f"[{'SUCCESS' if success else 'FAILED'}] Hack attempt on {target}",
        }

    def scan(self) -> List[str]:
        """Scan the network. Returns list of reachable hostnames."""
        return ["node-1", "node-7", "nexus-gateway", "chimera-control"]

    def nmap(self, target: str = "nexus-gateway") -> List[dict]:
        """Simulate nmap port scan."""
        ports = {
            "node-7": [{"port": 22, "service": "ssh"}, {"port": 3000, "service": "nexus-api"}],
            "nexus-gateway": [{"port": 22, "service": "ssh"}, {"port": 80, "service": "http"}, {"port": 443, "service": "https"}],
            "chimera-control": [{"port": 8443, "service": "chimera-ctrl"}, {"port": 22, "service": "ssh"}],
        }
        return ports.get(target, [{"port": 22, "service": "ssh"}])

    def addXP(self, amount: int, skill: str | None = None) -> dict:
        """Award XP to the player."""
        return self._session.gs.add_xp(amount, skill)

    def completeChallenge(self, challenge_id: str) -> bool:
        """Mark a challenge as completed."""
        if self._session.gs.complete_challenge(challenge_id):
            self._session.gs.add_xp(50, "terminal")
            return True
        return False

    # ── Script execution ─────────────────────────────────────────────────

    def exec(self, cmd: str) -> List[str]:
        """Execute a game command. Returns list of output strings."""
        raw = self._session.cmds.execute(cmd)  # List[dict] — raw command output
        return [r.get("s", "") for r in raw if isinstance(r, dict) and "s" in r]

    def run(self, script_name: str, *args) -> List[dict]:
        """Run another script by name from /home/ghost/scripts/."""
        for path in [
            f"/home/ghost/scripts/{script_name}",
            f"/home/ghost/scripts/{script_name}.py",
            f"/scripts/{script_name}",
            f"/scripts/{script_name}.py",
        ]:
            r = self._session.fs.cat(path)
            if not r.get("error"):
                return run_script(r["content"], self._session, list(args), name=script_name)
        raise FileNotFoundError(f"Script '{script_name}' not found in /home/ghost/scripts/")

    def sleep(self, ms: int = 0) -> None:
        """No-op sleep (synchronous mode — yields nothing)."""
        pass

    # ── Developer helpers (available always, some need dev_mode) ─────────

    def getState(self) -> dict:
        """Return full serialized game state."""
        return self._session._state_snapshot()

    def spawn(self, path: str, content: str = "") -> bool:
        """Create a file at the given path."""
        self._session.fs.write_file(path, content)
        return True

    def getTime(self) -> float:
        """Return seconds since script start."""
        return time.time() - self._start

    def formatNum(self, n: float, decimals: int = 2) -> str:
        """Format a number with commas."""
        return f"{n:,.{decimals}f}"

    # ── LLM / AI ──────────────────────────────────────────────────────────

    def llm(self, prompt: str, system: str | None = None, max_tokens: int = 300,
            temperature: float = 0.7) -> str:
        """
        Call the LLM from inside a script.

        Example:
            response = ns.llm("Generate a hacking challenge about SQL injection.")
            ns.tprint(response)
        """
        try:
            import requests as _req
            r = _req.post(
                "http://localhost:7337/api/llm/generate",
                json={"prompt": prompt, "system": system,
                      "max_tokens": max_tokens, "temperature": temperature},
                timeout=30,
            )
            data = r.json()
            return data.get("response", "[llm: no response]")
        except Exception as e:
            return f"[llm error: {e}]"

    def aiChat(self, messages: list, max_tokens: int = 300) -> str:
        """
        Chat-style LLM call with message history.

        Example:
            reply = ns.aiChat([
                {"role": "system", "content": "You are a helpful hacker."},
                {"role": "user", "content": "What is a buffer overflow?"},
            ])
            ns.tprint(reply)
        """
        try:
            import requests as _req
            r = _req.post(
                "http://localhost:7337/api/llm/chat",
                json={"messages": messages, "max_tokens": max_tokens},
                timeout=30,
            )
            return r.json().get("response", "[aiChat: no response]")
        except Exception as e:
            return f"[aiChat error: {e}]"


def run_script(code: str, session: "GameSession",
               args: List[str] | None = None,
               name: str = "script",
               timeout_ms: int = 5000) -> List[dict]:
    """
    Execute a script in the Python sandbox.
    Returns a list of output-line dicts.
    """
    ns = NS(session, args or [])
    ns._script_name = name

    sandbox = {**_SAFE_BUILTINS, "ns": ns}

    try:
        exec(compile(code, f"<{name}>", "exec"), sandbox)  # noqa: S102
    except SystemExit:
        ns._output.append({"t": "dim", "s": f"[{name}] exited"})
    except Exception as e:
        tb = traceback.format_exc()
        last_line = tb.strip().split("\n")[-1]
        ns._output.append({"t": "error", "s": f"[{name}] {last_line}"})
        ns._output.append({"t": "dim",   "s": tb.replace("\n", " | ")[:200]})

    return ns._output


def validate_script(code: str) -> dict:
    """
    Validate script syntax without running it.
    Returns {"ok": True} or {"ok": False, "error": "..."}
    """
    try:
        compile(code, "<validate>", "exec")
        return {"ok": True}
    except SyntaxError as e:
        return {"ok": False, "error": f"SyntaxError at line {e.lineno}: {e.msg}"}
