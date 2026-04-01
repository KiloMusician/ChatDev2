# WAIT(1) — Terminal Depths Man Page

## NAME
  wait — wait for a background operation to complete

## SYNOPSIS
  wait [<job-id>]

## DESCRIPTION
Blocks until a backgrounded operation completes. Without arguments, waits for
all background jobs. With a job ID, waits for that specific job.

## EXAMPLES
  wait
  wait job-42

## SEE ALSO
  jobs, sleep, script

---
*Generated 2026-03-23*