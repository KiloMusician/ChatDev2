# WC(1) — Terminal Depths Man Page

## NAME
  wc — word, line, and character count

## SYNOPSIS
  wc [-l|-w|-c] <path>

## DESCRIPTION
Counts lines, words, or characters in a virtual filesystem file. With -l
counts lines only, -w words only, -c bytes only. Without flags shows all
three counts.

## EXAMPLES
  wc /home/ghost/.diary
  wc -l /var/log/system.log
  wc -w /opt/chimera/README.corp

## SEE ALSO
  cat, head, tail, grep

---
*Generated 2026-03-23*