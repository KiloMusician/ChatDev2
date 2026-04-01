# use

Consume a single-use item from your inventory. Items have immediate effects and are removed from your bag on use.

---

## SYNOPSIS

    use <item>

---

## ARGUMENTS

    item    The item identifier (see `items` for your current bag)

---

## ITEM EFFECTS

    medkit              -15% trace level. Emergency trace reduction.
    stim_patch          +50% XP for the next 3 commands.
    emp_charge          Disables one active NexusCorp scanner (10 cmd window).
    ghost_protocol_chip Activates Ghost Protocol for 10 commands.
    neural_ice          Enables jack-in to any node for one session.
    scrambler           Wipes the current session's entire trace log.
    credit_chip_50      Deposits 50 credits to your account.
    credit_chip_200     Deposits 200 credits.
    credit_chip_500     Deposits 500 credits.

---

## EXAMPLES

    use medkit
    use stim_patch
    use emp_charge
    use ghost_protocol_chip
    use neural_ice

---

## ERRORS

    use: no <item> in inventory   — You don't have this item. Run: loot <path> to find it.

---

## SEE ALSO

    man items, man loot, man ghost, man jack-in
