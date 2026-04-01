# CONCEPT / Katana-Keeper Integration

**Role in ecosystem:** Machine-health oracle. Read keeper state before any heavy workflow.

## Why Keeper First

Keeper provides deterministic, sub-second pressure signals (disk %, CPU %, RAM %, contention)
that NuSyQ-Hub cannot derive on its own. Running a healing cycle or ChatDev task against a
machine at 95% disk or critical CPU will fail or degrade the output. Keeper preflight prevents
that.

## Quick Preflight (CLI)

```powershell
# 1. Full snapshot — read this first
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File C:\CONCEPT\tools\keeper-bridge.ps1 snapshot

# 2. Pressure score (0-100; ok <40, info 40-59, warning 60-79, critical ≥80)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File C:\CONCEPT\keeper.ps1 score

# 3. Advisor recommendation (docker-prune, clean-temp, demote-dev-processes, none)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File C:\CONCEPT\keeper.ps1 advisor

# 4. Maintenance audit (disk, Docker, WSL, temp, downloads)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File C:\CONCEPT\keeper.ps1 think
```

**Decision rule:**
- `score < 60` and `advisor == "none"` → proceed
- `score 60-79` (warning) → proceed with caution; consider `keeper optimize` first
- `score ≥ 80` (critical) → **defer heavy work**; run `keeper optimize` or `keeper maintain`

## Quick Preflight (MCP)

If your client has the `katana-keeper` MCP server mounted (see `Dev-Mentor/.vscode/mcp.json`):

```
keeper_snapshot     ← always first
keeper_score        ← check pressure
keeper_advisor      ← get recommendation
keeper_think        ← check disk/Docker if disk pressure is elevated
```

## Python Helper

Drop this into any NuSyQ-Hub script before heavy operations:

```python
import subprocess, json, sys

def keeper_preflight(warn_threshold: int = 60, block_threshold: int = 80) -> dict:
    """Run keeper score + advisor preflight. Returns result dict."""
    try:
        out = subprocess.check_output(
            ["pwsh", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", r"C:\CONCEPT\tools\keeper-bridge.ps1", "snapshot"],
            timeout=15, text=True
        )
        snap = json.loads(out)
        score_val = snap.get("brain", {}).get("score", {}).get("score", 0) or 0
        status = snap.get("brain", {}).get("score", {}).get("status", "ok") or "ok"
    except Exception as e:
        print(f"[keeper_preflight] Could not reach Keeper: {e}", file=sys.stderr)
        return {"reachable": False, "score": 0, "status": "unknown", "proceed": True}

    proceed = score_val < block_threshold
    if score_val >= warn_threshold:
        print(f"[keeper_preflight] Pressure {status} (score={score_val}). "
              f"{'BLOCKED — run keeper optimize/maintain first.' if not proceed else 'Caution advised.'}")

    return {"reachable": True, "score": score_val, "status": status, "proceed": proceed}


# Usage:
if __name__ == "__main__":
    pf = keeper_preflight()
    if not pf["proceed"]:
        sys.exit(1)   # caller defers or escalates
```

## Agent Registration

CONCEPT is registered in [`data/agents/agents.json`](../data/agents/agents.json) as:

```json
{
  "name": "katana-keeper",
  "role": "performance_cultivator",
  "manifest": "https://github.com/KiloMusician/CONCEPT_SAMURAI/blob/main/agent_manifest.json"
}
```

## Keeper → NuSyQ-Hub Signal Map

| Keeper field | NuSyQ-Hub relevance |
|---|---|
| `brain.score.score` | Gate heavy tasks (block ≥80) |
| `brain.score.status` | ok / info / warning / critical |
| `brain.advisor.recommended` | `docker-prune` → run before docker-compose; `clean-temp` → free space |
| `brain.advisor.safe_to_apply` | false in gaming/heavy-gaming mode — defer then |
| `disk.pct_used` | >90% → defer ChatDev, Ollama pull, docker build |
| `mode` | `heavy-gaming` / `gaming` → do not run maintenance |
| `cpu_percent` | >80% → delay LLM inference tasks |
| `free_mem_mb` | <2048 → avoid spawning multiple agents |

## Recommended Integration Points

| Script | Where to add preflight |
|---|---|
| `scripts/healing_orchestrator.py` | Top of `cmd_heal()` — check score before writing files |
| `scripts/start_nusyq.py` | Before `doctor --auto-heal` |
| `scripts/submit_orchestrator_test_task.py` | Before submitting heavy tasks |
| Any `docker compose up` wrapper | Before spawning containers |

## Repo Links

- CONCEPT: `C:/CONCEPT` — `https://github.com/KiloMusician/CONCEPT_SAMURAI`
- Agent manifest: `C:/CONCEPT/agent_manifest.json`
- MCP server: `C:/CONCEPT/tools/keeper-mcp.ps1`
- Bridge: `C:/CONCEPT/tools/keeper-bridge.ps1`
