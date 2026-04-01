#!/usr/bin/env python3
"""CLI for Serena, the convergence layer."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

try:
    import typer
except ImportError as exc:  # pragma: no cover - operator-facing failure path
    raise SystemExit("Typer is required for scripts/serena_cli.py") from exc

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from agents.serena.serena_agent import SerenaAgent
from core.agent_bus import AgentBus

app = typer.Typer(add_completion=True, no_args_is_help=True)


def _agent(repo_root: Path) -> SerenaAgent:
    return SerenaAgent(repo_root=repo_root.resolve())


def _emit_json(payload: object) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command()
def ask(
    query: str,
    repo_root: Path = typer.Option(
        Path("."), "--repo-root", help="Repository root to inspect."
    ),
) -> None:
    """Ask Serena a question about the codebase."""
    typer.echo(_agent(repo_root).ask(query))


@app.command()
def locate(
    symbol: str,
    kind: str = typer.Option(
        "", "--kind", help="Optional kind filter: function, class, module, variable."
    ),
    repo_root: Path = typer.Option(
        Path("."), "--repo-root", help="Repository root to inspect."
    ),
) -> None:
    """Locate a symbol precisely in Serena's index."""
    agent = _agent(repo_root)
    typer.echo(agent.find(symbol, kind=kind or None))


@app.command()
def find(
    symbol: str,
    kind: str = typer.Option(
        "", "--kind", help="Optional kind filter: function, class, module, variable."
    ),
    repo_root: Path = typer.Option(
        Path("."), "--repo-root", help="Repository root to inspect."
    ),
) -> None:
    """Find a symbol using Serena's native vocabulary."""
    agent = _agent(repo_root)
    typer.echo(agent.find(symbol, kind=kind or None))


@app.command()
def grep(
    pattern: str,
    repo_root: Path = typer.Option(
        Path("."), "--repo-root", help="Repository root to inspect."
    ),
    scope: str = typer.Option(
        "", "--scope", help="Optional path prefix to narrow search."
    ),
    limit: int = typer.Option(
        20, "--limit", min=1, help="Maximum number of results to print."
    ),
    fallback_to_index: bool = typer.Option(
        True,
        "--fallback-to-index/--no-fallback-to-index",
        help="Use Serena's index if ripgrep is unavailable or returns no hits.",
    ),
) -> None:
    """Run a fast repo search, with optional Serena index fallback."""
    cwd = repo_root.resolve()
    rg_cmd = ["rg", "-n", "--no-heading", pattern]
    if scope:
        rg_cmd.append(scope)

    try:
        result = subprocess.run(  # nosec B603
            rg_cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=10,
        )
        if result.returncode in (0, 1):
            lines = [line for line in result.stdout.splitlines() if line.strip()]
            if lines:
                typer.echo("\n".join(lines[:limit]))
                return
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        typer.echo("[SERENA] rg timed out; falling back to indexed search.")

    if not fallback_to_index:
        raise typer.Exit(code=1)

    agent = _agent(cwd)
    results = (
        agent.memory.search_scoped(pattern, scope or "", limit=limit)
        if scope
        else agent.memory.search(pattern, limit=limit)
    )
    if not results:
        typer.echo(f"[SERENA] ∅ — No matches for '{pattern}'.")
        raise typer.Exit(code=1)

    for row in results[:limit]:
        typer.echo(
            f"{row.get('path','?')}:{row.get('lineno','?')} {row.get('kind','?')} {row.get('name','')}".rstrip()
        )


@app.command()
def task(
    recipient: str,
    task: str,
    repo_root: Path = typer.Option(
        Path("."), "--repo-root", help="Repository root to inspect."
    ),
    context: str = typer.Option("", "--context", help="Additional task context."),
    priority: str = typer.Option("P1", "--priority", help="Task priority label."),
    personal: bool = typer.Option(
        False, "--personal", help="Send directly to the agent's personal channel."
    ),
    wait: bool = typer.Option(
        False, "--wait", help="Wait for a response on the CLI agent's personal channel."
    ),
    timeout_s: int = typer.Option(
        15, "--timeout", min=1, help="Seconds to wait for a mesh response."
    ),
) -> None:
    """Send a mesh task to another agent."""
    repo_root = repo_root.resolve()
    bus = AgentBus(
        "serena-cli",
        capabilities=["task_dispatch"],
        tags=["mesh", "cli"],
        description="Serena CLI mesh dispatcher",
    )
    bus.register(metadata={"cwd": str(repo_root)})
    bus.heartbeat(extra={"cwd": str(repo_root)})
    channel = (
        AgentBus.personal_channel(recipient) if personal else AgentBus.TASK_CHANNEL
    )
    envelope = bus.request(
        recipient,
        {
            "task": task,
            "context": context,
            "priority": priority,
            "target": recipient,
        },
        channel=channel,
        tags=["task", "cli"],
    )
    result = {
        "sent": True,
        "id": envelope.id,
        "channel": channel,
        "recipient": recipient,
    }

    if not wait:
        _emit_json(result)
        return

    if not bus.connected or bus._redis is None:
        result["error"] = "Redis unavailable; cannot wait for mesh response."
        _emit_json(result)
        raise typer.Exit(code=1)

    pubsub = bus._redis.pubsub()
    reply_channel = AgentBus.personal_channel("serena-cli")
    pubsub.subscribe(reply_channel)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        item = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        if not item or not item.get("data"):
            time.sleep(0.1)
            continue
        try:
            payload = json.loads(item["data"])
        except Exception:
            continue
        if payload.get("correlation_id") == envelope.id:
            result["response"] = payload
            _emit_json(result)
            return

    result["timeout"] = timeout_s
    _emit_json(result)
    raise typer.Exit(code=1)


@app.command()
def status(
    repo_root: Path = typer.Option(
        Path("."), "--repo-root", help="Repository root to inspect."
    ),
) -> None:
    """Show Serena's current state."""
    _emit_json(_agent(repo_root).get_status())


@app.command()
def explain(
    target: str,
    repo_root: Path = typer.Option(
        Path("."), "--repo-root", help="Repository root to inspect."
    ),
) -> None:
    """Explain a file or file:symbol target from Serena's index."""
    path, _, name = target.partition(":")
    typer.echo(_agent(repo_root).explain(path, name=name or None))


@app.command()
def listen(
    repo_root: Path = typer.Option(
        Path("."), "--repo-root", help="Repository root to inspect."
    ),
) -> None:
    """Run Serena's mesh listener loop."""
    agent = _agent(repo_root)
    typer.echo("[SERENA] mesh listener online")
    agent.listen_on_mesh()


@app.command("fast-walk")
def fast_walk(
    repo_root: Path = typer.Option(
        Path("."), "--repo-root", help="Repository root to inspect."
    ),
    clear: bool = typer.Option(
        False, "--clear", help="Clear the current index before walking."
    ),
) -> None:
    """Run Serena's scoped walk and print index stats."""
    agent = _agent(repo_root)
    if clear:
        agent.memory.clear_index()
    _emit_json(agent.fast_walk())


if __name__ == "__main__":
    app()
