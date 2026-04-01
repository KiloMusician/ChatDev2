# BOMB(1) — Terminal Depths Man Page

## NAME
  bomb — deploy a logic bomb payload

## SYNOPSIS
  bomb [<target>|list|defuse <id>]

## DESCRIPTION
Plants a time-delayed logic bomb on a target node. The bomb executes a
payload at a specified time, causing system disruption. Logic bombs are
a high-risk, high-reward tool — detect and defuse enemy bombs with defuse.

## SUBCOMMANDS
  <target>    Deploy a bomb on the target
  list        List active planted bombs
  defuse <id> Disarm a detected bomb

## EXAMPLES
  bomb nexus-core
  bomb list
  bomb defuse bomb-003

## SEE ALSO
  hack, exploit, backdoor, crack

---
*Generated 2026-03-23*