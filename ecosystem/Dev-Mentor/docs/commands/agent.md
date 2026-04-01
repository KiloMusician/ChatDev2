# AGENT(1) — Terminal Depths Man Page

## NAME
  agent — inspect or interact with a specific agent directly

## SYNOPSIS
  agent <name> [status|history|trust|brief]

## DESCRIPTION
Direct agent interface — view a single agent's trust level, interaction
history, current mission state, and personality brief. Differs from talk
which opens a dialogue; agent is a read-only dossier view.

## SUBCOMMANDS
  status    Current state and availability
  history   Interaction history with this agent
  trust     Trust level and relationship score
  brief     Personality and capability summary

## EXAMPLES
  agent ada status
  agent raven trust
  agent zero brief

## SEE ALSO
  talk, agents, osint, profile

---
*Generated 2026-03-23*