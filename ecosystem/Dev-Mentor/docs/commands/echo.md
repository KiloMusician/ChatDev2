# ECHO(1) — Terminal Depths Man Page

## NAME
  echo — print text to the terminal

## SYNOPSIS
  echo [<text>...]

## DESCRIPTION
Outputs its arguments to the terminal. Supports basic variable expansion
($USER, $LEVEL, $XP) and ANSI colour codes in devmode. Useful for
scripting and testing VFS file content.

## EXAMPLES
  echo hello world
  echo "Current user: $USER"
  echo $LEVEL

## SEE ALSO
  cat, script, spawn

---
*Generated 2026-03-23*