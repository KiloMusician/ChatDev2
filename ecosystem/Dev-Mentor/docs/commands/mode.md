# mode

## NAME
mode — toggle game experience mode

## SYNOPSIS
```
mode [horror|cosy|default]
mode
```

## DESCRIPTION
Adjusts the tone and content of your Terminal Depths experience. Mode persists across sessions.

## MODES
- `horror` — darker ambient content, SCP-Keter events more frequent, corrupted text on high trace
- `cosy` — softer palette descriptions, warmer agent dialogue, reduced threat intensity
- `default` — standard cyberpunk experience

## EXAMPLES
```
mode horror
mode cosy
mode            (shows current mode)
mode default    (resets to standard)
```

## SEE ALSO
`status`, `ambient`, `hive`
