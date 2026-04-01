# ACCESS(1) — Terminal Depths Man Page

## NAME
  access — check or request access to restricted systems

## SYNOPSIS
  access [<system>|request <system>|list]

## DESCRIPTION
Checks your access level to a restricted system or path. With request,
submits an access request (may trigger social engineering challenges).
list shows all systems and your current access tier.

## EXAMPLES
  access
  access /opt/chimera/core
  access request nexus-admin
  access list

## SEE ALSO
  chmod, sudo, hack, exploit

---
*Generated 2026-03-23*