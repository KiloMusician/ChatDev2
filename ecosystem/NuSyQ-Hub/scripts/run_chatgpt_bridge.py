#!/usr/bin/env python3
"""Run the ChatGPT bridge (uvicorn wrapper)

Usage:
  python scripts/run_chatgpt_bridge.py
"""

from __future__ import annotations

from src.system.chatgpt_bridge import run_standalone

if __name__ == "__main__":
    run_standalone()
