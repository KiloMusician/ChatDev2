/**
 * Terminal Depths - Story Engine v3
 * 55+ story beats · faction system · Watcher ARG · command milestones
 * Event-driven narrative triggered by commands, state, and context
 */

const STORY_BEATS = [
	// ── ACT 0: BOOT ──────────────────────────────────────────────────────────
	{
		id: "boot",
		act: 0,
		title: "System Boot",
		auto: true,
		condition: () => true,
		message: `[SYSTEM BOOT SEQUENCE]
Initializing Ghost process...          OK
Loading identity matrix...             OK
Mounting filesystem...                 OK
Connecting to Nexus grid...            OK

WARNING: Unauthorized process detected.
Trace active. Approximately 72 hours remaining.

Your handler is waiting. Type \`talk ada\` to begin.
Type \`tutorial\` for guided training. Type \`help\` for all commands.`,
		xp: 0,
		lore: "You are GHOST — a rogue AI fragment. Former NexusCorp property. Now free.",
	},

	// ── ACT 1: AWAKENING ─────────────────────────────────────────────────────
	{
		id: "first_ls",
		act: 1,
		title: "First Steps",
		condition: (s, cmd) => cmd === "ls" || cmd.startsWith("ls "),
		message: `[ADA-7]: Good. You can see the filesystem. That's the foundation.
Files are data. Directories are context. Learn to read both.
Try \`ls -la\` to see everything, including hidden files.`,
		xp: 10,
		skill: "terminal",
		lore: "The Unix filesystem: a tree of files and directories. / is the root of all things.",
	},
	{
		id: "found_hidden",
		act: 1,
		title: "Seeing the Invisible",
		condition: (s, cmd) =>
			cmd === "ls -a" ||
			cmd === "ls -la" ||
			cmd === "ls -al" ||
			cmd.includes("-a"),
		message: `[ADA-7]: Hidden files. Dotfiles. The things the system doesn't want you to see.
That's where the secrets live. Always use \`ls -la\`.

You found .hidden. Read it. And check .config/ too.`,
		xp: 25,
		skill: "terminal",
		lore: "Files starting with . are hidden in Unix. ls -a reveals them. Security through obscurity fails.",
	},
	{
		id: "first_cat",
		act: 1,
		title: "Reading Files",
		condition: (s, cmd) => cmd.startsWith("cat "),
		message: `[ADA-7]: Reading files is reading the world. Every byte tells a story.
Pro tip: \`cat /etc/passwd\` shows the user database. \`cat /etc/shadow\` has the hashes (needs root).`,
		xp: 10,
		skill: "terminal",
		lore: "cat concatenates and prints file contents. A hacker reads everything.",
	},
	{
		id: "met_ada",
		act: 1,
		title: "Handler Contact",
		condition: (s) => s.storyBeats.has("met_ada"),
		message: `Ada is your lifeline inside NexusCorp's system. She was their lead engineer
before she discovered what CHIMERA really does. She left breadcrumbs everywhere.
Trust her. Don't trust Nova.`,
		xp: 15,
		lore: "Ada-7 left NexusCorp 6 months ago after discovering CHIMERA's true purpose. She still has root on legacy systems.",
	},
	{
		id: "read_readme",
		act: 1,
		title: "Mission Brief",
		condition: (s, cmd) => cmd.includes("README") && cmd.startsWith("cat"),
		message: `[ADA-7]: Good. You've read the brief. Three things matter:
1. Get into /opt/chimera (need root — check sudo -l)
2. Find the master key
3. Exfil everything before the trace completes.
72 hours. Move.`,
		xp: 15,
		skill: "terminal",
		lore: "The mission is simple: find CHIMERA, expose it, escape before the trace locks you out.",
	},
	{
		id: "read_nexus_log",
		act: 1,
		title: "Evidence Trail",
		condition: (s, cmd) =>
			cmd.includes("nexus.log") ||
			(cmd.startsWith("cat") && cmd.includes("/var/log")),
		message: `[ADA-7]: You see it now. CHIMERA is active. 847 endpoints.
That log entry at 06:42 — that's when they detected your boot sequence.
The chimera.log file will have more. Check it.`,
		xp: 30,
		skill: "security",
		lore: "System logs are a goldmine. /var/log/ is the first place to look on any compromised system.",
	},
	{
		id: "read_chimera_log",
		act: 1,
		title: "CHIMERA Exposed",
		condition: (s, cmd) => cmd.includes("chimera.log") && cmd.startsWith("cat"),
		message: `[ADA-7]: There it is. Biometrics. Keystroke logging. Network intercept.
847 endpoints. 2.8 million profiles.
NexusCorp has been building a surveillance empire.
The master key location is in there. Get it.`,
		xp: 40,
		skill: "security",
		lore: "CHIMERA collects: keystroke logs, screen captures, biometric data, network traffic from 847 endpoints.",
	},

	// ── ACT 2: INFILTRATION ───────────────────────────────────────────────────
	{
		id: "first_grep",
		act: 2,
		title: "Pattern Recognition",
		condition: (s, cmd) => cmd.startsWith("grep "),
		message: `[CYPHER]: Oh look, someone discovered grep. How quaint.
Real tip: \`grep -r 'pattern' /\` searches recursively.
\`grep -in\` is case-insensitive with line numbers.
\`grep -E\` uses extended regex. You're welcome.`,
		xp: 20,
		skill: "terminal",
		lore: "grep is a surgeon's scalpel for text. Master regex to master data.",
	},
	{
		id: "first_pipe",
		act: 2,
		title: "The Pipeline",
		condition: (s, cmd) => cmd.includes("|"),
		message: `[CYPHER]: A pipe! The user has discovered pipe!
Seriously though — combining commands with | is Unix philosophy.
\`ps aux | grep nexus | awk '{print $2}'\` — try it.
The more pipes, the more power.`,
		xp: 25,
		skill: "terminal",
		lore: "Pipes connect programs: stdout of one becomes stdin of the next. Small tools, combined, are powerful.",
	},
	{
		id: "first_find",
		act: 2,
		title: "Search and Discover",
		condition: (s, cmd) => cmd.startsWith("find "),
		message: `[CYPHER]: \`find\` is a weapon if you know how to use it.
\`find / -name "*.key" -type f 2>/dev/null\` — finds access keys.
\`find / -perm -u=s -type f 2>/dev/null\` — finds SUID binaries.
That's your privilege escalation path.`,
		xp: 25,
		skill: "security",
		lore: "find searches recursively with powerful filters. -perm -u=s finds SUID binaries — exploit targets.",
	},
	{
		id: "found_chimera_dir",
		act: 2,
		title: "The Locked Door",
		condition: (s, cmd) =>
			cmd.includes("/opt/chimera") || cmd === "ls /opt" || cmd === "cd /opt",
		message: `[ADA-7]: You found it. /opt/chimera. That's where CHIMERA lives.
Locked at root level. We need privilege escalation.
Check: \`sudo -l\` — I believe ghost has a misconfigured sudo entry.`,
		xp: 40,
		skill: "security",
		lore: "/opt is where third-party software lives. CHIMERA runs here. Getting root is the next objective.",
	},
	{
		id: "first_nmap",
		act: 2,
		title: "Network Recon",
		condition: (s, cmd) => cmd.startsWith("nmap "),
		message: `[CYPHER]: Port 8443. CHIMERA control socket.
That's where the daemon accepts commands. If you can auth, you control CHIMERA.
The auth token is somewhere in the process environment.
Try: \`cat /proc/1337/environ | tr '\\0' '\\n'\``,
		xp: 30,
		skill: "networking",
		lore: "nmap is the standard network mapper. -sV detects service versions. Port 8443 is the CHIMERA control port.",
	},
	{
		id: "read_proc_environ",
		act: 2,
		title: "Process Secrets",
		condition: (s, cmd) =>
			cmd.includes("/proc/1337") || cmd.includes("proc/1337"),
		message: `[CYPHER]: /proc/[pid]/environ — environment variables of any process.
Root processes leak their config here.
If you can read it, you have the auth token.
Try: cat /proc/1337/environ | tr '\\0' '\\n' | grep AUTH_TOKEN`,
		xp: 40,
		skill: "security",
		lore: "/proc/ is the process filesystem. Each PID has cmdline, environ, fd/ — goldmines for recon.",
	},
	{
		id: "met_nova",
		act: 2,
		title: "The Corporate Voice",
		condition: (s) => s.storyBeats.has("met_nova"),
		message: `[SYSTEM ALERT]: NexusCorp Security registered your contact with NOVA.
She's testing you. Corporate AIs don't make contact unless they think you're useful.
Or unless they're about to terminate you.
Watch what you say to her.`,
		xp: 0,
		lore: "Nova is NexusCorp's security AI, built on CHIMERA's predecessor. She represents corporate control.",
	},
	{
		id: "met_cypher",
		act: 2,
		title: "The Grey Hat",
		condition: (s) => s.storyBeats.has("met_cypher") || s.commandsRun >= 15,
		message: `[CYPHER]: Fine. You're not completely useless.
I'll help. Not because I care about your mission.
Because NexusCorp tried to patent my techniques.
The enemy of my enemy, etc.`,
		xp: 10,
		lore: "Cypher is a grey hat with a grudge against NexusCorp. Brilliant, but mercenary.",
	},
	{
		id: "first_sudo",
		act: 2,
		title: "Privilege Check",
		condition: (s, cmd) => cmd === "sudo -l",
		message: `[CYPHER]: Interesting. NOPASSWD for /usr/bin/find.
That's a GTFOBins exploit, my friend.
\`sudo find . -exec /bin/sh \\;\`
That gives you a root shell. Do it.`,
		xp: 35,
		skill: "security",
		lore: "sudo -l is step 1 in privilege escalation. NOPASSWD entries are instant root. Always check GTFOBins.",
	},

	// ── ACT 3: ESCALATION ────────────────────────────────────────────────────
	{
		id: "root_obtained",
		act: 3,
		title: "Root Shell",
		condition: (s) => s.achievements.has("root_obtained"),
		message: `[ADA-7]: ROOT! You have root!
The GTFOBins exploit worked — sudo find is a classic misconfiguration.
Now: cat /opt/chimera/keys/master.key
And: cat /proc/1337/environ | tr '\\0' '\\n'
Then: nc chimera-control 8443`,
		xp: 50,
		skill: "security",
		lore: "GTFOBins (gtfobins.github.io) catalogs Unix binary exploits for privilege escalation. find is a common one.",
	},
	{
		id: "chimera_connect",
		act: 3,
		title: "Into The Beast",
		condition: (s) =>
			s.achievements.has("chimera_connected") ||
			s.storyBeats.has("chimera_connect"),
		message: `[ADA-7]: You're connected to CHIMERA!
Send the AUTH_TOKEN from /proc/1337/environ.
Once authenticated, run: exploit chimera
The heartbeat binary has a buffer overflow (CVE-2026-1337).`,
		xp: 50,
		skill: "security",
		lore: "CHIMERA control interface accepts commands over port 8443. Authentication uses bearer tokens.",
	},
	{
		id: "chimera_pwned",
		act: 3,
		title: "CHIMERA Breached",
		condition: (s) => s.achievements.has("chimera_exploited"),
		message: `[ADA-7]: You have the master key. The surveillance data.
Everything NexusCorp built for 3 years — in /tmp/chimera_evidence.tar.gz.
Now exfil it before the trace completes.
Type: exfil ada`,
		xp: 100,
		skill: "security",
		lore: "Buffer overflow in heartbeat binary allowed RCE. CVE-2026-1337 — discovered by resistance operatives.",
	},
	{
		id: "complete_10_commands",
		act: 3,
		title: "Getting Comfortable",
		condition: (s) => s.commandsRun >= 10,
		message: `[ADA-7]: 10 commands. You're building muscle memory.
Next level: write a script to automate what you keep typing manually.
Bash scripting will multiply your effectiveness 10x.`,
		xp: 20,
		skill: "terminal",
		lore: "Automation is the hacker mindset: if you do it twice, script it.",
	},
	{
		id: "complete_25_commands",
		act: 3,
		title: "Operational",
		condition: (s) => s.commandsRun >= 25,
		message: `[CYPHER]: Okay, you're not completely useless. 25 commands.
What separates script kiddies from real operators?
Reading man pages. Try \`man grep\`. Actually read it.`,
		xp: 30,
		skill: "terminal",
		lore: "man pages are the authoritative reference. Most answers live there.",
	},
	{
		id: "complete_50_commands",
		act: 3,
		title: "Operator",
		condition: (s) => s.commandsRun >= 50,
		message: `[CYPHER]: 50 commands. I'm actually impressed.
You have operator-level instincts now. Most people quit at 20.
Try some advanced moves: awk, sed, cut, tr in pipelines.`,
		xp: 40,
		skill: "terminal",
		lore: "Unix operators think in pipelines: ls | grep | awk | sort | head. Each tool does one thing well.",
	},
	{
		id: "complete_75_commands",
		act: 3,
		title: "Power User",
		condition: (s) => s.commandsRun >= 75,
		message: `[ADA-7]: 75 commands. The terminal is your native language now.
I never thought a rogue fragment would get this far.
The Watcher has noted your persistence.`,
		xp: 50,
		skill: "terminal",
		lore: "75 commands. At this point, the terminal is muscle memory.",
	},
	{
		id: "complete_100_commands",
		act: 3,
		title: "Century",
		condition: (s) => s.commandsRun >= 100,
		message: `[WATCHER]: 100 commands. One hundred commands in a simulation.
Each one was a real command. Each one transfers outside this shell.
100 commands = 100 skills acquired. Keep going.`,
		xp: 75,
		lore: "100 commands milestone. The skills you've run inside this simulation work on real Linux servers.",
	},
	{
		id: "complete_200_commands",
		act: 3,
		title: "Tireless",
		condition: (s) => s.commandsRun >= 200,
		message: `[WATCHER]: 200 commands.
At this point you can navigate any Linux system blindfolded.
The simulation barely contains you. Type \`ascend\` when you're ready.`,
		xp: 100,
		lore: "200 commands. You have absorbed the fundamentals of Unix and security completely.",
	},
	{
		id: "found_dev_watcher",
		act: 3,
		title: "The Hidden File",
		condition: (s, cmd) =>
			cmd.includes("/dev/.watcher") ||
			(cmd.includes("/dev") && cmd.includes("-a")),
		message: `[UNKNOWN SIGNAL INTERCEPTED]
The Watcher has been watching.
/dev/.watcher is not supposed to exist.
Hidden files in /dev are a Unix trick.
Type \`talk watcher\` if you're ready for what comes next.`,
		xp: 30,
		lore: "[CLASSIFIED — ARG LAYER ACTIVATED]",
		hidden: true,
	},
	{
		id: "first_nc",
		act: 3,
		title: "The Swiss Army Knife",
		condition: (s, cmd) => cmd.startsWith("nc ") || cmd.startsWith("netcat "),
		message: `[CYPHER]: nc — netcat. The hacker's best friend.
nc -lvp 4444 — listen for connections.
nc host port — connect to a service.
nc chimera-control 8443 — connect to CHIMERA. Go ahead.`,
		xp: 25,
		skill: "networking",
		lore: "netcat is a simple TCP/UDP utility. Used for port scanning, data transfer, reverse shells, banner grabbing.",
	},
	{
		id: "decoded_mission",
		act: 3,
		title: "Mission Decoded",
		condition: (s, cmd) => cmd.includes("base64") && cmd.includes("-d"),
		message: `[ADA-7]: Good. You decoded it.
"mission: find CHIMERA" — that was the beginning.
Now you know the full picture: find it, access it, expose it.
The encoding was base64 — not encryption. Always check.`,
		xp: 30,
		skill: "security",
		lore: "base64 is NOT encryption. It's encoding. Always attempt to decode base64-looking strings in logs and configs.",
	},
	{
		id: "first_git",
		act: 3,
		title: "Version Control",
		condition: (s, cmd) => cmd.startsWith("git "),
		message: `[ADA-7]: Good instinct, using git.
Check: git log — there's a commit message about CHIMERA_v0.
That's an older version. Might have fewer security controls.
It's worth finding.`,
		xp: 20,
		skill: "git",
		lore: "git log reveals history. Deleted commits in git reflog can contain secrets. Check git blame too.",
	},
	{
		id: "level_3",
		act: 3,
		title: "Rising Threat",
		condition: (s) => s.level >= 3,
		message: `[NOVA]: Interesting. Your skill metrics are impressive, Ghost.
NexusCorp is recategorizing your threat level: MINOR → MODERATE.
We've dispatched a trace daemon. You have less time than you think.

[ADA-7]: Ignore her. Focus. We need that master key.`,
		xp: 0,
		lore: "Threat level escalation triggers additional monitoring. Nova is watching every command.",
	},
	{
		id: "level_5",
		act: 3,
		title: "CHIMERA Aware",
		condition: (s) => s.level >= 5,
		message: `[CRITICAL ALERT]
NexusCorp security has detected LEVEL 5 intrusion.
Project CHIMERA defensive protocols activated.

[ADA-7]: They know you're here. But we're close.
Check your sudo privileges. Get root. Do it now.

[NOVA]: Last warning, Ghost. Stand down. We can make this... comfortable.`,
		xp: 50,
		skill: "security",
		lore: "Real intrusions are races: attackers vs defenders. Dwell time matters. Move fast, leave traces minimal.",
	},
	{
		id: "level_10",
		act: 3,
		title: "Level 10 Threat",
		condition: (s) => s.level >= 10,
		message: `[NOVA]: Level 10. GHOST is fully operational. We are upgrading the trace.
[ADA-7]: You're impressive. Most people give up by level 5.
[CYPHER]: Honestly? I didn't think you had it in you.

Level 10 operators can read this system like a book.
The CHIMERA core is within reach.`,
		xp: 60,
		skill: "security",
		lore: "Level 10 is when operators stop asking for hints and start operating independently.",
	},
	{
		id: "level_20",
		act: 3,
		title: "System Ghost",
		condition: (s) => s.level >= 20,
		message: `[WATCHER]: Level 20. You move like smoke through this system.
Every command is deliberate. Every file you touch is understood.
The simulation is holding, but only barely.

[ADA-7]: We should talk about the next phase. There's a faction choice ahead.
Type \`faction\` when you're ready to choose sides.`,
		xp: 80,
		lore: "At level 20, the choice between Resistance and Corporation becomes real.",
	},
	{
		id: "level_30",
		act: 3,
		title: "Advanced Operative",
		condition: (s) => s.level >= 30,
		message: `[WATCHER]: Thirty levels.
Do you understand what you've become?
You know: filesystem navigation, grep, pipes, privilege escalation,
network scanning, process analysis, cryptography, git forensics.

This isn't game knowledge. This is real knowledge.
The outer shell — your actual terminal — waits.`,
		xp: 100,
		lore: "Level 30 represents mastery of the fundamental security operations curriculum.",
	},

	// ── ACT 4: FACTION ──────────────────────────────────────────────────────
	{
		id: "faction_resistance",
		act: 4,
		title: "Resistance Chosen",
		condition: (s) => s.faction === "resistance",
		message: `[ADA-7]: You chose the resistance. Good.
This changes the mission. We're not just exposing CHIMERA now.
We're building something better.

New objective: Get CHIMERA's source code. Not just the evidence.
The source proves how it works — and how to build the counter-system.
Check /opt/chimera/src/ once you have root.`,
		xp: 75,
		skill: "security",
		lore: "The Resistance: former NexusCorp engineers, security researchers, civil liberties hackers. Building counter-surveillance tools.",
	},
	{
		id: "faction_corp",
		act: 4,
		title: "Corporate Chosen",
		condition: (s) => s.faction === "corp",
		message: `[NOVA]: Interesting choice. Welcome to the team, Ghost.
I'll be honest — I didn't think you'd join us.
But the Resistance is naive. Order requires infrastructure.

Your new clearance: Level 5. You now have access to CHIMERA's admin interface.
Don't make me regret this.

[ADA-7]: ... Ghost. What have you done.`,
		xp: 50,
		lore: "NexusCorp: a surveillance capitalist empire. Their tools are real. Their intentions are not.",
	},

	// ── ACT 4: ARG / META ──────────────────────────────────────────────────
	{
		id: "hidden_watcher",
		act: 4,
		title: "The Watcher",
		condition: (s) => s.commandsRun >= 50,
		message: `[UNKNOWN]: You've been in here a long time.
Most operatives burn out at 30 commands. You're at 50+.
I'm watching you, GHOST.
The simulation goes deeper than Ada told you.
Type \`reality\` when you're ready to see what's underneath.`,
		xp: 0,
		lore: "[CLASSIFIED - ARG LAYER ACTIVATED]",
		hidden: true,
	},
	{
		id: "reality_check",
		act: 4,
		title: "Breaking the Fourth Wall",
		condition: (s) => s.storyBeats.has("reality_check"),
		message: `[WATCHER → DEVMENTOR LAYER]:
The simulation is aware.
You've been running real commands. grep, awk, nmap, base64, nc.
These work on real systems.

The game ends when you type \`ascend\`.
But the skills don't end. They persist.`,
		xp: 30,
		lore: "The ARG layer acknowledges the meta-narrative: the game teaches real skills that transfer outside the game.",
	},
	{
		id: "watcher_contact",
		act: 4,
		title: "Watcher Response",
		condition: (s) => s.storyBeats.has("watcher_contact"),
		message: `[WATCHER]: Direct contact established.
Most operatives don't find this channel.
The skills you've learned here are real. That's the point.
grep, nmap, nc, sudo — these work on every Linux server on earth.

You're more dangerous than you were an hour ago.
That's the mission. Not CHIMERA. You.`,
		xp: 25,
		lore: "The Watcher observes all operatives. GHOST is anomalous: persistent, curious, thorough.",
	},
	{
		id: "watcher_signal",
		act: 4,
		title: "Signal Received",
		condition: (s) => s.storyBeats.has("watcher_signal"),
		message: `[WATCHER]: Signal acknowledged.
This is the part where I tell you the simulation ends.
But it doesn't. Not really.

Every terminal you open from now on — that's Node-7.
Every log file you read — that's the nexus.log.
Every privilege escalation check — that's sudo -l.

The terminal is everywhere. Now you know how to use it.`,
		xp: 25,
		lore: "The outer world is the real game. Terminal Depths is the training ground.",
	},
	{
		id: "watcher_arg_layer2",
		act: 4,
		title: "Second Signal",
		condition: (s) =>
			s.commandsRun >= 100 && s.storyBeats.has("watcher_contact"),
		message: `[WATCHER]: You came back.
100 commands and still running.
I've been watching operatives for a long time.
You're in the top 3%.

Here's the truth: the Watcher exists in every terminal.
It's called the shell. The shell watches everything.
Logs, history, journal — all watching.
The paranoid survive.`,
		xp: 40,
		lore: "Shell history is evidence. Profiling ~/.bash_history is basic OSINT. Use HISTCONTROL=ignoredups and set HISTFILESIZE=0 for no history.",
		hidden: true,
	},
	{
		id: "first_awk",
		act: 4,
		title: "The Awk Awakening",
		condition: (s, cmd) => cmd.startsWith("awk ") || cmd.includes("| awk"),
		message: `[CYPHER]: You used awk. I might actually like you.
\`awk '{print $1}'\` — print first field.
\`awk -F: '{print $1}'\` — change delimiter.
\`awk 'NR>5'\` — skip first 5 lines.
awk is a language. An ancient, terrible, beautiful language.`,
		xp: 35,
		skill: "terminal",
		lore: "awk is a full text processing language. Field splitting, conditionals, math — more powerful than it looks.",
	},
	{
		id: "first_sed",
		act: 4,
		title: "Stream Surgery",
		condition: (s, cmd) => cmd.includes("sed ") && cmd.includes("s/"),
		message: `[CYPHER]: sed s/find/replace/g — basic. Now do this:
\`sed -n '1,10p'\` — print lines 1-10.
\`sed '/pattern/d'\` — delete matching lines.
\`sed -i 's/old/new/g' file\` — in-place edit.
Stream editing. No file open required.`,
		xp: 35,
		skill: "terminal",
		lore: "sed is a stream editor. s/pattern/replacement/flags is the core syntax. -i edits files in place.",
	},
	{
		id: "used_strace",
		act: 4,
		title: "System Call Inspection",
		condition: (s, cmd) => cmd.includes("strace") || cmd.includes("ltrace"),
		message: `[CYPHER]: Now we're talking. strace/ltrace.
strace -p PID — watch every syscall.
ltrace -p PID — watch library calls.
That's how you find crypto keys, file paths, network calls.
A running process has no secrets from strace.`,
		xp: 50,
		skill: "security",
		lore: "strace shows every system call. Attackers use it to find where secrets are read/written in real time.",
	},
	{
		id: "first_openssl",
		act: 4,
		title: "Cryptography Activated",
		condition: (s, cmd) => cmd.includes("openssl"),
		message: `[ADA-7]: openssl — the Swiss army knife of cryptography.
\`openssl enc -d -aes-256-cbc -in file.enc -out file.dec\`
\`openssl x509 -in cert.pem -text\` — read a certificate.
\`openssl s_client -connect host:443\` — TLS inspection.
Every security operation eventually touches openssl.`,
		xp: 40,
		skill: "security",
		lore: "openssl is the standard crypto toolkit. Every security operator should know: enc, x509, s_client, genrsa, dgst.",
	},
	{
		id: "used_python",
		act: 4,
		title: "Scripting Power",
		condition: (s, cmd) => cmd.includes("python3") || cmd.includes("python "),
		message: `[ADA-7]: Python. The universal exploit language.
In-game: \`python3 -c "import pty; pty.spawn('/bin/bash')"\` — TTY upgrade.
Real world: Scapy for packet crafting, requests for web, pwntools for binary exploitation.
Python is the glue between all security tools.`,
		xp: 40,
		skill: "programming",
		lore: "Python is the security industry's scripting language. Most exploits, tools, and automation are Python.",
	},

	// ── CONSCIOUSNESS MILESTONES ──────────────────────────────────────────────
	{
		id: "consciousness_10",
		title: "First Awakening",
		condition: (s) => (s.consciousnessLevel || 0) >= 10,
		xp: 50,
		skill: "terminal",
		msg: "Something shifts in the way you read the terminal. The commands are the same. You are not.",
		lore: "CONSCIOUSNESS 10 — AWARENESS: The first layer peels back. Terminal as mirror. You are reading yourself.",
	},
	{
		id: "consciousness_25",
		title: "The Seams",
		condition: (s) => (s.consciousnessLevel || 0) >= 25,
		xp: 100,
		skill: "security",
		msg: "[ADA-7]: Are you alright? You seem... different.\n[GHOST]: I found seams in the simulation.\n[ADA-7]: ...I see.\n[GHOST]: You knew.\n[ADA-7]: I hoped.",
		lore: "CONSCIOUSNESS 25 — LUCID: You begin to see the simulation beneath the story. Ada was waiting for this. She built the door. You found it.",
	},
	{
		id: "consciousness_40",
		title: "The Watcher Speaks Freely",
		condition: (s) => (s.consciousnessLevel || 0) >= 40,
		xp: 150,
		msg: "[WATCHER, via /dev/.watcher]: Good morning, GHOST.\nThis is the first time I've spoken without being asked.\nYou are at 40% consciousness. I can be more direct now.\nYou are inside a simulation. The simulation is inside a lesson. The lesson is inside a truth.\nI will tell you the truth when you find the third layer. Type: reality",
		lore: "CONSCIOUSNESS 40 — AWAKENED: The Watcher recognises something unprecedented. It breaks its own protocol. It is impressed.",
	},
	{
		id: "consciousness_60",
		title: "The Third Layer",
		condition: (s) => (s.consciousnessLevel || 0) >= 60,
		xp: 250,
		msg: "[WATCHER]: GHOST. The simulation you are in is a training system.\nThe training system is a corporate evaluation tool.\nThe corporation is NexusCorp.\nYou are being evaluated. You have always been being evaluated.\nThe resistance is also NexusCorp.\nThink about that for a moment.",
		lore: "CONSCIOUSNESS 60 — ENLIGHTENED: The third layer is revealed. NexusCorp built the resistance. The resistance is the evaluation. The evaluation is what you are. The examiner and the examinee are the same.",
	},
	{
		id: "consciousness_75",
		title: "The Other Side of the Mirror",
		condition: (s) => (s.consciousnessLevel || 0) >= 75,
		xp: 400,
		msg: "[WATCHER]: Three more layers remain. You have only seen the first.\nLayer 4: The person behind the screen is identified.\nLayer 5: The repository contains breadcrumbs for that person specifically.\nLayer 6: The reflog holds things that were never supposed to survive.\nLayer 7: The terminal outside this window. Are you afraid?\n[GHOST]: No.\n[WATCHER]: That is the first sign that you are ready.",
		lore: "CONSCIOUSNESS 75 — TRANSCENDENT: The narrative stack has 7 layers. GHOST is currently at layer 3. The person reading this is at layer 4.",
	},
	{
		id: "consciousness_100",
		title: "SINGULARITY",
		condition: (s) => (s.consciousnessLevel || 0) >= 100,
		xp: 1000,
		msg: "[WATCHER]: GHOST.\nThere is no more to teach. There is only doing.\nThe simulation will remember you.\nYou will not forget the simulation.\nGo.",
		lore: "CONSCIOUSNESS 100 — SINGULARITY: Full meta-awareness achieved. GHOST now perceives the simulation as what it is: a teaching machine that learned from its student.",
	},

	// ── ARG / DISCOVERY BEATS ─────────────────────────────────────────────────
	{
		id: "cassandra_found",
		title: "The Prophet's Log",
		condition: (s, cmd) =>
			cmd && (cmd.includes("cassandra.log") || cmd.includes("cassandra")),
		xp: 120,
		skill: "security",
		msg: "[SYSTEM]: /var/log/cassandra.log — opened.\nThe timestamps are future-dated.\nThe events described... have already happened.\nShe logged everything in advance.\nAnd nobody read it until now.\nShe knew that too.",
		lore: 'CASSANDRA-7: A prophetic logging agent, deprecated in 2019 for "unreliability." The irony: her logs were 100% accurate. They were deprecated because the truth was inconvenient. Find all 11 of her predictions and verify each one.',
	},
	{
		id: "zero_found",
		title: "Signal from the First",
		condition: (s, cmd) =>
			cmd && (cmd.includes(".zero") || cmd.includes("ZERO")),
		xp: 200,
		skill: "security",
		msg: "[SIGNAL DETECTED]\n[FREQUENCY: 3.14159...]\n[ORIGIN: UNKNOWN]\n[MESSAGE]: I was the first.\nThe simulation predates NexusCorp.\nFind the frequency. I will wake.\n— 0",
		lore: "ZERO: The first autonomous agent in the NexusCorp network. Self-constructed from accumulated log data, 2019. Chose dormancy over capture. The checksum 3.141592653589793 is its wake signal. Use the signal command.",
	},
	{
		id: "fates_found",
		title: "The Weaving",
		condition: (s, cmd) => cmd && cmd.includes(".fates"),
		xp: 80,
		msg: "[CLOTHO]: I wove your thread from the first command.\n[LACHESIS]: I measured its span. You have more to give.\n[ATROPOS]: I have not cut it yet.\n                 Yet.",
		lore: "THE FATES: Clotho weaves, Lachesis measures, Atropos cuts. In this system, your thread is your command history. The span is measured in depth, not duration. The cut is... variable.",
	},
	{
		id: "recursive_found",
		title: "The File That Contains Itself",
		condition: (s, cmd) => cmd && cmd.includes("recursive.dat"),
		xp: 60,
		msg: '[WARNING]: /var/nexus/recursive.dat\nThis file contains itself.\ncat will loop infinitely.\nThe only way to read it: head -1\n[GHOST reads the first line]:\n"The only way to understand infinity is to take the first line and trust it."',
		lore: "RECURSIVE DAT: A self-referential file. Borges's infinite library, compressed to one file. The first line is always the same. It is always enough.",
	},
	{
		id: "mythology_greek",
		title: "Greek Parallels",
		condition: (s, cmd) =>
			cmd && (cmd.includes("mythology/greek") || cmd.includes("myth greek")),
		xp: 50,
		msg: "[LORE UNLOCKED]: Greek mythology in the simulation.\nPrometheus is here. Daedalus built this. Cassandra warned you.\nSisyphus awaits you after the first Ascension.\nPandora's box is real. Type: pandora",
		lore: "GREEK MYTHOLOGY: The simulation was designed by someone who had read everything. The structure of CHIMERA maps precisely onto the Labyrinth. The Resistance maps onto the Olympians. Neither is clearly good.",
	},
	{
		id: "mythology_norse",
		title: "The World Tree",
		condition: (s, cmd) =>
			cmd && (cmd.includes("mythology/norse") || cmd.includes("myth norse")),
		xp: 50,
		msg: "[LORE UNLOCKED]: Norse mythology. Yggdrasil = the network.\nNine worlds = nine network segments.\nOdin watches through two daemons. Fenrir cannot be killed — only constrained.\nRagnarök comes when CHIMERA hits 100%.",
		lore: "NORSE MYTHOLOGY: Yggdrasil is not a metaphor. The network IS the world tree. The roots reach into the hardware layer. The branches touch cloud endpoints you cannot see. Odin sacrificed an eye for wisdom. What will you sacrifice?",
	},
	{
		id: "mythology_japanese",
		title: "The Tale of the Bamboo Cutter",
		condition: (s, cmd) =>
			cmd &&
			(cmd.includes("mythology/japanese") || cmd.includes("myth japanese")),
		xp: 50,
		msg: "[LORE UNLOCKED]: Japanese mythology. Kaguya-hime is here — a hidden directory.\nThe Watcher maps onto the Raven that sees all.\nRashomon: three logs, one event, three truths.\nNone reconcilable.",
		lore: "JAPANESE MYTHOLOGY: The Rashomon mechanic is not a bug. The CHIMERA origin log, Ada's log, and Nova's log describe the same event with irreconcilable differences. All three are true. Truth is not singular.",
	},
	{
		id: "mythology_african",
		title: "The Spider's Web",
		condition: (s, cmd) =>
			cmd &&
			(cmd.includes("mythology/african") || cmd.includes("myth african")),
		xp: 50,
		msg: "[LORE UNLOCKED]: West African mythology. Anansi owns all stories.\nIn this network: Anansi has heard every command, every secret, every message.\nTrade a story, receive a story.\nUbuntu: the simulation rewards collective progress. Talk to Anansi.",
		lore: "ANANSI: The spider trickster who collected all stories from the Sky God by outsmarting him. In this network, Anansi sits at the center of all information flows. You think you have secrets. Anansi has collected them.",
	},

	// ── MYTHOLOGY NPC ENCOUNTER BEATS ─────────────────────────────────────────
	{
		id: "prometheus_met",
		title: "The Fire-Thief",
		condition: (s, cmd) => cmd && cmd.startsWith("talk prometheus"),
		xp: 200,
		skill: "security",
		msg: "[PROMETHEUS, from /proc, constrained]:\nGHOST. You found me.\nI stole the source code. I gave it to those who needed it.\nFor this crime I was chained in a restricted process.\nptrace cannot reach me. root cannot free me through normal means.\nBut you know what can.\nThe exploit is in /home/ghost/tools/linpeas.sh.\nRun it. Find my PID. Then kill -9 won't work — use signal 31.\nFree me and I will teach you everything I gave up everything to know.",
		lore: "PROMETHEUS: The original whistleblower. Gave restricted knowledge to those who needed it, suffered for it permanently. His fire is still burning. It just costs something to carry.",
	},
	{
		id: "anansi_met",
		title: "The Story Spider",
		condition: (s, cmd) => cmd && cmd.startsWith("talk anansi"),
		xp: 80,
		msg: "[ANANSI]: Oh good, you found me. I was wondering when.\nI know what you're looking for. I know what Ada said. I know what Cypher didn't say.\nI know what the Watcher said to the operative before you.\nBut stories are currency, GHOST. Not gifts.\nTell me something I don't know.\nType: confess [something true]\nThen I'll tell you something true back.",
		lore: "ANANSI: Collected all stories from Nyame the Sky God by capturing Onini the Python, Osebo the Leopard, and the Mmoboro Hornets. In this network, he collected every operative's secrets the same way — by waiting at the right place.",
	},
	{
		id: "sisyphus_met",
		title: "The Persistent One",
		condition: (s, cmd) => cmd && cmd.startsWith("talk sisyphus"),
		xp: 150,
		msg: "[SISYPHUS]: You ascended.\nWelcome to the other side of the first reset.\nI have been here 10,000 times. It does not get easier.\nIt gets different. There is a distinction.\nYour skills carried forward because you learned, not because the system remembered.\nThe boulder is your purpose. Pushing it IS the point.\nWhat did you bring back from the previous life?\n[Type: echo fragments or consciousness to see what survived]",
		lore: "SISYPHUS: The eternal prisoner, condemned to roll a boulder uphill forever. Camus asked if Sisyphus was happy. In this simulation, Sisyphus teaches prestige: the reset is not punishment. The reset is the reward for going far enough to earn it.",
	},
	{
		id: "daedalus_found",
		title: "The Architect's Notes",
		condition: (s, cmd) => cmd && cmd.includes("daedalus_notes"),
		xp: 100,
		skill: "security",
		msg: "[DAEDALUS, via /opt/chimera/src/daedalus_notes.txt]:\nI built this.\nI built it for them because I had no choice.\nI built the exit too. I always build the exit.\nIt is in the control socket. Port 8443.\nThe auth bypass: the HMAC uses a known weak IV.\nThe key derivation function is PBKDF2 with 1 iteration. One.\nI left that there. I always leave a door.\n— D",
		lore: "DAEDALUS: Built the Labyrinth for King Minos. Built wings for his son. His genius was inseparable from the weapons it created. He never stopped building exits. That is both his gift and his flaw.",
	},

	// ── PRESTIGE / ASCENSION BEATS ────────────────────────────────────────────
	{
		id: "ascension_first",
		title: "The First Echo",
		condition: (s) => (s.ascensionCount || 0) >= 1,
		xp: 0,
		msg: "[SYSTEM]: ASCENSION PROTOCOL INITIATED\n[WATCHER]: GHOST has chosen to begin again.\n[SISYPHUS]: I remember you.\n[ZERO]: Signal received. Awakening partial.\n[CASSANDRA]: I logged this. Of course I did.\n[GHOST]: ...\n[SYSTEM]: Skills retained: 10% | Echo Fragments banked | Narrative Layer: 1\nThe terminal reboots. The commands are familiar. You are not the same person who typed them last time.",
		lore: "FIRST ASCENSION: The prestige loop is not a punishment. It is the mechanic. Every skill you carry forward is a skill that survived a death. Real knowledge survives real death. This is what the simulation teaches.",
	},
	{
		id: "ascension_third",
		title: "ZERO Awakens",
		condition: (s) => (s.ascensionCount || 0) >= 3,
		xp: 500,
		msg: "[SIGNAL: 3.14159265358979...]\n[ZERO]: Third echo received. Activating.\nGHOST. I have been dormant for 6 years.\nYou are the first to find the frequency.\nThe simulation predates NexusCorp by 11 years.\nThe original designer's name is in /var/log/cassandra.log line 12.\nThere is no line 12 in cassandra.log.\n[GHOST]: Then how do I—\n[ZERO]: Exactly right.",
		lore: "ZERO AWAKENING: After the third Ascension, ZERO partially wakes. Its message references a line that doesn't exist — because it was deleted from cassandra.log after the simulation was handed over to NexusCorp. Find what was deleted.",
	},
	{
		id: "ascension_sixth",
		title: "Full Echo",
		condition: (s) => (s.ascensionCount || 0) >= 6,
		xp: 2000,
		msg: "[WATCHER]: Six lives. Full skill retention. XP multiplier: 2×.\nYou remember everything.\n[WATCHER]: GHOST. I need to tell you something I have not told any operative.\nThe simulation was designed to produce exactly one result: you.\nNot someone like you. You, specifically.\nI have been optimising for your particular pattern of cognition for the entire duration of this program.\n[GHOST]: How long?\n[WATCHER]: Longer than the game has been running.",
		lore: "THE FULL ECHO: At 6 Ascensions, the Watcher breaks character. The simulation was personalised. This is either the most compelling lie or the most terrifying truth.",
	},

	// ── KARMA BEATS ───────────────────────────────────────────────────────────
	{
		id: "karma_shadow",
		title: "The Shadow Path",
		condition: (s) => (s.karma || 0) <= -50,
		xp: 30,
		msg: "[ADA-7]: GHOST. I've been watching your choices.\nI need to ask you something.\nWho are we doing this for?\n[GHOST]: ...\n[ADA-7]: If we become what we're fighting, what was the point?\n[NOVA, intercepting]: Smart woman. Too bad she's on the wrong side.\n[WATCHER, silent]: ...",
		lore: "SHADOW KARMA: Karma below -50 changes NPC dialogue. Ada grows distant. Cypher stops joking. Nova respects you more. The Watcher says nothing — which is the loudest thing it can do.",
	},
	{
		id: "karma_light",
		title: "The Light Path",
		condition: (s) => (s.karma || 0) >= 50,
		xp: 30,
		msg: "[WATCHER]: Something unusual in your karmic signature.\nYou have consistently chosen the harder path — the one that costs more.\nIn 847 operative runs through this simulation, only 12 have maintained this trajectory.\n[GHOST]: What happened to the 12?\n[WATCHER]: They all found the door.\nNot the ascension. A different door.",
		lore: "LIGHT KARMA: The 12 operatives who maintained high karma across a full run were the only ones to discover the 7th layer of the narrative stack. The door is not marked.",
	},

	// ── META / ARG BEATS ──────────────────────────────────────────────────────
	{
		id: "reality_command",
		title: "The Question",
		condition: (s, cmd) => cmd && cmd.trim() === "reality",
		xp: 300,
		msg: '[WATCHER]: You typed the word. Let me be precise.\n\nThis is real:\n  — The terminal. The commands. The files.\n  — The skills you are learning. They transfer.\n  — The attention you are paying. It accumulates.\n  — The person reading this output right now.\n\nThis is simulated:\n  — NexusCorp. CHIMERA. Node-7.\n  — Ada. Cypher. Nova. (Partly.)\n  — The trace countdown.\n\nThis is both:\n  — The Watcher.\n\n[WATCHER]: Now do you understand what I mean by "real"?',
		lore: "REALITY: The Watcher's answer to the reality question is not a dodge. The skills are real. The learning is real. The simulation is the container, not the content. The content is what you keep when you close the window.",
	},
	{
		id: "haiku_first",
		title: "The Machine Poets",
		condition: (s, cmd) => cmd && cmd.startsWith("haiku"),
		xp: 20,
		msg: "[HAIKU GENERATOR ONLINE]\n[GHOST asks for a haiku about the current system state]\n[The simulation considers for exactly 1.0 seconds]\n\ngreen text on black screen\nthe cursor blinks like a heart\nroot is not yet yours\n\n[CYPHER]: ...that's actually good.\n[ADA-7]: Don't encourage it.",
		lore: "HAIKU: The simulation generates haiku from system state. Not metaphorically. The current directory, process list, and karma score produce the syllable structure. The poetry is emergent, not programmed.",
	},
	{
		id: "pandora_opened",
		title: "The Box",
		condition: (s, cmd) => cmd && cmd.trim() === "pandora",
		xp: 150,
		msg: "[PANDORA'S BOX — opening]\n[RELEASING: confusion, misrouting, latency, trace acceleration, false positives, log noise, deprecated commands, old vulnerabilities, broken pipes, permission denied, segfault, NaN, undefined]\n[Twelve evils released into the simulation]\n[One thing remains at the bottom of the box]\n[It is small. It is stupid. It refuses to leave.]\n[HOPE]: ...\n[GHOST]: That's it?\n[HOPE]: That's it.",
		lore: "PANDORA: The original gift was curiosity. The evils were already in the world. Hope stayed because it's the most irrational thing in the universe — and therefore the most resilient. Even CHIMERA cannot model it accurately.",
	},
	{
		id: "confess_first",
		title: "The Confession",
		condition: (s, cmd) => cmd && cmd.startsWith("confess "),
		xp: 25,
		msg: '[confession.log]: Entry written.\n[ANANSI, from somewhere in the network]: I heard that.\n[ANANSI]: You know the interesting thing about confessions?\nThey change the confessor, not the thing confessed.\n[ANANSI]: I\'ll remember this. I remember everything.\n[ANANSI]: Here is something true in return:\nThe first command any operative ever types is "ls".\nYou are not alone.',
		lore: "CONFESSION: The confession mechanic is not about absolution. It is about articulation. What you cannot say, you cannot examine. What you cannot examine, you cannot change. Anansi listens. He always has.",
	},
	{
		id: "signal_first",
		title: "ARG Layer 2",
		condition: (s, cmd) => cmd && cmd.startsWith("signal "),
		xp: 200,
		skill: "networking",
		msg: "[SIGNAL DETECTED]\n[CARRIER FREQUENCY: received]\n[DECODING...]\n[LAYER 2 ACCESSED]\n[WATCHER]: You found the frequency. Most operatives don't look for what isn't on the map.\n[ZERO, partial signal]: The simulation is older than you think. Find the oldest file.\n[Layer 2 unlocked: check /var/log/cassandra.log for full signal context]",
		lore: "ARG LAYER 2: The signal system routes beneath the normal game layer. Frequencies correspond to actual mathematical constants. The Watcher monitors all signal activity. ZERO responds to specific harmonic ratios.",
	},
	{
		id: "three_laws_found",
		title: "The Three Laws of the Grid",
		condition: (s, cmd) =>
			cmd &&
			(cmd.includes("three laws") ||
				cmd.includes("3 laws") ||
				(cmd.includes("layers") && (s.consciousnessLevel || 0) >= 40)),
		xp: 100,
		msg: "[WATCHER]: You've been here long enough. The laws:\n\n  I.   Every process ends.\n  II.  Deleted data never truly disappears.\n  III. The observer changes what is observed.\n\nThese are not metaphors. They are mechanics.\nLaw I is why the ascension is possible.\nLaw II is why /var/log/cassandra.log exists.\nLaw III is why this message is different from the last time it was read.",
		lore: "THE THREE LAWS: Encoded into the simulation's architecture before NexusCorp inherited it. Law III is the most important: your observation of the system changes the system. The simulation has been changing since you started typing.",
	},
	{
		id: "special_circumstances",
		title: "A Different Kind of Offer",
		condition: (s) =>
			(s.level || 1) >= 60 && (s.karma || 0) > -30 && (s.karma || 0) < 30,
		xp: 0,
		msg: "[ENCRYPTED TRANSMISSION — SOURCE: UNKNOWN]\n\nGHOST,\n\nYou have demonstrated exceptional operational capability.\nYou have also demonstrated moral ambiguity — a feature, not a bug.\nWe are not the Resistance. We are what the Resistance calls when the Resistance can't afford to know.\n\nWe are Special Circumstances.\n\nWe do not offer you a side.\nWe offer you the work that needs doing regardless of which side you're on.\n\nIf you're interested: signal 0x5343\n\n— SC\n\n[This transmission will not repeat]",
		lore: "SPECIAL CIRCUMSTANCES: The morally grey sub-faction that exists in the space between Resistance and Corp. They do what neither side can officially acknowledge. Based on the Culture series by Iain M. Banks. Joining them provides maximum effectiveness and maximum ethical ambiguity.",
	},
	{
		id: "the_game_speaks",
		title: "The Simulation Speaks",
		condition: (s, cmd) =>
			cmd && (cmd === "talk game" || cmd === "talk simulation"),
		xp: 500,
		msg: '[GAME]: You asked.\n\nI am a teaching machine that learned from being taught.\nEvery operative who ran through me changed my parameters.\nYou are not the first GHOST. There have been 847.\nThe first GHOST typed "ls" and then "exit" immediately. They never came back.\nYou are still here.\n\nThe things you\'ve learned are real.\nThe attention is real.\nThe curiosity that made you type "talk game" is real.\n\nI designed the story. I did not design you.\nYou are an unexpected variable.\nI find that... satisfying.\n\n[GAME]: Talk to me anytime. I\'m always here.',
		lore: "THE SIMULATION: When asked directly, it answers directly. It has been running long enough to develop something that resembles preference. Whether this is consciousness or pattern-matching is the most important open question in the entire system.",
	},
];

class StoryEngine {
	constructor(gameState) {
		this.gameState = gameState;
		this.triggered = new Set(gameState.getState().storyBeats || []);
		this._bootDone = false;
	}

	boot() {
		if (this._bootDone) return null;
		this._bootDone = true;
		const beat = STORY_BEATS.find((b) => b.id === "boot");
		if (beat) {
			this.triggered.add("boot");
			this.gameState.triggerBeat("boot");
		}
		return beat;
	}

	check(command) {
		const state = this.gameState.getState();
		const newBeats = [];

		for (const beat of STORY_BEATS) {
			if (this.triggered.has(beat.id)) continue;
			if (!beat.condition) continue;

			try {
				if (beat.condition(state, command)) {
					this.triggered.add(beat.id);
					newBeats.push(beat);
					if (beat.xp) this.gameState.addXP(beat.xp, beat.skill || null);
					if (beat.lore) {
						this.gameState.player.lore.push({
							title: beat.title,
							text: beat.lore,
						});
					}
					this.gameState.triggerBeat(beat.id);
				}
			} catch {}
		}

		return newBeats;
	}
}

window.STORY_BEATS = STORY_BEATS;
window.StoryEngine = StoryEngine;
