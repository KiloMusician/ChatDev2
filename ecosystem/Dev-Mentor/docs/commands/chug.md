# CHUG(1) — Terminal Depths Man Page

## NAME
  chug — CHUG Engine status and cycle management

## SYNOPSIS
  chug [status|cycle|history|trigger]

## DESCRIPTION
The CHUG (Continuous Heuristic Upgrade Generation) Engine runs autonomous
7-phase improvement cycles on the project. From within the game, chug shows
the engine's current phase, recent cycle history, and improvements made.

## SUBCOMMANDS
  status    Current cycle phase and health
  cycle     Show most recent cycle details
  history   Last 10 cycle summaries
  trigger   Manually trigger a new CHUG cycle (dev mode)

## EXAMPLES
  chug status
  chug cycle
  chug history

## SEE ALSO
  swarm, gordon, serena, version

---
*Generated 2026-03-23*