# DIFF(1) — Terminal Depths Man Page

## NAME
  diff — compare two files or game states

## SYNOPSIS
  diff <file1> <file2>

## DESCRIPTION
Shows line-by-line differences between two virtual filesystem files. Also
supports comparing game state snapshots: diff state:before state:after.
Useful for detecting changes made by in-game events or agents.

## EXAMPLES
  diff /etc/passwd /tmp/passwd.bak
  diff /home/ghost/.diary /tmp/diary.bak

## SEE ALSO
  cat, grep, patch

---
*Generated 2026-03-23*