# STORY(1) — Terminal Depths Man Page

## NAME
  story — view story beat history and active narrative threads

## SYNOPSIS
  story [beats|threads|log|next]

## DESCRIPTION
The story command shows the current state of the narrative engine: triggered
story beats (117 registered), active threads, and what the next logical beat
is. Log shows full chronological beat history for your session.

## SUBCOMMANDS
  beats     All registered beats and their trigger status
  threads   Active narrative threads
  log       Chronological story event log
  next      Predicted next story beat based on current state

## EXAMPLES
  story
  story beats
  story log
  story next

## SEE ALSO
  arcs, arc, endings, converge, watcher

---
*Generated 2026-03-23*