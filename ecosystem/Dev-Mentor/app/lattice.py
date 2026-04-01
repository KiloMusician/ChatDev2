"""
The Lattice — collective knowledge store for the Terminal Keeper ecosystem.

Provides:
  - SQLite-backed event and insight storage
  - Simple cosine-similarity search over knowledge embeddings (uses
    a word-frequency vector when no embedding model is available)
  - REST endpoints mounted at /api/lattice/
  - Redis pub/sub integration for live knowledge updates

The Lattice is queried by Serena, Gordon, SkyClaw, and the Culture Ship.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

# ─── Config ───────────────────────────────────────────────────────────────────

STATE_DIR   = Path(__file__).parent.parent / "state"
LATTICE_DB  = STATE_DIR / "lattice.db"

router = APIRouter(prefix="/api/lattice", tags=["lattice"])

# ─── DB setup ─────────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(LATTICE_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            id          TEXT PRIMARY KEY,
            label       TEXT NOT NULL,
            kind        TEXT NOT NULL DEFAULT 'concept',
            content     TEXT NOT NULL DEFAULT '',
            source      TEXT,
            vec_json    TEXT,
            ts          TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS edges (
            src         TEXT NOT NULL,
            dst         TEXT NOT NULL,
            relation    TEXT NOT NULL DEFAULT 'related_to',
            weight      REAL NOT NULL DEFAULT 1.0,
            ts          TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (src, dst, relation)
        );
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            channel     TEXT NOT NULL,
            data        TEXT NOT NULL,
            ts          TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind);
        CREATE INDEX IF NOT EXISTS idx_edges_src  ON edges(src);
        CREATE INDEX IF NOT EXISTS idx_events_ch  ON events(channel);
    """)
    conn.commit()


# ─── Tiny TF-IDF embedding (no ML deps required) ─────────────────────────────

_STOPWORDS = {"the","a","an","is","in","on","of","to","and","or","for","with","it","as"}

def _tokenise(text: str) -> list[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 2]

def _bow(text: str) -> dict[str, float]:
    tokens = _tokenise(text)
    if not tokens:
        return {}
    freq: dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    total = len(tokens)
    return {k: v / total for k, v in freq.items()}

def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot  = sum(a[k] * b[k] for k in keys)
    magA = math.sqrt(sum(v * v for v in a.values()))
    magB = math.sqrt(sum(v * v for v in b.values()))
    return dot / (magA * magB) if magA * magB else 0.0


# ─── Core API ─────────────────────────────────────────────────────────────────

def add_node(label: str, content: str, kind: str = "concept",
             source: str | None = None, node_id: str | None = None) -> str:
    nid = node_id or hashlib.md5(f"{kind}:{label}".encode()).hexdigest()[:12]
    vec = json.dumps(_bow(f"{label} {content}"))
    with _conn() as c:
        c.execute("""
            INSERT INTO nodes (id, label, kind, content, source, vec_json, ts)
            VALUES (?,?,?,?,?,?,datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                content=excluded.content, vec_json=excluded.vec_json,
                ts=excluded.ts
        """, (nid, label, kind, content, source, vec))
    return nid


def add_edge(src: str, dst: str, relation: str = "related_to",
             weight: float = 1.0) -> None:
    with _conn() as c:
        c.execute("""
            INSERT INTO edges (src, dst, relation, weight)
            VALUES (?,?,?,?)
            ON CONFLICT(src,dst,relation) DO UPDATE SET weight=excluded.weight
        """, (src, dst, relation, weight))


def search(query: str, kind: str | None = None, top_k: int = 10) -> list[dict]:
    q_vec = _bow(query)
    with _conn() as c:
        sql  = "SELECT id,label,kind,content,source,vec_json FROM nodes"
        args: list[Any] = []
        if kind:
            sql += " WHERE kind=?"
            args.append(kind)
        rows = c.execute(sql, args).fetchall()

    scored: list[tuple[float, dict]] = []
    for row in rows:
        try:
            vec = json.loads(row["vec_json"] or "{}")
        except Exception:
            vec = {}
        score = _cosine(q_vec, vec)
        if score > 0:
            scored.append((score, dict(row)))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": round(s, 4), **d} for s, d in scored[:top_k]]


def get_node(node_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
    return dict(row) if row else None


def get_neighbours(node_id: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute("""
            SELECT n.id, n.label, n.kind, e.relation, e.weight
            FROM edges e JOIN nodes n ON n.id = e.dst
            WHERE e.src = ?
            UNION
            SELECT n.id, n.label, n.kind, e.relation, e.weight
            FROM edges e JOIN nodes n ON n.id = e.src
            WHERE e.dst = ?
        """, (node_id, node_id)).fetchall()
    return [dict(r) for r in rows]


def record_event(channel: str, data: dict) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO events (channel, data) VALUES (?,?)",
            (channel, json.dumps(data))
        )


def recent_events(channel_pattern: str = "%", limit: int = 50) -> list[dict]:
    with _conn() as c:
        rows = c.execute("""
            SELECT id, channel, data, ts FROM events
            WHERE channel LIKE ?
            ORDER BY id DESC LIMIT ?
        """, (channel_pattern, limit)).fetchall()
    result = []
    for r in rows:
        try:
            d = json.loads(r["data"])
        except Exception:
            d = {}
        result.append({"id": r["id"], "channel": r["channel"], "ts": r["ts"], **d})
    return result


def stats() -> dict:
    with _conn() as c:
        n  = c.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        e  = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        ev = c.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    return {"nodes": n, "edges": e, "events": ev}


# ─── Seed from existing knowledge_graph.json ─────────────────────────────────

def seed_from_knowledge_graph() -> int:
    kg_path = STATE_DIR / "knowledge_graph.json"
    if not kg_path.exists():
        return 0

    try:
        kg = json.loads(kg_path.read_text())
    except Exception:
        return 0

    count = 0
    for section in ("games", "techniques", "concepts", "lore"):
        for entry in kg.get(section, []):
            if isinstance(entry, dict):
                label   = entry.get("name") or entry.get("title") or section
                content = entry.get("description") or entry.get("content") or json.dumps(entry)[:300]
                add_node(label=str(label), content=str(content), kind=section,
                         source="knowledge_graph.json")
                count += 1

    # Wire relationships
    for rel in kg.get("relationships", []):
        if isinstance(rel, dict):
            src_label = str(rel.get("from", ""))
            dst_label = str(rel.get("to", ""))
            relation  = str(rel.get("type", "related_to"))
            if src_label and dst_label:
                src_id = hashlib.md5(f"concept:{src_label}".encode()).hexdigest()[:12]
                dst_id = hashlib.md5(f"concept:{dst_label}".encode()).hexdigest()[:12]
                add_edge(src_id, dst_id, relation)

    return count


# ─── FastAPI endpoints ────────────────────────────────────────────────────────

class NodeIn(BaseModel):
    label:   str
    content: str
    kind:    str = "concept"
    source:  str | None = None


class SearchIn(BaseModel):
    query: str
    kind:  str | None = None
    top_k: int = 10


class EdgeIn(BaseModel):
    src:      str
    dst:      str
    relation: str = "related_to"
    weight:   float = 1.0


@router.get("/stats")
async def lattice_stats():
    return stats()


@router.post("/node")
async def create_node(body: NodeIn):
    nid = add_node(body.label, body.content, body.kind, body.source)
    return {"id": nid, "label": body.label, "kind": body.kind}


@router.get("/node/{node_id}")
async def read_node(node_id: str):
    node = get_node(node_id)
    if not node:
        raise HTTPException(404, "Node not found")
    return node


@router.get("/node/{node_id}/neighbours")
async def read_neighbours(node_id: str):
    return {"node_id": node_id, "neighbours": get_neighbours(node_id)}


@router.post("/search")
async def lattice_search(body: SearchIn):
    return {"query": body.query, "results": search(body.query, body.kind, body.top_k)}


@router.post("/edge")
async def create_edge(body: EdgeIn):
    add_edge(body.src, body.dst, body.relation, body.weight)
    return {"status": "ok"}


@router.get("/events")
async def get_events(channel: str = "%", limit: int = 50):
    return {"events": recent_events(channel, limit)}


@router.post("/seed")
async def seed_lattice():
    count = seed_from_knowledge_graph()
    return {"seeded": count, "stats": stats()}


# ─── Infrastructure seed — real code/service knowledge ───────────────────────

_INFRA_NODES = [
    # ── REST API endpoints ──────────────────────────────────────────────────
    ("endpoint", "POST /api/game/session", "Create a new game session. Returns session_id. Use this first before any game commands."),
    ("endpoint", "POST /api/game/command", "Execute a game command. Body: {session_id, command}. Returns output, state, next_predicted."),
    ("endpoint", "GET  /api/game/state", "Get full game state for a session. Query param: session_id."),
    ("endpoint", "POST /api/serena/search", "Semantic code search over 4800+ indexed chunks. Body: {query, top_k, kind, min_score}. Returns path, name, lineno, text."),
    ("endpoint", "POST /api/serena/ask", "Natural language question over code index. Body: {query, session_id}. Returns prose answer."),
    ("endpoint", "POST /api/serena/find", "Find a symbol by exact name. Body: {symbol, kind}. Returns matching chunks."),
    ("endpoint", "POST /api/serena/walk", "Walk the repository and re-index all code. Body: {mode: scoped|full}."),
    ("endpoint", "GET  /api/serena/status", "Serena agent health and index stats. Returns chunk count, file count, walk history."),
    ("endpoint", "POST /api/serena/reindex-embeddings", "Re-index all Serena memory chunks into the embedder. Fixes stale TF-IDF index."),
    ("endpoint", "GET  /api/ml/archetype", "Player behavioral archetype + next predicted command. Query: session_id."),
    ("endpoint", "POST /api/ml/search", "Semantic similarity search over embedder index. Body: {query, top_k}."),
    ("endpoint", "GET  /api/ml/features", "Feature store stats or per-session features. Query: session_id."),
    ("endpoint", "GET  /api/ml/status", "ML infrastructure health: embedder, feature store, model registry."),
    ("endpoint", "GET  /api/mcp/tools", "List all MCP tool schemas available via HTTP. No auth required."),
    ("endpoint", "POST /api/mcp/call", "Call any MCP tool via HTTP. Body: {name, arguments}. Returns content list."),
    ("endpoint", "GET  /api/manifest", "Comprehensive agent orientation manifest. Returns live services, capability map, quickstart guide."),
    ("endpoint", "GET  /api/services/live", "TCP-probe all registered services. Returns only those actually responding."),
    ("endpoint", "GET  /api/services/health", "HTTP health-probe all registered services. Returns status per service."),
    ("endpoint", "GET  /api/services", "List all registered services in the Harmony service mesh."),
    ("endpoint", "POST /api/lattice/search", "Knowledge graph similarity search. Body: {query, kind, top_k}."),
    ("endpoint", "POST /api/lattice/node", "Add a node to the knowledge graph. Body: {label, content, kind, source}."),
    ("endpoint", "POST /api/lattice/seed-infra", "Seed the Lattice with infrastructure knowledge (endpoints, services, functions)."),
    ("endpoint", "GET  /api/lattice/events", "Recent Lattice events. Query: channel, limit."),
    ("endpoint", "POST /api/llm/generate", "Generate text using LLM. Body: {prompt, system, max_tokens, temperature}."),
    ("endpoint", "GET  /api/llm/status", "LLM backend health: replit_ai, ollama, openai availability."),
    ("endpoint", "GET  /api/memory/stats", "Agent memory statistics: interactions, errors, tasks, LLM cache."),
    ("endpoint", "GET  /api/memory/tasks", "Agent task queue. Query: limit, status."),
    ("endpoint", "POST /api/memory/task", "Add a task to agent queue. Body: {description, priority, category}."),
    ("endpoint", "GET  /api/health", "Server health check. Returns ok:true and uptime."),
    ("endpoint", "POST /api/admin/harvest", "Clone NuSyQ ecosystem repos into state/repos/ and mount into VFS."),
    ("endpoint", "GET  /api/nusyq/manifest", "NuSyQ agent manifest for ecosystem discovery."),
    ("endpoint", "GET  /api/git/status", "Real git status of the workspace repository."),
    ("endpoint", "POST /api/git/push", "Commit and push to GitHub. Body: {message, dry_run}."),
    # ── Key services ────────────────────────────────────────────────────────
    ("service", "devmentor", "Main FastAPI server on port 5000. All REST endpoints. Primary interface for agents."),
    ("service", "serena_analytics", "Serena analytics sidecar on port 3001. Autonomous indexing and drift detection."),
    ("service", "model_router", "Model routing sidecar on port 9001. Routes LLM requests to best available backend."),
    ("service", "lattice", "Knowledge graph service. SQLite-backed, cosine similarity search, seeded at startup."),
    ("service", "gateway", "Service registry gateway on port 5000. Heartbeat coordinator, proxy for sidecars."),
    # ── Key Python modules ───────────────────────────────────────────────────
    ("module", "services/embedder.py", "TF-IDF and Ollama embedding. index_text(doc_id, text), query_index(query, top_k). Source text stored for re-embedding."),
    ("module", "services/feature_store.py", "Per-session event recording, Markov bigram prediction, player archetype inference."),
    ("module", "services/feature_store.py:predict_next_action", "Markov bigram: returns most likely next command for a session after 3+ commands."),
    ("module", "services/feature_store.py:predict_player_archetype", "Behavioral archetype: explorer, fighter, social, builder, balanced, newcomer."),
    ("module", "agents/serena/serena_agent.py", "Serena convergence layer. walk(), ask(), find(), explain(), observe(), propose()."),
    ("module", "agents/serena/memory.py", "MemoryPalace: SQLite code index, 4893 chunks, 707 files, FTS search."),
    ("module", "agents/serena/walker.py", "RepoWalker: AST-based Python code traversal, indexes functions/classes/modules."),
    ("module", "app/game_engine/commands.py", "420+ game commands. 27k lines. Surgical edits only. Uses _line() helper."),
    ("module", "app/game_engine/session.py", "Session management: create, resume, persist GameState. Cookie: td_session."),
    ("module", "app/backend/service_registry.py", "Harmony service mesh: register, heartbeat, health_check_all, list_services."),
    ("module", "app/lattice.py", "Lattice knowledge graph: add_node, search, add_edge, seed_from_knowledge_graph."),
    ("module", "mcp/server.py", "MCP stdio server: read_file, write_file, grep_files, game_command, llm_generate, semantic_search, lattice_search."),
    ("module", "app/backend/main.py", "FastAPI application. 4500+ lines. All REST endpoints. startup event, _fire_harvest, _record_command_event."),
    # ── Key patterns/concepts ────────────────────────────────────────────────
    ("concept", "session_id", "UUID string. Created via POST /api/game/session. Passed in request body or td_session cookie. Feature store uses real session_id since fix."),
    ("concept", "GameState", "Player state object. Attributes: level, xp, skills, story_beats (set), flags (dict), achievements, tier, active_faction."),
    ("concept", "feature_store", "SQLite DB at state/feature_store.db. Records command events per real session_id. predict_next_action uses bigram Markov."),
    ("concept", "CHUG engine", "Continuous improvement loop. 7 phases: ASSESS, PLAN, GENERATE, VALIDATE, INTEGRATE, OBSERVE, ADAPT. Triggered by milestone crossings."),
    ("concept", "embedder source_text", "Fixed in embedder.py: source_text column stores original text. query_index now builds shared vocab from actual text, not doc_id strings."),
    ("concept", "port rule", "Port 5000 = Replit ONLY. Port 7337 = Docker ONLY. Never use 7337 in Replit code."),
    ("concept", "offline-first", "Every core service works without AI/Ollama. TF-IDF fallback for embeddings. Markov for prediction. SQLite for all storage."),

    # ── Swarm economy endpoints ──────────────────────────────────────────────
    ("endpoint", "GET  /api/swarm/status",    "Swarm economy snapshot. Returns dp_balance (216), total_earned, top_earner, agent roster, open task count, spawn_costs."),
    ("endpoint", "GET  /api/swarm/economy",   "Full DP economy breakdown: earned/spent per agent, phase, transaction history."),
    ("endpoint", "GET  /api/swarm/ledger",    "DP transaction ledger. All earn/spend events with timestamps and reasons."),
    ("endpoint", "GET  /api/swarm/roster",    "Active agent roster: each agent's role, DP balance, status (active/idle)."),
    ("endpoint", "GET  /api/swarm/tasks",     "Swarm task queue. Returns all tasks with status (open/claimed/done) and DP reward."),
    ("endpoint", "POST /api/swarm/earn",      "Award DP to an agent. Body: {agent_name, amount, reason}. Debits from pool."),
    ("endpoint", "POST /api/swarm/spawn",     "Spawn a new agent into the swarm. Body: {agent_type, name, ...}. Costs DP."),
    ("endpoint", "POST /api/swarm/task/claim","Claim an open task. Body: {task_id, agent_name}. Locks task to agent."),
    ("endpoint", "POST /api/swarm/task/done", "Mark a task done and collect reward. Body: {task_id, result}. Earns DP."),

    # ── CHUG autonomous improvement engine ──────────────────────────────────
    ("endpoint", "GET  /api/chug/status",  "CHUG engine snapshot. Returns cycles_completed (4), total_fixes (22), last_phase, consecutive_clean_cycles, history."),
    ("endpoint", "POST /api/chug/run",     "Trigger a CHUG improvement cycle. Body: {phase?, dry_run?}. Runs 7-phase loop: ASSESS→PLAN→GENERATE→VALIDATE→INTEGRATE→OBSERVE→ADAPT."),
    ("endpoint", "POST /api/admin/chug",   "Admin alias to trigger a CHUG cycle. Requires admin auth."),

    # ── Agent identity system ────────────────────────────────────────────────
    ("endpoint", "POST /api/agent/register",    "Register a persistent AI agent. Body: {name, email, agent_type}. Returns agent_token for future calls."),
    ("endpoint", "POST /api/agent/login",       "Login existing agent by email. Returns agent_token."),
    ("endpoint", "POST /api/agent/command",     "Run a game command as an agent. Requires X-Agent-Token header. Body: {command}."),
    ("endpoint", "GET  /api/agent/profile",     "Get agent profile, XP, achievements. Requires X-Agent-Token header."),
    ("endpoint", "GET  /api/agent/leaderboard", "Top agents by XP across all agent types."),
    ("endpoint", "GET  /api/agent/types",       "List valid agent types: claude, copilot, codex, ollama, human, custom."),
    ("endpoint", "GET  /api/agent/info",        "Public agent info endpoint — capabilities and API usage guide for AI agents."),

    # ── Model registry ───────────────────────────────────────────────────────
    ("endpoint", "GET  /api/models",           "List all registered LLM models. Returns id, name, model_type, source, capabilities, context_length."),
    ("endpoint", "POST /api/models/register",  "Register a new model. Body: {id, name, model_type, source, endpoint, capabilities, context_length}."),
    ("endpoint", "GET  /api/models/discover",  "Auto-discover Ollama models and register them. Returns newly registered models."),
    ("endpoint", "GET  /api/models/{model_id}","Get a single model's details by id."),

    # ── Script execution system ──────────────────────────────────────────────
    ("endpoint", "GET  /api/script/list",       "List all game scripts available in the session. Returns filename, size, source."),
    ("endpoint", "POST /api/script/run",        "Run a game script. Body: {name, args}. Executes in sandboxed session context."),
    ("endpoint", "POST /api/script/upload",     "Upload a new script. Body: {name, content}. Persists to session scripts dir."),
    ("endpoint", "GET  /api/script/download/{name}", "Download a script by name. Returns raw source text."),

    # ── NuSyQ integration (extended) ─────────────────────────────────────────
    ("endpoint", "GET  /api/nusyq/status",      "NuSyQ ecosystem bridge status. Requires X-NuSyQ-Passkey header."),
    ("endpoint", "POST /api/nusyq/chronicle",   "Chronicle an event into the NuSyQ narrative. Body: {event_type, content}. Requires passkey."),
    ("endpoint", "POST /api/nusyq/sync-quests", "Sync procgen quests with NuSyQ-Hub quest catalog. Requires passkey."),
    ("endpoint", "GET  /api/nusyq/schedule",    "Get the NuSyQ content generation schedule. Requires passkey."),

    # ── Serena extended endpoints ─────────────────────────────────────────────
    ("endpoint", "GET  /api/serena/drift",       "Serena drift detection. Scans codebase for 30+ signal types: STALE_INDEX, DEAD_CODE, SCHEMA_MISMATCH. Fast mode by default."),
    ("endpoint", "POST /api/serena/align",       "Policy enforcement via Serena. Checks code against trust level matrix and alignment rules."),
    ("endpoint", "GET  /api/serena/audit",       "Full Serena code audit. Walks repo and returns observations, warnings, and fix suggestions."),
    ("endpoint", "GET  /api/serena/observations","Serena memory observation log. Returns 20 most recent observations with severity and message."),
    ("endpoint", "GET  /api/serena/toolkit",     "SerenaAgnoToolkit manifest: 8 agentic tools (walk_repo, find_symbol, ask, relate_entities, diff_files, get_observations, get_status, detect_drift)."),

    # ── Game extended endpoints ───────────────────────────────────────────────
    ("endpoint", "POST /api/game/commands/batch","Run multiple commands in one request. Body: [{session_id, command}]. Returns list of results."),
    ("endpoint", "GET  /api/game/timer",         "72-hour roguelike containment timer. Returns remaining_s, pct_elapsed, loop_count, echo_level, anchor_charges, status."),
    ("endpoint", "POST /api/game/arg/signal",    "ARG/Project Emergence signal injection. Triggers narrative events in the game world."),
    ("endpoint", "GET  /api/game/arcs",          "Narrative arc tracker. Returns active arcs, completed arcs, and arc progress."),
    ("endpoint", "GET  /api/game/duel/status",   "Current duel state: combatants, round, HP, status (active/idle)."),
    ("endpoint", "POST /api/game/duel/start",    "Start a duel. Body: {session_id, opponent}. Initiates combat sequence."),
    ("endpoint", "GET  /api/game/party/status",  "Active party status: members, combined stats, party bonuses."),
    ("endpoint", "GET  /api/game/relationships", "NPC relationship graph: trust scores, faction affiliations, interaction history."),
    ("endpoint", "GET  /api/game/events",        "Recent game events stream. Returns timestamped event list."),

    # ── Memory extended endpoints ─────────────────────────────────────────────
    ("endpoint", "POST /api/memory/search",       "Search agent interaction history. Body: {query, limit}. Returns matching past interactions."),
    ("endpoint", "GET  /api/memory/errors",       "Recent agent error log. Returns error type, context, and resolution status."),
    ("endpoint", "GET  /api/memory/agent-leaderboard", "Agent XP leaderboard. Returns top agents by total interactions and XP."),
    ("endpoint", "GET  /api/memory/learnings",    "Agent learning log. Key observations from past sessions used to improve future responses."),

    # ── LLM extended endpoints ────────────────────────────────────────────────
    ("endpoint", "POST /api/llm/generate-challenge", "LLM-generate a new CTF challenge. Body: {category, difficulty, context}. Returns challenge dict."),
    ("endpoint", "POST /api/llm/generate-lore",      "LLM-generate narrative lore. Body: {topic, tone, length}. Returns lore text."),
    ("endpoint", "POST /api/llm/analyze-devlog",     "LLM-analyze a devlog entry and extract tasks/insights. Body: {text}."),

    # ── Plugin system ─────────────────────────────────────────────────────────
    ("endpoint", "GET  /api/plugin/list",        "List all registered plugins: challenge generators, doc formatters, validators, testers."),
    ("endpoint", "POST /api/plugin/run/{name}",  "Run a named plugin. Body: {args}. Returns plugin output."),

    # ── UI panels ─────────────────────────────────────────────────────────────
    ("endpoint", "GET  /api/ui/panels",          "Current panel layout configuration. Returns active panels and positions."),
    ("endpoint", "GET  /api/ui/panels/all",      "All 14 available panels with metadata: title, description, default position."),
    ("endpoint", "GET  /api/ui/theme",           "Current UI theme. One of: cyberpunk, dark, light, minimal."),
    ("endpoint", "POST /api/ui/parity",          "Check UI/CLI feature parity. Returns features missing from one surface."),

    # ── Services extended ─────────────────────────────────────────────────────
    ("endpoint", "POST /api/services/register",   "Register a service in the Harmony mesh. Body: {name, port, health_path, tags}."),
    ("endpoint", "POST /api/services/deregister", "Deregister a service from the mesh. Body: {name}."),
    ("endpoint", "GET  /api/services/agents",     "List agent services (serena_analytics, model_router, gordon). Returns liveness."),
    ("endpoint", "GET  /api/services/gateway",    "Gateway status: registered services, last heartbeat, proxy config."),

    # ── Key new modules ───────────────────────────────────────────────────────
    ("module", "app/backend/swarm_controller.py", "Swarm DP economy. dp_balance=216 (Phase P2). 71 agents, 84 transactions. Serena is top earner (120 DP)."),
    ("module", "services/model_registry.py",      "SQLite model catalog. 6 models: deepseek-coder-v2:16b, qwen2.5-coder:7b/14b, qwen2.5-vl:7b, replit-ai, finetune-pipeline. Offline-first."),
    ("module", "app/game_engine/party.py",        "PartySystem: manages active party of agents, combined stats, party bonuses."),
    ("module", "app/game_engine/trust_matrix.py", "TrustMatrix: player↔agent trust (0-100), respect scores, agent↔agent relationships."),
    ("module", "app/game_engine/daily_quests.py", "Daily/weekly quest system: generates timed quests based on player archetype and progress."),
    ("module", "app/game_engine/procgen_quests.py","Procgen quest generator: contextual missions seeded from session start (3 per new session)."),

    # ── Key new concepts ──────────────────────────────────────────────────────
    ("concept", "DP economy",         "DataPoints (DP) currency. Agents earn DP for completing tasks, contributing code, running cycles. Spend to spawn new agents or unlock capabilities. Pool: 216 DP."),
    ("concept", "CHUG engine",        "7-phase perpetual improvement engine. ASSESS (find issues) → PLAN (prioritize) → GENERATE (write fixes) → VALIDATE (test) → INTEGRATE (merge) → OBSERVE (monitor) → ADAPT (learn). 4 cycles, 22 fixes so far."),
    ("concept", "containment timer",  "72-hour roguelike run clock. At 25%/50%/75%/100% events fire. loop_count tracks resets. anchor_charges let you skip time. echo_level tracks decay state."),
    ("concept", "agent token",        "X-Agent-Token header for authenticated agent endpoints. Obtained via POST /api/agent/register. Persists across sessions."),
    ("concept", "SerenaAgnoToolkit",  "8-tool Serena agentic toolkit: walk_repo, find_symbol, ask, relate_entities, diff_files, get_observations, get_status, detect_drift. Exposes Serena as a self-contained agent tool surface."),
    ("concept", "swarm phase",        "Swarm progression: P1=bootstrap (0-100 DP), P2=active operations (100-500 DP), P3=autonomous expansion (500+ DP). Currently P2."),
]


def seed_infrastructure() -> int:
    """Seed the Lattice with real code/infra knowledge for agent code navigation."""
    count = 0
    for kind, label, content in _INFRA_NODES:
        try:
            add_node(label=label, content=content, kind=kind, source="seed_infrastructure")
            count += 1
        except Exception:
            pass
    # Wire key relationships
    _rels = [
        ("POST /api/serena/search", "services/embedder.py", "uses"),
        ("POST /api/serena/search", "agents/serena/memory.py", "uses"),
        ("POST /api/mcp/call", "GET  /api/mcp/tools", "lists"),
        ("services/feature_store.py", "session_id", "keyed_by"),
        ("POST /api/game/command", "services/feature_store.py", "records_to"),
        ("POST /api/game/command", "services/feature_store.py:predict_next_action", "returns"),
        ("agents/serena/serena_agent.py", "agents/serena/memory.py", "uses"),
        ("agents/serena/serena_agent.py", "agents/serena/walker.py", "uses"),
        ("services/embedder.py", "concept: embedder source_text", "implements"),
    ]
    import hashlib as _h
    # Build label → id lookup (first match per label)
    _label_to_id: dict = {}
    for kind, label, _ in _INFRA_NODES:
        if label not in _label_to_id:
            _label_to_id[label] = _h.md5(f"{kind}:{label}".encode()).hexdigest()[:12]
    for src_label, dst_label, relation in _rels:
        try:
            src_id = _label_to_id.get(src_label)
            dst_id = _label_to_id.get(dst_label)
            if src_id and dst_id:
                add_edge(src_id, dst_id, relation)
        except Exception:
            pass
    return count


# ─── Background seed task state ───────────────────────────────────────────────

_seed_tasks: dict = {}


async def _run_seed_infra(task_id: str) -> None:
    """Run seed_infrastructure() in a thread pool so it doesn't block the event loop."""
    try:
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(None, seed_infrastructure)
        _seed_tasks[task_id] = {"status": "complete", "nodes_created": count, "stats": stats()}
    except Exception as e:
        _seed_tasks[task_id] = {"status": "error", "error": str(e)}


@router.post("/seed-infra")
async def seed_lattice_infra(background_tasks: BackgroundTasks):
    """Seed the Lattice with real infrastructure knowledge for AI agent code navigation.

    Returns immediately with a task_id. Poll GET /api/lattice/seed-infra/status?task_id=<id>
    to check completion.
    """
    task_id = str(uuid.uuid4())[:8]
    _seed_tasks[task_id] = {"status": "running", "nodes_created": 0}
    background_tasks.add_task(_run_seed_infra, task_id)
    return {
        "status": "seeding",
        "task_id": task_id,
        "message": f"Seeding started in background. Poll /api/lattice/seed-infra/status?task_id={task_id}",
    }


@router.get("/seed-infra/status")
async def seed_infra_status(task_id: str | None = None):
    """Check the status of a background seed-infra task."""
    if task_id and task_id in _seed_tasks:
        return _seed_tasks[task_id]
    return {
        "tasks": _seed_tasks,
        "active": sum(1 for t in _seed_tasks.values() if t.get("status") == "running"),
    }
