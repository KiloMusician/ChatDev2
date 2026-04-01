"""Copilot extension infrastructure and registry."""

from abc import ABC, abstractmethod


class CopilotExtension(ABC):
    """Base interface for Copilot extensions."""

    @abstractmethod
    def activate(self) -> None:
        """Activate the extension."""

    @abstractmethod
    def send_query(self, query: str) -> str:
        """Send a query to the extension and return the response."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the extension."""


EXTENSION_REGISTRY: dict[str, type[CopilotExtension]] = {}


def register_extension(name: str, extension_cls: type[CopilotExtension]) -> None:
    """Register an extension class under the given name."""
    EXTENSION_REGISTRY[name] = extension_cls


# Import built-in extensions to populate the registry (currently none)
