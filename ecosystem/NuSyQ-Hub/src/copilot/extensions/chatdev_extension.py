"""ChatDev extension providing ChatDev access for Copilot."""

from __future__ import annotations

import subprocess

from integration.chatdev_launcher import ChatDevLauncher

from . import CopilotExtension, register_extension


class ChatDevExtension(CopilotExtension):
    """Copilot extension that manages a ChatDev session."""

    def __init__(self) -> None:
        """Initialize ChatDevExtension."""
        self.launcher: ChatDevLauncher | None = None
        self.process: subprocess.Popen[str] | None = None

    def activate(self) -> None:
        """Boot ChatDev using the integration launcher."""
        if self.process and self.process.poll() is None:
            return
        self.launcher = ChatDevLauncher()
        self.process = self.launcher.launch_chatdev()

    def send_query(self, query: str) -> str:
        """Send a query to the ChatDev process and return its response."""
        if not self.process or self.process.poll() is not None:
            msg = "ChatDev process is not active"
            raise RuntimeError(msg)
        if not self.process.stdin or not self.process.stdout:
            msg = "ChatDev process is not interactive"
            raise RuntimeError(msg)
        self.process.stdin.write(query + "\n")
        self.process.stdin.flush()
        return self.process.stdout.readline().strip()

    def shutdown(self) -> None:
        """Terminate the ChatDev process if it is running."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
        self.launcher = None


# Register extension for dynamic discovery
register_extension("chatdev", ChatDevExtension)
