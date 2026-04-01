# LTRACE(1) — Terminal Depths Man Page

## NAME
  ltrace — library call tracer

## SYNOPSIS
  ltrace <command>

## DESCRIPTION
Intercepts and records dynamic library calls made by a virtual process.
Useful for CTF reverse engineering — catches strcmp calls that reveal
hardcoded passwords.

## EXAMPLES
  ltrace ./crackme
  ltrace /opt/chimera/checker

## SEE ALSO
  strace, gdb, strings

---
*Generated 2026-03-23*