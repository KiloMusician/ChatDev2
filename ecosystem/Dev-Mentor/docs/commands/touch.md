# TOUCH(1) — Terminal Depths Man Page

## NAME
  touch — create an empty file in the virtual filesystem

## SYNOPSIS
  touch <path>

## DESCRIPTION
Creates an empty virtual filesystem file at the specified path, or updates
the modification timestamp if it already exists. The parent directory must
exist. Use spawn to create files with initial content.

## EXAMPLES
  touch /tmp/notes.txt
  touch /home/ghost/.hidden
  touch /var/log/custom.log

## SEE ALSO
  spawn, mkdir, cat, ls

---
*Generated 2026-03-23*