"""SNS-Core Integration Helper.

Connects SNS-Core notation system to NuSyQ-Hub for 41% token reduction.

[OmniTag: sns_core_helper, token_optimization, ai_communication, zero_token]
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# SNS-Core symbol mapping (from temp_sns_core/symbols.md)
SNS_SYMBOLS = {
    # Structural
    "⨳": "system/scope boundary",
    "⦾": "integration point",
    "→": "flow/sequence",
    "∞": "recursive/infinite",
    "⟡": "module/component",
    "⚡": "action/event",
    # Semantic
    "◆": "data structure",
    "○": "process",
    "●": "state",
    "◉": "entity",
    "♦": "configuration",
    "◊": "metadata",
    # Operational
    "⟢": "transform",
    "⟣": "validate",
    "⨀": "aggregate",
    "⊕": "compose",
    "⊗": "decompose",
    "⊙": "observe",
}


def convert_to_sns(text: str, aggressive: bool = False) -> tuple[str, dict[str, Any]]:
    """Convert natural language to SNS-Core notation.

    Args:
        text: Input text to convert
        aggressive: Use maximum compression (60-85% claimed reduction)

    Returns:
        (sns_text, metadata) where metadata includes token savings
    """
    sns_text = text
    replacements = []
    lowercase_text = text.lower()

    # === STRUCTURAL PATTERNS ===
    # System/scope boundaries
    patterns = [
        (r"\bsystem\s", "⨳ ", "system → ⨳"),
        (r"\bscope\s", "⨳ ", "scope → ⨳"),
        (r"\bintegration\s+point", "⦾", "integration point → ⦾"),
        (r"\bintegration\b", "⦾", "integration → ⦾"),
        (r"\bmodule\s", "⟡ ", "module → ⟡"),
        (r"\bcomponent\s", "⟡ ", "component → ⟡"),
    ]

    for pattern, replacement, label in patterns:
        if re.search(pattern, lowercase_text, re.IGNORECASE):
            sns_text = re.sub(pattern, replacement, sns_text, flags=re.IGNORECASE)
            if label not in replacements:
                replacements.append(label)

    # Flow/sequence patterns
    flow_patterns = [
        (r"\s+flow\s+", " → ", "flow → →"),
        (r"\s+then\s+", " → ", "then → →"),
        (r"\s+follows\s+", " → ", "follows → →"),
    ]

    for pattern, replacement, label in flow_patterns:
        if re.search(pattern, lowercase_text, re.IGNORECASE):
            sns_text = re.sub(pattern, replacement, sns_text, flags=re.IGNORECASE)
            if label not in replacements:
                replacements.append(label)

    # === DATA STRUCTURE PATTERNS ===
    data_patterns = [
        (r"\bdata\s+structure", "◆", "data structure → ◆"),
        (r"\bprocess\s", "○ ", "process → ○"),
        (r"\bstate\s", "● ", "state → ●"),
        (r"\bentity\s", "◉ ", "entity → ◉"),
        (r"\bconfiguration\s", "♦ ", "configuration → ♦"),
        (r"\bmetadata\s", "◊ ", "metadata → ◊"),
    ]

    for pattern, replacement, label in data_patterns:
        if re.search(pattern, lowercase_text, re.IGNORECASE):
            sns_text = re.sub(pattern, replacement, sns_text, flags=re.IGNORECASE)
            if label not in replacements:
                replacements.append(label)

    # === OPERATIONAL PATTERNS ===
    operational_patterns = [
        (r"\btransform", "⟢", "transform → ⟢"),
        (r"\bvalidate\s", "⟣ ", "validate → ⟣"),
        (r"\baggregate", "⨀", "aggregate → ⨀"),
        (r"\bagregate", "⨀", "aggregate → ⨀"),
        (r"\bcompose\s", "⊕ ", "compose → ⊕"),
        (r"\bdecompose\s", "⊗ ", "decompose → ⊗"),
        (r"\bobserve\s", "⊙ ", "observe → ⊙"),
    ]

    for pattern, replacement, label in operational_patterns:
        if re.search(pattern, lowercase_text, re.IGNORECASE):
            sns_text = re.sub(pattern, replacement, sns_text, flags=re.IGNORECASE)
            if label not in replacements:
                replacements.append(label)

    # === AGGRESSIVE MODE: Advanced Patterns (60-85% claimed) ===
    if aggressive:
        # Function/method compression
        aggressive_patterns = [
            (r"\b(function|method|def)\s+\w+\s*\(", "ƒ(", "function definition → ƒ("),
            (r"\bclass\s+\w+", "Ⓒ", "class definition → Ⓒ"),
            (r"\breturn\s", "↩ ", "return → ↩"),
            (r"\bimport\s+", "⬆ ", "import → ⬆"),
            (r"\bfrom\s+", "⬇ ", "from → ⬇"),
            (r"\basync\s+def", "∿ƒ", "async def → ∿ƒ"),
            (r"\bawait\s+", "⏳ ", "await → ⏳"),
            (r"\btry\s*:", "⚠:", "try → ⚠:"),
            (r"\bexcept\s+", "❌ ", "except → ❌"),
            (r"\bif\s+", "❓ ", "if → ❓"),
            (r"\bfor\s+", "⤴ ", "for → ⤴"),
            (r"\bwhile\s+", "⤵ ", "while → ⤵"),
        ]

        for pattern, replacement, label in aggressive_patterns:
            if re.search(pattern, lowercase_text, re.IGNORECASE):
                sns_text = re.sub(pattern, replacement, sns_text, flags=re.IGNORECASE)
                if label not in replacements:
                    replacements.append(label)

        # Common word compression (aggressive only - reduces clarity)
        word_replacements = [
            (r"\berror\b", "❌", "error → ❌"),
            (r"\bwarning\b", "⚠", "warning → ⚠"),
            (r"\bsuccess\b", "✅", "success → ✅"),
            (r"\binput\b", "⬅", "input → ⬅"),
            (r"\boutput\b", "➡", "output → ➡"),
            (r"\bstart\b", "▶", "start → ▶"),
            (r"\bstop\b", "⏹", "stop → ⏹"),
            (r"\bpause\b", "⏸", "pause → ⏸"),
        ]

        for word, symbol, label in word_replacements:
            if re.search(word, lowercase_text, re.IGNORECASE):
                sns_text = re.sub(word, symbol, sns_text, flags=re.IGNORECASE)
                if label not in replacements:
                    replacements.append(label)

    # Calculate token savings (approximate)
    original_tokens = estimate_tokens(text)
    sns_tokens = estimate_tokens(sns_text)
    savings_pct = (
        ((original_tokens - sns_tokens) / original_tokens * 100) if original_tokens > 0 else 0
    )

    metadata = {
        "original_length": len(text),
        "sns_length": len(sns_text),
        "original_tokens_est": original_tokens,
        "sns_tokens_est": sns_tokens,
        "savings_pct": round(savings_pct, 1),
        "replacements": replacements,
        "mode": "aggressive" if aggressive else "normal",
    }

    return sns_text, metadata


def estimate_tokens(text: str) -> int:
    """Rough token estimate (GPT-style, ~4 chars per token)."""
    return len(text) // 4


def load_sns_symbols() -> dict[str, str]:
    """Load SNS-Core symbol definitions from temp_sns_core/."""
    # Try to load from temp_sns_core if available
    symbols_file = Path(__file__).parents[2] / "temp_sns_core" / "symbols.md"
    if symbols_file.exists():
        # Parse symbols.md (simple format: "⨳ - system/scope")
        try:
            symbols = {}
            with open(symbols_file, encoding="utf-8") as f:
                for line in f:
                    if " - " in line:
                        parts = line.strip().split(" - ", 1)
                        if len(parts) == 2:
                            symbol, meaning = parts
                            symbols[symbol.strip()] = meaning.strip()

            # Ensure we always include canonical SNS symbols
            merged_symbols = {**SNS_SYMBOLS, **symbols}
            return merged_symbols
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)

    # Fallback to hardcoded
    return SNS_SYMBOLS


def analyze_token_savings(text: str) -> dict[str, Any]:
    """Analyze potential token savings for a text block.

    Returns comprehensive metrics for SNS-Core conversion.
    """
    sns_text, metadata = convert_to_sns(text, aggressive=False)

    # Also try aggressive mode
    sns_aggressive, metadata_agg = convert_to_sns(text, aggressive=True)

    return {
        "original": {
            "text": text,
            "length": len(text),
            "tokens_est": estimate_tokens(text),
        },
        "sns_normal": {
            "text": sns_text,
            "length": len(sns_text),
            "tokens_est": metadata["sns_tokens_est"],
            "savings_pct": metadata["savings_pct"],
            "replacements": metadata["replacements"],
        },
        "sns_aggressive": {
            "text": sns_aggressive,
            "length": len(sns_aggressive),
            "tokens_est": metadata_agg["sns_tokens_est"],
            "savings_pct": metadata_agg["savings_pct"],
            "replacements": metadata_agg["replacements"],
        },
        "validated_reduction": 41.0,  # From temp_sns_core/README.md
        "claimed_reduction": "60-85%",  # From docs
    }


def format_sns_report(analysis: dict[str, Any]) -> str:
    """Format SNS-Core analysis as readable report."""
    report = []
    report.append("🔣 SNS-Core Token Analysis")
    report.append("=" * 50)

    orig = analysis["original"]
    normal = analysis["sns_normal"]
    agg = analysis["sns_aggressive"]

    report.append("\n📊 Original Text:")
    report.append(f"  Length: {orig['length']} chars")
    report.append(f"  Tokens: ~{orig['tokens_est']}")

    report.append("\n🔹 SNS Normal Mode:")
    report.append(f"  Length: {normal['length']} chars ({normal['length'] - orig['length']:+d})")
    report.append(f"  Tokens: ~{normal['tokens_est']} ({normal['savings_pct']:+.1f}%)")
    report.append(f"  Replacements: {len(normal['replacements'])}")

    report.append("\n⚡ SNS Aggressive Mode:")
    report.append(f"  Length: {agg['length']} chars ({agg['length'] - orig['length']:+d})")
    report.append(f"  Tokens: ~{agg['tokens_est']} ({agg['savings_pct']:+.1f}%)")
    report.append(f"  Replacements: {len(agg['replacements'])}")

    report.append(f"\n✅ Validated: {analysis['validated_reduction']}% reduction")
    report.append(f"📈 Claimed: {analysis['claimed_reduction']} reduction")

    return "\n".join(report)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_text = " ".join(sys.argv[1:])
    else:
        test_text = "The system integration point processes data structure flow through state validation then aggregates results"

    analysis = analyze_token_savings(test_text)
    logger.info(format_sns_report(analysis))
    logger.info("\n📝 Sample Conversion:")
    logger.info(f"  Original: {analysis['original']['text']}")
    logger.info(f"  SNS:      {analysis['sns_normal']['text']}")
