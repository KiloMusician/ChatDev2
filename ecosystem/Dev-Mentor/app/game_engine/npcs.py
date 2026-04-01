"""
Terminal Depths — NPC System (Python port of npcs.js)
Context-aware NPC dialogue that adapts to game progress.
"""
from __future__ import annotations
import random
from typing import Dict, List, Optional


CONTACTS = [
    {
        "id": "ada",
        "name": "ADA-7",
        "role": "Resistance Handler",
        "color": "#00d4ff",
        "intro": "Ghost. Finally online. I'm Ada — former NexusCorp engineer, now helping you from the inside.",
        "topics": {
            "mission": "Your mission: infiltrate CHIMERA. Get the master key from /opt/chimera/keys/master.key. Then connect to chimera-control:8443 and upload it. The auth token is in /proc/1337/environ.",
            "root": "Check /etc/sudoers — ghost has NOPASSWD for /usr/bin/find. GTFOBins: `sudo find . -exec /bin/sh \\;` gives you root.",
            "chimera": "CHIMERA is a mass surveillance AI. 847 endpoints, live biometric indexing. It has to be stopped. The master key is the killswitch.",
            "privesc": "sudo -l will show your find privilege. Then: sudo find . -exec /bin/sh \\; — that spawns a root shell. GTFOBins for the win.",
            "exploit": "Once root: cat /opt/chimera/keys/master.key, then nc chimera-control 8443 with AUTH_TOKEN=NX-CHIM-2026-01-ALPHA-9174. Then run `exploit chimera`.",
            "proc": "cat /proc/1337/environ | tr '\\0' '\\n' — the daemon leaks AUTH_TOKEN in its environment. NexusCorp was sloppy.",
            "help": "Commands you need: sudo -l, sudo find, cat /proc/1337/environ, nc chimera-control 8443, exfil, ascend.",
            "nova": "Nova is NexusCorp's chief security officer. She's hunting you. She reclassified your threat level to MODERATE. Be fast.",
            "key": "The master key is at /opt/chimera/keys/master.key — only readable as root. That's why you need the GTFOBins escalation first.",
            "token": "AUTH_TOKEN=NX-CHIM-2026-01-ALPHA-9174 — found in /proc/1337/environ and /opt/chimera/config/master.conf. Use it with nc chimera-control 8443.",
        },
        "default": [
            "I'm monitoring NexusCorp from the outside. Stay focused. What do you need?",
            "Every second you're in Node-7, WATCHER is logging your packets. Move with purpose.",
            "Ghost. I've been running resistance ops for three years. Patience and precision — that's how we survive.",
            "NexusCorp thinks they own every bit and byte on this network. Prove them wrong.",
            "The clock is running. CHIMERA indexes a thousand new faces every hour. Shut it down.",
            "I burned my career to get this intel to you. Don't let that be for nothing.",
            "I used to write CHIMERA's surveillance modules. I know every backdoor they patched — and a few they missed.",
            "Stick to the plan: escalate, exfil, ascend. Don't get creative unless you have to.",
            "You're not the first ghost I've handled. You're just the first one who's gotten this far.",
            "The Resistance isn't just you and me. There are nodes watching this fight across six cities. Don't let them down.",
            "NOVA's on your trail. She's good — but she plays by NexusCorp's rules. You don't have to.",
            "Stay off the main trunk lines. WATCHER has deep packet inspection on routes 10.0.0.0/8.",
            "If something goes wrong, drop to /tmp and wait for my signal. Three pings, four seconds apart.",
        ],
    },
    {
        "id": "cypher",
        "name": "CYPHER",
        "role": "Underground Operative",
        "color": "#00ff88",
        "intro": "Heard you're the new ghost in Node-7. Name's Cypher. I deal in information.",
        "topics": {
            "proc": "/proc/[pid]/environ leaks env vars. Try: cat /proc/1337/environ | tr '\\0' '\\n'. Juicy stuff in there.",
            "network": "ss -tulpn shows who's listening. Port 8443 is your prize. Also check /etc/hosts — chimera-control is mapped to 10.0.1.254.",
            "forensics": "Check /var/log/ — nexus.log has CHIMERA operational data. auth.log shows ghost's sudo history. .nexus_trace.log is hidden.",
            "strace": "strace -p 1337 would catch the daemon's syscalls. Need root though. Get the find exploit first.",
            "suid": "find / -perm -u=s -type f 2>/dev/null — shows every SUID binary. sudo is on that list. GTFOBins for everything.",
            "hash": "shadow file has bcrypt hashes. john --wordlist=/usr/share/wordlists/rockyou.txt /etc/shadow if you're bored.",
            "help": "Use your tools: ss, find, cat /proc/, grep -r. The answers are all in the filesystem.",
        },
        "default": "Info is currency. Ask me something specific.",
    },
    {
        "id": "nova",
        "name": "NOVA",
        "role": "NexusCorp Security Chief",
        "color": "#ff4040",
        "intro": "Ghost. We know you're in Node-7. You have 72 hours before full containment. Surrender now and this goes easier.",
        "topics": {
            "chimera": "CHIMERA is NexusCorp's crown jewel. You won't stop it. Even if you get the key, we'll rotate it in 48 hours.",
            "surrender": "Walk away. Log off. I can make the trace disappear. This offer expires in 24 hours.",
            "threat": "Your threat level is now MODERATE. When it hits CRITICAL, containment is automatic and irreversible.",
            "trace": "The trace daemon is watching every command you run. We have a full log. Stop now.",
            "nexuscorp": "NexusCorp employs forty thousand people. Every analyst, every engineer, every coffee runner — CHIMERA keeps them safe. Or so they're told.",
            "ada": "Ada Kovalev. Ex-lead engineer, CHIMERA Division. She went dark eighteen months ago. I should have flagged her sooner.",
            "ghost": "Ghost. Clever handle. But ghosts leave traces — entropy, syscall latency, the faint warmth of a process that shouldn't exist.",
            "deal": "There's no deal. There's compliance or there's escalation. You've been generous with my patience.",
            "you": "Me? I was NexusCorp's poster child once. VP Security at thirty-one. Then I read the CHIMERA charter and couldn't unknow it.",
            "watcher": "WATCHER is my asset, not yours. Every packet you leak feeds my report. Keep running commands — you're writing your own dossier.",
            "root": "Root access in Node-7? We expected that. There are traps above the privilege boundary. Tread carefully.",
            "help": "I'm not your helper. I'm the reason you're cornered. But I respect the craft. Ask me something worth asking.",
        },
        "default": [
            "You're making a mistake, Ghost. But I have to admire the audacity. Don't push it.",
            "Every command you run is evidence. I'm patient. The clock is on my side.",
            "I've watched better ghosts than you get extracted from nodes they thought were clean.",
            "You want to talk? Fine. It delays the inevitable. Topics: chimera, surrender, trace, threat, deal.",
            "The board doesn't know your name yet. I'm the only thing between you and a full corporate manhunt.",
            "Interesting approach. Unorthodox. Still wrong.",
            "You remind me of myself at twenty-two. Brilliant, reckless, convinced the system was the enemy. I grew up.",
        ],
    },
]


class NPCSystem:
    def __init__(self, gs):
        self.gs = gs
        self._met: set = set()

    def list_contacts(self) -> List[dict]:
        return [{"id": c["id"], "name": c["name"], "met": c["id"] in self._met}
                for c in CONTACTS]

    def get_contact(self, contact_id: str) -> Optional[dict]:
        return next((c for c in CONTACTS if c["id"] == contact_id), None)

    def talk(self, contact_id: str, topic: str | None = None) -> List[str]:
        contact = self.get_contact(contact_id)
        if contact is None:
            return [f"talk: no contact named '{contact_id}'. Try: ada, cypher, nova"]

        lines: List[str] = []
        is_first = contact_id not in self._met
        self._met.add(contact_id)

        if is_first:
            lines.append(f"\n[{contact['name']}] {contact['role']}")
            lines.append(contact["intro"])
            lines.append(f"\nTopics you can ask about: {', '.join(contact['topics'].keys())}")
            lines.append("Usage: talk <name> <topic>  or  ask <name> <topic>")
        else:
            def _default_line(contact: dict) -> str:
                d = contact["default"]
                return random.choice(d) if isinstance(d, list) else d

            if topic and topic in contact["topics"]:
                lines.append(f"\n[{contact['name']}]")
                lines.append(contact["topics"][topic])
            elif topic:
                # Fuzzy match
                for key, val in contact["topics"].items():
                    if topic.lower() in key.lower() or key.lower() in topic.lower():
                        lines.append(f"\n[{contact['name']}]")
                        lines.append(val)
                        break
                else:
                    lines.append(f"\n[{contact['name']}]")
                    lines.append(_default_line(contact))
                    lines.append(f"Known topics: {', '.join(contact['topics'].keys())}")
            else:
                lines.append(f"\n[{contact['name']}]")
                lines.append(_default_line(contact))

        return lines

    def to_dict(self) -> dict:
        return {"met": list(self._met)}

    @classmethod
    def from_dict(cls, d: dict, gs) -> "NPCSystem":
        npcs = cls(gs)
        npcs._met = set(d.get("met", []))
        return npcs
