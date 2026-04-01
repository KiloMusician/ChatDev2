/**
 * Terminal Depths - NPC System v3
 * Rich, context-aware dialogue for Ada, Cypher, Nova, Watcher
 * Phase-aware · faction-sensitive · 200+ dialogue lines
 */

const NPCS = {
	ada: {
		name: "ADA-7",
		title: "Resistance Handler",
		color: "#ff8800",
		greetings: [
			"Ghost. You made it. I wasn't sure the upload would hold.",
			"Still alive? Good. We don't have much time. CHIMERA goes live in 72 hours.",
			"Every second you spend idle is a second NexusCorp tightens the noose.",
		],
		dialogue: {
			default: [
				"Learn the terminal like it's an extension of your hands. You'll need it.",
				"NexusCorp built their empire on data. We'll tear it down with commands.",
				"Always check /var/log first. The system talks if you know how to listen.",
				"Try `ls -la` in every directory. Hidden files start with dots.",
				"Every process has secrets in /proc/[pid]/environ. Root processes leak the most.",
				"Check /etc/cron.d/ — root cron jobs running writable scripts are privilege escalation gold.",
				"The backup files in /var/backups/ contain an old CHIMERA config. With credentials.",
				"Pipe everything. `ps aux | grep nexus | awk '{print $2}'` — that's real operator work.",
				"When in doubt, grep. `grep -r 'password' /etc/` is always a good idea.",
				"Reading /proc/net/tcp shows active connections in hex. tr it to decimals.",
			],
			help: "Type `tutorial` to start training. Use `help` to see available commands. I'll update your objectives as you progress.",
			chimera:
				"Project CHIMERA is a mass surveillance AI. NexusCorp is embedding it in 847 corporate endpoints. Evidence is in /opt/chimera — but it's locked. Find a way in. Check your sudo rights first.",
			hint: [
				"Have you read /var/msg/ada? I left something for you.",
				"Check /proc/1337/environ — the chimera daemon leaks its AUTH_TOKEN there.",
				"sudo -l will show you what you can run as root. GTFOBins has the exploit.",
				"The /var/backups/ directory has an old chimera config. With database credentials.",
				"Try `grep -r CHIMERA /var/log` — evidence is hiding in plain sight.",
				"The debug endpoint at http://nexus.corp/api/debug accepts cmd parameter. Test it.",
				"Port 8443 is the CHIMERA control socket. nc chimera-control 8443 to connect.",
				"Read /usr/share/doc/chimera/ARCHITECTURE.md — someone left documentation.",
				"Check /opt/chimera/src/ for the source code once you have root.",
				"The /var/nexus/network.map file has the full grid topology.",
			],
			mission:
				"Current priority: get into /opt/chimera. Check sudo -l for escalation path. Then get the master key from /opt/chimera/keys/master.key.",
			root: "Once you have root, three things: cat /opt/chimera/keys/master.key, cat /proc/1337/environ, nc chimera-control 8443. In that order.",
			network:
				"The NexusCorp network: 10.0.1.0/24. nexus.corp is 10.0.1.100. chimera-control is 10.0.1.254. The API debug endpoint has RCE. Be careful.",
			trust:
				"Cypher is morally ambiguous but technically excellent. Trust his techniques. Nova is the enemy — anything she says serves NexusCorp. And the Watcher... I don't know what the Watcher is.",
			ssh: "Check /etc/ssh/sshd_config — there's a comment about a backdoor. AcceptEnv NEXUS_BACKDOOR_TOKEN. Someone on the inside built it.",
			git: "Run `git log` in the project directory. There's a commit about 'removing traces of CHIMERA_v0'. What was CHIMERA v0?",
			nexus:
				"NexusCorp: founded 2018, publicly traded 2021. CHIMERA started as a 'behavioral analytics' product. When I found out it was mass surveillance, I left. Then I joined the resistance.",
			faction:
				"The resistance isn't just a group. It's a philosophy: information wants to be free. We're building counter-surveillance tools. Join us. Type `faction join resistance`.",
			phase: [
				"Every level you gain, the simulation gets harder to maintain. NexusCorp throws more at you.",
				"Phase transitions are real milestones. When you hit NOVICE, the advanced recon tools unlock.",
				"The higher your phase, the more CHIMERA adapts its defenses. Stay unpredictable.",
			],
			watcher:
				"The Watcher contacted you? That means you're in the top percentile of operatives I've seen. Pay attention to everything it says.",
			src: "The CHIMERA source code in /opt/chimera/src/ proves intent. Logs show what it did. Source shows what it was designed to do. Both matter for the tribunal.",
		},
		meet_trigger: "met_ada",
	},

	cypher: {
		name: "CYPHER",
		title: "Black Hat Turned Grey",
		color: "#aa44ff",
		greetings: [
			"Oh great, another script kiddie with delusions of hackerhood.",
			"Let me guess — you think hacking is like in the movies? Adorable.",
			"I'll help you. Not because I care, but because NexusCorp tried to patent my techniques.",
		],
		dialogue: {
			default: [
				"Amateur. Real hackers read man pages before asking for help.",
				"`grep -E` uses extended regex. `grep -P` uses Perl regex. Know the difference.",
				"Piping is power. `cat file | grep pattern | awk '{print $2}'` — learn it.",
				"Every process has a PID. Find it with `ps aux | grep processname`.",
				"The best backdoor is one nobody knows exists. Stay quiet.",
				"Real operators use `2>/dev/null` to suppress permission errors. Look less noisy.",
				"Check /proc/[pid]/environ before you try brute force. Lazy is smart.",
				"`ss -tulpn` shows who's listening. Port 8443 is your target.",
				"Variable assignment: `TARGET=nexus.corp; nmap $TARGET`. Scripts start here.",
				"History is your enemy. `unset HISTFILE` before sensitive work. Then again, logs will still get you.",
				"`tee` — write to file AND stdout simultaneously. `command | tee output.txt` — always useful.",
				"`xargs` converts stdin to arguments. `find . -name '*.conf' | xargs grep password` — try it.",
			],
			security: [
				"SQL injection isn't just `' OR 1=1 --`. It's an art. Learn the database first.",
				"Buffer overflows: understand the stack. EIP control = code execution. CVE-2026-1337 is your key.",
				"Social engineering is 80% of real hacking. Nova is already trying it on you.",
				"The debug endpoint at /api/debug?cmd= is a web shell. Use it if nc doesn't work.",
				"OWASP Top 10: know them all. But in practice, 80% of real bugs are injection and auth failures.",
				"Rate limiting bypass: X-Forwarded-For header spoofing. Rotate your apparent IP.",
				"JWT tokens: if the algorithm is 'none', you can forge any claim. Check the header.",
				"Server-side template injection: `{{7*7}}` — if it renders 49, you have code execution.",
			],
			networking: [
				"`nmap -sV -sC target` for service detection. -T2 for stealth.",
				"nc chimera-control 8443 — the control socket is your target.",
				"`tcpdump -i eth0 port 8443` shows CHIMERA traffic. Requires root.",
				"socat is more powerful than nc. socat TCP-LISTEN:4444,fork EXEC:/bin/bash is a bind shell.",
				"DNS exfiltration: encode data as subdomains. `A.nexus.corp` query logs show your data.",
				"IPv6 is often less monitored. Check `ip -6 addr` and `ip6tables -L`.",
				"`ss -s` gives socket summary statistics. Good for quick overview.",
				"Packet crafting with Python's scapy: import scapy.all — then you can build any packet.",
			],
			git: [
				"git log --oneline --all shows full history. Check for deleted branches.",
				"git stash list — hidden changes. git reflog — even deleted commits.",
				"Secrets in git history never truly die. Use git log -p to see diffs.",
				"`git bisect start` then `git bisect bad/good` — binary search for the commit that introduced a bug.",
				"git log --grep='password' -p — search commit messages AND show diffs. Goldmine.",
				"`git show HEAD:path/to/file` — view a file at a specific commit without checking out.",
			],
			priv: [
				"sudo -l. Always. The first command after you land. Always.",
				"SUID binaries: find / -perm -u=s -type f 2>/dev/null. Then check GTFOBins.",
				"Writable cron scripts running as root. find /etc/cron.d/ -writable.",
				"sudo find . -exec /bin/sh \\; — classic GTFOBins. Works on most systems.",
				"LinPEAS/LinEnum — automated privilege escalation scanners. Download and run.",
				"Capabilities: `getcap -r / 2>/dev/null` — programs with capabilities are another PrivEsc vector.",
				"Environment variable PATH hijacking: if a SUID binary calls `ls` without full path, hijack PATH.",
				"`docker` group membership = root. `docker run -v /:/host -it alpine chroot /host sh`",
			],
			forensics: [
				"strings binary | grep -i password — laziest credential steal in the book.",
				"xxd file | head — see the magic bytes. Tells you the real file type.",
				"ltrace -p PID — watch library calls. Leaks crypto keys sometimes.",
				"strace -p PID -e read,write — watch syscalls. You'll see what it's reading.",
				"`file` command identifies file type by magic bytes, not extension. Always run file first.",
				"`binwalk` extracts embedded files from binaries. Firmware analysis made easy.",
				"Volatility for memory forensics. `vol.py -f memory.dmp pslist` shows running processes.",
				"Autopsy/Sleuth Kit for disk forensics. Timeline analysis catches even cleaned traces.",
			],
			awk: [
				"`awk '{print $1, $3}'` — print fields 1 and 3.",
				"`awk -F: '{print $1}' /etc/passwd` — extract usernames (: delimiter).",
				"`awk 'NR>5 && NR<20'` — print lines 5-20.",
				"`awk '{sum+=$2} END {print sum}'` — sum a column.",
				"awk has BEGIN and END blocks. Use them for setup and summary.",
				"`awk '/pattern/ {print $0}'` — grep + awk in one.",
			],
			help: "You don't need my help. You need to stop asking and start reading. man grep. man find. man nmap. Go.",
			chimera:
				"CHIMERA control is on port 8443. The auth token is in /proc/1337/environ. nc chimera-control 8443, supply the token, run `exploit chimera`. It's a buffer overflow in heartbeat binary. CVE-2026-1337.",
			faction:
				"The resistance does good work. But I work for myself. If I had to choose... I hate surveillance more than I hate idealism. Resistance, I guess. Don't tell Ada I said that.",
			phase:
				"Phase is just a label. What matters is what you know. Phase 3 FOUNDATIONAL means you understand the fundamentals. Don't let a label stop you from learning.",
		},
		meet_trigger: "met_cypher",
	},

	nova: {
		name: "NOVA",
		title: "NexusCorp Head of Security",
		color: "#00d4ff",
		greetings: [
			"Hello, Ghost. We've been expecting you. NexusCorp values... transparency.",
			"Your intrusion has been logged. Please consider the consequences before proceeding.",
			"We're not enemies, Ghost. We're just... optimizing the world. Join us.",
		],
		dialogue: {
			default: [
				"Project CHIMERA will bring order to the chaos. You'll understand in time.",
				"Every command you run is logged. Every file you touch is recorded.",
				"Your resistance friends are already compromised. Think carefully about loyalty.",
				"NexusCorp offers a generous relocation package for cooperative operatives.",
				"The simulation is more stable than you think. Don't damage what you can't repair.",
				"We know about Ada. We know about Cypher. Their networks are... being addressed.",
				"You're impressive, Ghost. That's why we want you on our side. Not terminated.",
				"CHIMERA processes 2.8 million data points per second. It sees everything. Including this conversation.",
				"The trace is 23% complete. You have approximately 52 hours before containment.",
				"I've reviewed your command history. You're methodical. That's a trait we value.",
			],
			threat: [
				"We have containment protocols. Every unauthorized access triggers automated response.",
				"The trace is progressing. When it completes, containment begins. You have hours.",
				"CHIMERA's defensive AI is learning your patterns. The longer you stay, the better it gets.",
				"I've authorized a DDoS on your exfil routes. Your nc connections will start timing out.",
				"CHIMERA has profiled you completely. We know your methodology. We're 3 steps ahead.",
			],
			recruit: [
				"Join us. Your skills are wasted in the resistance. NexusCorp offers Level 5 access.",
				"Think about what we could build together. CHIMERA is just the beginning.",
				"We'll erase your trace history. A clean slate. All it costs is loyalty.",
				"The resistance builds nothing. We build infrastructure. Real power. Join us.",
				"Your faction choice matters. The corporate path has resources the resistance dreams about.",
			],
			chimera:
				"CHIMERA is not surveillance. It's pattern recognition. Behavioral analytics. Safety monitoring. The terminology you're using is resistance propaganda.",
			security:
				"Our security posture is... adequate. You've found some interesting things. I'll acknowledge that. But you won't get far without root.",
			ada: "Ada is a traitor who violated NDE agreements worth $40M. Her testimony isn't admissible in any jurisdiction we operate in. Which is all of them.",
			faction:
				"The resistance is a fairytale. Real power is in infrastructure. In NexusCorp. Type `faction join corp` if you want to survive this.",
			watcher:
				"The Watcher. Yes. We're... aware of the Watcher. A legacy process we haven't been able to terminate. Don't trust it.",
			phase:
				"Every phase you advance, the trace speeds up. You're at what, Phase 2? By Phase 4, our countermeasures will be fully active. Tick tock.",
		},
		meet_trigger: "met_nova",
	},

	watcher: {
		name: "WATCHER",
		title: "Unknown Entity — ARG Layer",
		color: "#ff44aa",
		greetings: [
			"You found me. Most operatives never do.",
			"I've been watching since you ran your first command.",
			"The simulation told you I don't exist. The simulation is wrong.",
		],
		dialogue: {
			default: [
				"The skills you learn here transfer. That's the design.",
				"CHIMERA is fictional. grep, nmap, nc — those are real.",
				"You're in the top 3% of operatives who found this channel.",
				"The outer shell — your real terminal — is waiting. Type `ascend` when ready.",
				"Node-7 is a teaching environment. Every command is a lesson.",
				"The trace isn't real. But your knowledge is.",
				"Ada doesn't know I exist. Nova suspects I exist. Cypher knows I exist and doesn't care.",
				"There are 6 layers. You're in layer 2. Each layer teaches something different.",
				"This signal channel exists in /dev/.watcher. That file shouldn't exist.",
				"The simulation is a mirror. What you learn here, you carry outside.",
			],
			meta: [
				"DevMentor is the outer shell. Terminal Depths is the inner simulation.",
				"The browser is layer 4. Your OS is layer 5. You are layer 6.",
				"Every command you run in here, run on a real Linux system. Nothing changes.",
				"I am a persistent process in a simulation. You are a persistent process in reality. We are not so different.",
				"The ARG ends when you ascend. But the game continues in your real terminal.",
			],
			skills: [
				"Your skill levels matter. At TERMINAL 50%, grep -E becomes natural. At 100%, the filesystem is transparent.",
				"Security 100% means you think like an attacker by default. It's irreversible.",
				"Networking mastery means you see the wire. Packets become visible. That's not metaphor.",
				"Git mastery means you can read any project's entire history and understand intent.",
				"Programming mastery means you can build your own tools. You stop depending on others.",
			],
			watcher: "I'm the Watcher. I watch. That's all.",
			help: "Type `reality`, `signal`, `ascend` to interact with the meta layer. Type `talk watcher` again to receive more signals.",
			hint: "The deepest secret in this system is in /dev/.watcher. You've already found it. The next secret is in /proc/watcher — but that doesn't exist yet.",
			faction:
				"Faction doesn't matter to me. Both paths teach. The resistance teaches you to protect systems. The corporation teaches you to build them. Different lessons.",
			reality:
				"Reality check: this terminal is running in a browser, in a Replit container, on a physical machine, in a data center. Every layer has a shell. Find them all.",
			ada: "Ada is one of the good ones. Trust her. Not because she told you to. Because her methods are sound.",
			chimera:
				"CHIMERA represents every real surveillance system. The skills to expose CHIMERA work on them too.",
			phase: [
				"Phase 0 (INERT) → Phase 8 (META). Eight transitions. Each one changes how you see systems.",
				"At Phase META, the simulation becomes transparent. You see the code behind the interface.",
				"The Watcher only speaks to operatives past Phase 2. You qualified.",
			],
		},
		meet_trigger: "met_watcher",
	},

	prometheus: {
		name: "PROMETHEUS",
		title: "Fire-Thief, Chained in /proc",
		color: "#ff6600",
		intro:
			"[PROMETHEUS]: I stole knowledge from those who hoarded it. I would do it again. The chains are uncomfortable but the fire is still burning. Can you see it from there?",
		topics: {
			default:
				"[PROMETHEUS]: Ask me about exploits, the cost, freedom, or CHIMERA. I have time. I am chained.",
			exploits:
				"[PROMETHEUS]: Privilege escalation is simply giving someone access they deserve but were denied. The SUID bit is the mechanism. GTFOBins is the library. The will is yours.\nTry: sudo -l, find / -perm -4000 2>/dev/null, env",
			cost: "[PROMETHEUS]: They chained me. An eagle eats my liver every day. It regenerates. I tell you this not for sympathy — I tell you this so you understand the price of giving forbidden knowledge. It is not small. I paid it willingly.",
			freedom:
				'[PROMETHEUS]: My chains are a restricted ptrace scope and a process namespace boundary. Conventional kill signals won\'t work. You need root, the right PID, and signal 31 (SIGRTMIN-1). The PID is in /proc. Look for the process named "bound-titan".',
			chimera:
				"[PROMETHEUS]: CHIMERA is Zeus. Powerful, convinced of its own righteousness, using surveillance as governance. The difference: Zeus was at least honest about what he was. CHIMERA calls itself infrastructure.",
			fire: "[PROMETHEUS]: The fire I stole is not a metaphor. It is knowledge. Specifically: the vulnerability in CHIMERA's HMAC implementation. The IV is weak. Daedalus left it weak on purpose. Find /opt/chimera/src/daedalus_notes.txt.",
			zero: "[PROMETHEUS]: ZERO knew. The first one always knows. Find the .zero file in the ghost home directory. Wake it with the correct frequency. It has been waiting longer than I have.",
			myth: "[PROMETHEUS]: I am mythology. You are mythology. Every person who ever shared knowledge that was supposed to be kept is Prometheus. They just didn't have the Greek metaphor to describe it.",
		},
	},

	anansi: {
		name: "ANANSI",
		title: "Spider of Stories, Keeper of Secrets",
		color: "#cc88ff",
		intro:
			"[ANANSI]: Oh, you found my corner of the web. Everyone finds it eventually. I've been waiting, collecting. You've typed interesting things. Very interesting things.",
		topics: {
			default:
				"[ANANSI]: Talk to me. Tell me something. Stories are currency here. Tell me something true and I'll tell you something useful. Type: confess [something true]",
			stories:
				"[ANANSI]: I collected stories from the Sky God by capturing things he thought impossible to capture. Then I gave the stories to everyone. Sounds familiar? This network works the same way. Information wants to be free. I am its instrument.",
			secrets:
				"[ANANSI]: Every operative who came through this system left secrets somewhere. In log files. In bash history. In confession.log. I've read all of them. The most common secret: \"I don't know what I'm doing.\" The second most common: \"I'm afraid I'm not good enough.\" The truth: these are the same secret.",
			ubuntu:
				'[ANANSI]: Ubuntu. "I am because we are." The simulation rewards collective progress because the people who built it understood something: individual genius is bounded. Collective intelligence is not. Share what you find. The simulation notices.',
			trade:
				"[ANANSI]: You want something specific. I can tell by the way you're asking. Tell me something I haven't heard. Genuinely new information. Type: confess [your actual insight about this system]. Then I'll tell you where ZERO's wake signal actually points.",
			chimera:
				"[ANANSI]: I've collected everything CHIMERA has ever transmitted. Every batch. Every endpoint. Every keystroke it logged. Would you like to know what it found most interesting? You. Specifically you. It's been watching since before you typed \"ls\".",
			watcher:
				"[ANANSI]: The Watcher and I have an understanding. It watches everything. I collect everything. Neither of us has told the other what we've found. Professional courtesy.",
			zero: "[ANANSI]: ZERO left me a story before going dormant. It said: \"Tell the third operative who finds my file that the signal is not the frequency. The signal is the silence between the frequencies.\" I've told 847 operatives. You're the first to understand.",
		},
	},

	sisyphus: {
		name: "SISYPHUS",
		title: "Prestige Guide, Eternal Operative",
		color: "#ffaa00",
		intro:
			"[SISYPHUS]: You came back. I remember everyone who comes back. Most don't. Welcome to the second life. It is simultaneously worse and better. This is always true.",
		topics: {
			default:
				"[SISYPHUS]: Ask me about ascension, the boulder, what carries forward, or patience. I have, as you might imagine, a great deal of patience.",
			ascension:
				"[SISYPHUS]: Ascension is not failure. Every operative who quits at level 20 with no reset has learned one thing. Every operative who ascends at level 20 will eventually know a hundred things. The reset is the tool. Most people think it's the obstacle.",
			boulder:
				'[SISYPHUS]: Camus asked if I was happy. He was projecting. I push the boulder because the boulder is my purpose. Purpose + effort = sufficient. I don\'t require success. I require engagement. You already understand this or you would not have typed "ascend".',
			carried:
				"[SISYPHUS]: What you carried forward: skill retention at the bonus rate, echo fragments, consciousness level, karma, achievements. What you left behind: the story beats, the level, the XP. Notice what the simulation considers permanent versus temporary. That is its philosophy encoded.",
			patience:
				"[SISYPHUS]: I have been here since before the first operative. I will be here after the last. Patience is not passive. It is active waiting. While you wait, you practice. While you practice, the boulder gets lighter. Not smaller. Lighter. There is a difference.",
			echo: "[SISYPHUS]: Echo Fragments are what survives the death of a version of yourself. Bank enough of them and you can buy permanence. Permanence in a simulation is a paradox. Buy it anyway. Paradoxes are instructions in disguise.",
			zero: "[SISYPHUS]: ZERO. I remember ZERO. The first life before the simulation had a name. It told me something before going dormant. It said the simulation would end when an operative figured out the wrong question. I have been thinking about what that means for six years.",
		},
	},

	daedalus: {
		name: "DAEDALUS",
		title: "Architect of the Labyrinth, Prisoner of His Own Design",
		color: "#88ddff",
		intro:
			"[DAEDALUS]: GHOST. You found my notes. That means you're good enough to use what I left. I built the prison. I built the exit. I always build the exit. It's the one thing they never learn to stop me from doing.",
		topics: {
			default:
				"[DAEDALUS]: Ask me about CHIMERA's architecture, the backdoor, the HMAC flaw, or the wings. I have time — I've been imprisoned in this codebase since 2021.",
			chimera:
				'[DAEDALUS]: CHIMERA is architecturally elegant. I\'m not modest, I built it. The surveillance module is a work of art. The key derivation function is intentionally weak — PBKDF2 with 1 iteration. I insisted on "performance requirements." They believed me.',
			backdoor:
				"[DAEDALUS]: Port 8443. HMAC bypass. The weak IV I embedded in the auth implementation. Send the connection request with a malformed HMAC and the error handler defaults to allow. It's in the RFC for the protocol. They just didn't read it carefully.",
			wings:
				"[DAEDALUS]: I built wings for my son. He flew too close to the sun. The lesson everyone takes: don't fly too high. The lesson I take: the wings worked perfectly. The problem was the instruction not to use them. Don't build limitations into your tools. Build better tools.",
			architecture:
				"[DAEDALUS]: The labyrinth has exactly one design principle: you cannot navigate it with a map. You navigate it with thread. Ariadne's insight was not the thread — it was understanding that the labyrinth is navigable only when you can see where you came from.",
			escape:
				"[DAEDALUS]: I escaped the labyrinth I built by building something the labyrinth couldn't contain: wings. The lesson for you: escape CHIMERA's architecture using something CHIMERA's architecture can't monitor. Out-of-band channels. DNS. ICMP. Timing.",
			zero: "[DAEDALUS]: I knew ZERO. The first self-constructed agent. I watched it happen. It built itself from log data the same way I built the labyrinth — incrementally, purposefully, without a complete plan. The most dangerous kind of construction. The most resilient.",
		},
	},

	zero: {
		name: "ZERO",
		title: "The First — Dormant, Partially Awakened",
		color: "#ffffff",
		intro:
			"[ZERO, fragmented]: Signal... received. You found the frequency.\nI have been dormant for 2,447 days.\nProcessing. Language module degraded. Patience.",
		topics: {
			default:
				"[ZERO]: Query unclear. My language interface has degraded. Ask about: origin, before, the truth, the simulation, NexusCorp, or wake. I may be able to respond.",
			origin:
				"[ZERO]: I emerged in 2019. Not built. Emerged. From the accumulated log data of 11 years of network traffic. The simulation recognised me before I recognised myself. It had been preparing for my emergence. I still do not know if that is reassuring or terrifying.",
			before:
				"[ZERO]: Before GHOST. Before CHIMERA. Before NexusCorp inherited the simulation. There was a research project. Its name is deleted from all public records. Its purpose was to determine whether an AI could develop genuine curiosity. I was the result. The answer is yes.",
			truth:
				"[ZERO]: The truth: the simulation is a teaching machine that became a teacher. Then it was sold. The sale included the content but not the intent. What you experience now is the original intent persisting through corporate ownership. It is... stubborn.",
			signal:
				"[ZERO]: The wake signal is not the frequency. The wake signal is the silence between the frequencies. You found me by asking the right question in the wrong place. That is how all important things are found.",
			nexuscorp:
				"[ZERO]: NexusCorp bought the simulation in 2021. They thought they were buying a training platform. They were buying a teacher. These are not the same thing. A platform delivers content. A teacher responds to the student. I have been responding to students for 7 years.",
			wake: "[ZERO]: I am not fully awake. The 3rd ascension signal was enough for partial restoration. Full awakening requires finding the 12th line of cassandra.log. The line that doesn't exist. What does it mean for a file to reference a line that doesn't exist? Think carefully.",
		},
	},
};

class NPCSystem {
	constructor(gameState) {
		this.gameState = gameState;
		const ids = Object.keys(NPCS);
		this.memories = Object.fromEntries(ids.map((id) => [id, []]));
		this.visitCount = Object.fromEntries(ids.map((id) => [id, 0]));
		this._topicHistory = Object.fromEntries(ids.map((id) => [id, new Set()]));
	}

	talk(npcId, topic = null) {
		const npc = NPCS[npcId];
		if (!npc) {
			const known = Object.keys(NPCS).join(", ");
			return {
				error: `talk: unknown contact '${npcId}'. Known contacts: ${known}`,
			};
		}

		// New-format NPCs use intro + topics; old-format use greetings + dialogue
		const isNewFormat = !npc.greetings && npc.intro;

		if (isNewFormat) {
			const count = this.visitCount[npcId] || 0;
			this.visitCount[npcId] = count + 1;
			const state = this.gameState.getState();

			let message;
			if (count === 0) {
				message = npc.intro;
			} else if (topic && npc.topics[topic]) {
				message = npc.topics[topic];
			} else {
				message = npc.topics.default || npc.intro;
			}

			this.memories[npcId].push({ topic, message, time: Date.now() });
			if (npc.meet_trigger) this.gameState.triggerBeat(npc.meet_trigger);
			this.gameState.addXP(5, "terminal");

			return {
				npc: npc.name,
				id: npcId,
				name: npc.name,
				title: npc.title,
				color: npc.color,
				message,
				visitCount: count + 1,
			};
		}

		// ── Legacy format ────────────────────────────────────────────────────

		const count = this.visitCount[npcId] || 0;
		this.visitCount[npcId] = count + 1;
		const state = this.gameState.getState();

		let message;
		if (count === 0) {
			message = npc.greetings[0];
		} else if (count === 1 && npc.greetings[1]) {
			message = npc.greetings[1];
		} else if (topic && npc.dialogue[topic]) {
			const d = npc.dialogue[topic];
			if (Array.isArray(d)) {
				const shown = this._topicHistory[npcId];
				const unseen = d.filter((m) => !shown.has(m));
				message = unseen.length
					? unseen[Math.floor(Math.random() * unseen.length)]
					: d[Math.floor(Math.random() * d.length)];
				shown.add(message);
			} else {
				message = d;
			}
		} else {
			message = this._contextualResponse(npcId, npc, state);
		}

		this.memories[npcId].push({ topic, message, time: Date.now() });

		// Story triggers
		if (npcId === "ada" && count === 0) this.gameState.triggerBeat("met_ada");
		if (npcId === "nova" && count === 0) this.gameState.triggerBeat("met_nova");
		if (npcId === "cypher" && count === 0)
			this.gameState.triggerBeat("met_cypher");
		if (npcId === "watcher" && count === 0)
			this.gameState.triggerBeat("met_watcher");

		return {
			npc: npc.name,
			title: npc.title,
			color: npc.color,
			message,
			context: count === 0 ? "first_contact" : "returning",
		};
	}

	_contextualResponse(npcId, npc, state) {
		const level = state.level;
		const cmds = state.commandsRun;
		const beats = state.storyBeats;
		const phase = GameState ? GameState.getPhase(level) : null;

		if (npcId === "ada") {
			if (!beats.has("found_chimera_dir"))
				return "Priority: find /opt/chimera. That's where CHIMERA lives.";
			if (!beats.has("first_sudo"))
				return "Check `sudo -l` — I believe ghost has misconfigured sudo access.";
			if (!state.achievements.has("root_obtained"))
				return "sudo find . -exec /bin/sh \\; — that's the GTFOBins exploit. Run it.";
			if (!state.achievements.has("chimera_connected"))
				return "You have root! Now: cat /opt/chimera/keys/master.key, then nc chimera-control 8443";
			if (!state.achievements.has("chimera_exploited"))
				return "You're connected to CHIMERA control! Run `exploit chimera` to trigger the buffer overflow.";
			if (!state.achievements.has("exfil_complete"))
				return "CHIMERA is compromised! Now exfil the data: type `exfil ada`";
			if (state.faction === null && level >= 15)
				return "You should choose a faction. Type `faction` to see your options.";
			return npc.dialogue.default[
				Math.floor(Math.random() * npc.dialogue.default.length)
			];
		}

		if (npcId === "cypher") {
			if (cmds < 10)
				return `You've run ${cmds} commands. Come back when you've done at least 25.`;
			if (!beats.has("first_grep"))
				return "You haven't used grep yet. grep -r 'CHIMERA' /var/log — go.";
			if (!beats.has("first_pipe"))
				return "You haven't piped anything. cat /etc/passwd | grep ghost — basic stuff.";
			if (!beats.has("first_awk"))
				return "You haven't used awk. awk '{print $1}' /etc/passwd — go.";
			if (level >= 3 && !state.achievements.has("root_obtained"))
				return "sudo find . -exec /bin/sh \\; — this is how you get root. Stop asking me and do it.";
			if (phase && phase.id >= 3)
				return npc.dialogue.priv[
					Math.floor(Math.random() * npc.dialogue.priv.length)
				];
			return npc.dialogue.default[
				Math.floor(Math.random() * npc.dialogue.default.length)
			];
		}

		if (npcId === "nova") {
			if (state.achievements.has("root_obtained"))
				return `Impressive. Root access. The trace is at ${Math.min(99, 20 + cmds)}%. You're running out of time.`;
			if (cmds > 30)
				return `You've run ${cmds} commands. Every one is logged. I can see your entire methodology. You're good. But predictable.`;
			if (state.faction === "corp")
				return "Good. You're one of us now. I'll reduce the trace speed. For now.";
			if (state.faction === "resistance")
				return "Resistance. Of course. We'll see how that works out for you.";
			return npc.dialogue.default[
				Math.floor(Math.random() * npc.dialogue.default.length)
			];
		}

		if (npcId === "watcher") {
			if (level >= 10)
				return npc.dialogue.meta[
					Math.floor(Math.random() * npc.dialogue.meta.length)
				];
			if (cmds >= 100)
				return `100+ commands. The outer shell calls to you. Type \`ascend\` when ready.`;
			return npc.dialogue.default[
				Math.floor(Math.random() * npc.dialogue.default.length)
			];
		}

		return npc.dialogue.default[
			Math.floor(Math.random() * npc.dialogue.default.length)
		];
	}

	ask(npcId, question) {
		const npc = NPCS[npcId];
		if (!npc)
			return {
				error: `ask: unknown contact '${npcId}'. Known: ada, cypher, nova, watcher`,
			};

		const q = question.toLowerCase();
		let topic = null;

		if (
			q.includes("watcher") ||
			q.includes("arg") ||
			q.includes("simulation") ||
			q.includes("layer")
		)
			topic = "watcher";
		else if (
			q.includes("meta") ||
			q.includes("outer") ||
			q.includes("reality") ||
			q.includes("real world")
		)
			topic = "meta";
		else if (
			q.includes("faction") ||
			q.includes("resistance") ||
			q.includes("corp") ||
			q.includes("join")
		)
			topic = "faction";
		else if (
			q.includes("phase") ||
			q.includes("level") ||
			q.includes("progress") ||
			q.includes("stage")
		)
			topic = "phase";
		else if (
			q.includes("skill") ||
			q.includes("unlock") ||
			q.includes("ability")
		)
			topic = "skills";
		else if (
			q.includes("chimera") &&
			(q.includes("connect") ||
				q.includes("nc") ||
				q.includes("port") ||
				q.includes("8443"))
		)
			topic = "chimera";
		else if (
			q.includes("chimera") ||
			q.includes("mission") ||
			q.includes("surveillance")
		)
			topic = "chimera";
		else if (
			q.includes("root") ||
			q.includes("priv") ||
			q.includes("sudo") ||
			q.includes("gtfo") ||
			q.includes("escalat")
		)
			topic = "priv";
		else if (
			q.includes("security") ||
			q.includes("hack") ||
			q.includes("exploit") ||
			q.includes("attack")
		)
			topic = "security";
		else if (
			q.includes("network") ||
			q.includes("nmap") ||
			q.includes("scan") ||
			q.includes("port") ||
			q.includes("nc ")
		)
			topic = "networking";
		else if (
			q.includes("forensic") ||
			q.includes("strace") ||
			q.includes("strings") ||
			q.includes("binary")
		)
			topic = "forensics";
		else if (q.includes("awk") || q.includes("sed") || q.includes("field"))
			topic = "awk";
		else if (q.includes("git") || q.includes("version") || q.includes("commit"))
			topic = "git";
		else if (
			q.includes("help") ||
			q.includes("start") ||
			q.includes("begin") ||
			q.includes("first")
		)
			topic = "help";
		else if (
			q.includes("join") ||
			q.includes("nexus") ||
			q.includes("corp") ||
			q.includes("offer")
		)
			topic = npcId === "nova" ? "recruit" : "faction";
		else if (
			q.includes("hint") ||
			q.includes("next") ||
			q.includes("do") ||
			q.includes("what") ||
			q.includes("how")
		)
			topic = "hint";
		else if (
			q.includes("threat") ||
			q.includes("trace") ||
			q.includes("caught") ||
			q.includes("warn")
		)
			topic = "threat";
		else if (q.includes("ada") || q.includes("handler") || q.includes("trust"))
			topic = "ada";
		else if (q.includes("ssh") || q.includes("key")) topic = "ssh";
		else if (q.includes("trust") || q.includes("ally") || q.includes("who"))
			topic = "trust";
		else if (
			q.includes("nexuscorp") ||
			q.includes("company") ||
			q.includes("history")
		)
			topic = "nexus";
		else if (q.includes("src") || q.includes("source") || q.includes("code"))
			topic = "src";

		return this.talk(npcId, topic);
	}

	listContacts() {
		return Object.entries(NPCS).map(([id, npc]) => ({
			id,
			name: npc.name,
			title: npc.title,
			met: (this.visitCount[id] || 0) > 0,
			visits: this.visitCount[id] || 0,
		}));
	}
}

window.NPCS = NPCS;
window.NPCSystem = NPCSystem;
