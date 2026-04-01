# RELAY(1) — Terminal Depths Man Page

## NAME
  relay — relay communications through an anonymous proxy chain

## SYNOPSIS
  relay [<target>|setup|status|teardown]

## DESCRIPTION
Routes your commands through a chain of proxy nodes, obscuring your origin.
Required for some high-risk operations where direct attribution would trigger
countermeasures.

## EXAMPLES
  relay setup
  relay nexus-core
  relay status
  relay teardown

## SEE ALSO
  cloak, hack, pivot, tor

---
*Generated 2026-03-23*