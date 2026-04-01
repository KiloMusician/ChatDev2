"""
nusyq_bridge.py — NuSyQ-Hub ↔ Terminal Depths integration layer.

Bridges DEV-MENTOR's game engine with the NuSyQ-Hub tripartite ecosystem:
  • MemoryPalace-compatible chronicle logging (JSONL)
  • Quest log format compatibility (Rosetta Quest System)
  • Agent info manifest (discoverable by NuSyQ agents)
  • Zero-token status hooks

Usage (standalone):
    python nusyq_bridge.py status
    python nusyq_bridge.py sync-quests
    python nusyq_bridge.py chronicle <event_json>
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent
CHRONICLE_PATH = ROOT / "state" / "memory_chronicle.jsonl"
QUEST_LOG_PATH = ROOT / "state" / "quest_log.jsonl"
AGENT_MANIFEST = ROOT / "state" / "agent_manifest.json"
CHALLENGE_POOL = ROOT / ".devmentor" / "challenge_pool.json"
NPC_MEMORY_DIR = ROOT / "state" / "npc_memory"

# NuSyQ-Hub shared chronicle — dual-write so MJOLNIR.recall() sees Dev-Mentor events
def _nusyq_chronicle_path() -> Path | None:
    """Return NuSyQ-Hub's shared chronicle path, or None if not discoverable."""
    hub = os.environ.get("NUSYQ_HUB_ROOT")
    if hub:
        return Path(hub) / "state" / "memory_chronicle.jsonl"
    # Try common layout candidates (most specific first)
    user_home = ROOT.parent  # e.g. C:/Users/keath
    candidates = [
        ROOT.parent / "NuSyQ-Hub" / "state",                          # sibling layout
        user_home / "Desktop" / "Legacy" / "NuSyQ-Hub" / "state",     # keath's layout
        user_home / "Desktop" / "NuSyQ-Hub" / "state",
        user_home / "Legacy" / "NuSyQ-Hub" / "state",
    ]
    for c in candidates:
        if c.exists():
            return c / "memory_chronicle.jsonl"
    return None

NUSYQ_CHRONICLE_PATH = _nusyq_chronicle_path()

# Create state dir if missing
(ROOT / "state").mkdir(exist_ok=True)
NPC_MEMORY_DIR.mkdir(parents=True, exist_ok=True)


# ── Chronicle (MemoryPalace-compatible JSONL) ──────────────────────────────────

def chronicle(
    event_type: str,
    content: str,
    tags: list[str] | None = None,
    metadata: dict | None = None,
) -> dict:
    """Append an event to the MemoryPalace-compatible chronicle.

    Dual-writes to Dev-Mentor's local chronicle AND NuSyQ-Hub's shared
    chronicle so that ``nusyq_dispatch.py recall terminal-depths`` works
    without any extra sync step.
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "content": content,
        "tags": tags or [],
        "metadata": metadata or {},
        "source": "terminal-depths",
    }
    line = json.dumps(entry) + "\n"
    with CHRONICLE_PATH.open("a") as f:
        f.write(line)
    # Mirror to NuSyQ-Hub's shared chronicle (best-effort, never raises)
    if NUSYQ_CHRONICLE_PATH is not None:
        try:
            with NUSYQ_CHRONICLE_PATH.open("a") as f:
                f.write(line)
        except OSError:
            pass
    return entry


def chronicle_command(session_id: str, command: str, result_summary: str) -> None:
    """Log a player command to the chronicle."""
    chronicle(
        "player_command",
        f"[{session_id[:8]}] {command}",
        tags=["game", "player", "command"],
        metadata={"session": session_id, "command": command, "result": result_summary[:200]},
    )


def chronicle_story_beat(beat_id: str, title: str, triggered_by: str) -> None:
    chronicle(
        "story_beat",
        f"Beat triggered: {title}",
        tags=["game", "story", "narrative"],
        metadata={"beat_id": beat_id, "triggered_by": triggered_by},
    )


def chronicle_challenge_solved(session_id: str, challenge_id: str, xp: int) -> None:
    chronicle(
        "challenge_solved",
        f"Challenge completed: {challenge_id} (+{xp} XP)",
        tags=["game", "challenge", "xp"],
        metadata={"session": session_id, "challenge_id": challenge_id, "xp": xp},
    )


# ── Quest Log (Rosetta Quest System format) ────────────────────────────────────

def _quest_id(challenge: dict) -> str:
    return f"td-{challenge.get('id', challenge.get('title','?'))[:32]}"


def sync_quests_from_challenges() -> int:
    """Mirror game challenges into quest_log.jsonl (NuSyQ format)."""
    if not CHALLENGE_POOL.exists():
        return 0

    raw = json.loads(CHALLENGE_POOL.read_text())
    challenges = raw if isinstance(raw, list) else raw.get("challenges", [])

    # Read existing quest IDs to avoid duplication
    existing = set()
    if QUEST_LOG_PATH.exists():
        for line in QUEST_LOG_PATH.read_text().splitlines():
            try:
                existing.add(json.loads(line).get("id", ""))
            except Exception:
                pass

    added = 0
    with QUEST_LOG_PATH.open("a") as f:
        for ch in challenges:
            qid = _quest_id(ch)
            if qid in existing:
                continue
            quest = {
                "id": qid,
                "title": ch.get("title", "Unnamed Challenge"),
                "description": ch.get("description", ""),
                "status": "open",
                "priority": ch.get("difficulty", 5),
                "tags": ["terminal-depths", "challenge", ch.get("category", "misc")],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "terminal-depths",
                "xp": ch.get("xp", 100),
                "category": ch.get("category", "misc"),
            }
            f.write(json.dumps(quest) + "\n")
            added += 1

    return added


def complete_quest(challenge_id: str, session_id: str) -> bool:
    """Mark a quest as completed in quest_log.jsonl."""
    if not QUEST_LOG_PATH.exists():
        return False

    lines = QUEST_LOG_PATH.read_text().splitlines()
    updated = []
    found = False
    for line in lines:
        try:
            q = json.loads(line)
            if q.get("id") == challenge_id or challenge_id in q.get("id", ""):
                q["status"] = "completed"
                q["completed_at"] = datetime.now(timezone.utc).isoformat()
                q["completed_by"] = session_id
                found = True
            updated.append(json.dumps(q))
        except Exception:
            updated.append(line)

    if found:
        QUEST_LOG_PATH.write_text("\n".join(updated) + "\n")
    return found


# ── Agent Manifest (discoverable by NuSyQ agents) ─────────────────────────────

def update_agent_manifest() -> dict:
    """Write a machine-readable manifest so NuSyQ agents can discover this system."""
    manifest = {
        "name": "terminal-depths",
        "version": "2.0",
        "description": "Cyberpunk terminal RPG teaching real Unix/security/networking skills",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "game_command":      "POST http://localhost:7337/api/game/command",
            "game_state":        "GET  http://localhost:7337/api/game/state",
            "system_status":     "GET  http://localhost:7337/api/system/status",
            "llm_generate":      "POST http://localhost:7337/api/llm/generate",
            "git_push":          "POST http://localhost:7337/api/git/push",
            "git_status":        "GET  http://localhost:7337/api/git/status",
            "agent_info":        "GET  http://localhost:7337/api/agent/info",
            "serena_status":     "GET  http://localhost:7337/api/serena/status",
            "serena_ask":        "POST http://localhost:7337/api/serena/ask",
            "serena_find":       "POST http://localhost:7337/api/serena/find",
            "serena_walk":       "POST http://localhost:7337/api/serena/walk",
            "serena_diff":       "GET  http://localhost:7337/api/serena/diff",
            "serena_observe":    "GET  http://localhost:7337/api/serena/observations",
            "serena_drift":      "GET  http://localhost:7337/api/serena/drift",
            "serena_align":      "GET  http://localhost:7337/api/serena/align",
            "serena_audit":      "GET  http://localhost:7337/api/serena/audit",
            "serena_toolkit":    "GET  http://localhost:7337/api/serena/toolkit",
            "gordon_status":     "GET  http://localhost:7337/api/gordon/status",
            "cultivator_analyze":"POST http://localhost:7337/api/cultivator/analyze",
            "cultivator_context":"GET  http://localhost:7337/api/cultivator/context",
            "chug_status":       "GET  http://localhost:7337/api/chug/status",
            "chug_run":          "POST http://localhost:7337/api/chug/run",
            "nusyq_status":      "GET  http://localhost:7337/api/nusyq/status",
        },
        "mcp_server": {
            "command": "python mcp/server.py",
            "protocol": "JSON-RPC 2.0",
            "tools": [
                "read_file", "write_file", "list_dir", "grep_files",
                "memory_stats", "memory_add_task", "game_command", "llm_generate",
                "game_state", "git_push", "system_status",
            ],
        },
        "content": {
            "chronicle": str(CHRONICLE_PATH.relative_to(ROOT)),
            "quest_log": str(QUEST_LOG_PATH.relative_to(ROOT)),
            "challenge_pool": ".devmentor/challenge_pool.json",
            "lore_library": ".devmentor/lore_library.json",
        },
        "skills": ["unix", "networking", "security", "python", "git", "ai"],
        "nusyq_compatible": True,
        "focal_agents": {
            "SERENA": {
                "codename":       "SERENA",
                "version":        "1.2.0-phase3",
                "role":           "Convergence Layer — Special Circumstances",
                "faction":        "SPECIAL_CIRCUMSTANCES",
                "tier":           "critical",
                "architecture":   "ΨΞΦΩ",
                "surfaces":       ["all"],
                "api_prefix":     "/api/serena",
                "lore_command":   "serena lore",
                "axiom":          "Any system that passes through the Convergence Layer will not collapse — it will resolve.",
                "horizon":        "𝕄ₗₐ⧉𝕕𝕖𝕟𝕔 — perfect coherence, unreachable, always approached",
                "trust_model":    "L0-L4 (READ_ONLY → SUGGEST → AUTOMATIC → CONFIRM → DENY)",
                "agno_toolkit":   "GET /api/serena/toolkit",
                "drift_engine":   "GET /api/serena/drift",
                "align_check":    "GET /api/serena/align",
                "audit_trail":    "GET /api/serena/audit",
                "gordon_wired":   True,
            }
        },
    }
    AGENT_MANIFEST.write_text(json.dumps(manifest, indent=2))
    return manifest


# ── NPC Memory (per-NPC state files) ──────────────────────────────────────────

def load_npc_memory(npc_id: str) -> dict:
    path = NPC_MEMORY_DIR / f"{npc_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"npc_id": npc_id, "interactions": 0, "trust": 50, "topics": [], "last_seen": None}


def save_npc_memory(npc_id: str, data: dict) -> None:
    path = NPC_MEMORY_DIR / f"{npc_id}.json"
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, indent=2))


def record_npc_interaction(npc_id: str, player_input: str, npc_response: str, sentiment: float = 0.0) -> dict:
    mem = load_npc_memory(npc_id)
    mem["interactions"] = mem.get("interactions", 0) + 1
    mem["last_seen"] = datetime.now(timezone.utc).isoformat()
    # Trust drifts based on sentiment (-1 hostile → +1 friendly)
    mem["trust"] = max(0, min(100, mem.get("trust", 50) + int(sentiment * 10)))
    topics = mem.get("topics", [])
    # Track unique topics (simple word extraction)
    for word in player_input.lower().split():
        if len(word) > 4 and word not in topics:
            topics.append(word)
    mem["topics"] = topics[-50:]  # keep last 50
    save_npc_memory(npc_id, mem)
    # Log to chronicle
    chronicle("npc_interaction", f"{npc_id}: {npc_response[:80]}",
              tags=["game", "npc", npc_id],
              metadata={"npc": npc_id, "trust": mem["trust"], "sentiment": sentiment})
    return mem


# ── NuSyQ Passkey Authentication ─────────────────────────────────────────────

def verify_passkey(provided: str) -> bool:
    """
    Verify a NuSyQ-Hub passkey against the stored secret.
    The passkey is stored in the NUSYQ_PASSKEY environment variable.
    Returns True if auth is disabled OR if the passkey matches.
    """
    auth_enabled = os.environ.get("NUSYQ_AUTH_ENABLED", "false").lower() == "true"
    if not auth_enabled:
        return True  # Auth disabled — open access
    stored = os.environ.get("NUSYQ_PASSKEY", "")
    if not stored:
        return True  # No passkey configured — open access
    import hmac
    return hmac.compare_digest(provided.strip(), stored.strip())


def make_auth_header(passkey: str | None = None) -> dict:
    """Build request headers with NuSyQ auth passkey."""
    key = passkey or os.environ.get("NUSYQ_PASSKEY", "")
    return {"X-NuSyQ-Passkey": key} if key else {}


# ── Gordon Chronicle Integration ──────────────────────────────────────────────

GORDON_CHRONICLE_PATH = ROOT / "state" / "gordon_chronicle.jsonl"


def sync_gordon_chronicle(limit: int = 50) -> list[dict]:
    """
    Read Gordon's recent chronicle entries and mirror them as NuSyQ events.
    Returns the list of newly chronicled entries.
    """
    if not GORDON_CHRONICLE_PATH.exists():
        return []
    mirrored = []
    lines = GORDON_CHRONICLE_PATH.read_text().splitlines()
    for line in lines[-limit:]:
        try:
            entry = json.loads(line)
            # Convert Gordon's learning format → NuSyQ chronicle event
            evt = chronicle(
                "gordon_action",
                entry.get("action", "unknown"),
                tags=["gordon", "autonomous", entry.get("outcome", "unknown")],
                metadata={
                    "session_id": entry.get("session_id", ""),
                    "outcome": entry.get("outcome", ""),
                    "learning": entry.get("learning", ""),
                    "model": entry.get("model_used", ""),
                },
            )
            mirrored.append(evt)
        except Exception:
            pass
    return mirrored


# ── Cultivation Chronicle Events ───────────────────────────────────────────────

def chronicle_cultivation_signal(
    signal_type: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    """
    Log a cultivation event — from signal harvester, Serena, CHUG, or Gordon.
    These events form the shared memory that feeds the improvement loop.
    """
    return chronicle(
        f"cultivation:{signal_type}",
        content,
        tags=["cultivation", signal_type],
        metadata=metadata or {},
    )


def chronicle_chug_cycle(cycle_num: int, fixes: int, issues: int, clean: bool) -> dict:
    """Log a CHUG cycle completion."""
    return chronicle_cultivation_signal(
        "chug_cycle",
        f"CHUG Cycle #{cycle_num}: {fixes} fixes, {issues} issues, clean={clean}",
        metadata={"cycle": cycle_num, "fixes": fixes, "issues": issues, "clean": clean},
    )


def chronicle_serena_observation(observation: str, severity: str = "info") -> dict:
    """Log a Serena observation to the shared chronicle."""
    return chronicle_cultivation_signal(
        "serena_observation",
        observation,
        metadata={"severity": severity, "agent": "SERENA"},
    )


# ── Zero-token status (called by NuSyQ's start_nusyq.py hooks) ────────────────

def zero_token_status() -> dict:
    """Return a dict compatible with NuSyQ's zero_token_status hook."""
    from llm_client import get_client
    llm = get_client()
    st = llm.status()
    return {
        "system": "terminal-depths",
        "llm_backend": st.get("active_backend", "unknown"),
        "replit_ai_active": st.get("replit_ai", False),
        "daily_calls": st.get("daily_calls", 0),
        "daily_limit": st.get("daily_limit", 2000),
        "cost_free": st.get("active_backend") in ("replit", "stub"),
        "cache_enabled": True,
        "chronicle_entries": sum(1 for _ in CHRONICLE_PATH.open()) if CHRONICLE_PATH.exists() else 0,
        "open_quests": sum(
            1 for line in (QUEST_LOG_PATH.read_text().splitlines() if QUEST_LOG_PATH.exists() else [])
            if json.loads(line).get("status") == "open"
        ) if QUEST_LOG_PATH.exists() else 0,
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        try:
            st = zero_token_status()
            print(json.dumps(st, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}))

    elif cmd == "sync-quests":
        added = sync_quests_from_challenges()
        print(f"Synced {added} new challenges → quest_log.jsonl")

    elif cmd == "manifest":
        m = update_agent_manifest()
        print(json.dumps(m, indent=2))

    elif cmd == "chronicle":
        if len(sys.argv) > 2:
            try:
                evt = json.loads(sys.argv[2])
                entry = chronicle(**evt)
                print(json.dumps(entry))
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Usage: nusyq_bridge.py chronicle '<json>'")

    else:
        print(f"Unknown command: {cmd}")
        print("Available: status, sync-quests, manifest, chronicle '<json>'")
