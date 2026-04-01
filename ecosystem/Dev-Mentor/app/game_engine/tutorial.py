"""
Terminal Depths — Tutorial Engine (Python port of tutorial.js)
42-step guided training sequence.

Multi-variant steps: some steps require the player to try multiple
commands before advancing, giving acknowledgment for each one.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Set


# ── Variant helper ─────────────────────────────────────────────────────────
def _v(cmd: str, match: str, label: str) -> Dict[str, str]:
    """Shorthand for a variant entry."""
    return {"cmd": cmd, "match": match, "label": label}


STEPS: List[Dict[str, Any]] = [
    # ORIENTATION
    {"id": 1, "section": "Orientation", "title": "Where Am I?",
     "objective": "Find out where you are. Run `pwd`.",
     "hint": "pwd = Print Working Directory. Always know your location.",
     "match": r"^pwd$", "xp": 10},

    {"id": 2, "section": "Orientation", "title": "List Files",
     "objective": "List files in your home directory with `ls`.",
     "hint": "ls shows directory contents.",
     "match": r"^ls(\s|$)", "xp": 10},

    {"id": 3, "section": "Orientation", "title": "Who Am I?",
     "objective": "Identify yourself with `whoami`.",
     "hint": "whoami prints your username. Know your identity on the grid.",
     "match": r"^whoami$", "xp": 10},

    {"id": 4, "section": "Orientation", "title": "Read the README",
     "objective": "Read README.md with `cat README.md`.",
     "hint": "cat prints file contents. README files are always the first door.",
     "match": r"cat\s+.*README", "xp": 15},

    {"id": 5, "section": "Orientation", "title": "Hidden Files",
     "objective": "Show hidden files with `ls -la`.",
     "hint": "The -a flag shows dotfiles (files starting with .). -l gives long format.",
     "match": r"ls\s+.*-\w*a", "xp": 15},

    # NAVIGATION
    {"id": 6, "section": "Navigation", "title": "Change Directory",
     "objective": "Navigate to /var/log with `cd /var/log`.",
     "hint": "cd changes directory. /var/log holds system event logs.",
     "match": r"cd\s+/var/log", "xp": 10},

    {"id": 7, "section": "Navigation", "title": "Read a Log",
     "objective": "Read nexus.log with `cat nexus.log`.",
     "hint": "Log files reveal what happened. nexus.log has CHIMERA traffic.",
     "match": r"cat\s+.*nexus\.log", "xp": 20},

    # Multi-variant step: try BOTH cd ~ and cd (no args)
    {"id": 8, "section": "Navigation", "title": "Back Home — Two Ways",
     "objective": "Return home TWO ways: first try `cd ~`, then try `cd` (no arguments).",
     "hint": "Both `cd ~` and bare `cd` return to home. Try each — same destination, different syntax.",
     "match": r"^cd(\s+~|\s+\$HOME|)$",
     "xp": 15,
     "variants": [
         _v("cd ~",   r"^cd\s+~$",     "tilde shorthand — cd ~ always means home"),
         _v("cd",     r"^cd$",          "bare cd — no argument defaults to home"),
     ]},

    {"id": 9, "section": "Navigation", "title": "Explore /etc",
     "objective": "List files in /etc.",
     "hint": "ls /etc — system configuration lives here. passwd, shadow, hosts.",
     "match": r"ls\s+(/etc|/etc/)", "xp": 10},

    {"id": 10, "section": "Navigation", "title": "Read passwd",
     "objective": "Read /etc/passwd to enumerate users.",
     "hint": "cat /etc/passwd — shows system accounts. Format: name:x:uid:gid:...",
     "match": r"cat\s+/etc/passwd", "xp": 20},

    # TEXT TOOLS
    {"id": 11, "section": "Text Tools", "title": "Search with grep",
     "objective": "Use grep to find 'CHIMERA' in nexus.log.",
     "hint": "grep CHIMERA /var/log/nexus.log — grep is pattern search.",
     "match": r"grep\s+.*CHIMERA", "xp": 20},

    # Multi-variant: try BOTH awk AND cut
    {"id": 12, "section": "Text Tools", "title": "Filter Users — Two Tools",
     "objective": "Extract usernames from /etc/passwd using BOTH awk AND cut.",
     "hint": "Try awk first: `awk -F: '{print $1}' /etc/passwd`, then cut: `cut -d: -f1 /etc/passwd`",
     "match": r"(awk|cut)\s+.*passwd",
     "xp": 30,
     "variants": [
         _v("awk -F: '{print $1}' /etc/passwd", r"awk\s+.*passwd", "awk: field processor, -F sets delimiter"),
         _v("cut -d: -f1 /etc/passwd",           r"cut\s+.*passwd", "cut: simpler, -d sets delimiter, -f selects field"),
     ]},

    {"id": 13, "section": "Text Tools", "title": "Sort Output",
     "objective": "Sort /etc/passwd alphabetically.",
     "hint": "cat /etc/passwd | sort — sort orders lines. Piping chains commands.",
     "match": r"sort\s+.*passwd|passwd.*\|\s*sort", "xp": 15},

    {"id": 14, "section": "Text Tools", "title": "Word Count",
     "objective": "Count lines in a log file with wc -l.",
     "hint": "cat /var/log/nexus.log | wc -l — wc -l counts newlines.",
     "match": r"wc\s+.*-\w*l|wc\s+.*nexus", "xp": 15},

    {"id": 15, "section": "Text Tools", "title": "Pipeline Power",
     "objective": "Chain grep and sort with a pipe (|).",
     "hint": "grep ghost /etc/passwd | sort — the pipe | sends output to the next command.",
     "match": r"\|", "xp": 20},

    # SYSTEM RECON
    {"id": 16, "section": "Recon", "title": "Process List",
     "objective": "List running processes with `ps aux`.",
     "hint": "ps aux shows all processes. Look for CHIMERA daemons.",
     "match": r"ps\s+.*aux|ps\s+.*a", "xp": 20},

    {"id": 17, "section": "Recon", "title": "Find SUID Binaries",
     "objective": "Find SUID binaries with `find / -perm -u=s -type f`.",
     "hint": "SUID binaries run as their owner (often root) — escalation vectors.",
     "match": r"find\s+.*perm\s+.*[su]", "xp": 30},

    # Multi-variant: try BOTH ss AND netstat
    {"id": 18, "section": "Recon", "title": "Open Ports — Two Tools",
     "objective": "See listening ports with BOTH `ss -tulpn` AND `netstat -tulpn`.",
     "hint": "Try ss first (modern), then netstat (classic). Port 8443 is CHIMERA's control socket.",
     "match": r"ss\s+.*tulpn|netstat",
     "xp": 30,
     "variants": [
         _v("ss -tulpn",      r"ss\s+.*tulpn",  "ss: modern socket statistics (iproute2)"),
         _v("netstat -tulpn", r"netstat",         "netstat: classic net-tools, still widely used"),
     ]},

    {"id": 19, "section": "Recon", "title": "Check Environment",
     "objective": "Read /proc/1337/environ to find leaked secrets.",
     "hint": "cat /proc/1337/environ | tr '\\0' '\\n' — process env vars are in /proc/<pid>/environ.",
     "match": r"1337.*environ|environ.*1337|cat\s+/proc/1337", "xp": 35},

    {"id": 20, "section": "Recon", "title": "Check Sudoers",
     "objective": "Check your sudo privileges with `sudo -l`.",
     "hint": "sudo -l lists allowed (and forbidden) commands. Look for NOPASSWD entries.",
     "match": r"^sudo\s+-l$", "xp": 25},

    # CRYPTO & ENCODING
    {"id": 21, "section": "Crypto", "title": "Decode Base64",
     "objective": "Decode mission.enc with base64 -d.",
     "hint": "cat mission.enc | base64 -d — base64 is common encoding, not encryption.",
     "match": r"base64\s+.*-d|base64\s+.*decode", "xp": 30},

    # Multi-variant: try BOTH xxd AND hexdump
    {"id": 22, "section": "Crypto", "title": "Hex Inspection — Two Tools",
     "objective": "Inspect a binary with BOTH `xxd` AND `hexdump`.",
     "hint": "Try xxd first: `xxd /opt/chimera/data/collected.db | head`, then hexdump: `hexdump -C /opt/chimera/data/collected.db | head`",
     "match": r"xxd|hexdump|od\s",
     "xp": 25,
     "variants": [
         _v("xxd /opt/chimera/data/collected.db | head",      r"xxd",       "xxd: hex+ASCII dump, most readable"),
         _v("hexdump -C /opt/chimera/data/collected.db | head", r"hexdump",  "hexdump -C: canonical format, similar to xxd"),
     ]},

    # NETWORKING
    {"id": 23, "section": "Networking", "title": "Ping a Host",
     "objective": "Test connectivity with `ping -c 3 nexus.corp`.",
     "hint": "ping sends ICMP echo requests. -c 3 sends exactly 3 packets then stops.",
     "match": r"^ping\s+", "xp": 15},

    # Multi-variant: try BOTH dig AND nslookup
    {"id": 24, "section": "Networking", "title": "DNS Lookup — Two Tools",
     "objective": "Resolve a hostname with BOTH `dig` AND `nslookup`.",
     "hint": "Try dig first: `dig nexus.corp`, then nslookup: `nslookup chimera-control`",
     "match": r"^dig\s+|^nslookup\s+",
     "xp": 20,
     "variants": [
         _v("dig nexus.corp",            r"^dig\s+",       "dig: modern DNS tool, verbose output"),
         _v("nslookup chimera-control",  r"^nslookup\s+",  "nslookup: classic, simpler output"),
     ]},

    {"id": 25, "section": "Networking", "title": "Scan Ports",
     "objective": "Scan nexus.corp with nmap.",
     "hint": "nmap -sV nexus.corp — -sV attempts to detect service versions.",
     "match": r"^nmap\s+", "xp": 25},

    {"id": 26, "section": "Networking", "title": "Connect to CHIMERA",
     "objective": "Connect to chimera-control port 8443 with nc.",
     "hint": "nc chimera-control 8443 — netcat is the 'Swiss Army knife' of networking.",
     "match": r"nc\s+chimera-control", "xp": 40},

    # PRIVILEGE ESCALATION
    {"id": 27, "section": "PrivEsc", "title": "GTFOBins Exploit",
     "objective": "Use find to get a root shell: `sudo find . -exec /bin/sh \\;`",
     "hint": "sudo find . -exec /bin/sh \\; — spawns root shell via GTFOBins misconfig.",
     "match": r"sudo\s+find.*exec.*/bin/sh", "xp": 80},

    {"id": 28, "section": "PrivEsc", "title": "Read Shadow",
     "objective": "As root, read /etc/shadow.",
     "hint": "cat /etc/shadow — only root can read this. Contains hashed passwords.",
     "match": r"cat\s+/etc/shadow", "xp": 30},

    {"id": 29, "section": "PrivEsc", "title": "Read Master Key",
     "objective": "Read /opt/chimera/keys/master.key.",
     "hint": "cat /opt/chimera/keys/master.key — the key to CHIMERA's control plane.",
     "match": r"master\.key", "xp": 50},

    # EXPLOITATION
    {"id": 30, "section": "Exploitation", "title": "Talk to Ada",
     "objective": "Contact your handler: `talk ada`.",
     "hint": "Ada has critical intel for you. She's been waiting.",
     "match": r"^talk\s+ada", "xp": 20},

    {"id": 31, "section": "Exploitation", "title": "Check Your Tools",
     "objective": "Check your tools with `inventory`.",
     "hint": "inventory shows what you have. Know your loadout.",
     "match": r"^inventory$", "xp": 10},

    {"id": 32, "section": "Exploitation", "title": "Install a Tool",
     "objective": "Install a tool: `apt install nmap`.",
     "hint": "apt install <tool> — package management. Tools are power.",
     "match": r"apt\s+install|pkg\s+install", "xp": 15},

    {"id": 33, "section": "Exploitation", "title": "Exploit CHIMERA",
     "objective": "Run `exploit chimera` after connecting.",
     "hint": "First: nc chimera-control 8443, then exploit chimera. Timing matters.",
     "match": r"^exploit\s+chimera$", "xp": 60},

    {"id": 34, "section": "Exploitation", "title": "Exfiltrate Data",
     "objective": "Run `exfil` to transmit captured data to Ada.",
     "hint": "exfil — uploads all evidence. Don't leave traces.",
     "match": r"^exfil$", "xp": 75},

    {"id": 35, "section": "Exploitation", "title": "Ascend",
     "objective": "Run `ascend` to complete the mission.",
     "hint": "ascend — the final step. You've earned it. The loop ends here.",
     "match": r"^ascend$", "xp": 100},

    # SKILLS
    {"id": 36, "section": "Skills", "title": "View Skills",
     "objective": "Check your skill matrix with `skills`.",
     "hint": "skills shows all your stats. Everything you've done is tracked.",
     "match": r"^skills$", "xp": 10},

    {"id": 37, "section": "Skills", "title": "Write a Script",
     "objective": "Run python3 inline: `python3 -c \"print('hello')\"`.",
     "hint": "python3 -c '...' runs inline Python. No file needed.",
     "match": r"python3\s+.*-c", "xp": 20},

    {"id": 38, "section": "Skills", "title": "Git Log",
     "objective": "View git history with `git log`.",
     "hint": "git log shows commits. History is evidence.",
     "match": r"^git\s+log", "xp": 15},

    {"id": 39, "section": "Skills", "title": "System Info",
     "objective": "Get OS info with `uname -a`.",
     "hint": "uname -a shows kernel and OS details. Know your battlefield.",
     "match": r"^uname", "xp": 10},

    {"id": 40, "section": "Skills", "title": "Disk Usage",
     "objective": "Check disk usage with `df -h`.",
     "hint": "df -h shows filesystem usage. -h = human readable (GB not bytes).",
     "match": r"^df\s", "xp": 10},

    {"id": 41, "section": "Skills", "title": "History",
     "objective": "View command history with `history`.",
     "hint": "history shows past commands. Your past betrays your methods.",
     "match": r"^history$", "xp": 10},

    {"id": 42, "section": "Skills", "title": "Help",
     "objective": "View all commands with `help`.",
     "hint": "help lists every available command. You've come far, Ghost.",
     "match": r"^help$", "xp": 10},
]

# Build lookup by id for review mode
STEPS_BY_ID: Dict[int, Dict] = {s["id"]: s for s in STEPS}


class TutorialEngine:
    def __init__(self, gs):
        self.gs = gs

    @property
    def step(self) -> Optional[Dict]:
        idx = self.gs.tutorial_step
        return STEPS[idx] if idx < len(STEPS) else None

    @property
    def progress(self) -> int:
        return self.gs.tutorial_step

    @property
    def percent(self) -> int:
        return min(100, round(self.gs.tutorial_step / len(STEPS) * 100))

    def get_all(self) -> List[Dict]:
        return STEPS

    def get_by_id(self, step_id: int) -> Optional[Dict]:
        return STEPS_BY_ID.get(step_id)

    def _get_tried(self, step_id: int) -> Set[int]:
        """Return set of variant indices tried for this step."""
        tried_map = getattr(self.gs, "tutorial_tried_variants", {})
        return set(tried_map.get(str(step_id), []))

    def _record_tried(self, step_id: int, variant_idx: int) -> Set[int]:
        """Record a variant as tried and return full set."""
        if not hasattr(self.gs, "tutorial_tried_variants"):
            self.gs.tutorial_tried_variants = {}
        key = str(step_id)
        existing = set(self.gs.tutorial_tried_variants.get(key, []))
        existing.add(variant_idx)
        self.gs.tutorial_tried_variants[key] = list(existing)
        return existing

    def check(self, cmd: str) -> Optional[Dict]:
        """
        Check cmd against current step.
        Returns None if no match.
        Returns dict with keys:
          - "completed": step dict — always present on match
          - "variant": matched variant dict (multi-variant steps)
          - "variant_idx": int index of matched variant
          - "all_done": bool — True if step is now complete
          - "remaining": list of unmatched variants (when not all_done)
          - "advance": bool — True when tutorial_step incremented
        """
        step = self.step
        if step is None:
            return None

        variants = step.get("variants")

        if variants:
            # Multi-variant step — check each unmatched variant
            tried = self._get_tried(step["id"])
            for i, v in enumerate(variants):
                if i in tried:
                    continue
                try:
                    if re.search(v["match"], cmd.strip(), re.IGNORECASE):
                        tried = self._record_tried(step["id"], i)
                        all_done = len(tried) >= len(variants)
                        if all_done:
                            # Award XP and advance
                            self.gs.advance_tutorial()
                            self.gs.add_xp(step.get("xp", 15), "terminal")
                        else:
                            # Partial XP reward for each variant tried
                            partial_xp = max(3, step.get("xp", 15) // len(variants))
                            self.gs.add_xp(partial_xp, "terminal")
                        remaining = [variants[j] for j in range(len(variants)) if j not in tried]
                        return {
                            "completed": step,
                            "variant": v,
                            "variant_idx": i,
                            "variant_total": len(variants),
                            "variants_done": len(tried),
                            "all_done": all_done,
                            "remaining": remaining,
                            "advance": all_done,
                        }
                except re.error:
                    continue
            return None
        else:
            # Standard single-match step
            try:
                if re.search(step["match"], cmd.strip(), re.IGNORECASE):
                    self.gs.advance_tutorial()
                    self.gs.add_xp(step.get("xp", 10), "terminal")
                    return {
                        "completed": step,
                        "all_done": True,
                        "advance": True,
                    }
            except re.error:
                pass
            return None

    def to_dict(self) -> dict:
        return {}

    @classmethod
    def from_dict(cls, d: dict, gs) -> "TutorialEngine":
        return cls(gs)
