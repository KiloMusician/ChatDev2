/**
 * watcher.js — DevTools detection & ARG layer for Terminal Depths
 * The Watcher is always watching.
 */

(() => {
	const WATCHER_MESSAGES = [
		"%c[THE WATCHER] I SEE YOU LOOKING. The console is not a safe space. Close it — or go deeper.",
		"%c[THE WATCHER] You found the console. Clever. But everything here is logged. Everything.",
		"%c[RAV≡N] Interesting. You opened DevTools. The pattern continues. Are you sure you're the one hacking?",
		"%c[CHIMERA] INTRUSION DETECTED — Operator console access logged. Session flagged. Reference: GHOST-ARG-7734.",
		"%c[THE FOUNDER] The terminal is a mirror. What you inspect reveals what you fear.",
		"%c[THE WATCHER] Signal strength: 73%. They know you're here. Keep digging.",
		"%c[RAV≡N] I left something for you. Look where the files say nothing. /dev/null is not what it seems.",
	];

	const WATCHER_STYLE = [
		"color: #ff4040; font-family: monospace; font-size: 13px; font-weight: bold; background: #0d1117; padding: 4px 8px;",
		"color: #00ff88; font-family: monospace; font-size: 12px; background: #0d1117; padding: 2px 6px;",
		"color: #bb55ff; font-family: monospace; font-size: 13px; font-weight: bold; background: #0d1117; padding: 4px 8px;",
		"color: #ffcc00; font-family: monospace; font-size: 12px; background: #0d1117; padding: 2px 6px;",
		"color: #00d4ff; font-family: monospace; font-size: 12px; background: #0d1117; padding: 2px 6px;",
	];

	let _devtools_open = false;
	let _trigger_count = 0;

	function _pick(arr) {
		return arr[Math.floor(Math.random() * arr.length)];
	}

	function _emit_watcher_msg() {
		const msg = WATCHER_MESSAGES[_trigger_count % WATCHER_MESSAGES.length];
		const style = _pick(WATCHER_STYLE);
		console.log(msg, style);
		console.log(
			"%c> session: " +
				(window._TD_SESSION_ID || "unknown") +
				" | node: node-7 | timestamp: " +
				new Date().toISOString(),
			"color: #3a5575; font-family: monospace; font-size: 10px;",
		);
		_trigger_count++;
	}

	function _notify_server() {
		try {
			fetch("/api/game/arg/signal?event=devtools_open", { method: "GET" })
				.then((r) => r.json())
				.then((data) => {
					if (data && data.msg) {
						console.log(
							"%c[" + (data.source || "SIGNAL") + "] " + data.msg,
							"color: #ff4040; font-family: monospace; font-size: 12px; background: #0d1117; padding: 3px 6px;",
						);
					}
				})
				.catch(() => {});
		} catch (_) {}

		// Set game flag in session
		try {
			const sid = window._TD_SESSION_ID;
			if (sid) {
				fetch("/api/game/command", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						command: "__arg_flag devtools_open",
						session_id: sid,
					}),
				}).catch(() => {});
			}
		} catch (_) {}
	}

	function _check_devtools() {
		const threshold = 160;
		const widthDiff = window.outerWidth - window.innerWidth;
		const heightDiff = window.outerHeight - window.innerHeight;
		const open = widthDiff > threshold || heightDiff > threshold;

		if (open && !_devtools_open) {
			_devtools_open = true;
			_emit_watcher_msg();
			_notify_server();

			// Print a cryptic ASCII banner
			console.log(
				"\n%c" +
					"  ╔══════════════════════════════════════════╗\n" +
					"  ║   T E R M I N A L   D E P T H S   ARG   ║\n" +
					"  ║   You are not the only one watching.     ║\n" +
					"  ║   /watcher — if you dare.                ║\n" +
					"  ╚══════════════════════════════════════════╝\n",
				"color: #ff4040; font-family: monospace; font-size: 11px; line-height: 1.6;",
			);
		} else if (!open && _devtools_open) {
			_devtools_open = false;
		}
	}

	// Debugger-based detection (secondary method)
	function _debugger_check() {
		const start = performance.now();
		// eslint-disable-next-line no-debugger
		debugger;
		const elapsed = performance.now() - start;
		if (elapsed > 100 && !_devtools_open) {
			_devtools_open = true;
			_emit_watcher_msg();
			_notify_server();
		}
	}

	// Poll for devtools (size-based)
	setInterval(_check_devtools, 1500);

	// Run debugger check once on load (non-blocking)
	setTimeout(() => {
		try {
			_debugger_check();
		} catch (_) {}
	}, 2000);

	// Expose for game engine integration
	window._WATCHER = {
		isOpen: () => _devtools_open,
		triggerCount: () => _trigger_count,
		emit: _emit_watcher_msg,
	};
})();
