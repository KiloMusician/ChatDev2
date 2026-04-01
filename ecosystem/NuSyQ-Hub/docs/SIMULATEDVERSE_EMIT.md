SimulatedVerse → TerminalEmitter

This document explains how SimulatedVerse can emit structured terminal events
into the NuSyQ-Hub TerminalManager via a small Node helper that calls the Python
emitter located in the NuSyQ-Hub repository.

Why

- Some processes (Node) are easier to instrument from Node code. Instead of
  re-implementing the terminal protocol in Node, we call the canonical Python
  emitter to keep NDJSON formatting consistent.

Files

- SimulatedVerse/scripts/emit_terminal.js — Node helper that invokes the
  NuSyQ-Hub Python emitter.
- NuSyQ-Hub/scripts/emit_terminal.py — Python emitter that forwards messages to
  TerminalManager channels.

Usage From the SimulatedVerse repo root:

```bash
# emit a simple startup event
npm run emit:start

# or call directly
node scripts/emit_terminal.js Main info "SimulatedVerse started"
```

Notes

- The Node helper resolves the path to the NuSyQ-Hub emitter using the current
  user's Desktop path (conservative default). If you run this setup in a
  different layout, update the absolute path in `scripts/emit_terminal.js` to
  point to `.../NuSyQ-Hub/scripts/emit_terminal.py`.
- Alternatively, you can call the Python emitter directly from system scripts or
  CI steps:

```bash
python /path/to/NuSyQ-Hub/scripts/emit_terminal.py Main info "message" '{"k":"v"}'
```

Security

- The emitter runs as the invoking user and writes only to `data/terminal_logs/`
- inside `NuSyQ-Hub` when the TerminalManager is available.
- Avoid sending sensitive secrets in the `message` or `meta` fields.
