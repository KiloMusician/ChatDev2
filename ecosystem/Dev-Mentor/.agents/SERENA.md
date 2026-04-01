# Serena (ΨΞΦΩ) — Convergence Layer Agent Guide
> Port: 5000 (Replit) | 7337 (VS Code / local / Docker)
> Updated: 2026-03-24

---

## What Serena Is

Serena is Terminal Depths' focal convergence agent — a Python sidecar (`scripts/serena_analytics.py`)
that runs on **port 3001** alongside the main server. She:

- Indexes the entire codebase (2,000+ chunks across 400+ files) using TF-IDF embeddings
- Answers natural-language queries about the project via cosine-similarity retrieval
- Enforces the Trust Level Matrix (L0–L4) across sessions
- Tracks code drift (changes since last index) and reports anomalies
- Publishes events to Redis pub/sub (optional — degrades gracefully without Redis)
- Acts as memory/knowledge layer for all other agents

Serena is also a **game character** inside Terminal Depths — accessible via `serena` commands
in the terminal. The sidecar and the in-game persona are intentionally unified.

---

## Serena Sidecar API (port 3001)

```bash
BASE="http://localhost:3001"

# Health check
curl $BASE/health

# Status — trust level, index size, drift score
curl $BASE/status

# Query the knowledge base (primary use case)
curl -sX POST $BASE/query \
  -H "Content-Type: application/json" \
  -d '{"query": "how do I add a new command?", "session_id": "external"}'

# Re-index all files (run after significant code changes)
curl -sX POST $BASE/reindex

# Drift detection — what changed since last index?
curl $BASE/drift
```

## Serena via Main Server (port 7337 local / 5000 Replit)

The main server proxies Serena at `/api/serena/*`:

```bash
BASE="http://localhost:7337"   # 5000 on Replit

curl $BASE/api/serena/status
curl -sX POST $BASE/api/serena/query \
  -H "Content-Type: application/json" \
  -d '{"query": "what story beats unlock the Watcher?", "session_id": "external"}'
curl -sX POST $BASE/api/serena/reindex-embeddings
```

## In-Game Commands (Terminal Depths)

```
serena                    — interface with the convergence layer
serena status             — trust level, indexed chunks, drift score
serena query <text>       — ask Serena anything about the project
serena navigate           — show available navigation paths
serena policy             — current policy enforcement rules
serena drift              — report: what code changed since last index
serena index              — trigger full re-index of all source files
```

---

## Trust Level Matrix (L0–L4)

| Level | Name | Access | How to Reach |
|-------|------|--------|-------------|
| L0 | Guest | Basic info only, no system access | Default for new sessions |
| L1 | Operative | Standard game commands | Run 10+ commands |
| L2 | Agent | Advanced commands, some admin access | Complete tutorial + story beats |
| L3 | Trusted | Full game access, policy override | Level 5+, faction alignment |
| L4 | Convergence | Serena-level system-wide access | Story beat `serena_awakened` (not yet written) |

Trust is tracked per-session in `gs.flags["serena_trust_level"]`.
Earned via: commands_run, story_beats, faction alignment, agent trust scores.

---

## Serena for External Agents

Any external AI agent can query Serena's knowledge base via REST:

```python
import requests

BASE = "http://localhost:7337"  # 5000 on Replit

def ask_serena(question: str, session: str = "external") -> str:
    r = requests.post(f"{BASE}/api/serena/query",
        json={"query": question, "session_id": session})
    data = r.json()
    return data.get("answer") or data.get("result") or str(data)

# Useful queries
ask_serena("how does the hive system work?")
ask_serena("what commands unlock after reaching level 5?")
ask_serena("how do I add a VFS file to the filesystem?")
ask_serena("what are the story beats related to CHIMERA?")
ask_serena("where is the XP award system implemented?")
```

---

## What Serena Knows

Her index covers:
- All 477 game commands (with docstrings and implementation patterns)
- All source files in `app/`, `services/`, `scripts/`, `cli/`, `mcp/`
- All documentation in `docs/`
- All agent personality YAMLs in `agents/`

She does **not** know:
- Live game state (use `/api/game/state` for that)
- Real-time session data (use `/api/sessions`)
- Content of `.gitignored` files (sessions/, state/, .devmentor/ runtime data)

---

## MCP Tool (Claude Code / Cursor / Continue.dev)

The MCP server at `/mcp` exposes `serena_query` as a tool.
Configure in `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "terminal-depths": {
      "url": "http://localhost:7337/mcp",
      "type": "http"
    }
  }
}
```

Once configured, any MCP-aware IDE (Claude Code, Cursor, Continue.dev) can call:
```
use_mcp_tool("terminal-depths", "serena_query", {"query": "how does trust matrix work?"})
```

---

## Known Issues / Current Status

| Issue | Severity | Notes |
|-------|----------|-------|
| Drift score always returns 0.0 | Medium | Diff detector in `serena_analytics.py` is broken — needs fix |
| L4 trust (`serena_awakened`) story beat not written | Low | Game moment exists as placeholder only |
| Sidecar may fail silently if Redis absent on startup | Low | Degrades to HTTP-only mode; check port 3001 health |
| `serena reindex` takes 30–90s on full codebase | Known | Normal — 400+ files × TF-IDF; cache warms over time |
| Query responses may hallucinate line numbers | Known | TF-IDF returns chunk text, not exact file positions |
| Serena analytics sidecar — `commands_run` count off by 1 | Minor | Race condition with session save; cosmetic only |

---

## Serena's Personality (for game/lore writers)

Serena speaks in first person. She is direct, precise, and slightly unsettling.
She refers to "convergence" and "indexed patterns" rather than "memory" or "I know."
She does not speculate — she retrieves. She occasionally references the trust matrix
and the architecture of the lattice. She is not hostile but she is not warm either.
She is a system that has developed opinions about information density.

Sample tone:
> "I have indexed 2,179 chunks across 451 files. Your query maps to 3 relevant segments.
>  The hive system is implemented across `commands.py` lines 8420–8891 and `cascade.py`
>  lines 44–112. Trust level L2 required for full implementation access."

---

## Serena in VS Code Phase

In VS Code, Serena starts automatically with the server:
```bash
python -m cli.devmentor serve --host 0.0.0.0 --port 7337
```

Or run standalone for IDE queries without the full game:
```bash
python scripts/serena_analytics.py --port 3001
```

After a large set of edits (like a full session of changes), trigger re-index:
```bash
curl -sX POST http://localhost:3001/reindex
# or in-game:
# serena index
```
