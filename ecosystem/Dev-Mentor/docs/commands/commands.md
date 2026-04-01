# commands

## NAME
commands — search and browse all available commands

## SYNOPSIS
```
commands search <query>
commands list
```

## DESCRIPTION
The command palette for Terminal Depths. Browse, search, and discover all 469+ available commands by name or description.

## SUBCOMMANDS

### commands search \<query\>
Fuzzy-search all command names and their descriptions. Returns a ranked list of matches.

```
commands search faction     # find all faction-related commands
commands search puzzle      # find puzzle commands
commands search file        # find file operations
```

### commands list
Display all commands in a compact 4-column grid, grouped alphabetically.

## EXAMPLES
```
commands search network
commands search story
commands search boss
commands list
```

## TIPS
- Use `man <command>` to read the full documentation for any command
- Commands are case-insensitive
- Use `help` for a categorized overview

## SEE ALSO
`help`, `man`, `skills`, `quests`
