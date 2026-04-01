# RESET(1) — Terminal Depths Man Page

## NAME
  reset — reset game state components

## SYNOPSIS
  reset [<component>]

## DESCRIPTION
Resets specific game state components: timer (restart containment clock),
mole (clear investigation state), quests (clear generated quests),
skills (wipe skill XP). Full reset only via newgame.

## EXAMPLES
  reset timer
  reset quests
  reset mole

## SEE ALSO
  newgame, save, timer, mole

---
*Generated 2026-03-23*