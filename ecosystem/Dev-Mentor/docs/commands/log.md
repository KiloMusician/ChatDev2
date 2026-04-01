# LOG(1) — Terminal Depths Man Page

## NAME
  log — view game event logs

## SYNOPSIS
  log [<type>|clear|export]

## DESCRIPTION
Shows the game's event log: commands executed, XP awarded, story beats
triggered, and errors. log clear wipes the display buffer. log export
saves the log to a VFS file.

## SUBCOMMANDS
  (none)     Last 50 events
  <type>     Filter: xp, story, error, combat, agent
  clear      Clear log display
  export     Save log to /tmp/game.log

## EXAMPLES
  log
  log story
  log xp
  log clear

## SEE ALSO
  journal, timeline, story

---
*Generated 2026-03-23*