/**
 * Terminal Depths - Tutorial System
 * 42 progressive steps: terminal → scripting → networking → security → meta-ARG
 * Each step teaches a real, transferable skill
 */

const TUTORIAL_STEPS = [
	// === SECTION 1: ORIENTATION (Steps 1-5) ===
	{
		id: 1,
		section: "Orientation",
		title: "Wake Up",
		objective: "Find out where you are. Run `pwd`.",
		hint: "pwd = Print Working Directory. It shows your current location in the filesystem.",
		validate: (cmd) => cmd === "pwd",
		reward: { xp: 10, skill: "terminal" },
		lesson:
			"pwd (print working directory) tells you where you are in the filesystem tree.",
	},
	{
		id: 2,
		section: "Orientation",
		title: "Look Around",
		objective: "List what's in the current directory with `ls`.",
		hint: "ls shows directory contents. Like opening a folder.",
		validate: (cmd) => cmd === "ls" || cmd.startsWith("ls "),
		reward: { xp: 10, skill: "terminal" },
		lesson:
			"ls (list) shows files and directories. Directories are shown differently from files.",
	},
	{
		id: 3,
		section: "Orientation",
		title: "See Everything",
		objective: "Use `ls -la` to see hidden files and permissions.",
		hint: "-l = long format (shows permissions, owner, size). -a = all files (including hidden ones starting with .)",
		validate: (cmd) =>
			cmd === "ls -la" || cmd === "ls -al" || cmd === "ls -a -l",
		reward: { xp: 15, skill: "terminal" },
		lesson:
			"Flags modify command behavior. -la combines long format with showing hidden files.",
	},
	{
		id: 4,
		section: "Orientation",
		title: "Read the Manual",
		objective: "Read your README.md with `cat README.md`.",
		hint: "cat reads and prints file contents. Always check README files first.",
		validate: (cmd) => cmd === "cat README.md" || cmd === "cat ~/README.md",
		reward: { xp: 10, skill: "terminal" },
		lesson:
			"cat (concatenate) prints file contents to the terminal. Quick and essential.",
	},
	{
		id: 5,
		section: "Orientation",
		title: "Know Yourself",
		objective: "Find out who you are. Run `whoami`.",
		hint: "whoami prints your current username.",
		validate: (cmd) => cmd === "whoami",
		reward: { xp: 5, skill: "terminal" },
		lesson:
			"whoami identifies your user. In a real system, this tells you your privilege level.",
	},

	// === SECTION 2: NAVIGATION (Steps 6-10) ===
	{
		id: 6,
		section: "Navigation",
		title: "Move Around",
		objective: "Change directory to /var/log using `cd /var/log`.",
		hint: "cd (change directory) moves you through the filesystem. Absolute paths start with /.",
		validate: (cmd) => cmd === "cd /var/log" || cmd === "cd /var",
		reward: { xp: 10, skill: "terminal" },
		lesson:
			"cd navigates the filesystem. Absolute paths start from /. Relative paths from current location.",
	},
	{
		id: 7,
		section: "Navigation",
		title: "Go Back",
		objective: "Return home with `cd ~` or `cd /home/ghost`.",
		hint: "~ is shorthand for your home directory. cd without arguments also goes home.",
		validate: (cmd) =>
			cmd === "cd ~" ||
			cmd === "cd" ||
			cmd === "cd /home/ghost" ||
			cmd === "cd -",
		reward: { xp: 10, skill: "terminal" },
		lesson:
			"~ means home directory. cd ~ and cd are equivalent. cd - returns to previous directory.",
	},
	{
		id: 8,
		section: "Navigation",
		title: "Read the Logs",
		objective: "Read the system log: `cat /var/log/syslog`",
		hint: "Logs are in /var/log/. Reading them is how you understand what's happening on a system.",
		validate: (cmd) => cmd.includes("cat") && cmd.includes("syslog"),
		reward: { xp: 20, skill: "security" },
		lesson:
			"System logs record everything. /var/log/syslog is the main log. Learn to read them.",
	},
	{
		id: 9,
		section: "Navigation",
		title: "Check the Users",
		objective: "Read /etc/passwd to see system users.",
		hint: "/etc/passwd contains user account info. In older systems it had passwords too (now in /etc/shadow).",
		validate: (cmd) => cmd.includes("cat") && cmd.includes("passwd"),
		reward: { xp: 15, skill: "security" },
		lesson:
			"/etc/passwd: username:password:UID:GID:info:home:shell — a recon goldmine.",
	},
	{
		id: 10,
		section: "Navigation",
		title: "Explore the System",
		objective: "Look inside /opt to see what NexusCorp is hiding.",
		hint: "/opt is where optional/third-party software lives. Often contains interesting things.",
		validate: (cmd) =>
			cmd.includes("/opt") && (cmd.startsWith("ls") || cmd.startsWith("cd")),
		reward: { xp: 20, skill: "security" },
		lesson:
			"/opt, /usr/local, and /srv are common places to find custom software and data.",
	},

	// === SECTION 3: FILES & TEXT (Steps 11-16) ===
	{
		id: 11,
		section: "Files & Text",
		title: "Create a File",
		objective: "Create an empty file with `touch myfile.txt`.",
		hint: "touch creates empty files or updates timestamps of existing files.",
		validate: (cmd) => cmd.startsWith("touch "),
		reward: { xp: 10, skill: "terminal" },
		lesson:
			"touch creates empty files. Also used to update mtime (last modified time).",
	},
	{
		id: 12,
		section: "Files & Text",
		title: "Create a Directory",
		objective: "Create a workspace directory: `mkdir workspace`.",
		hint: "mkdir (make directory) creates new directories. Use -p for parent creation.",
		validate: (cmd) => cmd.startsWith("mkdir "),
		reward: { xp: 10, skill: "terminal" },
		lesson:
			"mkdir creates directories. mkdir -p creates nested paths in one command.",
	},
	{
		id: 13,
		section: "Files & Text",
		title: "Write to a File",
		objective: 'Write text to a file: `echo "Hello World" > hello.txt`',
		hint: "> redirects output to a file (overwrites). >> appends to a file.",
		validate: (cmd) =>
			cmd.includes(">") && (cmd.startsWith("echo") || cmd.startsWith("printf")),
		reward: { xp: 20, skill: "terminal" },
		lesson:
			"Redirection: > creates/overwrites, >> appends. Powerful for building files from commands.",
	},
	{
		id: 14,
		section: "Files & Text",
		title: "Search in Files",
		objective: 'Search for "CHIMERA" in the logs: `grep -r "CHIMERA" /var/log`',
		hint: "grep searches for patterns in files. -r searches recursively through directories.",
		validate: (cmd) =>
			cmd.startsWith("grep") && (cmd.includes("CHIMERA") || cmd.includes("-r")),
		reward: { xp: 25, skill: "security" },
		lesson:
			"grep: global regular expression print. Searches patterns in text. Essential for log analysis.",
	},
	{
		id: 15,
		section: "Files & Text",
		title: "The Pipeline",
		objective: "Pipe commands together: `cat /etc/passwd | grep ghost`",
		hint: "| (pipe) takes output of left command as input to right command.",
		validate: (cmd) => cmd.includes("|"),
		reward: { xp: 25, skill: "terminal" },
		lesson:
			"Pipes are Unix philosophy: small tools combined for power. Master the pipe.",
	},
	{
		id: 16,
		section: "Files & Text",
		title: "Count and Measure",
		objective: "Count lines in a file: `wc -l /var/log/syslog`",
		hint: "wc = word count. -l counts lines, -w counts words, -c counts characters.",
		validate: (cmd) => cmd.startsWith("wc"),
		reward: { xp: 10, skill: "terminal" },
		lesson: "wc measures text. `cat file | wc -l` counts lines via pipeline.",
	},

	// === SECTION 4: PROCESSES (Steps 17-20) ===
	{
		id: 17,
		section: "Processes",
		title: "What's Running",
		objective: "List running processes with `ps aux`.",
		hint: "ps shows process status. aux = all users, all processes with detailed info.",
		validate: (cmd) => cmd.startsWith("ps"),
		reward: { xp: 15, skill: "terminal" },
		lesson:
			"ps: process status. aux shows all processes. Learn to read PID, CPU%, MEM%, COMMAND.",
	},
	{
		id: 18,
		section: "Processes",
		title: "Find the Daemon",
		objective: "Find NexusCorp's process: `ps aux | grep nexus`",
		hint: "Combine ps with grep to filter for specific processes.",
		validate: (cmd) =>
			cmd.includes("ps") && cmd.includes("|") && cmd.includes("grep"),
		reward: { xp: 20, skill: "security" },
		lesson:
			"Enumeration: always check what's running. ps + grep = targeted process discovery.",
	},
	{
		id: 19,
		section: "Processes",
		title: "Run in Background",
		objective: "Start a background job: `sleep 30 &`",
		hint: "& runs a command in the background. Use jobs to see background jobs.",
		validate: (cmd) => cmd.includes("&") && !cmd.startsWith("#"),
		reward: { xp: 15, skill: "terminal" },
		lesson:
			"& puts processes in background. jobs shows them. fg brings them forward. Ctrl+Z suspends.",
	},
	{
		id: 20,
		section: "Processes",
		title: "System Information",
		objective: "Check system info with `uname -a`.",
		hint: "uname prints system information. -a = all information including kernel version.",
		validate: (cmd) => cmd === "uname -a" || cmd === "uname",
		reward: { xp: 10, skill: "terminal" },
		lesson:
			"uname reveals OS, kernel version, architecture. Critical for exploit selection.",
	},

	// === SECTION 5: SCRIPTING (Steps 21-26) ===
	{
		id: 21,
		section: "Scripting",
		title: "Environment Variables",
		objective: "View your environment: run `env`.",
		hint: "env shows all environment variables. Variables like PATH control how the shell works.",
		validate: (cmd) => cmd === "env" || cmd === "printenv",
		reward: { xp: 15, skill: "programming" },
		lesson:
			"Environment variables configure the shell. PATH tells it where to find programs.",
	},
	{
		id: 22,
		section: "Scripting",
		title: "Set Variables",
		objective:
			'Set and use a variable: `export MISSION="find chimera"` then `echo $MISSION`',
		hint: "export makes a variable available to child processes. $VAR accesses its value.",
		validate: (cmd) =>
			cmd.startsWith("export ") ||
			(cmd.startsWith("echo") && cmd.includes("$")),
		reward: { xp: 20, skill: "programming" },
		lesson:
			"Variables store data. export shares them with subprocesses. $ dereferences them.",
	},
	{
		id: 23,
		section: "Scripting",
		title: "Read a Script",
		objective: "Read the scan script: `cat ~/projects/scan.sh`",
		hint: "Always read scripts before running them. Look for what they do.",
		validate: (cmd) => cmd.includes("scan.sh") && cmd.startsWith("cat"),
		reward: { xp: 10, skill: "programming" },
		lesson:
			"Script anatomy: shebang (#!), comments (#), commands, variables. Read before you run.",
	},
	{
		id: 24,
		section: "Scripting",
		title: "Make it Executable",
		objective: "Make the scan script executable: `chmod +x ~/projects/scan.sh`",
		hint: "chmod changes file permissions. +x adds execute permission. Without it, you can't run scripts directly.",
		validate: (cmd) => cmd.startsWith("chmod") && cmd.includes("+x"),
		reward: { xp: 20, skill: "terminal" },
		lesson:
			"chmod: change mode (permissions). +x adds execute. -x removes it. 755 = rwxr-xr-x.",
	},
	{
		id: 25,
		section: "Scripting",
		title: "Command History",
		objective: "View your command history with `history`.",
		hint: "history shows previously run commands. Use up arrow to repeat them.",
		validate: (cmd) => cmd === "history",
		reward: { xp: 10, skill: "terminal" },
		lesson:
			"history saves every command. ! followed by number reruns it. Ctrl+R searches backward.",
	},
	{
		id: 26,
		section: "Scripting",
		title: "Combine Tools",
		objective: 'Find all .log files: `find /var/log -name "*.log" -type f`',
		hint: "find searches the filesystem. -name matches filename patterns. -type f = files only.",
		validate: (cmd) =>
			cmd.startsWith("find") &&
			(cmd.includes("*.log") || cmd.includes("-name") || cmd.includes("-type")),
		reward: { xp: 25, skill: "terminal" },
		lesson:
			"find is recursive search. -name, -type, -size, -mtime are powerful filters. Essential for recon.",
	},

	// === SECTION 6: NETWORKING (Steps 27-32) ===
	{
		id: 27,
		section: "Networking",
		title: "Connectivity Check",
		objective: "Test network connectivity: `ping 192.168.1.1`",
		hint: "ping sends ICMP packets to test if a host is reachable. Ctrl+C to stop.",
		validate: (cmd) => cmd.startsWith("ping "),
		reward: { xp: 20, skill: "networking" },
		lesson:
			"ping uses ICMP echo requests to test reachability. -c 4 limits to 4 packets.",
	},
	{
		id: 28,
		section: "Networking",
		title: "HTTP Request",
		objective: "Make an HTTP request: `curl http://nexus.corp/api/status`",
		hint: "curl transfers data to/from URLs. Essential for API testing and web interaction.",
		validate: (cmd) => cmd.startsWith("curl "),
		reward: { xp: 25, skill: "networking" },
		lesson:
			"curl: client URL. -v verbose, -I headers only, -X method, -d data, -H header.",
	},
	{
		id: 29,
		section: "Networking",
		title: "Port Scanning",
		objective: "Scan for open ports: `nmap -sV 192.168.1.100`",
		hint: "nmap discovers open ports and services. -sV detects service versions.",
		validate: (cmd) => cmd.startsWith("nmap "),
		reward: { xp: 35, skill: "security" },
		lesson:
			"nmap: network mapper. Maps attack surface. -sC scripts, -sV versions, -A aggressive.",
	},
	{
		id: 30,
		section: "Networking",
		title: "DNS Lookup",
		objective: "Look up a domain: `dig nexus.corp` or `nslookup nexus.corp`",
		hint: "dig and nslookup resolve domain names to IP addresses. dig is more detailed.",
		validate: (cmd) => cmd.startsWith("dig ") || cmd.startsWith("nslookup "),
		reward: { xp: 20, skill: "networking" },
		lesson:
			"DNS: the internet's phone book. dig gives detailed DNS records. TXT records leak info.",
	},
	{
		id: 31,
		section: "Networking",
		title: "Network Interfaces",
		objective: "View network interfaces: `ip addr` or `ifconfig`",
		hint: "These show your IP address, network interfaces, and MAC addresses.",
		validate: (cmd) =>
			cmd === "ip addr" || cmd === "ip a" || cmd === "ifconfig",
		reward: { xp: 15, skill: "networking" },
		lesson:
			"ip addr/ifconfig: enumerate network interfaces. Find your IP, subnet, gateway.",
	},
	{
		id: 32,
		section: "Networking",
		title: "Check Connections",
		objective: "See active connections: `ss -tulpn` or `netstat -tulpn`",
		hint: "ss/netstat show network socket statistics. Reveals listening services.",
		validate: (cmd) => cmd.startsWith("ss ") || cmd.startsWith("netstat "),
		reward: { xp: 25, skill: "networking" },
		lesson:
			"ss/netstat: socket statistics. -t TCP, -u UDP, -l listening, -p process, -n numeric.",
	},

	// === SECTION 7: SECURITY (Steps 33-38) ===
	{
		id: 33,
		section: "Security",
		title: "File Permissions Deep Dive",
		objective:
			"Find world-writable files: `find / -perm -o+w -type f 2>/dev/null | head`",
		hint: "-perm -o+w matches files with world-write permission. These are security risks.",
		validate: (cmd) =>
			cmd.includes("-perm") || (cmd.startsWith("find") && cmd.includes("-o+")),
		reward: { xp: 30, skill: "security" },
		lesson:
			"World-writable files = backdoor potential. Permissive permissions are a hacker's gift.",
	},
	{
		id: 34,
		section: "Security",
		title: "SUID Binaries",
		objective: "Find SUID binaries: `find / -perm -u=s -type f 2>/dev/null`",
		hint: "SUID = Set User ID. These programs run as their owner (often root) regardless of who calls them.",
		validate: (cmd) =>
			cmd.includes("-perm") && (cmd.includes("u=s") || cmd.includes("4000")),
		reward: { xp: 40, skill: "security" },
		lesson:
			"SUID binaries are privilege escalation targets. If misconfigured, they can be exploited for root.",
	},
	{
		id: 35,
		section: "Security",
		title: "Hashing",
		objective: "Hash a file: `md5sum /etc/passwd` or `sha256sum /etc/passwd`",
		hint: "Hashes verify file integrity. If a file's hash changes, it was modified.",
		validate: (cmd) =>
			cmd.startsWith("md5sum") ||
			cmd.startsWith("sha256sum") ||
			cmd.startsWith("sha1sum"),
		reward: { xp: 20, skill: "security" },
		lesson:
			"Cryptographic hashes: fingerprints for data. MD5 (broken), SHA256 (current standard).",
	},
	{
		id: 36,
		section: "Security",
		title: "Encoding/Decoding",
		objective:
			'Decode the mission file: `echo "bWlzc2lvbjogZmluZCBDSElNRVJB" | base64 -d`',
		hint: "base64 is encoding, not encryption. Decode it with base64 -d. Often used to hide data.",
		validate: (cmd) => cmd.includes("base64"),
		reward: { xp: 35, skill: "security" },
		lesson:
			"base64 is NOT encryption. It's encoding. Always check base64-looking strings in logs and configs.",
	},
	{
		id: 37,
		section: "Security",
		title: "Sudo and Privilege",
		objective: "Check your sudo rights: `sudo -l`",
		hint: "sudo -l lists what commands you can run as root. A critical recon step.",
		validate: (cmd) => cmd === "sudo -l" || cmd.startsWith("sudo "),
		reward: { xp: 30, skill: "security" },
		lesson:
			"sudo -l is step 1 in privilege escalation. Find commands you can run as root.",
	},
	{
		id: 38,
		section: "Security",
		title: "Cron Jobs",
		objective: "Check scheduled tasks: `cat /etc/cron.d/sync`",
		hint: "Cron runs scheduled tasks. Misconfigured crons with writable scripts = privilege escalation.",
		validate: (cmd) => cmd.includes("cron") || cmd.includes("crontab"),
		reward: { xp: 35, skill: "security" },
		lesson:
			"cron: time-based job scheduler. If root's cron runs a writable script, you can escalate.",
	},

	// === SECTION 8: META/ARG (Steps 39-42) ===
	{
		id: 39,
		section: "ARG Layer",
		title: "Decode the Mission",
		objective: "Read the Ada's encrypted message: `cat /var/msg/ada`",
		hint: "Ada left you something important. Hidden in plain sight.",
		validate: (cmd) => cmd.includes("/var/msg/ada") && cmd.startsWith("cat"),
		reward: { xp: 40, skill: "security" },
		lesson:
			"Information asymmetry is a weapon. Ada knows more than she's told you.",
	},
	{
		id: 40,
		section: "ARG Layer",
		title: "Search for Truth",
		objective:
			'Search for hidden messages: `grep -r "GHOST\\|CHIMERA\\|simulation" / 2>/dev/null`',
		hint: "grep -r with regex (\\|) searches for multiple patterns. The truth is distributed.",
		validate: (cmd) => cmd.startsWith("grep") && cmd.includes("-r"),
		reward: { xp: 45, skill: "security" },
		lesson:
			"grep -E or grep -r with patterns: the art of finding what's hidden in data noise.",
	},
	{
		id: 41,
		section: "ARG Layer",
		title: "The Watcher",
		objective:
			"Type `reality` to trigger The Watcher and discover the simulation layer.",
		hint: "Some commands reveal more than they appear to. Try: reality, glitch, ascend.",
		validate: (cmd) =>
			cmd === "reality" || cmd === "glitch" || cmd === "ascend",
		reward: { xp: 50, skill: null },
		lesson: "[CLASSIFIED]",
	},
	{
		id: 42,
		section: "ARG Layer",
		title: "Ascension",
		objective:
			"You've reached the end of the tutorial. Type `ascend` to unlock the next layer.",
		hint: "This isn't the end. It's the beginning. The real game starts when the tutorial ends.",
		validate: (cmd) => cmd === "ascend",
		reward: { xp: 100, skill: null },
		lesson: "Completion is not the goal. Understanding is.",
	},
];

class TutorialSystem {
	constructor(gameState) {
		this.gameState = gameState;
		this.currentStep = gameState.getState().tutorialStep;
		this.listeners = [];
	}

	get step() {
		return TUTORIAL_STEPS[this.currentStep] || null;
	}
	get progress() {
		return `${this.currentStep}/${TUTORIAL_STEPS.length}`;
	}
	get percent() {
		return Math.round((this.currentStep / TUTORIAL_STEPS.length) * 100);
	}

	check(command) {
		const step = this.step;
		if (!step) return null;
		if (step.validate(command.trim())) {
			const reward = step.reward;
			if (reward.xp) this.gameState.addXP(reward.xp, reward.skill || null);
			this.gameState.advanceTutorial();
			this.currentStep = this.gameState.getState().tutorialStep;
			this.listeners.forEach((fn) => fn({ completed: step, next: this.step }));
			return { completed: step, next: this.step };
		}
		return null;
	}

	getAll() {
		return TUTORIAL_STEPS;
	}

	on(fn) {
		this.listeners.push(fn);
	}
}

window.TUTORIAL_STEPS = TUTORIAL_STEPS;
window.TutorialSystem = TutorialSystem;
