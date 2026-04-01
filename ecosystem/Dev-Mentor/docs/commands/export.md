# EXPORT(1) — Terminal Depths Man Page

## NAME
  export — set virtual environment variables

## SYNOPSIS
  export <VAR>=<value>

## DESCRIPTION
Sets a variable in the current shell environment for the session. Exported
variables are accessible via $VAR expansion in echo and scripts.
Note: only affects the virtual shell environment, not real system env.

## EXAMPLES
  export TARGET=nexus-core
  export DEBUG=1
  export FACTION=chimera

## SEE ALSO
  env, echo, script

---
*Generated 2026-03-23*