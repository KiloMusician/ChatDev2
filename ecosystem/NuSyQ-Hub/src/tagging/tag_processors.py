from typing import Any


def process_omni_tags(tags: list[str]) -> dict[str, dict[str, Any]]:
    """Process a list of OmniTags and return a structured representation."""
    processed_tags: dict[str, dict[str, Any]] = {}
    for tag in tags:
        processed_tags[tag] = {
            "type": "OmniTag",
            "description": f"Processed OmniTag: {tag}",
            "metadata": {
                "created_at": "2023-01-01T00:00:00Z",
                "source": "KILO-FOOLISH",
            },
        }
    return processed_tags


def process_mega_tags(tags: list[str]) -> dict[str, dict[str, Any]]:
    """Process a list of MegaTags and return a structured representation."""
    processed_tags: dict[str, dict[str, Any]] = {}
    for tag in tags:
        processed_tags[tag] = {
            "type": "MegaTag",
            "description": f"Processed MegaTag: {tag}",
            "metadata": {
                "created_at": "2023-01-01T00:00:00Z",
                "source": "KILO-FOOLISH",
            },
        }
    return processed_tags


def enhance_context_with_tags(context: dict[str, Any], tags: list[str]) -> dict[str, Any]:
    """Enhance the given context with processed tags."""
    existing = context.get("tags")
    if not isinstance(existing, dict):
        existing = {}

    existing.update(
        {
            "omni_tags": process_omni_tags(tags),
            "mega_tags": process_mega_tags(tags),
        }
    )
    context["tags"] = existing
    return context


def validate_tags(tags: list[str]) -> bool:
    """Validate the provided tags for correct format and structure."""
    return all(not (not isinstance(tag, str) or len(tag) == 0) for tag in tags)


def extract_tags_from_context(context: dict[str, Any]) -> list[str]:
    """Extract tags from the provided context."""
    tags_section = context.get("tags")
    if not isinstance(tags_section, dict):
        return []

    def _keys_of_dict(value: Any) -> list[str]:
        if isinstance(value, dict):
            return [key for key in value if isinstance(key, str)]
        return []

    omni_tags = _keys_of_dict(tags_section.get("omni_tags"))
    mega_tags = _keys_of_dict(tags_section.get("mega_tags"))
    return omni_tags + mega_tags
