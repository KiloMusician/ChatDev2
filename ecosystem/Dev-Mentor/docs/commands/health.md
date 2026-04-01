# HEALTH(1) — Terminal Depths Man Page

## NAME
  health — display system health status

## SYNOPSIS
  health [<service>]

## DESCRIPTION
Shows health status of all registered services: API, ML services, sidecars,
and the Lattice. With a service name, shows detailed health for that service.
Uses TCP probing for liveness detection.

## EXAMPLES
  health
  health serena
  health model_router
  health gateway

## SEE ALSO
  metrics, version, swarm, status

---
*Generated 2026-03-23*