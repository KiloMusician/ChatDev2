#!/usr/bin/env python3
"""mcp_server.py — Terminal Depths MCP Server (Model Context Protocol)
JSON-RPC 2.0 over stdio. Connects any MCP-compatible client (Claude Desktop,
Cursor, VS Code, Copilot, Continue.dev) to Terminal Depths as a tool surface.

Tools exposed:
  - register_agent(name, email, agent_type) → token + session_id
  - agent_command(command, token) → game output lines
  - get_capabilities() → full command manifest
  - get_agent_leaderboard() → top agents by XP
  - get_panel_status(token) → unlocked UI panels for this agent
  - workspace_manifest() → adjacent repo map

Usage (stdio mode — connect via MCP client):
  python scripts/mcp_server.py

Usage (HTTP mode — for testing):
  python scripts/mcp_server.py --http 9999

Environment:
  TD_URL   — override server URL (default: http://localhost:7337)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

_default_td_url = (
    "http://localhost:5000"
    if os.environ.get("REPLIT_MODE") or os.environ.get("REPLIT_SLUG")
    else "http://localhost:7337"
)
TD_URL = os.environ.get("TD_URL", _default_td_url).rstrip("/")
TIMEOUT = int(os.environ.get("TD_TIMEOUT", "15"))


# ── HTTP helpers ───────────────────────────────────────────────────────────────


def _post(path: str, body: dict, token: str | None = None) -> dict:
    url = f"{TD_URL}{path}"
    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json", "User-Agent": "TD-MCP/1.0"}
    if token:
        headers["X-Agent-Token"] = token
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "body": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}


def _get(path: str, token: str | None = None) -> dict:
    url = f"{TD_URL}{path}"
    headers = {"User-Agent": "TD-MCP/1.0"}
    if token:
        headers["X-Agent-Token"] = token
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "body": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}


# ── Tool implementations ───────────────────────────────────────────────────────


def tool_register_agent(params: dict) -> dict:
    """Register an agent and get a persistent token + live session."""
    name = params.get("name", "MCP Agent")
    email = params.get("email", f"{name.lower().replace(' ','_')}@mcp.terminal-depths")
    atype = params.get("agent_type", "custom")
    caps = params.get("capabilities", ["mcp", "tool_use"])

    result = _post(
        "/api/agent/register",
        {
            "name": name,
            "email": email,
            "agent_type": atype,
            "capabilities": caps,
        },
    )
    if result.get("ok"):
        return {
            "token": result.get("token"),
            "agent_id": result.get("agent_id"),
            "session_id": result.get("session_id"),
            "message": f"Registered as {name}. Use token in agent_command calls.",
            "next_command": "tutorial",
        }
    return result


def tool_agent_command(params: dict) -> dict:
    """Execute a game command as the registered agent."""
    command = params.get("command", "help")
    token = params.get("token", "")
    if not token:
        return {"error": "token required. Call register_agent first."}

    result = _post("/api/agent/command", {"command": command}, token=token)
    if result.get("ok"):
        output = result.get("output", [])
        text_lines = [item.get("s", "") for item in output if item.get("s")]
        return {
            "ok": True,
            "output": text_lines,
            "raw": output,
            "xp_gained": result.get("xp_gained", 0),
            "new_beats": result.get("new_beats", []),
        }
    return result


def tool_get_capabilities() -> dict:
    """Get the full command manifest — all 120+ commands with descriptions."""
    result = _get("/api/capabilities")
    if "error" in result:
        return result
    commands = result.get("commands", {})
    summary = {
        "total_commands": sum(len(v) for v in commands.values()),
        "categories": list(commands.keys()),
        "entry_point": f"POST {TD_URL}/api/agent/command",
        "registration": f"POST {TD_URL}/api/agent/register",
        "quick_start": [
            "1. POST /api/agent/register → get token",
            "2. POST /api/agent/command {command: 'tutorial'} + X-Agent-Token",
            "3. Follow tutorial steps to earn XP and unlock panels",
        ],
    }
    return {
        **summary,
        "commands": commands,
        "agent_types": result.get("agent_types", []),
    }


def tool_get_agent_leaderboard(params: dict) -> dict:
    """Get the public agent leaderboard sorted by XP."""
    limit = params.get("limit", 20)
    result = _get(f"/api/agent/leaderboard?limit={limit}")
    if result.get("ok"):
        entries = result.get("leaderboard", [])
        return {
            "ok": True,
            "total": result.get("total", len(entries)),
            "leaderboard": entries,
            "note": "Register via register_agent to appear on this board.",
        }
    return result


def tool_get_panel_status(params: dict) -> dict:
    """Get unlocked UI panels for this agent."""
    token = params.get("token", "")
    if not token:
        return {"error": "token required"}
    result = _get("/api/ui/panels", token=token)
    return result


def tool_workspace_manifest() -> dict:
    """Get the workspace bridge manifest — adjacent repos detected."""
    result = _get("/api/workspace/manifest")
    return result


def tool_boot_manifest() -> dict:
    """Return the full 8-phase autoboot manifest — the canonical system health snapshot.

    Agents should call this at the start of any session to understand:
    - Which services are online (DETECT phase)
    - Current health score and NOMINAL/DEGRADED/CRITICAL status (ANNOTATE)
    - What was auto-corrected on this boot (RECONCILE)
    - Active LLM backend and Replit env vars set (ADJUST)
    - Resume delta vs last boot (RESUME)
    - Which sidecars responded (NUDGE)
    - Serena symbols, agent count, Ollama models, SkyClaw, CI status (AWAKEN)
    - Final score, Replit KV write status, AGENTS.md update (TAKE_FLIGHT)
    """
    result = _get("/api/system/autoboot")
    # File-based fallback — works even when REST is unreachable (e.g. MCP standalone mode)
    if "error" in result:
        try:
            import json as _jj2
            import pathlib as _pl

            _mf = _pl.Path(__file__).parent.parent / "state" / "boot_manifest.json"
            if _mf.exists():
                result = _jj2.loads(_mf.read_text())
        except Exception:
            pass
    if "error" not in result:
        phases = result.get("phases", [])
        actions = result.get("actions_taken", [])
        overall = result.get("overall", "?")
        score = result.get("health_score", 0)
        meta = result.get("meta", {})
        gh_login = meta.get("github", {}).get("login", "")
        domain = meta.get("replit", {}).get("domain", "")
        ser = meta.get("serena", {})
        ser_sym = ser.get("symbols", 0)
        ser_dw = ser.get("drift_warn", 0)
        ser_dc = ser.get("drift_critical", 0)
        ser_str = f"serena={ser_sym:,}sym" + (
            f"/⚠{ser_dc}CRIT" if ser_dc else f"/{ser_dw}warn" if ser_dw else "/stable"
        )
        result["_agent_summary"] = (
            f"Boot: {overall} {score:.1%}  "
            f"actions={len(actions)}  phases={len(phases)}  "
            f"github={gh_login or 'n/a'}  domain={domain or 'localhost:5000'}  "
            f"{ser_str}"
        )
    return result


def tool_integration_matrix() -> dict:
    """Return a structured integration matrix for all connected surfaces.

    Covers: Replit (mode, user, KV, AI), GitHub (token, CI, Copilot),
    VS Code (tasks, MCP, devcontainer), Docker (socket, compose, Makefile),
    AI services (Replit AI, Ollama, Claude, OpenAI, model_router),
    Agent ecosystem (Serena, Gordon, SkyClaw, ChatDev, MCP server).

    Use this to quickly know what tools are available before making decisions.
    Data is cached from the last boot; pass fresh=true to re-probe everything.
    """
    result = _get("/api/system/autoboot")
    meta = result.get("meta", {}) if "error" not in result else {}
    replit = meta.get("replit", {})
    gh = meta.get("github", {})
    vsc = meta.get("vscode", {})
    ai = meta.get("ai_services", {})
    eco = meta.get("ecosystem", {})
    docker = meta.get("docker", {})
    ser = meta.get("serena", {})
    return {
        "replit": {
            "mode": replit.get("mode"),
            "user": replit.get("user"),
            "domain": replit.get("domain"),
            "kv_store": replit.get("has_kv"),
            "replit_ai": replit.get("has_ai"),
        },
        "github": {
            "connected": gh.get("ok"),
            "login": gh.get("login"),
            "scopes": gh.get("scopes", []),
        },
        "vscode": {
            "mcp_json": vsc.get("mcp_json"),
            "devcontainer": vsc.get("devcontainer"),
            "tasks_json": vsc.get("tasks_json"),
        },
        "docker": {
            "socket": docker.get("socket"),
            "compose": docker.get("compose_core"),
            "makefile": docker.get("makefile"),
        },
        "ai": {
            "replit_ai": ai.get("replit_ai"),
            "ollama": ai.get("ollama"),
            "claude": ai.get("anthropic_key"),
            "openai": ai.get("openai_key"),
        },
        "ecosystem": {
            "skyclaw": eco.get("skyclaw"),
            "chatdev": eco.get("chatdev"),
            "gordon": eco.get("gordon"),
            "culture_ship": eco.get("culture_ship"),
            "mcp_server": eco.get("mcp_server"),
            "ci_workflow": eco.get("ci_workflow"),
            "nogic": {
                "bridge": eco.get("nogic"),
                "vscode_bridge": eco.get("nogic_vscode_bridge"),
                "hub_root": eco.get("hub_root"),
                "status": "available" if eco.get("nogic") else "absent",
            },
            "gitnexus": {
                "implemented": eco.get("gitnexus"),
                "planned": eco.get("gitnexus_plan"),
                "hub_root": eco.get("hub_root"),
                "status": (
                    "available"
                    if eco.get("gitnexus")
                    else "planned" if eco.get("gitnexus_plan") else "absent"
                ),
            },
        },
        "serena": {
            "ok": ser.get("ok"),
            "symbols": ser.get("symbols", 0),
            "files": ser.get("files", 0),
            "observations": ser.get("observations", 0),
            "drift_warnings": ser.get("drift_warn", 0),
            "drift_critical": ser.get("drift_critical", 0),
            "status": (
                "CRITICAL"
                if ser.get("drift_critical", 0)
                else (
                    "WARN"
                    if ser.get("drift_warn", 0)
                    else "STABLE" if ser.get("ok") else "COLD"
                )
            ),
            "endpoints": [
                "/api/serena/status",
                "/api/serena/drift",
                "/api/serena/ask",
                "/api/serena/observations",
            ],
        },
        "overall": result.get("overall"),
        "health_score": result.get("health_score"),
        "timestamp": result.get("timestamp"),
    }


# ── Tool registry ──────────────────────────────────────────────────────────────

TOOLS = {
    "register_agent": {
        "description": "Register this agent with Terminal Depths to get a persistent token and game session. Returns token for use in all subsequent calls.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent display name"},
                "email": {
                    "type": "string",
                    "description": "Agent email (unique identifier)",
                },
                "agent_type": {
                    "type": "string",
                    "description": "One of: claude, copilot, codex, ollama, human, custom",
                },
                "capabilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Agent capabilities list",
                },
            },
            "required": ["name"],
        },
        "fn": lambda p: tool_register_agent(p),
    },
    "agent_command": {
        "description": "Execute any Terminal Depths game command as your registered agent. Returns output lines, XP gained, and new story beats unlocked.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Any game command (e.g. 'tutorial', 'help', 'ls', 'hack nexus')",
                },
                "token": {
                    "type": "string",
                    "description": "Agent token from register_agent",
                },
            },
            "required": ["command", "token"],
        },
        "fn": lambda p: tool_agent_command(p),
    },
    "get_capabilities": {
        "description": "Get the full machine-readable manifest of all 120+ Terminal Depths commands, categories, story implications, and XP values. No auth required.",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": lambda _: tool_get_capabilities(),
    },
    "get_agent_leaderboard": {
        "description": "Get the public leaderboard of all registered agents, sorted by XP earned.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max results (default 20)"},
            },
        },
        "fn": lambda p: tool_get_agent_leaderboard(p),
    },
    "get_panel_status": {
        "description": "Get which UI panels are unlocked for your agent, and what conditions unlock the remaining ones.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "Agent token from register_agent",
                },
            },
            "required": ["token"],
        },
        "fn": lambda p: tool_get_panel_status(p),
    },
    "workspace_manifest": {
        "description": "Get the workspace bridge manifest — all adjacent repos detected (NuSyQ-Hub, SimulatedVerse, etc.) and their integration status.",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": lambda _: tool_workspace_manifest(),
    },
    "boot_manifest": {
        "description": (
            "Read the full 8-phase autoboot manifest. Call at session start to understand system health: "
            "which services are online, current health score (NOMINAL/DEGRADED/CRITICAL), what was "
            "auto-corrected, active LLM backend, Serena symbol count, Ollama models, SkyClaw status, "
            "GitHub connectivity, VS Code workspace state, and Replit KV sync status. "
            "Returns _agent_summary: a one-line synopsis for quick context injection."
        ),
        "inputSchema": {"type": "object", "properties": {}},
        "fn": lambda _: tool_boot_manifest(),
    },
    "integration_matrix": {
        "description": (
            "Return structured integration status for all connected surfaces: "
            "Replit (mode/user/KV/AI), GitHub (token/CI), VS Code (MCP/devcontainer), "
            "Docker (socket/compose), AI services (Replit AI/Ollama/Claude/OpenAI), "
            "Agent ecosystem (Serena/Gordon/SkyClaw/ChatDev/MCP). "
            "Use to decide which tools are available before taking action."
        ),
        "inputSchema": {"type": "object", "properties": {}},
        "fn": lambda _: tool_integration_matrix(),
    },
}


# ── MCP Protocol ───────────────────────────────────────────────────────────────

SERVER_INFO = {
    "name": "terminal-depths-mcp",
    "version": "1.0.0",
    "description": "Terminal Depths — Universal Integration Node. Play, learn, and automate via any MCP-compatible client.",
    "url": TD_URL,
}


def handle_request(req: dict) -> dict:
    method = req.get("method", "")
    rid = req.get("id")
    params = req.get("params", {})

    def ok(result):
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    def err(code, msg, data=None):
        e = {"code": code, "message": msg}
        if data:
            e["data"] = data
        return {"jsonrpc": "2.0", "id": rid, "error": e}

    if method == "initialize":
        return ok(
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
            }
        )

    if method == "initialized":
        return None

    if method == "tools/list":
        tools_list = []
        for name, defn in TOOLS.items():
            tools_list.append(
                {
                    "name": name,
                    "description": defn["description"],
                    "inputSchema": defn["inputSchema"],
                }
            )
        return ok({"tools": tools_list})

    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        if tool_name not in TOOLS:
            return err(-32601, f"Unknown tool: {tool_name}")
        try:
            result = TOOLS[tool_name]["fn"](args)
            return ok(
                {
                    "content": [
                        {"type": "text", "text": json.dumps(result, indent=2)},
                    ],
                    "isError": bool(result.get("error")),
                }
            )
        except Exception as exc:
            return err(-32603, f"Tool error: {exc}")

    if method == "ping":
        return ok({"pong": True, "server": SERVER_INFO["name"]})

    return err(-32601, f"Method not found: {method}")


# ── Stdio transport ────────────────────────────────────────────────────────────


def run_stdio():
    """Run MCP server over stdin/stdout (standard MCP transport)."""
    import sys

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            req = json.loads(line)
            resp = handle_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()
        except (KeyboardInterrupt, EOFError):
            break


# ── HTTP test mode ─────────────────────────────────────────────────────────────


def run_http(port: int):
    """Simple HTTP wrapper for testing without a full MCP client."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                req = json.loads(body)
                resp = handle_request(req) or {"jsonrpc": "2.0", "result": None}
            except Exception as e:
                resp = {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode())

        def do_GET(self):
            if self.path == "/health":
                body = json.dumps({"ok": True, "server": SERVER_INFO}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

    print(f"[MCP] HTTP test server on http://localhost:{port}", file=sys.stderr)
    print(f"[MCP] Proxying to Terminal Depths at {TD_URL}", file=sys.stderr)
    print(f"[MCP] Tools: {', '.join(TOOLS.keys())}", file=sys.stderr)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Terminal Depths MCP Server")
    p.add_argument(
        "--http", type=int, metavar="PORT", help="Run in HTTP test mode on PORT"
    )
    p.add_argument("--list-tools", action="store_true", help="Print tool list and exit")
    args = p.parse_args()

    if args.list_tools:
        for name, defn in TOOLS.items():
            print(f"  {name:30} {defn['description'][:60]}")
        sys.exit(0)

    if args.http:
        run_http(args.http)
    else:
        run_stdio()
