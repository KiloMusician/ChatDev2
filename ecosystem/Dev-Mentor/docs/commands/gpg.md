# GPG(1) — Terminal Depths Man Page

## NAME
  gpg — GNU Privacy Guard operations

## SYNOPSIS
  gpg [--encrypt|--decrypt|--sign|--verify] <file>

## DESCRIPTION
GPG encryption and signing operations. Some ARG fragments and CTF flags are
GPG-encrypted. Use with keys found in /home/ghost/.gnupg/ or recovered
through other means.

## EXAMPLES
  gpg --decrypt secret.gpg
  gpg --verify message.sig message.txt
  gpg --encrypt --recipient ada message.txt

## SEE ALSO
  openssl, decrypt, encrypt, forensics

---
*Generated 2026-03-23*