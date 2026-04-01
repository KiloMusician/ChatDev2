#!/usr/bin/env python3
"""Check Ollama installation and connectivity.

This script reports whether the Ollama executable is present and, if
OLLAMA_HOST and OLLAMA_PORT are configured, attempts a TCP connection.
"""

import os
import shutil
import socket


def main() -> int:
    path = shutil.which("ollama")
    print("ollama_executable:", path)
    host = os.environ.get("OLLAMA_HOST")
    port = os.environ.get("OLLAMA_PORT")
    print("OLLAMA_HOST env:", host)
    print("OLLAMA_PORT env:", port)

    if host and port:
        try:
            s = socket.create_connection((host, int(port)), timeout=2)
            s.close()
            print("TCP connection to OLLAMA_HOST:PORT succeeded")
            return 0
        except Exception as e:
            print("TCP connection failed:", e)
            return 2

    # If no host/port provided, just report executable presence
    return 0 if path else 3


if __name__ == "__main__":
    raise SystemExit(main())
