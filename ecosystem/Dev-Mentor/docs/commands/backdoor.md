# BACKDOOR(1) — Terminal Depths Man Page

## NAME
  backdoor — plant a persistent backdoor on a compromised node

## SYNOPSIS
  backdoor [<target>|list|remove <id>]

## DESCRIPTION
After gaining access to a target node, backdoor installs a persistent
listener. Active backdoors provide ongoing intelligence and enable
re-entry without re-exploiting. Requires prior successful hack or exploit.

## SUBCOMMANDS
  <target>     Install backdoor on target node
  list         List all active backdoors
  remove <id>  Remove a backdoor

## EXAMPLES
  backdoor nexus-core
  backdoor list
  backdoor remove bd-001

## SEE ALSO
  hack, exploit, botnet, recon

---
*Generated 2026-03-23*