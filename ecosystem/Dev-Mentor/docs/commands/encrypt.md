# ENCRYPT(1) — Terminal Depths Man Page

## NAME
  encrypt — encrypt data for storage or transmission

## SYNOPSIS
  encrypt [--key <key>] [--cipher <name>] <data>

## DESCRIPTION
Encrypts data using various ciphers. Useful for securing exfiltrated
data before transmission and for understanding encryption in CTF challenges.

## OPTIONS
  --key <key>     Encryption key
  --cipher <n>    Cipher algorithm (aes, xor, caesar)

## EXAMPLES
  encrypt --cipher caesar "hello world"
  encrypt --key secret --cipher xor "payload data"

## SEE ALSO
  decrypt, base64, steg

---
*Generated 2026-03-23*