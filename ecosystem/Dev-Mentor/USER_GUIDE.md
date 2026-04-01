# Terminal Depths — Player Guide

## What Is Terminal Depths?

Terminal Depths is a cyberpunk terminal RPG built into DevMentor. You play as **GHOST**, an operative trapped on **Node-7** of the NexusCorp surveillance grid. Your mission: use real Linux/Unix commands to hack, recon, escalate privileges, and expose the CHIMERA AI.

**You learn real terminal skills as you play.** Every command you run is authentic Unix.

---

## Quick Start

1. Open the game at **`/game`** from the DevMentor Console
2. The terminal starts with `ghost@node-7:~$`
3. Type `help` to see all available commands
4. Type `tutorial` to see your current learning objective
5. Run commands — every action earns XP and teaches real skills

---

## Interface Overview

```
┌──────────────────────────────────────────────────────────────┐
│  ▓ TERMINAL DEPTHS  Node-7 · NexusCorp   [⌨ SFX] [♪ Music] │
├─────────────────────────────────────┬────────────────────────┤
│                                     │  [OBJ][STATS][TUT]     │
│   TERMINAL (main area)              │  [CHAL][LORE][MAP]     │
│   Commands run here                 │  [LOG][TREE]           │
│                                     │                        │
│   ghost@node-7:~$  _               │   Info Panel           │
└─────────────────────────────────────┴────────────────────────┘
```

### Info Panel Tabs

| Tab | Content |
|-----|---------|
| **OBJ** | Current mission objective and story beats |
| **STATS** | Level, XP, skill bars, karma, achievements |
| **TUT** | Tutorial progress (42 steps) |
| **CHAL** | Challenge list — 40 challenges to complete |
| **LORE** | Discovered lore fragments |
| **MAP** | NexusCorp network grid — click nodes to scan |
| **LOG** | Timeline feed of all significant events |
| **TREE** | Visual SVG skill tree with unlock milestones |

### Sound Controls

- **⌨ button** — Toggle keyboard click SFX (stored in your browser)
- **♪ button** — Toggle ambient cyberpunk music
- Music automatically intensifies during hack commands

---

## Progression System

### Levels (1–125)

XP accumulates from commands and challenges. Each level grants new story and NPC interactions.

### 8 Phases

| Phase | Levels | Description |
|-------|--------|-------------|
| 0 — INERT | 1–5 | System barely responsive |
| 1 — HOPELESS | 6–15 | Neural pathways initialising |
| 2 — NOVICE | 16–30 | Pattern recognition online |
| 3 — FOUNDATIONAL | 31–40 | Core skillset acquired |
| 4 — COMPETENT | 41–55 | NexusCorp threat level raised |
| 5 — EXPERT | 56–75 | You move like a ghost |
| 6 — TRANSCENDENT | 76–90 | Simulation strains to contain you |
| 7 — INEFFABLE | 91–100 | Beyond classification |
| 8 — META | 101–125 | You are the simulation |

### 5 Skills

Each skill reaches 0–100% through use:

- **Terminal** — cd, ls, cat, grep, awk, sed, pipes
- **Networking** — nmap, ping, nc, curl, dig
- **Security** — find -perm, strace, exploit, sudo
- **Programming** — python3, bash scripting, awk
- **Git** — git log, stash, rebase, bisect

Reach milestones (25%, 50%, 75%, 100%) to unlock abilities.

### Consciousness, Karma, Prestige

- **Consciousness** (0–100): Rises as you discover deeper truths
- **Karma**: Affected by choices with NPCs and factions
- **Ascension**: Type `ascend` at high level to prestige — carry skill memory into a new life

---

## Core Commands Reference

### Filesystem

```bash
ls -la          # list files including hidden
cd /path        # change directory
cat file.txt    # read file
find / -name "*.log"  # search files
mkdir dir       # create directory
mv old new      # rename/move
cp src dst      # copy
rm -rf dir      # remove (careful!)
```

### Text Processing

```bash
grep -r CHIMERA /var/log/   # search in files
awk '{print $1}' file       # field extraction
sed 's/old/new/g' file      # substitute text
sort, uniq, wc, head, tail  # standard tools
```

### Networking

```bash
ping 10.0.1.100         # test connectivity
nmap -sV 10.0.1.254     # port scan
nc chimera-control 8443 # connect to port
curl http://nexus.corp  # HTTP request
dig nexus.corp          # DNS lookup
```

### Security / Exploitation

```bash
sudo -l                 # check sudo privileges
find / -perm -u=s       # find SUID binaries
sudo find . -exec /bin/sh \;   # GTFOBins root exploit
ssh ghost@nexus-db      # SSH to another node
strace -p 1337          # trace process
```

### Game-Specific Commands

```bash
help                    # all commands list
tutorial                # current tutorial step
phase                   # show current phase
skills                  # display skill stats
challenges              # view challenge list
talk ada                # chat with NPC Ada
talk nova               # chat with Agent Nova
talk watcher            # contact The Watcher (ARG)
faction resistance      # join the Resistance
faction corp            # join NexusCorp
map                     # ASCII network map
signal                  # scan for ARG signals
hack chimera-control    # attempt to hack CHIMERA
exfil                   # exfiltrate data (after root)
ascend                  # prestige reset
crack passwords.txt     # crack password hashes
expose <agent>          # reveal the mole
```

### AI Commands

```bash
ai "What should I do next?"     # ask AI game master
ask ada "How do I get root?"    # ask specific NPC
```

### Developer Mode (advanced)

```bash
devmode                 # toggle developer mode
inspect <npc>           # inspect NPC state
spawn <npc>             # spawn an NPC
teleport <node>         # jump to network node
profile commands        # performance profiling
generate challenge      # LLM-generate a challenge
```

---

## Clickable Interface Elements

The game supports **click-to-fill** interactions:

- **`ls` output** — Click a filename to fill `cat <file>` in the input. Double-click to run it.
- **NPC names** — Click `[ADA-7]` or any NPC tag to fill `talk <npc>` in the input.
- **Map nodes** — Click a network node to fill `ping <ip>`. Double-click to run `nmap`.
- **Command history** — Click a previous command in the terminal to re-fill it. Double-click to re-run.

---

## NPC Roster

| NPC | Role | Command |
|-----|------|---------|
| **ADA-7** | Mentor, always helpful | `talk ada` |
| **Nova** | Antagonist, corp spy | `talk nova` |
| **Cypher** | Hacker ally | `talk cypher` |
| **Watcher** | Mysterious ARG entity | `talk watcher` (unlockable) |
| **Prometheus** | Resistance commander | `talk prometheus` |
| **Anansi** | Trickster info broker | `talk anansi` |
| **Solon** | Strategist | `talk solon` |
| **Echo** | Intel specialist | `talk echo` |
| **Daedalus** | Engineer | `talk daedalus` |
| **Zero** | Unknown presence | `talk zero` (ARG) |

---

## Walkthrough: First 10 Minutes

1. **`ls -la`** — See your home directory including hidden files
2. **`cat /var/msg/ada`** — Read Ada's first message
3. **`tutorial`** — See your current learning objective
4. **`grep CHIMERA /var/log/nexus.log`** — Find your first lead
5. **`talk ada`** — Ask Ada what to do next
6. **`find / -name "*.key"`** — Search for encryption keys
7. **`sudo -l`** — Check your sudo privileges
8. **`ps aux | grep nexus`** — Find the surveillance daemon
9. **`nmap -sV 10.0.1.254`** — Scan CHIMERA control node
10. **`hack chimera-control`** — Begin your mission

---

## The ARG Layer

Terminal Depths has a hidden ARG (Alternate Reality Game) layer:

- **`signal`** — Scan for hidden radio signals in the grid
- **`signal analyze <id>`** — Decode a captured signal
- **`myth`** — Discover hidden mythology references
- **`watcher`** — Contact The Watcher (requires story progress)
- **`expose <agent>`** — Reveal a mole (requires 3 clues)

Find the three clue files:
```
/var/log/.anomaly_0x4A2B.log
/tmp/.transfer_847b.partial
/opt/chimera/cache/.internal_847.memo
```

---

## Factions

Choose your path with `faction <name>`:

| Faction | Style | Effect |
|---------|-------|--------|
| **resistance** | +Karma, story depth | Anti-corporate path |
| **corp** | -Karma, power route | Ruthless efficiency |

---

## Saving Progress

Your game state is automatically saved to `localStorage`. It persists between browser sessions. Type `save` to manually checkpoint.

---

## Tips & Tricks

- **Tab completion** works on commands and file paths
- **Arrow Up/Down** cycles through command history
- **Ctrl+L** clears the terminal
- **Ctrl+C** cancels current input
- **Pipe commands**: `cat /etc/passwd | grep ghost | awk -F: '{print $3}'`
- **Redirect output**: `nmap -sV 10.0.1.254 > scan_results.txt`
- The **LOG tab** shows a full chronological event history
- The **TREE tab** shows your skill progression with SVG visualization

---

## Modding

See [`docs/MODDING.md`](docs/MODDING.md) for instructions on adding custom commands, challenges, agents, and story beats.
