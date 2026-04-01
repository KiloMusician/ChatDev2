# SU(1) — Terminal Depths Man Page

## NAME
  su — switch user context in the virtual filesystem

## SYNOPSIS
  su [<username>]

## DESCRIPTION
Switches the active shell user context. Without arguments, escalates to root
(if permitted by current story state). With a username, switches to that
agent's home context. Affects file permission checks and prompt colour.

## EXAMPLES
  su
  su root
  su ghost
  su ada

## SEE ALSO
  sudo, chmod, chown, whoami

---
*Generated 2026-03-23*