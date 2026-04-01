# PLUGIN(1) — Terminal Depths Man Page

## NAME
  plugin — manage game engine plugins

## SYNOPSIS
  plugin [list|info <name>|enable <name>|disable <name>]

## DESCRIPTION
Terminal Depths uses a modular plugin architecture for challenge generation,
documentation, formatting, and testing. View and toggle active plugins
from the game shell.

## SUBCOMMANDS
  list              Show all registered plugins and status
  info <name>       Plugin details and capabilities
  enable <name>     Activate a disabled plugin
  disable <name>    Deactivate a plugin

## EXAMPLES
  plugin list
  plugin info challenge_gen
  plugin enable procgen_quests

## SEE ALSO
  chug, validate, version

---
*Generated 2026-03-23*