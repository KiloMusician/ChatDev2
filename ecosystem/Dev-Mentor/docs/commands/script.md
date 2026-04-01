# SCRIPT(1) — Terminal Depths Man Page

## NAME
  script — manage and run in-game automation scripts

## SYNOPSIS
  script list|run|cat|new|validate|edit <name> [args...]

## DESCRIPTION
The Terminal Depths scripting subsystem lets you write and run in-game
automation scripts (Bitburner-style). Scripts automate tasks, run hacks,
and can interact with the game API. Validated scripts run in a sandboxed
interpreter.

## SUBCOMMANDS
  list              List all saved scripts
  run <name> [args] Execute a script with optional arguments
  cat <name>        Print script source code
  new <name>        Create a new empty script
  validate <name>   Check script for syntax errors
  edit <name>       Open script in editor (VS Code mode)

## EXAMPLES
  script list
  script cat recon.js
  script run recon.js --target nexus-core
  script new my_hack.js
  script validate my_hack.js

## SEE ALSO
  compress, spawn, hack, run

---
*Generated 2026-03-23*