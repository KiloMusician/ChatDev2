# METRICS(1) — Terminal Depths Man Page

## NAME
  metrics — display system and game performance metrics

## SYNOPSIS
  metrics [game|system|ml|registry]

## DESCRIPTION
Shows operational metrics: game session stats, API request counts, ML model
inference latency, challenge completion rates, and service registry health.
Used for monitoring and CHUG engine quality assessments.

## SUBCOMMANDS
  game      Player activity and progress metrics
  system    Server performance (requests/s, latency)
  ml        ML service metrics (embedder, inference)
  registry  Service registry health stats

## EXAMPLES
  metrics
  metrics game
  metrics system
  metrics ml

## SEE ALSO
  health, version, chug, swarm

---
*Generated 2026-03-23*