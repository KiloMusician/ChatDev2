# CP(1) — Terminal Depths Man Page

## NAME
  cp — copy files or directories in the virtual filesystem

## SYNOPSIS
  cp <source> <destination>

## DESCRIPTION
Copies a virtual filesystem node to a new path. The source must exist. If the
destination is a directory, the file is copied into it. Binary and narrative
artefact files can be duplicated for inspection or manipulation.

## EXAMPLES
  cp /home/ghost/.diary /tmp/diary.bak
  cp /opt/chimera/core/payload.sh /tmp/
  cp /etc/passwd /home/ghost/passwd.copy

## SEE ALSO
  mv, rm, ls, cat

---
*Generated 2026-03-23*