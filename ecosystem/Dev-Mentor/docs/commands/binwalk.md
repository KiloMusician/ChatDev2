# BINWALK(1) — Terminal Depths Man Page

## NAME
  binwalk — scan a binary for embedded files and signatures

## SYNOPSIS
  binwalk <file>

## DESCRIPTION
Scans binary files for embedded data, file signatures, and compressed
archives. Used in forensics CTF challenges to detect hidden payloads or
steganographic data embedded within binary files.

## EXAMPLES
  binwalk /tmp/firmware.bin
  binwalk /opt/chimera/image.dat
  binwalk /home/ghost/mystery.bin

## SEE ALSO
  strings, xxd, steg, forensics

---
*Generated 2026-03-23*