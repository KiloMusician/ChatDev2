# SPAWN_AGENT(1) — Terminal Depths Man Page

## NAME
  spawn_agent — create a new autonomous agent in the swarm

## SYNOPSIS
  spawn_agent <name> [<personality>]

## DESCRIPTION
Instantiates a new agent in the 71-agent orchestration swarm. The agent
receives a YAML personality file and begins executing its role in the
autonomous development loop. Requires swarm operator clearance.

## EXAMPLES
  spawn_agent watcher-delta vigilant
  spawn_agent epsilon-7 explorer

## SEE ALSO
  swarm, agents, chug, hive

---
*Generated 2026-03-23*