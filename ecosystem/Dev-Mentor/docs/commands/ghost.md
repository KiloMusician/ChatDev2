# ghost

Activate the Ghost Protocol — a sub-dermal EM scatter array that randomizes your electromagnetic signature 200 times/second. Requires the `ghost_chip` cyberware implant OR the `ghost_protocol_chip` consumable item.

---

## SYNOPSIS

    ghost <subcommand>

---

## SUBCOMMANDS

    activate          Enable Ghost Protocol stealth mode
    deactivate        Disable Ghost Protocol, reset blow risk
    status            Show current stealth state, charges, blow risk
    ping              Send a covert presence signal to known resistance nodes

---

## STEALTH MECHANICS

When Ghost Protocol is active:
- Trace is reduced by 60% passively
- Each command burns 1 ghost charge (starting pool: 20)
- Blow risk increases +5% per command after charge 15
- If cover is blown, Ghost Protocol auto-deactivates
- Wait 5 commands before re-activating after a blow

---

## HEAT INTERACTION

The `ghost_chip` implant generates +0.3% heat per command while Ghost Protocol is active. If heat exceeds 90%, glitch events may reveal your position unexpectedly.

---

## BLOW RISK

When blow risk exceeds 80%, NexusCorp scanners begin flagging your signature. Above 95%, blow is guaranteed on the next command.

---

## EXAMPLES

    ghost activate
    ghost status
    ghost ping
    ghost deactivate

---

## SEE ALSO

    man cyberware, cyberware install ghost_chip, man jack-in
