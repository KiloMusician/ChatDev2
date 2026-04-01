# STEG(1) — Terminal Depths Man Page

## NAME
  steg — steganography tool for ARG challenges

## SYNOPSIS
  steg [encode <file> <msg>|decode <file>|analyze <file>]

## DESCRIPTION
The steg tool handles steganographic encoding and decoding. Used in forensics
and ARG challenges to hide and reveal messages within files. Many ARG
fragments contain steganographic data.

## EXAMPLES
  steg analyze /home/ghost/image.png
  steg decode /tmp/suspect.jpg
  steg encode /tmp/cover.png "hidden message"

## SEE ALSO
  forensics, binwalk, hexdump, osint

---
*Generated 2026-03-23*