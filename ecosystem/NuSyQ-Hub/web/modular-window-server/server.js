/**
 * ΞNuSyQ Modular Window System - Express Server
 * Serves the quantum modular interface on port 8080
 */

const express = require('express');
const path = require('path');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { exec } = require('child_process');
const fs = require('fs');
const fsp = require('fs/promises');

const app = express();
const PORT = process.env.PORT || 8080;

// Backend API endpoints
const FLASK_API = 'http://localhost:5001';
const FASTAPI = 'http://localhost:8000';

// Paths shared with the Python terminal ecosystem
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const LOG_DIR = path.join(REPO_ROOT, 'data', 'terminal_logs');
fs.mkdirSync(LOG_DIR, { recursive: true });

// In-memory terminal channels/logs (lightweight, restart-safe)
const TERMINAL_CHANNELS = new Set([
    'main',
    'agents',
    'ollama',
    'copilot',
    'chatdev',
    'errors',
    'shell-wsl',
    'shell-pwsh',
    'shell-cmd'
]);

// Keep a rolling buffer of terminal entries per channel (fast path for UI)
const TERMINAL_BUFFER_LIMIT = 200;
const terminalLogs = new Map();

// Normalize channel names to match Python terminal ecosystem (lowercase, underscores)
function normalizeChannel(channel = 'main') {
    const safe = String(channel || 'main').toLowerCase().replace(/[^a-z0-9]+/g, '_');
    return safe || 'main';
}

async function appendToLog(channel, entry) {
    const safe = normalizeChannel(channel);
    const logPath = path.join(LOG_DIR, `${safe}.log`);
    const payload = {
        ts: entry.ts || new Date().toISOString(),
        channel,
        level: entry.level || 'INFO',
        message: entry.message || '',
        meta: entry.metadata || entry.meta || {},
    };
    try {
        await fsp.appendFile(logPath, `${JSON.stringify(payload)}\n`, 'utf8');
    } catch (err) {
        console.warn(`[TERMINAL] Failed to append log for ${channel}:`, err.message);
    }
}

function addTerminalEntry(channel, entry, { persist = true } = {}) {
    const safeChannel = normalizeChannel(channel);
    TERMINAL_CHANNELS.add(safeChannel);

    if (!terminalLogs.has(safeChannel)) {
        terminalLogs.set(safeChannel, []);
    }
    const buffer = terminalLogs.get(safeChannel);
    const enriched = {
        timestamp: entry.timestamp || Date.now(),
        ts: entry.ts || new Date().toISOString(),
        level: entry.level || 'INFO',
        message: entry.message || '',
        metadata: entry.metadata || entry.meta || {},
    };

    buffer.unshift(enriched);
    if (buffer.length > TERMINAL_BUFFER_LIMIT) {
        buffer.length = TERMINAL_BUFFER_LIMIT;
    }

    if (persist) {
        appendToLog(safeChannel, enriched); // fire and forget
    }
}

async function readRecentEntries(channel, limit = 50) {
    const safeChannel = normalizeChannel(channel);
    const logPath = path.join(LOG_DIR, `${safeChannel}.log`);

    // Gather from buffer first for speed
    const buffered = (terminalLogs.get(safeChannel) || []).slice(0, limit);
    const remaining = limit - buffered.length;

    if (remaining <= 0) {
        return buffered;
    }

    try {
        const data = await fsp.readFile(logPath, 'utf8');
        if (!data) return buffered;
        const lines = data.trim().split('\n');
        const tail = lines.slice(-limit);
        const parsed = tail
            .map((line) => {
                try {
                    const obj = JSON.parse(line);
                    return {
                        timestamp: obj.timestamp || Date.parse(obj.ts || Date.now()),
                        ts: obj.ts || new Date().toISOString(),
                        level: obj.level || 'INFO',
                        message: obj.message || '',
                        metadata: obj.meta || obj.metadata || {},
                    };
                } catch (err) {
                    return {
                        timestamp: Date.now(),
                        level: 'INFO',
                        message: line,
                        metadata: { parse_error: true },
                    };
                }
            })
            .reverse(); // newest last lines at end; keep descending order

        // Deduplicate buffered entries (match on ts+message)
        const seen = new Set(buffered.map((b) => `${b.ts}|${b.message}`));
        const merged = [...parsed.filter((p) => !seen.has(`${p.ts}|${p.message}`)), ...buffered];
        return merged.slice(0, limit);
    } catch (err) {
        // file might not exist yet
        return buffered;
    }
}

async function runShellCommand(channel, command) {
    let shellCommand = command;
    let options = { timeout: 15000, windowsHide: true }; // 15s guard

    switch (channel) {
        case 'shell-wsl':
            // Run via WSL bash (requires WSL installed)
            shellCommand = `wsl.exe -e bash -lc "${command.replace(/"/g, '\\"')}"`;
            break;
        case 'shell-pwsh':
            shellCommand = `powershell.exe -NoLogo -NoProfile -Command "${command.replace(/"/g, '\\"')}"`;
            break;
        case 'shell-cmd':
            shellCommand = `cmd.exe /c ${command}`;
            break;
        default:
            return {
                stdout: '',
                stderr: `Unsupported shell channel: ${channel}`,
                exitCode: 1
            };
    }

    return new Promise((resolve) => {
        exec(shellCommand, options, (error, stdout, stderr) => {
            resolve({
                stdout: stdout || '',
                stderr: stderr || '',
                exitCode: error ? error.code || 1 : 0,
                error: error ? error.message : null
            });
        });
    });
}

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));
// Expose state and docs for UI data binding (read-only)
app.use('/state', express.static(path.join(__dirname, '..', '..', 'state')));
app.use('/docs', express.static(path.join(__dirname, '..', '..', 'docs')));

// Proxy to Flask Dashboard API (real-time data)
// Maps /api/dashboard/* → http://localhost:5001/api/*
app.use('/api/dashboard', createProxyMiddleware({
    target: FLASK_API,
    changeOrigin: true,
    pathRewrite: { '^/api/dashboard': '' },
    onProxyReq: (proxyReq, req, res) => {
        console.log(`[PROXY] ${req.method} ${req.url} → ${FLASK_API}${proxyReq.path}`);
    }
}));

// Proxy to FastAPI (status, health)
// Maps /api/system/* → http://localhost:8000/api/*
app.use('/api/system', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/system': '' },
    onProxyReq: (proxyReq, req, res) => {
        console.log(`[PROXY] ${req.method} ${req.url} → ${FASTAPI}${proxyReq.path}`);
    }
}));

// =============================================================================
// GAME-LIKE API ROUTES - Proxied to FastAPI backend (port 8000)
// Inspired by Bitburner, Hacknet, GreyHack, EmuDevz, HackHub
// =============================================================================

// fl1ght.exe Smart Search - proxied to FastAPI
app.use('/api/fl1ght', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/fl1ght': '/api/fl1ght' }
}));

// Hints, tutorials, FAQ, commands - game guidance system
app.use('/api/hints', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/hints': '/api/hints' }
}));

app.use('/api/tutorials', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/tutorials': '/api/tutorials' }
}));

app.use('/api/faq', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/faq': '/api/faq' }
}));

app.use('/api/commands', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/commands': '/api/commands' }
}));

// RPG Progression - skills, XP, progress
app.use('/api/skills', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/skills': '/api/skills' }
}));

app.use('/api/progress', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/progress': '/api/progress' }
}));

app.use('/api/rpg', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/rpg': '/api/rpg' }
}));

// Guild Board - multi-agent coordination
app.use('/api/guild', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/guild': '/api/guild' }
}));

// Actions/Ops - scriptable automation
app.use('/api/actions', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/actions': '/api/actions' }
}));

// Tips - contextual help
app.use('/api/tips', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/tips': '/api/tips' }
}));

// Evolve - AI suggestions
app.use('/api/evolve', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/evolve': '/api/evolve' }
}));

// Search - unified catalog search
app.use('/api/search', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/search': '/api/search' }
}));

// Ops - operations helpers
app.use('/api/ops', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/ops': '/api/ops' }
}));

// Systems - Culture Ship, SimulatedVerse, Orchestrator status
app.use('/api/systems', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/systems': '/api/systems' }
}));

// Metrics - system metrics
app.use('/api/metrics', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/metrics': '/api/metrics' }
}));

// Quests - quest tracking
app.use('/api/quests', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/quests': '/api/quests' }
}));

// Agents - agent list
app.use('/api/agents', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/agents': '/api/agents' }
}));

// Map - system navigation map
app.use('/api/map', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/map': '/api/map' }
}));

// Whoami - identity check
app.use('/api/whoami', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/whoami': '/api/whoami' }
}));

// Game state persistence - save/load/reset
app.use('/api/game', createProxyMiddleware({
    target: FASTAPI,
    changeOrigin: true,
    pathRewrite: { '^/api/game': '/api/game' }
}));

// =============================================================================
// LOCAL ENDPOINTS
// =============================================================================

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'operational',
        service: 'NuSyQ-Hub Modular Window System',
        port: PORT,
        timestamp: new Date().toISOString(),
        modules: ['QuantumTerminal', 'ConsciousChatBox', 'RPGStatusDisplay'],
        backends: {
            flask: FLASK_API,
            fastapi: FASTAPI
        },
        game_features: [
            'fl1ght.exe smart search',
            'RPG progression',
            'Guild board',
            'Actions/Ops',
            'Tips & guidance'
        ]
    });
});

// API endpoint for module data (placeholder for future quantum module integration)
app.get('/api/modules', (req, res) => {
    res.json({
        modules: [
            { id: 'terminal', type: 'QuantumTerminal', status: 'active' },
            { id: 'chat_interface', type: 'ConsciousChatBox', status: 'active' },
            { id: 'status_monitor', type: 'RPGStatusDisplay', status: 'active' }
        ]
    });
});

// --- Lightweight Terminal API (single-process, dev-use) ---

// List channels
app.get('/api/terminals', (req, res) => {
    try {
        const diskChannels = fs.readdirSync(LOG_DIR)
            .filter((name) => name.endsWith('.log'))
            .map((name) => name.replace(/\.log$/, ''));
        diskChannels.forEach((ch) => TERMINAL_CHANNELS.add(ch));
    } catch (err) {
        // non-fatal; fall back to in-memory set
    }
    res.json(Array.from(TERMINAL_CHANNELS));
});

// Health check for terminal API
app.get('/api/terminals/health', (req, res) => {
    res.json({ status: 'ok', channels: Array.from(TERMINAL_CHANNELS) });
});

// Recent entries for channel
app.get('/api/terminals/:channel/recent', async (req, res) => {
    const { channel } = req.params;
    const count = Math.min(parseInt(req.query.count || '50', 10), 200);
    try {
        const entries = await readRecentEntries(channel, count);
        res.json(entries.slice(0, count));
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// Send/execute command
app.post('/api/terminals/send', async (req, res) => {
    const { channel, message, level = 'INFO', metadata = {} } = req.body || {};

    if (!channel || !message) {
        return res.status(400).json({ success: false, error: 'channel and message required' });
    }

    TERMINAL_CHANNELS.add(channel);

    // Log inbound command
    addTerminalEntry(channel, { level, message, metadata: { ...metadata, type: 'command' } });

    let result = { success: true };

    // Execute shell commands for shell channels
    if (channel.startsWith('shell-')) {
        result = await runShellCommand(channel, message);

        // Capture stdout/stderr as separate log entries
        if (result.stdout) {
            addTerminalEntry(channel, {
                level: result.exitCode === 0 ? 'SUCCESS' : 'INFO',
                message: result.stdout,
                metadata: { type: 'command_response', command: message }
            });
        }
        if (result.stderr) {
            addTerminalEntry(channel, {
                level: 'ERROR',
                message: result.stderr,
                metadata: { type: 'command_response', command: message }
            });
        }

        // Summary line
        addTerminalEntry(channel, {
            level: result.exitCode === 0 ? 'SUCCESS' : 'ERROR',
            message: `exit ${result.exitCode}${result.error ? ` | ${result.error}` : ''}`,
            metadata: { type: 'command_response', command: message }
        });
    }

    res.json({
        success: true,
        channel,
        message,
        result
    });
});

// Ship status (JSON or SSE)
app.get('/api/status/ship', async (req, res) => {
    const statusPath = path.join(REPO_ROOT, 'state', 'reports', 'ship_status.json');
    if (req.query.stream === 'sse') {
        res.writeHead(200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            Connection: 'keep-alive',
        });
        const send = () => {
            try {
                if (fs.existsSync(statusPath)) {
                    const data = JSON.parse(fs.readFileSync(statusPath, 'utf8'));
                    res.write(`data: ${JSON.stringify(data)}\n\n`);
                }
            } catch (err) {
                res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
            }
        };
        const timer = setInterval(send, 4000);
        req.on('close', () => clearInterval(timer));
        send();
        return;
    }
    try {
        if (fs.existsSync(statusPath)) {
            const data = JSON.parse(fs.readFileSync(statusPath, 'utf8'));
            return res.json(data);
        }
        const py = process.env.PYTHON_BIN || 'python';
        const result = spawnSync(py, ['scripts/service_watch.py', '--json'], {
            cwd: REPO_ROOT,
            encoding: 'utf8',
            timeout: 5000,
        });
        if (result.status === 0 && result.stdout) {
            return res.json(JSON.parse(result.stdout));
        }
        return res.status(500).json({ error: 'service_watch failed', detail: result.stderr });
    } catch (err) {
        return res.status(500).json({ error: err.message });
    }
});

// Tail terminal logs by channel (JSON or SSE)
app.get('/api/logs/:channel', async (req, res) => {
    const channel = (req.params.channel || 'main').toLowerCase().replace(/[^a-z0-9_]+/g, '_');
    const logPath = path.join(REPO_ROOT, 'data', 'terminal_logs', `${channel}.log`);
    if (req.query.stream === 'sse') {
        res.writeHead(200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            Connection: 'keep-alive',
        });
        let lastLength = 0;
        const send = () => {
            try {
                if (!fs.existsSync(logPath)) return;
                const data = fs.readFileSync(logPath, 'utf8');
                const lines = data.trim().split('\n');
                if (lines.length > lastLength) {
                    const chunk = lines.slice(lastLength);
                    res.write(`data: ${JSON.stringify({ lines: chunk })}\n\n`);
                    lastLength = lines.length;
                }
            } catch (err) {
                res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
            }
        };
        const timer = setInterval(send, 2000);
        req.on('close', () => clearInterval(timer));
        send();
        return;
    }
    try {
        if (!fs.existsSync(logPath)) {
            return res.json({ channel, lines: [] });
        }
        const data = fs.readFileSync(logPath, 'utf8');
        const lines = data.trim().split('\n').slice(-200).map((line) => {
            try {
                return JSON.parse(line);
            } catch (e) {
                return { ts: null, level: 'INFO', message: line };
            }
        });
        return res.json({ channel, lines });
    } catch (err) {
        return res.status(500).json({ error: err.message });
    }
});

// Local actions (bypass FastAPI)
app.post('/api/local/actions/build', async (req, res) => {
    const py = process.env.PYTHON_BIN || 'python';
    const timeoutMs = parseInt(process.env.BUILD_TIMEOUT_MS || '180000', 10);
    const result = spawnSync(py, ['scripts/game_build_pipeline.py', '--skip-packaging'], {
        cwd: REPO_ROOT,
        encoding: 'utf8',
        timeout: timeoutMs,
    });
    const payload = { returncode: result.status, stdout: result.stdout, stderr: result.stderr };
    try { logToChannel('testing', `Build rc=${result.status}`); } catch (_) {}
    return res.json(payload);
});

app.post('/api/local/actions/chamber', async (req, res) => {
    const py = process.env.PYTHON_BIN || 'python';
    const timeoutMs = parseInt(process.env.CHAMBER_TIMEOUT_MS || '90000', 10);
    const result = spawnSync(py, ['scripts/chamber_run_cyberterminal.py'], {
        cwd: REPO_ROOT,
        encoding: 'utf8',
        timeout: timeoutMs,
    });
    const payload = { returncode: result.status, stdout: result.stdout, stderr: result.stderr };
    try { logToChannel('testing', `Chamber rc=${result.status}`); } catch (_) {}
    return res.json(payload);
});

app.post('/api/local/actions/start-services', async (req, res) => {
    const py = process.env.PYTHON_BIN || 'python';
    const result = spawnSync(py, ['scripts/nusyq_launcher.py', 'start-services'], {
        cwd: REPO_ROOT,
        encoding: 'utf8',
        timeout: 60000,
    });
    const payload = { returncode: result.status, stdout: result.stdout, stderr: result.stderr };
    try { logToChannel('testing', `start-services rc=${result.status}`); } catch (_) {}
    return res.json(payload);
});

app.post('/api/local/cyberterminal/run', async (req, res) => {
    const py = process.env.PYTHON_BIN || 'python';
    const body = req.body || {};
    const commands = body.commands || [];
    const statePath = body.state_path || null;
    try {
        const proc = spawnSync(py, ['scripts/cyberterminal_run.py'], {
            cwd: REPO_ROOT,
            input: JSON.stringify({ commands, state_path: statePath }),
            encoding: 'utf8',
            timeout: 10000,
        });
        if (proc.status === 0 && proc.stdout) {
            return res.json(JSON.parse(proc.stdout));
        }
        return res.status(500).json({ error: 'cyberterminal_run failed', detail: proc.stderr });
    } catch (err) {
        return res.status(500).json({ error: err.message });
    }
});

// Serve main interface
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════════════════════════════╗
║     🌌 ΞNuSyQ Modular Window System - Server Running              ║
║     Inspired by Bitburner, Hacknet, GreyHack, EmuDevz, HackHub    ║
╚════════════════════════════════════════════════════════════════════╝

🌐 Server Status:
   Port: ${PORT}
   URL:  http://localhost:${PORT}

🔮 Quantum Modules Initialized:
   ✅ QuantumTerminal
   ✅ ConsciousChatBox
   ✅ RPGStatusDisplay

🎮 Game-Like Features:
   🔍 fl1ght.exe     - /api/fl1ght?q=<query>
   📊 Progress       - /api/progress
   ⚡ Actions        - /api/actions
   💡 Tips           - /api/tips/random
   👥 Guild          - /api/guild/summary

🔗 Proxied Backends:
   Flask (NuSyQ):        ${FLASK_API} → /api/dashboard/*
   FastAPI (Hub):        ${FASTAPI}   → /api/*

🔧 API Endpoints:
   GET /health          - Health check
   GET /api/modules     - Module status
   GET /api/fl1ght      - Smart search
   GET /api/hints       - Quest hints
   GET /api/progress    - RPG progression
   GET /api/skills      - Skill XP
   GET /api/actions     - Available operations
   GET /api/guild/*     - Guild board
   GET /api/systems/*   - System status

Press Ctrl+C to stop the server
`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n\n🌙 Shutting down ΞNuSyQ Modular Window System...');
    process.exit(0);
});
