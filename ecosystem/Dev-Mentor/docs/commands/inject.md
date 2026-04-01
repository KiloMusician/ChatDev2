# INJECT(1) — Terminal Depths Man Page

## NAME
  inject — inject a payload into a running process or file

## SYNOPSIS
  inject <target> <payload>

## DESCRIPTION
Injects a payload into a running virtual process or modifies a file in-place.
Used in privilege escalation and exploit challenges. Requires an active shell
session on the target or write access to the target file.

## EXAMPLES
  inject chimera-daemon stealth-rootkit
  inject /usr/bin/sudo setuid-patch
  inject nexus-agent memory-exploit

## SEE ALSO
  exploit, hack, backdoor, exec_script

---
*Generated 2026-03-23*