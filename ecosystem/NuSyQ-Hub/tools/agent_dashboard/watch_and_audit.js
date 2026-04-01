const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname);
const auditPs = path.join(root, 'terminal_audit.ps1');
const extensionsPs = path.join(root, 'extensions_audit.ps1');
const statusPath = path.join(root, 'status.json');

function runPowerShell(scriptPath) {
  return new Promise((resolve, reject) => {
    const ps = spawn('pwsh', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', scriptPath], {
      windowsHide: true,
    });
    let out = '';
    let err = '';
    ps.stdout.on('data', (d) => (out += d.toString()));
    ps.stderr.on('data', (d) => (err += d.toString()));
    ps.on('close', (code) => {
      if (code === 0) resolve({ out, err });
      else reject(new Error(`exit ${code}: ${err}`));
    });
  });
}

async function runAll() {
  try {
    await runPowerShell(auditPs);
  } catch (e) {
    console.error('Audit failed:', e.message);
  }
  try {
    await runPowerShell(extensionsPs);
  } catch (e) {
    // not fatal
  }
}

// initial run
runAll().catch(() => {});

// watch for filesystem events under the tools/agent_dashboard directory
fs.watch(root, { persistent: true }, (eventType, filename) => {
  if (!filename) return;
  if (
    filename.endsWith('.log') ||
    filename === 'quests.json' ||
    filename === 'status.example.json'
  ) {
    // re-run audit on relevant changes
    runAll().catch(() => {});
  }
});

// periodic run every 30 seconds
setInterval(() => {
  runAll().catch(() => {});
}, 30000);

console.log('watch_and_audit running — monitoring', root);
