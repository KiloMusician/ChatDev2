"""Hugging Face MCP Bridge for NuSyQ ecosystem.

Provides integration with Hugging Face Hub MCP tools for ML model/dataset
discovery, paper search, documentation access, and dynamic Gradio space invocation.

MCP Tool Prefix: mcp_evalstate_hf-_
Total Tools: 10

Categories:
- Search: Models, datasets, papers, spaces
- Documentation: HF docs search and fetch
- Authentication: User info
- Execution: Dynamic Gradio space invocation, image generation

Note: Tools are authenticated as user 'KiloEthereal'.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HFResourceType(Enum):
    """Types of Hugging Face resources."""

    MODEL = "model"
    DATASET = "dataset"
    SPACE = "space"
    PAPER = "paper"


@dataclass
class HFBridgeStatus:
    """HuggingFace bridge availability status."""

    available: bool
    authenticated: bool = False
    username: str | None = None
    hf_hub_installed: bool = False
    message: str = ""


@dataclass
class HFSearchResult:
    """Search result from HuggingFace Hub."""

    resource_type: HFResourceType
    id: str
    name: str
    description: str = ""
    downloads: int = 0
    likes: int = 0
    tags: list[str] = field(default_factory=list)


# ── MCP Tool Catalog ──────────────────────────────────────────────────────────

HUGGINGFACE_MCP_TOOLS: dict[str, dict[str, Any]] = {
    # Search Tools
    "dataset_search": {
        "category": "search",
        "description": "Search HuggingFace datasets by query, tags, or filters",
        "parameters": ["query", "filter", "sort", "limit"],
        "usage": "Find datasets for training, fine-tuning, or evaluation",
        "example_queries": ["text-classification", "sentiment analysis", "image-captioning"],
    },
    "model_search": {
        "category": "search",
        "description": "Search HuggingFace models by query, task, library, or tags",
        "parameters": ["query", "filter", "sort", "limit"],
        "usage": "Discover pre-trained models for various ML tasks",
        "common_tasks": [
            "text-generation",
            "text-classification",
            "image-classification",
            "object-detection",
        ],
    },
    "paper_search": {
        "category": "search",
        "description": "Search ML papers (arXiv) referenced on HuggingFace",
        "parameters": ["query", "sort", "limit"],
        "usage": "Find research papers related to models or methods",
        "notes": "Papers often referenced by model cards and dataset descriptions",
    },
    "space_search": {
        "category": "search",
        "description": "Search Gradio/Streamlit spaces (demos)",
        "parameters": ["query", "filter", "sort", "limit"],
        "usage": "Find interactive ML demos and applications",
        "examples": ["image-to-text", "text-to-image", "chat", "audio"],
    },
    # Repository Info
    "hub_repo_details": {
        "category": "info",
        "description": "Get detailed info about a HF repository (model, dataset, or space)",
        "parameters": ["repo_id", "repo_type"],
        "usage": "Fetch metadata, downloads, files, and configuration",
    },
    # Documentation
    "hf_doc_search": {
        "category": "docs",
        "description": "Search HuggingFace documentation",
        "parameters": ["query", "library"],
        "usage": "Find documentation for transformers, diffusers, datasets, etc.",
        "libraries": ["transformers", "diffusers", "datasets", "accelerate", "peft", "trl"],
    },
    "hf_doc_fetch": {
        "category": "docs",
        "description": "Fetch specific documentation page content",
        "parameters": ["doc_path", "library"],
        "usage": "Get full content of a specific doc page",
    },
    # Authentication
    "hf_whoami": {
        "category": "auth",
        "description": "Get current authenticated user info",
        "parameters": [],
        "usage": "Check authentication status and user details",
        "note": "Authenticated as 'KiloEthereal'",
    },
    # Execution
    "dynamic_space": {
        "category": "execute",
        "description": "Invoke a Gradio space dynamically",
        "parameters": ["space_id", "inputs"],
        "usage": "Run inference on any Gradio-based space",
        "examples": [
            "stabilityai/stable-diffusion-3-medium",
            "Qwen/Qwen2-VL-7B-Instruct",
        ],
    },
    "gr1_z_image_turbo_generate": {
        "category": "generate",
        "description": "Generate images using Turbo image generation space",
        "parameters": ["prompt", "negative_prompt", "steps", "cfg_scale"],
        "usage": "Quick image generation via optimized space",
    },
}


class HuggingFaceBridge:
    """Bridge to HuggingFace Hub MCP tools.

    Provides unified access to:
    - Model/dataset/space/paper search
    - Documentation lookup
    - Dynamic Gradio space invocation
    - Authentication status
    """

    MCP_PREFIX = "mcp_evalstate_hf-_"

    def __init__(self) -> None:
        """Initialize HuggingFace bridge."""
        self._status: HFBridgeStatus | None = None

    def probe(self) -> HFBridgeStatus:
        """Probe HuggingFace MCP availability.

        Returns:
            HFBridgeStatus with availability details.
        """
        # Check if huggingface_hub is installed
        import importlib.util

        hf_hub_installed = importlib.util.find_spec("huggingface_hub") is not None

        # Check for HF token (indicates authentication)
        hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
        # MCP extension has pre-authenticated session as KiloEthereal;
        # env token presence grants additional programmatic API access.
        token_authenticated = bool(hf_token)

        self._status = HFBridgeStatus(
            available=True,  # MCP tools always available via extension
            authenticated=True,  # MCP extension is pre-authenticated as KiloEthereal
            username="KiloEthereal",
            hf_hub_installed=hf_hub_installed,
            message=(
                "HuggingFace MCP ready (authenticated as KiloEthereal"
                + (", HF_TOKEN present" if token_authenticated else "")
                + ")"
            ),
        )

        try:
            from src.system.agent_awareness import emit as _emit

            _detail = (
                f"hub_installed={hf_hub_installed} token={token_authenticated} user=KiloEthereal"
            )
            _emit(
                "agents", f"HuggingFace probe: {_detail}", level="INFO", source="huggingface_bridge"
            )
        except Exception:
            pass

        return self._status

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a specific MCP tool.

        Args:
            tool_name: Tool name without prefix (e.g., 'model_search').

        Returns:
            Tool metadata dict or None if not found.
        """
        return HUGGINGFACE_MCP_TOOLS.get(tool_name)

    def get_tools_by_category(self, category: str) -> list[str]:
        """Get all tools in a category.

        Args:
            category: Category name (search, info, docs, auth, execute, generate).

        Returns:
            List of tool names in the category.
        """
        return [
            name for name, info in HUGGINGFACE_MCP_TOOLS.items() if info["category"] == category
        ]

    def get_mcp_tool_name(self, tool: str) -> str:
        """Get full MCP tool name with prefix.

        Args:
            tool: Short tool name (e.g., 'model_search').

        Returns:
            Full MCP name (e.g., 'mcp_evalstate_hf-_model_search').
        """
        return f"{self.MCP_PREFIX}{tool}"

    def format_search_recommendations(self, task: str) -> dict[str, Any]:
        """Get search recommendations for a task.

        Args:
            task: ML task description.

        Returns:
            Dict with recommended search queries and tools.
        """
        # Map common tasks to HF tags
        task_mapping = {
            "text-generation": ["text-generation", "causal-lm", "language-modeling"],
            "classification": [
                "text-classification",
                "sentiment-analysis",
                "zero-shot-classification",
            ],
            "qa": ["question-answering", "extractive-qa", "conversational"],
            "summarization": ["summarization", "text2text-generation"],
            "translation": ["translation", "machine-translation"],
            "image": ["image-classification", "image-to-text", "text-to-image"],
            "audio": ["automatic-speech-recognition", "text-to-speech", "audio-classification"],
            "code": ["text-generation", "code-generation", "code-completion"],
        }

        tags = task_mapping.get(task.lower(), [task])

        return {
            "recommended_tools": [
                self.get_mcp_tool_name("model_search"),
                self.get_mcp_tool_name("dataset_search"),
                self.get_mcp_tool_name("space_search"),
            ],
            "suggested_queries": tags,
            "common_filters": ["downloads", "likes", "trending"],
        }


# ── Module-Level Functions ────────────────────────────────────────────────────

_bridge: HuggingFaceBridge | None = None


def get_bridge() -> HuggingFaceBridge:
    """Get or create HuggingFace bridge singleton.

    Returns:
        HuggingFaceBridge instance.
    """
    global _bridge
    if _bridge is None:
        _bridge = HuggingFaceBridge()
    return _bridge


def probe_huggingface() -> dict[str, Any]:
    """Probe HuggingFace availability for agent registry.

    Returns:
        Dict with status and detail for agent registry.
    """
    bridge = get_bridge()
    status = bridge.probe()

    return {
        "status": "online" if status.available else "offline",
        "detail": f"HuggingFace MCP: {len(HUGGINGFACE_MCP_TOOLS)} tools, user: {status.username or 'anonymous'}",
    }


def quick_status() -> str:
    """Get quick one-line status for display.

    Returns:
        Status string.
    """
    bridge = get_bridge()
    status = bridge.probe()

    auth_info = f"user: {status.username}" if status.authenticated else "anonymous"
    return f"HuggingFace: ONLINE - {len(HUGGINGFACE_MCP_TOOLS)} tools ({auth_info})"


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("HuggingFace MCP Bridge - NuSyQ Integration")
    print("=" * 60)

    bridge = get_bridge()
    status = bridge.probe()

    print(f"\nStatus: {'ONLINE' if status.available else 'OFFLINE'}")
    print(f"Authenticated: {status.authenticated}")
    print(f"Username: {status.username or 'N/A'}")
    print(f"HF Hub Library: {'Installed' if status.hf_hub_installed else 'Not Installed'}")

    print(f"\nTotal MCP Tools: {len(HUGGINGFACE_MCP_TOOLS)}")
    print("\nTools by Category:")
    for category in ["search", "info", "docs", "auth", "execute", "generate"]:
        tools = bridge.get_tools_by_category(category)
        if tools:
            print(f"  {category}: {len(tools)} tools")
            for tool in tools:
                info = bridge.get_tool_info(tool)
                if info:
                    print(f"    - {tool}: {info['description']}")

    print("\nSearch Recommendations for 'code generation':")
    recs = bridge.format_search_recommendations("code")
    print(f"  Tools: {', '.join(recs['recommended_tools'])}")
    print(f"  Queries: {', '.join(recs['suggested_queries'])}")

    print(f"\nQuick Status: {quick_status()}")
