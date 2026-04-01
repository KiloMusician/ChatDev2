# HASHCAT(1) — Terminal Depths Man Page

## NAME
  hashcat — advanced password recovery

## SYNOPSIS
  hashcat [OPTIONS] <hash> <wordlist>

## DESCRIPTION
GPU-accelerated hash cracking tool. Faster than crack for large hash
databases. Supports MD5, SHA1, SHA256, NTLM, and bcrypt hash types.

## EXAMPLES
  hashcat -m 0 target.hash rockyou.txt
  hashcat -m 1000 ntlm.hash common.txt

## SEE ALSO
  crack, md5sum, sha256sum, wordlist

---
*Generated 2026-03-23*