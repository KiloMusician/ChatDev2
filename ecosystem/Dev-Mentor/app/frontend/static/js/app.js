const view = document.getElementById("view");
const crumb = document.getElementById("crumb");

async function apiGet(path) {
	const r = await fetch(path);
	return await r.json();
}
async function apiText(path) {
	const r = await fetch(path);
	return await r.text();
}
async function apiPost(path, body) {
	const r = await fetch(path, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body || {}),
	});
	return await r.json();
}

function escapeHtml(s) {
	return s
		.replaceAll("&", "&amp;")
		.replaceAll("<", "&lt;")
		.replaceAll(">", "&gt;");
}

async function renderDashboard() {
	crumb.textContent = "Dashboard";
	const state = await apiGet("/api/state");
	const env = await apiGet("/api/run/detect").catch(() => ({
		ok: false,
		output: "",
	}));

	const achievements = (state.achievements || [])
		.map(
			(a) =>
				`<span class="badge"><span class="dot good"></span>${escapeHtml(a)}</span>`,
		)
		.join(" ");
	const xp = JSON.stringify(state.skill_xp || {});

	view.innerHTML = `
    <div class="card">
      <div class="row">
        <div class="kpi">
          <div class="label">Active Tutorial</div>
          <div class="value">${escapeHtml(state.active_tutorial || "unknown")}</div>
        </div>
        <div class="kpi">
          <div class="label">Active Track</div>
          <div class="value">${escapeHtml(state.active_track || "unknown")}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="label">XP</div>
      <pre>${escapeHtml(xp)}</pre>
      <div class="label">Achievements</div>
      <div class="small">${achievements || "none yet"}</div>
    </div>

    <div class="card">
      <div class="label">Environment (detect)</div>
      <pre>${escapeHtml(env.output || "")}</pre>
    </div>
  `;
}

async function renderTutorials() {
	crumb.textContent = "Tutorials";
	const state = await apiGet("/api/state");
	const active = state.active_tutorial || "START_HERE.md";
	const content = await apiText(`/api/file?path=${encodeURIComponent(active)}`);
	view.innerHTML = `
    <div class="card">
      <div class="label">Active tutorial</div>
      <div class="small">${escapeHtml(active)}</div>
    </div>
    <div class="card">
      <pre>${escapeHtml(content)}</pre>
    </div>
    <div class="card">
      <button class="btn" id="btn-next">Next Step</button>
    </div>
  `;
	document.getElementById("btn-next").onclick = async () => {
		const r = await apiPost("/api/run/next", {});
		alert(r.output || "done");
		renderTutorials();
	};
}

async function renderChallenges() {
	crumb.textContent = "Challenges";
	const active = "challenges/git-challenges/01-first-commit/README.md";
	const content = await apiText(`/api/file?path=${encodeURIComponent(active)}`);
	view.innerHTML = `
    <div class="card">
      <div class="label">Sample challenge</div>
      <div class="small">${escapeHtml(active)}</div>
    </div>
    <div class="card">
      <pre>${escapeHtml(content)}</pre>
    </div>
    <div class="card">
      <button class="btn" id="btn-validate2">Validate</button>
    </div>
  `;
	document.getElementById("btn-validate2").onclick = async () => {
		const r = await apiPost("/api/run/validate", {});
		alert(r.output || "done");
	};
}

async function renderTools() {
	crumb.textContent = "Tools";
	view.innerHTML = `
    <div class="card">
      <div class="label">One-click tools (deterministic)</div>
      <div class="row">
        <button class="btn" id="t-start">Start/Resume</button>
        <button class="btn" id="t-status">Generate Status</button>
        <button class="btn" id="t-improve">Improve (No AI)</button>
        <button class="btn" id="t-export">Export ZIP</button>
        <button class="btn" id="t-import">Import ZIP</button>
      </div>
      <div class="small" style="margin-top:10px">Outputs appear as alerts for now; later we stream into a log console.</div>
    </div>
  `;
	const bind = (id, task) => {
		document.getElementById(id).onclick = async () => {
			const r = await apiPost(`/api/run/${task}`, {});
			alert(r.output || "done");
		};
	};
	bind("t-start", "start");
	bind("t-status", "status");
	bind("t-improve", "improve");
	bind("t-export", "export");
	bind("t-import", "import");
}

async function renderState() {
	crumb.textContent = "State";
	const state = await apiGet("/api/state");
	view.innerHTML = `
    <div class="card">
      <div class="label">.devmentor/state.json</div>
      <pre id="state-pre">${escapeHtml(JSON.stringify(state, null, 2))}</pre>
    </div>
    <div class="card">
      <div class="label">Quick edits</div>
      <div class="row">
        <button class="btn" id="reset">Reset to defaults</button>
      </div>
      <div class="small" style="margin-top:10px">Later: in-app editing + schema-guarded patching.</div>
    </div>
  `;
	document.getElementById("reset").onclick = async () => {
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
		await apiPost("/api/state", defaults);
		renderState();
	};
}

const routes = {
	dashboard: renderDashboard,
	tutorials: renderTutorials,
	challenges: renderChallenges,
	tools: renderTools,
	state: renderState,
};

document.querySelectorAll(".navbtn").forEach((btn) => {
	btn.onclick = () => {
		const v = btn.dataset.view;
		routes[v]();
	};
});

document.getElementById("btn-status").onclick = async () => {
	const r = await apiPost("/api/run/status", {});
	alert(r.output || "done");
};
document.getElementById("btn-export").onclick = async () => {
	const r = await apiPost("/api/run/export", {});
	alert(r.output || "done");
};
document.getElementById("btn-validate").onclick = async () => {
	const r = await apiPost("/api/run/validate", {});
	alert(r.output || "done");
};

routes.dashboard();
