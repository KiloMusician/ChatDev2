"""Ecosystem status API — surfaces health of all NuSyQ repos running locally."""
from __future__ import annotations

import asyncio
import os
import subprocess
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/ecosystem", tags=["ecosystem"])

ECOSYSTEM_DIR = Path(__file__).resolve().parents[2] / "ecosystem"

SERVICES = [
    {
        "id": "chatdev",
        "name": "ChatDev 2.0 (DevAll)",
        "repo": "current",
        "url": "http://localhost:6400/health",
        "port": 6400,
        "type": "fastapi",
        "description": "Zero-code multi-agent orchestration platform. This repo.",
    },
    {
        "id": "dev-mentor",
        "name": "Dev-Mentor (Terminal Depths)",
        "repo": "Dev-Mentor",
        "url": "http://localhost:8008/api/manifest",
        "port": 8008,
        "type": "fastapi",
        "description": "Cyberpunk terminal RPG + multi-agent orchestration + CHUG engine.",
    },
    {
        "id": "concept-samurai",
        "name": "CONCEPT_SAMURAI",
        "repo": "CONCEPT_SAMURAI",
        "url": "http://localhost:3001/",
        "port": 3001,
        "type": "static",
        "description": "Concept docs, superpowers spec, and katana-keeper system orchestrator.",
    },
    {
        "id": "simulatedverse",
        "name": "SimulatedVerse",
        "repo": "SimulatedVerse",
        "url": "http://localhost:3000/api/health",
        "port": 3000,
        "type": "node",
        "description": "RimWorld-style AI simulation sandbox with agent patch-bay.",
    },
    {
        "id": "nusyq-hub",
        "name": "NuSyQ-Hub",
        "repo": "NuSyQ-Hub",
        "url": None,
        "port": None,
        "type": "cli",
        "description": "Quantum-inspired orchestration brain — runs in analysis/health CLI mode.",
    },
    {
        "id": "nusyq-ultimate",
        "name": "NuSyQ Ultimate",
        "repo": "NuSyQ_Ultimate",
        "url": None,
        "port": None,
        "type": "library",
        "description": "Multi-agent management layer: agent registry, adaptive timeouts, process tracking.",
    },
]


async def _probe(url: str, timeout: float = 2.0) -> Dict[str, Any]:
    """Probe a URL and return status info."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            return {"online": True, "status_code": r.status_code, "latency_ms": None}
    except Exception as e:
        return {"online": False, "error": str(e)[:80]}


_REPO_INFO_CACHE: Dict[str, Any] = {}
_REPO_INFO_TTL = 120  # seconds


def _repo_info(repo_id: str) -> Dict[str, Any]:
    """Get basic git info for a repo (cached for 2 minutes)."""
    now = time.time()
    cached = _REPO_INFO_CACHE.get(repo_id)
    if cached and now - cached["_ts"] < _REPO_INFO_TTL:
        return {k: v for k, v in cached.items() if k != "_ts"}

    repo_path = ECOSYSTEM_DIR / repo_id
    if not repo_path.exists():
        return {"cloned": False}
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=repo_path, stderr=subprocess.DEVNULL, timeout=3
        ).decode().strip()
        commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%h %s"],
            cwd=repo_path, stderr=subprocess.DEVNULL, timeout=3
        ).decode().strip()
        # Use `du` for fast disk usage (excludes .git)
        du_out = subprocess.check_output(
            ["du", "-s", "--exclude=.git", str(repo_path)],
            stderr=subprocess.DEVNULL, timeout=5
        ).decode().split()[0]
        size_mb = round(int(du_out) / 1024, 1)
        result: Dict[str, Any] = {
            "cloned": True,
            "branch": branch,
            "latest_commit": commit,
            "size_mb": size_mb,
        }
        _REPO_INFO_CACHE[repo_id] = {**result, "_ts": now}
        return result
    except Exception:
        return {"cloned": True}


def _nusyq_hub_health() -> Dict[str, Any]:
    """Read last NuSyQ-Hub health snapshot if available."""
    snap = Path("/tmp/nusyq_hub_health.txt")
    if snap.exists() and snap.stat().st_mtime > time.time() - 300:
        return {"snapshot": snap.read_text()[-1000:], "fresh": True}
    hub_snap = ECOSYSTEM_DIR / "NuSyQ-Hub" / "state" / "reports" / "spine_health_snapshot.json"
    if hub_snap.exists():
        try:
            return {"snapshot": hub_snap.read_text()[-500:], "fresh": False}
        except Exception:
            pass
    return {"snapshot": None, "fresh": False}


@router.get("/status")
async def ecosystem_status():
    """Return live health status of all NuSyQ ecosystem repos."""
    probes = []
    for svc in SERVICES:
        if svc["url"]:
            probes.append(_probe(svc["url"]))
        else:
            probes.append(asyncio.sleep(0, result={"online": None, "note": "cli/library mode"}))

    loop = asyncio.get_event_loop()
    repo_ids = [svc["repo"] if svc["repo"] != "current" else None for svc in SERVICES]
    repo_infos = await asyncio.gather(*[
        loop.run_in_executor(None, _repo_info, rid) if rid else asyncio.sleep(0, result={"cloned": True, "note": "this repo"})
        for rid in repo_ids
    ])
    results = await asyncio.gather(*probes)

    services_out = []
    for svc, probe, info in zip(SERVICES, results, repo_infos):
        entry = {**svc, "health": probe, "repo_info": info}
        if svc["id"] == "nusyq-hub":
            entry["hub_health"] = _nusyq_hub_health()
        services_out.append(entry)

    online = sum(1 for s in services_out if s["health"].get("online") is True)
    cli_mode = sum(1 for s in services_out if s["health"].get("online") is None)

    return {
        "summary": {
            "online": online,
            "cli_mode": cli_mode,
            "total": len(SERVICES),
        },
        "services": services_out,
        "ecosystem_dir": str(ECOSYSTEM_DIR),
    }


@router.post("/chug")
async def run_chug():
    """Run a CHUG cultivation cycle on the Dev-Mentor repo."""
    chug_path = ECOSYSTEM_DIR / "Dev-Mentor" / "chug_engine.py"
    if not chug_path.exists():
        return {"error": "chug_engine.py not found"}
    try:
        result = subprocess.run(
            ["python", str(chug_path), "--phase", "1"],
            cwd=str(ECOSYSTEM_DIR / "Dev-Mentor"),
            capture_output=True, text=True, timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-500:],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "CHUG phase timed out after 30s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/repos")
async def list_repos():
    """List all cloned ecosystem repos with basic file stats."""
    repos = []
    if not ECOSYSTEM_DIR.exists():
        return {"repos": []}
    for d in sorted(ECOSYSTEM_DIR.iterdir()):
        if not d.is_dir():
            continue
        info = _repo_info(d.name)
        info["name"] = d.name
        info["path"] = str(d)
        repos.append(info)
    return {"repos": repos}
