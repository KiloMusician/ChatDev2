import express from 'express';
import cors from 'cors';
import path from 'path';
import { existsSync } from 'fs';
import { fileURLToPath } from 'url';

const app = express();
app.use(cors());
app.use(express.json());

const HOST = process.env.SIMULATEDVERSE_HOST || '127.0.0.1';
const PORT = Number(process.env.SIMULATEDVERSE_PORT || process.env.PORT || 5002);
const BASE = HOST.startsWith('http') ? HOST : `http://${HOST}`;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PUBLIC_DIR_CANDIDATES = [
    path.resolve(__dirname, '../client/public'),
    path.resolve(__dirname, '../dist/public'),
    path.resolve(__dirname, './public'),
];
const PUBLIC_DIR = PUBLIC_DIR_CANDIDATES.find((candidate) => existsSync(path.join(candidate, 'index.html'))) || PUBLIC_DIR_CANDIDATES[0];
const INDEX_HTML = path.join(PUBLIC_DIR, 'index.html');

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy', ok: true, mode: 'minimal', agents: 9, timestamp: Date.now() });
});

app.get('/healthz', (req, res) => {
    res.json({ ok: true, mode: 'minimal', timestamp: Date.now() });
});

app.get('/readyz', (req, res) => {
    res.json({ ok: true, mode: 'minimal', timestamp: Date.now() });
});

app.use(express.static(PUBLIC_DIR));

// Agent API routes (dynamic imports to avoid persistence layer)
const loadAgentRoutes = async () => {
    try {
        const { agentsRouter } = await import('./router/agents.js');
        app.use('/api/agents', agentsRouter);
        console.log('✅ Agent routes loaded');
    } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        console.log('⚠️  Agent routes not available:', msg);
    }

    try {
        const { proposals } = await import('./router/proposals.js');
        app.use('/api/proposals', proposals);
        console.log('✅ Proposal routes loaded');
    } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        console.log('⚠️  Proposal routes not available:', msg);
    }

    try {
        const { pu } = await import('./router/pu.js');
        app.use('/api/pu', pu);
        console.log('✅ PU Queue routes loaded');
    } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        console.log('⚠️  PU Queue routes not available:', msg);
    }
};

loadAgentRoutes();

app.get('/', (_req, res) => {
    res.sendFile(INDEX_HTML);
});

app.get('*', (req, res, next) => {
    if (req.path.startsWith('/api') || req.path.startsWith('/assets/') || req.path.includes('.')) {
        return next();
    }
    res.sendFile(INDEX_HTML);
});

const server = app.listen(PORT, HOST, () => {
    console.log(`
======================================================================
 SIMULATEDVERSE MINIMAL MODE
 Static Client: ${BASE}:${PORT}/
 Agent API: ${BASE}:${PORT}/api/agents
 Health Check: ${BASE}:${PORT}/api/health
======================================================================
    `);
});

const shutdown = (signal: NodeJS.Signals) => {
    console.log(`[minimal_server] received ${signal}; shutting down`);
    server.close(() => process.exit(signal === 'SIGTERM' ? 143 : 130));
};

process.once('SIGINT', () => shutdown('SIGINT'));
process.once('SIGTERM', () => shutdown('SIGTERM'));

server.on('error', (error) => {
    console.error('[minimal_server] listen failed:', error);
    process.exit(1);
});
