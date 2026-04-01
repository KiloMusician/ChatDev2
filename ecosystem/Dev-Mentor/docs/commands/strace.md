# STRACE(1) — Terminal Depths Man Page

## NAME
  strace — trace system calls and signals

## SYNOPSIS
  strace <command>

## DESCRIPTION
Traces system calls made by a virtual process. Useful for understanding how
programs interact with the OS and for finding hidden file reads, network
connections, and privilege escalation opportunities.

## EXAMPLES
  strace ./crackme
  strace -p 1337
  strace /opt/chimera/daemon

## SEE ALSO
  gdb, ltrace, ps

---
*Generated 2026-03-23*