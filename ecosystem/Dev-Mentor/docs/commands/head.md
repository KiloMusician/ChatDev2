# HEAD(1) — Terminal Depths Man Page

## NAME
  head — output the first lines of a file

## SYNOPSIS
  head [-n <count>] <path>

## DESCRIPTION
Prints the first N lines of a virtual filesystem file (default: 10).
Works on both virtual and mounted real files.

## EXAMPLES
  head /etc/passwd
  head -n 5 /home/ghost/.diary
  head /opt/chimera/README.corp

## SEE ALSO
  tail, cat, grep, wc

---
*Generated 2026-03-23*