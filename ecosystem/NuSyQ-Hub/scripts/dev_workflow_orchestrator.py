#!/usr/bin/env python3
"""Developer Workflow Orchestrator for NuSyQ.

Watches the repo for changes and runs a configurable pipeline of actions
(lint, test, build, docs, snapshots). Uses asyncio for concurrency,
watchdog (if available) for file watching, and Typer (if available) for CLI.
Falls back to polling + argparse when extras are missing.

Usage examples:
  python scripts/dev_workflow_orchestrator.py run --config config/dev_orchestrator.json --once
  python scripts/dev_workflow_orchestrator.py run --config config/dev_orchestrator.json --watch

Config file example (JSON):
{
  "root": ".",
  "watch_dirs": ["src", "scripts"],
  "debounce_seconds": 1.0,
  "concurrency_limit": 2,
  "context": {"env": "dev"},
  "tasks": [
    {"name": "ruff", "plugin": "python", "script": "scripts/run_ruff.py", "args": [], "triggers": ["*.py"], "always": false},
    {"name": "pytest", "plugin": "python", "script": "scripts/run_pytest.py", "args": ["-q"], "triggers": ["*.py"], "always": false},
    {"name": "npm-test", "plugin": "node", "script": "web/run_tests.js", "args": [], "triggers": ["web/**/*"], "always": false}
  ]
}
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # optional
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except Exception:  # pragma: no cover
    Observer = None
    FileSystemEventHandler = object

try:  # optional
    import typer
except Exception:  # pragma: no cover
    typer = None


# ----------------------------------------------------------------------------
# Models & plugin interfaces
# ----------------------------------------------------------------------------


@dataclass
class TaskResult:
    name: str
    returncode: int
    output: str
    error: str
    duration: float


class Plugin:
    name: str = "base"

    async def run(self, ctx: Context, **kwargs) -> TaskResult:
        raise NotImplementedError


@dataclass
class Context:
    root: Path
    config: dict[str, Any]
    env: dict[str, str] = field(default_factory=lambda: dict(os.environ))


# ----------------------------------------------------------------------------
# Built-in plugins
# ----------------------------------------------------------------------------


class PythonScriptPlugin(Plugin):
    name = "python"

    async def run(self, ctx: Context, script: str, args: list[str] | None = None) -> TaskResult:
        args = args or []
        script_path = (ctx.root / script).resolve()
        if not script_path.exists():
            raise FileNotFoundError(f"Python script {script_path} not found")
        start = time.perf_counter()
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=ctx.env,
        )
        cfg_bytes = json.dumps(ctx.config).encode()
        stdout, stderr = await proc.communicate(input=cfg_bytes)
        duration = time.perf_counter() - start
        return TaskResult(
            name=f"python:{script}",
            returncode=proc.returncode,
            output=stdout.decode(),
            error=stderr.decode(),
            duration=duration,
        )


class NodeScriptPlugin(Plugin):
    name = "node"

    async def run(self, ctx: Context, script: str, args: list[str] | None = None) -> TaskResult:
        args = args or []
        script_path = (ctx.root / script).resolve()
        if not script_path.exists():
            raise FileNotFoundError(f"Node script {script_path} not found")
        start = time.perf_counter()
        proc = await asyncio.create_subprocess_exec(
            "node",
            str(script_path),
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=ctx.env,
        )
        cfg_bytes = json.dumps(ctx.config).encode()
        stdout, stderr = await proc.communicate(input=cfg_bytes)
        duration = time.perf_counter() - start
        return TaskResult(
            name=f"node:{script}",
            returncode=proc.returncode,
            output=stdout.decode(),
            error=stderr.decode(),
            duration=duration,
        )


PLUGIN_REGISTRY: dict[str, Plugin] = {
    "python": PythonScriptPlugin(),
    "node": NodeScriptPlugin(),
}


def register_plugin(plugin: Plugin) -> None:
    if plugin.name in PLUGIN_REGISTRY:
        raise ValueError(f"Plugin {plugin.name} already registered")
    PLUGIN_REGISTRY[plugin.name] = plugin


# ----------------------------------------------------------------------------
# Task runner & scheduler
# ----------------------------------------------------------------------------


@dataclass
class Task:
    name: str
    plugin: str
    script: str
    args: list[str]
    triggers: list[str]
    always: bool = False


@dataclass
class OrchestratorConfig:
    tasks: list[Task]
    watch_dirs: list[str]
    debounce_seconds: float = 1.0
    concurrency_limit: int = 2


class Orchestrator:
    def __init__(self, ctx: Context, cfg: OrchestratorConfig):
        self.ctx = ctx
        self.cfg = cfg
        self._queue: asyncio.Queue[Task] = asyncio.Queue()
        self._stop_event = asyncio.Event()

    def _match_triggers(self, path: Path) -> list[Task]:
        matches: list[Task] = []
        for task in self.cfg.tasks:
            if task.always:
                matches.append(task)
                continue
            for pat in task.triggers:
                if path.match(pat):
                    matches.append(task)
                    break
        return matches

    async def _task_worker(self) -> None:
        while not self._stop_event.is_set():
            task = await self._queue.get()
            try:
                plugin = PLUGIN_REGISTRY[task.plugin]
            except KeyError:
                print(f"[WARN] Unknown plugin {task.plugin}, skipping")
                self._queue.task_done()
                continue
            print(f"[INFO] Running {task.name} via {task.plugin}")
            result = await plugin.run(self.ctx, script=task.script, args=task.args)
            print(f"[RESULT] {result.name} rc={result.returncode} dur={result.duration:.2f}s")
            if result.output:
                print(result.output)
            if result.error:
                print(result.error, file=sys.stderr)
            self._queue.task_done()

    async def enqueue(self, task: Task) -> None:
        await self._queue.put(task)

    async def stop(self) -> None:
        self._stop_event.set()

    async def run(self) -> None:
        workers = [asyncio.create_task(self._task_worker()) for _ in range(self.cfg.concurrency_limit)]
        await self._stop_event.wait()
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    def _on_fs_event(self, event) -> None:  # type: ignore
        path = Path(getattr(event, "src_path", ""))
        if not path:
            return
        for task in self._match_triggers(path):
            asyncio.run_coroutine_threadsafe(self.enqueue(task), asyncio.get_event_loop())

    def start_watch(self) -> None:
        if Observer is None:
            print("[WARN] watchdog not installed, using polling loop")
            loop = asyncio.get_event_loop()
            self._poll_task = loop.create_task(self._poll_loop())
            return
        handler = FileSystemEventHandler()
        handler.on_created = self._on_fs_event
        handler.on_modified = self._on_fs_event
        observer = Observer()
        for d in self.cfg.watch_dirs:
            observer.schedule(handler, d, recursive=True)
        observer.start()
        print(f"[INFO] Watching: {', '.join(self.cfg.watch_dirs)}")

    async def _poll_loop(self) -> None:
        mtimes: dict[str, float] = {}
        while not self._stop_event.is_set():
            for d in self.cfg.watch_dirs:
                for p in Path(d).rglob("*"):
                    try:
                        mtime = p.stat().st_mtime
                    except FileNotFoundError:
                        continue
                    key = str(p)
                    if mtimes.get(key) != mtime:
                        mtimes[key] = mtime
                        for task in self._match_triggers(p):
                            await self.enqueue(task)
            await asyncio.sleep(self.cfg.debounce_seconds)


# ----------------------------------------------------------------------------
# Config loading
# ----------------------------------------------------------------------------


def load_context_and_config(path: str) -> (Context, OrchestratorConfig):
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file {path} not found")
    with cfg_path.open() as f:
        raw = json.load(f)
    ctx = Context(root=Path(raw.get("root", ".")), config=raw.get("context", {}))
    tasks = [
        Task(
            name=e["name"],
            plugin=e["plugin"],
            script=e["script"],
            args=e.get("args", []),
            triggers=e.get("triggers", []),
            always=e.get("always", False),
        )
        for e in raw.get("tasks", [])
    ]
    cfg = OrchestratorConfig(
        tasks=tasks,
        watch_dirs=[str(Path(d).resolve()) for d in raw.get("watch_dirs", ["./"])],
        debounce_seconds=raw.get("debounce_seconds", 1.0),
        concurrency_limit=raw.get("concurrency_limit", 2),
    )
    return ctx, cfg


# ----------------------------------------------------------------------------
# CLI setup
# ----------------------------------------------------------------------------


def _build_argparse_cli(factory: Callable[[Context, OrchestratorConfig], Orchestrator]):
    parser = argparse.ArgumentParser(description="NuSyQ Developer Workflow Orchestrator")
    parser.add_argument("--config", "-c", default="config/dev_orchestrator.json")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--watch", action="store_true")
    return parser


def build_cli(factory: Callable[[Context, OrchestratorConfig], Orchestrator]):
    if typer is None:
        parser = _build_argparse_cli(factory)
        args = parser.parse_args()
        ctx, cfg = load_context_and_config(args.config)
        orch = factory(ctx, cfg)
        loop = asyncio.get_event_loop()
        if args.once:
            for t in cfg.tasks:
                if t.always:
                    loop.run_until_complete(orch.enqueue(t))
            loop.run_until_complete(orch._queue.join())
            return None
        if args.watch:
            orch.start_watch()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(orch.stop()))
            loop.run_until_complete(orch.run())
            return None
        parser.print_help()
        return None

    app = typer.Typer(help="NuSyQ Developer Workflow Orchestrator")

    @app.command()
    def run(
        config: str = typer.Option("config/dev_orchestrator.json", help="Path to config JSON"),
        once: bool = typer.Option(False, help="Run tasks marked always and exit"),
        watch: bool = typer.Option(False, help="Watch for changes and run tasks"),
    ):
        print("[orchestrator] starting (typer path)")
        ctx, cfg = load_context_and_config(config)
        orch = factory(ctx, cfg)
        loop = asyncio.get_event_loop()
        if once:
            for t in cfg.tasks:
                if t.always:
                    loop.run_until_complete(orch.enqueue(t))
            loop.run_until_complete(orch._queue.join())
            return
        if watch:
            orch.start_watch()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(orch.stop()))
            loop.run_until_complete(orch.run())
        else:
            typer.echo("Nothing to do. Use --once or --watch.")

    return app


def orchestrator_factory(ctx: Context, cfg: OrchestratorConfig) -> Orchestrator:
    return Orchestrator(ctx, cfg)


if __name__ == "__main__":
    cli = build_cli(orchestrator_factory)
    if typer and isinstance(cli, typer.Typer):
        cli()
