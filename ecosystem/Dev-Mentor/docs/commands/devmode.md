# DEVMODE(1) — Terminal Depths Man Page

## NAME
  devmode — toggle developer mode

## SYNOPSIS
  devmode [on|off|status]

## DESCRIPTION
Developer mode enables privileged commands: spawn, inject, fs_reset, and
direct state manipulation. In devmode, certain story gates and level
requirements are bypassed.

## SUBCOMMANDS
  on      Enable devmode
  off     Disable devmode
  status  Current devmode state

## EXAMPLES
  devmode on
  devmode status
  devmode off

## SEE ALSO
  debug, spawn, fs_reset, inject

---
*Generated 2026-03-23*