# CHMOD(1) — Terminal Depths Man Page

## NAME
  chmod — change file permissions in the virtual filesystem

## SYNOPSIS
  chmod <mode> <path>

## DESCRIPTION
Modifies file permission bits on virtual filesystem nodes. Unlocks or restricts
access to sensitive files. Some paths require root context or specific story
beats to modify.

## EXAMPLES
  chmod 600 /home/ghost/.ssh/id_rsa
  chmod 755 /opt/chimera/core/run.sh
  chmod 777 /tmp/payload.sh

## SEE ALSO
  chown, ls, cat, sudo

---
*Generated 2026-03-23*