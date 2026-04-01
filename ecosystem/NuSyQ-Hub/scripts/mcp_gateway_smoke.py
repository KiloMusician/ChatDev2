#!/usr/bin/env python3
"""Smoke test for llm_route and swarm_run via MCP server (in-process)."""

from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.integration.universal_llm_gateway import UniversalLLMGateway  # type: ignore
from src.orchestration.swarm_router import get_swarm_router  # type: ignore


def main() -> None:
    gw = UniversalLLMGateway(dry_run=True)
    print("== llm_route dry-run ==")
    res = gw.route_request("Say hello", capability_tags=["code"])
    print(res)

    router = get_swarm_router()
    print("== swarm_run sequential (dry-run) ==")
    seq = router.run_sequential(
        [
            {"prompt": "Step 1: summarize apples", "capability_tags": ["code"]},
            {"prompt": "Step 2: summarize oranges", "capability_tags": ["code"]},
        ]
    )
    print(seq)

    print("== swarm_run vote (dry-run) ==")
    vote = router.run_vote(
        [
            {"prompt": "Option A: cats", "capability_tags": ["code"]},
            {"prompt": "Option B: dogs", "capability_tags": ["code"]},
        ]
    )
    print(vote)


if __name__ == "__main__":
    sys.path.insert(0, ".")
    main()
