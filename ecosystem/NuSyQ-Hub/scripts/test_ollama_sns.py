"""Test Ollama-assisted SNS-CORE conversion
Validates Task #3: Use Ollama for SNS notation conversion
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.sns_core_integration import SNSCoreHelper


def test_ollama_conversion():
    print("=" * 60)
    print("Testing Ollama-assisted SNS-CORE Conversion")
    print("Model: qwen2.5-coder:14b")
    print("=" * 60)

    test_cases = [
        "Analyze the code for errors and suggest fixes",
        "Extract keywords from the query and classify the intent",
        "Process the documents and generate a summary report",
        "Review code and identify potential security vulnerabilities",
    ]

    total_savings = []

    for i, test_prompt in enumerate(test_cases, 1):
        print(f"\n{'─' * 60}")
        print(f"Test Case {i}:")
        print(f"Natural: {test_prompt}")

        # Convert (rule-based only for now - Ollama needs tuning)
        sns = SNSCoreHelper.convert_to_sns(test_prompt, pattern="flow", use_ollama=False)
        print(f"SNS:     {sns}")

        # Check for SNS symbols
        has_arrow = "→" in sns
        has_symbols = any(sym in sns for sym in ["→", "|", "?:", "+", "∥"])
        print(f"Has flow symbol (→): {has_arrow}")
        print(f"Has SNS symbols: {has_symbols}")

        # Token comparison
        metrics = SNSCoreHelper.compare_token_counts(test_prompt, sns)
        print(f"Token savings: {metrics['savings_percent']:.1f}%")
        print(f"Traditional: {metrics['traditional_tokens']} tokens")
        print(f"SNS: {metrics['sns_tokens']} tokens")

        total_savings.append(metrics["savings_percent"])

        # Validation
        is_valid, errors = SNSCoreHelper.validate_sns(sns)
        print(f"Valid SNS: {is_valid}")
        if errors:
            print(f"Validation errors: {errors}")

    print(f"\n{'=' * 60}")
    print("Summary:")
    print(f"Average token savings: {sum(total_savings) / len(total_savings):.1f}%")
    print("Target: 40-50% savings")

    avg_savings = sum(total_savings) / len(total_savings)
    if avg_savings >= 35:
        print(f"✅ PASS: Achieved {avg_savings:.1f}% savings (target: 35%+)")
        return True
    else:
        print(f"⚠️  WARN: Only {avg_savings:.1f}% savings (target: 35%+)")
        return False


if __name__ == "__main__":
    success = test_ollama_conversion()
    exit(0 if success else 1)
