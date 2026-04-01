# cyberware

Manage street-level cybernetic implants. Buy, install, monitor, and cool your augmentation loadout.

---

## SYNOPSIS

    cyberware <subcommand> [args]

---

## SUBCOMMANDS

    catalog                  Browse all available implants and prices
    install <id>             Purchase and install an implant (costs credits)
    uninstall <id>           Remove an implant (no refund)
    status                   Show installed implants, heat level, slot usage
    slots                    Display slot breakdown with installed/max counts
    cool                     Reduce heat by 15% (free action)
    info <id>                Detailed stats for a specific implant

---

## IMPLANT SLOTS

    cortex    3 slots — cognitive and memory augmentation
    reflex    2 slots — reaction and defensive systems
    optical   2 slots — vision and reconnaissance
    dermal    2 slots — stealth and armor-grade subdermal
    neural    1 slot  — rare high-tier Lattice integration

---

## HEAT SYSTEM

Each installed implant generates heat each command cycle. Heat accumulates and causes glitch events above 90%. At 100% the system auto-cools to 80% (painful). Use `cyberware cool` proactively.

---

## AVAILABLE IMPLANTS

    syn_cortex      800cr   cortex   +10% XP gain, +2 skill roll bonus
    mnemonic_lace  1500cr   cortex   command history +50, -5% puzzle fail
    overclock_v3   2500cr   cortex   2x XP for 10 commands after install
    reflex_buffer   600cr   reflex   auto-evade first intercept per session
    pain_editor    1200cr   reflex   50% trace escalation resistance
    data_eye        900cr   optical  reveals hidden files in ls output
    spectrum_scope 1800cr   optical  +15% exploit success, scan reveals
    ghost_chip     1400cr   dermal   -20% trace, unlocks ghost command
    ice_breaker    3000cr   dermal   +20% exploit success
    lattice_tap    5000cr   neural   +30% social XP, unlocks jack-in

---

## EXAMPLES

    cyberware catalog
    cyberware install ghost_chip
    cyberware cool
    cyberware status
    cyberware info lattice_tap

---

## SEE ALSO

    man ghost, man jack-in, cat /opt/implants/catalog.txt, man augment
