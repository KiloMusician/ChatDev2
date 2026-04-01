# MITRE(1) — Terminal Depths Man Page

## NAME
  mitre — MITRE ATT&CK framework browser (Cybrary-inspired)

## SYNOPSIS
  mitre [tactics|tactic <TA####>|technique <T####>|search <term>]

## DESCRIPTION
Browse the MITRE ATT&CK Enterprise Matrix v18: 14 tactics, 216 techniques,
and 475 sub-techniques. Studying tactics awards XP and tracks toward the
ATT&CK Scholar achievement. Used by SOC analysts, red teamers, and defenders.

## TACTICS (14)
  TA0043  Reconnaissance        TA0001  Initial Access
  TA0002  Execution             TA0003  Persistence
  TA0004  Privilege Escalation  TA0005  Defense Evasion
  TA0006  Credential Access     TA0007  Discovery
  TA0008  Lateral Movement      TA0009  Collection
  TA0011  Command and Control   TA0010  Exfiltration
  TA0040  Impact                TA0042  Resource Development

## SUBCOMMANDS
  tactics              List all 14 enterprise tactics
  tactic <TA####>      Show tactic details and techniques (+10 XP)
  technique <T####>    Show technique detail (+5 XP)
  search <term>        Search across all tactics and techniques

## EXAMPLES
  mitre tactics
  mitre tactic TA0001
  mitre technique T1566
  mitre search phishing
  mitre search lateral

## ACHIEVEMENTS
  Study all 14 tactics → ATT&CK Scholar achievement (+100 XP)

## SEE ALSO
  assess, career, path, swarm, serena

---
*Generated 2026-03-23 | Source: MITRE ATT&CK v18 · Cybrary*