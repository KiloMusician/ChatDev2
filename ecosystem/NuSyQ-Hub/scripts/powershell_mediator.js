#!/usr/bin/env node
// Lightweight PSES supervisor: starts Start-EditorServices via pwsh and restarts on exit.
// Usage: node powershell_mediator.js --pwsh "C:\\Program Files\\PowerShell\\7\\pwsh.exe" --bundledModules "C:\\Users\\keath\\.vscode\\extensions\\ms-vscode.powershell-2025.4.0\\modules"

const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

const argv = require('minimist')(process.argv.slice(2));
const pwsh = argv.pwsh || 'C:\\Program Files\\PowerShell\\7\\pwsh.exe';
const bundledModules =
  argv.bundledModules ||
  path.join(
    process.env.USERPROFILE || '~',
    '.vscode',
    'extensions',
    'ms-vscode.powershell-2025.4.0',
    'modules'
  );
// Default mediator directory under workspace .vscode/mediator
const logDir = argv.logDir || path.join(process.cwd(), '.vscode', 'mediator');
const logPath = argv.log || path.join(logDir, 'mediator.log');
const sessionPath = argv.session || path.join(logDir, 'mediator.session.json');
const mediatorPidPath = argv.mediatorPid || path.join(logDir, 'mediator.pid');
const childPidPath = argv.childPid || path.join(logDir, 'child.pid');
const httpPort = argv.httpPort || 52101;
const httpPortPath = path.join(logDir, 'mediator.http.port');

let currentChild = null;

function log(msg) {
  const line = new Date().toISOString() + ' ' + msg + '\n';
  try {
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
  } catch (e) {}
  fs.appendFileSync(logPath, line);
  process.stdout.write(line);
}

function startPses() {
  log(`Starting PSES with pwsh: ${pwsh}`);

  // Ensure bundledModules exists; if not, attempt to locate the extension modules folder
  function resolveBundledModules() {
    try {
      if (fs.existsSync(bundledModules)) return bundledModules;
    } catch (e) {}
    // try to find ms-vscode.powershell-* under %USERPROFILE%/.vscode/extensions
    try {
      const extRoot = path.join(process.env.USERPROFILE || '', '.vscode', 'extensions');
      if (fs.existsSync(extRoot)) {
        const entries = fs.readdirSync(extRoot);
        for (const e of entries) {
          if (e.toLowerCase().startsWith('ms-vscode.powershell-')) {
            const candidate = path.join(extRoot, e, 'modules');
            if (fs.existsSync(candidate)) return candidate;
          }
        }
      }
    } catch (e) {}
    return null;
  }

  const resolvedBundled = resolveBundledModules();
  if (!resolvedBundled) {
    log(
      'Could not locate bundled PowerShellEditorServices modules. Mediator will not start PSES until modules are available.'
    );
    // avoid tight restart loop; try again in 30s
    setTimeout(() => startPses(), 30000);
    return;
  }

  log(`Using bundledModules path: ${resolvedBundled}`);
  // Compute the absolute path to the module PSD1 on the Node side and verify it exists
  const moduleAbsPath = path.join(
    resolvedBundled,
    'PowerShellEditorServices',
    'PowerShellEditorServices.psd1'
  );
  if (!fs.existsSync(moduleAbsPath)) {
    log(`PowerShellEditorServices psd1 not found at ${moduleAbsPath}. Will retry in 30s.`);
    // extra debug: list the resolvedBundled children
    try {
      const childList = fs.readdirSync(resolvedBundled).join(', ');
      log(`Contents of bundledModules (${resolvedBundled}): ${childList}`);
    } catch (e) {}
    setTimeout(() => startPses(), 30000);
    return;
  }

  // Create a temporary PowerShell launcher script to avoid quoting/escaping problems when using -Command
  const launcherScript = path.join(logDir, `start_editor_services_${Date.now()}.ps1`);
  const psLauncher = [];
  // Use absolute module path and absolute values to avoid Join-Path differences inside pwsh
  psLauncher.push(`$modulePath = '${moduleAbsPath.replace(/'/g, "''")}'`);
  psLauncher.push(`$bundled = '${resolvedBundled.replace(/'/g, "''")}'`);
  psLauncher.push(`$logDir = '${logDir.replace(/'/g, "''")}'`);
  psLauncher.push(`$sessionPath = '${sessionPath.replace(/'/g, "''")}'`);
  psLauncher.push(
    'if (-not (Test-Path $modulePath)) { Write-Error "PowerShellEditorServices module not found at $modulePath"; exit 2 }'
  );
  psLauncher.push('Import-Module -Name $modulePath -Force');
  psLauncher.push(
    "Start-EditorServices -BundledModulesPath $bundled -LogPath $logDir -LogLevel Trace -SessionDetailsPath $sessionPath -FeatureFlags @() -HostName 'Mediator' -HostProfileId 'mediator' -EnableConsoleRepl"
  );

  try {
    fs.writeFileSync(launcherScript, psLauncher.join('\n'), { encoding: 'utf8' });
    log(`Wrote temporary launcher script: ${launcherScript}`);
  } catch (e) {
    log('Failed to write launcher script: ' + e.message);
    setTimeout(() => startPses(), 10000);
    return;
  }

  let execPath = pwsh;
  try {
    if (!fs.existsSync(execPath)) {
      log(`pwsh not found at ${execPath}, falling back to 'pwsh' from PATH`);
      execPath = 'pwsh';
    }
  } catch (e) {
    execPath = 'pwsh';
  }

  const child = spawn(
    execPath,
    ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', launcherScript],
    {
      stdio: ['ignore', 'pipe', 'pipe'],
    }
  );
  currentChild = child;

  // Write child PID for external control
  try {
    fs.writeFileSync(childPidPath, String(child.pid), { encoding: 'utf8' });
    log(`Wrote child PID ${child.pid} to ${childPidPath}`);
  } catch (e) {
    log(`Failed to write child PID: ${e.message}`);
  }

  // Schedule cleanup of the temporary launcher script after the child starts
  try {
    // Attempt multiple removals in case the launcher is briefly locked by the child process.
    const maxAttempts = 6;
    const attemptDelay = 2000; // 2s between attempts
    let attempts = 0;
    const tryRemove = () => {
      attempts += 1;
      try {
        if (fs.existsSync(launcherScript)) {
          fs.unlinkSync(launcherScript);
          log(`Removed temporary launcher script: ${launcherScript}`);
          return;
        } else {
          // already gone
          return;
        }
      } catch (e) {
        log(`Attempt ${attempts}: Failed to remove temporary launcher script: ${e.message}`);
        if (attempts < maxAttempts) {
          setTimeout(tryRemove, attemptDelay);
        } else {
          log(`Giving up removing launcher script after ${attempts} attempts: ${launcherScript}`);
        }
      }
    };
    // start first attempt after a short delay to allow child to acquire any locks
    setTimeout(tryRemove, 3000);
  } catch (e) {
    log(`Failed to schedule launcher cleanup: ${e.message}`);
  }

  child.stdout.on('data', (data) => log(`[stdout] ${data.toString().trim()}`));
  child.stderr.on('data', (data) => log(`[stderr] ${data.toString().trim()}`));

  child.on('exit', (code, signal) => {
    try {
      fs.unlinkSync(childPidPath);
    } catch (e) {}
    // If exit code indicates module missing (2) or other early failure, backoff longer
    if (code === 2) {
      log(`PSES exited with code=${code} (module error). Backing off for 30s before retry.`);
      setTimeout(() => startPses(), 30000);
      return;
    }
    log(`PSES exited with code=${code} signal=${signal}. Restarting in 5s...`);
    setTimeout(() => startPses(), 5000);
  });
}

// Ensure log dir exists
try {
  fs.mkdirSync(path.dirname(logPath), { recursive: true });
} catch (e) {}

log('PSES mediator starting');
// Write mediator PID file and setup cleanup
try {
  fs.mkdirSync(path.dirname(logPath), { recursive: true });
} catch (e) {}

try {
  // If a PID file exists, check if that process is still running. If so, refuse to start to avoid multiple mediators.
  if (fs.existsSync(mediatorPidPath)) {
    try {
      const existing = fs.readFileSync(mediatorPidPath, 'utf8').trim();
      const existingPid = Number(existing);
      if (!Number.isNaN(existingPid) && existingPid > 0) {
        try {
          // signal 0 to test for process existence
          process.kill(existingPid, 0);
          log(`Existing mediator process detected with PID ${existingPid}; aborting startup.`);
          process.exit(0);
        } catch (e) {
          // process not found; remove stale PID file and continue
          try {
            fs.unlinkSync(mediatorPidPath);
            log(`Removed stale mediator PID file for PID ${existingPid}`);
          } catch (u) {}
        }
      }
    } catch (e) {}
  }
  fs.writeFileSync(mediatorPidPath, String(process.pid), { encoding: 'utf8' });
  log(`Wrote mediator PID ${process.pid} to ${mediatorPidPath}`);
} catch (e) {
  log(`Failed to write mediator PID: ${e.message}`);
}

process.on('exit', () => {
  try {
    fs.unlinkSync(mediatorPidPath);
  } catch (e) {}
  try {
    fs.unlinkSync(childPidPath);
  } catch (e) {}
  try {
    fs.unlinkSync(httpPortPath);
  } catch (e) {}
});

process.on('SIGINT', () => process.exit(0));
process.on('SIGTERM', () => process.exit(0));

// Ensure we cleanup if an unexpected error occurs
process.on('uncaughtException', (err) => {
  log('Uncaught exception: ' + (err && err.stack ? err.stack : String(err)));
  try {
    if (currentChild && !currentChild.killed) {
      try {
        currentChild.kill();
      } catch (e) {}
    }
  } catch (e) {}
  try {
    if (fs.existsSync(mediatorPidPath)) fs.unlinkSync(mediatorPidPath);
  } catch (e) {}
  try {
    if (fs.existsSync(childPidPath)) fs.unlinkSync(childPidPath);
  } catch (e) {}
  try {
    if (fs.existsSync(httpPortPath)) fs.unlinkSync(httpPortPath);
  } catch (e) {}
  // rethrow after a short delay to allow logs to flush
  setTimeout(() => process.exit(1), 200);
});

process.on('beforeExit', () => {
  try {
    if (currentChild && !currentChild.killed) {
      try {
        currentChild.kill();
      } catch (e) {}
    }
  } catch (e) {}
  try {
    if (fs.existsSync(mediatorPidPath)) fs.unlinkSync(mediatorPidPath);
  } catch (e) {}
  try {
    if (fs.existsSync(childPidPath)) fs.unlinkSync(childPidPath);
  } catch (e) {}
  try {
    if (fs.existsSync(httpPortPath)) fs.unlinkSync(httpPortPath);
  } catch (e) {}
});

// Start a tiny HTTP control server for status and graceful stop
function startHttpServer() {
  const server = http.createServer((req, res) => {
    if (req.method === 'GET' && req.url === '/status') {
      const status = {
        mediatorPid: process.pid,
        childPid: (() => {
          try {
            return fs.existsSync(childPidPath)
              ? fs.readFileSync(childPidPath, 'utf8').trim()
              : null;
          } catch (e) {
            return null;
          }
        })(),
        sessionPath,
        logPath,
      };
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(status));
      return;
    }

    if ((req.method === 'POST' || req.method === 'GET') && req.url === '/stop-child') {
      // attempt graceful kill of the child
      let childPid = null;
      try {
        childPid = fs.existsSync(childPidPath)
          ? fs.readFileSync(childPidPath, 'utf8').trim()
          : null;
      } catch (e) {}
      if (currentChild && !currentChild.killed) {
        try {
          currentChild.kill();
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ stopped: true, method: 'kill', pid: currentChild.pid }));
          log(`Requested currentChild.kill() for pid ${currentChild.pid}`);
          return;
        } catch (e) {
          log('currentChild.kill() failed: ' + e.message);
        }
      }
      if (childPid) {
        // fallback to taskkill on Windows
        exec(`taskkill /PID ${childPid} /T /F`, (err, stdout, stderr) => {
          if (err) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ stopped: false, error: err.message }));
            log('taskkill failed: ' + err.message);
            return;
          }
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ stopped: true, method: 'taskkill', pid: childPid }));
          log(`taskkill succeeded for pid ${childPid}`);
        });
        return;
      }
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ stopped: false, reason: 'no-child' }));
      return;
    }

    res.writeHead(404);
    res.end('Not found');
  });

  server.on('error', (e) => log('HTTP server error: ' + e.message));
  server.listen(httpPort, '127.0.0.1', () => {
    log(`HTTP control server listening on http://127.0.0.1:${httpPort}`);
    try {
      // write atomically: write to temp then rename
      const tmp = httpPortPath + '.tmp';
      fs.writeFileSync(tmp, String(httpPort), 'utf8');
      fs.renameSync(tmp, httpPortPath);
    } catch (e) {
      log('Failed to write http port file: ' + e.message);
    }
  });
}

startHttpServer();

startPses();
