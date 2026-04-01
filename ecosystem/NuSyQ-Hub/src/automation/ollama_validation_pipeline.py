#!/usr/bin/env python3
"""Ollama Validation Pipeline.

Routes Ollama model outputs through SimulatedVerse agents:
- Zod: Schema validation and type checking
- Council: Multi-agent voting on outputs
- Redstone: Logic analysis

This provides proof-gated local AI development.
"""

import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from src.integration.simulatedverse_unified_bridge import \
    SimulatedVerseUnifiedBridge as SimulatedVerseBridge

logger = logging.getLogger(__name__)


class OllamaValidationPipeline:
    """Route Ollama outputs through SimulatedVerse validation agents."""

    def __init__(self) -> None:
        """Initialize OllamaValidationPipeline."""
        self.bridge = SimulatedVerseBridge()
        self.reports_dir = Path("data/ollama_validations")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Available fast Ollama models (from debug results)
        self.fast_models = [
            "phi3.5:latest",  # 3.8B, fastest
            "qwen2.5-coder:7b",  # 7B, code-focused
            "llama3.1:8b",  # 8B, chat/reasoning
        ]

        logger.info(" OLLAMA VALIDATION PIPELINE")
        logger.info(" Local AI → SimulatedVerse Proof-Gated Validation")
        logger.info("=" * 80 + "\n")

    def generate_with_ollama(self, model: str, prompt: str, timeout: int = 30) -> str | None:
        """Generate code with Ollama model."""
        logger.info(f"[OLLAMA] Generating with {model}...")
        logger.info(f"   Prompt: {prompt[:60]}...")

        try:
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore",
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                logger.info(f"   ✅ Generated: {len(output)} chars")
                return output
            logger.info("   ❌ Generation failed")
            return None

        except subprocess.TimeoutExpired:
            logger.info(f"   ⏱️  Timeout after {timeout}s")
            return None
        except Exception as e:
            logger.info(f"   ❌ Error: {e}")
            return None

    def validate_with_zod(self, code: str, model_source: str) -> dict | None:
        """Validate code with Zod agent (schema/type checking)."""
        logger.info("\n[ZOD] Validating code structure...")

        task_id = self.bridge.submit_task(
            agent_id="zod",
            content=f"Validate code from {model_source}",
            metadata={
                "code": code,
                "source_model": model_source,
                "validation_type": "schema_check",
            },
        )

        logger.info(f"   Task ID: {task_id}")

        result = self.bridge.check_result(task_id, timeout=30)

        if result:
            effects = result.get("result", {}).get("effects", {})
            state_delta = effects.get("stateDelta", {})

            logger.info("   ✅ Zod validation complete")
            return {
                "task_id": task_id,
                "validation": state_delta,
                "artifact": effects.get("artifactPath"),
            }
        logger.info("   ⚠️  Zod timeout")
        return None

    def vote_with_council(self, proposals: list[dict]) -> dict | None:
        """Submit multiple outputs to Council for voting."""
        logger.info("\n[COUNCIL] Voting on model outputs...")

        task_id = self.bridge.submit_task(
            agent_id="council",
            content=f"Vote on {len(proposals)} Ollama model outputs",
            metadata={"proposals": proposals, "vote_type": "quality_comparison"},
        )

        logger.info(f"   Task ID: {task_id}")

        result = self.bridge.check_result(task_id, timeout=30)

        if result:
            effects = result.get("result", {}).get("effects", {})
            state_delta = effects.get("stateDelta", {})

            logger.info("   ✅ Council voted")
            return {
                "task_id": task_id,
                "vote_results": state_delta,
                "artifact": effects.get("artifactPath"),
            }
        logger.info("   ⚠️  Council timeout")
        return None

    def analyze_with_redstone(self, code: str) -> dict | None:
        """Analyze logic patterns with Redstone agent."""
        logger.info("\n[REDSTONE] Analyzing logic patterns...")

        task_id = self.bridge.submit_task(
            agent_id="redstone",
            content="Analyze code logic patterns",
            metadata={"code": code, "analysis_type": "logic_flow"},
        )

        logger.info(f"   Task ID: {task_id}")

        result = self.bridge.check_result(task_id, timeout=30)

        if result:
            effects = result.get("result", {}).get("effects", {})
            state_delta = effects.get("stateDelta", {})

            logger.info("   ✅ Redstone analysis complete")
            return {
                "task_id": task_id,
                "analysis": state_delta,
                "artifact": effects.get("artifactPath"),
            }
        logger.info("   ⚠️  Redstone timeout")
        return None

    def run_validation_workflow(self, prompt: str, use_council: bool = False) -> dict:
        """Complete validation workflow.

        1. Generate with Ollama (multiple models if council voting)
        2. Validate with Zod
        3. Optionally vote with Council
        4. Analyze with Redstone.
        """
        logger.info(" OLLAMA VALIDATION WORKFLOW")
        logger.info("=" * 80 + "\n")

        logger.info(f"Prompt: {prompt}")
        logger.info(f"Council voting: {use_council}")

        results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "generations": [],
            "validations": [],
            "council_vote": None,
            "redstone_analysis": None,
        }

        # Step 1: Generate with Ollama model(s)
        if use_council:
            # Generate with multiple models for comparison
            models_to_use = self.fast_models[:2]  # Use 2 fastest models
            logger.info(f"[GENERATE] Using {len(models_to_use)} models for council voting")
        else:
            # Single model
            models_to_use = [self.fast_models[0]]  # Use fastest model
            logger.info(f"[GENERATE] Using single model: {models_to_use[0]}")

        proposals: list[Any] = []
        for model in models_to_use:
            code = self.generate_with_ollama(model, prompt)
            if code:
                results["generations"].append({"model": model, "code": code, "length": len(code)})

                # Prepare for council voting
                proposals.append(
                    {
                        "model": model,
                        "code": code,
                        "quality_score": len(code) / 100,  # Simple heuristic
                    },
                )

        if not results["generations"]:
            logger.info("\n❌ No successful generations")
            return results

        # Step 2: Validate with Zod (use first generation)
        first_gen = results["generations"][0]
        zod_result = self.validate_with_zod(first_gen["code"], first_gen["model"])
        if zod_result:
            results["validations"].append(zod_result)

        # Step 3: Council voting (if multiple models)
        if use_council and len(proposals) > 1:
            council_result = self.vote_with_council(proposals)
            if council_result:
                results["council_vote"] = council_result

        # Step 4: Redstone logic analysis (use first generation)
        redstone_result = self.analyze_with_redstone(first_gen["code"])
        if redstone_result:
            results["redstone_analysis"] = redstone_result

        # Save report
        report_file = self.reports_dir / f"validation_{int(time.time())}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        # Summary
        logger.info(" VALIDATION WORKFLOW COMPLETE")
        logger.info(f"\n✅ Generations: {len(results['generations'])}")
        logger.info(f"✅ Validations: {len(results['validations'])}")
        logger.info(f"✅ Council Vote: {'Yes' if results['council_vote'] else 'No'}")
        logger.info(f"✅ Redstone Analysis: {'Yes' if results['redstone_analysis'] else 'No'}")
        logger.info(f"✅ Report: {report_file}")
        logger.info("\n" + "=" * 80 + "\n")

        return results


def main() -> None:
    """Demo: Test Ollama validation pipeline."""
    pipeline = OllamaValidationPipeline()

    # Test 1: Single model with validation
    logger.info(" TEST 1: Single Model Validation")

    result1 = pipeline.run_validation_workflow(
        prompt="Write a Python function to calculate factorial. Just the code:",
        use_council=False,
    )

    # Test 2: Multi-model with council voting
    logger.info(" TEST 2: Multi-Model Council Voting")

    result2 = pipeline.run_validation_workflow(
        prompt="Write a Python function to reverse a string. Just the code:",
        use_council=True,
    )

    logger.info(" ALL TESTS COMPLETE")
    logger.info(f"\nTest 1: {len(result1['generations'])} generations")
    logger.info(
        f"Test 2: {len(result2['generations'])} generations, council vote: {bool(result2['council_vote'])}",
    )
    logger.info("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
