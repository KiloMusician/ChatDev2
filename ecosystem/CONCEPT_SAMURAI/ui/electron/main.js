const { app, BrowserWindow, Tray, Menu, nativeImage, Notification, ipcMain, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

let mainWindow = null;
let tray = null;
let listenerProc = null;

// repo root: two levels up from ui/electron
const repoRoot = path.resolve(__dirname, '..', '..');

function createWindow() {
  if (mainWindow) {
    mainWindow.show();
    return;
  }

  mainWindow = new BrowserWindow({
    width: 800,
    height: 520,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });
}

function createTray() {
  let iconPath = path.join(__dirname, 'assets', 'icon.ico');
  let img = nativeImage.createFromPath(iconPath);
  if (img.isEmpty()) img = nativeImage.createEmpty();

  tray = new Tray(img);
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Open Dashboard', click: createWindow },
    { label: 'Toggle Listener', click: toggleListener },
    { label: 'Show Listener Status', click: showStatus },
    { type: 'separator' },
    { label: 'Exit', click: () => { app.quit(); } }
  ]);

  tray.setToolTip('Keeper');
  tray.setContextMenu(contextMenu);
  tray.on('double-click', createWindow);
}

function showStatus() {
  const statePath = path.join(repoRoot, 'state', 'listener.json');
  if (fs.existsSync(statePath)) {
    try {
      const content = fs.readFileSync(statePath, 'utf8');
      const obj = JSON.parse(content);
      new Notification({ title: 'Keeper - Listener', body: `Tracked: ${obj.process_name || 'unknown'}` }).show();
    } catch (e) {
      new Notification({ title: 'Keeper - Listener', body: 'Listener running (status unreadable)' }).show();
    }
  } else {
    new Notification({ title: 'Keeper - Listener', body: 'Listener not running' }).show();
  }
}

function toggleListener() {
  if (listenerProc) {
    try { listenerProc.kill(); } catch (e) { console.error(e); }
    listenerProc = null;
    new Notification({ title: 'Keeper', body: 'Listener stopped' }).show();
    return;
  }

  // Start the listener script via the repo's helper command
  const cmd = process.platform === 'win32' ? 'cmd.exe' : 'pwsh';
  const arg = process.platform === 'win32' ? ['/c', path.join(repoRoot, 'tools', 'keeper-listen.cmd')] : ['-NoProfile', '-File', path.join(repoRoot, 'keeper.ps1'), 'listen'];

  try {
    listenerProc = spawn(cmd, arg, { cwd: repoRoot, detached: false, shell: false });
    listenerProc.stdout.on('data', (d) => console.log(`[listener] ${d.toString()}`));
    listenerProc.stderr.on('data', (d) => console.error(`[listener-err] ${d.toString()}`));
    listenerProc.on('exit', (code, signal) => { console.log('listener exited', code, signal); listenerProc = null; });
    new Notification({ title: 'Keeper', body: 'Listener started' }).show();
  } catch (e) {
    console.error('Failed to start listener', e);
    new Notification({ title: 'Keeper', body: 'Failed to start listener' }).show();
  }
}

ipcMain.handle('get-listener-status', async () => {
  const statePath = path.join(repoRoot, 'state', 'listener.json');
  if (fs.existsSync(statePath)) {
    try { const content = fs.readFileSync(statePath, 'utf8'); return { running: true, state: JSON.parse(content) }; } catch (e) { return { running: true }; }
  } else {
    return { running: !!listenerProc };
  }
});

ipcMain.handle('toggle-listener', async () => { toggleListener(); return true; });
ipcMain.handle('open-file', async (ev, p) => { await shell.openPath(p); return true; });

app.whenReady().then(() => {
  createTray();
  createWindow();

  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

// Prevent app quit on Windows when windows are closed; keep tray running.
app.on('window-all-closed', (e) => {
  if (process.platform !== 'darwin') {
    e.preventDefault();
  }
});
