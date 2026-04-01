"""
Orchestration runner - concise

Runs a small set of consensus experiments for each repository to produce
starter recommendations. This is a local-only runner and will not call
ChatDev or perform network operations other than invoking local
`ollama run` via the orchestrator.

Usage:
    python orchestration_run_concise.py

Outputs:
- Reports/Orchestration/consensus_<repo>_<timestamp>.json
"""

import json
from datetime import datetime
from pathlib import Path

from .consensus_orchestrator import ConsensusOrchestrator

# Model constants
QWEN_CODER_7B = "qwen2.5-coder:7b"
CODELLAMA_7B = "codellama:7b"
QWEN_CODER_14B = "qwen2.5-coder:14b"
GEMMA2_9B = "gemma2:9b"
STARCODER2_15B = "starcoder2:15b"

ROOT = Path(__file__).parent
REPORTS = ROOT / "Reports" / "Orchestration"
REPORTS.mkdir(parents=True, exist_ok=True)

repos = {
    "NuSyQ-Hub": (
        "Create core orchestration modules for multi-agent coordination in Python"
    ),
    "SimulatedVerse": (
        "Scaffold a dual-interface server (express) and React UI integration"
    ),
    "NuSyQ": ("Design a REST API for MCP server with endpoints for agent coordination"),
}

models_map = {
    "NuSyQ-Hub": [QWEN_CODER_7B, CODELLAMA_7B],
    "SimulatedVerse": [QWEN_CODER_7B, STARCODER2_15B],
    "NuSyQ": [QWEN_CODER_14B, GEMMA2_9B],
}

for repo, task in repos.items():
    models = models_map.get(repo, ["qwen2.5-coder:7b"])
    orchestrator = ConsensusOrchestrator(models)
    print(f"\n=== Running consensus for {repo} ===")
    result = orchestrator.run_consensus(task, voting="simple", max_tokens=800)

    outpath = REPORTS / (
        f"consensus_{repo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"Saved: {outpath}")
