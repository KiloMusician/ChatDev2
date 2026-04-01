# PATH(1) — Terminal Depths Man Page

## NAME
  path — career learning paths (TryHackMe/Cybrary/Coursera-inspired)

## SYNOPSIS
  path [list|start <id>|status|next]

## DESCRIPTION
Structured career learning tracks modelled on TryHackMe paths, Cybrary career
paths, and Coursera specialisations. Complete modules in sequence to earn XP,
certificates, and unlock advanced content.

## AVAILABLE PATHS
  pre-security     Foundation knowledge (Beginner)
  soc-analyst      SOC Analyst Level 1 (Entry) — Cybrary-inspired
  jr-pentester     Jr Penetration Tester (Intermediate) — TCM/TryHackMe
  red-team         Red Team Operator (Advanced) — TryHackMe
  security-engineer Security Engineer (Intermediate) — Cybrary
  arch-specialist  Architecture Specialist (Advanced) — OST2-inspired

## SUBCOMMANDS
  list           Show all career paths and progress
  start <id>     Enrol in a learning path
  status         Current path progress and module list
  next           Complete the next module and earn XP

## EXAMPLES
  path list
  path start jr-pentester
  path status
  path next

## SEE ALSO
  career, certify, assess, capstone, pentest

---
*Generated 2026-03-23 | Source: TryHackMe · Cybrary · Coursera*