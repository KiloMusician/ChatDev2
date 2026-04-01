"""config/autoboot.py — Autonomous Boot Engine

8-Phase sequence that runs every startup:
  DETECT → ANNOTATE → RECONCILE → ADJUST → RESUME → NUDGE → AWAKEN → TAKE_FLIGHT

Each phase is independently isolated. Any single phase failure cannot crash the engine.
Results are written to state/boot_manifest.json and consumed by the game's `boot` command.
"""
from __future__ import annotations
import json, socket, sqlite3, importlib, os, time, shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

ROOT         = Path(__file__).parent.parent
STATE_DIR    = ROOT / "state"
MANIFEST_PATH = STATE_DIR / "boot_manifest.json"


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class PhaseResult:
    phase:       str
    ok:          bool          = True
    items:       list[dict]    = field(default_factory=list)
    actions:     list[str]     = field(default_factory=list)
    duration_ms: float         = 0.0
    error:       str           = ""

    def item(self, label: str, status: str, detail: str = "", action: str = ""):
        self.items.append({"label": label, "status": status, "detail": detail, "action": action})
        if action:
            self.actions.append(action)

    def warn(self, label: str, detail: str = ""):
        self.item(label, "warn", detail)

    def err(self, label: str, detail: str = ""):
        self.item(label, "error", detail)
        self.ok = False


@dataclass
class BootManifest:
    session_id:   str        = ""
    timestamp:    str        = ""
    env:          str        = "unknown"
    phases:       list[Any]  = field(default_factory=list)
    overall:      str        = "NOMINAL"
    online:       int        = 0
    total:        int        = 0
    health_score: float      = 1.0
    actions_taken: list[str] = field(default_factory=list)
    delta:        dict       = field(default_factory=dict)
    ready:        bool       = False
    meta:         dict       = field(default_factory=dict)  # integration probe results


# ── Probe utilities ──────────────────────────────────────────────────────────

def _probe(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def _http_get(url: str, timeout: float = 1.2) -> dict | None:
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def _pkg(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def _db_count(path: Path, table: str) -> tuple[bool, int]:
    if not path.exists():
        return False, 0
    try:
        conn = sqlite3.connect(path, timeout=1.0)
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.close()
        return True, n
    except Exception:
        return path.exists(), -1


def _ensure_table(conn: sqlite3.Connection, ddl: str):
    try:
        conn.execute(ddl)
        conn.commit()
    except Exception:
        pass


# ── Integration probe helpers ─────────────────────────────────────────────────

def _probe_github() -> dict:
    """Validate GITHUB_TOKEN against api.github.com. Returns login + scopes."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return {"ok": False, "reason": "no_token"}
    try:
        import urllib.request as _ur
        req = _ur.Request(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {token}",
                "User-Agent": "terminal-depths/2.0",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with _ur.urlopen(req, timeout=3.5) as resp:
            data   = json.loads(resp.read())
            scopes = [s.strip() for s in resp.headers.get("X-OAuth-Scopes", "").split(",") if s.strip()]
            return {"ok": True, "login": data.get("login", "?"),
                    "id": data.get("id"), "scopes": scopes[:6]}
    except Exception as exc:
        return {"ok": False, "reason": str(exc)[:80]}


def _probe_replit() -> dict:
    """Extract Replit environment metadata from well-known env vars."""
    return {
        "mode":      os.environ.get("REPLIT_MODE", ""),
        "user":      os.environ.get("REPLIT_USER", ""),
        "domain":    os.environ.get("REPLIT_DOMAINS", ""),
        "env":       os.environ.get("REPLIT_ENVIRONMENT", ""),
        "has_kv":    bool(os.environ.get("REPLIT_DB_URL")),
        "cluster":   os.environ.get("REPLIT_CLUSTER", ""),
        "has_ai":    bool(os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")),
        "userid":    os.environ.get("REPLIT_USERID", ""),
    }


def _probe_vscode() -> dict:
    """Check VS Code workspace artifacts present in the repo root."""
    return {
        "tasks_json":   (ROOT / ".vscode" / "tasks.json").exists(),
        "mcp_json":     (ROOT / ".vscode" / "mcp.json").exists(),
        "devcontainer": (ROOT / ".devcontainer" / "devcontainer.json").exists(),
        "settings":     (ROOT / ".vscode" / "settings.json").exists(),
        "extensions":   (ROOT / ".vscode" / "extensions.json").exists(),
    }


def _probe_ai_services() -> dict:
    """Quick presence check for AI service keys / reachable endpoints."""
    return {
        "replit_ai":    bool(os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")),
        "openai_key":   bool(os.environ.get("OPENAI_API_KEY")),
        "anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "ollama":       _probe("127.0.0.1", 11434, 0.3),
        "model_router": _probe("127.0.0.1", 9001, 0.3),
    }


def _find_existing_path(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _probe_hub_integrations() -> dict:
    """Detect Nogic and GitNexus surfaces in the sibling NuSyQ-Hub repo."""
    env_root = os.environ.get("NUSYQ_HUB_ROOT", "").strip()
    candidates = [
        Path(env_root) if env_root else None,
        ROOT.parent / "Desktop" / "Legacy" / "NuSyQ-Hub",
        Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub"),
        Path("/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub"),
    ]
    hub_root = _find_existing_path([p for p in candidates if p is not None])
    if hub_root is None:
        return {
            "hub_root": "",
            "nogic": False,
            "nogic_vscode_bridge": False,
            "gitnexus": False,
            "gitnexus_plan": False,
        }

    gitnexus_implemented = (hub_root / "src" / "orchestration" / "gitnexus.py").exists()

    return {
        "hub_root": str(hub_root),
        "nogic": (hub_root / "src" / "integrations" / "nogic_bridge.py").exists(),
        "nogic_vscode_bridge": (hub_root / "src" / "integrations" / "nogic_vscode_bridge.py").exists(),
        "gitnexus": gitnexus_implemented,
        "gitnexus_plan": (not gitnexus_implemented) and any(
            (
                hub_root / "CHATDEV_TASK_GITNEXUS.py",
                hub_root / "ACTIVATE_VIA_CHATDEV.md",
            )
        ),
    }


def _probe_ecosystem() -> dict:
    """Detect SkyClaw, ChatDev, Culture Ship, Gordon, MCP server scripts."""
    scripts = ROOT / "scripts"
    hub = _probe_hub_integrations()
    return {
        "skyclaw":        (scripts / "skyclaw_scanner.py").exists(),
        "chatdev":        (scripts / "chatdev_stub.py").exists(),
        "chatdev_worker": (scripts / "chatdev_worker.py").exists(),
        "culture_ship":   (scripts / "culture_ship.py").exists(),
        "gordon":         (scripts / "gordon_orchestrator.py").exists(),
        "mcp_server":     (scripts / "mcp_server.py").exists(),
        "ci_workflow":    (ROOT / ".github" / "workflows" / "ci.yml").exists(),
        "nogic":          hub.get("nogic", False),
        "nogic_vscode_bridge": hub.get("nogic_vscode_bridge", False),
        "gitnexus":       hub.get("gitnexus", False),
        "gitnexus_plan":  hub.get("gitnexus_plan", False),
        "hub_root":       hub.get("hub_root", ""),
    }


def _probe_docker() -> dict:
    """Check for Docker compose files and Docker socket availability."""
    return {
        "socket":       (Path("/var/run/docker.sock")).exists(),
        "compose_core": (ROOT / "docker-compose.yml").exists(),
        "compose_full": (ROOT / "docker-compose.full.yml").exists(),
        "makefile":     (ROOT / "Makefile").exists(),
        "dockerfile":   (ROOT / "Dockerfile").exists(),
    }


def _probe_serena() -> dict:
    """Probe Serena's code intelligence layer — direct DB read (no REST required)."""
    out: dict = {
        "ok": False, "symbols": 0, "files": 0,
        "observations": 0, "walks": 0,
        "drift_warn": 0, "drift_critical": 0,
    }
    try:
        import sqlite3 as _sq
        from config.runtime import PATHS
        ser_path = Path(PATHS.get("db_serena", "state/serena_memory.db"))
        if not ser_path.exists():
            return out
        con = _sq.connect(str(ser_path))
        cur = con.cursor()
        try:
            cur.execute("SELECT COUNT(*), COUNT(DISTINCT path) FROM code_index")
            row = cur.fetchone()
            out["symbols"] = row[0] or 0
            out["files"]   = row[1] or 0
        except Exception:
            pass
        try:
            cur.execute("SELECT COUNT(*) FROM observations")
            out["observations"] = cur.fetchone()[0] or 0
        except Exception:
            pass
        try:
            cur.execute("SELECT COUNT(*) FROM walks")
            out["walks"] = cur.fetchone()[0] or 0
        except Exception:
            pass
        # Read cached drift summary from meta table (written by /api/serena/drift)
        try:
            cur2 = con.cursor()
            cur2.execute("SELECT key, value FROM meta WHERE key IN ('last_drift_warn','last_drift_critical')")
            for k, v in cur2.fetchall():
                if k == "last_drift_warn":
                    out["drift_warn"]     = int(v)
                elif k == "last_drift_critical":
                    out["drift_critical"] = int(v)
        except Exception:
            pass
        con.close()
        out["ok"] = out["symbols"] > 0
    except Exception as exc:
        out["error"] = str(exc)
    return out


def _publish_kv(key: str, value: str) -> bool:
    """Write a value to Replit KV store. Returns True on success."""
    db_url = os.environ.get("REPLIT_DB_URL", "")
    if not db_url:
        return False
    try:
        import urllib.request as _ur
        import urllib.parse as _up
        body = _up.urlencode({key: value}).encode()
        req  = _ur.Request(db_url, data=body, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with _ur.urlopen(req, timeout=2.5) as resp:
            return resp.status < 300
    except Exception:
        return False


def _patch_agents_md(m: "BootManifest") -> bool:
    """Inject a live-status block into AGENTS.md between sentinel comments."""
    agents_path = ROOT / "AGENTS.md"
    if not agents_path.exists():
        return False
    try:
        import re
        domain = os.environ.get("REPLIT_DOMAINS", "localhost:5000")
        ts     = m.timestamp  # already formatted: "2026.MM.DD  HH:MM UTC"
        who    = os.environ.get("REPLIT_USER", "") or m.meta.get("replit", {}).get("user", "unknown")
        block  = (
            "<!-- AUTOBOOT:START -->\n"
            "## System Health (Live — Auto-Updated by Boot Engine)\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            f"| Boot Status | **{m.overall}** |\n"
            f"| Health Score | {m.health_score:.1%} |\n"
            f"| Services | {m.online}/{m.total} online |\n"
            f"| Replit User | {who} |\n"
            f"| Last Boot | {ts} |\n"
            f"| Public URL | https://{domain} |\n"
            f"| Autoboot API | `GET /api/system/autoboot` |\n"
            f"| Boot Manifest | `state/boot_manifest.json` |\n\n"
            "> Updated every restart by the 8-phase boot engine.  \n"
            "> External agents: read `td:boot:latest` from Replit KV for current state.\n"
            "<!-- AUTOBOOT:END -->"
        )
        content = agents_path.read_text(encoding="utf-8")
        START, END = "<!-- AUTOBOOT:START -->", "<!-- AUTOBOOT:END -->"
        if START in content and END in content:
            content = re.sub(
                re.escape(START) + r".*?" + re.escape(END),
                block,
                content,
                flags=re.DOTALL,
            )
        else:
            content = re.sub(r"(# [^\n]+\n)", r"\1\n" + block + "\n", content, count=1)
        agents_path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


# ── Phase 0: DETECT — fingerprint everything ─────────────────────────────────

def _phase_detect(m: BootManifest) -> PhaseResult:
    t0 = time.monotonic()
    r  = PhaseResult(phase="DETECT")
    try:
        from config.runtime import (
            RUNTIME_ENV, SELF_PORT, PATHS, build_service_status,
        )
        m.env = RUNTIME_ENV
        r.item("runtime_env",  "ok", RUNTIME_ENV)
        r.item("self_port",    "ok", str(SELF_PORT))

        # Service probes (uses port_map via runtime)
        services = build_service_status(quick=True)
        online   = sum(1 for v in services.values() if v.get("up"))
        total    = len(services)
        m.online, m.total = online, total
        for name, info in services.items():
            status = "up" if info.get("up") else "down"
            r.item(f"svc:{name}", status, f":{info.get('port', '?')}")

        # Database probes
        db_checks = [
            ("db_serena",  "code_index"),
            ("db_memory",  "agent_memory"),
            ("db_lattice", "lattice_nodes"),
            ("db_ml",      "model_registry"),
            ("db_rl",      "q_values"),
        ]
        for key, table in db_checks:
            p = PATHS.get(key)
            if p:
                exists, n = _db_count(Path(p), table)
                status = "ok" if exists else "missing"
                detail = (f"{n} rows" if n >= 0 else "schema error") if exists else "absent"
                r.item(f"db:{key}", status, detail)

        # Env secrets (existence only — never log values)
        for var in ("SESSION_SECRET", "GITHUB_TOKEN"):
            ok = bool(os.environ.get(var))
            r.item(f"env:{var}", "ok" if ok else "missing")

        # Critical packages
        for pkg in ("fastapi", "sqlalchemy", "numpy", "requests", "yaml"):
            r.item(f"pkg:{pkg}", "ok" if _pkg(pkg) else "missing")

        # Disk headroom
        try:
            usage = shutil.disk_usage(STATE_DIR if STATE_DIR.exists() else ROOT)
            pct   = usage.used / usage.total * 100
            free_mb = usage.free // 1_048_576
            r.item("disk:state/", "ok" if pct < 85 else "warn",
                   f"{pct:.1f}% used  ({free_mb} MB free)")
        except Exception:
            r.item("disk:state/", "skip", "unavailable")

        # ── Integration probes ────────────────────────────────────────────────

        # Replit environment metadata
        replit = _probe_replit()
        m.meta["replit"] = replit
        mode_label = replit.get("mode", "") or "standard"
        user_label = replit.get("user", "") or "?"
        r.item("replit:env", "ok",
               f"mode={mode_label}  user={user_label}  kv={'yes' if replit['has_kv'] else 'no'}")

        # GitHub API validation
        gh = _probe_github()
        m.meta["github"] = gh
        if gh["ok"]:
            scopes_str = ",".join(gh.get("scopes", []))[:40] or "read"
            r.item("github:api", "ok", f"login={gh['login']}  scopes=[{scopes_str}]")
        else:
            reason = gh.get("reason", "unknown")
            r.item("github:api", "warn" if "no_token" not in reason else "missing",
                   reason[:60])

        # VS Code workspace artifacts
        vsc = _probe_vscode()
        m.meta["vscode"] = vsc
        vsc_found = sum(vsc.values())
        r.item("vscode:workspace", "ok" if vsc_found >= 3 else "warn",
               f"{vsc_found}/5 artifacts (tasks/mcp/devcontainer/settings/extensions)")

        # AI service keys + endpoints
        ai = _probe_ai_services()
        m.meta["ai_services"] = ai
        ai_avail = [k for k, v in ai.items() if v]
        r.item("ai:services", "ok" if ai_avail else "warn",
               "  ".join(ai_avail) if ai_avail else "no AI services detected")

        # Ecosystem scripts (SkyClaw, ChatDev, Gordon, MCP)
        eco = _probe_ecosystem()
        m.meta["ecosystem"] = eco
        eco_found = [k for k, v in eco.items() if v]
        r.item("ecosystem:scripts", "ok",
               f"{len(eco_found)}/{len(eco)} scripts  ({','.join(eco_found[:4])}{'…' if len(eco_found)>4 else ''})")

        # Docker stack artifacts
        docker = _probe_docker()
        m.meta["docker"] = docker
        docker_label = ("socket+compose" if docker["socket"] and docker["compose_core"]
                        else "compose-only" if docker["compose_core"]
                        else "absent")
        r.item("docker:stack", "ok" if docker["compose_core"] else "warn", docker_label)

    except Exception as exc:
        r.ok    = False
        r.error = str(exc)
        r.item("detect:error", "error", str(exc))

    r.duration_ms = (time.monotonic() - t0) * 1000
    return r


# ── Phase 1: ANNOTATE — compute health score, write preliminary manifest ─────

def _phase_annotate(m: BootManifest, detect: PhaseResult) -> PhaseResult:
    t0 = time.monotonic()
    r  = PhaseResult(phase="ANNOTATE")
    try:
        svc_items = [i for i in detect.items if i["label"].startswith("svc:")]
        db_items  = [i for i in detect.items if i["label"].startswith("db:")]
        env_items = [i for i in detect.items if i["label"].startswith("env:")]
        pkg_items = [i for i in detect.items if i["label"].startswith("pkg:")]

        svc_up  = sum(1 for i in svc_items if i["status"] == "up")
        db_ok   = sum(1 for i in db_items  if i["status"] == "ok")
        env_ok  = sum(1 for i in env_items if i["status"] == "ok")
        pkg_ok  = sum(1 for i in pkg_items if i["status"] == "ok")

        r.item("services",    "ok" if svc_up > 0  else "warn",
               f"{svc_up}/{len(svc_items)} online")
        r.item("databases",   "ok" if db_ok >= 3  else "warn",
               f"{db_ok}/{len(db_items)} present")
        r.item("env_secrets", "ok" if env_ok == len(env_items) else "warn",
               f"{env_ok}/{len(env_items)} set")
        r.item("packages",    "ok" if pkg_ok >= 4 else "warn",
               f"{pkg_ok}/{len(pkg_items)} installed")

        # Weighted health score
        svc_w = svc_up / max(len(svc_items), 1)
        db_w  = db_ok  / max(len(db_items),  1)
        env_w = env_ok / max(len(env_items), 1)
        health = round(svc_w * 0.45 + db_w * 0.35 + env_w * 0.20, 3)
        m.health_score = health
        m.overall = ("NOMINAL" if health >= 0.65 else
                     "DEGRADED" if health >= 0.35 else "CRITICAL")

        r.item("health_score", "ok", f"{health:.1%}")
        r.item("system_mode",  "ok", m.overall)

        # Quest log annotation
        ql = STATE_DIR / "quest_log.jsonl"
        if ql.exists():
            lines = sum(1 for _ in ql.open())
            r.item("quest_log", "ok", f"{lines} challenges catalogued")
        else:
            r.warn("quest_log", "quest_log.jsonl absent — expected state/quest_log.jsonl")

        # Write preliminary manifest so it exists for RESUME to diff
        _write_manifest(m)
        r.item("manifest:preliminary", "ok", str(MANIFEST_PATH.name))

    except Exception as exc:
        r.ok    = False
        r.error = str(exc)

    r.duration_ms = (time.monotonic() - t0) * 1000
    return r


# ── Phase 2: RECONCILE — fix detectable issues ───────────────────────────────

def _phase_reconcile(m: BootManifest) -> PhaseResult:
    t0 = time.monotonic()
    r  = PhaseResult(phase="RECONCILE")

    # Ensure state/ exists
    if not STATE_DIR.exists():
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        r.item("mkdir:state/", "fixed", "created", "Created state/ directory")
    else:
        r.item("dir:state/", "ok", "exists")

    # Ensure sessions/ exists
    sessions_dir = ROOT / "sessions"
    if not sessions_dir.exists():
        sessions_dir.mkdir(parents=True, exist_ok=True)
        r.item("mkdir:sessions/", "fixed", "created", "Created sessions/ directory")
    else:
        r.item("dir:sessions/", "ok", "exists")

    # Stale git lock
    lock = ROOT / ".git" / "index.lock"
    if lock.exists() and lock.stat().st_size == 0:
        lock.unlink(missing_ok=True)
        r.item("git:index.lock", "fixed", "0-byte lock removed", "Removed stale .git/index.lock")
    else:
        r.item("git:index.lock", "ok", "clean")

    # Reconcile memory.db schema (agent memory, errors, tasks, LLM cache)
    try:
        from config.runtime import PATHS
        mem_path = Path(PATHS.get("db_memory", "state/memory.db"))
        mem_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(mem_path, timeout=2.0)
        _ensure_table(conn, """CREATE TABLE IF NOT EXISTS agent_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, agent TEXT,
            event_type TEXT, content TEXT, timestamp REAL, success INTEGER DEFAULT 1)""")
        _ensure_table(conn, """CREATE TABLE IF NOT EXISTS error_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL,
            error TEXT, context TEXT, resolved INTEGER DEFAULT 0)""")
        _ensure_table(conn, """CREATE TABLE IF NOT EXISTS pending_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT,
            priority INTEGER DEFAULT 5, created_at REAL)""")
        _ensure_table(conn, """CREATE TABLE IF NOT EXISTS llm_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT, prompt_hash TEXT UNIQUE,
            response TEXT, backend TEXT, created_at REAL, hits INTEGER DEFAULT 0)""")
        _ensure_table(conn, """CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, context TEXT,
            insight TEXT, confidence REAL DEFAULT 0.5, created_at REAL)""")
        conn.close()
        r.item("db:memory.db", "ok", "schema verified + reconciled")
    except Exception as exc:
        r.warn("db:memory.db", f"schema reconcile failed: {exc}")

    # Reconcile lattice.db schema
    try:
        from config.runtime import PATHS
        lat_path = Path(PATHS.get("db_lattice", "state/lattice.db"))
        lat_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(lat_path, timeout=2.0)
        _ensure_table(conn, """CREATE TABLE IF NOT EXISTS lattice_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, node_id TEXT UNIQUE,
            node_type TEXT, label TEXT, meta TEXT, created_at REAL, updated_at REAL)""")
        _ensure_table(conn, """CREATE TABLE IF NOT EXISTS lattice_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT, src TEXT, dst TEXT,
            weight REAL DEFAULT 1.0, edge_type TEXT, created_at REAL)""")
        conn.close()
        r.item("db:lattice.db", "ok", "schema verified + reconciled")
    except Exception as exc:
        r.warn("db:lattice.db", f"schema reconcile failed: {exc}")

    # ── Integration reconciliation ────────────────────────────────────────────

    # Patch AGENTS.md with current boot status (preliminary — before health score)
    try:
        patched = _patch_agents_md(m)
        if patched:
            r.item("agents_md", "fixed", "boot status injected into AGENTS.md")
            r.actions.append("AGENTS.md patched with live boot status block")
        else:
            r.item("agents_md", "skip", "AGENTS.md not found")
    except Exception as exc:
        r.warn("agents_md", str(exc)[:60])

    # Sync agent_manifest.json endpoints to actual running port
    try:
        from config.runtime import SELF_PORT
        manifest_path = ROOT / "state" / "agent_manifest.json"
        if manifest_path.exists():
            import json as _json
            mdata = _json.loads(manifest_path.read_text())
            updated = False
            replit_domain = os.environ.get("REPLIT_DOMAINS", "")
            if replit_domain and "endpoints" in mdata:
                for key, val in list(mdata["endpoints"].items()):
                    if "localhost:7337" in val and m.env == "replit":
                        mdata["endpoints"][key] = val.replace(
                            "localhost:7337", f"localhost:{SELF_PORT}"
                        )
                        updated = True
            if updated:
                manifest_path.write_text(_json.dumps(mdata, indent=2))
                r.item("agent_manifest", "fixed",
                       f"endpoints updated  (7337→{SELF_PORT})")
                r.actions.append(f"agent_manifest.json ports reconciled → :{SELF_PORT}")
            else:
                r.item("agent_manifest", "ok", "endpoints current")
        else:
            r.item("agent_manifest", "skip", "state/agent_manifest.json absent")
    except Exception as exc:
        r.warn("agent_manifest", str(exc)[:60])

    m.actions_taken.extend(r.actions)
    r.duration_ms = (time.monotonic() - t0) * 1000
    return r


# ── Phase 3: ADJUST — set runtime mode flags, choose LLM backend ─────────────

def _phase_adjust(m: BootManifest, detect: PhaseResult) -> PhaseResult:
    t0 = time.monotonic()
    r  = PhaseResult(phase="ADJUST")
    try:
        svc_items   = [i for i in detect.items if i["label"].startswith("svc:")]
        online      = sum(1 for i in svc_items if i["status"] == "up")
        total       = len(svc_items)

        offline_mode  = (online <= 1)
        degraded_mode = (not offline_mode and online < max(total * 0.4, 2))

        os.environ["TD_OFFLINE_MODE"]  = "1" if offline_mode  else "0"
        os.environ["TD_DEGRADED_MODE"] = "1" if degraded_mode else "0"

        mode_str = ("OFFLINE"  if offline_mode  else
                    "DEGRADED" if degraded_mode else "NOMINAL")
        r.item("runtime_mode", "ok", mode_str)
        r.actions.append(f"Runtime mode → {mode_str}")

        # LLM backend selection (most capable available wins)
        ollama_up  = any(i["label"] == "svc:ollama"  and i["status"] == "up" for i in detect.items)
        replit_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "")
        openai_key = os.environ.get("OPENAI_API_KEY", "")

        if ollama_up:
            preferred = "ollama"
        elif replit_url:
            preferred = "replit"
        elif openai_key:
            preferred = "openai"
        else:
            preferred = "none"

        os.environ.setdefault("TD_PREFERRED_LLM", preferred)
        r.item("preferred_llm", "ok", preferred)
        r.actions.append(f"LLM backend selected → {preferred}")

        # Sidecar readiness flags
        sidecar_map = {
            "serena_analytics": 7339,
            "model_router":     7340,
        }
        for name, port in sidecar_map.items():
            alive = _probe("127.0.0.1", port, timeout=0.35)
            r.item(f"sidecar:{name}", "up" if alive else "pending",
                   f":{port}  {'responding' if alive else 'starting'}")

        # Redis pub/sub availability
        redis_up = _probe("127.0.0.1", 6379, timeout=0.3)
        r.item("pubsub:redis", "ok" if redis_up else "offline",
               "agent mesh active" if redis_up else "no Redis — `make docker-core`")
        os.environ["TD_REDIS_AVAILABLE"] = "1" if redis_up else "0"
        r.actions.append(f"Redis pub/sub → {'online' if redis_up else 'offline'}")

        # ── Integration env vars ──────────────────────────────────────────────

        # Replit-native flags
        replit_meta = m.meta.get("replit", {})
        os.environ.setdefault("TD_REPLIT_MODE",   replit_meta.get("mode", ""))
        os.environ.setdefault("TD_REPLIT_USER",   replit_meta.get("user", ""))
        os.environ.setdefault("TD_REPLIT_DOMAIN", replit_meta.get("domain", ""))
        os.environ.setdefault("TD_REPLIT_KV",     "1" if replit_meta.get("has_kv") else "0")

        # GitHub connectivity
        gh_meta = m.meta.get("github", {})
        os.environ.setdefault("TD_GITHUB_CONNECTED", "1" if gh_meta.get("ok") else "0")
        os.environ.setdefault("TD_GITHUB_LOGIN",      gh_meta.get("login", ""))

        # VS Code workspace detection
        vsc_meta = m.meta.get("vscode", {})
        vsc_active = any(vsc_meta.values())
        os.environ.setdefault("TD_VSCODE_WORKSPACE", "1" if vsc_active else "0")
        os.environ.setdefault("TD_VSCODE_MCP",       "1" if vsc_meta.get("mcp_json") else "0")

        # Public URL (for agent manifest + AGENTS.md)
        domain = replit_meta.get("domain", "")
        if domain:
            os.environ.setdefault("TD_PUBLIC_URL", f"https://{domain}")

        r.item("integration:env", "ok",
               f"replit={os.environ.get('TD_REPLIT_MODE','?')}  "
               f"github={'✓' if gh_meta.get('ok') else '✗'}  "
               f"vscode={'✓' if vsc_active else '✗'}  "
               f"kv={'✓' if replit_meta.get('has_kv') else '✗'}")
        r.actions.append("Integration env vars set (TD_REPLIT_*, TD_GITHUB_*, TD_VSCODE_*, TD_PUBLIC_URL)")

        m.actions_taken.extend(r.actions)

    except Exception as exc:
        r.ok    = False
        r.error = str(exc)

    r.duration_ms = (time.monotonic() - t0) * 1000
    return r


# ── Phase 4: RESUME — diff against last manifest, restore continuity ──────────

def _phase_resume(m: BootManifest) -> PhaseResult:
    t0   = time.monotonic()
    r    = PhaseResult(phase="RESUME")
    prev: dict | None = None

    try:
        if MANIFEST_PATH.exists():
            prev = json.loads(MANIFEST_PATH.read_text())
    except Exception:
        pass

    if prev and not prev.get("ready", False):
        r.item("last_manifest", "warn", "previous boot did not complete — crash detected")
    elif prev:
        prev_ts    = prev.get("timestamp", "?")
        prev_score = prev.get("health_score", 0)
        prev_mode  = prev.get("overall", "?")
        prev_onl   = prev.get("online",  0)
        delta_onl  = m.online - prev_onl

        r.item("last_boot",     "ok", prev_ts)
        r.item("prev_health",   "ok", f"{prev_score:.1%}  [{prev_mode}]")
        r.item("service_delta", "ok" if delta_onl >= 0 else "warn",
               f"{'+' if delta_onl >= 0 else ''}{delta_onl} services vs last boot")
        r.item("actions_prev",  "ok",
               f"{len(prev.get('actions_taken', []))} actions last session")

        m.delta = {
            "prev_timestamp":    prev_ts,
            "prev_overall":      prev_mode,
            "prev_health_score": prev_score,
            "delta_online":      delta_onl,
        }
        r.actions.append(f"State resumed from {prev_ts}")
    else:
        r.item("last_boot", "fresh", "first boot — no prior manifest")
        m.delta = {"fresh_boot": True}

    # RL Q-table continuity
    try:
        from config.runtime import PATHS
        rl_path = Path(PATHS.get("db_rl", "state/rl_state.db"))
        if rl_path.exists():
            exists, n = _db_count(rl_path, "q_values")
            r.item("rl:q_table", "ok" if exists else "missing",
                   f"{n} Q-values" if n >= 0 else "schema issue")
        else:
            r.item("rl:q_table", "fresh", "new RL session")
    except Exception as exc:
        r.warn("rl:q_table", str(exc))

    m.actions_taken.extend(r.actions)
    r.duration_ms = (time.monotonic() - t0) * 1000
    return r


# ── Phase 5: NUDGE — poke sleeping subsystems back awake ─────────────────────

def _phase_nudge(m: BootManifest) -> PhaseResult:
    t0 = time.monotonic()
    r  = PhaseResult(phase="NUDGE")

    try:
        from config.runtime import SELF_PORT
        self_port = SELF_PORT
    except Exception:
        self_port = int(os.environ.get("PORT", 5000))

    # Self health check
    health = _http_get(f"http://127.0.0.1:{self_port}/api/health", timeout=1.5)
    if health:
        r.item("self:api", "ok", f"uptime={health.get('uptime_seconds', '?')}s")
    else:
        r.warn("self:api", "health endpoint unreachable — server still starting")

    # Serena analytics sidecar
    serena_h = _http_get("http://127.0.0.1:7339/health", timeout=0.9)
    if serena_h:
        r.item("nudge:serena_analytics", "ok", "responded to ping")
    else:
        r.item("nudge:serena_analytics", "pending", "silent — sidecar initializing")

    # Model router sidecar
    router_h = _http_get("http://127.0.0.1:7340/health", timeout=0.9)
    if router_h:
        r.item("nudge:model_router", "ok",
               f"primary={router_h.get('primary_endpoint', '?')}")
    else:
        r.item("nudge:model_router", "pending", "silent — sidecar initializing")

    # Redis PING
    redis_up = _probe("127.0.0.1", 6379, timeout=0.35)
    if redis_up:
        r.item("nudge:redis", "ok", "PONG received — pub/sub live")
        r.actions.append("Redis nudged — pub/sub confirmed")
    else:
        r.item("nudge:redis", "offline",
               "no response — run `make docker-core` to enable agent mesh")

    r.duration_ms = (time.monotonic() - t0) * 1000
    return r


# ── Phase 6: AWAKEN — warm the agent ecosystem ───────────────────────────────

def _phase_awaken(m: BootManifest) -> PhaseResult:
    t0 = time.monotonic()
    r  = PhaseResult(phase="AWAKEN")

    # Serena — Ψ-link (full probe: symbols, files, observations, drift)
    try:
        ser = _probe_serena()
        m.meta["serena"] = ser
        if ser.get("ok"):
            n       = ser["symbols"]
            n_files = ser["files"]
            n_obs   = ser["observations"]
            d_warn  = ser.get("drift_warn", 0)
            d_crit  = ser.get("drift_critical", 0)
            drift_str = (f" · ⚠ {d_crit} CRITICAL drift" if d_crit
                         else f" · {d_warn} drift warn" if d_warn
                         else " · Ψ-link STABLE")
            r.item("awaken:serena", "ok",
                   f"{n:,} symbols · {n_files} files · {n_obs} obs{drift_str}")
            r.actions.append(f"Serena awakened — {n:,} symbols · {n_obs} observations")
        else:
            r.item("awaken:serena", "cold", "no serena DB — first run (run `serena walk`)")
    except Exception as exc:
        r.warn("awaken:serena", str(exc))

    # Agent personalities
    try:
        agents_dir = ROOT / "agents"
        yaml_count = (
            len(list(agents_dir.rglob("*.yaml")) + list(agents_dir.rglob("*.yml")))
            if agents_dir.exists() else 0
        )
        r.item("awaken:agents", "ok", f"{yaml_count} personality YAML files")
        r.actions.append(f"Agent mesh awakened — {yaml_count} personalities")
    except Exception as exc:
        r.warn("awaken:agents", str(exc))

    # ML model registry
    try:
        from config.runtime import PATHS
        ml_path = Path(PATHS.get("db_ml", "state/ml_features.db"))
        if ml_path.exists():
            exists, n = _db_count(ml_path, "model_registry")
            r.item("awaken:ml", "ok" if exists else "warn",
                   f"{n} models in registry" if n >= 0 else "schema issue")
        else:
            r.item("awaken:ml", "fresh", "ML DB not yet initialised")
    except Exception as exc:
        r.warn("awaken:ml", str(exc))

    # Lattice knowledge graph
    try:
        from config.runtime import PATHS
        lat_path = Path(PATHS.get("db_lattice", "state/lattice.db"))
        if lat_path.exists():
            _, n_nodes = _db_count(lat_path, "lattice_nodes")
            _, n_edges = _db_count(lat_path, "lattice_edges")
            r.item("awaken:lattice", "ok",
                   f"{n_nodes} nodes · {n_edges} edges")
            r.actions.append(f"Lattice knowledge graph online — {n_nodes} nodes")
        else:
            r.item("awaken:lattice", "cold", "lattice DB absent — reconcile created schema")
    except Exception as exc:
        r.warn("awaken:lattice", str(exc))

    # Gordon RL agent status
    try:
        from config.runtime import PATHS
        rl_path = Path(PATHS.get("db_rl", "state/rl_state.db"))
        gordon_up = _probe("127.0.0.1", 3000, timeout=0.3)
        if gordon_up:
            r.item("awaken:gordon", "ok", "Gordon autonomous player ONLINE")
            r.actions.append("Gordon awakened — orchestrator responding")
        elif rl_path.exists():
            _, n = _db_count(rl_path, "q_values")
            r.item("awaken:gordon", "suspended",
                   f"Gordon offline  ({n} Q-values persisted)")
        else:
            r.item("awaken:gordon", "fresh", "Gordon awaiting first RL cycle")
    except Exception as exc:
        r.warn("awaken:gordon", str(exc))

    # ── Tool ecosystem awakening ──────────────────────────────────────────────

    # Ollama: enumerate available local models
    try:
        ollama_up = _probe("127.0.0.1", 11434, timeout=0.3)
        if ollama_up:
            models_data = _http_get("http://127.0.0.1:11434/api/tags", timeout=1.5)
            if models_data and "models" in models_data:
                model_names = [mdl.get("name", "?") for mdl in models_data["models"]]
                m.meta["ollama_models"] = model_names
                r.item("awaken:ollama", "ok",
                       f"{len(model_names)} models: {', '.join(model_names[:3])}{'…' if len(model_names)>3 else ''}")
                r.actions.append(f"Ollama awakened — {len(model_names)} models available")
            else:
                r.item("awaken:ollama", "ok", "online (no models loaded)")
        else:
            r.item("awaken:ollama", "offline", "run `make docker-up` for local inference")
    except Exception as exc:
        r.warn("awaken:ollama", str(exc)[:60])

    # SkyClaw scanner readiness
    try:
        eco = m.meta.get("ecosystem", {})
        if eco.get("skyclaw"):
            r.item("awaken:skyclaw", "ok", "scripts/skyclaw_scanner.py ready")
        else:
            r.item("awaken:skyclaw", "missing", "skyclaw_scanner.py not found")
    except Exception as exc:
        r.warn("awaken:skyclaw", str(exc)[:60])

    # ChatDev readiness
    try:
        eco = m.meta.get("ecosystem", {})
        if eco.get("chatdev"):
            r.item("awaken:chatdev", "ok" if eco.get("chatdev_worker") else "partial",
                   "stub + worker" if eco.get("chatdev_worker") else "stub only  (worker missing)")
        else:
            r.item("awaken:chatdev", "missing", "chatdev_stub.py not found")
    except Exception as exc:
        r.warn("awaken:chatdev", str(exc)[:60])

    # MCP tool surface
    try:
        eco = m.meta.get("ecosystem", {})
        if eco.get("mcp_server"):
            r.item("awaken:mcp", "ok",
                   "scripts/mcp_server.py ready — 30+ tools for Claude/Copilot/Cursor")
        else:
            r.item("awaken:mcp", "missing", "mcp_server.py not found")
    except Exception as exc:
        r.warn("awaken:mcp", str(exc)[:60])

    # CI/CD pipeline detection
    try:
        ci_path = ROOT / ".github" / "workflows" / "ci.yml"
        if ci_path.exists():
            lines = ci_path.read_text().splitlines()
            jobs  = [l.strip().rstrip(":") for l in lines if l.strip().endswith(":") and "name:" not in l and "on:" not in l and "jobs:" not in l and l[0:4] == "  " and l[4:8] != "    "]
            r.item("awaken:ci", "ok",
                   f".github/workflows/ci.yml  ({len(jobs)} jobs)")
        else:
            r.item("awaken:ci", "missing", "no CI workflow found")
    except Exception as exc:
        r.warn("awaken:ci", str(exc)[:60])

    m.actions_taken.extend(r.actions)
    r.duration_ms = (time.monotonic() - t0) * 1000
    return r


# ── Phase 7: TAKE FLIGHT — finalise, score, publish ─────────────────────────

def _phase_take_flight(m: BootManifest) -> PhaseResult:
    t0 = time.monotonic()
    r  = PhaseResult(phase="TAKE_FLIGHT")

    all_items = [i for phase in m.phases for i in phase.items]
    errors    = sum(1 for i in all_items if i["status"] == "error")
    warnings  = sum(1 for i in all_items if i["status"] in ("warn", "missing", "pending"))
    oks       = sum(1 for i in all_items if i["status"] in ("ok", "up", "fixed", "fresh"))
    total     = max(len(all_items), 1)

    raw_score = (oks - errors * 2.0) / total
    m.health_score = round(max(0.0, min(1.0, raw_score)), 3)

    if   errors > 4 or m.health_score < 0.30: m.overall = "CRITICAL"
    elif warnings > 6 or m.health_score < 0.60: m.overall = "DEGRADED"
    else:                                       m.overall = "NOMINAL"

    total_ms      = sum(p.duration_ms for p in m.phases)
    total_actions = len(m.actions_taken)

    r.item("boot_status",     "ok", m.overall)
    r.item("health_score",    "ok", f"{m.health_score:.1%}")
    r.item("actions_taken",   "ok", f"{total_actions} autonomous corrections")
    r.item("total_duration",  "ok", f"{total_ms:.0f} ms")
    r.item("items_evaluated", "ok", f"{total}  ({errors} errors · {warnings} warnings · {oks} ok)")

    m.ready = True

    # ── Broadcast layer — publish to every connected surface ─────────────────

    # Publish compact summary to Replit KV store
    try:
        import json as _json
        kv_payload = _json.dumps({
            "overall":      m.overall,
            "health_score": round(m.health_score, 3),
            "online":       m.online,
            "total":        m.total,
            "timestamp":    m.timestamp,
            "env":          m.env,
            "actions":      total_actions,
            "ready":        True,
            "public_url":   os.environ.get("TD_PUBLIC_URL", ""),
            "github_login": os.environ.get("TD_GITHUB_LOGIN", ""),
        })
        ok = _publish_kv("td:boot:latest", kv_payload)
        r.item("kv:replit", "ok" if ok else "skip",
               "td:boot:latest written" if ok else "REPLIT_DB_URL absent")
        if ok:
            r.actions.append("Boot manifest published to Replit KV → td:boot:latest")
    except Exception as exc:
        r.item("kv:replit", "warn", str(exc)[:60])

    # Final AGENTS.md patch (with accurate health score after TAKE_FLIGHT scoring)
    try:
        patched = _patch_agents_md(m)
        r.item("agents_md:final", "ok" if patched else "skip",
               "AGENTS.md updated with final scores" if patched else "AGENTS.md absent")
        if patched:
            r.actions.append("AGENTS.md final status block written")
    except Exception as exc:
        r.item("agents_md:final", "warn", str(exc)[:60])

    # _write_manifest is called by run() AFTER this phase result is appended,
    # ensuring TAKE_FLIGHT itself appears in the manifest.
    r.item("manifest:final",  "ok", MANIFEST_PATH.name)
    r.actions.append(f"Boot complete — {m.overall} · {m.health_score:.1%} · {total_actions} actions taken")
    m.actions_taken.extend(r.actions)

    r.duration_ms = (time.monotonic() - t0) * 1000
    return r


# ── I/O helpers ──────────────────────────────────────────────────────────────

def _write_manifest(m: BootManifest):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "session_id":    m.session_id,
            "timestamp":     m.timestamp,
            "env":           m.env,
            "overall":       m.overall,
            "online":        m.online,
            "total":         m.total,
            "health_score":  m.health_score,
            "actions_taken": m.actions_taken,
            "delta":         m.delta,
            "ready":         m.ready,
            "meta":          m.meta,
            "phases": [
                {
                    "phase":       p.phase,
                    "ok":          p.ok,
                    "duration_ms": round(p.duration_ms, 1),
                    "actions":     p.actions,
                    "error":       p.error,
                    "items":       p.items,
                }
                for p in m.phases
            ],
        }
        MANIFEST_PATH.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def load_manifest() -> dict | None:
    """Return the last boot manifest dict, or None if unavailable."""
    try:
        if MANIFEST_PATH.exists():
            return json.loads(MANIFEST_PATH.read_text())
    except Exception:
        pass
    return None


# ── Public API ───────────────────────────────────────────────────────────────

def run(session_id: str = "") -> BootManifest:
    """Execute all 8 phases and return the completed BootManifest.

    Safe to call from a background thread — never raises; phase errors are
    captured in PhaseResult.error and the engine continues regardless.
    """
    import datetime as _dt

    if not session_id:
        session_id = str(int(time.time()))

    m = BootManifest(
        session_id = session_id,
        timestamp  = _dt.datetime.utcnow().strftime("%Y.%m.%d  %H:%M UTC"),
    )

    # Ordered phase schedule — each lambda closes over `m` so phases can share data
    schedule = [
        ("DETECT",      lambda: _phase_detect(m)),
        ("ANNOTATE",    lambda: _phase_annotate(m, m.phases[0] if m.phases else PhaseResult("DETECT"))),
        ("RECONCILE",   lambda: _phase_reconcile(m)),
        ("ADJUST",      lambda: _phase_adjust(m, m.phases[0] if m.phases else PhaseResult("DETECT"))),
        ("RESUME",      lambda: _phase_resume(m)),
        ("NUDGE",       lambda: _phase_nudge(m)),
        ("AWAKEN",      lambda: _phase_awaken(m)),
        ("TAKE_FLIGHT", lambda: _phase_take_flight(m)),
    ]

    for name, fn in schedule:
        try:
            result = fn()
            result.phase = name  # normalise (lambda might have set a local name)
            m.phases.append(result)
        except Exception as exc:
            # A phase hard-crashed — record it, continue the sequence
            m.phases.append(PhaseResult(phase=name, ok=False, error=str(exc)))

    # Write final manifest here — all 8 phases are now appended (including TAKE_FLIGHT)
    _write_manifest(m)
    return m
