# katana-keeper design

katana-keeper is a lightweight orchestrator for switching your laptop between safe modes (gaming, coding, diagnose, restore). Key ideas:

- Keep state small: current.json, ringbuffer.json, tiny session summaries
- Use profiles (JSON) to describe reversible actions
- Always snapshot rollback state before applying changes
- Keep watch mode in memory and only persist tiny summaries
- Provide -WhatIf and -DebugMode for safety

This document is a short design note; further details can be added as the project evolves.
