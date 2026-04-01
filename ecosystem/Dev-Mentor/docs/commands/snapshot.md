# SNAPSHOT(1) — Terminal Depths Man Page

## NAME
  snapshot — capture the current game state snapshot

## SYNOPSIS
  snapshot [create|list|restore <id>|diff <id1> <id2>]

## DESCRIPTION
Creates a named snapshot of the current game state for comparison or
rollback. Snapshots capture XP, story beats, VFS state, and agent
relationships.

## EXAMPLES
  snapshot create
  snapshot list
  snapshot restore snap-42
  snapshot diff snap-40 snap-42

## SEE ALSO
  save, load, status

---
*Generated 2026-03-23*