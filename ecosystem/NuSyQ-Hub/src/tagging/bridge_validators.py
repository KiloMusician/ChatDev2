from typing import Any


def validate_omnitag(tag: dict[str, Any]) -> bool:
    """Validate the structure and content of an OmniTag."""
    required_fields = {"id", "context", "metadata"}
    if not required_fields.issubset(tag.keys()):
        return False

    if not isinstance(tag["id"], str) or not tag["id"]:
        return False

    if not isinstance(tag["context"], str):
        return False

    return isinstance(tag["metadata"], dict)


def validate_megatag(tag: dict[str, Any]) -> bool:
    """Validate the structure and content of a MegaTag."""
    required_fields = {"id", "type", "attributes"}
    if not required_fields.issubset(tag.keys()):
        return False

    if not isinstance(tag["id"], str) or not tag["id"]:
        return False

    if tag["type"] not in {"type1", "type2", "type3"}:
        return False

    return isinstance(tag["attributes"], dict)


def validate_contextual_memory(memory: object) -> bool:
    """Validate the integrity of the contextual memory structure."""
    if not isinstance(memory, list):
        return False
    for entry in memory:
        if not isinstance(entry, dict):
            return False
        if "id" not in entry or "context" not in entry:
            return False
    return True
