# STRINGS(1) — Terminal Depths Man Page

## NAME
  strings — extract printable strings from a file

## SYNOPSIS
  strings [-n <min>] <file>

## DESCRIPTION
Searches a binary file for sequences of printable characters. Essential for
CTF reverse engineering challenges — often reveals hardcoded passwords, flags,
and API endpoints.

## OPTIONS
  -n <min>   Minimum string length (default: 4)

## EXAMPLES
  strings /opt/chimera/core/payload.bin
  strings -n 8 /tmp/mystery.elf
  strings /var/cache/chimera/data.db

## SEE ALSO
  xxd, hexdump, forensics, binwalk

---
*Generated 2026-03-23*