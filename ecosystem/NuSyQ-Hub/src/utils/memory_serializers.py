"""OmniTag: {.

    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Memory"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

import json
from typing import Any, cast


def serialize_memory_node(memory_node: dict[str, Any]) -> str:
    """Serialize a memory node to a JSON string for persistent storage."""
    return json.dumps(memory_node)


def deserialize_memory_node(serialized_node: str) -> dict[str, Any]:
    """Deserialize a JSON string back into a memory node dictionary."""
    return cast(dict[str, Any], json.loads(serialized_node))


def serialize_memory_nodes(memory_nodes: list[dict[str, Any]]) -> str:
    """Serialize a list of memory nodes to a JSON string."""
    return json.dumps(memory_nodes)


def deserialize_memory_nodes(serialized_nodes: str) -> list[dict[str, Any]]:
    """Deserialize a JSON string back into a list of memory nodes."""
    return cast(list[dict[str, Any]], json.loads(serialized_nodes))


def save_memory_to_file(memory_data: list[dict[str, Any]], file_path: str) -> None:
    """Save serialized memory data to a file."""
    with open(file_path, "w") as file:
        file.write(serialize_memory_nodes(memory_data))


def load_memory_from_file(file_path: str) -> list[dict[str, Any]]:
    """Load memory data from a file and deserialize it."""
    with open(file_path) as file:
        return deserialize_memory_nodes(file.read())
