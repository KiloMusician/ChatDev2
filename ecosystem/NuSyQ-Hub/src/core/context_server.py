"""OmniTag: {.

    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Ollama"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

import errno
import http.server
import json
import socketserver
from pathlib import Path

from src.ai.ollama_hub import ollama_hub
from src.core.config_manager import ConfigManager


# Allow reuse of socket address
class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class AIContextHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        # Add CORS headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        # Respond to CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/models":
            self.serve_models()
        else:
            super().do_GET()

    def serve_models(self) -> None:
        models = ollama_hub.list_models()
        payload = {"models": models}
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))


if __name__ == "__main__":
    # Load configuration (from JSON file or environment)
    project_root = Path(__file__).parent.parent
    cfg_file = project_root / "config" / "settings.json"
    config = ConfigManager(cfg_file)
    host = config.get("context_server.host", "127.0.0.1")
    port = config.get("context_server.port", 11435)
    # Try binding, fallback to next free port
    while True:
        try:
            with ReusableTCPServer((host, port), AIContextHandler) as httpd:
                addr = host or "localhost"
                httpd.serve_forever()
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                port += 1
                continue
            raise
        except KeyboardInterrupt:
            httpd.server_close()
        break
