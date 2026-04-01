# SPAWN(1) — Terminal Depths Man Page

## NAME
  spawn — create files or directories in devmode

## SYNOPSIS
  spawn <path> [content]

## DESCRIPTION
Developer mode command for injecting new virtual filesystem nodes. Provide a
path to create a directory, or a path plus content string to create a file.
The node appears immediately in ls output and is readable with cat.

## EXAMPLES
  spawn /tmp/test-dir
  spawn /tmp/note.txt "classified payload — do not delete"
  spawn /home/ghost/ops/mission.md "# Operation Nightfall"

## SEE ALSO
  touch, mkdir, cat, ls

---
*Generated 2026-03-23*