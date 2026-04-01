# HEXDUMP(1) — Terminal Depths Man Page

## NAME
  hexdump — display file contents in hexadecimal

## SYNOPSIS
  hexdump [-C] <file>

## DESCRIPTION
Displays file contents in hexadecimal format. With -C shows ASCII
interpretation alongside hex. Alias for xxd -C.

## EXAMPLES
  hexdump /tmp/mystery.bin
  hexdump -C /opt/chimera/payload.bin

## SEE ALSO
  xxd, strings, forensics, binwalk

---
*Generated 2026-03-23*