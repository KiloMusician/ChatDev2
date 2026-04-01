# WORDLIST(1) — Terminal Depths Man Page

## NAME
  wordlist — manage password wordlists

## SYNOPSIS
  wordlist [list|get <name>|custom <words>]

## DESCRIPTION
Manages wordlists used by crack and gobuster. Several built-in wordlists
are available (common, big, rockyou). Custom wordlists can be created from
gathered intelligence.

## EXAMPLES
  wordlist list
  wordlist get rockyou
  wordlist custom "nexuscorp chimera lattice ghost"

## SEE ALSO
  crack, gobuster, hashcat

---
*Generated 2026-03-23*