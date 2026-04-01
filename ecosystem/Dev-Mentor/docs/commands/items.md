# items

Display your current item inventory — consumables, loot drops, and cascade rewards.

---

## SYNOPSIS

    items

---

## DESCRIPTION

Shows all items in your bag with quantities. Items are acquired via `loot`, cascade rewards, story triggers, and NPC interactions.

---

## ITEM CATALOG

    medkit              Reduces trace level by 15%
    stim_patch          +50% XP multiplier for next 3 commands
    emp_charge          Disables one NexusCorp scanner for 10 commands
    ghost_protocol_chip Activates Ghost Protocol for 10 commands (no implant required)
    neural_ice          Enables jack-in for one session (no lattice_tap required)
    scrambler           Wipes current session trace log
    credit_chip_50      50 credits (auto-deposit on use)
    credit_chip_200     200 credits
    credit_chip_500     500 credits — rare cascade drop

---

## ACQUIRING ITEMS

    loot <path>       Scavenge VFS paths for drops
    Story beats       Cascade engine drops on key progression moments
    NPC rewards       High-trust NPC interactions unlock item gifts
    Achievements      Milestone unlocks include item grants

---

## EXAMPLES

    items
    loot /var/nexus-leaks
    use medkit

---

## SEE ALSO

    man use, man loot, man cyberware, man ghost
