# DECRYPT(1) — Terminal Depths Man Page

## NAME
  decrypt — decrypt an encrypted file or string

## SYNOPSIS
  decrypt [--key <key>] [--cipher <name>] <file|data>

## DESCRIPTION
Decrypts data using various cipher algorithms: AES, RSA, XOR, Caesar,
Vigenere. Used in CTF cryptography challenges. Key can be a file path or
inline string.

## OPTIONS
  --key <key>     Decryption key or key file
  --cipher <n>    Cipher algorithm (aes, rsa, xor, caesar)

## EXAMPLES
  decrypt --cipher caesar "khoor zruog"
  decrypt --key /tmp/private.pem --cipher rsa /tmp/secret.enc
  decrypt --cipher xor --key "deadbeef" /tmp/data.bin

## SEE ALSO
  encrypt, crack, base64, forensics

---
*Generated 2026-03-23*