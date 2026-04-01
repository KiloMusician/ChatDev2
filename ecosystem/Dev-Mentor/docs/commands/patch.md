# PATCH(1) — Terminal Depths Man Page

## NAME
  patch — apply a patch to a virtual file

## SYNOPSIS
  patch <file> <patch-file>

## DESCRIPTION
Applies a unified diff patch to a virtual filesystem file. Used in narrative
scenarios where you need to modify system files to advance objectives.

## EXAMPLES
  patch /etc/hosts /tmp/hosts.patch
  patch /opt/chimera/config.yaml /tmp/fix.patch

## SEE ALSO
  diff, cat, chmod

---
*Generated 2026-03-23*