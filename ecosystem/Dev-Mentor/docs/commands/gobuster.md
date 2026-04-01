# GOBUSTER(1) — Terminal Depths Man Page

## NAME
  gobuster — directory and file brute-force scanner

## SYNOPSIS
  gobuster dir -u <url> -w <wordlist>

## DESCRIPTION
Brute-forces hidden directories and files on virtual web servers. Discovers
admin panels, hidden endpoints, and CTF flag files on in-game web targets.

## EXAMPLES
  gobuster dir -u http://nexus-core -w common.txt
  gobuster dir -u http://chimera-web -w big.txt

## SEE ALSO
  scan, nmap, hack, wget

---
*Generated 2026-03-23*