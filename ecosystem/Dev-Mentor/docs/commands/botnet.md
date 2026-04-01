# BOTNET(1) — Terminal Depths Man Page

## NAME
  botnet — manage your compromised node network

## SYNOPSIS
  botnet [status|add <node>|remove <node>|execute <cmd>]

## DESCRIPTION
A botnet pools compromised nodes for coordinated operations: distributed
brute-force, DDOS simulation, and mass data exfiltration. Nodes are added
after successful hack operations.

## SUBCOMMANDS
  status          Show botnet size and active nodes
  add <node>      Recruit a compromised node
  remove <node>   Drop a node from the botnet
  execute <cmd>   Run a command across all botnet nodes

## EXAMPLES
  botnet status
  botnet add chimera-node
  botnet execute "exfil /etc/shadow"

## SEE ALSO
  hack, backdoor, exploit, swarm

---
*Generated 2026-03-23*