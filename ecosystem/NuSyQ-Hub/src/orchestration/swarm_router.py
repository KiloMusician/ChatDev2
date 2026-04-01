"""SwarmRouter facade over existing Agent/MCP registry (Phase 2).

Supports simple sequential, concurrent (simulated), map-reduce, and voting flows.
This is a lightweight orchestrator shim; actual agent execution can be plugged in later.
"""

from __future__ import annotations

import logging
from typing import Any

from src.integration.universal_llm_gateway import UniversalLLMGateway
from src.system.telemetry import log_span

logger = logging.getLogger(__name__)


class SwarmRouter:
    def __init__(self, gateway: UniversalLLMGateway | None = None) -> None:
        """Initialize SwarmRouter with gateway."""
        self.gateway = gateway or UniversalLLMGateway()

    def run_sequential(self, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """steps: list of {prompt, capability_tags?, model_hint?}."""
        results = []
        for step in steps:
            res = self.gateway.route_request(
                prompt=step.get("prompt", ""),
                model_hint=step.get("model_hint"),
                capability_tags=step.get("capability_tags", []),
            )
            results.append(res)
            if res.get("error"):
                break
        log_span(
            "swarm_sequential",
            {"steps": len(steps), "errors": [r for r in results if r.get("error")]},
        )
        return results

    def run_concurrent(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            self.gateway.route_request(
                prompt=t.get("prompt", ""),
                model_hint=t.get("model_hint"),
                capability_tags=t.get("capability_tags", []),
            )
            for t in tasks
        ]

    def run_vote(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        votes = self.run_concurrent(tasks)
        # Placeholder voting: pick first non-error
        winner = next((v for v in votes if not v.get("error")), votes[0] if votes else {})
        # Optional cross-model diff if two results present
        diffs = []
        if len(votes) >= 2:
            try:
                from src.system.safety import diff_responses

                diffs.append(
                    diff_responses(
                        votes[0].get("output", votes[0].get("echo", "")),
                        votes[1].get("output", votes[1].get("echo", "")),
                    )
                )
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)
        log_span(
            "swarm_vote",
            {
                "votes": len(votes),
                "winner_error": winner.get("error") if winner else None,
                "diffs": diffs,
            },
        )
        return {"winner": winner, "votes": votes}

    def run_map_reduce(
        self,
        map_tasks: list[dict[str, Any]],
        reduce_prompt: str,
        reduce_model_hint: str | None = None,
    ) -> dict[str, Any]:
        mapped = self.run_concurrent(map_tasks)
        summaries = [m.get("echo", "") for m in mapped if not m.get("error")]
        reduce_input = "\n".join(summaries)
        reduced = self.gateway.route_request(
            prompt=f"{reduce_prompt}\n\n{reduce_input}",
            model_hint=reduce_model_hint,
        )
        log_span(
            "swarm_map_reduce",
            {
                "maps": len(map_tasks),
                "reduce_error": reduced.get("error") if isinstance(reduced, dict) else None,
            },
        )
        return {"map": mapped, "reduce": reduced}


def get_swarm_router() -> SwarmRouter:
    return SwarmRouter()
