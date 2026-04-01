# CHOWN(1) — Terminal Depths Man Page

## NAME
  chown — change file ownership in the virtual filesystem

## SYNOPSIS
  chown <user>[:<group>] <path>

## DESCRIPTION
Changes the owner and optionally the group of a virtual filesystem node.
Affects how the node appears in ls output and which agents can access it.

## EXAMPLES
  chown root:root /opt/chimera/core/payload
  chown ghost /home/ghost/.diary
  chown ada:agents /var/log/agent_comms.log

## SEE ALSO
  chmod, ls, sudo

---
*Generated 2026-03-23*