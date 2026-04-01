"""Tiny CLI for the NuSyQ spine (opt-in)."""

import argparse
import logging

from . import eventlog, registry, router, state

logger = logging.getLogger(__name__)


def _status() -> None:
    st = state.read_state()
    events = eventlog.read_events(10)
    logger.info("NuSyQ Spine status")
    logger.info("state: %s", st)
    logger.info("recent events: %s", len(events))


def _snapshot() -> None:
    s = state.snapshot_state()
    logger.info("Wrote snapshot: %s", s.get("timestamp"))


def _find(query: str) -> None:
    res = registry.REGISTRY.find(query)
    logger.info(f"Found {len(res)} capabilities for '{query}'")
    for r in res:
        logger.info(r)


def _run(cmd: str) -> None:
    res = router.ROUTER.run_tool(cmd)
    logger.info(res)


def _register(name: str, path: str, force: bool = False) -> None:
    # Three-Before-New enforcement: require no matches unless --force
    matches = registry.REGISTRY.find(name)
    if matches and not force:
        logger.info(f"Found {len(matches)} similar capabilities. Use --force to register anyway.")
        for m in matches[:5]:
            logger.info(" -", m.get("name"), m.get("meta", {}).get("path"))
        return
    meta = {"path": path, "example": f"python {path}", "tags": ["manual"]}
    registry.REGISTRY.register(name, meta)
    logger.info(f"Registered capability: {name}")


def _agent_run(goal: str) -> None:
    # Minimal agent runner: map simple goals to deterministic tools when possible
    matches = registry.REGISTRY.find(goal)
    if matches:
        # pick first candidate and run its example
        cmd = matches[0]["meta"].get("example")
        logger.info(f"Routing goal to tool: {matches[0]['name']} -> {cmd}")
        res = router.ROUTER.run_tool(cmd)
        logger.info(res)
        return
    # fallback: echo the goal (agent tier not implemented yet)
    logger.info("No deterministic tool found — echoing goal (agent flow TBD)")
    res = router.ROUTER.run_tool(f"echo Agent goal: {goal}")
    logger.info(res)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="nusyq")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("status")
    sub.add_parser("snapshot")
    f = sub.add_parser("find")
    f.add_argument("query")
    r = sub.add_parser("run")
    r.add_argument("cmd")
    reg = sub.add_parser("register")
    reg.add_argument("name")
    reg.add_argument("path")
    reg.add_argument("--force", action="store_true")
    a = sub.add_parser("agent")
    a.add_argument("run")
    a.add_argument("goal")

    args = p.parse_args(argv)
    if args.cmd == "status":
        _status()
    elif args.cmd == "snapshot":
        _snapshot()
    elif args.cmd == "find":
        _find(args.query)
    elif args.cmd == "run":
        _run(args.cmd)
    elif args.cmd == "register":
        _register(args.name, args.path, force=args.force)
    elif args.cmd == "agent":
        if getattr(args, "run", None):
            _agent_run(args.goal)
        else:
            logger.info("agent subcommands: run <goal>")
    else:
        p.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
