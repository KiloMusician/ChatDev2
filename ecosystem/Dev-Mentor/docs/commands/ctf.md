# CTF(1) — Terminal Depths Man Page

## NAME
  ctf — Capture the Flag challenge board

## SYNOPSIS
  ctf [list|<id>|submit <flag>|hint <id>|leaderboard]

## DESCRIPTION
Alias for challenge with CTF-focused subcommands. Displays available CTF
challenges by category, shows detailed challenge info, and processes flag
submissions. Challenges span reverse engineering, cryptography, forensics,
web exploitation, and privilege escalation.

## SUBCOMMANDS
  list              Browse all challenges
  <id>              Challenge details and description
  submit <flag>     Submit a flag for the current challenge
  hint <id>         Request a hint (costs credits)
  leaderboard       Top solvers and points

## EXAMPLES
  ctf list
  ctf re-001
  ctf submit CTF{d3c0d3d}
  ctf leaderboard

## SEE ALSO
  challenge, flag, solve, submit, forensics

---
*Generated 2026-03-23*