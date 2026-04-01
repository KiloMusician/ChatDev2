# jack-in

Establish a direct neural uplink to a network node. Requires `lattice_tap` cyberware (neural slot) or `neural_ice` item. While jacked in, all commands execute at +30% XP bonus for 5 command cycles.

---

## SYNOPSIS

    jack-in <node>

---

## ARGUMENTS

    node    The node identifier to connect to (e.g. node-7, nexus-core, vault-9)

---

## REQUIREMENTS

    lattice_tap cyberware installed (preferred), OR
    neural_ice item in inventory (consumed on use)

---

## SESSION WINDOW

- Duration: 5 commands
- XP multiplier: +30% on all actions
- Faction comms are audible during jack-in (ambient Lattice messages)
- Connection drops after 5 commands or if trace exceeds 80%

---

## MECHANICS

Jack-in creates a direct mesh bridge to the target node. The Lattice Tap implant provides a clean interface — neural_ice provides a temporary tunneled connection. The experience is described differently by everyone who survives it.

---

## EXAMPLES

    jack-in node-7
    jack-in nexus-core
    jack-in vault-9

---

## LORE

"The mesh becomes a part of you. You start hearing it in your dreams.
Your dreams start appearing in the mesh."
— /opt/implants/lattice_tap_manual.txt

---

## SEE ALSO

    man cyberware, cyberware install lattice_tap, man ghost, man items
