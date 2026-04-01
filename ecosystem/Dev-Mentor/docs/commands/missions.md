# MISSIONS(1) — Terminal Depths Man Page

## NAME
  missions — view and manage active missions

## SYNOPSIS
  missions [list|<id>|accept <id>|abandon <id>|complete]

## DESCRIPTION
The mission system tracks all active and available operations: story missions,
faction missions, and agent-issued tasks. Completing missions awards XP,
credits, and advances story arcs.

## SUBCOMMANDS
  list           All available and active missions
  <id>           Mission briefing and objectives
  accept <id>    Accept a mission
  abandon <id>   Abandon a mission
  complete       Check completion status of active missions

## EXAMPLES
  missions list
  missions m-042
  missions accept m-042
  missions complete

## SEE ALSO
  quests, faction, party, challenge

---
*Generated 2026-03-23*