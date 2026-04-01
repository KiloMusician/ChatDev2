const vscode = require('vscode');
const path = require('node:path');
const fs = require('node:fs');

let logPanel;
let logWatcher;

function activate(context) {
  const startParty = vscode.commands.registerCommand('startChatDevParty', () => {
    launchScript('src/tools/ChatDev-Party-System.py');
  });

  const launchTask = vscode.commands.registerCommand('launchChatDevTask', () => {
    launchScript('src/integration/chatdev_launcher.py');
  });

  context.subscriptions.push(startParty, launchTask);
}

function launchScript(scriptRelativePath) {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders) {
    vscode.window.showErrorMessage('No workspace folder open.');
    return;
  }
  const scriptPath = path.join(workspaceFolders[0].uri.fsPath, scriptRelativePath); // workspace-local trusted path # nosemgrep
  const terminal = vscode.window.createTerminal('ChatDev');
  terminal.show(true);
  terminal.sendText(`python "${scriptPath}"`);
  showLogPanel();
}

function showLogPanel() {
  if (logPanel) {
    logPanel.reveal(vscode.ViewColumn.Beside);
    return;
  }
  logPanel = vscode.window.createWebviewPanel('chatdevLogs', 'ChatDev Logs', vscode.ViewColumn.Beside, {
    enableScripts: true
  });
  logPanel.onDidDispose(() => {
    logPanel = undefined;
    if (logWatcher) {
      logWatcher.close();
      logWatcher = undefined;
    }
  });
  logPanel.webview.html = getWebviewContent();

  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders) {
    return;
  }
  const logFile = path.join(workspaceFolders[0].uri.fsPath, 'logs', 'chatdev.log');
  if (fs.existsSync(logFile)) {
    const sendData = () => {
      fs.readFile(logFile, 'utf8', (err, data) => {
        if (!err && logPanel) {
          logPanel.webview.postMessage({
            type: 'update',
            value: data,
            updatedAt: new Date().toISOString(),
          });
        }
      });
    };
    sendData();
    logWatcher = fs.watch(logFile, sendData);
  } else {
    logPanel.webview.postMessage({
      type: 'update',
      value: `Waiting for log file at ${logFile}`,
      updatedAt: new Date().toISOString(),
    });
  }
}

function getWebviewContent() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: var(--vscode-font-family);
      color: var(--vscode-foreground);
      background:
        radial-gradient(circle at top right, color-mix(in srgb, var(--vscode-button-background) 14%, transparent), transparent 34%),
        linear-gradient(180deg, color-mix(in srgb, var(--vscode-editor-background) 92%, white), var(--vscode-editor-background));
      margin: 0;
      padding: 16px;
    }
    .shell {
      max-width: 1200px;
      margin: 0 auto;
    }
    .hero {
      display: grid;
      grid-template-columns: minmax(220px, 1.2fr) minmax(220px, 1fr);
      gap: 14px;
      padding: 16px;
      border: 1px solid var(--vscode-panel-border);
      border-radius: 14px;
      background: color-mix(in srgb, var(--vscode-editor-background) 84%, white);
      margin-bottom: 16px;
    }
    .hero h1 {
      margin: 0 0 8px;
      font-size: 22px;
    }
    .hero p, .meta {
      margin: 0;
      opacity: 0.8;
      line-height: 1.45;
      font-size: 12px;
    }
    .metrics {
      display: grid;
      grid-template-columns: repeat(2, minmax(110px, 1fr));
      gap: 10px;
    }
    .metric {
      border: 1px solid var(--vscode-panel-border);
      border-radius: 10px;
      padding: 10px;
      background: color-mix(in srgb, var(--vscode-editor-background) 90%, white);
    }
    .metric span {
      display: block;
      font-size: 11px;
      text-transform: uppercase;
      opacity: 0.78;
    }
    .metric strong {
      display: block;
      font-size: 20px;
      margin-top: 6px;
    }
    .toolbar {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }
    button {
      border: 1px solid var(--vscode-button-border, transparent);
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      padding: 8px 12px;
      border-radius: 8px;
      cursor: pointer;
    }
    button:hover {
      background: var(--vscode-button-hoverBackground);
    }
    pre {
      margin: 0;
      padding: 14px;
      border: 1px solid var(--vscode-panel-border);
      border-radius: 12px;
      background: color-mix(in srgb, var(--vscode-editor-background) 88%, black);
      white-space: pre-wrap;
      word-break: break-word;
      font-family: var(--vscode-editor-font-family, Consolas, monospace);
      font-size: 12px;
      line-height: 1.45;
      min-height: 360px;
      max-height: 70vh;
      overflow: auto;
    }
    @media (max-width: 900px) {
      .hero, .metrics {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="hero">
      <div>
        <h1>ChatDev Log Console</h1>
        <p>
          Lightweight log view for the standalone ChatDev launcher. Use the mediator cockpit for the broader
          control plane; use this panel when you want a focused stream on ChatDev runtime output.
        </p>
      </div>
      <div class="metrics">
        <div class="metric"><span>Status</span><strong id="status">waiting</strong></div>
        <div class="metric"><span>Lines</span><strong id="lineCount">0</strong></div>
        <div class="metric"><span>Last Update</span><strong id="updatedAt">n/a</strong></div>
        <div class="metric"><span>Auto-Scroll</span><strong id="autoscrollState">on</strong></div>
      </div>
    </div>
    <div class="toolbar">
      <button id="toggleScroll">Toggle Auto-Scroll</button>
    </div>
    <div class="meta">Source: logs/chatdev.log</div>
    <pre id="log">Waiting for ChatDev output…</pre>
  </div>
  <script>
    const vscode = acquireVsCodeApi();
    let autoScroll = true;
    const logEl = document.getElementById('log');
    const statusEl = document.getElementById('status');
    const lineCountEl = document.getElementById('lineCount');
    const updatedAtEl = document.getElementById('updatedAt');
    const autoScrollEl = document.getElementById('autoscrollState');
    document.getElementById('toggleScroll').addEventListener('click', () => {
      autoScroll = !autoScroll;
      autoScrollEl.textContent = autoScroll ? 'on' : 'off';
    });
    window.addEventListener('message', event => {
      const { type, value, updatedAt } = event.data;
      if (type === 'update') {
        logEl.textContent = value;
        lineCountEl.textContent = String(value.split(/\\r?\\n/).filter(Boolean).length);
        statusEl.textContent = value.startsWith('Waiting for log file') ? 'waiting' : 'streaming';
        updatedAtEl.textContent = updatedAt ? new Date(updatedAt).toLocaleTimeString() : 'n/a';
        if (autoScroll) {
          logEl.scrollTop = logEl.scrollHeight;
        }
      }
    });
  </script>
</body>
</html>`;
}

function deactivate() {
  if (logWatcher) {
    logWatcher.close();
    logWatcher = undefined;
  }
}

module.exports = { activate, deactivate };
