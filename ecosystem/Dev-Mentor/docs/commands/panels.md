# PANELS(1) — Terminal Depths Man Page

## NAME
  panels — manage the UI panel layout

## SYNOPSIS
  panels [list|show <name>|hide <name>|layout <preset>]

## DESCRIPTION
The Panel Evolution System provides 14 configurable UI panels with 4 layout
presets. Manage which panels are visible and arrange them to your workflow.
Layout preferences persist across sessions.

## SUBCOMMANDS
  list           All available panels
  show <name>    Show a hidden panel
  hide <name>    Hide a panel
  layout <n>     Switch to a layout preset (1-4)

## EXAMPLES
  panels list
  panels show ml
  panels hide colony
  panels layout 2

## SEE ALSO
  theme, status, swarm

---
*Generated 2026-03-23*