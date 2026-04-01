# MKDIR(1) — Terminal Depths Man Page

## NAME
  mkdir — create a directory in the virtual filesystem

## SYNOPSIS
  mkdir <path>

## DESCRIPTION
Creates a new directory node in the Terminal Depths virtual filesystem. The
parent directory must already exist. Created directories persist for the
session and can hold files created with touch or spawn.

## EXAMPLES
  mkdir /tmp/workspace
  mkdir /home/ghost/ops
  mkdir /var/cache/exfil

## SEE ALSO
  touch, spawn, ls, rm

---
*Generated 2026-03-23*