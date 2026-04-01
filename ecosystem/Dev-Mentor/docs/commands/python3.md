# PYTHON3(1) — Terminal Depths Man Page

## NAME
  python3 — run Python in the virtual environment

## SYNOPSIS
  python3 [<file>|-c <code>]

## DESCRIPTION
Executes Python code in the Terminal Depths sandbox. Useful for quick
calculations, data processing, and CTF challenge scripting. Has access
to the game API via import terminal_depths.

## EXAMPLES
  python3 -c "print('hello world')"
  python3 script.py
  python3 -c "from terminal_depths import api; print(api.player_level())"

## SEE ALSO
  script, run, exec_script

---
*Generated 2026-03-23*