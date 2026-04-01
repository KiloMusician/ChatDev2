# SCHEDULE(1) — Terminal Depths Man Page

## NAME
  schedule — manage scheduled tasks

## SYNOPSIS
  schedule [list|add <cmd> <interval>|remove <id>|run <id>]

## DESCRIPTION
The in-game task scheduler runs commands at specified intervals. Used for
automating reconnaissance, periodic health checks, and content generation
cycles. Similar to cron but operates in-session.

## SUBCOMMANDS
  list              Show all scheduled tasks
  add <cmd> <int>   Schedule a command at interval (seconds)
  remove <id>       Remove a scheduled task
  run <id>          Run a scheduled task immediately

## EXAMPLES
  schedule list
  schedule add "recon nexus-core" 300
  schedule run sched-001

## SEE ALSO
  crontab, jobs, script

---
*Generated 2026-03-23*