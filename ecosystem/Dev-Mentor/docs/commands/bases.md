# BASE64(1) — Terminal Depths Man Page

## NAME
  base64 — encode or decode base64 data

## SYNOPSIS
  base64 [encode|decode] <data>

## DESCRIPTION
Encodes or decodes base64 data. Frequently used in CTF challenges and ARG
puzzles. Many in-game files contain base64-encoded secrets.

## EXAMPLES
  base64 encode "hello world"
  base64 decode "aGVsbG8gd29ybGQ="
  cat /tmp/secret.b64 | base64 decode

## SEE ALSO
  xxd, hexdump, md5sum, sha256sum

---
*Generated 2026-03-23*