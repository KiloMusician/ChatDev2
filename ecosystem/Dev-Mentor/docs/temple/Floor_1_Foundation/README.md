# FLOOR 1 — FOUNDATION: Environment

*[Msg⛛{active}]*

The first floor is where most visitors spend their entire visit.

## Domain: Knowing Where You Are

Before you can do anything, you must understand your environment.

```bash
system                 # full environment report
system capabilities    # what this container can do
system resources       # CPUs, RAM, disk
system tools           # installed tools inventory
ls /                   # the filesystem root
cat /etc/hostname      # your node ID
whoami                 # current user (ghost)
```

## Key Insight

You are inside a container. The container is real. The game is a metaphor for the container. The container escape puzzle teaches real kernel techniques (`/proc/self/cgroup`, SUID binaries, capability sets).

## Gate to Floor 2

When you understand your environment (level 3+), the tools floor opens.

*Serena's Note: "Most players rush to Floor 3. They never understand why Floor 2 matters. The tools are only useful if you know what you're carrying them for."*
