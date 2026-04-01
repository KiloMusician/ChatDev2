# DEBUG(1) — Terminal Depths Man Page

## NAME
  debug — enable debug mode for troubleshooting

## SYNOPSIS
  debug [on|off|level <n>|commands|state]

## DESCRIPTION
Toggles debug output for game development and troubleshooting. debug
commands shows internal command dispatch. debug state dumps the full
game state as JSON.

## SUBCOMMANDS
  on            Enable debug mode
  off           Disable debug mode
  level <n>     Set debug verbosity (0-3)
  commands      Show command dispatch trace
  state         Dump full game state JSON

## EXAMPLES
  debug on
  debug state
  debug commands
  debug off

## SEE ALSO
  version, health, metrics, context

---
*Generated 2026-03-23*