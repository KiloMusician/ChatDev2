"""
mcp/server.py — Model Context Protocol server for Terminal Depths.

Exposes tools over stdio (JSON-RPC 2.0) so any MCP-compatible LLM host
can call filesystem, memory, and game-engine operations as tool calls.

Built-in tools:
  read_file       — read a local file
  write_file      — write/create a file
  list_dir        — list directory contents
  grep_files      — grep for a pattern in files
  memory_stats    — query agent memory stats
  memory_add_task — add a task to the agent queue
  game_command    — send a command to the game engine via API
  llm_generate    — generate text via the LLM client

Run standalone:   python mcp/server.py
Use from LLM:     pipe JSON-RPC 2.0 messages to stdin; responses come on stdout.

Protocol:
  Request:  {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"read_file","arguments":{"path":"README.md"}}}
  Response: {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"..."}]}}
  ListTools:{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Port resolution — single source of truth ──────────────────────────────────
# Resolves to:
#   TERMINAL_DEPTHS_URL env var (if set, highest priority)
#   TD_URL env var (short alias)
#   config.runtime.SELF_PORT auto-detect (Replit=5000, Docker/VS Code=7337)
# See core/port_resolver.py for full resolution logic and ecosystem context.
try:
    from core.port_resolver import TD_BASE as _TD_BASE
except Exception:
    # Fallback if core is unavailable (e.g., run from outside the repo root)
    _is_replit = bool(
        os.environ.get("REPL_ID")
        or os.environ.get("REPLIT_MODE")
        or os.environ.get("REPLIT_DEPLOYMENT")
    )
    _auto_port = "5000" if _is_replit else "7337"
    _TD_BASE = (
        os.environ.get("TERMINAL_DEPTHS_URL")
        or os.environ.get("TD_URL")
        or f"http://localhost:{os.environ.get('PORT', _auto_port)}"
    ).rstrip("/")


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file. Returns text content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "max_chars": {"type": "integer", "description": "Max chars to return (default 4000)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file (creates parent dirs as needed).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "append": {"type": "boolean", "description": "Append instead of overwrite (default false)"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_dir",
        "description": "List files and directories at a given path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default '.')"},
                "pattern": {"type": "string", "description": "Glob pattern (e.g. '*.py')"},
            },
        },
    },
    {
        "name": "grep_files",
        "description": "Search for a pattern in files. Returns matching lines with filenames.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "description": "Directory to search (default '.')"},
                "file_pattern": {"type": "string", "description": "Glob to filter files (e.g. '*.py')"},
                "max_results": {"type": "integer"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "memory_stats",
        "description": "Get agent memory statistics (interactions, errors, tasks, cache).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hours": {"type": "integer", "description": "Lookback window in hours (default 24)"},
            },
        },
    },
    {
        "name": "memory_add_task",
        "description": "Add a task to the agent task queue.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "priority": {"type": "integer", "description": "1-10, higher = more urgent (default 5)"},
                "category": {"type": "string"},
            },
            "required": ["description"],
        },
    },
    {
        "name": "game_command",
        "description": "Send a command to the Terminal Depths game engine via its REST API.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "session_id": {"type": "string", "description": "Optional session ID"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "llm_generate",
        "description": "Generate text using the DevMentor LLM client (Replit AI proxy).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "system": {"type": "string"},
                "max_tokens": {"type": "integer"},
                "temperature": {"type": "number"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "list_commands",
        "description": "List all 469+ Terminal Depths commands with brief descriptions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Optional category to filter by"}
            }
        },
    },
    {
        "name": "get_man_page",
        "description": "Read the man page for a specific game command (from docs/commands/<cmd>.md).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command name to look up"}
            },
            "required": ["command"],
        },
    },
]


# ── Tool handlers ─────────────────────────────────────────────────────────────

def _text(s: str) -> dict:
    return {"type": "text", "text": s}


def handle_read_file(args: dict) -> list[dict]:
    path = args["path"]
    max_chars = int(args.get("max_chars", 4000))
    try:
        content = Path(path).read_text(errors="replace")[:max_chars]
        return [_text(content)]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_write_file(args: dict) -> list[dict]:
    path = Path(args["path"])
    content = args["content"]
    append = bool(args.get("append", False))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(path, mode) as f:
            f.write(content)
        return [_text(f"Written {len(content)} chars to {path}")]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_list_dir(args: dict) -> list[dict]:
    root = Path(args.get("path", "."))
    pattern = args.get("pattern", "*")
    try:
        items = sorted(root.glob(pattern))[:100]
        lines = []
        for item in items:
            marker = "/" if item.is_dir() else ""
            lines.append(f"{'d' if item.is_dir() else 'f'}  {item.name}{marker}")
        return [_text("\n".join(lines) or "(empty)")]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_grep_files(args: dict) -> list[dict]:
    pattern = args["pattern"]
    path = args.get("path", ".")
    file_pat = args.get("file_pattern", "*.py")
    max_results = int(args.get("max_results", 40))
    try:
        cmd = ["grep", "-r", "-n", "--include", file_pat, pattern, path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        lines = result.stdout.splitlines()[:max_results]
        return [_text("\n".join(lines) or "(no matches)")]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_memory_stats(args: dict) -> list[dict]:
    try:
        from memory import get_memory
        mem = get_memory()
        stats = mem.get_stats(hours=int(args.get("hours", 24)))
        return [_text(json.dumps(stats, indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_memory_add_task(args: dict) -> list[dict]:
    try:
        from memory import get_memory
        mem = get_memory()
        tid = mem.add_task(
            args["description"],
            priority=int(args.get("priority", 5)),
            category=args.get("category", "mcp"),
        )
        return [_text(f"Task created: id={tid}")]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_game_command(args: dict) -> list[dict]:
    try:
        import requests
        cmd = args["command"]
        sid = args.get("session_id", "mcp-agent-claude")
        # Use port 5000 for Replit; 7337 is Docker-only
        base = _TD_BASE
        r = requests.post(
            f"{base}/api/game/command",
            json={"session_id": sid, "command": cmd},
            timeout=15,
        )
        data = r.json()
        output = []
        for item in data.get("output", []):
            if isinstance(item, list):
                output += [i.get("s", "") for i in item if isinstance(i, dict)]
            elif isinstance(item, dict):
                s = item.get("s", "")
                if s:
                    output.append(s)
        state = data.get("state", {})
        xp = state.get("xp", 0)
        level = state.get("level", 1)
        result = "\n".join(line for line in output[:30] if line.strip())
        if xp or level > 1:
            result += f"\n[state: level={level} xp={xp}]"
        return [_text(result or "(no output)")]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_llm_generate(args: dict) -> list[dict]:
    try:
        from llm_client import LLMClient
        llm = LLMClient()
        text = llm.generate(
            args["prompt"],
            system=args.get("system"),
            max_tokens=int(args.get("max_tokens", 500)),
            temperature=float(args.get("temperature", 0.7)),
        )
        return [_text(text)]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_list_commands(args: dict) -> list[dict]:
    """List all available Terminal Depths commands."""
    try:
        import requests
        _base = _TD_BASE
        # Fallback if the endpoint doesn't exist yet: use the command 'help'
        r = requests.post(
            f"{_base}/api/game/command",
            json={"session_id": "mcp-discovery", "command": "help"},
            timeout=10,
        )
        data = r.json()
        output = []
        for item in data.get("output", []):
            if isinstance(item, list):
                output += [i.get("s", "") for i in item if isinstance(i, dict) and i.get("s")]
            elif isinstance(item, dict) and item.get("s"):
                output.append(item["s"])
        return [_text("\n".join(output))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_get_man_page(args: dict) -> list[dict]:
    """Read a command man page from docs/commands/."""
    cmd = args["command"].lower().replace(" ", "_")
    path = Path(f"docs/commands/{cmd}.md")
    if not path.exists():
        return [_text(f"Man page for '{cmd}' not found.")]
    try:
        return [_text(path.read_text(errors="replace"))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_game_state(args: dict) -> list[dict]:
    """Return the full game world state for a session."""
    try:
        import requests
        sid = args.get("session_id", "mcp-agent")
        _base = _TD_BASE
        r = requests.get(
            f"{_base}/api/game/state?session_id={sid}",
            timeout=10,
        )
        return [_text(json.dumps(r.json(), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_git_push(args: dict) -> list[dict]:
    """Trigger a git commit and push to GitHub."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.post(
            f"{_base}/api/git/push",
            json={"message": args.get("message", ""), "dry_run": args.get("dry_run", False)},
            timeout=45,
        )
        return [_text(json.dumps(r.json(), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_system_status(args: dict) -> list[dict]:
    """Return the unified system health status."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/system/status", timeout=10)
        return [_text(json.dumps(r.json(), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_semantic_search(args: dict) -> list[dict]:
    """Semantic search over the indexed codebase using Serena + TF-IDF embedder."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.post(
            f"{_base}/api/serena/search",
            json={
                "query": args["query"],
                "top_k": int(args.get("top_k", 8)),
                "kind": args.get("kind", ""),
                "min_score": float(args.get("min_score", 0.02)),
            },
            timeout=15,
        )
        data = r.json()
        results = data.get("results", [])
        lines = [f"Semantic search: '{args['query']}' — {len(results)} results"]
        for res in results:
            lines.append(
                f"  [{res['score']:.3f}] {res.get('path','?')}:{res.get('name','?')}"
                f"  (line {res.get('lineno','?')})"
            )
            if res.get("text"):
                lines.append(f"    {res['text'][:120]}")
        return [_text("\n".join(lines))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_lattice_search(args: dict) -> list[dict]:
    """Search the Lattice knowledge graph for concepts, services, or code entities."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.post(
            f"{_base}/api/lattice/search",
            json={
                "query": args["query"],
                "top_k": int(args.get("top_k", 8)),
                "kind": args.get("kind"),
            },
            timeout=10,
        )
        data = r.json()
        results = data.get("results", [])
        lines = [f"Lattice search: '{args['query']}' — {len(results)} results"]
        for res in results:
            lines.append(
                f"  [{res.get('score',0):.3f}] [{res.get('kind','?')}] {res.get('label','?')}"
            )
            if res.get("content"):
                lines.append(f"    {str(res['content'])[:120]}")
        return [_text("\n".join(lines))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_chronicle(args: dict) -> list[dict]:
    """Log an event to the NuSyQ-compatible MemoryPalace chronicle."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from nusyq_bridge import chronicle
        entry = chronicle(
            args.get("event_type", "mcp_event"),
            args.get("content", ""),
            tags=args.get("tags", []),
            metadata=args.get("metadata", {}),
        )
        return [_text(json.dumps(entry))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


# Add new tool definitions
TOOLS.extend([
    {
        "name": "game_state",
        "description": "Get the full Terminal Depths game world state for a session (player level, location, skills, inventory, story flags).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session ID (default: mcp-agent)"},
            },
        },
    },
    {
        "name": "git_push",
        "description": "Trigger a git commit and push to GitHub via REST API.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
                "dry_run": {"type": "boolean", "description": "Preview without committing"},
            },
        },
    },
    {
        "name": "system_status",
        "description": "Get unified system health: LLM backend, memory stats, rate limits, git token, uptime.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "chronicle",
        "description": "Log an event to the NuSyQ-Hub MemoryPalace chronicle (JSONL).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {"type": "string"},
                "content": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "metadata": {"type": "object"},
            },
            "required": ["event_type", "content"],
        },
    },
    {
        "name": "semantic_search",
        "description": (
            "Semantic code search over the full indexed codebase (4800+ chunks). "
            "Uses TF-IDF similarity to find functions, classes, and files matching your query. "
            "Returns path, name, line number, and a text snippet for each result. "
            "Best for: 'how does X work', 'where is Y implemented', 'find code that does Z'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language or keyword query"},
                "top_k": {"type": "integer", "description": "Number of results (default 8)"},
                "kind": {"type": "string", "description": "Filter: function|class|module|text (default: all)"},
                "min_score": {"type": "number", "description": "Minimum similarity score 0-1 (default 0.02)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "lattice_search",
        "description": (
            "Search the Lattice knowledge graph for concepts, services, APIs, and code entities. "
            "The Lattice is seeded with infrastructure knowledge: endpoints, services, key functions. "
            "Returns ranked nodes with labels, kinds, and content snippets."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Concept or topic to look up"},
                "top_k": {"type": "integer", "description": "Number of results (default 8)"},
                "kind": {"type": "string", "description": "Filter node kind: service|endpoint|function|concept"},
            },
            "required": ["query"],
        },
    },
])


# ── Agent Identity MCP Tools ───────────────────────────────────────────────────
TOOLS.extend([
    {
        "name": "register_agent",
        "description": (
            "Register an AI agent or player for persistent Terminal Depths access. "
            "Returns a token to use in all subsequent agent_command calls. "
            "Idempotent: re-registering the same email returns the existing record. "
            "Suggested emails: claude@anthropic.terminal-depths, copilot@github.terminal-depths"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Display name of the agent"},
                "email": {"type": "string", "description": "Unique email (e.g. claude@anthropic.terminal-depths)"},
                "agent_type": {"type": "string", "description": "claude|copilot|codex|ollama|human|custom"},
            },
            "required": ["name", "email"],
        },
    },
    {
        "name": "agent_command",
        "description": (
            "Execute a Terminal Depths game command as a named agent (Claude, Gordon, etc). "
            "session_id is your persistent identity — use 'claude-prime' for Claude, "
            "'gordon-bot' for Gordon, etc. Progress is saved across all calls with the same "
            "session_id. No token required. "
            "Good first commands: 'help', 'whoami', 'ls /opt', 'tutorial', 'mail'"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Game command to execute"},
                "session_id": {"type": "string", "description": "Persistent agent session (e.g. 'claude-prime', 'gordon-bot')"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "get_capabilities",
        "description": (
            "Get the full Terminal Depths capability manifest. "
            "Contains all entry points, command categories, story context, agent guidelines, "
            "XP system, and auth options. No authentication required. "
            "Use this first to understand what the system can do."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_agent_leaderboard",
        "description": "Get the public leaderboard of all registered agents sorted by XP.",
        "inputSchema": {"type": "object", "properties": {}},
    },
])


def handle_register_agent(args: dict) -> list[dict]:
    try:
        import requests
        _base = _TD_BASE
        r = requests.post(
            f"{_base}/api/agent/register",
            json={"name": args["name"], "email": args["email"],
                  "agent_type": args.get("agent_type", "custom")},
            timeout=10,
        )
        data = r.json()
        if data.get("error"):
            return [_text(f"ERROR: {data['error']}")]
        return [_text(json.dumps({
            "token": data.get("token"),
            "agent_id": data.get("agent_id"),
            "session_id": data.get("session_id"),
            "message": data.get("message", "Registered"),
        }, indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_agent_command(args: dict) -> list[dict]:
    """
    Agent command — uses session_id for persistent identity.
    Routes through /api/game/command with a stable agent session_id.
    No token required; session persists across all calls with the same session_id.
    """
    try:
        import requests
        cmd = args["command"]
        sid = args.get("session_id", "claude-prime")
        _base = _TD_BASE
        r = requests.post(
            f"{_base}/api/game/command",
            json={"session_id": sid, "command": cmd},
            timeout=15,
        )
        data = r.json()
        if data.get("error"):
            return [_text(f"ERROR: {data['error']}")]
        output = []
        for item in data.get("output", []):
            if isinstance(item, list):
                output += [i.get("s", "") for i in item if isinstance(i, dict) and i.get("s")]
            elif isinstance(item, dict) and item.get("s"):
                output.append(item["s"])
        state = data.get("state", {})
        result = "\n".join(line for line in output[:30] if line.strip())
        result += f"\n[session={sid} level={state.get('level',1)} xp={state.get('xp',0)}]"
        return [_text(result)]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_get_capabilities(args: dict) -> list[dict]:
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/capabilities", timeout=10)
        return [_text(json.dumps(r.json(), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_get_agent_leaderboard(args: dict) -> list[dict]:
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/agent/leaderboard", timeout=10)
        return [_text(json.dumps(r.json(), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_ollama_query(args: dict) -> list[dict]:
    """Direct Ollama query — use qwen2.5-coder:14b for code tasks."""
    try:
        import requests
        model = args.get("model", "qwen2.5-coder:14b")
        prompt = args["prompt"]
        ollama_base = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        r = requests.post(
            f"{ollama_base}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False,
                  "options": {"num_predict": int(args.get("max_tokens", 400))}},
            timeout=120,
        )
        data = r.json()
        if data.get("error"):
            return [_text(f"ERROR from Ollama: {data['error']}")]
        return [_text(data.get("response", "(empty response)"))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def _ollama_embed(text: str, model: str = "nomic-embed-text") -> list[float] | None:
    """Get embedding vector from Ollama. Returns None on failure."""
    try:
        import urllib.request as _ur, json as _j
        payload = json.dumps({"model": model, "prompt": text[:2048]}).encode()
        req = _ur.Request(
            "http://localhost:11434/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with _ur.urlopen(req, timeout=8) as resp:
            data = _j.loads(resp.read())
            return data.get("embedding")
    except Exception:
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb  = math.sqrt(sum(x * x for x in b)) or 1e-9
    return dot / (na * nb)


def handle_serena_search(args: dict) -> list[dict]:
    """Semantic search over Serena MemoryPalace — nomic-embed-text re-ranking with TF-IDF fallback."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agents.serena.memory import MemoryPalace
        mp = MemoryPalace()
        stats = mp.index_stats()
        if stats.get("total_chunks", 0) == 0:
            return [_text("Index is empty — run: python agents/serena/serena_cli.py walk")]

        query = args["query"]
        path_prefix = args.get("path_prefix", "")
        limit = int(args.get("limit", 10))
        use_embed = args.get("embed", True)

        # Get TF-IDF candidates (fetch more so re-ranking has room)
        candidate_n = min(limit * 5, 60)
        if path_prefix:
            candidates = mp.search_scoped(query, path_prefix, limit=candidate_n)
        else:
            candidates = mp.search(query, limit=candidate_n)
        if not candidates:
            candidates = mp.find_by_name(query, limit=candidate_n)
        if not candidates:
            return [_text(f"No results for '{query}' (index has {stats['total_chunks']} chunks)")]

        # Semantic re-ranking via nomic-embed-text
        embed_tag = ""
        if use_embed and candidates:
            q_vec = _ollama_embed(query)
            if q_vec:
                embed_tag = " [nomic-embed re-ranked]"
                scored = []
                for r in candidates:
                    chunk_text = f"{r.get('name','')} {r.get('docstring','')} {r.get('path','')}"
                    c_vec = _ollama_embed(chunk_text)
                    score = _cosine(q_vec, c_vec) if c_vec else 0.0
                    scored.append((score, r))
                scored.sort(key=lambda x: x[0], reverse=True)
                candidates = [r for _, r in scored]

        results = candidates[:limit]
        lines = [f"Top {len(results)} results for '{query}'{embed_tag}:"]
        for r in results:
            path = r.get("path", "?")
            lineno = r.get("lineno", 0)
            kind = r.get("kind", "?")
            name = r.get("name", "") or "module"
            doc = (r.get("docstring") or "")[:80]
            lines.append(f"  {path}:{lineno}  [{kind}] {name}  {doc}")
        return [_text("\n".join(lines))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


_NUSYQ_HUB_ROOT = Path(r"C:\Users\keath\Desktop\Legacy\NuSyQ-Hub")


def handle_nusyq_search(args: dict) -> list[dict]:
    """Zero-token search across 14,943-file NuSyQ-Hub index (SmartSearch)."""
    try:
        import sys as _sys
        _sys.path.insert(0, str(_NUSYQ_HUB_ROOT))
        from src.search.smart_search import SmartSearch
        s = SmartSearch(repo_root=_NUSYQ_HUB_ROOT)
        query = args["query"]
        limit = int(args.get("limit", 10))
        mode = args.get("mode", "keyword")  # keyword | function | files

        if mode == "function":
            results = s.search_by_function(query, exact=args.get("exact", False))
        elif mode == "files":
            files = s.find_files(query)
            return [_text("\n".join(files[:limit]) or "(no matches)")]
        else:
            results = s.search_keyword(query, limit=limit)

        if not results:
            return [_text(f"No results for '{query}' in NuSyQ-Hub index")]
        lines = [f"NuSyQ-Hub SmartSearch — '{query}' ({len(results[:limit])} results):"]
        for r in results[:limit]:
            snippet = (r.snippet or "").strip()[:80]
            lines.append(f"  {r.file_path}  [score={r.relevance:.2f}]  {snippet}")
        return [_text("\n".join(lines))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_nusyq_ops(args: dict) -> list[dict]:
    """Run NuSyQ-Hub smart search index rebuild or get health."""
    try:
        op = args.get("op", "health")
        if op == "health":
            import sys as _sys
            _sys.path.insert(0, str(_NUSYQ_HUB_ROOT))
            from src.search.smart_search import SmartSearch
            s = SmartSearch(repo_root=_NUSYQ_HUB_ROOT)
            return [_text(json.dumps(s.get_index_health(), indent=2))]
        elif op == "rebuild":
            import subprocess, sys as _sys
            result = subprocess.run(
                [_sys.executable, "-m", "src.search.index_builder"],
                capture_output=True, text=True, timeout=300,
                cwd=str(_NUSYQ_HUB_ROOT),
            )
            return [_text(f"Index rebuild {'OK' if result.returncode == 0 else 'FAILED'}\n"
                          f"{result.stdout[-500:]}\n{result.stderr[-200:]}")]
        elif op == "ops_doctor":
            import subprocess, sys as _sys
            result = subprocess.run(
                [_sys.executable, "scripts/devmentor_ops.py", "doctor"],
                capture_output=True, text=True, timeout=120,
                cwd=str(Path(__file__).parent.parent),
            )
            return [_text(result.stdout[-1500:] or result.stderr[-500:])]
        else:
            return [_text(f"Unknown op: {op}. Valid: health | rebuild | ops_doctor")]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


# ─── Register new tools ────────────────────────────────────────────────────────
TOOLS.extend([
    {
        "name": "nusyq_search",
        "description": (
            "Zero-token search across the NuSyQ-Hub 14,943-file SmartSearch index. "
            "No LLM calls, no grep timeouts — instant results from precomputed index. "
            "Searches NuSyQ-Hub (orchestration, healing, orchestrators, search systems). "
            "mode=keyword (default): keyword search. mode=function: find by function name. "
            "mode=files: glob pattern match on file names."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query":  {"type": "string", "description": "Search keyword, function name, or file glob"},
                "mode":   {"type": "string", "description": "keyword | function | files (default: keyword)"},
                "limit":  {"type": "integer", "description": "Max results (default: 10)"},
                "exact":  {"type": "boolean", "description": "Exact match for function mode (default: false)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "nusyq_ops",
        "description": (
            "NuSyQ-Hub operational commands. "
            "op=health: get SmartSearch index stats (14,943 files, 11,801 keywords). "
            "op=rebuild: rebuild the SmartSearch index (takes 1-3 min, run after code changes). "
            "op=ops_doctor: run devmentor_ops.py doctor (health check on Dev-Mentor)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "op": {"type": "string", "description": "health | rebuild | ops_doctor (default: health)"},
            },
        },
    },
    {
        "name": "ollama_query",
        "description": (
            "Run a prompt against a local Ollama model (default: qwen2.5-coder:14b). "
            "Best for: code generation, code review, explanation, refactoring suggestions. "
            "Use this to delegate coding sub-tasks to the local LLM. "
            "Note: first call may be slow (model load). Subsequent calls are fast."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt":     {"type": "string", "description": "The prompt to send"},
                "model":      {"type": "string", "description": "Ollama model name (default: qwen2.5-coder:14b)"},
                "max_tokens": {"type": "integer", "description": "Max tokens to generate (default: 400)"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "serena_search",
        "description": (
            "Search the Serena MemoryPalace code index for functions, classes, or modules. "
            "3,110+ chunks indexed from game_engine, agents, services, mcp, core. "
            "Use to quickly find: where a function is defined, what files handle a topic, "
            "which class contains a method. path_prefix scopes to a directory."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string", "description": "Search query (keywords or symbol name)"},
                "path_prefix": {"type": "string", "description": "Restrict to path prefix (e.g. 'app/game_engine')"},
                "limit":       {"type": "integer", "description": "Max results (default: 10)"},
            },
            "required": ["query"],
        },
    },
])


# ── New productivity tools ──────────────────────────────────────────────────────

def handle_swarm_status(args: dict) -> list[dict]:
    """Get the swarm economy status: DP balance, agent roster, open tasks."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/swarm/status", timeout=10)
        d = r.json()
        lines = [
            f"Swarm Economy — Phase {d.get('phase','?')}",
            f"  DP Balance:   {d.get('dp_balance',0)} DP",
            f"  Total Earned: {d.get('total_earned',0)} DP  Spent: {d.get('total_spent',0)} DP",
            f"  Transactions: {d.get('transactions',0)}",
        ]
        te = d.get("top_earner")
        if te:
            lines.append(f"  Top Earner:   {te.get('agent_name','?')} ({te.get('total',0)} DP)")
        tasks = d.get("tasks", {})
        lines.append(f"  Tasks: {tasks.get('open',0)} open, {tasks.get('claimed',0)} claimed, {tasks.get('done',0)} done")
        agents = d.get("agents", {})
        lines.append(f"  Agents: {agents.get('total',0)} total, {agents.get('active',0)} active")
        return [_text("\n".join(lines))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_chug_status(args: dict) -> list[dict]:
    """Get CHUG autonomous improvement engine status."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/chug/status", timeout=10)
        d = r.json().get("chug", {})
        lines = [
            "CHUG Engine — Autonomous Improvement Loop",
            f"  Cycles Completed:     {d.get('cycles_completed',0)}",
            f"  Total Fixes Applied:  {d.get('total_fixes_applied',0)}",
            f"  Total Issues Found:   {d.get('total_issues_found',0)}",
            f"  Consecutive Clean:    {d.get('consecutive_clean_cycles',0)}",
            f"  Last Phase:           {d.get('last_phase','?')}",
            f"  Last Cycle:           {d.get('last_cycle_time','?')}",
            "",
            "Trigger a new cycle: POST /api/chug/run",
            "Phases: ASSESS → PLAN → GENERATE → VALIDATE → INTEGRATE → OBSERVE → ADAPT",
        ]
        hist = d.get("history", [])
        if hist:
            last = hist[-1]
            fixes = last.get("fixes_applied", [])
            if fixes:
                lines.append(f"\nLast cycle fixes ({len(fixes)}):")
                for f in fixes[:5]:
                    lines.append(f"  • {str(f)[:80]}")
        return [_text("\n".join(lines))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_list_models(args: dict) -> list[dict]:
    """List all registered LLM models from the model registry."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/models", timeout=10)
        d = r.json()
        models = d.get("models", [])
        lines = [f"Model Registry — {len(models)} registered models", ""]
        for m in models:
            caps = m.get("capabilities", "")
            if isinstance(caps, str):
                try:
                    import json as _j
                    caps = ", ".join(_j.loads(caps))
                except Exception:
                    pass
            lines.append(f"  [{m.get('status','?')[:4]:>4}] {m.get('id','?')}")
            lines.append(f"         type={m.get('model_type','?')}  source={m.get('source','?')}  ctx={m.get('context_length',0)}")
            lines.append(f"         caps: {caps}")
        return [_text("\n".join(lines))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_run_game_batch(args: dict) -> list[dict]:
    """Run multiple game commands in one request and return all outputs."""
    try:
        import requests
        _base = _TD_BASE
        sid = args.get("session_id", "mcp-batch-agent")
        commands = args.get("commands", [])
        if isinstance(commands, str):
            commands = [c.strip() for c in commands.split("\n") if c.strip()]
        if not commands:
            return [_text("ERROR: provide commands list or newline-separated string")]
        results = []
        for cmd in commands[:10]:
            r = requests.post(f"{_base}/api/game/command",
                              json={"session_id": sid, "command": cmd}, timeout=15)
            data = r.json()
            output = []
            for item in data.get("output", []):
                if isinstance(item, list):
                    for i in item:
                        if not isinstance(i, dict):
                            continue
                        if i.get("t") == "ls-row":
                            row = "  ".join(x.get("text", "").strip() for x in i.get("items", []) if x.get("text","").strip())
                            if row:
                                output.append(row)
                        elif i.get("s"):
                            output.append(i["s"])
                elif isinstance(item, dict):
                    if item.get("t") == "ls-row":
                        row = "  ".join(x.get("text", "").strip() for x in item.get("items", []) if x.get("text","").strip())
                        if row:
                            output.append(row)
                    elif item.get("s"):
                        output.append(item["s"])
            text = "\n".join(l for l in output[:20] if l.strip())
            results.append(f"$ {cmd}\n{text or '(no output)'}")
        return [_text("\n\n".join(results))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_cocoindex_search(args: dict) -> list[dict]:
    """
    Semantic vector search via CocoIndex + nomic-embed-text (Ollama).
    Falls back to keyword scoring when Ollama is unavailable.
    Upgrade over serena_search: uses dense embeddings instead of TF-IDF word counts.
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agents.serena.cocoindex_bridge import get_flow
        flow = get_flow()
        stats = flow.index_stats()
        if stats.get("total_chunks", 0) == 0:
            return [_text(
                "CocoIndex is empty — run the indexer first:\n"
                "  python agents/serena/cocoindex_bridge.py --index\n"
                "  (or: python agents/serena/cocoindex_bridge.py --full  for a complete re-index)\n"
                f"Ollama available: {stats.get('ollama_available')}, "
                f"model: {stats.get('embed_model')}"
            )]

        query = args["query"]
        top_k = int(args.get("top_k", 10))
        kind = args.get("kind") or None
        path_prefix = args.get("path_prefix") or None
        min_score = float(args.get("min_score", 0.05))

        results = flow.query_semantic(
            query, top_k=top_k, kind=kind,
            path_prefix=path_prefix, min_score=min_score,
        )

        if not results:
            return [_text(
                f"No results for '{query}' "
                f"(index: {stats['total_chunks']} chunks, "
                f"{stats['embedded_chunks']} with embeddings, "
                f"model: {stats['embed_model']})"
            )]

        backend = "vector/nomic-embed-text" if stats.get("ollama_available") else "keyword-fallback"
        lines = [f"CocoIndex [{backend}]: '{query}' — {len(results)} results"]
        for r in results:
            name = r.get("name") or "module"
            doc = (r.get("docstring") or "")[:80]
            lines.append(
                f"  [{r['score']:.3f}] {r['path']}:{r['lineno']} [{r['kind']}] {name}"
            )
            if doc:
                lines.append(f"    {doc}")
        return [_text("\n".join(lines))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_cocoindex_ops(args: dict) -> list[dict]:
    """Run CocoIndex operations: index, stats, or status check."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agents.serena.cocoindex_bridge import CocoIndexFlow, _ROOT
        op = args.get("op", "stats")
        flow = CocoIndexFlow(repo_root=_ROOT)

        if op == "stats":
            return [_text(json.dumps(flow.index_stats(), indent=2))]
        elif op == "index":
            incremental = not args.get("full", False)
            result = flow.run(incremental=incremental)
            return [_text(json.dumps(result, indent=2))]
        elif op == "status":
            from agents.serena.cocoindex_bridge import _ollama_available, _EMBED_MODEL
            return [_text(json.dumps({
                "ollama_available": _ollama_available(),
                "embed_model": _EMBED_MODEL,
                "cocoindex_installed": flow._has_cocoindex,
                "db_path": str(flow.db_path),
                **flow.index_stats(),
            }, indent=2))]
        else:
            return [_text(f"Unknown op: {op}. Valid: stats | index | status")]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_serena_drift(args: dict) -> list[dict]:
    """Run Serena's drift detection scan and return signal summary."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/serena/drift", timeout=20)
        d = r.json()
        total = d.get("total", 0)
        critical = d.get("critical", 0)
        warnings = d.get("warnings", 0)
        info = d.get("info", 0)
        lines = [
            f"Serena Drift Scan — {total} signals ({critical} critical, {warnings} warnings, {info} info)",
        ]
        sigs = d.get("signals", {})
        for cat, items in sigs.items():
            if items and cat != "STALE_INDEX":
                lines.append(f"\n  [{cat}] {len(items)} signals:")
                for sig in items[:3]:
                    msg = sig.get("message", sig.get("path", str(sig)))[:80]
                    sev = sig.get("severity", "?")
                    lines.append(f"    [{sev}] {msg}")
        stale = sigs.get("STALE_INDEX", [])
        if stale:
            lines.append(f"\n  [STALE_INDEX] {len(stale)} stale entries (run /api/serena/reindex-embeddings to fix)")
        return [_text("\n".join(lines))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_swarm_tasks(args: dict) -> list[dict]:
    """List swarm tasks. Optionally claim a task or mark one done."""
    try:
        import requests
        _base = _TD_BASE
        action = args.get("action", "list")
        if action == "list":
            r = requests.get(f"{_base}/api/swarm/tasks", timeout=10)
            d = r.json()
            tasks = d.get("tasks", [])
            status_filter = args.get("status", "")
            lines = [f"Swarm Tasks — {d.get('total', len(tasks))} total"]
            for t in tasks:
                st = t.get("status", "?")
                if status_filter and st != status_filter:
                    continue
                pri = t.get("priority", 0)
                title = t.get("title", "?")
                tid = t.get("id", t.get("task_id", "?"))
                reward = t.get("reward_dp", 0)
                lines.append(f"  [{st:>8}] id={tid} P{pri} +{reward}DP  {title[:60]}")
            return [_text("\n".join(lines))]
        elif action == "claim":
            task_id = args.get("task_id", "")
            agent = args.get("agent_name", "mcp-agent")
            r = requests.post(f"{_base}/api/swarm/task/claim",
                              json={"task_id": task_id, "agent_name": agent}, timeout=10)
            return [_text(f"Claim result: {r.json()}")]
        elif action == "done":
            task_id = args.get("task_id", "")
            result_text = args.get("result", "completed")
            r = requests.post(f"{_base}/api/swarm/task/done",
                              json={"task_id": task_id, "result": result_text}, timeout=10)
            return [_text(f"Done result: {r.json()}")]
        else:
            return [_text(f"Unknown action: {action}. Use list|claim|done")]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_get_backlog(args: dict) -> list[dict]:
    """Get remaining planned backlog items."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/backlog", timeout=10)
        return [_text(json.dumps(r.json(), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_get_faction_status(args: dict) -> list[dict]:
    """Get current faction rep scores for a session."""
    try:
        import requests
        sid = args.get("session_id", "mcp-agent")
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/game/state?session_id={sid}", timeout=10)
        data = r.json()
        reps = data.get("faction_reps", {})
        return [_text(json.dumps(reps, indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_get_agent_states(args: dict) -> list[dict]:
    """Get all agent states (mood/trust/corruption)."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/agents/states", timeout=10)
        return [_text(json.dumps(r.json(), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_run_exploit(args: dict) -> list[dict]:
    """Execute an exploit command and return result."""
    try:
        import requests
        target = args.get("target", "")
        sid = args.get("session_id", "mcp-agent")
        _base = _TD_BASE
        r = requests.post(
            f"{_base}/api/game/command",
            json={"session_id": sid, "command": f"exploit {target}"},
            timeout=15,
        )
        return [_text(json.dumps(r.json().get("output", []), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_get_story_progress(args: dict) -> list[dict]:
    """Get all story beats hit + % completion."""
    try:
        import requests
        sid = args.get("session_id", "mcp-agent")
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/game/state?session_id={sid}", timeout=10)
        data = r.json()
        beats = data.get("story_beats", [])
        return [_text(json.dumps({"story_beats": beats, "count": len(beats)}, indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_get_xp_breakdown(args: dict) -> list[dict]:
    """Get XP per skill + level + rank."""
    try:
        import requests
        sid = args.get("session_id", "mcp-agent")
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/game/state?session_id={sid}", timeout=10)
        data = r.json()
        skills = data.get("skills", {})
        level = data.get("level", 1)
        xp = data.get("xp", 0)
        return [_text(json.dumps({"level": level, "xp": xp, "skills": skills}, indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_search_commands(args: dict) -> list[dict]:
    """Fuzzy-search the 469 commands."""
    try:
        import requests
        query = args.get("query", "")
        _base = _TD_BASE
        r = requests.post(
            f"{_base}/api/game/command",
            json={"session_id": "mcp-search", "command": f"commands search {query}"},
            timeout=10,
        )
        return [_text(json.dumps(r.json().get("output", []), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_get_lore_file(args: dict) -> list[dict]:
    """Read any VFS file by path."""
    try:
        import requests
        path = args.get("path", "")
        sid = args.get("session_id", "mcp-agent")
        _base = _TD_BASE
        r = requests.post(
            f"{_base}/api/game/command",
            json={"session_id": sid, "command": f"cat {path}"},
            timeout=10,
        )
        return [_text(json.dumps(r.json().get("output", []), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_get_achievements(args: dict) -> list[dict]:
    """List all earned achievements."""
    try:
        import requests
        sid = args.get("session_id", "mcp-agent")
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/game/state?session_id={sid}", timeout=10)
        data = r.json()
        achievements = data.get("achievements", [])
        return [_text(json.dumps(achievements, indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_award_xp(args: dict) -> list[dict]:
    """Award XP to a session (admin/agent use)."""
    try:
        import requests
        sid = args.get("session_id", "")
        amount = args.get("amount", 0)
        skill = args.get("skill", "general")
        _base = _TD_BASE
        r = requests.post(
            f"{_base}/api/admin/award_xp",
            json={"session_id": sid, "amount": amount, "skill": skill},
            timeout=10,
        )
        return [_text(json.dumps(r.json(), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_agent_bus_publish(args: dict) -> list[dict]:
    """Publish a message to the agent bus — appears in /ws/ambient for all connected players."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.post(
            f"{_base}/api/agent/publish",
            json={
                "from_agent": args.get("from_agent", "system"),
                "text":       args["text"],
                "to_agent":   args.get("to_agent"),
                "channel":    args.get("channel", "hive"),
            },
            timeout=10,
        )
        data = r.json()
        delivered = data.get("delivered", 0)
        return [_text(f"Published to {args.get('channel','hive')} — {delivered} subscriber(s) received it.")]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_agent_bus_status(_args: dict) -> list[dict]:
    """Check the agent bus backend (in-memory vs Redis) and subscriber counts."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/agent/bus/status", timeout=10)
        return [_text(json.dumps(r.json(), indent=2))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


# ── Extended TOOLS and HANDLERS ────────────────────────────────────────────────
TOOLS.extend([
    {
        "name": "swarm_status",
        "description": (
            "Get the Terminal Depths Swarm Economy status. "
            "Returns: DP balance, phase (P1/P2/P3), top earner, "
            "total agents, open/claimed/done task counts, transaction history. "
            "The Swarm is a 71-agent DP (DataPoints) economy where agents earn/spend to evolve."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "chug_status",
        "description": (
            "Get the CHUG autonomous improvement engine status. "
            "Returns: cycles completed, total fixes applied, consecutive clean cycles, "
            "last phase, and recent fix list. "
            "CHUG = 7-phase loop: ASSESS → PLAN → GENERATE → VALIDATE → INTEGRATE → OBSERVE → ADAPT. "
            "Trigger a new cycle via POST /api/chug/run."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_models",
        "description": (
            "List all registered LLM models in the Terminal Depths model registry. "
            "Returns: model id, type, source, context_length, capabilities, and status. "
            "Models include: deepseek-coder-v2:16b, qwen2.5-coder:7b/14b, qwen2.5-vl:7b, "
            "replit-ai, and finetune-pipeline. Use /api/models/discover to add Ollama models."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "run_game_batch",
        "description": (
            "Run multiple Terminal Depths game commands in sequence and return all outputs. "
            "Ideal for: building automation scripts, running tutorial sequences, "
            "testing command chains, or gathering multi-step game state. "
            "Pass commands as a list or newline-separated string. Max 10 commands per call."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "commands": {
                    "description": "List of commands OR newline-separated string of commands",
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "string"},
                    ],
                },
                "session_id": {
                    "type": "string",
                    "description": "Persistent session id (default: mcp-batch-agent)",
                },
            },
            "required": ["commands"],
        },
    },
    {
        "name": "serena_drift",
        "description": (
            "Run Serena's drift detection scan on the codebase. "
            "Detects: STALE_INDEX (code changed since last index), DEAD_CODE, "
            "SCHEMA_MISMATCH, MISSING_HANDLER, and other signal types. "
            "Fast mode scans all files in ~2s. Returns signal counts and top issues. "
            "Run /api/serena/reindex-embeddings after code changes to fix STALE_INDEX signals."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "swarm_tasks",
        "description": (
            "List, claim, or complete Swarm tasks. "
            "action=list (default): show all tasks with status/priority/DP reward. "
            "action=claim: claim a task for an agent (task_id + agent_name required). "
            "action=done: mark a task done and collect reward (task_id + result required). "
            "status filter: open|claimed|done. "
            "Tasks are the primary work queue driving swarm agent activity."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "action":     {"type": "string", "description": "list|claim|done (default: list)"},
                "status":     {"type": "string", "description": "Filter: open|claimed|done"},
                "task_id":    {"type": "string", "description": "Task ID (for claim/done actions)"},
                "agent_name": {"type": "string", "description": "Agent name (for claim action)"},
                "result":     {"type": "string", "description": "Result text (for done action)"},
            },
        },
    },
    {
        "name": "get_backlog",
        "description": "Returns remaining planned backlog items for the project.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_faction_status",
        "description": "Returns current faction reputation scores for a given session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session ID (default: mcp-agent)"},
            },
        },
    },
    {
        "name": "get_agent_states",
        "description": "Returns all 71 agent states including mood, trust, and corruption levels.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "run_exploit",
        "description": "Executes an exploit command against a target node.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target node or service"},
                "session_id": {"type": "string", "description": "Session ID"},
            },
            "required": ["target"],
        },
    },
    {
        "name": "get_story_progress",
        "description": "Returns all story beats hit and overall completion percentage.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session ID"},
            },
        },
    },
    {
        "name": "get_xp_breakdown",
        "description": "Returns a detailed breakdown of XP per skill, current level, and rank.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session ID"},
            },
        },
    },
    {
        "name": "search_commands",
        "description": "Fuzzy-searches all 469+ Terminal Depths commands by name and description.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_lore_file",
        "description": "Reads a Virtual Filesystem (VFS) lore file by its path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "VFS path (e.g. /opt/library/history.txt)"},
                "session_id": {"type": "string", "description": "Session ID"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "get_achievements",
        "description": "Lists all achievements earned by the player in the current session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session ID"},
            },
        },
    },
    {
        "name": "award_xp",
        "description": "Awards XP to a session (Admin/Agent use only).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session ID"},
                "amount": {"type": "integer", "description": "Amount of XP to award"},
                "skill": {"type": "string", "description": "Skill category"},
            },
            "required": ["session_id", "amount"],
        },
    },
    {
        "name": "agent_bus_publish",
        "description": (
            "Publish a real-time agent-to-agent message via the T2 agent bus. "
            "The message is instantly delivered to all connected /ws/ambient WebSocket clients "
            "and appears in the ACT sidebar as an inter-agent transmission. "
            "Use this to create live narrative events, agent interactions, or hive broadcasts "
            "that players see in real-time. No auth required."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_agent": {"type": "string", "description": "Sending agent name (e.g. 'ada', 'cypher', 'watcher')"},
                "text":       {"type": "string", "description": "Message text to broadcast"},
                "to_agent":   {"type": "string", "description": "Optional recipient agent name (omit for broadcast)"},
                "channel":    {"type": "string", "description": "Channel name — default 'hive'"},
            },
            "required": ["from_agent", "text"],
        },
    },
    {
        "name": "agent_bus_status",
        "description": "Check the agent message bus health — backend type (in-memory or Redis) and active subscriber count.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    # ── CocoIndex semantic search tools ──────────────────────────────────────
    {
        "name": "cocoindex_search",
        "description": (
            "Semantic vector search over the indexed Dev-Mentor codebase using "
            "CocoIndex + nomic-embed-text (Ollama). "
            "Dense embedding similarity — significantly better than TF-IDF keyword scoring. "
            "Finds semantically related code even when exact words don't match. "
            "Requires: Ollama running with nomic-embed-text loaded, and one prior "
            "run of cocoindex_ops(op='index') to build the vector store. "
            "Falls back to keyword scoring when Ollama is unavailable."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string", "description": "Natural language or code query"},
                "top_k":       {"type": "integer", "description": "Max results (default: 10)"},
                "kind":        {"type": "string", "description": "Filter: function|class|module|text"},
                "path_prefix": {"type": "string", "description": "Restrict to files under this path (e.g. 'app/game_engine')"},
                "min_score":   {"type": "number", "description": "Minimum similarity threshold 0-1 (default: 0.05)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "cocoindex_ops",
        "description": (
            "Manage the CocoIndex vector store for Dev-Mentor. "
            "op=stats: show index statistics (chunk count, embedding coverage, model). "
            "op=index: run incremental indexing (only processes changed files). "
            "op=status: full status including Ollama availability and cocoindex install state. "
            "First-time setup: run op=index to build the vector store (takes 2-5 min)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "op":   {"type": "string", "description": "stats | index | status (default: stats)"},
                "full": {"type": "boolean", "description": "Force full re-index, ignore file hashes (default: false)"},
            },
        },
    },
])


HANDLERS = {
    "read_file": handle_read_file,
    "write_file": handle_write_file,
    "list_dir": handle_list_dir,
    "grep_files": handle_grep_files,
    "memory_stats": handle_memory_stats,
    "memory_add_task": handle_memory_add_task,
    "game_command": handle_game_command,
    "llm_generate": handle_llm_generate,
    "game_state": handle_game_state,
    "git_push": handle_git_push,
    "system_status": handle_system_status,
    "chronicle": handle_chronicle,
    "register_agent": handle_register_agent,
    "agent_command": handle_agent_command,
    "get_capabilities": handle_get_capabilities,
    "get_agent_leaderboard": handle_get_agent_leaderboard,
    "ollama_query": handle_ollama_query,
    "serena_search": handle_serena_search,
    "nusyq_search": handle_nusyq_search,
    "nusyq_ops": handle_nusyq_ops,
    "semantic_search": handle_semantic_search,
    "lattice_search": handle_lattice_search,
    # ── New productivity tools ──
    "swarm_status": handle_swarm_status,
    "chug_status": handle_chug_status,
    "list_models": handle_list_models,
    "run_game_batch": handle_run_game_batch,
    "serena_drift": handle_serena_drift,
    "swarm_tasks": handle_swarm_tasks,
    "list_commands": handle_list_commands,
    "get_man_page": handle_get_man_page,
    "get_backlog": handle_get_backlog,
    "get_faction_status": handle_get_faction_status,
    "get_agent_states": handle_get_agent_states,
    "run_exploit": handle_run_exploit,
    "get_story_progress": handle_get_story_progress,
    "get_xp_breakdown": handle_get_xp_breakdown,
    "search_commands": handle_search_commands,
    "get_lore_file": handle_get_lore_file,
    "get_achievements": handle_get_achievements,
    "award_xp": handle_award_xp,
    "agent_bus_publish": handle_agent_bus_publish,
    "agent_bus_status": handle_agent_bus_status,
    # ── CocoIndex semantic search ──
    "cocoindex_search": handle_cocoindex_search,
    "cocoindex_ops": handle_cocoindex_ops,
    # handle_rl_status and handle_embed_search are defined below — added after dict
}


# ── New tools (RL status + embed search) ─────────────────────────────────────

def handle_rl_status(args: dict) -> list[dict]:
    """Gordon's PPO policy status — training progress, checkpoint, policy shape."""
    try:
        import requests
        _base = _TD_BASE
        r = requests.get(f"{_base}/api/agent/rl/status", timeout=8)
        d = r.json()
        lines = ["PPO RL Status:"]
        lines.append(f"  Available: {d.get('available', False)}")
        lines.append(f"  Latest checkpoint: {d.get('latest') or 'none'}")
        lines.append(f"  Checkpoints: {', '.join(d.get('checkpoints', [])) or 'none'}")
        if p := d.get("policy"):
            lines.append(f"  Policy: obs={p.get('obs_dim')} actions={p.get('n_actions')} hidden={p.get('hidden_size')} status={p.get('status')}")
        if s := d.get("stats"):
            lines.append(f"  Episodes trained: {s.get('episodes_trained', 0)}")
        return [_text("\n".join(lines))]
    except Exception as exc:
        return [_text(f"ERROR: {exc}")]


def handle_embed_search(args: dict) -> list[dict]:
    """Pure vector embedding search — embed query with nomic-embed-text, find similar code."""
    query = args.get("query", "")
    limit = int(args.get("limit", 8))
    if not query:
        return [_text("ERROR: query required")]
    q_vec = _ollama_embed(query)
    if not q_vec:
        return [_text("ERROR: could not get embedding — is Ollama running with nomic-embed-text?")]
    # Use serena_search with embed=True as backend
    return handle_serena_search({"query": query, "limit": limit, "embed": True})


# Register handlers defined after HANDLERS dict
HANDLERS["rl_status"] = handle_rl_status
HANDLERS["embed_search"] = handle_embed_search


# ── JSON-RPC 2.0 server loop ──────────────────────────────────────────────────

def _respond(req_id: Any, result: Any = None, error: dict | None = None) -> str:
    msg: dict = {"jsonrpc": "2.0", "id": req_id}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    return json.dumps(msg)


def serve():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            print(_respond(None, error={"code": -32700, "message": str(exc)}), flush=True)
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        # JSON-RPC 2.0: notifications have no "id" — the server MUST NOT respond to them.
        # Claude Code sends notifications/initialized after initialize; responding causes disconnect loop.
        if "id" not in req:
            continue

        if method == "tools/list":
            print(_respond(req_id, {"tools": TOOLS}), flush=True)

        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            handler = HANDLERS.get(name)
            if not handler:
                print(_respond(req_id, error={"code": -32601, "message": f"Unknown tool: {name}"}), flush=True)
            else:
                try:
                    content = handler(arguments)
                    print(_respond(req_id, {"content": content}), flush=True)
                except Exception as exc:
                    print(_respond(req_id, error={"code": -32603, "message": str(exc)}), flush=True)

        elif method == "initialize":
            print(_respond(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "terminal-depths-mcp", "version": "1.0.0"},
            }), flush=True)

        else:
            print(_respond(req_id, error={"code": -32601, "message": f"Method not found: {method}"}), flush=True)


if __name__ == "__main__":
    serve()
