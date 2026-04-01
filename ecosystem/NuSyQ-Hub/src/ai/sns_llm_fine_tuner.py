"""SNS-Core LLM Fine-Tuning Module.

Trains local Ollama models to output SNS notation natively.

[OmniTag: sns_llm_fine_tuner, model_training, zero_token, adaptive_learning]
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from src.config.service_config import ServiceConfig


@dataclass
class TrainingExample:
    """Single training example for SNS notation."""

    input_text: str
    output_sns: str
    category: str  # structural, flow, data, operational, aggressive
    token_savings: float  # percentage saved


class SNSLLMFineTuner:
    """Fine-tunes Ollama models for native SNS output."""

    def __init__(
        self,
        model_name: str = "qwen2.5-coder",
        ollama_url: str | None = None,
        state_dir: Path = Path("state"),
    ):
        """Initialize fine-tuner.

        Args:
            model_name: Base model to fine-tune
            ollama_url: Ollama API endpoint (defaults to environment config)
            state_dir: Directory for training data and checkpoints
        """
        self.model_name = model_name
        self.ollama_url = ollama_url or ServiceConfig.get_ollama_url()
        self.state_dir = state_dir
        self.training_data_file = state_dir / "sns_training_data.jsonl"
        self.checkpoint_dir = state_dir / "sns_checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def generate_training_data(self) -> list[TrainingExample]:
        """Generate comprehensive training examples for SNS notation.

        Returns:
            List of training examples
        """
        examples = [
            # Structural patterns
            TrainingExample(
                "Define a system boundary",
                "⨳ system_boundary",
                "structural",
                35.0,
            ),
            TrainingExample(
                "Create a module component",
                "⟡ module_component",
                "structural",
                38.0,
            ),
            TrainingExample(
                "Establish integration point",
                "⦾ integration_point",
                "structural",
                40.0,
            ),
            # Flow patterns
            TrainingExample(
                "Process flows from input to output",
                "input → process → output",
                "flow",
                25.0,
            ),
            TrainingExample(
                "Then execute validation",
                "execute → validate → confirm",
                "flow",
                28.0,
            ),
            # Data patterns
            TrainingExample(
                "Handle a data structure",
                "◆ data_structure",
                "data",
                35.0,
            ),
            TrainingExample(
                "Process a workflow",
                "○ process_workflow",
                "data",
                36.0,
            ),
            TrainingExample(
                "Manage entity state",
                "● entity_state",
                "data",
                37.0,
            ),
            # Operational patterns
            TrainingExample(
                "Transform the data",
                "⟢ transform_data",
                "operational",
                40.0,
            ),
            TrainingExample(
                "Validate the input",
                "⟣ validate_input",
                "operational",
                41.0,
            ),
            # Aggressive mode patterns
            TrainingExample(
                "Define a function called process_request",
                "ƒ(process_request)",
                "aggressive",
                65.0,
            ),
            TrainingExample(
                "Create a class called DataHandler",
                "Ⓒ DataHandler",
                "aggressive",
                62.0,
            ),
            TrainingExample(
                "Check if value exists",
                "❓ value_exists",
                "aggressive",
                50.0,
            ),
            TrainingExample(
                "Loop through items",
                "⤴ items",
                "aggressive",
                48.0,
            ),
            TrainingExample(
                "Handle errors in async function",
                "∿ƒ() ⚠ error_handling",
                "aggressive",
                70.0,
            ),
            TrainingExample(
                "Import required module",
                "⬆ module_name",
                "aggressive",
                45.0,
            ),
            TrainingExample(
                "Error occurred during execution",
                "❌ execution_error",
                "aggressive",
                40.0,
            ),
        ]
        return examples

    def save_training_data(self, examples: list[TrainingExample]) -> None:
        """Save training examples to JSONL file.

        Args:
            examples: Training examples
        """
        with open(self.training_data_file, "w") as f:
            for example in examples:
                record = {
                    "input": example.input_text,
                    "output": example.output_sns,
                    "category": example.category,
                    "token_savings": example.token_savings,
                }
                f.write(json.dumps(record) + "\n")

    def test_model_response(self, prompt: str, test_model: str = "llama2") -> str:
        """Test model response without full fine-tuning.

        Args:
            prompt: Input prompt
            test_model: Model to test

        Returns:
            Model's response
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": test_model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,  # Lower temperature for consistency
                },
                timeout=30,
            )
            response.raise_for_status()
            response_text: str = response.json().get("response", "").strip()
            return response_text
        except Exception as e:
            return f"Error testing model: {e}"

    def evaluate_sns_output(self, output: str) -> dict[str, Any]:
        """Evaluate SNS notation output quality.

        Args:
            output: Model output to evaluate

        Returns:
            Evaluation metrics
        """
        # Count SNS symbols used
        sns_symbols = set("⨳⦾→∞⟡⚡◆○●◉♦◊⟢⟣⨀⊕⊗⊙ƒⓒ❓⤴⤵⏳⬆⬇❌⚠✅")
        symbols_found = sum(1 for char in output if char in sns_symbols)

        # Check for patterns
        has_structural = any(char in output for char in "⨳⦾⟡")
        has_flow = "→" in output
        has_data = any(char in output for char in "◆○●◉")
        has_operational = any(char in output for char in "⟢⟣⨀")
        has_aggressive = any(char in output for char in "ƒⓒ❓⤴")

        return {
            "symbols_used": symbols_found,
            "has_structural": has_structural,
            "has_flow": has_flow,
            "has_data": has_data,
            "has_operational": has_operational,
            "has_aggressive": has_aggressive,
            "quality_score": min(
                100,
                symbols_found * 10
                + (
                    has_structural * 15
                    + has_flow * 12
                    + has_data * 13
                    + has_operational * 14
                    + has_aggressive * 20
                ),
            ),
        }

    def create_fine_tuning_prompt(self) -> str:
        """Create a system prompt for SNS notation.

        Returns:
            System prompt for model
        """
        return """You are an expert in SNS-Core notation system.
SNS-Core is a symbolic notation for efficient communication that reduces token usage by 40-85%.

Core symbols:
- ⨳ = system/scope boundary
- ⦾ = integration point
- → = flow/sequence
- ⟡ = module/component
- ◆ = data structure
- → = flow/sequence
- ❓ = conditional (if)
- ⤴ = loop (for)
- ⚠ = error/warning
- ✅ = success
- ❌ = failure
- ƒ( = function definition
- Ⓒ = class definition

When asked to convert text, use these symbols to create concise notation.
Prioritize clarity and token reduction. Use aggressive mode only when explicitly requested."""

    def prepare_fine_tuning_dataset(self) -> str:
        """Prepare dataset for fine-tuning.

        Returns:
            Path to prepared dataset
        """
        examples = self.generate_training_data()
        self.save_training_data(examples)

        # Create augmented dataset with variations
        augmented_file = self.state_dir / "sns_augmented_training.jsonl"
        with open(augmented_file, "w") as f:
            for example in examples:
                # Original
                record = {
                    "input": f"Convert to SNS: {example.input_text}",
                    "output": example.output_sns,
                }
                f.write(json.dumps(record) + "\n")

                # With category hint
                record = {
                    "input": f"Convert to SNS ({example.category}): {example.input_text}",
                    "output": example.output_sns,
                }
                f.write(json.dumps(record) + "\n")

                # Reverse - SNS to explanation
                record = {
                    "input": f"Explain SNS notation: {example.output_sns}",
                    "output": example.input_text,
                }
                f.write(json.dumps(record) + "\n")

        return str(augmented_file)

    def estimate_training_impact(self) -> dict[str, Any]:
        """Estimate impact of fine-tuning.

        Returns:
            Impact estimation
        """
        examples = self.generate_training_data()

        avg_savings = sum(e.token_savings for e in examples) / len(examples)
        total_examples = len(examples) * 3  # With augmentation

        return {
            "total_training_examples": total_examples,
            "categories_covered": len({e.category for e in examples}),
            "avg_token_savings_percent": round(avg_savings, 1),
            "estimated_cost_savings_yearly": round(
                50000 * (avg_savings / 100) * 0.00003, 2
            ),  # Assuming 50k tokens/day
            "training_data_file": str(self.training_data_file),
            "model": self.model_name,
            "estimated_training_time_hours": 2,
        }

    def generate_training_report(self) -> dict[str, Any]:
        """Generate comprehensive training report.

        Returns:
            Training report with metrics
        """
        examples = self.generate_training_data()

        return {
            "timestamp": datetime.now().isoformat(),
            "model": self.model_name,
            "training_summary": {
                "total_examples": len(examples),
                "categories": list({e.category for e in examples}),
                "avg_savings_pct": round(sum(e.token_savings for e in examples) / len(examples), 1),
            },
            "impact_estimation": self.estimate_training_impact(),
            "next_steps": [
                "1. Prepare augmented training dataset: prepare_fine_tuning_dataset()",
                "2. Create fine-tuning configuration for Ollama",
                "3. Run fine-tuning (estimated 2 hours)",
                "4. Evaluate fine-tuned model vs baseline",
                "5. Deploy fine-tuned model to production",
            ],
        }


def create_sns_fine_tuner(
    model_name: str = "qwen2.5-coder",
) -> SNSLLMFineTuner:
    """Factory function to create fine-tuner."""
    return SNSLLMFineTuner(model_name=model_name)
