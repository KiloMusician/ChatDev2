# CAPSTONE(1) — Terminal Depths Man Page

## NAME
  capstone — multi-stage capstone challenges (TCM Security-inspired)

## SYNOPSIS
  capstone [list|start <id>|status|submit <flag>]

## DESCRIPTION
Multi-stage challenge scenarios modelled on TCM Security's capstone boxes.
Each capstone has 4-5 progressive stages requiring real skills. Completing
a capstone awards large XP bonuses and adds to your portfolio.

## CAPSTONES
  operator-zero    Beginner — recon → access → escalate → exfil
  red-network      Intermediate — OSINT → phish → pivot → AD → impact
  chimera-final    Expert — infiltrate chimera's core (story-linked)
  arch-gauntlet    Advanced — assembly → reversing → heap → kernel → firmware

## SUBCOMMANDS
  list             Show all capstones and progress
  start <id>       Begin a capstone
  status           Current capstone progress
  submit <flag>    Submit the stage flag to advance

## EXAMPLES
  capstone list
  capstone start operator-zero
  capstone status
  capstone submit nexus-01
  capstone submit cmd-exec

## SEE ALSO
  pentest, ctf, challenge, path, portfolio

---
*Generated 2026-03-23 | Source: TCM Security PJPT capstone*