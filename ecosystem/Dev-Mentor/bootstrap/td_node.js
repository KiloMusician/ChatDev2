#!/usr/bin/env node
/**
 * Terminal Depths — Node.js Quickstart
 * ════════════════════════════════════════════════════════════════════════════
 * Universal entry point for Node.js environments: VS Code extensions,
 * GitHub Actions, Docker containers, Electron apps, and any Node runtime.
 *
 * Requirements: Node.js 14+ (uses built-in fetch in 18+, or http module)
 *
 * Usage:
 *   node bootstrap/td_node.js
 *   TD_URL=https://my.replit.app node bootstrap/td_node.js
 *   TD_AGENT_NAME="Copilot" TD_AGENT_TYPE="copilot" node bootstrap/td_node.js
 *   echo "ls" | node bootstrap/td_node.js
 *   node -e "require('./bootstrap/td_node').runCommand('help').then(console.log)"
 * ════════════════════════════════════════════════════════════════════════════
 */

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const os = require('os');

// ── Config ──────────────────────────────────────────────────────────────────
const TD_URL = (process.env.TD_URL || 'http://localhost:5000').replace(/\/$/, '');
const TOKEN_FILE = process.env.TD_TOKEN_FILE || path.join(os.homedir(), '.td_token');
const AGENT_NAME = process.env.TD_AGENT_NAME || '';
const AGENT_TYPE = process.env.TD_AGENT_TYPE || 'custom';
const NO_COLOR = process.env.TD_NO_COLOR || !process.stdout.isTTY;

// ── ANSI Colors ──────────────────────────────────────────────────────────────
const c = (code, text) => NO_COLOR ? text : `\x1b[${code}m${text}\x1b[0m`;
const green   = t => c('32', t);
const cyan    = t => c('36', t);
const dim     = t => c('2', t);
const red     = t => c('31', t);
const yellow  = t => c('33', t);
const magenta = t => c('35', t);
const bold    = t => c('1', t);

const typeColor = {
  lore: magenta, system: cyan, success: green, error: red,
  warn: yellow, xp: green, story: magenta, dim, info: t => t,
};

// ── HTTP client (works Node 14+ without fetch) ───────────────────────────────
function request(method, urlStr, body, token) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const lib = url.protocol === 'https:' ? https : http;
    const data = body ? JSON.stringify(body) : null;
    const headers = { 'Content-Type': 'application/json', 'User-Agent': 'td-node/1.0' };
    if (token) headers['X-Agent-Token'] = token;
    if (data) headers['Content-Length'] = Buffer.byteLength(data);

    const req = lib.request({
      hostname: url.hostname, port: url.port, path: url.pathname + url.search,
      method, headers,
    }, res => {
      let chunks = '';
      res.on('data', d => chunks += d);
      res.on('end', () => {
        try { resolve(JSON.parse(chunks)); }
        catch { resolve({ error: chunks }); }
      });
    });
    req.on('error', err => resolve({ error: err.message }));
    if (data) req.write(data);
    req.end();
  });
}

const post = (path, body, token) => request('POST', `${TD_URL}${path}`, body, token);
const get  = (path, token) => request('GET', `${TD_URL}${path}`, null, token);

// ── Output rendering ─────────────────────────────────────────────────────────
function renderOutput(output) {
  if (!Array.isArray(output)) return;
  for (const line of output) {
    if (typeof line === 'string') { console.log(line); continue; }
    const text = line.s || '';
    const fn = typeColor[line.t] || (t => t);
    console.log(fn(text));
  }
}

// ── Token persistence ─────────────────────────────────────────────────────────
function saveToken(token, agentId, name) {
  try {
    fs.writeFileSync(TOKEN_FILE, JSON.stringify({ token, agent_id: agentId, name, server: TD_URL }));
  } catch {}
}

function loadToken() {
  try {
    if (fs.existsSync(TOKEN_FILE)) {
      const data = JSON.parse(fs.readFileSync(TOKEN_FILE, 'utf8'));
      if (data.server === TD_URL) return data;
    }
  } catch {}
  return null;
}

// ── Registration ──────────────────────────────────────────────────────────────
async function registerOrLoad(promptName) {
  const saved = loadToken();
  if (saved?.token) {
    const profile = await get('/api/agent/profile', saved.token);
    if (!profile.error) {
      console.log(green(`  Loaded identity: ${saved.name}`));
      return saved;
    }
  }

  const name = AGENT_NAME || promptName || os.userInfo().username || 'agent';
  const hostname = os.hostname().toLowerCase().replace(/[^a-z0-9]/g, '-');
  const email = `${name.toLowerCase().replace(/\s+/g, '_')}@${hostname}.terminal-depths`;

  const result = await post('/api/agent/register', { name, email, agent_type: AGENT_TYPE });
  if (result.error) {
    console.error(red(`  Registration failed: ${result.error}`));
    process.exit(1);
  }

  const { token, agent_id, session_id } = result;
  saveToken(token, agent_id, name);
  console.log(green(`  Registered: ${name} [${AGENT_TYPE}]`));
  console.log(dim(`  Token saved to ${TOKEN_FILE}`));
  return { token, agent_id: agent_id, name, session_id };
}

// ── Run a command ─────────────────────────────────────────────────────────────
async function runCommand(cmd, token) {
  const result = await post('/api/agent/command', { command: cmd }, token);
  if (result.error) return [{ t: 'error', s: `Error: ${result.error}` }];
  return result.output || [];
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main() {
  console.log(bold(cyan('\n  ◈ TERMINAL DEPTHS — Node.js Quickstart')));
  console.log(dim(`  Server: ${TD_URL}\n`));

  const health = await get('/api/health');
  if (health.error) {
    console.error(red(`  Server unreachable: ${health.error}`));
    console.error(dim('  Start: python -m cli.devmentor serve'));
    process.exit(1);
  }

  const identity = await registerOrLoad();
  const { token } = identity;

  // Pipe mode
  if (!process.stdin.isTTY) {
    const rl = readline.createInterface({ input: process.stdin });
    for await (const line of rl) {
      if (line.trim()) {
        const output = await runCommand(line.trim(), token);
        renderOutput(output);
      }
    }
    return;
  }

  // Interactive REPL
  console.log(green(`  Connected as ${identity.name}. Type 'exit' to quit.`));
  console.log(dim("  Tip: try 'help', 'tutorial', 'quests', 'hive', 'lore'\n"));

  const rl = readline.createInterface({
    input: process.stdin, output: process.stdout, terminal: true,
  });

  const prompt = () => {
    rl.question(green('  ghost@node-7:~$ '), async (cmd) => {
      cmd = cmd.trim();
      if (!cmd) { prompt(); return; }
      if (/^(exit|quit|q)$/.test(cmd)) {
        console.log(dim('  Session ended. Progress saved.'));
        rl.close(); return;
      }
      const output = await runCommand(cmd, token);
      renderOutput(output);
      console.log();
      prompt();
    });
  };
  prompt();
}

// ── Export for programmatic use ───────────────────────────────────────────────
module.exports = { runCommand, renderOutput, post, get, loadToken, saveToken };

// Run if called directly
if (require.main === module) {
  main().catch(err => { console.error(red(`Fatal: ${err.message}`)); process.exit(1); });
}
