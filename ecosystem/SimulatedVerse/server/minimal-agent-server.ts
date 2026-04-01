// Minimal Agent-Only Server for SimulatedVerse
// Bypasses ALL DB/storage/schema dependencies

import express from 'express';
import cors from 'cors';

const app = express();
app.use(cors());
app.use(express.json({ limit: '256kb' }));

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    mode: 'agent-only',
    message: 'DB persistence disabled - agents only',
    timestamp: Date.now()
  });
});

// Load ONLY agent router (no DB dependencies)
const loadAgentRoutes = async () => {
  try {
    const { agentsRouter } = await import('./router/agents.js');
    app.use('/api/agents', agentsRouter);
    console.log('✅ Agent routes loaded');
    
    // Test agent loading immediately
    const testReq: any = { path: '/api/agents' };
    const testRes: any = {
      json: (data: any) => {
        console.log(`📊 Agent count: ${data.count}`);
        if (data.count === 0) {
          console.log('⚠️  No agents loaded - check agents/ directory');
        } else {
          console.log(`✅ ${data.count} agents available:`, data.agents.map((a: any) => a.id || a.name).join(', '));
        }
      }
    };
  } catch (error: any) {
    console.error('❌ Failed to load agent routes:', error.message);
    console.error('   Full error:', error);
  }
};

// Load PU queue (if it doesn't depend on DB)
const loadPURoutes = async () => {
  try {
    const { pu } = await import('./router/pu.js');
    app.use('/api/pu', pu);
    console.log('✅ PU Queue routes loaded');
  } catch (error: any) {
    console.log('⚠️  PU Queue not available:', error.message);
  }
};

// Load Culture Ship (if it doesn't depend on broken schemas)
const loadCultureShipRoutes = async () => {
  try {
    const cultureShipRoutes = await import('./routes/culture-ship.js');
    app.use('/api/culture-ship', cultureShipRoutes.default);
    console.log('✅ Culture Ship routes loaded');
  } catch (error: any) {
    console.log('⚠️  Culture Ship not available:', error.message);
  }
};

// Initialize routes
const startServer = async () => {
  console.log('');
  console.log('======================================================================');
  console.log(' SIMULATEDVERSE AGENT-ONLY MODE');
  console.log(' DB Persistence: DISABLED');
  console.log(' Agents: ENABLED');
  console.log('======================================================================');
  console.log('');
  console.log(`  Health Check: http://localhost:${PORT}/api/health`);
  console.log(`  Agent API: http://localhost:${PORT}/api/agents`);
  console.log(`  PU Queue: http://localhost:${PORT}/api/pu`);
  console.log(`  Culture Ship: http://localhost:${PORT}/api/culture-ship`);
  console.log('');
  console.log('======================================================================');
  console.log('');

  await loadPURoutes();
  await loadCultureShipRoutes();
  await loadAgentRoutes();

  console.log('📍 All routes loaded, about to call app.listen()...');
  console.log('📍 PORT:', PORT);
  console.log('📍 app exists:', !!app);
  
  const server = app.listen(PORT, () => {
    console.log(`🚀 Server listening on port ${PORT}`);
    console.log(`📡 Server instance:`, !!server);
    console.log(`📍 Server address:`, server.address());
  });

  console.log('📍 app.listen() call completed, server object:', !!server);
  
  // Explicitly keep server alive
  server.ref();

  // Keep process alive
  process.on('SIGTERM', () => {
    console.log('SIGTERM signal received: closing HTTP server');
    server.close(() => {
      console.log('HTTP server closed');
    });
  });

  return server;
};

// Keep global reference to prevent GC
let serverInstance: any = null;

const PORT = Number(process.env.PORT || process.env.SIMULATEDVERSE_PORT || '5002');

// Add process error handlers
process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error);
});

startServer().then((server) => {
  serverInstance = server; // Keep reference
  console.log('✅ startServer() completed successfully');
  console.log('⏳ Process should now stay alive...');
  
  // Keep event loop alive
  setInterval(() => {
    // Do nothing, just keep process alive
  }, 10000);
}).catch(error => {
  console.error('❌ Failed to start server:', error);
  process.exit(1);
});

console.log('📝 Script execution continues after startServer() call...');
