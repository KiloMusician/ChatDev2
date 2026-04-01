const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

/**
 * Activate the extension
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  const openCommand = vscode.commands.registerCommand('agentDashboard.open', () => {
    AgentDashboardPanel.createOrShow(context.extensionUri);
  });

  const refreshCommand = vscode.commands.registerCommand('agentDashboard.refresh', () => {
    AgentDashboardPanel.refresh();
  });

  context.subscriptions.push(openCommand, refreshCommand);
}

class AgentDashboardPanel {
  static currentPanel = null;

  static createOrShow(extensionUri) {
    const column = vscode.window.activeTextEditor
      ? vscode.window.activeTextEditor.viewColumn
      : vscode.ViewColumn.One;

    if (AgentDashboardPanel.currentPanel) {
      AgentDashboardPanel.currentPanel.panel.reveal(column);
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      'agentDashboard',
      'NuSyQ Agent Dashboard',
      column,
      {
        enableScripts: true,
        localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'media')],
      }
    );

    AgentDashboardPanel.currentPanel = new AgentDashboardPanel(panel, extensionUri);
  }

  static refresh() {
    if (AgentDashboardPanel.currentPanel) AgentDashboardPanel.currentPanel.update();
  }

  constructor(panel, extensionUri) {
    this.panel = panel;
    this.extensionUri = extensionUri;

    this._disposables = [];

    // Set initial HTML
    this.panel.webview.html = this._getHtmlForWebview(this.panel.webview);

    // Message handling
    this.panel.webview.onDidReceiveMessage(
      async (message) => {
        if (message.command === 'requestData') {
          const data = await this._gatherData();
          this.panel.webview.postMessage({ command: 'initialData', payload: data });
        } else if (message.command === 'openFile' && message.path) {
          const uri = vscode.Uri.file(message.path);
          vscode.window.showTextDocument(uri);
        } else if (message.command === 'attemptAutofix') {
          try {
            const root = (vscode.workspace.workspaceFolders || [])[0].uri.fsPath;
            const repairPath = path.join(root, 'state', 'repair_requests.json');
            let arr = [];
            if (fs.existsSync(repairPath)) {
              try {
                arr = JSON.parse(fs.readFileSync(repairPath, 'utf8') || '[]');
              } catch (e) {
                arr = [];
              }
            }
            arr.push({
              action: 'rehydrate',
              circuitId: message.circuitId || null,
              requestedBy: 'agent-dashboard',
            });
            fs.writeFileSync(repairPath, JSON.stringify(arr, null, 2), 'utf8');
            vscode.window.showInformationMessage('Repair request submitted.');
          } catch (e) {
            vscode.window.showErrorMessage('Failed to submit repair request: ' + String(e));
          }
        }
      },
      null,
      this._disposables
    );

    // Watch files for changes and push updates
    const workspaceFolders = vscode.workspace.workspaceFolders || [];
    if (workspaceFolders.length > 0) {
      const root = workspaceFolders[0].uri.fsPath;
      this._watchPaths = [
        path.join(root, 'state', 'unified_errors.json'),
        path.join(root, 'src', 'Rosetta_Quest_System', 'quest_log.jsonl'),
        path.join(root, 'tools', 'agent_dashboard', 'status.json'),
      ];

      this._watchers = this._watchPaths
        .map((p) => {
          try {
            return fs.watch(p, { persistent: false }, async () => {
              const data = await this._gatherData();
              this.panel.webview.postMessage({ command: 'update', payload: data });
            });
          } catch (e) {
            return null;
          }
        })
        .filter(Boolean);
    }

    this.panel.onDidDispose(() => this.dispose(), null, this._disposables);
  }

  dispose() {
    AgentDashboardPanel.currentPanel = null;
    this._disposables.forEach((d) => d && d.dispose && d.dispose());
    if (this._watchers) this._watchers.forEach((w) => w && w.close && w.close());
  }

  async _gatherData() {
    const workspaceFolders = vscode.workspace.workspaceFolders || [];
    const root = workspaceFolders.length ? workspaceFolders[0].uri.fsPath : undefined;
    const result = { agents: [], quests: [], errors: null };

    if (!root) return result;

    // Read status.json if present
    try {
      const statusPath = path.join(root, 'tools', 'agent_dashboard', 'status.json');
      if (fs.existsSync(statusPath)) {
        const s = fs.readFileSync(statusPath, 'utf8');
        result.agents = JSON.parse(s);
      }
    } catch (e) {
      // ignore
    }

    // Read unified_errors.json
    try {
      const errPath = path.join(root, 'state', 'unified_errors.json');
      if (fs.existsSync(errPath)) {
        const s = fs.readFileSync(errPath, 'utf8');
        result.errors = JSON.parse(s);
      }
    } catch (e) {
      // ignore
    }

    // Read quest_log.jsonl
    try {
      const qPath = path.join(root, 'src', 'Rosetta_Quest_System', 'quest_log.jsonl');
      if (fs.existsSync(qPath)) {
        const contents = fs.readFileSync(qPath, 'utf8');
        const lines = contents.split(/\r?\n/).filter(Boolean);
        result.quests = lines.map((l) => {
          try {
            return JSON.parse(l);
          } catch (e) {
            return { raw: l };
          }
        });
      }
    } catch (e) {
      // ignore
    }

    return result;
  }

  _getHtmlForWebview(webview) {
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, 'media', 'main.js')
    );
    const styleUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, 'media', 'main.css')
    );

    return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="${styleUri}" rel="stylesheet" />
  <title>NuSyQ Agent Dashboard</title>
</head>
<body>
  <div id="root">
    <header>
      <h1>NuSyQ Agent Dashboard</h1>
      <div class="controls">
        <button id="refresh">Refresh</button>
                <button id="attemptFix">Attempt Auto-fix Latest</button>
      </div>
    </header>
    <section id="agents" class="panel">
      <h2>Agents</h2>
      <div id="agents-list">Loading...</div>
    </section>
    <section id="quests" class="panel">
      <h2>Quests</h2>
      <div id="quests-list">Loading...</div>
    </section>
    <section id="errors" class="panel">
      <h2>Unified Errors</h2>
      <pre id="errors-list">Loading...</pre>
    </section>
  </div>
  <script src="${scriptUri}"></script>
          <script>
            document.getElementById('attemptFix').addEventListener('click', () => {
              vscode.postMessage({ command: 'attemptAutofix', circuitId: null });
            });
          </script>
</body>
</html>`;
  }
}

function deactivate() {}

module.exports = { activate, deactivate };
const vscode = require('vscode');

// track open dashboard panels so we can push updates
const panels = [];

async function readJsonFile(uri) {
  try {
    const bytes = await vscode.workspace.fs.readFile(uri);
    return JSON.parse(Buffer.from(bytes).toString('utf8'));
  } catch (e) {
    return null;
  }
}

async function readJsonlFile(uri) {
  try {
    const bytes = await vscode.workspace.fs.readFile(uri);
    const txt = Buffer.from(bytes).toString('utf8');
    return txt
      .split(/\r?\n/)
      .filter(Boolean)
      .map((l) => JSON.parse(l));
  } catch (e) {
    return null;
  }
}

/**
 * Activate extension
 * Registers commands and watchers.
 */
function activate(context) {
  const openCmd = vscode.commands.registerCommand('agentDashboard.open', async () => {
    const panel = vscode.window.createWebviewPanel(
      'agentDashboard',
      'NuSyQ Agent Dashboard',
      vscode.ViewColumn.One,
      { enableScripts: true, retainContextWhenHidden: true }
    );

    panels.push(panel);
    panel.onDidDispose(() => {
      const idx = panels.indexOf(panel);
      if (idx !== -1) panels.splice(idx, 1);
    });

    // initial load
    await pushCurrentStateToPanel(panel, context);

    // message handler
    panel.webview.onDidReceiveMessage(
      async (message) => {
        const wf = (vscode.workspace.workspaceFolders || [])[0];
        if (message.command === 'refresh') {
          await pushCurrentStateToPanel(panel, context);
        } else if (message.command === 'runErrorReport') {
          await runTaskByLabel([
            'NuSyQ: Unified Error Report',
            'NuSyQ: Unified Error Report (Split Full)',
          ]);
        } else if (message.command === 'runSnapshot') {
          await runTaskByLabel(['NuSyQ: Snapshot (Spine Lens)', 'NuSyQ: Activate Ecosystem']);
        } else if (message.command === 'openFile') {
          try {
            const uri = vscode.Uri.file(message.payload);
            const doc = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(doc, { preview: true });
          } catch (e) {
            vscode.window.showErrorMessage('Failed to open file: ' + String(e));
          }
        }
      },
      undefined,
      context.subscriptions
    );
  });
  context.subscriptions.push(openCmd);

  // lightweight refresh command
  context.subscriptions.push(
    vscode.commands.registerCommand('agentDashboard.refresh', async () => {
      for (const p of panels) await pushCurrentStateToPanel(p, context);
      vscode.window.showInformationMessage('Agent Dashboard refreshed.');
    })
  );

  // run unified error report from tasks
  context.subscriptions.push(
    vscode.commands.registerCommand('agentDashboard.runErrorReport', async () => {
      await runTaskByLabel([
        'NuSyQ: Unified Error Report',
        'NuSyQ: Unified Error Report (Split Full)',
      ]);
    })
  );

  // file watchers for live updates
  try {
    const folder = (vscode.workspace.workspaceFolders || [])[0];
    if (folder) {
      const statusPattern = new vscode.RelativePattern(folder, 'tools/agent_dashboard/status.json');
      const questPattern = new vscode.RelativePattern(
        folder,
        'src/Rosetta_Quest_System/quest_log.jsonl'
      );
      const unifiedPattern = new vscode.RelativePattern(folder, 'state/unified_errors.json');

      const statusWatcher = vscode.workspace.createFileSystemWatcher(statusPattern);
      const questWatcher = vscode.workspace.createFileSystemWatcher(questPattern);
      const unifiedWatcher = vscode.workspace.createFileSystemWatcher(unifiedPattern);

      const notify = async () => {
        const bytes = await Promise.all(panels.map((p) => pushCurrentStateToPanel(p, context)));
      };

      statusWatcher.onDidChange(notify, null, context.subscriptions);
      statusWatcher.onDidCreate(notify, null, context.subscriptions);
      statusWatcher.onDidDelete(notify, null, context.subscriptions);

      questWatcher.onDidChange(notify, null, context.subscriptions);
      questWatcher.onDidCreate(notify, null, context.subscriptions);
      questWatcher.onDidDelete(notify, null, context.subscriptions);

      unifiedWatcher.onDidChange(notify, null, context.subscriptions);
      unifiedWatcher.onDidCreate(notify, null, context.subscriptions);
      unifiedWatcher.onDidDelete(notify, null, context.subscriptions);

      context.subscriptions.push(statusWatcher, questWatcher, unifiedWatcher);
    }
  } catch (e) {
    // ignore watcher creation errors
  }
}

function deactivate() {}

async function pushCurrentStateToPanel(panel, context) {
  const wf = (vscode.workspace.workspaceFolders || [])[0];
  if (!wf) {
    panel.webview.postMessage({ command: 'error', payload: 'No workspace folder open.' });
    return;
  }

  const folder = wf.uri;
  // read source files (best-effort)
  const statusUri = vscode.Uri.joinPath(folder, 'tools', 'agent_dashboard', 'status.json');
  const unifiedUri = vscode.Uri.joinPath(folder, 'state', 'unified_errors.json');
  const questUri = vscode.Uri.joinPath(folder, 'src', 'Rosetta_Quest_System', 'quest_log.jsonl');

  const [status, unified, quests] = await Promise.all([
    readJsonFile(statusUri),
    readJsonFile(unifiedUri),
    readJsonlFile(questUri),
  ]);

  const parsed = {
    agents: (status && status.agents) || [],
    questsSummary: summarizeQuests(quests),
    errors: unified || null,
    rawStatus: status || null,
  };

  panel.webview.html = getWebviewContent(panel.webview, context.extensionUri, parsed);
  panel.webview.postMessage({ command: 'update', payload: parsed });
}

function summarizeQuests(quests) {
  if (!quests) return { totals: {}, active: [] };
  const byId = new Map();
  for (const ev of quests) {
    if (!ev.details || !ev.details.id) continue;
    byId.set(ev.details.id, ev.details);
  }
  const totals = { pending: 0, active: 0, complete: 0, other: 0 };
  for (const q of byId.values()) {
    const s = (q.status || 'unknown').toLowerCase();
    if (s === 'pending' || s === 'pending') totals.pending++;
    else if (s === 'active') totals.active++;
    else if (s === 'completed' || s === 'complete') totals.complete++;
    else totals.other++;
  }
  const active = Array.from(byId.values())
    .filter((q) => (q.status || '').toLowerCase() === 'active')
    .slice(0, 6);
  return { totals, active };
}

async function runTaskByLabel(labels) {
  try {
    const tasks = await vscode.tasks.fetchTasks();
    const candidate = tasks.find(
      (t) => labels.includes(t.name) || labels.includes(t.definition && t.definition.label)
    );
    if (!candidate) {
      vscode.window.showErrorMessage('No matching task found: ' + labels.join(', '));
      return;
    }
    await vscode.tasks.executeTask(candidate);
    vscode.window.showInformationMessage(
      'Started task: ' + (candidate.name || candidate.definition.label)
    );
  } catch (e) {
    vscode.window.showErrorMessage('Failed to run task: ' + String(e));
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]);
}

function getWebviewContent(webview, extensionUri, data) {
  const nonce = getNonce();
  const agents = data && data.agents ? data.agents : [];
  const qs = data && data.questsSummary ? data.questsSummary : { totals: {}, active: [] };
  const errors = data && data.errors ? data.errors : null;

  const agentsHtml = agents.length
    ? `<table style="width:100%;border-collapse:collapse"><thead><tr><th style="text-align:left">Agent</th><th>Status</th><th>Last seen</th></tr></thead><tbody>${agents
        .map(
          (a) =>
            `<tr><td>${escapeHtml(a.name || '')}</td><td>${escapeHtml(a.status || '')}</td><td>${escapeHtml(a.last_seen || '')}</td></tr>`
        )
        .join('')}</tbody></table>`
    : '<p>No agent status available.</p>';

  const activeQuestsHtml = qs.active.length
    ? `<ul>${qs.active.map((q) => `<li><strong>${escapeHtml(q.title || q.id || '')}</strong> — ${escapeHtml(q.description ? q.description.split('\n')[0] : '')}</li>`).join('')}</ul>`
    : '<p>No active quests.</p>';

  // Build a detailed errors list with per-error auto-fix buttons when available
  let errorSummaryHtml;
  if (!errors) {
    errorSummaryHtml = '<p>No unified error report found.</p>';
  } else {
    const totalsHtml = `<div><strong>Totals:</strong> Errors: ${errors.totals.errors}, Warnings: ${errors.totals.warnings}, Total: ${errors.totals.total}</div>`;
    const sourcesHtml = `<div style="margin-top:8px"><strong>Sources:</strong><ul>${(
      errors.sources || []
    )
      .map((s) => `<li>${escapeHtml(s.source)} — errors:${s.errors} warnings:${s.warnings}</li>`)
      .join('')}</ul></div>`;

    // Render an interactive per-error list if errors.list exists (array of error entries)
    const perErrorList =
      errors.list && errors.list.length
        ? `<div style="margin-top:10px"><strong>Errors:</strong><ul>${errors.list
            .map((e, idx) => {
              const id = escapeHtml(e.id || e.circuitId || 'err-' + idx);
              const title = escapeHtml(e.title || e.message || JSON.stringify(e).slice(0, 120));
              const circuitId = escapeHtml(e.circuitId || '');
              const fixBtn = circuitId
                ? `<button class="attempt-fix-btn" data-circuit-id="${circuitId}">Attempt Auto-fix</button>`
                : '';
              return `<li style="margin-bottom:6px"><strong>${title}</strong> <div style="font-size:0.9em;color:var(--vscode-descriptionForeground);">source: ${escapeHtml(e.source || '')} — type: ${escapeHtml(e.type || '')}</div>${fixBtn}</li>`;
            })
            .join('')}</ul></div>`
        : '<p>No detailed errors available.</p>';

    errorSummaryHtml = totalsHtml + sourcesHtml + perErrorList;
  }

  return `<!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NuSyQ Agent Dashboard</title>
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 16px; color: var(--vscode-foreground); background: var(--vscode-editor-background);}
      h1 { margin: 0 0 8px 0 }
      .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px }
      .card { background: var(--vscode-panel-background); padding: 12px; border-radius: 8px; box-shadow: var(--vscode-widget-shadow); }
      table { width:100%; }
      th, td { padding:6px 8px; border-bottom:1px solid rgba(0,0,0,0.06) }
      button { margin-right:8px }
    </style>
  </head>
  <body>
    <h1>NuSyQ Agent Dashboard</h1>
    <div style="margin-bottom:12px">
      <button id="refresh">Refresh</button>
      <button id="runError">Run Unified Error Report</button>
      <button id="runSnapshot">Run System Snapshot</button>
      <button id="openErrors">Open Unified Error File</button>
      <button id="attemptFix">Attempt Auto-fix Latest</button>
    </div>

    <div class="grid">
      <div class="card">
        <h2>Agents</h2>
        ${agentsHtml}
      </div>

      <div class="card">
        <h2>Error Summary</h2>
        ${errorSummaryHtml}
      </div>

      <div class="card" style="grid-column:1/3">
        <h2>Quest Progress</h2>
        <div><strong>Totals:</strong> pending: ${qs.totals.pending || 0}, active: ${qs.totals.active || 0}, complete: ${qs.totals.complete || 0}</div>
        <h3 style="margin-top:8px">Active Quests</h3>
        ${activeQuestsHtml}
      </div>
    </div>

    <script nonce="${nonce}">
      const vscode = acquireVsCodeApi();
      document.getElementById('refresh').addEventListener('click', () => vscode.postMessage({ command: 'refresh' }));
      document.getElementById('runError').addEventListener('click', () => vscode.postMessage({ command: 'runErrorReport' }));
      document.getElementById('runSnapshot').addEventListener('click', () => vscode.postMessage({ command: 'runSnapshot' }));
      document.getElementById('openErrors').addEventListener('click', () => vscode.postMessage({ command: 'openFile', payload: '${vscode.Uri.joinPath(vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri : { path: '' }, 'state', 'unified_errors.json').fsPath}' }));
      document.getElementById('attemptFix').addEventListener('click', () => vscode.postMessage({ command: 'attemptAutofix', circuitId: null }));

      // Delegate clicks for per-error Attempt Auto-fix buttons
      document.addEventListener('click', (ev) => {
        const t = ev.target;
        if (t && t.classList && t.classList.contains('attempt-fix-btn')) {
          const circuitId = t.getAttribute('data-circuit-id') || null;
          vscode.postMessage({ command: 'attemptAutofix', circuitId });
        }
      });

      window.addEventListener('message', event => {
        const msg = event.data;
        if (msg.command === 'update') {
          // full update posted by extension — could be used to animate or show incremental changes
          console.log('dashboard update', msg.payload);
        } else if (msg.command === 'error') {
          console.error(msg.payload);
        }
      });
    </script>
  </body>
  </html>`;
}

function getNonce() {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) text += possible.charAt(Math.floor(Math.random() * possible.length));
  return text;
}

module.exports = { activate, deactivate };
