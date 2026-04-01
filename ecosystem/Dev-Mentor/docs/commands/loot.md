# loot

Scavenge a filesystem path for dropped items, cached credits, or abandoned cyberware. High-value paths yield better drops. Loot is added to your item bag and can be viewed with `items`.

---

## SYNOPSIS

    loot <path>

---

## ARGUMENTS

    path    Any readable VFS path (e.g. /var/nexus-leaks, /tmp, /opt/implants)

---

## DROP TABLE

Loot quality is influenced by:
- Path depth (deeper = rarer)
- Your current trust level with factions
- Whether Ghost Protocol is active (hidden caches revealed)
- Any installed optical cyberware (data_eye reveals extra drops)

Common drops:
    medkit              Restore 15% trace reduction
    stim_patch          +50% XP for next 3 commands
    emp_charge          Disable one NexusCorp scanner
    ghost_protocol_chip Temporary ghost protocol (no implant required)
    credit_chip_*       Credits ranging from 50 to 500

Rare drops:
    neural_ice          One-use jack-in without lattice_tap
    scrambler           Wipe trace log for current session

---

## EXAMPLES

    loot /var/nexus-leaks
    loot /tmp
    loot /opt/implants
    loot /home/ghost/.cache

---

## SEE ALSO

    man items, man use, man ghost, cyberware install data_eye
