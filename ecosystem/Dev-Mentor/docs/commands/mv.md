# MV(1) — Terminal Depths Man Page

## NAME
  mv — move or rename files in the virtual filesystem

## SYNOPSIS
  mv <source> <destination>

## DESCRIPTION
Moves a virtual filesystem node to a new path, or renames it in place. If the
destination is an existing directory, the source is moved into it. Useful for
staging exfiltration payloads or reorganising evidence.

## EXAMPLES
  mv /tmp/loot.dat /home/ghost/loot.dat
  mv /opt/chimera/old-payload.sh /tmp/
  mv /var/log/trace.log /var/log/trace.bak

## SEE ALSO
  cp, rm, ls

---
*Generated 2026-03-23*