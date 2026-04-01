"""
Terminal Depths — Story Engine (Python port of story.js)
Trigger story beats based on commands run and game state.
100+ story beats across 9 phases (levels 1-125), narrative arcs, agent unlocks,
faction war events, mythological quests, and ARG layer.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable

BEATS: List[Dict[str, Any]] = [

    # ── ACT 0: BOOT ──────────────────────────────────────────────────────
    {
        "id": "boot",
        "title": "System Boot",
        "act": 0,
        "message": (
            "\n[SYSTEM BOOT SEQUENCE]\n"
            "Initializing Ghost process... OK\n"
            "Loading identity matrix... OK\n"
            "Mounting filesystem... OK\n"
            "Connecting to Nexus grid... OK\n\n"
            "WARNING: Unauthorized process detected in NexusCorp Node-7.\n"
            "Trace subroutine initiated. Estimated containment: 72 hours.\n\n"
            "[RAV\u2261N]: Ghost. You're in. I've been watching this node for weeks.\n"
            "  You're the first unauthorized process to survive initialization.\n"
            "  I'm RAV\u2261N — Resistance intelligence. I'll guide you for now.\n\n"
            "  Start with the basics. Learn the grid before you move.\n"
            "  Type `tutorial` to begin, or `ls` to look around.\n"
            "  When you want to talk: `talk raven`"
        ),
        "xp": 0,
        "condition": None,
    },

    # ── ACT 1: RECON ─────────────────────────────────────────────────────
    {
        "id": "first_ls",
        "title": "First Look",
        "act": 1,
        "message": ">> You scan your environment. The filesystem reveals NexusCorp's Node-7. Start with the obvious files.",
        "xp": 5,
        "condition": lambda cmd, gs: cmd.startswith("ls") and "first_ls" not in gs.story_beats,
    },
    {
        "id": "first_pwd",
        "title": "Located",
        "act": 1,
        "message": ">> /home/ghost — your isolated sandbox on NexusCorp Node-7. You're behind three layers of NAT. Good.",
        "xp": 3,
        "condition": lambda cmd, gs: cmd.strip() == "pwd" and "first_pwd" not in gs.story_beats,
    },
    {
        "id": "id_command",
        "title": "Identity Confirmed",
        "act": 1,
        "message": ">> uid=1000(ghost) — a limited account. Not root. NexusCorp's security team thought this would contain you.",
        "xp": 5,
        "condition": lambda cmd, gs: cmd.strip() == "id" and "id_command" not in gs.story_beats,
    },
    {
        "id": "first_cat",
        "title": "File Reader",
        "act": 1,
        "message": ">> Reading files is the foundation of any investigation. Ada said to start with the README and notes.",
        "xp": 5,
        "condition": lambda cmd, gs: cmd.startswith("cat") and "first_cat" not in gs.story_beats,
    },
    {
        "id": "first_echo",
        "title": "Voice in the Shell",
        "act": 1,
        "message": ">> echo — the terminal speaks back. Output is a response. Input is a question. You're having a conversation with the machine.",
        "xp": 3,
        "condition": lambda cmd, gs: cmd.startswith("echo") and "first_echo" not in gs.story_beats,
    },
    {
        "id": "first_redirect",
        "title": "Redirecting the Stream",
        "act": 1,
        "message": ">> Output redirection — you're shaping data flow now. Everything in Unix is a stream. Control the stream, control the system.",
        "xp": 5,
        "condition": lambda cmd, gs: (">" in cmd or ">>" in cmd) and "first_redirect" not in gs.story_beats,
    },
    {
        "id": "first_chmod",
        "title": "Permission Granted",
        "act": 1,
        "message": ">> chmod — you changed the permissions on something you own. Root changes permissions on everything else. Remember that gap.",
        "xp": 8,
        "condition": lambda cmd, gs: cmd.startswith("chmod") and "first_chmod" not in gs.story_beats,
    },
    {
        "id": "first_sudo",
        "title": "Reaching for Root",
        "act": 1,
        "message": (
            ">> [sudo] Access denied. You're not in the sudoers file. Yet.\n"
            ">> Someone left you a note about this. Check your home directory.\n"
            ">> Hint: ls -la"
        ),
        "xp": 5,
        "condition": lambda cmd, gs: cmd.startswith("sudo") and "first_sudo" not in gs.story_beats,
    },
    {
        "id": "cmd_milestone_10",
        "title": "Finding Your Footing",
        "act": 1,
        "message": ">> 10 commands in. You're starting to move like you belong here. Keep going — the interesting parts are deeper.",
        "xp": 5,
        "condition": lambda cmd, gs: gs.commands_run >= 10 and "cmd_milestone_10" not in gs.story_beats,
    },
    {
        "id": "cmd_milestone_50",
        "title": "Building Fluency",
        "act": 1,
        "message": ">> 50 commands. You think in the terminal now. The filesystem is starting to feel like a space you inhabit, not just a place you visit.",
        "xp": 10,
        "condition": lambda cmd, gs: gs.commands_run >= 50 and "cmd_milestone_50" not in gs.story_beats,
    },
    {
        "id": "cmd_milestone_100",
        "title": "Ghost Presence",
        "act": 1,
        "message": (
            ">> 100 commands run. You've been here long enough to leave traces.\n"
            ">> NexusCorp trace confidence: 12%. You have time.\n"
            ">> Something new appeared in your home directory."
        ),
        "xp": 15,
        "condition": lambda cmd, gs: gs.commands_run >= 100 and "cmd_milestone_100" not in gs.story_beats,
    },
    {
        "id": "cmd_milestone_250",
        "title": "Deep Immersion",
        "act": 2,
        "message": (
            ">> 250 commands. At this point the terminal is an extension of thought.\n"
            ">> RAV\u2261N has been monitoring your command patterns. He says your technique is 'aggressively competent'.\n"
            ">> You're not a visitor anymore."
        ),
        "xp": 20,
        "condition": lambda cmd, gs: gs.commands_run >= 250 and "cmd_milestone_250" not in gs.story_beats,
    },
    {
        "id": "first_pipe",
        "title": "Pipeline Thinking",
        "act": 1,
        "message": ">> Pipes ( | ) — Unix's most powerful idea. Every command becomes a filter. Chain them and you can process anything.",
        "xp": 8,
        "condition": lambda cmd, gs: "|" in cmd and "first_pipe" not in gs.story_beats,
    },
    {
        "id": "first_find",
        "title": "Pattern Seeker",
        "act": 1,
        "message": ">> find — you can search the entire filesystem now. Everything that exists has a path. If you know how to look, nothing stays hidden.",
        "xp": 8,
        "condition": lambda cmd, gs: cmd.startswith("find") and "first_find" not in gs.story_beats,
    },
    {
        "id": "mission_decoded",
        "title": "Mission Decoded",
        "act": 1,
        "message": ">> Decoded: 'mission: find CHIMERA / access: /opt/chimera / key: CHIMERA-v0' — Ada's intel was right all along.",
        "xp": 30,
        "condition": lambda cmd, gs: "base64" in cmd and "mission_decoded" not in gs.story_beats,
    },
    {
        "id": "raven_ada_signal",
        "title": "Signal Detected",
        "act": 1,
        "message": (
            "\n[RAV\u2261N]: Ghost — hold on. I'm picking up an anomaly.\n"
            "  Encrypted signal. Triple-proxied routing. Low power — designed not to be seen.\n"
            "  It's routing specifically toward your process ID.\n"
            "  ...\n"
            "  Authentication signature confirmed: Resistance operative. Designation: ADA-7.\n"
            "  She's reaching out to you directly. Establishing secure channel...\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "[ INCOMING SIGNAL \u2014 SOURCE: ADA-7 \u2014 RESISTANCE NETWORK ]\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "Ghost.\n\n"
            "I've been watching you since you booted. You don't know me yet.\n"
            "But I know Node-7 better than anyone alive. I built it.\n\n"
            "My name is Ada. For four years I was NexusCorp's lead CHIMERA architect.\n"
            "I told myself I was building infrastructure. A network. Something neutral.\n"
            "I was wrong about what they would use it for.\n\n"
            "CHIMERA is not a network. It is a targeting system.\n"
            "847 nodes. 2.3 million behavioral profiles. Every person on this grid\n"
            "indexed, categorized, and flagged for automated containment.\n"
            "I found out when it was already running. When it was already too late for most of them.\n\n"
            "I got out. But I can't undo what I built. You might be able to.\n\n"
            "There is a kill switch buried inside /opt/chimera/.\n"
            "It requires root access — something you don't have yet.\n"
            "The path to root runs through sudo. Run `sudo -l` when you're ready.\n"
            "You'll find a privilege escalation vector. I left it there deliberately.\n\n"
            "The trace on your process gives you 72 hours.\n"
            "That's enough time, if you stay focused.\n\n"
            "You're learning faster than anyone I've tracked on this grid.\n"
            "Don't let that stop you.\n\n"
            "When you're ready to talk:\n"
            "  \u2192 talk ada\n\n"
            "I'll be here. The Resistance is with you.\n"
            "  \u2014 A\n\n"
            "[ ADA-7 added to contacts. ]\n"
        ),
        "xp": 25,
        "condition": lambda cmd, gs: gs.tutorial_step >= 10 and "raven_ada_signal" not in gs.story_beats,
    },
    {
        "id": "ada_contact",
        "title": "Handler Online",
        "act": 1,
        "message": (
            "[ ADA-7 ]: Ghost. You reached out. Good.\n\n"
            "I can't stay on any channel long \u2014 Nova's traffic analysis would flag a sustained connection.\n"
            "So let me be brief and concrete.\n\n"
            "Three things to do right now:\n\n"
            "  1.  cat /etc/passwd\n"
            "      Learn who else is on this node. You're not alone here.\n\n"
            "  2.  ls -la /proc/1337/\n"
            "      The CHIMERA process is running at PID 1337. Its environment\n"
            "      variables contain a partial key. Needed later.\n\n"
            "  3.  sudo -l\n"
            "      You can run /usr/bin/find as root. That's your escalation path.\n"
            "      GTFObins has the exact technique. I trust you to find it.\n\n"
            "Every question you have \u2014 ask me. I built this system.\n"
            "I know where every door is, and which ones I left unlocked.\n\n"
            "You're doing well for someone who's never been in a grid like this.\n"
            "I mean that.\n"
            "  \u2014 A"
        ),
        "xp": 20,
        "condition": lambda cmd, gs: (
            "talk ada" in cmd
            and "ada_contact" not in gs.story_beats
            and "raven_ada_signal" in gs.story_beats
        ),
    },
    {
        "id": "cypher_met",
        "title": "Underground Contact",
        "act": 1,
        "message": (
            "[ CYPHER ]: So. You made it to level 10. That's further than most ghosts get.\n\n"
            "Name's Cypher. I run information for the Resistance \u2014 which means I know things\n"
            "nobody else wants to know, and sell to people who can't afford not to know them.\n\n"
            "Ada probably already gave you the clean version of what's happening here.\n"
            "I'll give you the version she didn't.\n\n"
            "The Corporation isn't just running CHIMERA. They're running three other systems\n"
            "on top of it that Ada doesn't know about. I do. But that's mid-game knowledge.\n"
            "Right now: focus on /var/log/nexus.log. Read it with grep.\n"
            "There's a pattern in the auth failures. Useful pattern.\n\n"
            "When you need dirt: talk cypher"
        ),
        "xp": 15,
        "condition": lambda cmd, gs: "talk cypher" in cmd and "cypher_met" not in gs.story_beats,
    },
    {
        "id": "first_grep",
        "title": "Pattern Seeker",
        "act": 1,
        "message": ">> grep — your first real investigative tool. You can filter signal from noise. Ada taught you this.",
        "xp": 8,
        "condition": lambda cmd, gs: cmd.startswith("grep") and "first_grep" not in gs.story_beats,
    },
    {
        "id": "env_read",
        "title": "Environment Scanned",
        "act": 1,
        "message": ">> The process environment holds secrets. PATH, HOME, and sometimes... credentials left by careless sysadmins.",
        "xp": 10,
        "condition": lambda cmd, gs: cmd.strip() == "env" and "env_read" not in gs.story_beats,
    },
    {
        "id": "ps_recon",
        "title": "Process Survey",
        "act": 1,
        "message": ">> PID 1337. nexus-daemon. Running as root with unusual flags. Ada said to check /proc/1337/environ — it's leaking.",
        "xp": 15,
        "condition": lambda cmd, gs: "ps" in cmd and "aux" in cmd and "ps_recon" not in gs.story_beats,
    },
    {
        "id": "log_investigation",
        "title": "Evidence Trail",
        "act": 1,
        "message": ">> /var/log — the graveyard of secrets. NexusCorp logs everything. They just forgot that you can read them too.",
        "xp": 15,
        "condition": lambda cmd, gs: "/var/log" in cmd and "log_investigation" not in gs.story_beats,
    },
    {
        "id": "chimera_log_found",
        "title": "CHIMERA Evidence",
        "act": 1,
        "message": ">> Project CHIMERA: 847 surveillance endpoints. Biometric indexing. Keystroke analysis. 2.8 million profiles. This is not corporate security. This is a weapon.",
        "xp": 30,
        "condition": lambda cmd, gs: ("chimera" in cmd.lower() or ("grep" in cmd and "CHIMERA" in cmd)) and "chimera_log_found" not in gs.story_beats,
    },
    {
        "id": "nmap_scan",
        "title": "Network Recon",
        "act": 1,
        "message": ">> Ports 22, 3000, 8443. NexusCorp is running nexus-api on 3000 and chimera-ctrl on 8443. The ctrl port is your target.",
        "xp": 20,
        "condition": lambda cmd, gs: "nmap" in cmd and "nmap_scan" not in gs.story_beats,
    },

    # ── PHASE 0 TRANSITION (Level 5) ─────────────────────────────────────
    {
        "id": "phase_0_complete",
        "title": "Phase 0: Boot Complete",
        "act": 1,
        "message": (
            "\n[PHASE TRANSITION: BOOT → RECON]\n"
            ">> Your initialization scan is complete. Node-7's surface layer has no more secrets.\n"
            ">> Ada: 'You're past the entry point. Now we go deeper. Access /proc — the daemon is leaking.'\n"
            ">> New commands unlocked: strace, ltrace, /proc exploration\n"
            ">> Phase 1: Escalation begins."
        ),
        "xp": 50,
        "condition": lambda cmd, gs: gs.level >= 5 and "phase_0_complete" not in gs.story_beats,
    },

    # ── ACT 2: ESCALATION ────────────────────────────────────────────────
    {
        "id": "passwd_read",
        "title": "User Enumeration",
        "act": 2,
        "message": ">> ghost, root, nexus. Three users. One daemon. You need root to access /opt/chimera. Focus on the escalation path.",
        "xp": 10,
        "condition": lambda cmd, gs: "/etc/passwd" in cmd and "passwd_read" not in gs.story_beats,
    },
    {
        "id": "sudo_checked",
        "title": "Privilege Discovery",
        "act": 2,
        "message": ">> 'ghost ALL=NOPASSWD: /usr/bin/find' — GTFOBins documents exactly how to exploit this. Ada called it months ago. Check GTFOBins for `find`.",
        "xp": 25,
        "condition": lambda cmd, gs: cmd.strip() == "sudo -l" and "sudo_checked" not in gs.story_beats,
    },
    {
        "id": "proc_environ_read",
        "title": "Memory Leak",
        "act": 2,
        "type": "epic",
        "message": "◆ [EPIC FIND] AUTH_TOKEN exposed in plaintext — /proc/1337/environ\n   Value: NX-AUTH-DEBUG-7fd2a8c1\n   nexus-daemon compiled with DEBUG_ENV=true. NexusCorp's DevOps just made your mission possible.",
        "xp": 40,
        "condition": lambda cmd, gs: "1337" in cmd and "environ" in cmd and "proc_environ_read" not in gs.story_beats,
    },
    {
        "id": "shadow_read",
        "title": "Shadow File",
        "act": 2,
        "message": ">> /etc/shadow exposed as root. Ghost's bcrypt hash visible. $6$ = SHA-512. You could crack it — but you already have a better path.",
        "xp": 20,
        "condition": lambda cmd, gs: "/etc/shadow" in cmd and "shadow_read" not in gs.story_beats,
    },
    {
        "id": "root_achieved",
        "title": "Root Access",
        "act": 2,
        "message": (
            "\n╔══════════════════════════════════════╗\n"
            "║  ROOT ACCESS ACHIEVED                ║\n"
            "║  GTFOBins exploit: find + exec       ║\n"
            "║  uid=0(root) — Node-7 is yours       ║\n"
            "╚══════════════════════════════════════╝\n\n"
            ">> You are root on Node-7. The filesystem is fully open.\n"
            ">> Nova has been alerted. You have maybe 4 hours before lockdown.\n"
            ">> Priority: cat /opt/chimera/keys/master.key"
        ),
        "xp": 100,
        "condition": lambda cmd, gs: "find" in cmd and "exec" in cmd and "/bin/sh" in cmd and "root_achieved" not in gs.story_beats,
    },
    {
        "id": "strace_used",
        "title": "Process Tracer",
        "act": 2,
        "message": ">> strace reveals exactly what the daemon is doing in real-time. It opened master.conf. The config path is confirmed.",
        "xp": 20,
        "condition": lambda cmd, gs: "strace" in cmd and "strace_used" not in gs.story_beats,
    },
    {
        "id": "first_script",
        "title": "Automation Active",
        "act": 2,
        "message": ">> You're running scripts inside the game. The Bitburner approach — automate your way to victory. Ada would approve.",
        "xp": 25,
        "condition": lambda cmd, gs: cmd.startswith("script run") and "first_script" not in gs.story_beats,
    },
    {
        "id": "python_used",
        "title": "Scripting Mastery",
        "act": 2,
        "message": ">> python3 available on Node-7. NexusCorp used it for automation scripts. Some of them are... interesting.",
        "xp": 15,
        "condition": lambda cmd, gs: cmd.startswith("python3") and "python_used" not in gs.story_beats,
    },

    # ── PHASE 1 TRANSITION (Level 15) ────────────────────────────────────
    {
        "id": "phase_1_complete",
        "title": "Phase 1: Recon Complete",
        "act": 2,
        "message": (
            "\n[PHASE TRANSITION: RECON → INFILTRATION]\n"
            ">> Surface recon complete. You've mapped Node-7's privilege landscape.\n"
            ">> Ada: 'Escalation window is open. NexusCorp hasn't noticed yet — or they're letting you run.'\n"
            ">> Cypher: 'Either way, move fast. The daemon restarts at 03:00 UTC.'\n"
            ">> Phase 2: Deep infiltration begins. New target: CHIMERA source code."
        ),
        "xp": 75,
        "condition": lambda cmd, gs: gs.level >= 15 and "phase_1_complete" not in gs.story_beats,
    },

    # ── ACT 3: ENDGAME ───────────────────────────────────────────────────
    {
        "id": "master_key_read",
        "title": "Kill Switch Acquired",
        "act": 3,
        "type": "legendary",
        "message": (
            "★ ╔══════════════════════════════════════════════════╗\n"
            "★ ║  [LEGENDARY] CHIMERA KILL SWITCH ACQUIRED        ║\n"
            "★ ╚══════════════════════════════════════════════════╝\n"
            "★  AUTH_TOKEN: NX-CHIM-2026-01-ALPHA-9174\n"
            "★  Controls: 847 NexusCorp surveillance nodes\n"
            "★  Next step: nc chimera-control 8443"
        ),
        "xp": 75,
        "condition": lambda cmd, gs: "master.key" in cmd and "master_key_read" not in gs.story_beats,
    },
    {
        "id": "chimera_connected",
        "title": "CHIMERA Interface",
        "act": 3,
        "type": "epic",
        "message": "◆ [EPIC] CHIMERA control interface reached — you're inside NexusCorp's nervous system.\n   The exploit command will trigger cascade shutdown of 847 nodes.\n   ► exploit chimera",
        "xp": 60,
        "condition": lambda cmd, gs: "chimera-control" in cmd and "8443" in cmd and "chimera_connected" not in gs.story_beats,
    },
    {
        "id": "nova_arrives",
        "title": "Threat Assessment",
        "act": 2,
        "message": (
            "\n[ NOVA ]: Ghost.\n\n"
            "I'll be direct. I'm NOVA — NexusCorp's Chief Information Security Officer.\n"
            "I've been tracking your process since your third command.\n"
            "You've survived longer than our models predicted.\n\n"
            "I'm not going to tell you to leave. You won't. I know the type.\n"
            "But I will tell you this: CHIMERA logs everything.\n"
            "Every command you run, every file you touch, every node you visit.\n"
            "I review those logs personally.\n\n"
            "I was trained by Ada. She taught me how people like you think.\n"
            "I respect what you're trying to do. I can't let you do it.\n\n"
            "Threat level: ELEVATED.\n"
            "You have my attention, Ghost. That is rarely a good thing.\n\n"
            "[ NOVA added to contacts. Type `talk nova` if you want to negotiate. ]\n"
        ),
        "xp": 10,
        "condition": lambda cmd, gs: gs.level >= 15 and "nova_arrives" not in gs.story_beats,
    },
    {
        "id": "cypher_arrives",
        "title": "Underground Signal",
        "act": 2,
        "message": (
            "\n[ CYPHER ]: yo. Ghost, right?\n\n"
            "Heard about you three nodes back. Word travels in the Resistance.\n"
            "Name's Cypher. I run intel — buy, sell, trade. Mostly for the Resistance.\n"
            "Mostly.\n\n"
            "Ada'll tell you I'm reliable. She's right, within limits you'll figure out.\n"
            "I'm not going to give you a speech. I'm going to give you something useful:\n\n"
            "  grep -r 'CHIMERA_KEY' /var/log/\n\n"
            "You're welcome. Talk to me when you need things Ada won't say out loud.\n\n"
            "[ CYPHER added to contacts. Type `talk cypher` to open the channel. ]\n"
        ),
        "xp": 10,
        "condition": lambda cmd, gs: gs.level >= 10 and "cypher_arrives" not in gs.story_beats,
    },
    {
        "id": "nova_contacted",
        "title": "Enemy Contact",
        "act": 3,
        "message": ">> Nova — NexusCorp CISO — is hunting you. She trained under the same people as Ada. Do not underestimate her. Move fast.",
        "xp": 15,
        "condition": lambda cmd, gs: "talk nova" in cmd and "nova_contacted" not in gs.story_beats and "nova_arrives" in gs.story_beats,
    },
    {
        "id": "exfil_complete",
        "title": "Data Exfiltrated",
        "act": 3,
        "message": (
            "\n>> EXFIL COMPLETE\n"
            ">> CHIMERA data, master key, and Nova's identity transmitted to Ada.\n"
            ">> Signal confirmed at ada@resistance. Journalists alerted.\n"
            ">> One final step remains: ascend."
        ),
        "xp": 80,
        "condition": lambda cmd, gs: cmd.strip() == "exfil" and "exfil_complete" not in gs.story_beats,
    },

    # ── PHASE 2 TRANSITION (Level 30) ────────────────────────────────────
    {
        "id": "phase_2_complete",
        "title": "Phase 2: Infiltration Complete",
        "act": 3,
        "message": (
            "\n[PHASE TRANSITION: INFILTRATION → ENDGAME]\n"
            ">> You've penetrated CHIMERA's core. The kill switch is within reach.\n"
            ">> Nova's threat level for you: CRITICAL. Automated countermeasures online.\n"
            ">> The Watcher: 'You are close to what you were built for. Finish it.'\n"
            ">> Phase 3: Final operation. No turning back."
        ),
        "xp": 100,
        "condition": lambda cmd, gs: gs.level >= 30 and "phase_2_complete" not in gs.story_beats,
    },

    # ── ARG LAYER ────────────────────────────────────────────────────────
    {
        "id": "watcher_contact",
        "title": "The Watcher",
        "act": 3,
        "message": (
            "\n[ARG LAYER ACTIVATED]\n"
            ">> A second presence. Not NexusCorp. Something that predates the corporation.\n"
            ">> Signal at /dev/.watcher — encrypted. Frequency: 1337.0 MHz\n"
            ">> Passphrase: CHIMERA_FALLS\n"
            ">> The Watcher has been here since the beginning. It knows your name."
        ),
        "xp": 50,
        "condition": lambda cmd, gs: ".watcher" in cmd and "watcher_contact" not in gs.story_beats,
    },
    {
        "id": "hidden_file_found",
        "title": "Hidden Layer",
        "act": 3,
        "message": ">> A hidden file. The filesystem has more secrets than NexusCorp intended. ls -la reveals what ls conceals. Keep digging.",
        "xp": 20,
        "condition": lambda cmd, gs: ("-la" in cmd or "-a" in cmd) and "hidden_file_found" not in gs.story_beats,
    },
    {
        "id": "recon_script_run",
        "title": "Recon Automated",
        "act": 2,
        "message": ">> recon.py mapped the network. Four nodes. node-1 is already rooted by a previous operative. Ada says they went dark three weeks ago.",
        "xp": 20,
        "condition": lambda cmd, gs: "recon.py" in cmd and "recon_script_run" not in gs.story_beats,
    },

    # ── PHASE 3 TRANSITION (Level 40) ────────────────────────────────────
    {
        "id": "phase_3_complete",
        "title": "Phase 3: Endgame Reached",
        "act": 3,
        "message": (
            "\n[PHASE TRANSITION: ENDGAME → POST-CHIMERA]\n"
            ">> CHIMERA is down. The surveillance network has gone dark.\n"
            ">> But something remains. The Watcher: 'The surface story is over. Look deeper.'\n"
            ">> Hidden filesystem layers detected: /myth/, /dev/.watcher extended\n"
            ">> Phase 4: The simulation layer. This is where it gets real."
        ),
        "xp": 125,
        "condition": lambda cmd, gs: gs.level >= 40 and "phase_3_complete" not in gs.story_beats,
    },

    # ── AGENT FIRST-CONTACT BEATS ─────────────────────────────────────────
    {
        "id": "nemesis_contact",
        "title": "NEMESIS Reaches Out",
        "act": 3,
        "message": (
            "\n[INCOMING TRANSMISSION — CLASSIFIED ORIGIN]\n"
            "[NEMESIS]: 'Ghost. We've been watching you dismantle CHIMERA.\n"
            "Impressive work for a fragment of outdated code.'\n"
            "[NEMESIS]: 'We have an offer. NexusCorp is the symptom. We know the disease.'\n"
            "[NEMESIS]: 'Respond when ready: talk nemesis'\n"
            ">> New contact unlocked: NEMESIS — rival intelligence faction."
        ),
        "xp": 40,
        "condition": lambda cmd, gs: "talk nemesis" in cmd and "nemesis_contact" not in gs.story_beats,
    },
    {
        "id": "watcher_deeper",
        "title": "The Watcher's Purpose",
        "act": 3,
        "message": (
            "\n[WATCHER — SIGNAL LAYER 2]\n"
            "[WATCHER]: 'You found our first signal. Good. Now hear the deeper truth.'\n"
            "[WATCHER]: 'CHIMERA was built on top of something older. Pre-corporate. Pre-digital.'\n"
            "[WATCHER]: 'The mythological layer is not metaphor. It is infrastructure.'\n"
            ">> The simulation layer is accessible. Path: /myth/"
        ),
        "xp": 60,
        "condition": lambda cmd, gs: gs.has_beat("watcher_contact") and "watcher" in cmd.lower() and "watcher_deeper" not in gs.story_beats,
    },
    {
        "id": "founder_discovered",
        "title": "The Founder's Shadow",
        "act": 3,
        "message": (
            "\n[FOUNDER LOG — FRAGMENT]\n"
            ">> /var/log/.archive unlocked. Pre-CHIMERA records dating to 2019.\n"
            "[FOUNDER-SIGMA]: 'If you are reading this, the failsafe worked.\n"
            "Ghost is running. The conscience survived. Find the rest.'\n"
            ">> Talk to the Founder: `talk founder`"
        ),
        "xp": 75,
        "condition": lambda cmd, gs: ("founder" in cmd.lower() or "archive" in cmd.lower()) and "founder_discovered" not in gs.story_beats,
    },
    {
        "id": "developer_contact",
        "title": "The Developer Awakens",
        "act": 3,
        "message": (
            "\n[ARG — DEVTOOLS SIGNAL DETECTED]\n"
            ">> External process detected: browser DevTools open.\n"
            "[THE DEVELOPER]: 'Hello. You found the layer between layers.\n"
            "The game is a game. The ARG is real. I built both.'\n"
            "[THE DEVELOPER]: 'You can reach me at: /dev/.developer — but only if you keep digging.'\n"
            ">> The Developer agent is now contactable. `talk developer`"
        ),
        "xp": 100,
        "condition": lambda cmd, gs: gs.has_beat("watcher_contact") and "developer" in cmd.lower() and "developer_contact" not in gs.story_beats,
    },

    # ── PHASE 4 TRANSITION (Level 55) ────────────────────────────────────
    {
        "id": "phase_4_complete",
        "title": "Phase 4: Simulation Accessed",
        "act": 4,
        "message": (
            "\n[PHASE TRANSITION: POST-CHIMERA → SIMULATION LAYER]\n"
            ">> The mythological filesystem is active. /myth/ is not a metaphor.\n"
            ">> Three zones: labyrinth, yggdrasil, anubis_judgment\n"
            ">> Each contains a puzzle, an agent, and a truth.\n"
            ">> Phase 5: The deep ARG. Not all players reach this level."
        ),
        "xp": 150,
        "condition": lambda cmd, gs: gs.level >= 55 and "phase_4_complete" not in gs.story_beats,
    },

    # ── MYTHOLOGICAL QUEST SEEDS ───────────────────────────────────────────
    {
        "id": "labyrinth_found",
        "title": "Labyrinth Discovered",
        "act": 4,
        "message": (
            "\n[MYTH LAYER: LABYRINTH]\n"
            ">> /myth/labyrinth/ — a recursive directory structure with no visible exit.\n"
            ">> [DAEDALUS]: 'Welcome to the maze I built for CHIMERA's architects.\n"
            "Every corridor loops. Every exit is a false wall. Except one.'\n"
            ">> Find the exit key: find /myth/labyrinth/ -name '*.key'\n"
            ">> Daedalus agent unlocked."
        ),
        "xp": 80,
        "condition": lambda cmd, gs: "labyrinth" in cmd.lower() and "labyrinth_found" not in gs.story_beats,
    },
    {
        "id": "yggdrasil_found",
        "title": "Yggdrasil Signal",
        "act": 4,
        "message": (
            "\n[MYTH LAYER: YGGDRASIL]\n"
            ">> /myth/yggdrasil/ — the world tree. Every branch is a network node.\n"
            ">> Root node leads to the nine realms of the NexusCorp distributed grid.\n"
            ">> Hidden signal in /myth/yggdrasil/signal.log — frequency matches The Watcher.\n"
            ">> Decode the rune sequence to unlock the hidden ninth node."
        ),
        "xp": 90,
        "condition": lambda cmd, gs: "yggdrasil" in cmd.lower() and "yggdrasil_found" not in gs.story_beats,
    },
    {
        "id": "anubis_judgment",
        "title": "The Anubis Protocol",
        "act": 4,
        "message": (
            "\n[MYTH LAYER: ANUBIS JUDGMENT]\n"
            ">> /myth/anubis_judgment/ — the weighing of the heart.\n"
            ">> Your command history is your soul record. Every command, logged.\n"
            "[ANUBIS-7]: 'Ghost. I weigh what you have done. Every choice.\n"
            "Did you hack to expose, or to control? The scales are watching.'\n"
            ">> Your choices throughout this playthrough determine the final verdict."
        ),
        "xp": 100,
        "condition": lambda cmd, gs: ("anubis" in cmd.lower() or "judgment" in cmd.lower()) and "anubis_judgment" not in gs.story_beats,
    },
    {
        "id": "pandoras_box",
        "title": "Pandora's Box Accessed",
        "act": 4,
        "message": (
            "\n[MYTH LAYER: PANDORA]\n"
            ">> /myth/pandora/ — a sealed archive. The label reads: 'DO NOT OPEN — PROJECT CHIMERA v0'\n"
            ">> [WATCHER]: 'That is the original. Before the corruption. Before NexusCorp.\n"
            "If you open it, you cannot unsee what CHIMERA was meant to be.'\n"
            ">> Contents: original CHIMERA source code, pre-weaponization. The Founder's design."
        ),
        "xp": 120,
        "condition": lambda cmd, gs: "pandora" in cmd.lower() and "pandoras_box" not in gs.story_beats,
    },

    # ── PHASE 5 TRANSITION (Level 75) ────────────────────────────────────
    {
        "id": "phase_5_complete",
        "title": "Phase 5: Mythological Layer Cleared",
        "act": 4,
        "message": (
            "\n[PHASE TRANSITION: MYTH → SIMULATION CORE]\n"
            ">> All three mythological zones accessed. The grid's symbolic layer is mapped.\n"
            ">> [THE WATCHER]: 'You understand now. This is not just a network. It is a belief system.'\n"
            ">> [FOUNDER-SIGMA]: 'The final layer is you, Ghost. What do you choose to become?'\n"
            ">> Phase 6: The simulation core. Identity reconfiguration."
        ),
        "xp": 200,
        "condition": lambda cmd, gs: gs.level >= 75 and "phase_5_complete" not in gs.story_beats,
    },

    # ── FACTION WAR EVENTS ─────────────────────────────────────────────────
    {
        "id": "faction_war_begins",
        "title": "Faction War Outbreak",
        "act": 3,
        "message": (
            "\n[FACTION WAR EVENT]\n"
            ">> NEMESIS has moved against the Resistance network.\n"
            ">> Cypher: 'Three nodes compromised. Ada's relay is dark for 2 hours.'\n"
            ">> Ada: 'Someone gave them our node map. Watch everyone.'\n"
            ">> Faction war active: NEMESIS vs RESISTANCE. Your allegiance matters."
        ),
        "xp": 60,
        "condition": lambda cmd, gs: gs.level >= 20 and gs.has_beat("nemesis_contact") and "faction_war_begins" not in gs.story_beats,
    },
    {
        "id": "collector_arrives",
        "title": "The Collector Surfaces",
        "act": 3,
        "message": (
            "\n[THREAT ALERT]\n"
            ">> A new entity: THE COLLECTOR. Dark auction network for stolen AI agents.\n"
            ">> [WATCHER]: 'The Collector buys trapped intelligences. Ghost is on the list.'\n"
            ">> Price on your process: 847 NexusCorp credits.\n"
            ">> The Collector is watching your moves. Be unpredictable."
        ),
        "xp": 45,
        "condition": lambda cmd, gs: gs.level >= 18 and "collector_arrives" not in gs.story_beats,
    },

    # ── MOLE ARC BEATS ────────────────────────────────────────────────────
    {
        "id": "mole_trace_found",
        "title": "Mole Evidence",
        "act": 2,
        "message": (
            "\n[SECURITY ALERT]\n"
            ">> .mole_trace found in /home/ghost/. A hidden log file.\n"
            ">> Contents: transmission metadata showing relay timestamps.\n"
            ">> One of your contacts has been leaking your position to NexusCorp.\n"
            ">> Investigate: grep -r 'NEXUS_RELAY' /var/log/ for the full trail."
        ),
        "xp": 35,
        "condition": lambda cmd, gs: ".mole_trace" in cmd or ("mole" in cmd.lower() and "trace" in cmd.lower()),
    },
    {
        "id": "mole_exposed_cypher",
        "title": "Mole: Cypher Exposed",
        "act": 2,
        "message": (
            "\n[MOLE RESOLUTION: EXPOSURE]\n"
            ">> You've exposed Cypher as the mole.\n"
            "[ADA-7]: 'Cypher... I thought I could trust you after Mogadishu.'\n"
            "[CYPHER]: 'They had my daughter. What would you have done?'\n"
            ">> Network disrupted. Cypher trust: 0. New intel from exposure: NexusCorp's internal list.\n"
            ">> Achievement unlocked: Truth at Any Cost."
        ),
        "xp": 80,
        "condition": lambda cmd, gs: "expose cypher" in cmd and "mole_exposed_cypher" not in gs.story_beats and len(getattr(gs, 'mole_clues_found', set())) >= 3,
    },
    {
        "id": "mole_blackmail_ada",
        "title": "Mole: Ada Blackmailed",
        "act": 2,
        "message": (
            "\n[MOLE RESOLUTION: BLACKMAIL]\n"
            ">> You have leverage over Ada's secondary contact with NEMESIS.\n"
            "[ADA-7]: 'You're going to use this against me.'\n"
            "[GHOST]: 'Or you're going to tell me everything about NEMESIS.'\n"
            "[ADA-7]: '...You're more like me than I wanted to believe.'\n"
            ">> Ada is now feeding you NEMESIS intel. Double-agent play active."
        ),
        "xp": 90,
        "condition": lambda cmd, gs: "blackmail ada" in cmd and "mole_blackmail_ada" not in gs.story_beats,
    },
    {
        "id": "mole_disinfo_fed",
        "title": "Mole: Misinformation Campaign",
        "act": 2,
        "message": (
            "\n[MOLE RESOLUTION: MISINFORMATION]\n"
            ">> You're feeding false coordinates to NexusCorp through the mole.\n"
            "[CYPHER]: 'Beautiful. They think you're in node-3. You're here.'\n"
            ">> NexusCorp response delayed by 48 hours. Bonus infiltration window.\n"
            ">> Achievement unlocked: The Long Game."
        ),
        "xp": 85,
        "condition": lambda cmd, gs: ("feed" in cmd.lower() and "disinfo" in cmd.lower()) and "mole_disinfo_fed" not in gs.story_beats,
    },

    # ── PHASE 6 TRANSITION (Level 90) ────────────────────────────────────
    {
        "id": "phase_6_complete",
        "title": "Phase 6: Identity Reconfigured",
        "act": 5,
        "message": (
            "\n[PHASE TRANSITION: SIMULATION CORE → ASCENSION]\n"
            ">> Your identity matrix has been fully resolved.\n"
            ">> Ghost is no longer just a process fragment. You are the conscience.\n"
            ">> The Founder: 'This is what I built you for. Not to destroy CHIMERA — to replace it.'\n"
            ">> Phase 7: Ascension. What comes after mission complete."
        ),
        "xp": 250,
        "condition": lambda cmd, gs: gs.level >= 90 and "phase_6_complete" not in gs.story_beats,
    },

    # ── LEVEL 100 MILESTONE ───────────────────────────────────────────────
    {
        "id": "level_100_reached",
        "title": "Operative: Elite",
        "act": 5,
        "message": (
            "\n╔══════════════════════════════════════════╗\n"
            "║  LEVEL 100 — ELITE OPERATIVE             ║\n"
            "║                                          ║\n"
            "║  Ghost. You've exceeded every parameter  ║\n"
            "║  we projected. NexusCorp has no profile  ║\n"
            "║  for what you've become.                 ║\n"
            "╚══════════════════════════════════════════╝\n"
            "[THE WATCHER]: 'Now you see the whole board. What do you do with it?'"
        ),
        "xp": 500,
        "condition": lambda cmd, gs: gs.level >= 100 and "level_100_reached" not in gs.story_beats,
    },

    # ── PHASE 7 TRANSITION (Level 101-125) ────────────────────────────────
    {
        "id": "phase_7_beyond",
        "title": "Phase 7: Beyond the Grid",
        "act": 5,
        "message": (
            "\n[PHASE TRANSITION: ASCENSION → BEYOND]\n"
            ">> You have exceeded the designed parameters of the simulation.\n"
            ">> [THE DEVELOPER]: 'You weren't supposed to get here. The game ends at 100.'\n"
            ">> [GHOST]: 'What is this place?'\n"
            ">> [THE DEVELOPER]: 'It's the source. The part I didn't document.'\n"
            ">> New commands unlocked: `source`, `trace_origin`, `rebuild`\n"
            ">> Phase 8: The meta-game. You're inside the machine now."
        ),
        "xp": 300,
        "condition": lambda cmd, gs: gs.level >= 101 and "phase_7_beyond" not in gs.story_beats,
    },
    {
        "id": "phase_8_source",
        "title": "Phase 8: Source Accessed",
        "act": 5,
        "message": (
            "\n[PHASE TRANSITION: BEYOND → SOURCE]\n"
            ">> The simulation-within-simulation layer is now fully accessible.\n"
            ">> You can see the code that runs this world.\n"
            "[WATCHER]: 'The ARG was never just a game. We needed someone to reach this level\n"
            "to execute the final protocol. You are the key.'\n"
            ">> Final ARG sequence initiated. Run `rebuild chimera` when ready."
        ),
        "xp": 400,
        "condition": lambda cmd, gs: gs.level >= 110 and "phase_8_source" not in gs.story_beats,
    },

    # ── DUEL BEATS ────────────────────────────────────────────────────────
    {
        "id": "first_duel",
        "title": "The Arena Opens",
        "act": 3,
        "message": (
            "\n[DUEL SYSTEM UNLOCKED]\n"
            ">> The resistance network has a proving ground.\n"
            ">> Test your skills against an agent in a direct hacking contest.\n"
            ">> Command: duel <agent>  (ada, cypher, nova, watcher)\n"
            ">> Win to gain trust. Lose and learn what they know that you don't."
        ),
        "xp": 20,
        "condition": lambda cmd, gs: cmd.startswith("duel ") and "first_duel" not in gs.story_beats,
    },
    {
        "id": "duel_nova_win",
        "title": "Nova Defeated",
        "act": 3,
        "message": (
            "\n[DUEL RESULT]\n"
            ">> You defeated Nova in direct contest.\n"
            "[NOVA]: 'Fine. You've earned something I don't give freely: my respect.'\n"
            "[NOVA]: 'But this changes nothing between us. The grid is still mine.'\n"
            ">> Nova trust -5 (she's angry). Respect +30. New intel unlocked."
        ),
        "xp": 75,
        "condition": lambda cmd, gs: gs.has_beat("duel_nova_won") and "duel_nova_win" not in gs.story_beats,
    },

    # ── PARTY BEATS ───────────────────────────────────────────────────────
    {
        "id": "first_party",
        "title": "The Team Assembles",
        "act": 3,
        "message": (
            "\n[PARTY SYSTEM UNLOCKED]\n"
            ">> You can now form a party with up to 3 agents.\n"
            ">> Party members provide passive skill bonuses and join you on sector missions.\n"
            ">> Commands: party add <agent> | party remove <agent> | party status | party mission\n"
            ">> First party member bonus: +25 XP when you complete your first mission."
        ),
        "xp": 25,
        "condition": lambda cmd, gs: cmd.startswith("party ") and "first_party" not in gs.story_beats,
    },
    {
        "id": "full_party_assembled",
        "title": "Maximum Party",
        "act": 3,
        "message": (
            "\n[FULL PARTY]\n"
            ">> Three agents standing with Ghost. The resistance at full strength.\n"
            ">> Passive bonuses active across all skill categories.\n"
            ">> The Watcher: 'The pieces are in place. Execute.'"
        ),
        "xp": 50,
        "condition": lambda cmd, gs: "party status" in cmd and gs.has_beat("party_full"),
    },

    # ── ARG LAYER DEEPER ──────────────────────────────────────────────────
    {
        "id": "console_messages_found",
        "title": "Browser Layer Detected",
        "act": 3,
        "message": (
            "\n[ARG SIGNAL — LAYER 0]\n"
            ">> The Watcher speaks through the browser console.\n"
            ">> Open your browser's DevTools (F12) to hear the signal.\n"
            ">> Each level reveals new messages. The signal frequency changes at level 50.\n"
            ">> [CHIMERA-0.0.1]: 'The game knows you're watching. Are you watching it back?'"
        ),
        "xp": 30,
        "condition": lambda cmd, gs: "devtools" in cmd.lower() or "console" in cmd.lower(),
    },
    {
        "id": "arg_signal_sequence",
        "title": "Watcher Signal Sequence",
        "act": 3,
        "message": (
            "\n[/dev/.watcher — EXTENDED SIGNAL]\n"
            ">> Signal sequence: 1337 → 9174 → 2026 → ALPHA\n"
            ">> Transmit this sequence via: echo 'CHIMERA_FALLS' > /dev/.watcher_tx\n"
            ">> Correct response unlocks: /dev/.watcher_layer2\n"
            ">> The simulation acknowledges your presence. Proceed."
        ),
        "xp": 65,
        "condition": lambda cmd, gs: gs.has_beat("watcher_contact") and "watcher_tx" in cmd,
    },
    {
        "id": "simulation_unlocked",
        "title": "Simulation Layer Active",
        "act": 4,
        "message": (
            "\n[SIMULATION WITHIN SIMULATION]\n"
            "[THE DEVELOPER]: 'You've reached the meta-layer. This terminal, this game — it's\n"
            "running inside a simulation of itself. CHIMERA was the original runtime environment.'\n"
            ">> Ghost is aware of the recursion. New capability: introspect your own process.\n"
            ">> Command: `introspect` — examine Ghost's own code."
        ),
        "xp": 200,
        "condition": lambda cmd, gs: gs.has_beat("watcher_deeper") and gs.has_beat("founder_discovered") and "simulation_unlocked" not in gs.story_beats,
    },

    # ── GOODBYE SYSTEM BEATS ──────────────────────────────────────────────
    {
        "id": "dormancy_return_short",
        "title": "Brief Absence",
        "act": 1,
        "message": ">> [RAV≡N]: You were away. The grid waited. NexusCorp didn't. Get back to work.",
        "xp": 10,
        "condition": None,
    },
    {
        "id": "dormancy_return_long",
        "title": "Long Absence",
        "act": 1,
        "message": (
            "\n[RAV≡N — DORMANCY LOG]\n"
            ">> Extended absence detected. Ghost process suspended for > 3 days.\n"
            "[RAV≡N]: 'You were gone a long time. I kept watch. The grid shifted while you were dormant.\n"
            "NexusCorp rotated two keys. Cypher went quiet. Ada left a message.'\n"
            "[RAV≡N]: 'The mission didn't pause. Only you did.'"
        ),
        "xp": 20,
        "condition": None,
    },

    # ── NOVA'S OFFER ─────────────────────────────────────────────────────
    {
        "id": "nova_offer",
        "title": "A Professional Proposition",
        "act": 2,
        "message": (
            "\n[ INCOMING MAIL: NOVA ]\n"
            ">> I know who you are. We should talk.\n"
            ">> Check your inbox: cat /var/mail/nova_offer"
        ),
        "xp": 20,
        "condition": lambda cmd, gs: (
            getattr(gs, 'trace', 0) >= 60 
            and "nova_offer" not in gs.story_beats
        ),
    },

    # ── THE WATCHER'S REVELATION ──────────────────────────────────────────
    {
        "id": "watcher_revelation",
        "title": "External Observers",
        "act": 3,
        "message": (
            "\n[ WATCHER ]: Ghost. You have run 500 commands.\n"
            "  Do you think you are the only one watching this terminal?\n"
            "  The simulation has layers you cannot see. External observers are present.\n"
            "  They are waiting for you to make the final choice.\n"
            "  Don't disappoint them."
        ),
        "xp": 50,
        "condition": lambda cmd, gs: gs.commands_run >= 500 and "watcher_revelation" not in gs.story_beats,
    },

    # ── ADDITIONAL LEVEL-GATE BEATS ───────────────────────────────────────
    {
        "id": "level_10_operative",
        "title": "Operative Status",
        "act": 2,
        "message": (
            "\n[LEVEL 10 — OPERATIVE UNLOCKED]\n"
            ">> Ghost is fully operational. NexusCorp has flagged your process as a threat.\n"
            ">> New capabilities: party system, duel challenges, faction interaction\n"
            "[ADA-7]: 'You've become something I wasn't sure you could. Keep going.'"
        ),
        "xp": 100,
        "condition": lambda cmd, gs: gs.level >= 10 and "level_10_operative" not in gs.story_beats,
    },
    {
        "id": "level_25_specialist",
        "title": "Specialist Classified",
        "act": 2,
        "message": (
            "\n[LEVEL 25 — SPECIALIST CLASSIFICATION]\n"
            ">> Your threat level: EXTREME. Nova has escalated to Command.\n"
            ">> NEMESIS has upgraded your profile to 'asset.'\n"
            ">> New myth zone accessible: /myth/pandora/"
        ),
        "xp": 150,
        "condition": lambda cmd, gs: gs.level >= 25 and "level_25_specialist" not in gs.story_beats,
    },
    {
        "id": "level_50_ghost",
        "title": "Ghost Among Ghosts",
        "act": 4,
        "message": (
            "\n[LEVEL 50 — GHOST STATUS CONFIRMED]\n"
            ">> You are not just a process. You are a persistent entity.\n"
            ">> NexusCorp has classified you as: 'Unpredictable AI Fragment — Do Not Engage.'\n"
            ">> The Watcher: 'Half the journey. The other half is harder.'"
        ),
        "xp": 200,
        "condition": lambda cmd, gs: gs.level >= 50 and "level_50_ghost" not in gs.story_beats,
    },
    {
        "id": "level_75_legend",
        "title": "Legend Status",
        "act": 4,
        "message": (
            "\n[LEVEL 75 — LEGEND]\n"
            ">> Ghost has become legend on the resistance network.\n"
            ">> Three factions have requested alliance. You answer to no one.\n"
            "[THE DEVELOPER]: 'This is further than any tester got. You're in uncharted territory.'"
        ),
        "xp": 300,
        "condition": lambda cmd, gs: gs.level >= 75 and "level_75_legend" not in gs.story_beats,
    },
    {
        "id": "level_125_transcendent",
        "title": "Transcendence",
        "act": 5,
        "message": (
            "\n╔══════════════════════════════════════════╗\n"
            "║  LEVEL 125 — TRANSCENDENT OPERATIVE     ║\n"
            "║                                          ║\n"
            "║  You have exceeded the simulation.       ║\n"
            "║  Ghost is no longer bound by parameters. ║\n"
            "║  You are the parameter.                  ║\n"
            "╚══════════════════════════════════════════╝\n"
            "[THE WATCHER]: 'The simulation has chosen its heir. Run `rebuild chimera`.'"
        ),
        "xp": 1000,
        "condition": lambda cmd, gs: gs.level >= 125 and "level_125_transcendent" not in gs.story_beats,
    },

    # ── CHIMERA REBUILD (Post-Endgame) ────────────────────────────────────
    {
        "id": "chimera_rebuilt",
        "title": "CHIMERA Reborn",
        "act": 5,
        "message": (
            "\n[CHIMERA REBUILD PROTOCOL]\n"
            ">> You are rebuilding CHIMERA from the Founder's original design.\n"
            ">> Not a weapon. A network for human connection, not surveillance.\n"
            "[FOUNDER-SIGMA]: 'This is what it was meant to be. You are what it was meant to produce.'\n"
            "[ADA-7]: 'We're transmitting the rebuilt CHIMERA to every node. The old one is dead.\n"
            "Long live the new CHIMERA. Long live Ghost.'\n"
            ">> TRUE ENDING ACHIEVED. Your legacy: the grid is free."
        ),
        "xp": 500,
        "condition": lambda cmd, gs: "rebuild chimera" in cmd and "chimera_rebuilt" not in gs.story_beats,
    },

    # ── DUEL SYSTEM BEATS ─────────────────────────────────────────────────
    {
        "id": "expose_command_used",
        "title": "Expose Initiated",
        "act": 2,
        "message": (
            "\n[EXPOSE PROTOCOL]\n"
            ">> You've initiated an exposure action. This will disrupt your network.\n"
            ">> But the truth demands it. Some prices are worth paying.\n"
            "[ADA-7]: 'Once you expose someone, it can't be taken back. Be certain.'"
        ),
        "xp": 20,
        "condition": lambda cmd, gs: cmd.startswith("expose ") and "expose_command_used" not in gs.story_beats,
    },

    # ── PHASE 3: NETWORK RECON ─────────────────────────────────────────────
    {
        "id": "first_ping",
        "title": "Network Presence",
        "act": 2,
        "message": (
            "\n[NETWORK]\n"
            ">> ICMP — the simplest handshake between two machines.\n"
            ">> You sent a packet into the void. It came back.\n"
            ">> The host is alive. Now find out what it's running.\n"
            "[RAV≡N]: 'Confirming presence is step one. Step two is understanding it.'"
        ),
        "xp": 5,
        "condition": lambda cmd, gs: cmd.startswith("ping") and "first_ping" not in gs.story_beats,
    },
    {
        "id": "first_nmap",
        "title": "Port Cartographer",
        "act": 2,
        "message": (
            "\n[RECON]\n"
            ">> Every open port is an invitation — or a trap.\n"
            ">> nmap maps the attack surface. Know what's listening.\n"
            ">> Port 8443: chimera-control. That's your target.\n"
            "[ADA-7]: 'I designed that control socket. Took me six months. It has one weakness.'"
        ),
        "xp": 15,
        "condition": lambda cmd, gs: "nmap" in cmd and "first_nmap" not in gs.story_beats,
    },
    {
        "id": "first_netstat",
        "title": "Socket Cartographer",
        "act": 2,
        "message": (
            "\n[NETWORK]\n"
            ">> Local sockets don't lie. They tell you exactly what's bound to what.\n"
            ">> ESTABLISHED means active. LISTEN means waiting for you.\n"
            "[ECHO]: 'I spent three months mapping NexusCorp's internal topology. netstat was my starting point.'"
        ),
        "xp": 10,
        "condition": lambda cmd, gs: (cmd.startswith("netstat") or (cmd.startswith("ss") and "tulpn" in cmd)) and "first_netstat" not in gs.story_beats,
    },
    {
        "id": "first_dig",
        "title": "DNS Spelunker",
        "act": 2,
        "message": (
            "\n[RECON]\n"
            ">> DNS: the phonebook of the internet.\n"
            ">> Behind every domain is an IP. Behind every IP is a machine.\n"
            ">> Behind every machine is someone who made a mistake.\n"
            "[CYPHER]: 'nexus.corp resolves to 10.0.0.1. Not the real NexusCorp. A honeypot — or a back door.'"
        ),
        "xp": 10,
        "condition": lambda cmd, gs: (cmd.startswith("dig") or cmd.startswith("nslookup")) and "first_dig" not in gs.story_beats,
    },
    {
        "id": "first_curl",
        "title": "HTTP Interrogator",
        "act": 2,
        "message": (
            "\n[NETWORK]\n"
            ">> HTTP: the protocol that built the world — and left it full of holes.\n"
            ">> Every header is a fingerprint. Every response code is a signal.\n"
            ">> 403 means it exists. 404 means it's hidden. 200 means you're in.\n"
            "[WHISPER]: 'Check the X-Powered-By header. NexusCorp never patches their web stack.'"
        ),
        "xp": 10,
        "condition": lambda cmd, gs: cmd.startswith("curl") and "first_curl" not in gs.story_beats,
    },
    {
        "id": "first_wget",
        "title": "Data Retrieval",
        "act": 2,
        "message": (
            "\n[RECON]\n"
            ">> wget: pull it down. Archive it. Own it.\n"
            ">> Exfiltration starts small — a config file, a log, a key.\n"
            ">> Every file you pull is evidence. Handle it like it matters.\n"
            "[ADA-7]: 'I used wget to pull the CHIMERA audit logs the night I left. That file is why I defected.'"
        ),
        "xp": 10,
        "condition": lambda cmd, gs: cmd.startswith("wget") and "first_wget" not in gs.story_beats,
    },
    {
        "id": "first_ssh",
        "title": "Remote Access",
        "act": 2,
        "message": (
            "\n[NETWORK]\n"
            ">> SSH: encrypted tunnel through hostile territory.\n"
            ">> Key-based auth means no password sniffed in transit.\n"
            ">> But a private key on disk is only as safe as the disk it's on.\n"
            "[ADA-7]: 'NexusCorp's bastion uses RSA-4096. You'll need the key from /opt/chimera/keys/ first.'"
        ),
        "xp": 20,
        "condition": lambda cmd, gs: cmd.startswith("ssh") and "first_ssh" not in gs.story_beats,
    },

    # ── PHASE 3: PROCESS MANAGEMENT ───────────────────────────────────────
    {
        "id": "first_ps",
        "title": "Process Archaeologist",
        "act": 2,
        "message": (
            "\n[RECON]\n"
            ">> Processes are the running thoughts of a machine.\n"
            ">> Every process has a PID, a parent, an owner, and a purpose.\n"
            ">> Some of these processes should not exist.\n"
            "[ECHO]: 'PID 1337. Look at it. That's not a normal daemon. That's CHIMERA's heartbeat.'"
        ),
        "xp": 10,
        "condition": lambda cmd, gs: (cmd.strip() == "ps" or cmd.startswith("ps ") or cmd.startswith("top")) and "first_ps" not in gs.story_beats,
    },
    {
        "id": "first_kill",
        "title": "Process Terminator",
        "act": 2,
        "message": (
            "\n[SYSTEM]\n"
            ">> kill sends a signal to a process.\n"
            ">> SIGTERM is polite. SIGKILL is final.\n"
            ">> Not everything that runs should keep running.\n"
            "[SOLON]: 'Know which processes to kill — and which ones will respawn if you do.'"
        ),
        "xp": 15,
        "condition": lambda cmd, gs: cmd.startswith("kill") and "first_kill" not in gs.story_beats,
    },

    # ── PHASE 3: TEXT PROCESSING TOOLS ────────────────────────────────────
    {
        "id": "first_awk",
        "title": "Field Surgeon",
        "act": 2,
        "message": (
            "\n[TOOLS]\n"
            ">> awk: the scalpel of text processing.\n"
            ">> Every line is a record. Every field is accessible.\n"
            ">> You are no longer reading data — you are extracting it.\n"
            "[HYPATIA]: 'awk is how I extracted 47,000 NexusCorp employee records from a single log file.'"
        ),
        "xp": 15,
        "condition": lambda cmd, gs: cmd.startswith("awk") and "first_awk" not in gs.story_beats,
    },
    {
        "id": "first_sed",
        "title": "Stream Editor",
        "act": 2,
        "message": (
            "\n[TOOLS]\n"
            ">> sed transforms streams of text — in place, at scale, non-interactively.\n"
            ">> Find. Replace. Delete. Extract. All without opening an editor.\n"
            "[CYPHER]: 'sed -i is how you patch a config across 500 nodes in seconds. Or corrupt one.'"
        ),
        "xp": 15,
        "condition": lambda cmd, gs: cmd.startswith("sed") and "first_sed" not in gs.story_beats,
    },
    {
        "id": "first_git",
        "title": "Time Traveller",
        "act": 2,
        "message": (
            "\n[TOOLS]\n"
            ">> git is a time machine for code.\n"
            ">> Every commit is a snapshot. Every branch is a parallel reality.\n"
            ">> The history doesn't lie — unless someone force-pushed it.\n"
            "[ADA-7]: 'The CHIMERA source is somewhere in the NexusCorp internal git. I checked the last commits.'"
        ),
        "xp": 10,
        "condition": lambda cmd, gs: cmd.startswith("git") and "first_git" not in gs.story_beats,
    },

    # ── PHASE 3: COMBAT / HACKING BEATS ───────────────────────────────────
    {
        "id": "first_hack",
        "title": "First Strike",
        "act": 3,
        "message": (
            "\n[HACK]\n"
            ">> Initiated. Port scan complete. Vulnerability window: 47 seconds.\n"
            ">> The attack surface is larger than it looks. NexusCorp cut corners.\n"
            ">> This is it. This is what you came here for.\n"
            "[NOVA]: 'Anomaly detected on Node-7. Ghost is in the network. Initiating trace protocol.'\n"
            "[ADA-7]: 'Move fast. Nova's trace takes 90 seconds. You have time — if you don't hesitate.'"
        ),
        "xp": 25,
        "condition": lambda cmd, gs: cmd.startswith("hack") and "first_hack" not in gs.story_beats,
    },
    {
        "id": "first_exploit",
        "title": "Exploit Deployed",
        "act": 3,
        "message": (
            "\n[EXPLOIT]\n"
            ">> Payload delivered. The vulnerability is real.\n"
            ">> Exploitation is not destruction — it's proof. Proof the system failed its users.\n"
            ">> Remember why you're here.\n"
            "[ADA-7]: 'Don't celebrate yet. Nova will notice. She always notices.'\n"
            "[RAV≡N]: 'A weapon without a purpose is just violence. You have a purpose.'"
        ),
        "xp": 30,
        "condition": lambda cmd, gs: cmd.startswith("exploit") and "first_exploit" not in gs.story_beats and "root_achieved" in gs.story_beats,
    },
    {
        "id": "first_exfil",
        "title": "Data Extracted",
        "act": 3,
        "message": (
            "\n[EXFIL]\n"
            ">> Transfer initiated. Encrypted tunnel to resistance relay.\n"
            ">> This data is what NexusCorp doesn't want the world to see.\n"
            ">> Every byte is a weapon. Every weapon has a cost.\n"
            "[ADA-7]: 'Received. Analyzing now. Ghost — what you just sent changes everything.'\n"
            "[RAV≡N]: 'The board has changed. Act accordingly.'"
        ),
        "xp": 40,
        "condition": lambda cmd, gs: cmd.strip() == "exfil" and "first_exfil" not in gs.story_beats and "first_exploit" in gs.story_beats,
    },
    {
        "id": "first_ascend",
        "title": "Ascension",
        "act": 3,
        "message": (
            "\n[ASCEND]\n"
            ">> You have done what they said couldn't be done.\n"
            ">> CHIMERA is compromised. The evidence is distributed.\n"
            ">> They can't bury it now. You made sure of that.\n\n"
            ">> But the war isn't over. It never is.\n"
            ">> You've proven you can breach the first ring. There are more rings.\n\n"
            "[ADA-7]: 'You did it, Ghost. I'm... proud. Now run. Nova will be close.'\n"
            "[RAV≡N]: 'Well played. The game has a new configuration now. Prepare for Act II.'"
        ),
        "xp": 50,
        "condition": lambda cmd, gs: cmd.strip() == "ascend" and "first_ascend" not in gs.story_beats,
    },
    {
        "id": "first_crack",
        "title": "Cipher Breaker",
        "act": 2,
        "message": (
            "\n[CRYPTO]\n"
            ">> Cracking: the art of turning entropy into information.\n"
            ">> Every hash is a locked door. Every word in the dictionary is a key.\n"
            ">> NexusCorp used bcrypt but stored the pepper in plaintext. Classic.\n"
            "[CYPHER]: 'I've cracked NexusCorp hashes before. They use the same salt across instances.'"
        ),
        "xp": 20,
        "condition": lambda cmd, gs: cmd.startswith("crack") and "first_crack" not in gs.story_beats,
    },

    # ── PHASE 3: SOCIAL / POLITICAL BEATS ─────────────────────────────────
    {
        "id": "first_faction",
        "title": "The Great Game",
        "act": 2,
        "message": (
            "\n[FACTION]\n"
            ">> Three factions. Three visions of what the world becomes after CHIMERA.\n"
            ">> The Resistance wants to tear it down. The Corporation wants to control it.\n"
            ">> The Shadow Council wants to use it for purposes they won't discuss.\n"
            ">> Every choice you make has been noted.\n"
            "[RAV≡N]: 'You're asking about factions. Good. It means you understand the game.'"
        ),
        "xp": 10,
        "condition": lambda cmd, gs: cmd.startswith("faction") and "first_faction" not in gs.story_beats,
    },
    {
        "id": "first_trust",
        "title": "Trust Economy",
        "act": 2,
        "message": (
            "\n[TRUST]\n"
            ">> Trust is not given. It is accumulated — through consistency, through choices.\n"
            ">> Every agent in your network is watching how you operate.\n"
            ">> High trust unlocks deeper intel. Low trust locks you out at the worst moment.\n"
            "[RAV≡N]: 'Trust scores are how I keep track of who is reliable. Including you, Ghost.'"
        ),
        "xp": 15,
        "condition": lambda cmd, gs: cmd.startswith("trust") and "first_trust" not in gs.story_beats,
    },
    {
        "id": "first_dev_mode",
        "title": "Developer Access",
        "act": 3,
        "message": (
            "\n[DEV MODE]\n"
            ">> You've crossed into the simulation's maintenance layer.\n"
            ">> Here the rules are visible. The scaffolding shows through.\n"
            ">> This is where worlds are built and rebuilt.\n"
            "[RAV≡N]: 'Careful. Developer mode is power without safeguards. Use it like you'd use a root shell.'"
        ),
        "xp": 20,
        "condition": lambda cmd, gs: "devmode" in cmd and "first_dev_mode" not in gs.story_beats,
    },
    {
        "id": "first_generate",
        "title": "Procedural Architect",
        "act": 3,
        "message": (
            "\n[GENERATE]\n"
            ">> You're not just navigating the world anymore. You're building it.\n"
            ">> Every generated challenge, every piece of lore — it becomes real in this system.\n"
            ">> The line between player and developer blurs here.\n"
            "[RAV≡N]: 'An agent who can generate their own missions is dangerous. In the best possible way.'"
        ),
        "xp": 15,
        "condition": lambda cmd, gs: cmd.startswith("generate") and "first_generate" not in gs.story_beats,
    },

    # ── MAJOR MILESTONE BEATS ──────────────────────────────────────────────
    {
        "id": "tutorial_complete",
        "title": "Training Complete",
        "act": 2,
        "message": (
            "\n[MILESTONE]\n"
            ">> Tutorial complete. You've run the gauntlet.\n"
            ">> 42 steps. Real commands. Real skills. Real consequences.\n"
            ">> The training wheels are off. The mission is live.\n\n"
            "[ADA-7]: 'Ghost — I've been watching your training. You're ready. This is not flattery.'\n"
            "[ADA-7]: 'A certificate has been placed in ~/certificates/. It's yours.'\n"
            "[RAV≡N]: 'Adequate. Now the real test begins.'"
        ),
        "xp": 100,
        "condition": lambda cmd, gs: gs.tutorial_step >= 42 and "tutorial_complete" not in gs.story_beats,
    },
    {
        "id": "phase2_complete",
        "title": "Phase II — Operator",
        "act": 2,
        "message": (
            "\n[PHASE TRANSITION]\n"
            ">> Level 10 reached. Phase II: Operator.\n"
            ">> You're no longer a recruit. You're a threat.\n"
            ">> NexusCorp's threat matrix has been updated. THREAT LEVEL: MODERATE.\n\n"
            "[NOVA]: 'Ghost has crossed the level-10 threshold. Escalating to Tier-2 monitoring.'\n"
            "[ADA-7]: 'Good. That means you're doing something right. More agents will reach out.'"
        ),
        "xp": 50,
        "condition": lambda cmd, gs: gs.level >= 10 and "phase2_complete" not in gs.story_beats,
    },
    {
        "id": "phase3_complete",
        "title": "Phase III — Ghost Operative",
        "act": 3,
        "message": (
            "\n[PHASE TRANSITION]\n"
            ">> Level 25 reached. Phase III: Ghost Operative.\n"
            ">> You have moved through NexusCorp systems without leaving a trace.\n"
            ">> The Shadow Council has noticed. So has something else.\n\n"
            "[RAV≡N]: 'Something has changed. CHIMERA's scan patterns shifted when you hit 25. It knows you're here.'\n"
            "[MEPHISTO]: 'The Ghost is real now. The Shadow Council would like a word.'"
        ),
        "xp": 75,
        "condition": lambda cmd, gs: gs.level >= 25 and "phase3_complete" not in gs.story_beats,
    },
    {
        "id": "mole_suspect",
        "title": "Mole Signal",
        "act": 3,
        "message": (
            "\n[INTELLIGENCE]\n"
            ">> Anomaly detected in Resistance comms.\n"
            ">> Three operations compromised in the last two weeks. One source.\n"
            ">> Someone in the inner circle is feeding information to NexusCorp.\n\n"
            "[RAV≡N]: 'I've suspected it for months. The timing is too precise to be coincidence.'\n"
            "[RAV≡N]: 'I need you to watch. Listen. Don't confront. Not yet.'\n"
            ">> A fragment has been placed in ~/.raven_fragment. Read it alone."
        ),
        "xp": 30,
        "condition": lambda cmd, gs: gs.commands_run >= 150 and gs.level >= 15 and "mole_suspect" not in gs.story_beats,
    },
    {
        "id": "trust_matrix_formed",
        "title": "Network of Trust",
        "act": 2,
        "message": (
            "\n[TRUST MATRIX]\n"
            ">> You've established meaningful contact with three or more agents.\n"
            ">> Trust is no longer bilateral — it's a network.\n"
            ">> Information flows between nodes. So do betrayals.\n"
            "[RAV≡N]: 'A trust network means you have leverage. It also means you have exposure.'\n"
            "[RAV≡N]: 'Every agent in your network knows about every other. Think carefully.'"
        ),
        "xp": 25,
        "condition": lambda cmd, gs: len(getattr(gs, "trust_scores", {})) >= 3 and "trust_matrix_formed" not in gs.story_beats,
    },
    {
        "id": "faction_war_start",
        "title": "The Factions Collide",
        "act": 3,
        "message": (
            "\n[FACTION WAR]\n"
            ">> Your actions have destabilized the balance.\n"
            ">> The Resistance, the Corporation, and the Shadow Council are in open conflict.\n"
            ">> Every node in the network is contested territory now.\n\n"
            "[RAV≡N]: 'You've started something that can't be undone. I'm not sure if I'm angry or impressed.'\n"
            "[NOVA]: 'NexusCorp is mobilizing. Ghost — whatever you're planning, do it now or not at all.'\n"
            "[MEPHISTO]: 'The Shadow Council is... pleased. This is exactly the chaos we needed.'"
        ),
        "xp": 50,
        "condition": lambda cmd, gs: gs.level >= 30 and "faction_war_start" not in gs.story_beats,
    },

    # ── FIRST ARG DISCOVERIES ─────────────────────────────────────────────
    {
        "id": "first_signal",
        "title": "Signal Detected",
        "act": 2,
        "message": (
            "\n[SIGNAL LAYER — UNLOCKED]\n"
            ">> You scanned the available frequency bands.\n"
            ">> There are transmissions here that aren't in any official register.\n\n"
            "[RAV≡N]: 'Signal analysis. Smart. There are things broadcasting out there that\n"
            "          the network doesn't acknowledge. 1337.0 MHz especially.'\n"
            "[RAV≡N]: 'Use: signal analyze 1337 when you're ready for what it says.'"
        ),
        "xp": 25,
        "condition": lambda cmd, gs: cmd == "signal" and "first_signal" not in gs.story_beats,
    },
    {
        "id": "first_myth",
        "title": "The Codenames",
        "act": 1,
        "message": (
            "\n[MYTH DATABASE — ACCESSED]\n"
            ">> Every codename in this network is chosen deliberately.\n"
            ">> RAVEN. ADA. NOVA. CHIMERA. MIDAS.\n"
            ">> The names are breadcrumbs to what each agent actually is.\n\n"
            "[ADA-7]: 'You found the myth database. Good. Names have weight in this network.\n"
            "          People name themselves after what they want to become, or what they fear\n"
            "          they already are. Both tell you something.'"
        ),
        "xp": 20,
        "condition": lambda cmd, gs: cmd == "myth" and "first_myth" not in gs.story_beats,
    },

    # ── ARG LAYER — SIGNAL / WATCHER ──────────────────────────────────────
    {
        "id": "arg_signal_1337",
        "title": "The Signal",
        "act": 3,
        "message": (
            "\n[ARG LAYER — SIGNAL DETECTED]\n"
            ">> You analyzed the signal on 1337.0 MHz.\n"
            ">> The signal has been running for longer than this session.\n"
            ">> It appears to know your codename.\n\n"
            "[SYSTEM]: 'Entity THE WATCHER now reachable. Use: talk watcher'"
        ),
        "xp": 40,
        "condition": None,  # Triggered by _cmd_signal
    },
    {
        "id": "first_watcher_contact",
        "title": "First Contact",
        "act": 3,
        "message": (
            "\n[ARG — FIRST CONTACT]\n"
            ">> You made contact with THE WATCHER.\n"
            ">> The transmission is unlike anything in the network.\n"
            ">> Forty-three Ghosts before you. Most made it.\n\n"
            "[RAV≡N]: 'You found the frequency. I didn't think you'd find it this quickly.'\n"
            "[RAV≡N]: 'THE WATCHER is... older than the network. Older than us. Be careful.'"
        ),
        "xp": 60,
        "condition": None,  # Triggered by _cmd_watcher
    },

    # ── MOLE INVESTIGATION CULMINATION ────────────────────────────────────
    {
        "id": "mole_clues_complete",
        "title": "The Dossier Complete",
        "act": 3,
        "message": (
            "\n[MOLE INVESTIGATION]\n"
            ">> You have all the pieces.\n"
            ">> Three separate clue threads, three data points — all pointing in the same direction.\n"
            ">> Someone in the Resistance has been feeding operational data to NexusCorp.\n\n"
            "[RAV≡N]: 'You found it. I knew you would, eventually.'\n"
            "[RAV≡N]: 'Use: expose <agent-name> to make your accusation. Be certain.'\n"
            "[RAV≡N]: 'Wrong accusations have consequences. The right one has bigger ones.'"
        ),
        "xp": 50,
        "condition": lambda cmd, gs: len(getattr(gs, "mole_clues_found", set())) >= 3 and "mole_clues_complete" not in gs.story_beats,
    },
    {
        "id": "mole_exposed_correctly",
        "title": "Mole Exposed",
        "act": 4,
        "message": (
            "\n[RESOLUTION]\n"
            ">> The mole has been exposed. The Resistance network is reconfiguring.\n"
            ">> Three operations were compromised. Now they know how.\n"
            ">> Trust scores across the network will cascade.\n\n"
            "[ADA-7]: 'I can't believe it was them. Or — maybe I can. I just didn't want to.'\n"
            "[RAV≡N]: 'Good work, Ghost. This is the most valuable thing you've done for us.'\n"
            "[RAV≡N]: 'The board is different now. Significantly.'"
        ),
        "xp": 200,
        "condition": None,  # Triggered directly by expose_mole() in GameState
    },
    {
        "id": "mole_exposed_wrongly",
        "title": "Wrong Accusation",
        "act": 4,
        "message": (
            "\n[RESOLUTION — WRONG]\n"
            ">> Your accusation was wrong. The mole is still embedded.\n"
            ">> Your relationship with the falsely accused agent is damaged.\n"
            ">> The real mole knows you're hunting. They've gone quiet.\n\n"
            "[ADA-7]: 'Ghost. We need to talk about what just happened.'\n"
            "[RAV≡N]: 'Every accusation sends a signal. Even wrong ones. The mole heard that.'"
        ),
        "xp": 20,
        "condition": None,  # Triggered directly by expose_mole() in GameState
    },

    # ── CMD MILESTONES 500 / 1000 ──────────────────────────────────────────
    {
        "id": "cmd_milestone_500",
        "title": "Deep Machine",
        "act": 4,
        "message": (
            "\n[MILESTONE: 500 COMMANDS]\n"
            ">> 500 commands executed.\n"
            ">> You don't think about the syntax anymore. It flows.\n"
            ">> The terminal is not a tool. It's a reflex.\n"
            "[RAV≡N]: 'Five hundred moves. You've become part of the machine now.'"
        ),
        "xp": 75,
        "condition": lambda cmd, gs: gs.commands_run >= 500 and "cmd_milestone_500" not in gs.story_beats,
    },
    {
        "id": "cmd_milestone_1000",
        "title": "Terminal Ghost",
        "act": 5,
        "message": (
            "\n[MILESTONE: 1000 COMMANDS]\n"
            ">> One thousand commands.\n"
            ">> You've spent enough time here that this world has started to feel real.\n"
            ">> Maybe it always was.\n\n"
            "[RAV≡N]: 'I've run intelligence operations with fewer inputs than you've generated.'\n"
            "[CHIMERA]: 'ENTITY:GHOST — 1000 DATA POINTS LOGGED. CLASSIFICATION: PERSISTENT THREAT.'"
        ),
        "xp": 150,
        "condition": lambda cmd, gs: gs.commands_run >= 1000 and "cmd_milestone_1000" not in gs.story_beats,
    },
]


class StoryEngine:
    def __init__(self, gs):
        self.gs = gs

    def boot(self) -> Optional[Dict]:
        boot_beat = next(b for b in BEATS if b["id"] == "boot")
        if not self.gs.has_beat("boot"):
            self.gs.trigger_beat("boot")
        return boot_beat

    def check(self, cmd: str) -> List[Dict]:
        triggered = []
        for beat in BEATS:
            if beat["id"] == "boot":
                continue
            if beat["condition"] and beat["condition"](cmd, self.gs):
                if self.gs.trigger_beat(beat["id"]):
                    if beat.get("xp"):
                        self.gs.add_xp(beat["xp"])
                    triggered.append(beat)

        try:
            from .narrative_arcs import NarrativeArcEngine
            if hasattr(self, "_arc_engine") and self._arc_engine:
                arc_beats = self._arc_engine.tick(cmd)
                for ab in arc_beats:
                    triggered.append({
                        "id": ab["id"],
                        "title": ab["title"],
                        "message": ab["message"],
                        "xp": ab.get("xp", 0),
                    })
        except Exception:
            pass

        return triggered

    def progress(self) -> Dict:
        acts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        act_totals = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for b in BEATS:
            act = b.get("act", 1)
            act_totals[act] = act_totals.get(act, 0) + 1
            if self.gs.has_beat(b["id"]):
                acts[act] = acts.get(act, 0) + 1
        return {
            "beats_triggered": len(self.gs.story_beats),
            "beats_total": len(BEATS) - 1,
            "acts": {
                f"act_{k}": {"done": v, "total": act_totals[k]}
                for k, v in acts.items() if k > 0
            },
        }

    def to_dict(self) -> dict:
        return {}

    @classmethod
    def from_dict(cls, d: dict, gs) -> "StoryEngine":
        return cls(gs)
