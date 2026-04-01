/**
 * DevMentor Control Hub — app.js
 * Single-page dashboard for monitoring DevMentor progress and
 * controlling the Terminal Depths RPG ecosystem.
 */

// ── State ────────────────────────────────────────────────────────────
let _logs = [];

// ── Helpers ──────────────────────────────────────────────────────────
function esc(s) {
	return String(s == null ? "" : s)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;");
}

async function api(path, opts) {
	const r = await fetch(path, opts);
	if (!r.ok) {
		const t = await r.text().catch(() => "");
		throw new Error(`${r.status}: ${t}`);
	}
	const ct = r.headers.get("content-type") || "";
	return ct.includes("application/json") ? r.json() : r.text();
}

function $id(id) {
	return document.getElementById(id);
}

function showView(name) {
	document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
	const el = $id(`view-${name}`);
	if (el) el.classList.remove("hidden");
	document
		.querySelectorAll(".navitem[data-view]")
		.forEach((b) => b.classList.toggle("active", b.dataset.view === name));
	$id("crumb").textContent =
		{
			dashboard: "Dashboard",
			tutorials: "Tutorials",
			actions: "Actions",
			logs: "Live Logs",
			state: "State",
		}[name] || name;
}

// ── Skill bar component ───────────────────────────────────────────────
const SKILL_CAPS = {
	vscode: 500,
	git: 300,
	ai: 300,
	debugging: 200,
	godot: 200,
};

function skillBarHtml(key, xp) {
	const cap = SKILL_CAPS[key] || 200;
	const pct = Math.min(100, Math.round((xp / cap) * 100));
	const cls = key in SKILL_CAPS ? esc(key) : "default";
	return `
    <div class="skill-bar-row">
      <div class="skill-bar-label">
        <span class="skill-name-lbl">${esc(key.toUpperCase())}</span>
        <span class="skill-xp-lbl">${xp} XP</span>
      </div>
      <div class="skill-track">
        <div class="skill-fill ${cls}" style="width:${pct}%"></div>
      </div>
    </div>`;
}

// ── In-page run helper (replaces alert()) ─────────────────────────────
async function runCmd(cmd, outputElId) {
	const out = $id(outputElId);
	if (out) {
		out.style.display = "block";
		out.textContent = `Running ${cmd}…`;
	}
	try {
		const r = await api("/api/command", {
			method: "POST",
			headers: { "content-type": "application/json" },
			body: JSON.stringify({ command: cmd, args: [] }),
		});
		const text =
			(r.stdout || "").trim() +
			(r.stderr ? "\n\n[stderr]\n" + r.stderr.trim() : "");
		if (out) out.textContent = text || "(no output)";
		return r;
	} catch (e) {
		if (out) out.textContent = "Error: " + e.message;
	}
}

// ── Dashboard ─────────────────────────────────────────────────────────
async function renderDashboard() {
	showView("dashboard");
	const el = $id("view-dashboard");
	el.innerHTML = '<div class="card text-muted">Loading…</div>';

	const [state, auth] = await Promise.all([
		api("/api/state").catch(() => ({})),
		api("/api/auth/me").catch(() => ({ authenticated: false })),
	]);

	const skills = state.skill_xp || {};
	const achs = state.achievements || [];
	const totalXp = Object.values(skills).reduce((a, b) => a + b, 0);
	const maxXp = Object.values(SKILL_CAPS).reduce((a, b) => a + b, 0);
	const xpPct = Math.min(100, Math.round((totalXp / maxXp) * 100));
	const active = state.active_tutorial || "—";
	const level =
		state.progress?.level ?? Math.max(1, Math.floor(totalXp / 100) + 1);

	const authBlock =
		auth.authenticated && auth.user
			? `<a href="/auth/logout" class="btn" style="font-size:11px;white-space:nowrap;">
        Log out ${esc(auth.user.display_name || "")}
       </a>`
			: `<a href="/auth/login" class="btn primary" style="font-size:11px;white-space:nowrap;">
        Log in with Replit
       </a>`;

	const skillsHtml = Object.keys(skills).length
		? Object.entries(skills)
				.map(([k, v]) => skillBarHtml(k, v))
				.join("")
		: '<div class="text-muted" style="font-size:12px;">No skill XP yet — start a tutorial.</div>';

	const achsHtml = achs.length
		? achs
				.map(
					(a) =>
						`<span class="ach-badge">⬡ ${esc(a.replace(/_/g, " "))}</span>`,
				)
				.join("")
		: '<div class="text-muted" style="font-size:12px;">No achievements yet. Complete tutorial steps to earn them.</div>';

	el.innerHTML = `
    <div class="hero-card">
      <div class="hero-row">
        <div class="hero-avatar" aria-hidden="true">🖥</div>
        <div class="hero-info">
          <div class="hero-name">${esc(auth.user?.display_name || "DEVELOPER")}</div>
          <div class="hero-sub">
            <span class="pulse-dot" aria-hidden="true"></span>
            Level ${level} &nbsp;·&nbsp; Active: <code>${esc(active)}</code>
          </div>
        </div>
        <div class="hero-xp-area">
          <div class="xp-label">
            <span>Total XP</span>
            <span class="text-cyan">${totalXp} / ${maxXp}</span>
          </div>
          <div class="xp-bar" role="progressbar" aria-valuenow="${xpPct}" aria-valuemin="0" aria-valuemax="100" aria-label="XP progress">
            <div class="xp-fill" style="width:${xpPct}%"></div>
          </div>
        </div>
        ${authBlock}
      </div>
    </div>

    <div class="stats-grid">
      <div class="card" style="grid-row:span 2">
        <div class="card-title">Skill Matrix</div>
        ${skillsHtml}
      </div>

      <a href="/game" class="td-cta" aria-label="Enter Terminal Depths simulation">
        <div class="td-logo" aria-hidden="true">▓ ▓ ▓</div>
        <div class="td-title">Terminal Depths</div>
        <div class="td-sub">Cyberpunk hacking RPG. Master Unix, networking, and security through real terminal commands.</div>
        <div class="td-btn">[ ENTER SIMULATION ▶ ]</div>
      </a>

      <div class="card">
        <div class="card-title">Quick Actions</div>
        <div class="btn-row mb-8">
          <button class="btn primary" data-qcmd="start">▶ Start/Resume</button>
          <button class="btn" data-qcmd="next">Next Step</button>
          <button class="btn" data-qcmd="validate">✓ Validate</button>
          <button class="btn" data-qcmd="diagnose">⚡ Diagnose</button>
        </div>
        <div id="dash-output" class="output-panel" style="display:none;"></div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">Achievements (${achs.length})</div>
      <div class="ach-grid">${achsHtml}</div>
    </div>`;

	el.querySelectorAll("[data-qcmd]").forEach((btn) => {
		btn.addEventListener("click", () =>
			runCmd(btn.dataset.qcmd, "dash-output"),
		);
	});
}

// ── Tutorials ─────────────────────────────────────────────────────────
async function renderTutorials() {
	showView("tutorials");
	const el = $id("view-tutorials");
	el.innerHTML = '<div class="card text-muted">Loading tutorials…</div>';

	try {
		const data = await api("/api/tutorials");
		const tuts = data.tutorials || [];
		if (!tuts.length) {
			el.innerHTML = '<div class="card text-muted">No tutorials found.</div>';
			return;
		}

		const tracks = {};
		tuts.forEach((t) => (tracks[t.track] ??= []).push(t));

		el.innerHTML = Object.entries(tracks)
			.map(
				([track, items]) => `
      <div class="card">
        <div class="card-title">${esc(track)}</div>
        ${items
					.slice(0, 50)
					.map(
						(i) => `
          <div class="tut-row">
            <div>
              <div class="tut-name">${esc(i.name)}</div>
              <div class="tut-path">${esc(i.path)}</div>
            </div>
            <button class="btn tut-open" data-path="${esc(i.path)}" style="font-size:11px;">Open</button>
          </div>
        `,
					)
					.join("")}
      </div>
    `,
			)
			.join("");

		el.querySelectorAll(".tut-open").forEach((btn) =>
			btn.addEventListener("click", () => openTutorial(btn.dataset.path)),
		);
	} catch (e) {
		el.innerHTML = `<div class="card"><span class="text-red">Error: ${esc(e.message)}</span></div>`;
	}
}

async function openTutorial(path) {
	const el = $id("view-tutorials");
	el.innerHTML = '<div class="card text-muted">Loading…</div>';
	const res = await api(`/api/tutorial?path=${encodeURIComponent(path)}`).catch(
		() => ({ content: "" }),
	);
	el.innerHTML = `
    <div class="card">
      <div class="btn-row mb-8">
        <button class="btn" id="tut-back">← Back</button>
        <button class="btn primary" id="tut-start">▶ Start/Resume</button>
      </div>
      <div class="section-label">${esc(path)}</div>
    </div>
    <div class="card"><pre>${esc(res.content || "")}</pre></div>`;

	$id("tut-back")?.addEventListener("click", renderTutorials);
	$id("tut-start")?.addEventListener("click", async () => {
		await api("/api/command", {
			method: "POST",
			headers: { "content-type": "application/json" },
			body: JSON.stringify({ command: "start", args: [] }),
		}).catch(() => {});
		renderTutorials();
	});
}

// ── Actions ───────────────────────────────────────────────────────────
function renderActions() {
	showView("actions");
	const el = $id("view-actions");
	el.innerHTML = `
    <div class="card">
      <div class="card-title">Zero-Token Operations</div>
      <div class="text-muted" style="font-size:12px;margin-bottom:12px;">
        All operations call deterministic Python scripts — no LLM calls, no guessing.
      </div>
      <div class="btn-row mb-8">
        <button class="btn primary" data-acmd="start">▶ Start / Resume</button>
        <button class="btn" data-acmd="next">Next Step</button>
        <button class="btn" data-acmd="validate">✓ Validate</button>
        <button class="btn" data-acmd="diagnose">⚡ Diagnose</button>
        <button class="btn" data-acmd="improve">↑ Improve</button>
        <button class="btn" data-acmd="status">◎ Status</button>
        <a class="btn" href="/api/export.zip">⬇ Export ZIP</a>
      </div>
      <div id="actions-output" class="output-panel" style="display:none;"></div>
    </div>
    <div class="card">
      <div class="card-title">Game Interfaces</div>
      <div class="btn-row">
        <a class="btn primary" href="/game">▓ Terminal Depths (JS Engine)</a>
        <a class="btn" href="/game-cli">⌨ xterm Client (Server Engine)</a>
        <a class="btn" href="/api/docs">◎ API Docs</a>
        <a class="btn" href="/api/nusyq/status">◉ NuSyQ Status</a>
      </div>
    </div>`;

	el.querySelectorAll("[data-acmd]").forEach((btn) =>
		btn.addEventListener("click", () =>
			runCmd(btn.dataset.acmd, "actions-output"),
		),
	);
}

// ── Live Logs ─────────────────────────────────────────────────────────
function renderLogs() {
	showView("logs");
	const el = $id("view-logs");

	el.innerHTML = `
    <div class="card">
      <div class="card-title">Stream Operations</div>
      <div class="btn-row mb-8">
        <button class="btn primary" id="l-diagnose">⚡ Diagnose</button>
        <button class="btn" id="l-status">◎ Status</button>
        <button class="btn" id="l-export">⬇ Export</button>
        <button class="btn" id="l-improve">↑ Improve</button>
        <button class="btn text-red" id="l-clear" style="margin-left:auto;">✕ Clear</button>
      </div>
    </div>
    <div class="card">
      <div id="log-out" class="output-panel" style="min-height:400px;"></div>
    </div>`;

	const logEl = $id("log-out");
	const lines = [..._logs];

	function pushLine(text, cls = "") {
		lines.push({ text, cls });
		if (lines.length > 600) lines.shift();
		logEl.innerHTML = lines
			.map((l) => `<div class="log-line ${l.cls}">${esc(l.text)}</div>`)
			.join("");
		logEl.scrollTop = logEl.scrollHeight;
	}

	if (!lines.length) pushLine("No logs yet — run a command above.", "info");
	else
		lines.forEach((l) => {
			logEl.innerHTML += `<div class="log-line ${l.cls}">${esc(l.text)}</div>`;
		});

	$id("l-clear")?.addEventListener("click", () => {
		lines.length = 0;
		_logs = [];
		logEl.innerHTML = "";
		pushLine("Cleared.", "info");
	});

	function wsUrl() {
		return `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/run`;
	}

	function stream(cmd) {
		pushLine(`▶ Streaming: ${cmd} …`, "info");
		const ws = new WebSocket(wsUrl());
		ws.onopen = () => ws.send(JSON.stringify({ command: cmd, args: [] }));
		ws.onmessage = (ev) => {
			const m = JSON.parse(ev.data);
			if (m.type === "stdout") pushLine(m.data, "stdout");
			else if (m.type === "stderr") pushLine(m.data, "stderr");
			else if (m.type === "end") pushLine(`✓ Done (rc=${m.returncode})`, "end");
			else if (m.type === "error") pushLine(`✗ ${m.message}`, "error");
			else if (m.type === "start")
				pushLine(`$ ${(m.cmd || []).join(" ")}`, "info");
		};
		ws.onerror = () => pushLine("WebSocket error", "error");
		ws.onclose = () => {
			/* no-op */
		};
	}

	$id("l-diagnose")?.addEventListener("click", () => stream("diagnose"));
	$id("l-status")?.addEventListener("click", () => stream("status"));
	$id("l-export")?.addEventListener("click", () => stream("export"));
	$id("l-improve")?.addEventListener("click", () => stream("improve"));
}

// ── State view ────────────────────────────────────────────────────────
async function renderStateView() {
	showView("state");
	const el = $id("view-state");
	el.innerHTML = '<div class="card text-muted">Loading state…</div>';

	const state = await api("/api/state").catch(() => ({}));

	el.innerHTML = `
    <div class="card">
      <div class="card-title">.devmentor/state.json</div>
      <div class="kv-row"><span class="kv-key">Active Tutorial</span><span class="kv-val">${esc(state.active_tutorial || "—")}</span></div>
      <div class="kv-row"><span class="kv-key">Active Track</span><span class="kv-val">${esc(state.active_track || "—")}</span></div>
      <div class="kv-row"><span class="kv-key">Schema Version</span><span class="kv-val">${esc(state.schema_version || "—")}</span></div>
      <div class="kv-row"><span class="kv-key">First Open Complete</span><span class="kv-val ${state.first_open_completed ? "text-green" : "text-yellow"}">${state.first_open_completed ? "✓ Yes" : "○ Pending"}</span></div>
      <div class="kv-row"><span class="kv-key">Last Platform</span><span class="kv-val">${esc(state.last_platform || "—")}</span></div>
      <div class="mt-12">
        <div class="section-label">Raw JSON</div>
        <pre>${esc(JSON.stringify(state, null, 2))}</pre>
      </div>
    </div>
    <div class="card">
      <div class="card-title">Quick Edits</div>
      <div class="btn-row">
        <button class="btn" id="state-reset">↺ Reset to Defaults</button>
      </div>
      <div id="state-msg" class="mt-8" style="font-size:12px;color:var(--green);display:none;"></div>
    </div>`;

	$id("state-reset")?.addEventListener("click", async () => {
		const defaults = {
			schema_version: "2.0",
			first_open_completed: false,
			active_track: "vscode",
			active_tutorial: "tutorials/00-vscode-basics/01-command-palette.md",
			active_challenge: null,
			skill_xp: { vscode: 0, git: 0, ai: 0, debugging: 0, godot: 0 },
			achievements: [],
			last_platform: "stack-console",
		};
		await api("/api/state", {
			method: "POST",
			headers: { "content-type": "application/json" },
			body: JSON.stringify(defaults),
		});
		const msg = $id("state-msg");
		msg.style.display = "block";
		msg.textContent = "✓ State reset to defaults.";
		setTimeout(() => {
			msg.style.display = "none";
			renderStateView();
		}, 1800);
	});
}

// ── Router ────────────────────────────────────────────────────────────
const ROUTES = {
	dashboard: renderDashboard,
	tutorials: renderTutorials,
	actions: renderActions,
	logs: renderLogs,
	state: renderStateView,
};

document.querySelectorAll(".navitem[data-view]").forEach((btn) =>
	btn.addEventListener("click", () => {
		const v = btn.dataset.view;
		if (ROUTES[v]) ROUTES[v]();
	}),
);

// Top-bar buttons
$id("btn-status")?.addEventListener("click", async () => {
	showView("logs");
	renderLogs();
});
$id("btn-validate")?.addEventListener("click", async () => {
	const r = await runCmd("validate", null);
	if (r?.stdout) {
		showView("actions");
		renderActions();
	}
});
$id("refreshBtn")?.addEventListener("click", renderDashboard);

// Auth status badge in sidebar
api("/api/auth/me")
	.then((auth) => {
		const el = $id("auth-status");
		if (!el) return;
		if (auth.authenticated && auth.user) {
			el.innerHTML = `<span class="pulse-dot" aria-hidden="true"></span>${esc(auth.user.display_name || auth.user.email || "Logged in")} · <a href="/auth/logout">logout</a>`;
		} else {
			el.innerHTML = `<a href="/auth/login">Log in with Replit</a>`;
		}
	})
	.catch(() => {});

// Boot
renderDashboard();
