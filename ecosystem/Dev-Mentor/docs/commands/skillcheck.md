# skillcheck

## NAME
skillcheck — perform a skill-based challenge roll

## SYNOPSIS
```
skillcheck <skill_name> <difficulty>
```

## DESCRIPTION
Roll a virtual d20 + skill bonus against a Difficulty Class (DC). Skill bonus is derived from your accumulated XP in the named skill (`skill_xp ÷ 50`). On success, awards +10 XP and grants lore. On failure, provides a hint.

## ARGUMENTS
- `skill_name` — any skill from your skill tree (e.g. networking, security, cryptography, social_engineering, programming, systems). Run `skills` to see your current XP.
- `difficulty` — integer DC target (typical: 8=easy, 12=medium, 16=hard, 20=near-impossible)

## EXAMPLES
```
skillcheck networking 12
skillcheck cryptography 16
skillcheck social_engineering 8
skillcheck security 20
```

## MECHANICS
```
roll = d20 + (skill_xp // 50)
success if roll >= difficulty
```

A level 1 player with 0 networking XP has a 65% chance of passing DC 8, 25% chance of DC 16.

## AWARDS
- Success: +10 XP, contextual flavor text
- Critical hit (natural 20): double XP

## SEE ALSO
`skills`, `archetype`, `challenge`, `nmap`
