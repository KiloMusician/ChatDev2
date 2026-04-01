"""Security subsystem — encrypted API key management.

Handles encrypted storage and secure access to API keys for fallback scenarios.
Prioritizes offline models while providing secure credential management when
external services are required.

OmniTag: {
    "purpose": "security_subsystem",
    "tags": ["Security", "Encryption", "APIKeys", "Credentials"],
    "category": "security",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = ["SecureAPIManager"]


def __getattr__(name: str):
    if name == "SecureAPIManager":
        from src.security.secure_api_manager import SecureAPIManager

        return SecureAPIManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
