# TAIL(1) — Terminal Depths Man Page

## NAME
  tail — output the last lines of a file

## SYNOPSIS
  tail [-n <count>] <path>

## DESCRIPTION
Prints the last N lines of a virtual filesystem file (default: 10). Supports
both virtual and mounted real files. Use eavesdrop for a live-tail simulation
of agent communications.

## EXAMPLES
  tail /var/log/system.log
  tail -n 20 /home/ghost/.diary
  tail /opt/chimera/core/.internal_847.memo

## SEE ALSO
  head, cat, grep, eavesdrop

---
*Generated 2026-03-23*