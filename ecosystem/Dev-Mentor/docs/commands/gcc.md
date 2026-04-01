# GCC(1) — Terminal Depths Man Page

## NAME
  gcc — compile C code in the virtual environment

## SYNOPSIS
  gcc [OPTIONS] <file>

## DESCRIPTION
Compiles C source files within the Terminal Depths sandbox. Used in reverse
engineering and binary exploitation challenges.

## EXAMPLES
  gcc -o exploit exploit.c
  gcc -O2 -o crackme crackme.c
  gcc -m32 -o vuln vuln.c

## SEE ALSO
  gdb, strings, objdump

---
*Generated 2026-03-23*