"""Council Consensus Synthesizer — Lightweight multi-agent response analysis.

Analyzes responses from multiple agents (collected by MjolnirProtocol.council())
and produces a structured consensus summary WITHOUT requiring another LLM call.

Uses Jaccard similarity on tokenized outputs to measure agreement, quality
scoring based on response status/timing/length, and selects the best
recommendation from the highest-quality response.

Usage:
    synthesizer = CouncilSynthesizer()
    result = synthesizer.synthesize(agent_responses)
    # result["consensus_level"] in ("strong", "moderate", "weak", "divergent")
"""

from __future__ import annotations

import re
from typing import Any


class CouncilSynthesizer:
    """Synthesize multi-agent council responses into consensus."""

    # Consensus thresholds (average pairwise Jaccard similarity)
    STRONG_THRESHOLD = 0.6
    MODERATE_THRESHOLD = 0.4
    WEAK_THRESHOLD = 0.2

    # Quality scoring parameters
    TIMING_PENALTY_MS = 30_000  # Responses >30s get reduced weight
    MIN_OUTPUT_LENGTH = 20  # Very short outputs get reduced weight

    def synthesize(self, agent_responses: dict[str, dict]) -> dict[str, Any]:
        """Analyze agent responses and produce consensus summary.

        Args:
            agent_responses: Dict mapping agent name → response dict.
                Each response has at minimum: {"status": str, "output": Any}
                Optional: {"timing_ms": float}

        Returns:
            {
                "consensus_level": "strong"|"moderate"|"weak"|"divergent",
                "confidence": float (0.0-1.0),
                "recommendation": str,
                "response_quality": {agent: float},
                "agreement_matrix": {agent_pair: float},
                "dissenting_views": [agent_name, ...],
                "agents_consulted": int,
                "agents_succeeded": int,
            }
        """
        if not agent_responses:
            return self._empty_result()

        # 1. Score each response's quality
        quality_scores = self._score_responses(agent_responses)

        # 2. Extract text outputs for successful responses
        text_outputs = self._extract_texts(agent_responses)

        # 3. Compute pairwise agreement
        agreement_matrix, avg_similarity = self._compute_agreement(text_outputs)

        # 4. Determine consensus level
        consensus_level = self._classify_consensus(avg_similarity)

        # 5. Select recommendation (highest quality response)
        recommendation = self._select_recommendation(agent_responses, quality_scores, text_outputs)

        # 6. Identify dissenting views
        dissenting = self._find_dissenting(text_outputs, recommendation)

        # 7. Compute overall confidence
        agents_succeeded = sum(1 for r in agent_responses.values() if r.get("status") == "ok")
        confidence = self._compute_confidence(
            avg_similarity, agents_succeeded, len(agent_responses)
        )

        result = {
            "consensus_level": consensus_level,
            "confidence": round(confidence, 3),
            "recommendation": recommendation,
            "response_quality": quality_scores,
            "agreement_matrix": agreement_matrix,
            "dissenting_views": dissenting,
            "agents_consulted": len(agent_responses),
            "agents_succeeded": agents_succeeded,
        }

        try:
            from src.system.agent_awareness import emit as _emit

            _lvl = "WARNING" if consensus_level == "divergent" else "INFO"
            _emit(
                "agents",
                f"Council: consensus={consensus_level} confidence={confidence:.2f}"
                f" agents={len(agent_responses)}/{agents_succeeded} dissenting={len(dissenting)}",
                level=_lvl,
                source="council_synthesizer",
            )
        except Exception:
            pass

        return result

    # ── Internal methods ────────────────────────────────────────────────────

    def _score_responses(self, responses: dict[str, dict]) -> dict[str, float]:
        """Score each response 0.0-1.0 based on status, timing, output length."""
        scores: dict[str, float] = {}
        for agent, resp in responses.items():
            status = resp.get("status", "error")
            if status != "ok":
                scores[agent] = 0.0
                continue

            score = 1.0

            # Timing penalty
            timing = resp.get("timing_ms")
            if timing is not None and timing > self.TIMING_PENALTY_MS:
                score *= 0.7

            # Output length penalty
            output_text = self._to_text(resp.get("output"))
            if len(output_text) < self.MIN_OUTPUT_LENGTH:
                score *= 0.5

            scores[agent] = round(score, 3)
        return scores

    def _extract_texts(self, responses: dict[str, dict]) -> dict[str, str]:
        """Extract text representations of successful responses."""
        texts: dict[str, str] = {}
        for agent, resp in responses.items():
            if resp.get("status") == "ok":
                texts[agent] = self._to_text(resp.get("output"))
        return texts

    @staticmethod
    def _to_text(output: Any) -> str:
        """Convert any output to text for comparison."""
        if output is None:
            return ""
        if isinstance(output, str):
            return output
        if isinstance(output, dict):
            # Extract meaningful text from dict outputs
            for key in ("output", "result", "text", "content", "response"):
                if key in output and isinstance(output[key], str):
                    return output[key]
            return str(output)
        return str(output)

    def _compute_agreement(self, texts: dict[str, str]) -> tuple[dict[str, float], float]:
        """Compute pairwise Jaccard similarity between agent outputs.

        Returns:
            (agreement_matrix, average_similarity)
        """
        agents = list(texts.keys())
        if len(agents) < 2:
            # Single agent or no agents → perfect self-agreement
            return {}, 1.0 if agents else 0.0

        matrix: dict[str, float] = {}
        similarities: list[float] = []

        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                a, b = agents[i], agents[j]
                sim = self._jaccard_similarity(texts[a], texts[b])
                key = f"{a}↔{b}"
                matrix[key] = round(sim, 3)
                similarities.append(sim)

        avg = sum(similarities) / len(similarities) if similarities else 0.0
        return matrix, avg

    @staticmethod
    def _jaccard_similarity(text_a: str, text_b: str) -> float:
        """Compute Jaccard similarity between two texts (word-level)."""
        # Tokenize: lowercase, split on non-alphanumeric
        tokens_a = set(re.findall(r"\w+", text_a.lower()))
        tokens_b = set(re.findall(r"\w+", text_b.lower()))

        if not tokens_a and not tokens_b:
            return 1.0  # Both empty → identical
        if not tokens_a or not tokens_b:
            return 0.0  # One empty → no similarity

        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union)

    def _classify_consensus(self, avg_similarity: float) -> str:
        """Map average similarity to consensus level."""
        if avg_similarity >= self.STRONG_THRESHOLD:
            return "strong"
        if avg_similarity >= self.MODERATE_THRESHOLD:
            return "moderate"
        if avg_similarity >= self.WEAK_THRESHOLD:
            return "weak"
        return "divergent"

    def _select_recommendation(
        self,
        responses: dict[str, dict],
        quality_scores: dict[str, float],
        texts: dict[str, str],
    ) -> str:
        """Select best response as recommendation."""
        if not texts:
            # All responses failed
            errors = [
                resp.get("output", resp.get("error", "unknown error"))
                for resp in responses.values()
            ]
            return f"All agents failed: {'; '.join(str(e) for e in errors)}"

        # Pick agent with highest quality score among those with text output
        best_agent = max(
            texts.keys(),
            key=lambda a: quality_scores.get(a, 0.0),
        )
        return texts[best_agent]

    def _find_dissenting(self, texts: dict[str, str], recommendation: str) -> list[str]:
        """Find agents whose output significantly differs from recommendation."""
        dissenting: list[str] = []
        for agent, text in texts.items():
            sim = self._jaccard_similarity(text, recommendation)
            if sim < 0.3:
                dissenting.append(agent)
        return dissenting

    @staticmethod
    def _compute_confidence(avg_similarity: float, succeeded: int, total: int) -> float:
        """Compute overall confidence score.

        Factors:
        - Agreement between agents (avg_similarity)
        - Success rate (succeeded / total)
        """
        if total == 0:
            return 0.0

        success_rate = succeeded / total
        # Weight: 60% agreement, 40% success rate
        return avg_similarity * 0.6 + success_rate * 0.4

    @staticmethod
    def _empty_result() -> dict[str, Any]:
        """Return result for empty input."""
        return {
            "consensus_level": "divergent",
            "confidence": 0.0,
            "recommendation": "No agents responded",
            "response_quality": {},
            "agreement_matrix": {},
            "dissenting_views": [],
            "agents_consulted": 0,
            "agents_succeeded": 0,
        }
