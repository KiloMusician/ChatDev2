"""OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}

This module documents a reusable TCP server stub for context examples.
"""

import socketserver

PORT = 0


class AIContextHandler(socketserver.BaseRequestHandler):
    """Placeholder request handler for documentation demos."""

    def handle(self) -> None:  # pragma: no cover - docs-only stub
        _ = self.request, self.client_address, self.server
        # Intentionally no-op for documentation context.


class ReusableTCPServer(socketserver.TCPServer):
    """TCPServer variant that enables address reuse for quick restarts."""

    allow_reuse_address = True


def create_server(port: int = PORT) -> socketserver.TCPServer:
    """Create a reusable TCP server without starting it."""
    return ReusableTCPServer(("", port), AIContextHandler)
