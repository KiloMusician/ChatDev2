#!/usr/bin/env python3
"""Generate ChatGPT function-calling schema (JSON) for the NuSyQ ChatGPT bridge.

Run:
  python scripts/generate_chatgpt_functions.py > scripts/chatgpt_functions.json

The output is a JSON array of function objects compatible with OpenAI/ChatGPT function calling.
"""

from __future__ import annotations

import json

functions = [
    {
        "name": "send_terminal",
        "description": "Send a message to a terminal channel in NuSyQ-Hub.",
        "parameters": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Terminal channel name (e.g., Errors, Tasks)",
                },
                "level": {"type": "string", "description": "Log level (info, warning, error)"},
                "message": {"type": "string", "description": "Message to send"},
                "meta": {"type": "object", "description": "Optional metadata object"},
            },
            "required": ["channel", "level", "message"],
        },
    },
    {
        "name": "submit_pu",
        "description": "Submit a Processing Unit (PU) request to the Hub.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "payload": {"type": "object"},
                "priority": {"type": "string", "enum": ["critical", "high", "normal", "low"]},
            },
            "required": ["title"],
        },
    },
    {
        "name": "execute_command",
        "description": "Execute a generic command via the ChatGPT bridge (best-effort).",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "args": {"type": "object"},
                "source": {"type": "string"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "get_quests_status",
        "description": "Retrieve recent quests from the Rosetta Quest System.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
]

print(json.dumps(functions, indent=2))
