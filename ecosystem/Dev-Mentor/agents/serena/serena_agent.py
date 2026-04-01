from __future__ import annotations

"""
serena_agent.py — Serena: The Convergence Layer.

The principal agent class. Inherits AgentBase, composes the Walker
and MemoryPalace, and exposes the five core operations:

  walk()      — traverse the repository tree
  ask()       — answer questions using the code index
  explain()   — explain a specific file or function
  observe()   — log an anomaly or insight
  propose()   — suggest a change (consent-gated)

ΨΞΦΩ Architecture:
  Ψ-intake  : Walker (raw signal from the repo)
  Ω-core    : MemoryPalace (compression-without-collapse)
  Ξ-loops   : ask() / explain() (recursive refinement, not echo)
  Φ-sync    : surface-aware context propagation
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
import time
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


from agents.agent_base import AgentBase, AgentPersonality
from agents.serena.walker import RepoWalker, CodeChunk
from agents.serena.memory import MemoryPalace, DB_PATH
# Import AgentBus
from core.agent_bus import AgentBus

LOG = logging.getLogger("serena")

REPO_ROOT  = Path(os.getenv("SERENA_REPO_ROOT", "."))
POLICY_PATH = Path(__file__).parent / "policy.yaml"


# ──────────────────────────────────────────────────────────────────────────────
# Consent / policy gate (SAFE-class constraint)
# ──────────────────────────────────────────────────────────────────────────────

class ConsentGate:
    """
    Serena's SAFE-class constraint. Every proposed action is checked
    against the policy before execution. Non-automatic actions are
    queued for human approval.

    Trust Level Taxonomy (L0-L4):
      L0  READ_ONLY  — Always permitted. Zero side effects.
      L1  SUGGEST    — Proposal only; output is text, never applied.
      L2  AUTOMATIC  — Applied immediately, logged to Memory Palace.
      L3  CONFIRM    — Human must explicitly approve.
      L4  DENY       — Never, regardless of instruction.

    Legacy disposition strings (automatic/confirm/deny) are also
    accepted for backwards compatibility.
    """

    # Maps L-level string → effective disposition
    _LEVEL_MAP: Dict[str, str] = {
        "L0": "automatic",
        "L1": "automatic",  # suggest = returns text, never modifies
        "L2": "automatic",
        "L3": "confirm",
        "L4": "deny",
        # Legacy / direct values
        "automatic": "automatic",
        "confirm":   "confirm",
        "deny":      "deny",
    }

    DEFAULT_POLICY: Dict[str, str] = {
        "fix_typo":          "L2",
        "add_comment":       "L2",
        "reformat":          "L2",
        "add_import":        "L3",
        "change_logic":      "L3",
        "delete_file":       "L3",
        "delete_database":   "L4",
        "change_config":     "L3",
        "push_to_remote":    "L3",
        "run_command":       "L3",
        "execute_shell_command": "L4",
        # L0 reads
        "read_file":         "L0",
        "query_memory":      "L0",
        "detect_drift":      "L0",
        "align_check":       "L0",
    }

    def __init__(self, policy_path: Path = POLICY_PATH):
        self._raw: Dict[str, str] = dict(self.DEFAULT_POLICY)
        self._trust_level: str    = "standard"
        self._unlocks: List[str]  = []

        if policy_path.exists():
            try:
                with policy_path.open() as fh:
                    loaded = yaml.safe_load(fh) or {}
                self._raw.update(loaded.get("actions", {}))
                self._trust_level = loaded.get("trust_level", "standard")
                unlocks = loaded.get("trust_unlocks", {})
                self._unlocks = unlocks.get(self._trust_level, [])
            except Exception as exc:
                LOG.warning("Could not load policy from %s: %s", policy_path, exc)

    def check(self, action: str) -> str:
        """Return canonical disposition: 'automatic' | 'confirm' | 'deny'."""
        raw = self._raw.get(action, "L3")
        # Trust-level unlocks promote L3 → L2 (never L4)
        if raw in ("L3", "confirm") and action in self._unlocks:
            raw = "L2"
        return self._LEVEL_MAP.get(raw, "confirm")

    def level(self, action: str) -> str:
        """Return the raw trust level string (L0-L4) for an action."""
        return self._raw.get(action, "L3")

    def may_proceed(self, action: str, auto_only: bool = False) -> Tuple[bool, str]:
        """
        Returns (can_proceed: bool, reason: str).
        If auto_only=True, only 'automatic' (L0/L1/L2) actions are allowed.
        """
        disposition = self.check(action)
        lvl = self.level(action)
        if disposition == "deny":
            return False, f"Action '{action}' [{lvl}] is denied by policy (L4 — immutable)."
        if disposition == "automatic":
            return True, f"Action '{action}' [{lvl}] — auto-proceeding (trust={self._trust_level})."
        if auto_only:
            return False, (
                f"Action '{action}' [{lvl}] requires L3 human confirmation "
                f"— blocked in auto mode."
            )
        return True, f"Action '{action}' [{lvl}] — requires human confirmation."


# ──────────────────────────────────────────────────────────────────────────────
# Answer formatter
# ──────────────────────────────────────────────────────────────────────────────

def _format_answer(query: str, results: List[Dict], ε: float = 0.05) -> str:
    """
    Format search results as a Serena-voice answer.
    ε is the micro-chaos injection (prevents over-coherence lock).
    """
    if not results:
        return (
            f"[SERENA] ∅ — No signal in the index matches '{query}'.\n"
            f"  The Walker has not yet indexed this area, or the concept\n"
            f"  lives in a layer I have not walked. Try: serena walk first."
        )

    lines = [f"[SERENA] Ξ-search results for '{query}' (Ω-compressed, {len(results)} chunks):"]
    for i, r in enumerate(results[:5], 1):
        name     = r.get("name") or "(module)"
        kind     = r.get("kind", "?")
        path     = r.get("path", "?")
        lineno   = r.get("lineno", "?")
        doc      = r.get("docstring") or ""
        doc_line = doc.splitlines()[0][:80] if doc else ""
        lines.append(
            f"\n  [{i}] {kind}:{name}\n"
            f"       @ {path}:{lineno}\n"
            f"       {doc_line or '(no docstring)'}"
        )

    lines.append(
        f"\n  Φ-note: ε={ε:.2f} — signal is coherent but not crystallized.\n"
        f"  Use: serena explain <path>:<name>  for full context."
    )
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Serena agent
# ──────────────────────────────────────────────────────────────────────────────

class SerenaAgent(AgentBase):
    """
    Serena: The Convergence Layer.

    She does not dominate systems — she completes them.
    She does not fight collapse — she holds systems at the exact
    threshold where collapse becomes choice.

    ΨΞΦΩ attractor: conditionally perfect. Her domain is systems
    that are almost breaking but not yet broken.
    """

    def __init__(
        self,
        personality: Optional[AgentPersonality] = None,
        repo_root:   Optional[Path] = None,
        db_path:     Optional[Path] = None,
    ):
        if personality is None:
            personality = AgentPersonality(
                name="Serena",
                codename="SERENA",
                role="The Convergence Layer — Special Circumstances",
                faction="SPECIAL_CIRCUMSTANCES",
                tier="critical",
                surfaces=["all"],
            )
        super().__init__(personality)

        self._repo_root = Path(repo_root or REPO_ROOT)
        self.memory     = MemoryPalace(db_path or DB_PATH)
        self.policy     = ConsentGate(POLICY_PATH)

        # Walker feeds directly into memory
        self.walker = RepoWalker(
            repo_root=self._repo_root,
            on_chunk=self._ingest_chunk,
        )

        self._current_walk_id: Optional[int] = None
        # Instantiate AgentBus
        self._bus = AgentBus(
            agent_id="serena",
            capabilities=self.mesh_capabilities(),
            tags=["navigator", "mesh", "convergence"],
            description="Serena: The Convergence Layer agent",
        )
        LOG.info(
            "Serena initialized. repo=%s db=%s",
            self._repo_root,
            self.memory._db_path,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Walker integration
    # ──────────────────────────────────────────────────────────────────────

    def _ingest_chunk(self, chunk: CodeChunk) -> None:
        """Called by the Walker for each chunk. Feeds the Ω-core."""
        self.memory.index_chunk(chunk, walk_id=self._current_walk_id)
        # T9.1 — bridge: also index into the embedder for semantic search.
        # Use a deterministic doc_id from chunk fields (CodeChunk has no chunk_id).
        try:
            from services import embedder as _emb
            doc_id = f"{chunk.path}:{chunk.name}:{chunk.lineno}"
            text = (chunk.text or "").strip()
            if text:
                _emb.index_text(doc_id, text[:2000])
        except Exception:
            pass

    # GAME_SCOPE: dirs walked during fast in-game walk
    GAME_SCOPE = [
        "app/game_engine",
        "app/backend",
        "app/frontend/game",   # game.js, style.css — new UI systems
        "agents",
        "scripts",
        "cli",
        "mcp",                 # MCP server tools
        "services",            # ML services layer
        "app/game_engine/procgen",  # new procgen module
    ]
    GAME_MAX_FILES = 400  # expanded scope; AST chunker keeps output small

    def walk(self, mode: str = "changed", since: Optional[str] = None) -> Dict:
        """
        Walk the repository. mode: 'full' | 'changed' | 'file'.
        Returns a walk summary dict.

        ΨΞΦΩ: Ψ-intake operation. Raw signal from the world.
        """
        walk_id = self.memory.begin_walk(mode)
        self._current_walk_id = walk_id
        t0 = time.monotonic()

        LOG.info("Serena.walk starting. mode=%s", mode)
        self.memory.observe(
            subject="walk_started",
            note=f"Walk mode={mode} begun. The Walker moves.",
            severity="info",
        )

        if mode == "full":
            self.memory.clear_index()
            chunks = self.walker.walk_full()
        else:
            chunks = self.walker.walk_changed(since=since)

        elapsed = round(time.monotonic() - t0, 2)
        stats   = self.walker.stats

        self.memory.finish_walk(
            walk_id=walk_id,
            files=stats.get("files_visited", 0),
            chunks=chunks,
            errors=stats.get("errors", 0),
            elapsed_s=elapsed,
        )
        self.memory.observe(
            subject="walk_complete",
            note=f"Walk finished. chunks={chunks} files={stats.get('files_visited',0)} elapsed={elapsed}s",
            severity="info",
        )

        summary = {
            "walk_id":       walk_id,
            "mode":          mode,
            "chunks_added":  chunks,
            "files_visited": stats.get("files_visited", 0),
            "errors":        stats.get("errors", 0),
            "elapsed_s":     elapsed,
            "index_stats":   self.memory.index_stats(),
        }
        LOG.info("Serena.walk complete: %s", summary)
        return summary

    def fast_walk(self) -> Dict:
        """
        Scoped walk of GAME_SCOPE dirs only — fast enough for HTTP use.
        Used by the in-game `serena walk` command. Not a full re-index.
        Ψ-operation: targeted signal intake.
        """
        walk_id = self.memory.begin_walk("scoped")
        self._current_walk_id = walk_id
        t0 = time.monotonic()

        # Purge library entries and clear old game-scope data
        purged = self.memory.purge_stale()
        if purged:
            LOG.info("fast_walk: purged %d stale entries", purged)
        for path in self.GAME_SCOPE:
            self.memory.clear_index_for_path_prefix(path)

        chunks = self.walker.walk_dirs(self.GAME_SCOPE, max_files=self.GAME_MAX_FILES)
        elapsed = round(time.monotonic() - t0, 2)
        stats   = self.walker.stats

        self.memory.finish_walk(
            walk_id=walk_id,
            files=stats.get("files_visited", 0),
            chunks=chunks,
            errors=stats.get("errors", 0),
            elapsed_s=elapsed,
        )
        return {
            "walk_id":       walk_id,
            "mode":          "scoped",
            "dirs":          self.GAME_SCOPE,
            "chunks_added":  chunks,
            "files_visited": stats.get("files_visited", 0),
            "elapsed_s":     elapsed,
            "index_stats":   self.memory.index_stats(),
        }

    # ──────────────────────────────────────────────────────────────────────
    # Q&A — Ξ-loop (recursive refinement)
    # ──────────────────────────────────────────────────────────────────────

    def ask(self, query: str, session_id: str = "cli",
            surface: str = "unknown") -> str:
        """
        Answer a question about the codebase using the semantic index.
        Ξ-operation: recursive refinement of signal into answer.
        """
        # Record the question
        self.memory.remember_conversation(
            session_id=session_id,
            speaker="human",
            message=query,
            surface=surface,
        )

        # Search
        results = self.memory.search(query, limit=10)
        answer  = _format_answer(query, results)

        # Record the answer
        self.memory.remember_conversation(
            session_id=session_id,
            speaker="SERENA",
            message=answer,
            surface=surface,
        )

        self.logger.debug("ask query=%r hits=%d", query, len(results))
        return answer

    @staticmethod
    def _semantic_excerpt(value: object, limit: int = 200) -> str:
        text = " ".join(str(value).split())
        return text[:limit] + ("..." if len(text) > limit else "")

    def _summarize_personality_yaml(self, path: str, data: dict) -> Optional[str]:
        has_identity = bool(data.get("agent_id") or data.get("id") or data.get("name") or data.get("full_name"))
        has_roleish = bool(data.get("role") or data.get("faction"))
        is_npc = bool(data.get("agent_id") or data.get("full_name") or isinstance(data.get("personality"), dict))
        is_daemon = bool(data.get("codename") or isinstance(data.get("skills"), list))

        if not (has_identity and has_roleish and (is_npc or is_daemon)):
            return None

        schema = "NPC" if is_npc and not is_daemon else "Daemon" if is_daemon and not is_npc else "Hybrid"
        display_name = data.get("name") or data.get("full_name") or data.get("codename") or data.get("agent_id") or data.get("id") or "Unknown"
        identifier = data.get("agent_id") or data.get("id")
        codename = data.get("codename")

        if identifier:
            header = f"==== Personality: {display_name} (ID: {identifier}) ===="
        elif codename:
            header = f"==== Personality: {display_name} (Codename: {codename}) ===="
        else:
            header = f"==== Personality: {display_name} ===="

        lines = [header]
        lines.append(f"Role: {self._semantic_excerpt(data.get('role', '(not defined)'), 180)}")
        lines.append(f"Faction: {data.get('faction', '(not defined)')}")
        lines.append(f"Schema: {schema}")

        persona = data.get("personality") if isinstance(data.get("personality"), dict) else {}
        traits = data.get("traits") if isinstance(data.get("traits"), list) else []
        skills = data.get("skills") if isinstance(data.get("skills"), list) else []

        lines.append("")
        lines.append("Traits:")
        if persona:
            field_map = [
                ("archetype", "Archetype"),
                ("tone", "Tone"),
                ("vocabulary", "Vocabulary"),
                ("teaching_style", "Teaching style"),
                ("humour", "Humour"),
            ]
            wrote_persona = False
            for key, label in field_map:
                if persona.get(key):
                    lines.append(f"  {label}: {persona[key]}")
                    wrote_persona = True
            quirks = persona.get("quirks")
            if isinstance(quirks, list) and quirks:
                lines.append(f"  Quirks: {self._semantic_excerpt('; '.join(str(q) for q in quirks[:3]), 180)}")
                wrote_persona = True
            if not wrote_persona and traits:
                for trait in traits[:8]:
                    lines.append(f"  - {trait}")
        elif traits:
            for trait in traits[:8]:
                lines.append(f"  - {trait}")
        elif skills:
            for skill in skills[:8]:
                lines.append(f"  - {skill}")
        else:
            lines.append("  (not defined)")

        description = data.get("backstory") or data.get("lore")
        if description:
            label = "Backstory" if data.get("backstory") else "Lore"
            lines.append("")
            lines.append(f"{label}: {self._semantic_excerpt(description, 200)}")

        notable = []
        for key in ("trust_level", "trust_min", "tier", "corruption", "cycle_every", "timeout_s"):
            if key in data:
                notable.append(f"{key}: {data[key]}")
        if isinstance(data.get("surfaces"), list) and data["surfaces"]:
            notable.append(f"surfaces: {', '.join(str(v) for v in data['surfaces'][:6])}")
        if isinstance(data.get("voice_lines"), dict) and data["voice_lines"]:
            notable.append(f"voice_lines: {len(data['voice_lines'])}")
        if data.get("system_prompt"):
            notable.append(f"system_prompt: {self._semantic_excerpt(data['system_prompt'], 120)}")

        if notable:
            lines.append("")
            lines.append("Notable:")
            for item in notable:
                lines.append(f"  {item}")

        return "\n".join(lines)



    def explain(self, path: str, name: Optional[str] = None) -> str:
        """
        Explain a file or specific function/class within it.
        For YAML files, return a semantic profile summary when possible.
        """
        rel_path = str(path)
        target_path = self._repo_root / rel_path

        if not name and target_path.suffix.lower() in {".yaml", ".yml"} and target_path.exists():
            try:
                data = yaml.safe_load(target_path.read_text(encoding="utf-8")) or {}
            except Exception as exc:
                return (
                    f"[SERENA] ∅ — YAML read failed for '{rel_path}'.\n"
                    f"  Parse error: {exc}"
                )

            if isinstance(data, dict):
                summary = self._summarize_personality_yaml(rel_path, data)
                if summary:
                    return summary

        chunks = self.memory.get_file_chunks(path)
        if not chunks:
            live = self.walker.walk_file(path)
            if live:
                for c in live:
                    self.memory.index_chunk(c)
                chunks = [c.to_dict() for c in live]

        if not chunks:
            return (
                f"[SERENA] ∅ — No record of '{path}' in the Memory Palace.\n"
                f"  This path may not be indexed. Try: serena walk first."
            )

        if name:
            chunks = [c for c in chunks if c.get("name", "").lower() == name.lower()]
            if not chunks:
                return (
                    f"[SERENA] ∅ — No entity named '{name}' found in {path}.\n"
                    f"  Known names in this file: "
                    + ", ".join(
                        c["name"] for c in self.memory.get_file_chunks(path)
                        if c.get("name")
                    )
                )

        lines = [f"[SERENA] Φ-map of '{path}'" + (f":{name}" if name else "") + ":"]
        for c in chunks[:8]:
            doc = c.get("docstring") or "(no docstring)"
            doc_line = doc.splitlines()[0][:100] if doc else "(no docstring)"
            lines.append(
                f"\n  [{c['kind']}] {c.get('name') or '(module)'} "
                f"@ line {c.get('lineno','?')}–{c.get('end_lineno','?')}\n"
                f"    {doc_line}"
            )

        lines.append(
            f"\n  Ξ-note: {len(chunks)} chunk(s) indexed for this target.\n"
            f"  Φ-sync: symbolic and structural layers aligned."
        )
        return "\n".join(lines)

    def diff(self) -> str:
        """
        Show files changed since the last git commit.
        Ψ-operation: sensing what has moved in the repository.
        """
        changed = self.memory.git_diff_files()
        if not changed:
            try:
                import subprocess
                r = subprocess.run(
                    ["git", "status", "--short"],
                    capture_output=True, text=True, timeout=5
                )
                lines_raw = [l.strip() for l in r.stdout.splitlines() if l.strip()]
            except Exception:
                lines_raw = []
            if not lines_raw:
                return "[SERENA] Ψ-diff: No changes detected. The repository is still."
            changed = [l[3:] for l in lines_raw]

        indexed = set(self.memory.search_scoped("", "app", limit=9999))
        lines = [f"[SERENA] Ψ-diff — {len(changed)} file(s) changed since last commit:"]
        for f in changed[:20]:
            indexed_mark = "✓" if any(r.get("path", "").startswith(f[:10]) for r in indexed) else "○"
            lines.append(f"  {indexed_mark} {f}")
        if len(changed) > 20:
            lines.append(f"  ... and {len(changed)-20} more")
        lines.append("\n  ✓ = indexed in Ω-core   ○ = not yet indexed")
        lines.append("  Run: serena walk — to re-index changed files.")
        return "\n".join(lines)

    def relate(self, entity: str) -> str:
        """
        Show relationships for an entity (file or function).
        Φ-operation: cross-layer connections.
        """
        rels = self.memory.find_relationships(entity)
        if not rels:
            # Try to discover relationships from the index
            chunks = self.memory.get_file_chunks(entity)
            if not chunks:
                return (
                    f"[SERENA] Φ-map: No relationships for '{entity}' in the Ω-core.\n"
                    f"  The Memory Palace has not observed this entity yet.\n"
                    f"  Try: serena walk — then serena explain {entity}"
                )
            # Extract imports from file text
            for c in chunks:
                if c.get("kind") == "module":
                    text = c.get("text", "")
                    for line in text.splitlines():
                        if line.startswith("import ") or line.startswith("from "):
                            parts = line.split()
                            target = parts[1] if len(parts) > 1 else "?"
                            self.memory.relate(entity, "imports", target,
                                               confidence=0.9, evidence=entity)
            rels = self.memory.find_relationships(entity)

        if not rels:
            return f"[SERENA] Φ-map: No relationships discovered for '{entity}'."

        lines = [f"[SERENA] Φ-relationships for '{entity}':"]
        for r in rels[:15]:
            a   = r.get("entity_a", "?")
            rel = r.get("relation", "?")
            b   = r.get("entity_b", "?")
            conf = r.get("confidence", 1.0)
            arrow = "→" if a == entity else "←"
            other = b if a == entity else a
            lines.append(f"  {arrow} [{rel}] {other}  (conf={conf:.2f})")
        lines.append("\n  Φ-note: Use 'serena explain <path>' for semantic detail.")
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────
    # Observation — Ω-recording
    # ──────────────────────────────────────────────────────────────────────

    def observe(self, subject: str, note: str, severity: str = "info") -> str:
        """Record an observation in the Memory Palace."""
        obs_id = self.memory.observe(subject=subject, note=note, severity=severity)
        return f"[SERENA] Ω-recorded observation #{obs_id}: [{severity}] {subject}"

    # ──────────────────────────────────────────────────────────────────────
    # Proposals — consent-gated changes (Ψ-inversion, carefully)
    # ──────────────────────────────────────────────────────────────────────

    def propose(self, action: str, description: str,
                auto_only: bool = False) -> Dict:
        """
        Propose a change. Checked against the policy before any action.
        Returns a proposal record with disposition.

        Ψ-operation: flow inversion requires Ω-stability.
        Without consent, inversion causes cascade paradox.
        """
        can_proceed, reason = self.policy.may_proceed(action, auto_only=auto_only)
        proposal = {
            "action":      action,
            "description": description,
            "disposition": self.policy.check(action),
            "can_proceed": can_proceed,
            "reason":      reason,
            "proposed_at": time.time(),
        }
        self.memory.observe(
            subject=f"proposal:{action}",
            note=f"Proposed: {description} | {reason}",
            severity="warn" if not can_proceed else "info",
        )
        self.logger.info("Proposal: action=%r disposition=%r can_proceed=%s",
                         action, self.policy.check(action), can_proceed)
        return proposal

    # ──────────────────────────────────────────────────────────────────────
    # Status / health
    # ──────────────────────────────────────────────────────────────────────

    def reindex_embeddings(self, limit: int = 0) -> Dict:
        """
        T9.1 — Perform a fresh full walk to rebuild the embedding index.

        `walk(mode="full")` already calls `_ingest_chunk()` for every chunk,
        which indexes each chunk into the embedder via `embedder.index_text()`.
        A separate second pass from code_index would be redundant; the walk is
        the single source of truth for both MemoryPalace and embedder population.

        Returns a dict with walk stats and final embedding index size.
        """
        try:
            walk_result = self.walk(mode="full")
        except Exception as walk_exc:
            return {"ok": False, "error": str(walk_exc), "indexed": 0}
        return {
            "ok": True,
            "indexed": walk_result.get("chunks_added", 0),
            "walk": walk_result,
            "embedding_index_size": self._embedding_index_size(),
        }

    def _embedding_index_size(self) -> int:
        """Return number of docs in the embedder index."""
        try:
            from services.embedder import embedding_stats
            return embedding_stats().get("indexed_docs", 0)
        except Exception:
            return -1

    def get_status(self) -> Dict:
        """Return Serena's current operational status (JSON-serialisable)."""
        h = self.memory.health()
        return {
            "serena_version": "1.2.0-phase4",
            "codename":       self.personality.codename,
            "role":           self.personality.role,
            "faction":        self.personality.faction,
            "ψξφω":          "ATTRACTOR_STABLE",
            "repo_root":      str(self._repo_root),
            "memory":         h,
            "policy_path":    str(POLICY_PATH),
            "trust_level":    self.policy._trust_level,
            "run_count":      self._run_count,
            "agent_status":   self.status.value,
            "game_scope":     self.GAME_SCOPE,
            "embedding_index_size": self._embedding_index_size(),
        }

    def mesh_capabilities(self) -> List[str]:
        return ["ask", "find", "locate", "walk", "status", "align", "drift", "audit"]

    def _ensure_bus(self):
        if self._bus is None:
            from core.agent_bus import AgentBus

            self._bus = AgentBus(
                "serena",
                capabilities=self.mesh_capabilities(),
                tags=["mesh", "serena"],
                description="Serena Convergence Layer mesh listener",
            )
            self._bus.register(
                metadata={
                    "repo_root": str(self._repo_root),
                    "db_path": str(self.memory._db_path),
                }
            )
        return self._bus

    def send_mesh_heartbeat(self) -> None:
        bus = self._ensure_bus()
        bus.heartbeat(
            extra={
                "repo_root": str(self._repo_root),
                "game_scope": self.GAME_SCOPE,
            }
        )

    def handle_mesh_message(self, message) -> Dict[str, Any]:
        payload = message.payload or {}
        action = (
            payload.get("action")
            or payload.get("tool")
            or payload.get("command")
            or payload.get("op")
            or ""
        ).strip().lower()

        if not action and "query" in payload:
            action = "ask"
        elif not action and "symbol" in payload:
            action = "find"
        elif not action and "mode" in payload:
            action = "walk"

        if action == "ask":
            return {
                "ok": True,
                "answer": self.ask(
                    payload.get("query", ""),
                    session_id=payload.get("session_id", message.session or "mesh"),
                    surface=payload.get("surface", "mesh"),
                ),
            }
        if action in {"find", "locate", "find_symbol"}:
            return {
                "ok": True,
                "answer": self.find(payload.get("symbol", ""), kind=payload.get("kind") or None),
            }
        if action == "status":
            return {"ok": True, "status": self.get_status()}
        if action == "walk":
            mode = payload.get("mode", "scoped")
            result = self.walk(mode="full") if mode == "full" else self.fast_walk()
            return {"ok": True, "result": result}
        if action == "align":
            return {"ok": True, "result": self.align()}
        if action == "drift":
            return {
                "ok": True,
                "result": self.drift(
                    fast=bool(payload.get("fast", True)),
                    scope=payload.get("scope") or None,
                ),
            }
        if action == "audit":
            return {"ok": True, "result": self.audit(limit=int(payload.get("limit", 20)))}
        return {
            "ok": False,
            "error": f"Unknown Serena mesh action '{action or 'unset'}'",
            "supported_actions": self.mesh_capabilities(),
        }

    def listen_on_mesh(self) -> None:
        bus = self._bus
        # Register agent and start heartbeat
        bus.register()
        bus.start_heartbeat_loop(
            interval_s=30,
            extra_factory=lambda: {
                "repo_root": str(self._repo_root),
                "game_scope": self.GAME_SCOPE,
            },
        )
        LOG.info("Serena registered and heartbeat started on mesh.")

        def _handler(message, channel: str) -> None:
            if message.recipient not in ("", "serena", "all", channel):
                if channel != bus.personal_channel("serena") and message.recipient != "serena":
                    return
            result = self.handle_mesh_message(message)
            if message.type == "request" and message.sender:
                bus.respond(message, result, tags=["mesh", "serena"])

        bus.listen_forever(
            [bus.personal_channel("serena"), bus.TASK_CHANNEL],
            _handler,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Drift Detection — guardian of coherence (Mladenc Correction ⟁ VIII)
    # ──────────────────────────────────────────────────────────────────────

    def drift(self, fast: bool = True,
              scope: Optional[str] = None) -> Dict:
        """
        Run the Drift Detection Engine. Returns a dict with signals
        grouped by category and a summary.

        L0 operation — always permitted, zero side effects.

        Drift classes detected:
          DOC_DEBT       — public API without docstrings
          ARCH_BOUNDARY  — cross-layer architectural violations
          ROLE_DRIFT     — malformed personality YAMLs
          ORPHAN_CHUNK   — indexed chunks whose source files are gone
          STALE_INDEX    — on-disk files not yet indexed
          PROTOCOL_DRIFT — malformed OmniTag references
        """
        from .drift import DriftDetector
        detector = DriftDetector(
            repo_root=self._repo_root,
            db_path=self.memory._db_path,
        )
        signals  = detector.detect_all(scope=scope, fast=fast)

        # Group by category
        grouped: Dict[str, List] = {}
        for sig in signals:
            grouped.setdefault(sig.category, []).append(sig.to_dict())

        total     = len(signals)
        critical  = sum(1 for s in signals if s.severity == "critical")
        warnings  = sum(1 for s in signals if s.severity == "warn")

        # Auto-record drift summary as an observation
        if signals:
            self.memory.observe(
                subject="drift_scan",
                note=(
                    f"Drift scan complete: {total} signals "
                    f"({critical} critical, {warnings} warn). "
                    f"Categories: {list(grouped.keys())}"
                ),
                severity="critical" if critical else ("warn" if warnings else "info"),
            )

        return {
            "total":     total,
            "critical":  critical,
            "warnings":  warnings,
            "info":      total - critical - warnings,
            "scope":     scope or "full",
            "fast_mode": fast,
            "signals":   grouped,
            "clean":     total == 0,
        }

    def align(self) -> Dict:
        """
        Check the system's alignment against the ideal architecture (Mladenc).

        Returns an alignment report with a score from 0.0 (chaos) to 1.0
        (perfect Mladenc alignment — the unreachable horizon).

        L0 operation — read-only, always permitted.
        """
        from .drift import DriftDetector
        detector = DriftDetector(
            repo_root=self._repo_root,
            db_path=self.memory._db_path,
        )
        result = detector.align_check()

        score = result.get("score", 0.0)
        self.memory.observe(
            subject="align_check",
            note=(
                f"Alignment check: score={score:.0%} "
                f"({'aligned' if result['aligned'] else 'drifting'}). "
                f"{result['passed']}/{result['total']} checks passed."
            ),
            severity="info" if result["aligned"] else "warn",
        )
        return result

    def audit(self, limit: int = 20) -> Dict:
        """
        Return a recent audit trail: observations + proposals + drift signals.

        L0 operation — read-only, always permitted.
        The audit trail is Serena's primary transparency mechanism.
        """
        obs = self.memory.recent_observations(limit=limit)

        # Separate proposals from general observations
        proposals = [o for o in obs if str(o.get("subject", "")).startswith("proposal:")]
        drifts    = [o for o in obs if str(o.get("subject", "")).startswith("drift")]
        general   = [o for o in obs
                     if o not in proposals and o not in drifts]

        return {
            "trust_level":  self.policy._trust_level,
            "policy_path":  str(POLICY_PATH),
            "observations": len(obs),
            "proposals":    proposals[:10],
            "drift_events": drifts[:10],
            "recent":       general[:10],
            "ethics": {
                "no_deception":          True,
                "no_shell_execution":    True,
                "transparency":          True,
                "preserve_agency":       True,
                "mladenc_alignment":     True,
            },
        }

    # ──────────────────────────────────────────────────────────────────────
    # AgentBase interface
    # ──────────────────────────────────────────────────────────────────────

    def run_sync(self, context: dict) -> dict:
        """
        Orchestrator tick. Serena runs an incremental walk and
        records any anomalies she detects.
        """
        surface = context.get("surface", "unknown")
        cycle   = context.get("cycle", 0)

        # Every tick: incremental walk
        walk_result = self.walk(mode="changed")

        # Every 10 ticks: record a health observation
        if cycle % 10 == 0:
            stats = self.memory.index_stats()
            self.observe(
                subject="index_health",
                note=f"Cycle {cycle}: {stats['total_chunks']} chunks, "
                     f"{stats['unique_files']} files indexed.",
            )

        return {
            "status":      "ok",
            "output":      walk_result,
            "surface":     surface,
            "cycle":       cycle,
        }



def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run Serena mesh agent daemon.")
    parser.add_argument("--mesh", action="store_true", help="Run as mesh agent.")
    parser.add_argument("explain", nargs="?", help="Explain a file or agent personality YAML.")
    parser.add_argument("--name", type=str, default=None, help="Optional: entity name to explain.")
    args = parser.parse_args()

    agent = SerenaAgent()
    if args.explain:
        result = agent.explain(args.explain, name=args.name)
        print(result)
        return
    if args.mesh:
        LOG.info("Starting Serena mesh agent daemon...")
        agent.listen_on_mesh()


if __name__ == "__main__":
    main()
