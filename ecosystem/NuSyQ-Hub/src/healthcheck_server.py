"""Lightweight health check HTTP server for Docker containers.

This minimal server provides /health and /ready endpoints for
container orchestration (Docker, Kubernetes) without requiring
the full application to be running.
"""

import http.server
import json
import socketserver
import sys
from datetime import datetime
from pathlib import Path


class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""

    def do_GET(self) -> None:
        """Handle GET requests for health/ready endpoints."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "nusyq-hub",
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == "/ready":
            # Check if critical files exist
            ready = all(
                [
                    Path("src/main.py").exists(),
                    Path("requirements.txt").exists(),
                    Path("config/settings.json").exists(),
                ],
            )
            status_code = 200 if ready else 503
            self.send_response(status_code)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "status": "ready" if ready else "not ready",
                "timestamp": datetime.now().isoformat(),
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format_string, *args) -> None:
        """Suppress access logs."""


def run_server(port=5000) -> None:
    """Run the health check server."""
    with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run_server(port)
