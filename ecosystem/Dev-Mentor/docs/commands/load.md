# LOAD(1) — Terminal Depths Man Page

## NAME
  load — load a saved game state

## SYNOPSIS
  load [<session-id>]

## DESCRIPTION
Loads a previously saved session. Without arguments, restores the most
recent auto-save. With a session ID, loads that specific save. Warning: any
unsaved progress in the current session is lost.

## EXAMPLES
  load
  load abc123

## SEE ALSO
  save, status, newgame

---
*Generated 2026-03-23*