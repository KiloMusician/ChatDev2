# LSOF(1) — Terminal Depths Man Page

## NAME
  lsof — list open virtual files

## SYNOPSIS
  lsof [<process>]

## DESCRIPTION
Lists all file descriptors currently open in the virtual filesystem. With a
process name, filters to that process only. Useful for discovering what
secret files certain agents or processes have open.

## EXAMPLES
  lsof
  lsof chimera-daemon
  lsof serena

## SEE ALSO
  ps, cat, ls, fds

---
*Generated 2026-03-23*