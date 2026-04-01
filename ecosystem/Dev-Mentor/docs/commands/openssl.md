# OPENSSL(1) — Terminal Depths Man Page

## NAME
  openssl — in-game SSL/TLS toolkit

## SYNOPSIS
  openssl <subcommand> [args...]

## DESCRIPTION
SSL/TLS and cryptographic operations. Used in CTF challenges for certificate
analysis, RSA operations, and hash verification.

## EXAMPLES
  openssl x509 -in cert.pem -text
  openssl rsa -in private.pem -pubout
  openssl dgst -sha256 /tmp/file.dat
  openssl enc -d -aes-256-cbc -in secret.enc

## SEE ALSO
  decrypt, encrypt, crack, ssl

---
*Generated 2026-03-23*