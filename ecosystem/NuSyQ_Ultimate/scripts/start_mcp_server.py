#!/usr/bin/env python3
"""
Start the NuSyQ MCP server in-process for local testing.
"""

import os
import sys
from pathlib import Path

import uvicorn

# Ensure repo root on sys.path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

try:
    from mcp_server.main_modular import NuSyQMCPServer
except ImportError:
    from mcp_server.main import NuSyQMCPServer

server = NuSyQMCPServer()
app = server.app

if __name__ == "__main__":
    port = int(os.environ.get("MCP_SERVER_PORT", os.environ.get("PORT", "8765")))
    host = os.environ.get("MCP_SERVER_HOST", "127.0.0.1")
    # If the server has a ConfigManager, update its runtime service config
    try:
        cfg_mgr = getattr(server, "config_manager", None)
        if cfg_mgr is not None and isinstance(cfg_mgr, object):
            if isinstance(cfg_mgr._config_cache, dict):
                svc = cfg_mgr._config_cache.get("service")
            else:
                svc = None
            if svc is None:
                cfg_mgr._config_cache["service"] = {}
            cfg_mgr._config_cache["service"]["host"] = host
            cfg_mgr._config_cache["service"]["port"] = port
    except (AttributeError, KeyError, TypeError, OSError):
        # Best-effort override — do not crash if internals differ
        pass
    uvicorn.run(app, host=host, port=port, log_level="info")
