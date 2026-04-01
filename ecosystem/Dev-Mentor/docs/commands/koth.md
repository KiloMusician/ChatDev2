# KOTH(1) — Terminal Depths Man Page

## NAME
  koth — King of the Hill competitive hacking mode (TryHackMe-inspired)

## SYNOPSIS
  koth [status|join|claim|defend|scores]

## DESCRIPTION
Competitive multiplayer hacking mode. Hack a target node, gain root access,
write your username to /root/king.txt, and defend your position against
rivals. Points are awarded for time as King and patches applied.

## MECHANICS
  - 60-minute sessions
  - Gain root access to become King
  - Write username to /root/king.txt to claim throne
  - Patch vulnerabilities to block rivals (+25 pts/patch)
  - Most total points wins (not just final King)

## SUBCOMMANDS
  status    Current game state and active King
  join      Enter a new KotH session
  claim     Write to king.txt (requires root access)
  defend    Apply vulnerability patches (+25 pts each)
  scores    Live scoreboard

## EXAMPLES
  koth join
  hack nexus-core
  exploit CVE-2021-3156
  koth claim
  koth defend
  koth scores

## SEE ALSO
  hack, exploit, escalate, scan, leaderboard

---
*Generated 2026-03-23 | Source: TryHackMe King of the Hill*