# RM(1) — Terminal Depths Man Page

## NAME
  rm — remove files or directories from the virtual filesystem

## SYNOPSIS
  rm [-r] <path>

## DESCRIPTION
Deletes a virtual filesystem node. Use -r for recursive directory removal.
Certain system paths (/etc, /proc, core story files) are protected and will
reject removal. Deleted nodes are gone for the session.

## EXAMPLES
  rm /tmp/payload.sh
  rm -r /tmp/workspace
  rm /home/ghost/loot.dat

## SEE ALSO
  mv, mkdir, ls, spawn

---
*Generated 2026-03-23*