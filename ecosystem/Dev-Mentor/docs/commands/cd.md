# CD(1) — Terminal Depths Man Page

## NAME
  cd — change the current working directory in the virtual filesystem

## SYNOPSIS
  cd [<path>]

## DESCRIPTION
Navigates the Terminal Depths virtual filesystem. Supports absolute paths
(/home, /opt, /var), relative paths (../), and ~ for home. Mounted real
directories (e.g. /repos) are also traversable.

## EXAMPLES
  cd /home/ghost
  cd /opt/chimera
  cd ../
  cd ~
  cd /repos/NuSyQ-Hub

## SEE ALSO
  ls, pwd, cat, find, mount

---
*Generated 2026-03-23*