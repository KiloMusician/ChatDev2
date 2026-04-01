#!/usr/bin/env python3
"""CLI entry point for the Copilot enhancement bridge."""

# OmniTag: {
#     "purpose": "file_systematically_tagged",
#     "tags": ["Python"],
#     "category": "auto_tagged",
#     "evolution_stage": "v1.0"
# }

import argparse
import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))


def _build_compact_response(result: dict, file_path: str) -> dict:
    """Trim large bridge payloads for terminal/UI consumption."""
    suggestions = result.get("suggestions", [])
    related_files = result.get("related_files", [])
    return {
        "timestamp": result.get("timestamp"),
        "file_path": file_path,
        "suggestions": suggestions,
        "kilo_enhancements": result.get("kilo_enhancements", {}),
        "related_files_count": len(related_files) if isinstance(related_files, list) else 0,
        "architecture_context": result.get("architecture_context", {}),
    }


def main() -> None:
    """Invoke the bridge and emit suggestions as JSON."""
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("file_path", nargs="?", default="")
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON response (recommended for terminal/VS Code output).",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=200000,
        help="Maximum file bytes to include in bridge input context.",
    )
    args = parser.parse_args()
    file_path = args.file_path
    content = ""
    if file_path and Path(file_path).is_file():
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            if args.max_bytes > 0:
                encoded = content.encode("utf-8")
                if len(encoded) > args.max_bytes:
                    content = encoded[: args.max_bytes].decode("utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            content = ""

    from src.integration.advanced_chatdev_copilot_integration import (
        CopilotEnhancementBridge,
    )

    bridge = CopilotEnhancementBridge()
    result = bridge.enhance_copilot_context(file_path, {"content": content})
    payload = _build_compact_response(result, file_path) if args.compact else result
    sys.stdout.write(json.dumps(payload))


if __name__ == "__main__":
    main()
